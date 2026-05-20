"""
TIER 6 - PROBABILITY ESTIMATOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Estimates probability of price moving UP vs DOWN in the next period.
Combines all evidence into a calibrated probability.

For binary options: this is the core "will it go up or down" estimate.
"""

from typing import Dict, Any
from core.engines.base_engine import BaseEngine


class ProbabilityEstimator(BaseEngine):
    """Tier 6: Move Probability Estimator - reads MarketContext"""
    
    ENGINE_NAME = "probability_estimator"
    ENGINE_VERSION = "1.0.0"
    TIER = 6
    
    def analyze(self, context=None, **kwargs) -> Dict[str, Any]:
        """Estimate UP/DOWN probability from full context"""
        try:
            ctx = context or kwargs.get('context')
            if ctx is None:
                return self.get_neutral_state()
            
            # Collect probabilistic evidence
            up_prob = self._estimate_up_probability(ctx)
            down_prob = 100 - up_prob
            
            # Confidence in the estimate
            estimate_confidence = self._estimate_confidence(ctx, up_prob)
            
            # Expected move magnitude
            expected_magnitude = self._expected_magnitude(ctx)
            
            # Direction
            if up_prob >= 58:
                direction = 'UP'
            elif up_prob <= 42:
                direction = 'DOWN'
            else:
                direction = 'NEUTRAL'
            
            # Edge: how far from 50/50
            edge = abs(up_prob - 50)
            
            return {
                'up_probability': up_prob,
                'down_probability': down_prob,
                'direction': direction,
                'edge': int(edge),
                'estimate_confidence': estimate_confidence,
                'expected_magnitude': expected_magnitude,
                'has_edge': edge >= 8,
                'confidence': estimate_confidence,
            }
        except Exception as e:
            print(f"❌ ProbabilityEstimator error: {e}")
            return self.get_neutral_state()
    
    def _estimate_up_probability(self, ctx) -> int:
        """Estimate probability of UP move (0-100)"""
        # Start at 50/50
        prob = 50.0
        
        # === Trend evidence ===
        trend_dir = ctx.trend.get('direction', 'NONE')
        trend_conf = ctx.trend.get('confidence', 50)
        if trend_dir == 'UP':
            prob += (trend_conf / 100) * 12
        elif trend_dir == 'DOWN':
            prob -= (trend_conf / 100) * 12
        
        # === MTF evidence ===
        mtf_dir = ctx.mtf.get('dominant_direction', 'NONE')
        mtf_align = ctx.mtf.get('alignment_score', 50)
        if mtf_dir == 'UP':
            prob += (mtf_align / 100) * 10
        elif mtf_dir == 'DOWN':
            prob -= (mtf_align / 100) * 10
        
        # === Continuation evidence ===
        cont_prob = ctx.continuation.get('continuation_probability', 50)
        cont_bias = ctx.continuation.get('bias', 'NEUTRAL')
        if cont_bias == 'CONTINUATION' and trend_dir == 'UP':
            prob += (cont_prob - 50) * 0.15
        elif cont_bias == 'CONTINUATION' and trend_dir == 'DOWN':
            prob -= (cont_prob - 50) * 0.15
        
        # === Market pressure evidence ===
        buy_pressure = ctx.orderflow.get('buy_pressure', 50)
        prob += (buy_pressure - 50) * 0.16
        
        # === Divergence evidence (reversal signal) ===
        if ctx.divergence.get('divergence_detected'):
            div_type = ctx.divergence.get('divergence_type', 'NONE')
            div_strength = ctx.divergence.get('divergence_strength', 0)
            if div_type == 'BULLISH':
                prob += (div_strength / 100) * 8
            elif div_type == 'BEARISH':
                prob -= (div_strength / 100) * 8
        
        # === Candle pattern evidence ===
        pattern_bias = ctx.candle_patterns.get('bias', 'NEUTRAL')
        pattern_strength = ctx.candle_patterns.get('pattern_strength', 0)
        if pattern_bias == 'BULLISH':
            prob += (pattern_strength / 100) * 6
        elif pattern_bias == 'BEARISH':
            prob -= (pattern_strength / 100) * 6
        
        # === Strength/momentum evidence ===
        rsi = ctx.strength.get('rsi', 50)
        if rsi > 50:
            prob += min(5, (rsi - 50) * 0.15)
        else:
            prob -= min(5, (50 - rsi) * 0.15)
        
        return int(min(95, max(5, prob)))
    
    def _estimate_confidence(self, ctx, up_prob) -> int:
        """Confidence in the probability estimate"""
        conf = 50
        
        # Clear edge = more confident
        edge = abs(up_prob - 50)
        conf += min(20, edge)
        
        # Low conflict = more confident
        conflict = ctx.conflict.get('conflict_score', 50)
        conf -= conflict * 0.25
        
        # Low noise = more confident
        noise = ctx.noise.get('noise_level', 50)
        conf -= (noise - 50) * 0.2
        
        # Synthesis clarity
        clarity = ctx.synthesized_context.get('market_clarity', 50)
        conf += (clarity - 50) * 0.3
        
        return int(min(100, max(0, conf)))
    
    def _expected_magnitude(self, ctx) -> str:
        """Expected size of the move"""
        regime = ctx.volatility.get('regime', 'NORMAL')
        expansion = ctx.volatility.get('expansion_probability', 50)
        
        if regime == 'EXTREME' or expansion > 70:
            return 'LARGE'
        elif regime == 'HIGH' or expansion > 55:
            return 'MEDIUM'
        elif regime == 'LOW':
            return 'SMALL'
        return 'MEDIUM'
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'up_probability': 50, 'down_probability': 50,
            'direction': 'NEUTRAL', 'edge': 0,
            'estimate_confidence': 0, 'expected_magnitude': 'MEDIUM',
            'has_edge': False, 'confidence': 0,
        }
