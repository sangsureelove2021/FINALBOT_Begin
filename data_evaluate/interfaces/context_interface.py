"""
Interface: Context

Abstract interface for context building.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd
from data_evaluate.models.market_context import MarketContext


class IContextBuilder(ABC):
    """Interface for building MarketContext from candle data"""
    
    @abstractmethod
    def build(self, symbol: str, candles: Dict[str, pd.DataFrame], 
              timeframe: str) -> MarketContext:
        """Build a complete MarketContext"""
        pass
