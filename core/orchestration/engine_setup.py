"""
Engine Setup

Central engine registration. Builds a populated EngineRegistry
with every analytical engine, registered under its correct tier.
"""

from core.orchestration.engine_registry import EngineRegistry

from core.orchestration.market_classifier.trend_engine import TrendEngine
from core.orchestration.market_classifier.strength_engine import StrengthEngine
from core.orchestration.market_classifier.volatility_engine import VolatilityEngine
from core.orchestration.market_classifier.structure_engine import StructureEngine
from core.orchestration.market_classifier.mtf_engine import MTFEngine
from core.orchestration.market_classifier.market_state_classifier import MarketStateClassifier
from core.orchestration.market_classifier.regime_quality_scorer import RegimeQualityScorer
from core.orchestration.advanced_tools.candle_pattern_analyzer import CandlePatternAnalyzer
from core.orchestration.advanced_tools.price_action_handler import PriceActionHandler
from core.orchestration.trap_detector import TrapDetector
from core.orchestration.noise_detector import NoiseDetector
from core.orchestration.liquidity_engine import LiquidityEngine
from core.orchestration.advanced_tools.divergence_analyzer import DivergenceAnalyzer
from core.orchestration.advanced_tools.transition_analyzer import TransitionAnalyzer
from core.orchestration.advanced_tools.conflict_analyzer import ConflictAnalyzer
from core.orchestration.advanced_tools.efficiency_analyzer import EfficiencyAnalyzer
from core.orchestration.advanced_tools.persistence_analyzer import PersistenceAnalyzer
from core.orchestration.advanced_tools.continuation_analyzer import ContinuationAnalyzer
from core.orchestration.market_classifier.market_pressure_analyzer import MarketPressureAnalyzer
from core.orchestration.anomaly_detector import AnomalyDetector
from core.orchestration.context_synthesizer import ContextSynthesizer
from core.orchestration.probability_estimator import ProbabilityEstimator
from core.scoring.signal_quality_scorer import SignalQualityScorer
from core.scoring.confidence_framework import ConfidenceFramework
from core.orchestration.explainability_engine import ExplainabilityEngine
from core.orchestration.market_classifier.market_structure_engine import MarketStructureEngine

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
