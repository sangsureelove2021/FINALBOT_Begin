"""
Market Context
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Unified market data object consumed by all intelligence engines.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime
import pandas as pd


@dataclass
class MarketContext:
    """Unified market context for all engines."""
    
    symbol: str = ""
    timestamp: Optional[datetime] = None
    timeframe: str = "M5"
    candles: Dict = field(default_factory=dict)  # Store dict of {timeframe: DataFrame}
    current_price: float = 0.0
    candle_index: int = 0
    
    # Intelligence outputs
    market_state: str = "UNKNOWN"
    market_volatility: float = 0.0
    noise_level: float = 0.0
    signal_conflict: float = 0.0
    
    # Scoring
    _scores: Dict = field(default_factory=dict)
    aggregated_score: float = 0.0
    strategy_recommendation: Dict = field(default_factory=dict)
    execution_decision: Dict = field(default_factory=dict)
    
    def set_score(self, key: str, value: float) -> None:
        """Set a score."""
        self._scores[key] = value
    
    def get_score(self, key: str) -> float:
        """Get a score."""
        return self._scores.get(key, 0.0)
    
    def has_errors(self) -> bool:
        """Check if context has errors."""
        return False  # TODO: Implement error tracking
    
    def add_warning(self, msg: str) -> None:
        """Add a warning."""
        pass  # TODO: Implement warning tracking
    
    
    @classmethod
    def build_from_candles(cls, symbol: str, candles_dict: Dict[str, pd.DataFrame], 
                          engines: List = None, timeframe: str = "M5"):
        """Build MarketContext from multi-timeframe candle data."""
        ctx = cls()
        ctx.symbol = symbol
        ctx.candles = candles_dict
        
        primary_df = candles_dict.get(timeframe)
        if primary_df is None or primary_df.empty:
            ctx.timestamp = None
            ctx.current_price = 0.0
            return ctx
        
        # Convert pandas index (Timestamp) to datetime
        try:
            last_ts = primary_df.index[-1]
            if isinstance(last_ts, str):
                ctx.timestamp = pd.Timestamp(last_ts).to_pydatetime()
            else:
                ctx.timestamp = pd.Timestamp(last_ts).to_pydatetime()
        except Exception as e:
            ctx.timestamp = datetime.utcnow()
        
        ctx.current_price = float(primary_df['close'].iloc[-1])
        return ctx
