"""
Core Model: Signal

Trading signal output (final decision from execution gate).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class SignalAction(Enum):
    """Trading action types"""
    CALL = "CALL"           # Bullish entry
    PUT = "PUT"             # Bearish entry
    NO_SIGNAL = "NO_SIGNAL" # No action
    BLOCKED = "BLOCKED"     # Signal blocked by risk gate


class SignalQuality(Enum):
    """Signal quality tiers"""
    PREMIUM = "PREMIUM"     # Highest quality (90-100)
    HIGH = "HIGH"           # High quality (75-89)
    MEDIUM = "MEDIUM"       # Medium quality (60-74)
    LOW = "LOW"             # Low quality (<60)


@dataclass(frozen=True)
class Signal:
    """
    Final trading signal from the system.
    
    This is the OUTPUT of the entire pipeline (Context -> Score -> Strategy -> Gate).
    """
    
    # Identification
    signal_id: str
    timestamp: datetime
    symbol: str
    timeframe: str
    
    # Action
    action: SignalAction
    
    # Quality
    confidence: int                     # 0-100
    quality: SignalQuality
    
    # Metadata
    strategy_name: str                  # Which strategy generated this
    reason: str                         # Human-readable reason
    
    # Risk info
    blocked_by: Optional[str] = None    # Reason for block (if BLOCKED)
    veto_reason: Optional[str] = None   # Veto reason
    
    # Context snapshot
    context_snapshot: Dict[str, Any] = field(default_factory=dict)
    score_snapshot: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"Confidence must be 0-100, got {self.confidence}")
    
    @property
    def is_actionable(self) -> bool:
        """Can this signal be acted upon?"""
        return self.action in (SignalAction.CALL, SignalAction.PUT)
    
    @property
    def is_blocked(self) -> bool:
        return self.action == SignalAction.BLOCKED
    
    @property
    def is_premium(self) -> bool:
        return self.quality == SignalQuality.PREMIUM
    
    def to_dict(self) -> dict:
        return {
            'signal_id': self.signal_id,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'action': self.action.value,
            'confidence': self.confidence,
            'quality': self.quality.value,
            'strategy_name': self.strategy_name,
            'reason': self.reason,
            'blocked_by': self.blocked_by,
            'veto_reason': self.veto_reason,
        }
