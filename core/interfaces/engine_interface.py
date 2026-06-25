"""
Interface: Engine

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
    
    def validate_input(self, payload: Any) -> bool:
        """Common input validation"""
        if payload is None:
            return False
        if isinstance(payload, pd.DataFrame):
            return not payload.empty
        if isinstance(payload, dict):
            return bool(payload)
        return True
