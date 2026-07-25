"""
Signal model for data_evaluate pipeline.
Replaces backtrader dependency with plain dataclass.
"""
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional


class SignalAction(IntEnum):
    NONE = 0
    LONG = 1
    SHORT = 2
    LONG_EXIT = 3
    SHORT_EXIT = 4


class SignalQuality(IntEnum):
    F = 0
    D = 1
    C = 2
    B = 3
    A = 4
    A_PLUS = 5


@dataclass
class Signal:
    action: SignalAction = SignalAction.NONE
    quality: SignalQuality = SignalQuality.F
    confidence: float = 0.0
    reason: str = ""
    symbol: str = ""
    timestamp: Optional[str] = None
    metadata: dict = field(default_factory=dict)
