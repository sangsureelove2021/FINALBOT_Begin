"""
Strategy Registry

Central registry of all available strategies.
"""

from typing import Dict, List, Optional
from strategy.base_strategy import BaseStrategy


class StrategyRegistry:
    """Registry of trading strategies"""
    
    def __init__(self):
        self._strategies: Dict[str, BaseStrategy] = {}
    
    def register(self, strategy: BaseStrategy) -> None:
        """Register a strategy"""
        self._strategies[strategy.strategy_name] = strategy
    
    def get(self, name: str) -> Optional[BaseStrategy]:
        return self._strategies.get(name)
    
    def list_all(self) -> List[BaseStrategy]:
        return list(self._strategies.values())
    
    def list_names(self) -> List[str]:
        return list(self._strategies.keys())
    
    def count(self) -> int:
        return len(self._strategies)
