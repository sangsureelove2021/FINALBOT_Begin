"""
Unit Tests - Engines
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tests that all engines run, return valid output, and handle bad input.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
from core.data.dummy_data import DummyDataSource


def test_tier1_engines():
    """Tier 1 engines produce valid output"""
    from core.engines.trend_engine import TrendEngine
    from core.engines.strength_engine import StrengthEngine
    from core.engines.volatility_engine import VolatilityEngine
    from core.engines.structure_engine import StructureEngine
    
    ds = DummyDataSource(seed=1)
    df = ds.get_candles('EURUSD', 'M5', 250)
    
    for Engine in [TrendEngine, StrengthEngine, VolatilityEngine, StructureEngine]:
        engine = Engine()
        result = engine.analyze(df)
        assert isinstance(result, dict), f"{Engine.__name__} must return dict"
        assert 'confidence' in result, f"{Engine.__name__} must include confidence"
        assert 0 <= result['confidence'] <= 100, f"{Engine.__name__} confidence out of range"
    print("  PASS: test_tier1_engines")


def test_engine_neutral_state_on_bad_input():
    """Engines return neutral state on empty/bad input"""
    from core.engines.trend_engine import TrendEngine
    
    engine = TrendEngine()
    # Empty dataframe
    result = engine.analyze(pd.DataFrame())
    assert isinstance(result, dict)
    assert result['confidence'] == 0
    print("  PASS: test_engine_neutral_state_on_bad_input")


def test_confidence_never_exceeds_100():
    """All engine confidence values must be 0-100"""
    from main import setup_engines
    from core.orchestration.context_builder import ContextBuilder
    
    registry = setup_engines()
    cb = ContextBuilder(registry)
    ds = DummyDataSource(seed=7)
    candles = ds.get_multi_timeframe('EURUSD', ['M1','M5','M15','M60'], 250)
    ctx = cb.build('EURUSD', candles, 'M5')
    
    for field_name in ['trend','strength','volatility','structure','mtf',
                       'market_state','synthesized_context','signal_quality',
                       'confidence_framework']:
        data = getattr(ctx, field_name)
        if isinstance(data, dict) and 'confidence' in data:
            c = data['confidence']
            assert 0 <= c <= 100, f"{field_name} confidence={c} out of range"
    print("  PASS: test_confidence_never_exceeds_100")


def test_all_engines_execute_without_errors():
    """Full context build produces no errors"""
    from main import setup_engines
    from core.orchestration.context_builder import ContextBuilder
    
    registry = setup_engines()
    cb = ContextBuilder(registry)
    ds = DummyDataSource(seed=3)
    candles = ds.get_multi_timeframe('EURUSD', ['M1','M5','M15','M60'], 250)
    ctx = cb.build('EURUSD', candles, 'M5')
    
    assert len(ctx.errors) == 0, f"Errors found: {ctx.errors}"
    assert len(ctx.engines_executed) == 25, f"Expected 25 engines, got {len(ctx.engines_executed)}"
    print("  PASS: test_all_engines_execute_without_errors")


if __name__ == '__main__':
    print("Running engine tests...")
    test_tier1_engines()
    test_engine_neutral_state_on_bad_input()
    test_confidence_never_exceeds_100()
    test_all_engines_execute_without_errors()
    print("✅ All engine tests passed")
