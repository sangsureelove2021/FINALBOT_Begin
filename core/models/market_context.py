"""
Core Model: Market Context
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Central shared context object. All engines read/write to MarketContext.
This is the HEART of the Intelligence OS.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List


@dataclass
class MarketContext:
    """
    Central market context object - the shared state used by all engines.
    
    Flow:
        Tier 1 engines populate: trend, strength, volatility, structure, mtf
        Tier 2 populates: market_state
        Tier 3 populates: price_action
        Tier 4 populates: detection (trap, noise, etc.)
        Tier 5 populates: behavior
        Tier 6 populates: synthesis, probabilities
        Tier 7 populates: quality scores
        Strategy reads ALL fields to make decisions
    """
    
    # === METADATA ===
    timestamp: datetime
    pair: str                           # e.g. 'EURUSD'
    timeframe: str                      # e.g. 'M5'
    current_price: float
    candle_index: int = 0
    
    # === TIER 1: Foundation (Filled by Tier 1 engines) ===
    trend: Dict[str, Any] = field(default_factory=dict)
    strength: Dict[str, Any] = field(default_factory=dict)
    volatility: Dict[str, Any] = field(default_factory=dict)
    structure: Dict[str, Any] = field(default_factory=dict)
    mtf: Dict[str, Any] = field(default_factory=dict)
    
    # === TIER 2: Market Classification ===
    market_state: Dict[str, Any] = field(default_factory=dict)
    regime_quality: Dict[str, Any] = field(default_factory=dict)
    
    # === TIER 3: Price Action ===
    candle_patterns: Dict[str, Any] = field(default_factory=dict)
    price_action: Dict[str, Any] = field(default_factory=dict)
    
    # === TIER 4: Detection ===
    traps: Dict[str, Any] = field(default_factory=dict)
    noise: Dict[str, Any] = field(default_factory=dict)
    liquidity: Dict[str, Any] = field(default_factory=dict)
    divergence: Dict[str, Any] = field(default_factory=dict)
    
    # === TIER 5: Behavior ===
    transition: Dict[str, Any] = field(default_factory=dict)
    conflict: Dict[str, Any] = field(default_factory=dict)
    efficiency: Dict[str, Any] = field(default_factory=dict)
    persistence: Dict[str, Any] = field(default_factory=dict)
    continuation: Dict[str, Any] = field(default_factory=dict)
    orderflow: Dict[str, Any] = field(default_factory=dict)
    anomaly: Dict[str, Any] = field(default_factory=dict)
    
    # === TIER 6: Synthesis ===
    synthesized_context: Dict[str, Any] = field(default_factory=dict)
    move_probability: Dict[str, Any] = field(default_factory=dict)
    
    # === TIER 7: Quality ===
    signal_quality: Dict[str, Any] = field(default_factory=dict)
    confidence_framework: Dict[str, Any] = field(default_factory=dict)
    explainability: Dict[str, Any] = field(default_factory=dict)
    
    # === SCORING ===
    scores: Dict[str, float] = field(default_factory=dict)
    aggregated_score: float = 0.0
    
    # === STRATEGY DECISIONS (filled by strategy layer) ===
    strategy_recommendation: Dict[str, Any] = field(default_factory=dict)
    
    # === EXECUTION GATE (filled by risk layer) ===
    execution_decision: Dict[str, Any] = field(default_factory=dict)
    
    # === TRACKING ===
    engines_executed: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def add_warning(self, message: str):
        """Add a warning message"""
        self.warnings.append(f"{datetime.utcnow().isoformat()}: {message}")
    
    def add_error(self, message: str):
        """Add an error message"""
        self.errors.append(f"{datetime.utcnow().isoformat()}: {message}")
    
    def mark_engine_executed(self, engine_name: str):
        """Track which engines have run"""
        if engine_name not in self.engines_executed:
            self.engines_executed.append(engine_name)
    
    def is_complete(self) -> bool:
        """Check if context has minimum required data"""
        return (
            bool(self.trend) and
            bool(self.strength) and
            bool(self.volatility)
        )
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def get_score(self, name: str, default: float = 0.0) -> float:
        """Get a score by name"""
        return self.scores.get(name, default)
    
    def set_score(self, name: str, value: float):
        """Set a score (validates 0-100)"""
        if not 0 <= value <= 100:
            raise ValueError(f"Score must be 0-100, got {value}")
        self.scores[name] = value
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'pair': self.pair,
            'timeframe': self.timeframe,
            'current_price': self.current_price,
            'candle_index': self.candle_index,
            'trend': self.trend,
            'strength': self.strength,
            'volatility': self.volatility,
            'structure': self.structure,
            'mtf': self.mtf,
            'market_state': self.market_state,
            'regime_quality': self.regime_quality,
            'candle_patterns': self.candle_patterns,
            'price_action': self.price_action,
            'traps': self.traps,
            'noise': self.noise,
            'liquidity': self.liquidity,
            'divergence': self.divergence,
            'transition': self.transition,
            'conflict': self.conflict,
            'efficiency': self.efficiency,
            'persistence': self.persistence,
            'continuation': self.continuation,
            'orderflow': self.orderflow,
            'anomaly': self.anomaly,
            'synthesized_context': self.synthesized_context,
            'move_probability': self.move_probability,
            'signal_quality': self.signal_quality,
            'confidence_framework': self.confidence_framework,
            'explainability': self.explainability,
            'scores': self.scores,
            'aggregated_score': self.aggregated_score,
            'strategy_recommendation': self.strategy_recommendation,
            'execution_decision': self.execution_decision,
            'engines_executed': self.engines_executed,
            'warnings': self.warnings,
            'errors': self.errors,
        }
