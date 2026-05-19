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
from core.engines.trend_engine import TrendEngine
from core.engines.strength_engine import StrengthEngine
from core.engines.volatility_engine import VolatilityEngine
from core.engines.structure_engine import StructureEngine
from core.engines.market_state_classifier import MarketStateClassifier
from core.orchestration.context_builder import ContextBuilder
from core.orchestration.pipeline import Pipeline
from core.orchestration.execution_gate import ExecutionGate
from strategy.compression_breakout.strategy import CompressionBreakoutStrategy


def setup_engines() -> EngineRegistry:
    """Create and register all engines"""
    registry = EngineRegistry()
    
    # Tier 1: Foundation
    registry.register(TrendEngine())
    registry.register(StrengthEngine())
    registry.register(VolatilityEngine())
    registry.register(StructureEngine())
    
    # Tier 2: Market State
    registry.register(MarketStateClassifier())
    
    # NOTE: Other tiers register here as they get implemented
    
    return registry


def setup_pipeline(registry: EngineRegistry) -> Pipeline:
    """Create the pipeline with all dependencies"""
    
    # Context builder
    context_builder = ContextBuilder(registry)
    
    # Strategies
    strategies = [
        CompressionBreakoutStrategy(),
    ]
    
    # Execution gate
    execution_gate = ExecutionGate(
        min_confidence=75,
        max_block_score=60,
    )
    
    # Pipeline
    pipeline = Pipeline(
        context_builder=context_builder,
        strategies=strategies,
        execution_gate=execution_gate,
    )
    
    return pipeline


def main():
    """Main entry point"""
    print("=" * 70)
    print("  FINALBOT - Market Intelligence Operating System")
    print("  Phase 0 - Core Skeleton + Tier 1 + Sample Strategy")
    print("=" * 70)
    print()
    
    # Setup
    print("⚙️  Setting up engines...")
    registry = setup_engines()
    print(f"   Registered {registry.count()} engines across tiers {registry.list_tiers()}")
    
    print("⚙️  Setting up pipeline...")
    pipeline = setup_pipeline(registry)
    
    # Get data
    print("📊 Loading dummy data...")
    data_source = DummyDataSource(seed=42)
    
    # Test pairs
    symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
    
    for symbol in symbols:
        print(f"\n━━━ Analyzing {symbol} ━━━")
        
        # Get multi-timeframe data
        candles = data_source.get_multi_timeframe(
            symbol,
            timeframes=['M1', 'M5', 'M15', 'M60'],
            count=250
        )
        
        # Execute pipeline
        signal = pipeline.execute(symbol, candles, timeframe='M5')
        
        # Display result
        print(f"  Signal ID: {signal.signal_id}")
        print(f"  Action:    {signal.action.value}")
        print(f"  Quality:   {signal.quality.value}")
        print(f"  Confidence: {signal.confidence}%")
        print(f"  Strategy:  {signal.strategy_name}")
        print(f"  Reason:    {signal.reason}")
        if signal.veto_reason:
            print(f"  Vetoed by: {signal.veto_reason}")
    
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
