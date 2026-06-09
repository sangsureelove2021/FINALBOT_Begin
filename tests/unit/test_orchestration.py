"""
Unit Tests: Orchestration Layer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validates EngineRegistry, ContextBuilder, ExecutionGate and the
full Pipeline wiring.
"""

import pytest
import pandas as pd

from core.engines.engine_setup import setup_engines
from core.orchestration.context_builder import ContextBuilder
from core.orchestration.execution_gate import ExecutionGate
from core.models.signal import Signal, SignalAction
from main import setup_pipeline
from tests.fixtures.sample_candles import make_multi_timeframe
from tests.fixtures.sample_context import (
    make_bullish_context, make_choppy_context,
)


class TestEngineRegistry:
    def test_registry_populated(self):
        reg = setup_engines()
        assert reg.count() == 25
        assert reg.list_tiers() == [1, 2, 3, 4, 5, 6, 7, 8]

    def test_tier_lookup(self):
        reg = setup_engines()
        tier1 = reg.get_by_tier(1)
        assert len(tier1) == 5  # trend/strength/volatility/structure/mtf


class TestContextBuilder:
    def test_builds_context(self):
        reg = setup_engines()
        builder = ContextBuilder(reg)
        candles = make_multi_timeframe(count=250)
        ctx = builder.build("EURUSD-OTC", candles, "M5")
        assert ctx.symbol == "EURUSD-OTC"
        assert ctx.current_price > 0

    def test_empty_data_safe(self):
        reg = setup_engines()
        builder = ContextBuilder(reg)
        ctx = builder.build("TEST", {"M5": pd.DataFrame()}, "M5")
        assert ctx is not None
        assert ctx.has_errors()


class TestExecutionGate:
    def test_gate_blocks_choppy(self):
        gate = ExecutionGate()
        ctx = make_choppy_context()
        ctx.set_score("confidence", 50)
        ctx.set_score("block", 80)
        decision = gate.evaluate(ctx, {"action": "CALL"})
        assert not decision["approved"]

    def test_gate_allows_clean(self):
        gate = ExecutionGate(min_confidence=75)
        ctx = make_bullish_context()
        ctx.set_score("confidence", 88)
        ctx.set_score("block", 10)
        decision = gate.evaluate(ctx, {"action": "CALL"})
        assert decision["approved"]


class TestPipeline:
    def test_pipeline_returns_signal(self):
        pipeline = setup_pipeline()
        candles = make_multi_timeframe(count=250)
        signal = pipeline.execute("EURUSD-OTC", candles, "M5")
        assert isinstance(signal, Signal)
        assert signal.action in SignalAction
        assert 0 <= signal.confidence <= 100

    def test_pipeline_empty_data(self):
        pipeline = setup_pipeline()
        signal = pipeline.execute("TEST", {"M5": pd.DataFrame()}, "M5")
        assert signal is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
