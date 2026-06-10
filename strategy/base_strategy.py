"""
Base Strategy

Base class for all strategies.

CRITICAL: Strategies must NOT contain market analysis logic.
They only CONSUME MarketContext and produce recommendations.
"""

from abc import abstractmethod
from typing import Dict, Any
from core.interfaces.strategy_interface import IStrategy
from core.models.market_context import MarketContext


class BaseStrategy(IStrategy):
    """Base class for all strategies"""
    
    STRATEGY_NAME = "base_strategy"
    REQUIRED_MARKET_STATE = "any"
    MIN_CONFIDENCE = 70
    
    @property
    def strategy_name(self) -> str:
        return self.STRATEGY_NAME
    
    @property
    def required_market_state(self) -> str:
        return self.REQUIRED_MARKET_STATE
    
    def is_eligible(self, context: MarketContext) -> bool:
        """
        Default eligibility: check market state matches.
        Override for custom checks.
        """
        if self.REQUIRED_MARKET_STATE == "any":
            return True
        
        current_state = context.market_state.get('state', '').upper()
        required = self.REQUIRED_MARKET_STATE.upper()
        
        return current_state == required or required in current_state
    
    @abstractmethod
    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        """
        Evaluate strategy. Must return:
            - action: 'CALL', 'PUT', or 'NO_SIGNAL'
            - confidence: 0-100
            - reason: str
            - entry_score: 0-100
            - block_score: 0-100
        """
        pass
    
    def _no_signal(self, reason: str) -> Dict[str, Any]:
        """Helper to create no-signal response"""
        return {
            'action': 'NO_SIGNAL',
            'confidence': 0,
            'reason': reason,
            'entry_score': 0,
            'block_score': 100,
        }
