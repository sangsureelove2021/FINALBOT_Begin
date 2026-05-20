"""
FINALBOT - Main Entry Point
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Wires together all components and runs the pipeline.
PHASE 0-3 Complete: Core + Tier 1-8 + Risk Gate

Usage:
    python main.py
"""

import sys
from datetime import datetime

from core.data.dummy_data import DummyDataSource
from core.engines.engine_registry import EngineRegistry

# Tier 1: Foundation
from core.engines.trend_engine import TrendEngine
from core.engines.strength_engine import StrengthEngine
from core.engines.volatility_engine import VolatilityEngine
from core.engines.structure_engine import StructureEngine
from core.engines.mtf_engine import MTFEngine

# Tier 2: Classification
from core.engines.market_state_classifier import MarketStateClassifier
from core.engines.regime_quality_scorer import RegimeQualityScorer

# Tier 3: Price Action
from core.engines.candle_pattern_analyzer import CandlePatternAnalyzer
from core.engines.price_action_handler import PriceActionHandler

# Tier 4: Detection
from core.engines.trap_detector import TrapDetector
from core.engines.noise_detector import NoiseDetector
from core.engines.liquidity_engine import LiquidityEngine
from core.engines.divergence_analyzer import DivergenceAnalyzer

# Tier 5: Behavior
from core.engines.transition_analyzer import TransitionAnalyzer
from core.engines.conflict_analyzer import ConflictAnalyzer
from core.engines.efficiency_analyzer import EfficiencyAnalyzer
from core.engines.persistence_analyzer import PersistenceAnalyzer
from core.engines.continuation_analyzer import ContinuationAnalyzer
from core.engines.market_pressure_analyzer import MarketPressureAnalyzer
from core.engines.anomaly_detector import AnomalyDetector

# Tier 6: Synthesis
from core.engines.context_synthesizer import ContextSynthesizer
from core.engines.probability_estimator import ProbabilityEstimator

# Tier 7: Quality
from core.engines.signal_quality_scorer import SignalQualityScorer
from core.engines.confidence_framework import ConfidenceFramework

# Tier 8: Utilities
from core.engines.explainability_engine import ExplainabilityEngine
from core.engines.performance_tracker import PerformanceTracker

# Orchestration
from core.orchestration.context_builder import ContextBuilder
from core.orchestration.pipeline import Pipeline
from core.orchestration.execution_gate import ExecutionGate

# Risk Gate
from execution.execution_guard import ExecutionGuard

# Strategy
from strategy.compression_breakout.strategy import CompressionBreakoutStrategy


def setup_engines() -> EngineRegistry:
    """Create and register all 24 engines across 8 tiers"""
    registry = EngineRegistry()
    
    # Tier 1: Foundation (5)
    registry.register(TrendEngine())
    registry.register(StrengthEngine())
    registry.register(VolatilityEngine())
    registry.register(StructureEngine())
    registry.register(MTFEngine())
    
    # Tier 2: Classification (2)
    registry.register(MarketStateClassifier())
    registry.register(RegimeQualityScorer())
    
    # Tier 3: Price Action (2)
    registry.register(CandlePatternAnalyzer())
    registry.register(PriceActionHandler())
    
    # Tier 4: Detection (4)
    registry.register(TrapDetector())
    registry.register(NoiseDetector())
    registry.register(LiquidityEngine())
    registry.register(DivergenceAnalyzer())
    
    # Tier 5: Behavior (7)
    registry.register(TransitionAnalyzer())
    registry.register(ConflictAnalyzer())
    registry.register(EfficiencyAnalyzer())
    registry.register(PersistenceAnalyzer())
    registry.register(ContinuationAnalyzer())
    registry.register(MarketPressureAnalyzer())
    registry.register(AnomalyDetector())
    
    # Tier 6: Synthesis (2)
    registry.register(ContextSynthesizer())
    registry.register(ProbabilityEstimator())
    
    # Tier 7: Quality (2)
    registry.register(SignalQualityScorer())
    registry.register(ConfidenceFramework())
    
    # Tier 8: Utilities (1 engine - PerformanceTracker is stateful, used separately)
    registry.register(ExplainabilityEngine())
    
    return registry


def setup_pipeline(registry: EngineRegistry) -> Pipeline:
    """Create the pipeline with all dependencies"""
    context_builder = ContextBuilder(registry)
    
    strategies = [
        CompressionBreakoutStrategy(),
    ]
    
    execution_gate = ExecutionGate(
        min_confidence=75,
        max_block_score=60,
    )
    
    return Pipeline(
        context_builder=context_builder,
        strategies=strategies,
        execution_gate=execution_gate,
    )


def main():
    """Main entry point"""
    print("=" * 70)
    print("  FINALBOT - Market Intelligence Operating System")
    print("  PHASE 0-3 COMPLETE: Core + Tier 1-8 + Risk Gate")
    print("=" * 70)
    print()
    
    print("⚙️  Setting up engines...")
    registry = setup_engines()
    print(f"   Registered {registry.count()} engines across tiers {registry.list_tiers()}")
    
    print("⚙️  Setting up pipeline...")
    pipeline = setup_pipeline(registry)
    
    print("⚙️  Setting up risk gate (ExecutionGuard)...")
    guard = ExecutionGuard(
        max_daily_loss=100.0,
        max_consecutive_losses=3,
        max_trades_per_session=20,
        min_confidence_to_execute=75,
    )
    
    print("⚙️  Setting up performance tracker...")
    tracker = PerformanceTracker()
    
    print("📊 Loading dummy data...")
    data_source = DummyDataSource(seed=42)
    
    symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
    
    for symbol in symbols:
        print(f"\n━━━ Analyzing {symbol} ━━━")
        
        candles = data_source.get_multi_timeframe(
            symbol,
            timeframes=['M1', 'M5', 'M15', 'M60'],
            count=250
        )
        
        # Pipeline produces signal
        signal = pipeline.execute(symbol, candles, timeframe='M5')
        
        # Risk gate final check
        guard_result = guard.check({
            'action': signal.action.value,
            'confidence': signal.confidence,
        })
        
        # Track signal
        tracker.record_signal({
            'action': signal.action.value,
            'confidence': signal.confidence,
            'quality': signal.quality.value,
            'symbol': symbol,
            'strategy_name': signal.strategy_name,
        })
        
        print(f"  Signal ID:   {signal.signal_id}")
        print(f"  Action:      {signal.action.value}")
        print(f"  Quality:     {signal.quality.value}")
        print(f"  Confidence:  {signal.confidence}%")
        print(f"  Strategy:    {signal.strategy_name}")
        print(f"  Reason:      {signal.reason}")
        print(f"  Risk Gate:   {'✅ ALLOWED' if guard_result['allowed'] else '🛑 VETOED'}")
        if not guard_result['allowed']:
            print(f"  Veto reason: {guard_result['reason']}")
    
    # Performance summary
    print(f"\n━━━ Performance Tracker ━━━")
    stats = tracker.get_statistics()
    print(f"  Total signals: {stats['total_signals']}")
    print(f"  Action breakdown: {stats['action_breakdown']}")
    print(f"  Avg confidence: {stats['average_confidence']}")
    
    print("\n" + "=" * 70)
    print("  ✅ Pipeline execution complete - ALL 8 TIERS OPERATIONAL")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
