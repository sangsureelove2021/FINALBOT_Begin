"""
Unit Tests: Scoring Layer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validates EntryScorer, BlockScorer, ConfidenceScorer and the
Score model against pre-built MarketContext fixtures.
"""

import pytest

from core.scoring.entry_scorer import EntryScorer
from core.scoring.block_scorer import BlockScorer
from core.scoring.confidence_scorer import ConfidenceScorer
from core.models.score import Score, ScoreSet
from tests.fixtures.sample_context import (
    make_bullish_context, make_choppy_context, make_empty_context,
)


class TestScoreModel:
    def test_score_bounds(self):
        s = Score(name="trend", value=80)
        assert s.value == 80
        assert s.is_high

    def test_score_invalid_value(self):
        with pytest.raises(ValueError):
            Score(name="bad", value=150)

    def test_score_weighted(self):
        s = Score(name="x", value=60, weight=2.0)
        assert s.weighted_value == 120

    def test_scoreset(self):
        ss = ScoreSet(scores={"a": Score(name="a", value=70)})
        assert ss.count == 1
        assert ss.get_value("a") == 70
        assert ss.get_value("missing", 5) == 5


class TestScorers:
    def test_entry_scorer_range(self):
        score = EntryScorer().score(make_bullish_context())
        assert 0 <= score <= 100

    def test_block_scorer_range(self):
        score = BlockScorer().score(make_bullish_context())
        assert 0 <= score <= 100

    def test_confidence_scorer_range(self):
        score = ConfidenceScorer().score(make_bullish_context())
        assert 0 <= score <= 100

    def test_choppy_blocks_higher(self):
        """A choppy market should not score lower block than a clean one."""
        clean = BlockScorer().score(make_bullish_context())
        choppy = BlockScorer().score(make_choppy_context())
        assert choppy >= clean

    def test_scorers_handle_empty_context(self):
        """Scorers must not crash on an empty context."""
        ctx = make_empty_context()
        for scorer in (EntryScorer(), BlockScorer(), ConfidenceScorer()):
            score = scorer.score(ctx)
            assert 0 <= score <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
