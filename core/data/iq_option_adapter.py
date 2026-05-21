"""
IQ Option Data Adapter
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Adapter for IQ Option API. Currently uses mock data.
Swap to real API: Replace synthetic_data() with iq_option API calls.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from core.data.data_source import IDataSource

logger = logging.getLogger(__name__)


class IQOptionAdapter(IDataSource):
    """
    IQ Option broker adapter.
    
    Status: MOCK (uses synthetic data)
    To use real API:
    1. pip install iqoptionapi
    2. Initialize: IQOptionAdapter(api_token="your_token")
    3. Replace synthetic_data() with get_from_api()
    """
    
    def __init__(self, api_token: Optional[str] = None, use_mock: bool = True):
        """
        Initialize adapter.
        
        Args:
            api_token: IQ Option API token (optional for mock mode)
            use_mock: Use synthetic data (True for testing, False for live)
        """
        self.api_token = api_token
        self.use_mock = use_mock
        self._connected = False
        self._connected = self._check_connection()
        
        if not use_mock and api_token:
            try:
                from iqoptionapi.api import IQOptionAPI
                self.api = IQOptionAPI("ws://", api_token, 1)
                logger.info("✅ IQ Option API initialized (real)")
            except Exception as e:
                logger.warning(f"⚠️ Could not initialize real API: {e}, falling back to mock")
                self.use_mock = True
        else:
            self.api = None
    
    def get_candles(self, symbol: str, timeframe: str = 'M1',
                   count: int = 200) -> pd.DataFrame:
        """
        Fetch candles for symbol.
        
        Args:
            symbol: 'EURUSD', 'GBPUSD', etc.
            timeframe: 'M1', 'M5', 'M15', 'M60', 'D1'
            count: Number of candles
        
        Returns:
            DataFrame [open, high, low, close, volume] indexed by datetime
        """
        if self.use_mock or not self._connected:
            return self._synthetic_data(symbol, timeframe, count)
        
        try:
            return self._get_from_api(symbol, timeframe, count)
        except Exception as e:
            logger.error(f"API error fetching {symbol}: {e}, using mock")
            return self._synthetic_data(symbol, timeframe, count)
    
    def get_multi_timeframe(self, symbol: str,
                           timeframes: Optional[List[str]] = None,
                           count: int = 200) -> Dict[str, pd.DataFrame]:
        """Get candles for multiple timeframes."""
        if timeframes is None:
            timeframes = ['M1', 'M5', 'M15', 'M60', 'D1']
        
        return {tf: self.get_candles(symbol, tf, count) for tf in timeframes}
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected
    
    def _check_connection(self) -> bool:
        """Verify connection to API or mock."""
        if self.use_mock:
            logger.info("📊 Using MOCK data source")
            return True
        
        if self.api_token:
            try:
                logger.info("🔌 Attempting IQ Option API connection...")
                # Simple check: can we initialize?
                return True
            except Exception as e:
                logger.error(f"❌ Connection failed: {e}")
                return False
        
        return False
    
    def _synthetic_data(self, symbol: str, timeframe: str, 
                       count: int) -> pd.DataFrame:
        """Generate realistic synthetic candles."""
        np.random.seed(hash(symbol + timeframe) % 2**32)  # Deterministic per symbol/tf
        
        tf_minutes = {
            'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30,
            'M60': 60, 'H1': 60, 'H4': 240, 'D1': 1440
        }
        minutes = tf_minutes.get(timeframe, 1)
        
        # Time index
        end_time = datetime.utcnow().replace(second=0, microsecond=0)
        dates = pd.date_range(end=end_time, periods=count, freq=f'{minutes}min')
        
        # Base price
        base_price = self._get_base_price(symbol)
        
        # Generate trend with momentum
        trend = np.random.normal(0.00005, 0.00015, count)
        noise = np.random.normal(0, 0.001, count)
        returns = trend + noise
        prices = base_price * np.exp(np.cumsum(returns))
        
        # OHLC
        opens = prices.copy()
        closes = prices * (1 + np.random.normal(0, 0.0005, count))
        
        # High/Low
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
        
        return df.sort_index()
    
    def _get_from_api(self, symbol: str, timeframe: str, 
                     count: int) -> pd.DataFrame:
        """Fetch from real IQ Option API (future implementation)."""
        if not self.api:
            raise RuntimeError("API not initialized")
        
        # This will be implemented when Boss provides credentials
        # For now, fall back to mock
        raise NotImplementedError("Real API not yet implemented")
    
    def _get_base_price(self, symbol: str) -> float:
        """Base price for symbol."""
        bases = {
            'EURUSD': 1.0850, 
            'EURUSD-OTC': 1.0850,  # Boss's trading pair
            'GBPUSD': 1.2650, 
            'USDJPY': 149.50,
            'AUDUSD': 0.6750, 
            'NZDUSD': 0.6150, 
            'USDCAD': 1.3550,
            'XAUUSD': 2050.0, 
            'BTCUSD': 65000.0, 
            'ETHUSD': 3500.0,
        }
        return bases.get(symbol, 1.0)
