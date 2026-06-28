"""
Base Engine

Base class with common functionality for all engines.
"""

import time
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import pandas as pd

from core.interfaces.engine_interface import IEngine
from core.models.engine_output import EngineOutput


class BaseEngine(IEngine):
    """
    Base class with common functionality for all engines.
    Provides timing, error handling, logging, and validation.
    """
    
    # Override these in subclasses
    ENGINE_NAME = "base_engine"
    ENGINE_VERSION = "1.0.0"
    TIER = 0
    MIN_CANDLES = 100
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._last_execution_time_ms: Optional[float] = None
    
    @property
    def engine_name(self) -> str:
        return self.ENGINE_NAME
    
    @property
    def engine_version(self) -> str:
        return self.ENGINE_VERSION
    
    @property
    def tier(self) -> int:
        return self.TIER
    
    def analyze(self, payload: Any, **kwargs) -> Dict[str, Any]:
        """
        Standard analyze entry point. Wraps _analyze with safety.
        """
        start_time = time.time()
        
        try:
            # Validate input
            if not self.validate_input(payload):
                raise ValueError("FAIL-FAST: Neutral state removed")
            
            # Run actual analysis
            result = self._analyze(payload, **kwargs)
            
            # Track timing
            self._last_execution_time_ms = (time.time() - start_time) * 1000
            
            return result
            
        except Exception as e:
            raise
    
    def _analyze(self, payload: Any, **kwargs) -> Dict[str, Any]:
        """
        Override this in subclasses.
        Contains the actual analysis logic.
        """
        raise NotImplementedError("Subclasses must implement _analyze()")
    
    
    def to_engine_output(self, data: Dict[str, Any], 
                        confidence: int = 50) -> EngineOutput:
        """Wrap data in standard EngineOutput format"""
        return EngineOutput(
            engine_name=self.engine_name,
            engine_version=self.engine_version,
            timestamp=datetime.now(timezone.utc),
            data=data,
            confidence=confidence,
            execution_time_ms=self._last_execution_time_ms,
        )
    
    @property
    def last_execution_time_ms(self) -> Optional[float]:
        return self._last_execution_time_ms
