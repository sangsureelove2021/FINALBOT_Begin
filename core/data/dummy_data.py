"""
Dummy Data Source
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generates fake candle data for testing without broker connection.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

from core.data.data_source import IDataSource


class DummyDataSource(IDataSource):
    """
    Generates realistic dummy candles for testing.
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self._connected = True
    
    def get_candles(self, symbol: str, timeframe: str = 'M1',
                   count: int = 200) -> pd.DataFrame:
        """Generate dummy candles"""
        
        # Time delta for each timeframe
        tf_minutes = {
            'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30,
            'M60': 60, 'H1': 60, 'H4': 240, 'D1': 1440
        }
        minutes = tf_minutes.get(timeframe, 1)
        
        # Generate datetime index
        end_time = datetime.now().replace(second=0, microsecond=0)
        dates = pd.date_range(
            end=end_time,
            periods=count,
            freq=f'{minutes}min'
        )
        
        # Generate realistic price with trend + noise
        base_price = self._get_base_price(symbol)
        
        # Random walk with mild trend
        returns = np.random.normal(0.0001, 0.001, count)
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Generate OHLC
        opens = prices.copy()
        closes = prices * (1 + np.random.normal(0, 0.0005, count))
        
        # High/Low: extend beyond open/close
        spread = np.abs(np.random.normal(0, 0.0003, count))
        highs = np.maximum(opens, closes) + spread
        lows = np.minimum(opens, closes) - spread
        
        # Volume
        volumes = np.random.randint(800, 2000, count).astype(float)
        
        df = pd.DataFrame({
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes,
        }, index=dates)
        
        return df
    
    def get_multi_timeframe(self, symbol: str,
                           timeframes: List[str] = None,
                           count: int = 200) -> Dict[str, pd.DataFrame]:
        """Generate dummy data for multiple timeframes"""
        if timeframes is None:
            timeframes = ['M1', 'M5', 'M15', 'M60', 'D1']
        
        return {tf: self.get_candles(symbol, tf, count) for tf in timeframes}
    
    def is_connected(self) -> bool:
        return self._connected
    
    def _get_base_price(self, symbol: str) -> float:
        """Get realistic base price for symbol"""
        bases = {
            'EURUSD': 1.0850, 'GBPUSD': 1.2650, 'USDJPY': 149.50,
            'AUDUSD': 0.6750, 'XAUUSD': 2050.0,  'BTCUSD': 65000.0,
        }
        return bases.get(symbol, 1.0)
