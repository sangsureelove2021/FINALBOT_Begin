"""
Integration Tests: End-to-End Pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test full pipeline from data to execution.
"""

import pytest
from datetime import datetime

from core.data.iq_option_adapter import IQOptionAdapter
from core.data.candle_buffer import CandleBuffer
from execution.position_sizer import PositionSizer
from execution.iq_option_executor import IQOptionExecutor
from execution.order_manager import OrderManager


class TestDataFlow:
    """Test data pipeline flow."""
    
    def test_adapter_to_buffer(self):
        """Test data flow from adapter to buffer."""
        adapter = IQOptionAdapter(use_mock=True)
        buffer = CandleBuffer()
        
        # Fetch data
        df = adapter.get_candles('EURUSD', 'M5', 100)
        assert len(df) == 100
        
        # Add to buffer
        buffer.append('EURUSD', 'M5', df)
        stored = buffer.get('EURUSD', 'M5')
        assert len(stored) == 100
    
    def test_multi_timeframe_data(self):
        """Test multi-timeframe data handling."""
        adapter = IQOptionAdapter(use_mock=True)
        
        candles = adapter.get_multi_timeframe(
            'EURUSD',
            timeframes=['M1', 'M5', 'M15'],
            count=100
        )
        
        assert 'M1' in candles
        assert 'M5' in candles
        assert 'M15' in candles
        assert all(len(df) == 100 for df in candles.values())


class TestExecutionFlow:
    """Test execution pipeline flow."""
    
    def test_position_sizing_to_order(self):
        """Test flow from position sizing to order."""
        sizer = PositionSizer(capital=2000, risk_percent=2)
        executor = IQOptionExecutor(use_mock=True)
        
        # Size position
        ps = sizer.calculate(
            entry_price=1.0850,
            stop_loss_price=1.0840,
            direction='CALL'
        )
        assert ps.is_valid
        
        # Execute order
        result = executor.send_order(
            symbol='EURUSD',
            direction='CALL',
            amount=ps.amount,
            expiry='M5'
        )
        
        assert result.status == 'pending'
        assert result.order_id
    
    def test_order_to_manager(self):
        """Test flow from order to manager."""
        executor = IQOptionExecutor(use_mock=True)
        manager = OrderManager()
        
        # Execute order
        result = executor.send_order(
            symbol='EURUSD',
            direction='CALL',
            amount=100,
            expiry='M5'
        )
        
        # Register in manager
        added = manager.add_trade(
            order_id=result.order_id,
            symbol='EURUSD',
            direction='CALL',
            amount=100,
            entry_price=1.0850
        )
        assert added
        
        # Verify in manager
        trades = manager.get_active_trades('EURUSD')
        assert len(trades) == 1
        assert trades[0].symbol == 'EURUSD'


class TestFullPipeline:
    """Test complete pipeline."""
    
    def test_end_to_end_flow(self):
        """Test full data → execution flow."""
        # Data
        adapter = IQOptionAdapter(use_mock=True)
        buffer = CandleBuffer()
        
        # Execution
        sizer = PositionSizer(capital=2000)
        executor = IQOptionExecutor(use_mock=True)
        manager = OrderManager()
        
        # Step 1: Fetch data
        df = adapter.get_candles('EURUSD', 'M5', 50)
        buffer.append('EURUSD', 'M5', df)
        
        # Step 2: Size position
        entry = 1.0850
        sl = 1.0840
        ps = sizer.calculate(entry_price=entry, stop_loss_price=sl)
        
        # Step 3: Execute
        order = executor.send_order(
            symbol='EURUSD',
            direction='CALL',
            amount=ps.amount,
            expiry='M5'
        )
        
        # Step 4: Track
        manager.add_trade(
            order_id=order.order_id,
            symbol='EURUSD',
            direction='CALL',
            amount=ps.amount,
            entry_price=entry
        )
        
        # Step 5: Close
        manager.close_trade(
            order_id=order.order_id,
            exit_price=1.0860,
            pnl=100
        )
        
        # Verify
        stats = manager.get_stats()
        assert stats['total_trades'] == 1
        assert stats['total_pnl'] == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
