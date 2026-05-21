"""
Reversal Strategy (V2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mean reversion strategy detecting bottom/top reversals.
"""

import logging
from typing import Optional
from core.models import MarketContext, Signal
from strategy.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class ReversalStrategy(BaseStrategy):
    """
    Detect reversal patterns at support/resistance levels.
    
    Entry Signals:
    - Market at extreme (top/bottom)
    - Mean reversion probability high
    - Pullback confirmation present
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Reversal Pattern V2"
        self.version = "2.0"
        self.min_confidence = 55
    
    def analyze(self, context: MarketContext) -> Optional[Signal]:
        """Analyze reversal opportunities."""
        
        if not context or not context.candles or len(context.candles) < 20:
            return None
        
        try:
            # Get recent price action
            candles = context.candles[-20:]
            prices = [c.close for c in candles]
            
            # Detect extremes (support/resistance)
            high = max(prices[-10:])
            low = min(prices[-10:])
            current = prices[-1]
            
            # Calculate extremeness
            range_val = high - low
            if range_val == 0:
                return Signal("NO_SIGNAL", 0)
            
            extremeness = abs(current - (high + low) / 2) / range_val * 100
            
            # Check for reversal setup
            entry_score = 0
            block_score = 0
            reason = ""
            direction = None
            
            # Bottom reversal (oversold)
            if current <= low + range_val * 0.2 and extremeness > 30:
                entry_score = min(75, 40 + extremeness / 2)
                direction = "CALL"
                reason = f"Oversold reversal (extremeness: {extremeness:.0f}%)"
            
            # Top reversal (overbought)
            elif current >= high - range_val * 0.2 and extremeness > 30:
                entry_score = min(75, 40 + extremeness / 2)
                direction = "PUT"
                reason = f"Overbought reversal (extremeness: {extremeness:.0f}%)"
            
            else:
                return Signal("NO_SIGNAL", 0)
            
            # Block conditions
            if context.market_volatility and context.market_volatility > 80:
                block_score = 70
                reason += " [HIGH_VOLATILITY_BLOCK]"
            
            if context.signal_conflict and context.signal_conflict > 0.6:
                block_score = 60
                reason += " [CONFLICT_BLOCK]"
            
            # Generate signal
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
