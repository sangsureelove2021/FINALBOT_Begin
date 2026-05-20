"""
Integration Test - End to End Pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
from core.data.dummy_data import DummyDataSource


def test_pipeline_produces_signal():
    """Pipeline produces a valid Signal object"""
    from main import setup_engines, setup_pipeline
    from core.models.signal import Signal, SignalAction
    
    registry = setup_engines()
    pipeline = setup_pipeline(registry)
    ds = DummyDataSource(seed=42)
    candles = ds.get_multi_timeframe('EURUSD', ['M1','M5','M15','M60'], 250)
    
    signal = pipeline.execute('EURUSD', candles, 'M5')
    
    assert isinstance(signal, Signal)
    assert signal.action in SignalAction
    assert 0 <= signal.confidence <= 100
    print("  PASS: test_pipeline_produces_signal")


def test_pipeline_handles_empty_data():
    """Pipeline does not crash on empty data"""
    from main import setup_engines, setup_pipeline
    
    registry = setup_engines()
    pipeline = setup_pipeline(registry)
    
    signal = pipeline.execute('TEST', {'M5': pd.DataFrame()}, 'M5')
    assert signal is not None
    print("  PASS: test_pipeline_handles_empty_data")


def test_risk_gate_blocks_correctly():
    """ExecutionGuard blocks when limits hit"""
    from execution.execution_guard import ExecutionGuard
    
    guard = ExecutionGuard(max_consecutive_losses=2)
    
    # Simulate 2 losses
    guard.record_trade_result(won=False, profit_loss=-10)
    guard.record_trade_result(won=False, profit_loss=-10)
    
    result = guard.check({'action': 'CALL', 'confidence': 90})
    assert not result['allowed'], "Should block after consecutive losses"
    assert result['veto_code'] == 'consecutive_losses'
    print("  PASS: test_risk_gate_blocks_correctly")


def test_risk_gate_allows_good_signal():
    """ExecutionGuard allows a clean high-confidence signal"""
    from execution.execution_guard import ExecutionGuard
    
    guard = ExecutionGuard()
    result = guard.check({'action': 'CALL', 'confidence': 85})
    assert result['allowed'], "Should allow clean signal"
    print("  PASS: test_risk_gate_allows_good_signal")


def test_multiple_seeds_no_crash():
    """Pipeline stable across many random datasets"""
    from main import setup_engines, setup_pipeline
    
    registry = setup_engines()
    pipeline = setup_pipeline(registry)
    
    for seed in [1, 10, 50, 100, 200, 500, 999]:
        ds = DummyDataSource(seed=seed)
        candles = ds.get_multi_timeframe('EURUSD', ['M1','M5','M15','M60'], 250)
        signal = pipeline.execute('EURUSD', candles, 'M5')
        assert signal is not None
    print("  PASS: test_multiple_seeds_no_crash")


if __name__ == '__main__':
    print("Running integration tests...")
    test_pipeline_produces_signal()
    test_pipeline_handles_empty_data()
    test_risk_gate_blocks_correctly()
    test_risk_gate_allows_good_signal()
    test_multiple_seeds_no_crash()
    print("✅ All integration tests passed")
