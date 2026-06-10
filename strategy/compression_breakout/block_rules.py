"""
Compression Breakout Block Rules

"""

from typing import Tuple
from core.models.market_context import MarketContext


class BlockRules:
    """Rules that BLOCK breakout entry"""
    
    @staticmethod
    def has_trap(context: MarketContext) -> Tuple[bool, str]:
        if context.traps.get('trap_detected'):
            return True, "Trap detected"
        return False, ""
    
    @staticmethod
    def has_high_noise(context: MarketContext) -> Tuple[bool, str]:
        noise = context.noise.get('noise_level', 0)
        if noise > 65:
            return True, f"High noise: {noise}"
        return False, ""
    
    @staticmethod
    def has_exhaustion(context: MarketContext) -> Tuple[bool, str]:
        exh = context.strength.get('exhaustion_risk', 0)
        if exh > 70:
            return True, f"Exhaustion risk: {exh}"
        return False, ""
    
    @staticmethod
    def has_anomaly(context: MarketContext) -> Tuple[bool, str]:
        if context.anomaly.get('anomaly_detected'):
            return True, "Anomaly detected"
        return False, ""
    
    @staticmethod
    def has_extreme_volatility(context: MarketContext) -> Tuple[bool, str]:
        regime = context.volatility.get('regime', 'NORMAL')
        if regime == 'EXTREME':
            return True, "Extreme volatility"
        return False, ""
