"""
Engine Setup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Central engine registration. Builds a populated EngineRegistry
with every analytical engine, registered under its correct tier.
"""

from core.engines.engine_registry import EngineRegistry

from core.engines.trend_engine import TrendEngine
from core.engines.strength_engine import StrengthEngine
from core.engines.volatility_engine import VolatilityEngine
from core.engines.structure_engine import StructureEngine
from core.engines.mtf_engine import MTFEngine
from core.engines.market_state_classifier import MarketStateClassifier
from core.engines.regime_quality_scorer import RegimeQualityScorer
from core.engines.candle_pattern_analyzer import CandlePatternAnalyzer
from core.engines.price_action_handler import PriceActionHandler
from core.engines.trap_detector import TrapDetector
from core.engines.noise_detector import NoiseDetector
from core.engines.liquidity_engine import LiquidityEngine
from core.engines.divergence_analyzer import DivergenceAnalyzer
from core.engines.transition_analyzer import TransitionAnalyzer
from core.engines.conflict_analyzer import ConflictAnalyzer
from core.engines.efficiency_analyzer import EfficiencyAnalyzer
from core.engines.persistence_analyzer import PersistenceAnalyzer
from core.engines.continuation_analyzer import ContinuationAnalyzer
from core.engines.market_pressure_analyzer import MarketPressureAnalyzer
from core.engines.anomaly_detector import AnomalyDetector
from core.engines.context_synthesizer import ContextSynthesizer
from core.engines.probability_estimator import ProbabilityEstimator
from core.engines.signal_quality_scorer import SignalQualityScorer
from core.engines.confidence_framework import ConfidenceFramework
from core.engines.explainability_engine import ExplainabilityEngine
from core.engines.market_structure_engine import MarketStructureEngine

# All analytical engines, in tier order
ENGINE_CLASSES = [
    TrendEngine, StrengthEngine, VolatilityEngine, StructureEngine, MTFEngine, MarketStructureEngine,
    MarketStateClassifier, RegimeQualityScorer,
    CandlePatternAnalyzer, PriceActionHandler,
    TrapDetector, NoiseDetector, LiquidityEngine, DivergenceAnalyzer,
    TransitionAnalyzer, ConflictAnalyzer, EfficiencyAnalyzer,
    PersistenceAnalyzer, ContinuationAnalyzer, MarketPressureAnalyzer,
    AnomalyDetector,
    ContextSynthesizer, ProbabilityEstimator,
    SignalQualityScorer, ConfidenceFramework,
    ExplainabilityEngine,
]


def setup_engines(config: dict = None) -> EngineRegistry:
    """
    Build and return a fully populated EngineRegistry.

    Args:
        config: optional shared config passed to each engine.

    Returns:
        EngineRegistry with all engines registered under their tier.
    """
    registry = EngineRegistry()
    for cls in ENGINE_CLASSES:
        try:
            engine = cls(config) if config else cls()
            registry.register(engine)
        except Exception as e:
            print(f"WARN: could not register {cls.__name__}: {e}")
    return registry
