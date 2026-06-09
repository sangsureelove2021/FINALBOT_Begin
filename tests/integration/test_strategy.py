"""
Integration Tests: Strategy Layer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validates CompressionBreakoutStrategy decisions against
pre-built MarketContext fixtures.
"""

import pytest

from strategy.compression_breakout.strategy import CompressionBreakoutStrategy
from tests.fixtures.sample_context import (
    make_bullish_context, make_bearish_context, make_choppy_context,
)


def _is_valid_result(result: dict) -> bool:
    return (
        result is not None
        and result.get("action") in ("CALL", "PUT", "NO_SIGNAL", "NO_SETUP")
        and 0 <= result.get("confidence", 0) <= 100
        and 0 <= result.get("entry_score", 0) <= 100
        and 0 <= result.get("block_score", 0) <= 100
    )


class TestCompressionBreakout:
    def test_returns_valid_shape(self):
        result = CompressionBreakoutStrategy().evaluate(make_bullish_context())
        assert _is_valid_result(result)

    def test_bullish_context(self):
        """A clean bullish breakout should not produce PUT."""
        result = CompressionBreakoutStrategy().evaluate(make_bullish_context())
        assert result["action"] in ("CALL", "NO_SIGNAL", "NO_SETUP")

    def test_bearish_context(self):
        """A clean bearish breakout should not produce CALL."""
        result = CompressionBreakoutStrategy().evaluate(make_bearish_context())
        assert result["action"] in ("PUT", "NO_SIGNAL", "NO_SETUP")

    def test_choppy_context_no_trade(self):
        """A choppy market must produce NO_SIGNAL or NO_SETUP — 'The Art of Saying NO'."""
        result = CompressionBreakoutStrategy().evaluate(make_choppy_context())
        assert result["action"] in ("NO_SIGNAL", "NO_SETUP")

    def test_eligibility_check(self):
        """is_eligible must run without error on any context."""
        strat = CompressionBreakoutStrategy()
        assert isinstance(strat.is_eligible(make_bullish_context()), bool)
        assert isinstance(strat.is_eligible(make_choppy_context()), bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
