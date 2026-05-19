"""
Engine Registry
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Central registry that maps engine names to instances.
Used by orchestration to find and execute engines.
"""

from typing import Dict, Optional, List
from core.engines.base_engine import BaseEngine


class EngineRegistry:
    """
    Registry of all engines in the system.
    Each tier registers its engines here.
    """
    
    def __init__(self):
        self._engines: Dict[str, BaseEngine] = {}
        self._tier_map: Dict[int, List[str]] = {}
    
    def register(self, engine: BaseEngine) -> None:
        """Register an engine"""
        name = engine.engine_name
        tier = engine.tier
        
        self._engines[name] = engine
        
        if tier not in self._tier_map:
            self._tier_map[tier] = []
        if name not in self._tier_map[tier]:
            self._tier_map[tier].append(name)
    
    def get(self, name: str) -> Optional[BaseEngine]:
        """Get engine by name"""
        return self._engines.get(name)
    
    def get_by_tier(self, tier: int) -> List[BaseEngine]:
        """Get all engines in a tier"""
        names = self._tier_map.get(tier, [])
        return [self._engines[n] for n in names if n in self._engines]
    
    def list_engines(self) -> List[str]:
        """List all registered engine names"""
        return list(self._engines.keys())
    
    def list_tiers(self) -> List[int]:
        """List all tiers that have engines"""
        return sorted(self._tier_map.keys())
    
    def count(self) -> int:
        return len(self._engines)
    
    def __contains__(self, name: str) -> bool:
        return name in self._engines
