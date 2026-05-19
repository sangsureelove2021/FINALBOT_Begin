"""
Core Model: Candle
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Immutable candle data structure (OHLCV) for type safety.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Candle:
    """Immutable candle data structure (OHLCV)"""
    
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    spread: Optional[float] = None
    tick_count: Optional[int] = None
    
    def __post_init__(self):
        if self.high < self.low:
            raise ValueError(f"High ({self.high}) < Low ({self.low})")
        if self.high < max(self.open, self.close):
            raise ValueError(f"High ({self.high}) < max(open, close)")
        if self.low > min(self.open, self.close):
            raise ValueError(f"Low ({self.low}) > min(open, close)")
        if self.volume < 0:
            raise ValueError(f"Volume cannot be negative: {self.volume}")
    
    @property
    def body(self) -> float:
        return abs(self.close - self.open)
    
    @property
    def wick_upper(self) -> float:
        return self.high - max(self.open, self.close)
    
    @property
    def wick_lower(self) -> float:
        return min(self.open, self.close) - self.low
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        return self.close < self.open
    
    @property
    def is_doji(self) -> bool:
        total_range = self.high - self.low
        if total_range == 0:
            return False
        return self.body / total_range < 0.1
    
    @property
    def range(self) -> float:
        return self.high - self.low
    
    @property
    def mid(self) -> float:
        return (self.high + self.low) / 2
    
    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'spread': self.spread,
            'tick_count': self.tick_count,
        }
