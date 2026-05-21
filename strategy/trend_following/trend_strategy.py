"""
Trend Following Strategy (V3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EMA-based trend following strategy.
"""

import logging
from typing import Optional
from core.models import MarketContext, Signal
from strategy.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class TrendFollowingStrategy(BaseStrategy):
    """
    Follow established trends with EMA confirmation.
    
    Entry Signals:
    - EMA alignment (all uptrend or downtrend)
    - Price above/below middle EMA
    - Trend strength confirmed
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Trend Following V3"
        self.version = "3.0"
        self.min_confidence = 50
    
    def analyze(self, context: MarketContext) -> Optional[Signal]:
        """Analyze trend following opportunities."""
        
        if not context or not context.candles or len(context.candles) < 50:
            return None
        
        try:
            # Calculate EMAs
            candles = context.candles[-50:]
            closes = [c.close for c in candles]
            
            ema9 = self._calculate_ema(closes, 9)
            ema21 = self._calculate_ema(closes, 21)
            ema55 = self._calculate_ema(closes, 55)
            current = closes[-1]
            
            # Detect trend
            entry_score = 0
            block_score = 0
            direction = None
            reason = ""
            
            # Uptrend: EMA9 > EMA21 > EMA55, price > EMA9
            if ema9 > ema21 > ema55 and current > ema9:
                strength = min(80, 40 + (current - ema55) / (ema55) * 100)
                entry_score = strength
                direction = "CALL"
                reason = f"Uptrend confirmed (EMA stack, strength: {strength:.0f}%)"
            
            # Downtrend: EMA9 < EMA21 < EMA55, price < EMA9
            elif ema9 < ema21 < ema55 and current < ema9:
                strength = min(80, 40 + (ema55 - current) / ema55 * 100)
                entry_score = strength
                direction = "PUT"
                reason = f"Downtrend confirmed (EMA stack, strength: {strength:.0f}%)"
            
            else:
                return Signal("NO_SIGNAL", 0)
            
            # Block conditions
            if context.market_state == "CHOPPY":
                block_score = 75
                reason += " [CHOPPY_BLOCK]"
            
            if context.noise_level and context.noise_level > 70:
                block_score = 65
                reason += " [HIGH_NOISE_BLOCK]"
            
            # Final confidence
            confidence = int(entry_score * (1 - block_score / 100))
            confidence = max(0, min(100, confidence))
            
            if confidence < self.min_confidence:
                return Signal("NO_SIGNAL", 0)
            
            signal = Signal(direction, confidence, reason=reason)
            logger.info(f"✅ {self.name}: {direction} @ {confidence}% - {reason}")
            return signal
            
        except Exception as e:
            logger.error(f"❌ {self.name} error: {e}")
            return Signal("NO_SIGNAL", 0)
    
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
