"""
Unit Tests: Data Models
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Validates Candle, Signal, CandleBuffer, PositionSizer against the
current model APIs.
"""

import pytest
from datetime import datetime, timezone
import pandas as pd

from core.models.candle import Candle
from core.models.signal import Signal, SignalAction, SignalQuality
from core.data.candle_buffer import CandleBuffer
from execution.position_sizer import PositionSizer, PositionSize


class TestCandle:
    def test_candle_creation(self):
        c = Candle(timestamp=datetime.now(timezone.utc), open=1.0850, high=1.0860,
                   low=1.0840, close=1.0855, volume=1000)
        assert c.open == 1.0850
        assert c.close == 1.0855
        assert c.high >= c.low

    def test_candle_body(self):
        c = Candle(timestamp=datetime.now(timezone.utc), open=1.0850, high=1.0860,
                   low=1.0840, close=1.0855, volume=1000)
        assert c.body == pytest.approx(0.0005)
        assert c.is_bullish

    def test_invalid_candle(self):
        """High < Low must raise ValueError."""
        with pytest.raises(ValueError):
            Candle(timestamp=datetime.now(timezone.utc), open=1.0850, high=1.0840,
                   low=1.0860, close=1.0855, volume=1000)


class TestSignal:
    def _make(self, action: SignalAction, confidence: int) -> Signal:
        return Signal(
            signal_id="t1", timestamp=datetime.now(timezone.utc),
            symbol="EURUSD-OTC", timeframe="M5",
            action=action, confidence=confidence,
            quality=SignalQuality.HIGH,
            strategy_name="compression_breakout", reason="unit test",
        )

    def test_call_signal(self):
        s = self._make(SignalAction.CALL, 85)
        assert s.action == SignalAction.CALL
        assert s.confidence == 85
        assert s.is_actionable

    def test_put_signal(self):
        s = self._make(SignalAction.PUT, 75)
        assert s.action == SignalAction.PUT
        assert s.is_actionable

    def test_no_signal(self):
        s = self._make(SignalAction.NO_SIGNAL, 0)
        assert s.action == SignalAction.NO_SIGNAL
        assert not s.is_actionable

    def test_confidence_bounds(self):
        """Confidence outside 0-100 must raise."""
        with pytest.raises(ValueError):
            self._make(SignalAction.CALL, 150)


class TestCandleBuffer:
    def test_buffer_creation(self):
        assert CandleBuffer(size=100).size == 100

    def test_append_candles(self):
        buf = CandleBuffer()
        df = pd.DataFrame(
            {'open': [1.0850, 1.0851], 'high': [1.0860, 1.0861],
             'low': [1.0840, 1.0841], 'close': [1.0855, 1.0856],
             'volume': [1000, 1100]},
            index=pd.date_range('2026-05-21', periods=2, freq='5min'))
        buf.append('EURUSD', 'M5', df)
        assert len(buf.get('EURUSD', 'M5')) == 2

    def test_buffer_size_limit(self):
        buf = CandleBuffer(size=10)
        df = pd.DataFrame(
            {'open': [1.0 + i * 0.001 for i in range(20)],
             'high': [1.0 + i * 0.001 + 0.001 for i in range(20)],
             'low': [1.0 + i * 0.001 - 0.001 for i in range(20)],
             'close': [1.0 + i * 0.001 + 0.0005 for i in range(20)],
             'volume': [1000] * 20},
            index=pd.date_range('2026-05-21', periods=20, freq='1min'))
        buf.append('EURUSD', 'M1', df)
        assert len(buf.get('EURUSD', 'M1')) <= 10


class TestPositionSizer:
    def test_position_size_calculation(self):
        sizer = PositionSizer(capital=2000, risk_percent=2)
        ps = sizer.calculate(entry_price=1.0850,
                             stop_loss_price=1.0840, direction='CALL')
        assert isinstance(ps, PositionSize)
        assert ps.is_valid
        assert ps.amount > 0

    def test_confidence_mode_scales_stake(self, monkeypatch):
        from core import config_loader

        monkeypatch.setattr(
            config_loader,
            "load_settings",
            lambda reload=False: {"capital": {"stake_per_trade": 30.0}},
        )

        sizer = PositionSizer(capital=2000, risk_percent=2)
        stake = sizer.calculate(confidence=90)

        assert isinstance(stake, float)
        assert stake > 30.0
        assert stake <= sizer.max_per_trade

    def test_confidence_mode_blocks_after_daily_limit(self, monkeypatch):
        from core import config_loader

        monkeypatch.setattr(
            config_loader,
            "load_settings",
            lambda reload=False: {"capital": {"stake_per_trade": 30.0}},
        )

        sizer = PositionSizer(capital=2000, risk_percent=2)
        sizer.record_trade(amount=30.0, result=-150.0)

        assert sizer.calculate(confidence=90) == 0.0

    def test_invalid_sl(self):
        """Stop loss equal to entry must be rejected."""
        sizer = PositionSizer()
        ps = sizer.calculate(entry_price=1.0850,
                             stop_loss_price=1.0850, direction='CALL')
        assert not ps.is_valid


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
