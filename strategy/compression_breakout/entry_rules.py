"""
Compression Breakout Entry Rules
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from core.models.market_context import MarketContext


class EntryRules:
    """Entry rules for compression breakout"""
    
    @staticmethod
    def check_compression_setup(context: MarketContext) -> bool:
        """Was the market compressed?"""
        atr_percentile = context.volatility.get('atr_percentile', 50)
        return atr_percentile <= 30
    
    @staticmethod
    def check_expansion_started(context: MarketContext) -> bool:
        """Is volatility starting to expand?"""
        expansion = context.volatility.get('expansion_probability', 50)
        spike = context.volatility.get('spike_detected', False)
        return expansion >= 60 or spike
    
    @staticmethod
    def check_direction_clear(context: MarketContext) -> bool:
        """Is the direction clear?"""
        direction = context.trend.get('direction', 'NONE')
        strength = context.trend.get('strength', 0)
        return direction != 'NONE' and strength >= 50
    
    @staticmethod
    def check_mtf_aligned(context: MarketContext) -> bool:
        """Is MTF aligned?"""
        alignment = context.mtf.get('alignment_score', 0)
        conflict = context.mtf.get('htf_ltf_conflict', False)
        return alignment >= 70 and not conflict
