"""
Unit Tests: Data Models
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test data model validation and schemas.
"""

import pytest
from datetime import datetime
import pandas as pd

from core.models.candle import Candle
from core.models.signal import Signal
from core.data.candle_buffer import CandleBuffer
from execution.position_sizer import PositionSizer, PositionSize


class TestCandle:
    """Test Candle model."""
    
    def test_candle_creation(self):
        """Test creating candle."""
        c = Candle(
            timestamp=datetime.utcnow(),
            open=1.0850,
            high=1.0860,
            low=1.0840,
            close=1.0855,
            volume=1000
        )
        assert c.open == 1.0850
        assert c.close == 1.0855
        assert c.high >= c.low
    
    def test_candle_body(self):
        """Test candle body calculation."""
        c = Candle(
            timestamp=datetime.utcnow(),
            open=1.0850,
            high=1.0860,
            low=1.0840,
            close=1.0855,
            volume=1000
        )
        body = c.close - c.open
        assert body > 0
    
    def test_invalid_candle(self):
        """Test invalid candle (high < low)."""
        with pytest.raises(AssertionError):
            c = Candle(
                timestamp=datetime.utcnow(),
                open=1.0850,
                high=1.0840,
                low=1.0860,
                close=1.0855,
                volume=1000
            )


class TestSignal:
    """Test Signal model."""
    
    def test_call_signal(self):
        """Test CALL signal."""
        signal = Signal(
            direction='CALL',
            confidence=85,
            entry_price=1.0850,
            stop_loss=1.0840,
            entry_score=82,
            block_score=15
        )
        assert signal.direction == 'CALL'
        assert signal.confidence == 85
        assert signal.is_valid()
    
    def test_put_signal(self):
        """Test PUT signal."""
        signal = Signal(
            direction='PUT',
            confidence=75,
            entry_price=1.0850,
            stop_loss=1.0860,
            entry_score=72,
            block_score=20
        )
        assert signal.direction == 'PUT'
    
    def test_no_signal(self):
        """Test NO_SIGNAL."""
        signal = Signal(
            direction='NO_SIGNAL',
            confidence=0,
            entry_price=0,
            stop_loss=0,
            entry_score=0,
            block_score=100
        )
        assert not signal.is_valid()


class TestCandleBuffer:
    """Test CandleBuffer."""
    
    def test_buffer_creation(self):
        """Test buffer creation."""
        buf = CandleBuffer(size=100)
        assert buf.size == 100
    
    def test_append_candles(self):
        """Test appending candles."""
        buf = CandleBuffer()
        df = pd.DataFrame({
            'open': [1.0850, 1.0851],
            'high': [1.0860, 1.0861],
            'low': [1.0840, 1.0841],
            'close': [1.0855, 1.0856],
            'volume': [1000, 1100]
        }, index=pd.date_range('2026-05-21', periods=2, freq='5min'))
        
        buf.append('EURUSD', 'M5', df)
        stored = buf.get('EURUSD', 'M5')
        assert len(stored) == 2
    
    def test_buffer_size_limit(self):
        """Test buffer size limit."""
        buf = CandleBuffer(size=10)
        
        # Create 20 candles
        df = pd.DataFrame({
            'open': [1.0 + i*0.001 for i in range(20)],
            'high': [1.0 + i*0.001 + 0.001 for i in range(20)],
            'low': [1.0 + i*0.001 - 0.001 for i in range(20)],
            'close': [1.0 + i*0.001 + 0.0005 for i in range(20)],
            'volume': [1000] * 20
        }, index=pd.date_range('2026-05-21', periods=20, freq='1min'))
        
        buf.append('EURUSD', 'M1', df)
        stored = buf.get('EURUSD', 'M1')
        
        # Should keep only last 10
        assert len(stored) <= 10


class TestPositionSizer:
    """Test PositionSizer."""
    
    def test_position_size_calculation(self):
        """Test basic position sizing."""
        sizer = PositionSizer(capital=2000, risk_percent=2)
        
        ps = sizer.calculate(
            entry_price=1.0850,
            stop_loss_price=1.0840,
            direction='CALL'
        )
        
        assert ps.is_valid
        assert ps.amount > 0
        assert ps.risk_percent == 2.0
    
    def test_position_size_limits(self):
        """Test position size limits."""
        sizer = PositionSizer(
            capital=2000,
            risk_percent=2,
            max_per_trade=500
        )
        
        # Large SL distance
        ps = sizer.calculate(
            entry_price=1.0850,
            stop_loss_price=1.0700,
            direction='CALL'
        )
        
        # Should be capped at max_per_trade
        assert ps.amount <= 500
    
    def test_daily_risk_limit(self):
        """Test daily risk limit."""
        sizer = PositionSizer(
            capital=2000,
            risk_percent=2,
            max_daily_risk=5
        )
        
        # Record trades that exceed daily limit
        for i in range(5):
            sizer.record_trade(100, result=-50)
        
        ps = sizer.calculate(
            entry_price=1.0850,
            stop_loss_price=1.0840,
            direction='CALL'
        )
        
        # Should be invalid due to daily limit
        assert not ps.is_valid
    
    def test_invalid_sl(self):
        """Test invalid stop loss."""
        sizer = PositionSizer()
        
        ps = sizer.calculate(
            entry_price=1.0850,
            stop_loss_price=1.0850,  # Same as entry
            direction='CALL'
        )
        
        assert not ps.is_valid


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
