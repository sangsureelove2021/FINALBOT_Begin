"""
Entry Scorer

Scores how good the current moment is for entry.
"""

from core.models.market_context import MarketContext


class EntryScorer:
    """Compute 0-100 entry quality score"""
    
    def score(self, context: MarketContext) -> int:
        """Compute entry score 0-100"""
        score = 50.0  # Base
        
        # Trend strength bonus
        trend_str = context.trend.get('strength', 0)
        if trend_str > 70:
            score += 15
        elif trend_str > 50:
            score += 8
        
        # Momentum confirmation
        strength_score = context.strength.get('strength_score', 50)
        if strength_score > 70:
            score += 10
        
        # MTF alignment bonus
        mtf_score = context.mtf.get('alignment_score', 50)
        if mtf_score > 80:
            score += 12
        elif mtf_score > 60:
            score += 6
        
        # Structure clarity bonus
        if context.structure.get('structure_score', 0) > 70:
            score += 8
        
        # Zone proximity bonus (price near key level)
        proximity = context.structure.get('zone_proximity', 'FAR')
        if proximity == 'AT_LEVEL':
            score += 5
        elif proximity == 'NEAR':
            score += 3
        
        # Volatility regime check
        regime = context.volatility.get('regime', 'NORMAL')
        if regime == 'EXTREME':
            score -= 15  # Don't enter in extreme volatility
        elif regime == 'LOW':
            state_str = context.market_state.get('state', 'UNKNOWN') if isinstance(context.market_state, dict) else context.market_state
            if state_str in ("ACCUMULATION", "BREAKOUT_EMERGING"):
                score += 15  # Compression is a strong plus for breakouts!
            else:
                score -= 8   # Avoid low vol for normal trend following
        
        return int(max(0, min(100, score)))
