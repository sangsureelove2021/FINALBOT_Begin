"""
Core Model: Score

Score representation for scoring pipeline.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class Score:
    """Single score value with metadata"""
    
    name: str                       # Score name (e.g. 'trend_strength')
    value: float                    # Score value 0-100
    weight: float = 1.0             # Weight in aggregation
    confidence: int = 100           # 0-100
    source: Optional[str] = None    # Which engine produced this
    
    def __post_init__(self):
        if not 0 <= self.value <= 100:
            raise ValueError(f"Score value must be 0-100, got {self.value}")
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be 0-100, got {self.confidence}")
        if self.weight < 0:
            raise ValueError(f"Weight cannot be negative: {self.weight}")
    
    @property
    def weighted_value(self) -> float:
        """Score value × weight"""
        return self.value * self.weight
    
    @property
    def is_high(self) -> bool:
        return self.value >= 70
    
    @property
    def is_low(self) -> bool:
        return self.value <= 30


@dataclass(frozen=True)
class ScoreSet:
    """Collection of scores"""
    
    scores: Dict[str, Score]
    aggregated: float = 0.0
    total_weight: float = 0.0
    
    def get(self, name: str) -> Optional[Score]:
        return self.scores.get(name)
    
    def get_value(self, name: str, default: float = 0.0) -> float:
        score = self.scores.get(name)
        return score.value if score else default
    
    @property
    def count(self) -> int:
        return len(self.scores)
