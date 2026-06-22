"""
Core Model: Engine Output

Standard output schema that every engine returns.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class EngineOutput:
    """
    Standard output from any engine in the system.
    
    Every engine must return data in this shape for consistency.
    """
    
    # Identification
    engine_name: str                    # e.g. 'trend_engine'
    engine_version: str                 # e.g. '1.0.0'
    timestamp: datetime                 # When analysis was performed
    
    # Data
    data: Dict[str, Any]                # Engine-specific output data
    
    # Quality metrics
    confidence: int                     # 0-100, how confident this output is
    
    # Optional
    warnings: tuple = field(default_factory=tuple)    # Non-fatal warnings
    error: Optional[str] = None         # Error message if engine failed
    execution_time_ms: Optional[float] = None  # How long it took
    
    def __post_init__(self):
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be 0-100, got {self.confidence}")
    
    @property
    def is_valid(self) -> bool:
        """Check if output is valid (no errors)"""
        return self.error is None
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if confidence is high (>= 70)"""
        return self.confidence >= 70
    
    def to_dict(self) -> dict:
        return {
            'engine_name': self.engine_name,
            'engine_version': self.engine_version,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data,
            'confidence': self.confidence,
            'warnings': list(self.warnings),
            'error': self.error,
            'execution_time_ms': self.execution_time_ms,
        }
