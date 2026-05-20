"""
FINALBOT - Main Entry Point
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Wires together all components and runs the pipeline.

Usage:
    python main.py
"""

import sys
from datetime import datetime

from core.data.dummy_data import DummyDataSource
from core.engines.engine_registry import EngineRegistry

# Tier 1
from core.engines.trend_engine import TrendEngine
from core.engines.strength_engine import StrengthEngine
from core.engines.volatility_engine import VolatilityEngine
from core.engines.structure_engine import StructureEngine
from core.engines.mtf_engine import MTFEngine

# Tier 2
from core.engines.market_state_classifier import MarketStateClassifier
from core.engines.regime_quality_scorer import RegimeQualityScorer

# Tier 3
from core.engines.candle_pattern_analyzer import CandlePatternAnalyzer
from core.engines.price_action_handler import PriceActionHandler

# Tier 4
from core.engines.trap_detector import TrapDetector
from core.engines.noise_detector import NoiseDetector
from core.engines.liquidity_engine import LiquidityEngine
from core.engines.divergence_analyzer import DivergenceAnalyzer

# Tier 5
from core.engines.transition_analyzer import TransitionAnalyzer
from core.engines.conflict_analyzer import ConflictAnalyzer
from core.engines.efficiency_analyzer import EfficiencyAnalyzer
from core.engines.persistence_analyzer import PersistenceAnalyzer
from core.engines.continuation_analyzer import ContinuationAnalyzer
from core.engines.market_pressure_analyzer import MarketPressureAnalyzer
from core.engines.anomaly_detector import AnomalyDetector

# Orchestration
from core.orchestration.context_builder import ContextBuilder
from core.orchestration.pipeline import Pipeline
from core.orchestration.execution_gate import ExecutionGate

# Strategy
from strategy.compression_breakout.strategy import CompressionBreakoutStrategy


def setup_engines() -> EngineRegistry:
    """Create and register all engines"""
    registry = EngineRegistry()
    
    # Tier 1: Foundation
    registry.register(TrendEngine())
    registry.register(StrengthEngine())
    registry.register(VolatilityEngine())
    registry.register(StructureEngine())
    registry.register(MTFEngine())
    
    # Tier 2: Classification
    registry.register(MarketStateClassifier())
    registry.register(RegimeQualityScorer())
    
    # Tier 3: Price Action
    registry.register(CandlePatternAnalyzer())
    registry.register(PriceActionHandler())
    
    # Tier 4: Detection
    registry.register(TrapDetector())
    registry.register(NoiseDetector())
    registry.register(LiquidityEngine())
    registry.register(DivergenceAnalyzer())
    
    # Tier 5: Behavior
    registry.register(TransitionAnalyzer())
    registry.register(ConflictAnalyzer())
    registry.register(EfficiencyAnalyzer())
    registry.register(PersistenceAnalyzer())
    registry.register(ContinuationAnalyzer())
    registry.register(MarketPressureAnalyzer())
    registry.register(AnomalyDetector())
    
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
    print("  PHASE 0-2: Core + Tier 1-5 Engines (20 engines)")
    print("=" * 70)
    print()
    
    print("⚙️  Setting up engines...")
    registry = setup_engines()
    print(f"   Registered {registry.count()} engines across tiers {registry.list_tiers()}")
    
    print("⚙️  Setting up pipeline...")
    pipeline = setup_pipeline(registry)
    
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
        
        signal = pipeline.execute(symbol, candles, timeframe='M5')
        
        print(f"  Signal ID:  {signal.signal_id}")
        print(f"  Action:     {signal.action.value}")
        print(f"  Quality:    {signal.quality.value}")
        print(f"  Confidence: {signal.confidence}%")
        print(f"  Strategy:   {signal.strategy_name}")
        print(f"  Reason:     {signal.reason}")
        if signal.veto_reason:
            print(f"  Vetoed by:  {signal.veto_reason}")
    
    print("\n" + "=" * 70)
    print("  ✅ Pipeline execution complete")
    print("=" * 70)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
