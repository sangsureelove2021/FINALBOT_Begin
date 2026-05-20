"""
TIER 6 - CONTEXT SYNTHESIZER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Synthesizes all Tier 1-5 outputs into a unified market picture.
This is where the system "understands" the market holistically.

Operates on MarketContext (reads all prior tiers).
"""

from typing import Dict, Any
from core.engines.base_engine import BaseEngine


class ContextSynthesizer(BaseEngine):
    """Tier 6: Context Synthesizer - reads MarketContext directly"""
    
    ENGINE_NAME = "context_synthesizer"
    ENGINE_VERSION = "1.0.0"
    TIER = 6
    
    def analyze(self, context=None, **kwargs) -> Dict[str, Any]:
        """
        Synthesize. Accepts MarketContext via 'context' kwarg.
        ContextBuilder passes context for Tier 6+ engines.
        """
        try:
            ctx = context or kwargs.get('context')
            if ctx is None:
                return self.get_neutral_state()
            
            # Synthesize directional bias
            directional_bias, bias_strength = self._synthesize_direction(ctx)
            
            # Synthesize market clarity
            clarity = self._synthesize_clarity(ctx)
            
            # Synthesize risk picture
            risk_level = self._synthesize_risk(ctx)
            
            # Overall market read
            market_read = self._compose_market_read(
                ctx, directional_bias, clarity, risk_level
            )
            
            # Tradeable assessment
            tradeable = self._is_tradeable(clarity, risk_level, ctx)
            
            return {
                'directional_bias': directional_bias,
                'bias_strength': bias_strength,
                'market_clarity': clarity,
                'risk_level': risk_level,
                'market_read': market_read,
                'tradeable': tradeable,
                'synthesis_quality': self._synthesis_quality(clarity, risk_level),
                'confidence': clarity,
            }
        except Exception as e:
            print(f"❌ ContextSynthesizer error: {e}")
            return self.get_neutral_state()
    
    def _synthesize_direction(self, ctx):
        """Combine all directional signals into one bias"""
        votes = {'UP': 0.0, 'DOWN': 0.0}
        
        # Trend (weight 3)
        trend_dir = ctx.trend.get('direction', 'NONE')
        if trend_dir in votes:
            votes[trend_dir] += 3.0 * (ctx.trend.get('confidence', 50) / 100)
        
        # MTF (weight 3)
        mtf_dir = ctx.mtf.get('dominant_direction', 'NONE')
        if mtf_dir in votes:
            votes[mtf_dir] += 3.0 * (ctx.mtf.get('alignment_score', 50) / 100)
        
        # Conflict analyzer EMA direction (weight 2)
        ema_dir = ctx.conflict.get('ema_direction', 'NONE')
        if ema_dir in votes:
            votes[ema_dir] += 2.0
        
        # Candle patterns bias (weight 1)
        pattern_bias = ctx.candle_patterns.get('bias', 'NEUTRAL')
        if pattern_bias == 'BULLISH':
            votes['UP'] += 1.0
        elif pattern_bias == 'BEARISH':
            votes['DOWN'] += 1.0
        
        # Price action bias (weight 1)
        pa_bias = ctx.price_action.get('directional_bias', 'NEUTRAL')
        if pa_bias == 'BULLISH':
            votes['UP'] += 1.0
        elif pa_bias == 'BEARISH':
            votes['DOWN'] += 1.0
        
        total = votes['UP'] + votes['DOWN']
        if total == 0:
            return 'NONE', 0
        
        if votes['UP'] > votes['DOWN']:
            direction = 'UP'
            strength = int((votes['UP'] / total) * 100)
        elif votes['DOWN'] > votes['UP']:
            direction = 'DOWN'
            strength = int((votes['DOWN'] / total) * 100)
        else:
            return 'NONE', 50
        
        return direction, strength
    
    def _synthesize_clarity(self, ctx) -> int:
        """How clear is the market picture (0-100)"""
        clarity = 50
        
        # Conflict reduces clarity
        conflict_score = ctx.conflict.get('conflict_score', 0)
        clarity -= conflict_score * 0.3
        
        # Noise reduces clarity
        noise_level = ctx.noise.get('noise_level', 50)
        clarity -= (noise_level - 50) * 0.3
        
        # Efficiency increases clarity
        efficiency = ctx.efficiency.get('overall_efficiency', 50)
        clarity += (efficiency - 50) * 0.3
        
        # MTF alignment increases clarity
        mtf_align = ctx.mtf.get('alignment_score', 50)
        clarity += (mtf_align - 50) * 0.2
        
        # Regime quality
        regime_q = ctx.regime_quality.get('overall_quality', 50)
        clarity += (regime_q - 50) * 0.2
        
        return int(min(100, max(0, clarity)))
    
    def _synthesize_risk(self, ctx) -> int:
        """Aggregate risk level (0-100, high = risky)"""
        risk = 0
        
        if ctx.traps.get('trap_detected'):
            risk += 30
        if ctx.anomaly.get('anomaly_detected'):
            risk += 25
        if ctx.transition.get('in_transition'):
            risk += 20
        
        noise = ctx.noise.get('noise_level', 0)
        risk += noise * 0.2
        
        exhaustion = ctx.strength.get('exhaustion_risk', 0)
        risk += exhaustion * 0.15
        
        conflict = ctx.conflict.get('conflict_score', 0)
        risk += conflict * 0.15
        
        return int(min(100, max(0, risk)))
    
    def _compose_market_read(self, ctx, bias, clarity, risk) -> str:
        """Human-readable market summary"""
        state = ctx.market_state.get('state', 'UNKNOWN')
        
        if risk > 65:
            return f"{state} but HIGH RISK - caution advised"
        if clarity < 35:
            return f"{state} - UNCLEAR picture, signals conflicting"
        if clarity > 70 and risk < 35:
            return f"{state} - CLEAR {bias} bias, favorable conditions"
        return f"{state} - {bias} bias, moderate clarity"
    
    def _is_tradeable(self, clarity, risk, ctx) -> bool:
        """Overall tradeable decision"""
        if risk > 60:
            return False
        if clarity < 40:
            return False
        if not ctx.market_state.get('tradeable', False):
            return False
        return True
    
    def _synthesis_quality(self, clarity, risk) -> int:
        """Quality of the synthesis 0-100"""
        return int(max(0, min(100, clarity - risk * 0.5)))
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'directional_bias': 'NONE', 'bias_strength': 0,
            'market_clarity': 30, 'risk_level': 50,
            'market_read': 'Insufficient data for synthesis',
            'tradeable': False, 'synthesis_quality': 0,
            'confidence': 0,
        }
