"""
Market Context
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Unified market data object consumed by all intelligence engines.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime


@dataclass
class MarketContext:
    """Unified market context for all engines."""
    
    symbol: str = ""
    timestamp: Optional[datetime] = None
    candles: List = field(default_factory=list)
    current_price: float = 0.0
    
    # Intelligence outputs
    market_state: str = "UNKNOWN"
    market_volatility: float = 0.0
    noise_level: float = 0.0
    signal_conflict: float = 0.0
    
    @classmethod
    def build_from_candles(cls, candles: list, symbol: str, timeframe: str = "M5"):
        """Build MarketContext from candle data."""
        ctx = cls()
        ctx.symbol = symbol
        ctx.candles = candles
        ctx.timestamp = candles[-1].timestamp if candles else None
        ctx.current_price = candles[-1].close if candles else 0
        return ctx
