"""
Interface: Strategy
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Abstract interface that every strategy must implement.

CRITICAL RULE: Strategies CANNOT contain market analysis logic.
Strategies only consume MarketContext and produce recommendations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from core.models.market_context import MarketContext
from core.models.signal import Signal


class IStrategy(ABC):
    """Interface for trading strategies"""
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Strategy name"""
        pass
    
    @property
    @abstractmethod
    def required_market_state(self) -> str:
        """Which market state this strategy targets"""
        pass
    
    @abstractmethod
    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        """
        Evaluate strategy against current context.
        
        Returns dict with:
            - 'action': 'CALL', 'PUT', or 'NO_SIGNAL'
            - 'confidence': 0-100
            - 'reason': str
            - 'entry_score': 0-100
            - 'block_score': 0-100 (higher = more reason to block)
        """
        pass
    
    @abstractmethod
    def is_eligible(self, context: MarketContext) -> bool:
        """Check if this strategy can run given current context"""
        pass
