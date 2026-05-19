"""
Interface: Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Abstract interface that every engine must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd


class IEngine(ABC):
    """
    Abstract interface for all engines.
    
    Every engine in the system must implement this interface
    to ensure consistent behavior and pluggability.
    """
    
    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Unique name for this engine"""
        pass
    
    @property
    @abstractmethod
    def engine_version(self) -> str:
        """Version of this engine"""
        pass
    
    @property
    @abstractmethod
    def tier(self) -> int:
        """Tier number (1-8)"""
        pass
    
    @abstractmethod
    def analyze(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Main analysis method.
        
        Must return a dictionary with engine-specific output.
        Must NEVER raise exceptions - return neutral state on error.
        """
        pass
    
    @abstractmethod
    def get_neutral_state(self) -> Dict[str, Any]:
        """
        Return safe neutral state when engine cannot analyze.
        Used when data is insufficient or errors occur.
        """
        pass
    
    def validate_input(self, candles_df: pd.DataFrame, min_candles: int = 100) -> bool:
        """Common input validation"""
        if candles_df is None or candles_df.empty:
            return False
        if len(candles_df) < min_candles:
            return False
        required = ['open', 'high', 'low', 'close']
        return all(col in candles_df.columns for col in required)
