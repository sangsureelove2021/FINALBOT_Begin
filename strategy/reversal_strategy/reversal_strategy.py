"""
Reversal Strategy (V2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mean reversion strategy detecting bottom/top reversals.
"""

import logging
from typing import Optional, Dict, Any
from core.models import MarketContext
from strategy.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class ReversalStrategy(BaseStrategy):
    """
    Detect reversal patterns at support/resistance levels.
    """
    
    def __init__(self):
        self.name = "Reversal Pattern V2"
        self.version = "2.0"
    
    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        """Analyze reversal opportunities."""
        
        if not context or not context.candles or len(context.candles) < 20:
            return {'action': 'NO_SIGNAL', 'confidence': 0}
        
        try:
            candles = context.candles[-20:]
            prices = [c.close for c in candles]
            high = max(prices[-10:])
            low = min(prices[-10:])
            current = prices[-1]
            
            range_val = high - low
            if range_val == 0:
                return {'action': 'NO_SIGNAL', 'confidence': 0}
            
            extremeness = abs(current - (high + low) / 2) / range_val * 100
            action = 'NO_SIGNAL'
            confidence = 0
            reason = ""
            
            # Bottom reversal
            if current <= low + range_val * 0.2 and extremeness > 30:
                action = 'CALL'
                confidence = min(75, int(40 + extremeness / 2))
                reason = f"Oversold reversal"
            
            # Top reversal
            elif current >= high - range_val * 0.2 and extremeness > 30:
                action = 'PUT'
                confidence = min(75, int(40 + extremeness / 2))
                reason = f"Overbought reversal"
            
            return {
                'action': action,
                'confidence': confidence,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"❌ {self.name} error: {e}")
            return {'action': 'NO_SIGNAL', 'confidence': 0}
