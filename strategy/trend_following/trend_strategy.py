"""
Trend Following Strategy (V3)

EMA-based trend following strategy.
"""

import logging
from typing import Dict, Any
from core.models import MarketContext
from strategy.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class TrendFollowingStrategy(BaseStrategy):
    """
    Follow established trends with EMA confirmation.
    """
    
    def __init__(self):
        self.name = "Trend Following V3"
        self.version = "3.0"
    
    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        """Analyze trend following opportunities."""
        
        if not context or not context.candles or len(context.candles) < 50:
            return {'action': 'NO_SIGNAL', 'confidence': 0}
        
        try:
            candles = context.candles[-50:]
            closes = [c.close for c in candles]
            
            ema9 = self._calculate_ema(closes, 9)
            ema21 = self._calculate_ema(closes, 21)
            ema55 = self._calculate_ema(closes, 55)
            current = closes[-1]
            
            action = 'NO_SIGNAL'
            confidence = 0
            reason = ""
            
            # Uptrend
            if ema9 > ema21 > ema55 and current > ema9:
                strength = min(80, int(40 + (current - ema55) / ema55 * 100))
                action = 'CALL'
                confidence = strength
                reason = f"Uptrend confirmed"
            
            # Downtrend
            elif ema9 < ema21 < ema55 and current < ema9:
                strength = min(80, int(40 + (ema55 - current) / ema55 * 100))
                action = 'PUT'
                confidence = strength
                reason = f"Downtrend confirmed"
            
            return {
                'action': action,
                'confidence': confidence,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f" {self.name} error: {e}")
            return {'action': 'NO_SIGNAL', 'confidence': 0}
    
    @staticmethod
    def _calculate_ema(values, period):
        """Simple EMA calculation."""
        if len(values) < period:
            return sum(values) / len(values)
        
        multiplier = 2 / (period + 1)
        ema = sum(values[:period]) / period
        
        for i in range(period, len(values)):
            ema = values[i] * multiplier + ema * (1 - multiplier)
        
        return ema
