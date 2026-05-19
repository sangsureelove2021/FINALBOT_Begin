"""
Compression Breakout Strategy (V1 Sample)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Strategy: 5M Volatility Compression Breakout

Concept:
    When volatility compresses (low ATR percentile),
    it usually leads to expansion (breakout).
    
    Trade in direction of expansion when:
    - ATR percentile was low (compression)
    - Volatility now expanding
    - Direction confirmed by MTF
    - No conflicts or anomalies
"""

from typing import Dict, Any
from strategy.base_strategy import BaseStrategy
from core.models.market_context import MarketContext


class CompressionBreakoutStrategy(BaseStrategy):
    """5M Volatility Compression Breakout strategy"""
    
    STRATEGY_NAME = "compression_breakout"
    REQUIRED_MARKET_STATE = "BREAKING_OUT"
    MIN_CONFIDENCE = 75
    
    # Parameters
    MAX_COMPRESSION_ATR_PERCENTILE = 30  # Was compressed
    MIN_EXPANSION_PROBABILITY = 60       # Should be expanding
    MIN_MTF_ALIGNMENT = 70               # MTF agreement
    MIN_TREND_STRENGTH = 50              # Some directional bias
    
    def is_eligible(self, context: MarketContext) -> bool:
        """Eligible only in compression -> expansion state"""
        # Check for compression history
        contraction_prob = context.volatility.get('contraction_probability', 50)
        expansion_prob = context.volatility.get('expansion_probability', 50)
        atr_percentile = context.volatility.get('atr_percentile', 50)
        
        # Look for breakout setup: was compressed (low ATR) + now expanding
        was_compressed = atr_percentile <= self.MAX_COMPRESSION_ATR_PERCENTILE
        is_expanding = expansion_prob >= self.MIN_EXPANSION_PROBABILITY
        
        return was_compressed or is_expanding
    
    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        """Evaluate breakout opportunity"""
        
        # Pre-checks
        if not self.is_eligible(context):
            return self._no_signal("Not in compression-breakout setup")
        
        # Get key metrics
        trend_dir = context.trend.get('direction', 'NONE')
        trend_strength = context.trend.get('strength', 0)
        trend_confidence = context.trend.get('confidence', 0)
        
        atr_percentile = context.volatility.get('atr_percentile', 50)
        expansion_prob = context.volatility.get('expansion_probability', 50)
        regime = context.volatility.get('regime', 'NORMAL')
        
        mtf_alignment = context.mtf.get('alignment_score', 50)
        mtf_conflict = context.mtf.get('htf_ltf_conflict', False)
        htf_direction = context.mtf.get('htf_direction', 'NONE')
        
        adx = context.strength.get('adx', 0)
        rsi = context.strength.get('rsi', 50)
        momentum_level = context.strength.get('momentum_level', 'WEAK')
        
        # === DECISION LOGIC ===
        
        # Block conditions
        if trend_dir == 'NONE':
            return self._no_signal("No clear direction")
        
        if trend_strength < self.MIN_TREND_STRENGTH:
            return self._no_signal(f"Trend too weak ({trend_strength})")
        
        if mtf_conflict:
            return self._no_signal("MTF conflict detected")
        
        if mtf_alignment < self.MIN_MTF_ALIGNMENT:
            return self._no_signal(f"MTF alignment too low ({mtf_alignment})")
        
        if regime == 'EXTREME':
            return self._no_signal("Volatility too extreme")
        
        # Direction agreement
        if htf_direction != 'NONE' and htf_direction != trend_dir:
            return self._no_signal(f"HTF says {htf_direction}, trend says {trend_dir}")
        
        # === CALCULATE SCORES ===
        
        # Entry score
        entry_score = 50
        entry_score += min(20, trend_strength / 5)         # +0 to +20
        entry_score += min(15, expansion_prob / 7)         # +0 to +15
        entry_score += min(10, mtf_alignment / 10)         # +0 to +10
        entry_score += 5 if momentum_level in ('STRONG', 'NORMAL') else 0
        entry_score = min(100, entry_score)
        
        # Block score
        block_score = 0
        if context.traps.get('trap_detected'):
            block_score += 30
        if context.noise.get('noise_level', 0) > 60:
            block_score += 20
        if context.strength.get('exhaustion_risk', 0) > 60:
            block_score += 15
        if context.trend.get('reversal_risk', 0) > 60:
            block_score += 15
        
        # Final confidence
        confidence = int(entry_score * (1 - block_score / 200))
        confidence = max(0, min(100, confidence))
        
        # Decision
        if confidence < self.MIN_CONFIDENCE:
            return self._no_signal(f"Confidence too low ({confidence})")
        
        # Determine action
        action = 'CALL' if trend_dir == 'UP' else 'PUT'
        
        reason = (
            f"Compression breakout: trend={trend_dir}, strength={trend_strength}, "
            f"ATR%={atr_percentile:.0f}, expand={expansion_prob:.0f}, "
            f"MTF={mtf_alignment:.0f}"
        )
        
        return {
            'action': action,
            'confidence': confidence,
            'reason': reason,
            'entry_score': int(entry_score),
            'block_score': int(block_score),
            'strategy_name': self.STRATEGY_NAME,
        }
