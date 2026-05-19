"""
Data Source Interface
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Abstract interface for candle data sources.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict
import pandas as pd


class IDataSource(ABC):
    """
    Interface for any data source (live broker, historical, dummy).
    """
    
    @abstractmethod
    def get_candles(self, symbol: str, timeframe: str, 
                   count: int = 200) -> pd.DataFrame:
        """
        Get recent candles for symbol.
        
        Args:
            symbol: Trading pair e.g. 'EURUSD'
            timeframe: 'M1', 'M5', 'M15', 'M60', 'D1'
            count: Number of candles
        
        Returns:
            DataFrame with [open, high, low, close, volume] indexed by datetime
        """
        pass
    
    @abstractmethod
    def get_multi_timeframe(self, symbol: str, 
                           timeframes: list, 
                           count: int = 200) -> Dict[str, pd.DataFrame]:
        """Get candles for multiple timeframes"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if data source is connected"""
        pass
