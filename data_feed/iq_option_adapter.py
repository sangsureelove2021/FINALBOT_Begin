"""
IQ Option Data Adapter

Single source of market data: IQ Option (DEMO account by default).
No fallback to synthetic data — if connection fails, the bot stops.

Pattern based on the field-tested BOT_2026 client:
  • Thread-safe candle fetch (shared buffer in iqoptionapi)
  • Per-call timeout (8s) so a hung websocket never freezes the loop
  • Auto-reconnect on dropped connection
  • Sanity-check median price (JPY pairs 50-300, others 0.5-10)
"""

import concurrent.futures
import threading
import time
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import logging
import os
import asyncio

from data_feed.data_source import IDataSource

logger = logging.getLogger(__name__)

# Global lock — iqoptionapi shares a single websocket buffer
_CANDLES_LOCK = threading.Lock()
# Default timeout, will be updated when config is available
_CANDLES_TIMEOUT_SEC = 8


class IQOptionAdapter(IDataSource):
    """IQ Option broker adapter — live API only."""

    def __init__(self, email: Optional[str] = None,
                 password: Optional[str] = None,
                 account_type: Optional[str] = None,
                 api_token: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize adapter.

        Args:
            email: IQ Option login email (or via IQ_EMAIL env var).
            password: IQ Option password (or via IQ_PASSWORD env var).
            account_type: 'DEMO' / 'PRACTICE' (demo) or 'REAL'.
            api_token: legacy, unused.
            config: Configuration from datafeed_config.json
        """
        # Initialize with configuration
        if config is None:
            from config_setting.config_loader import load_datafeed_settings
            config = load_datafeed_settings()
        
        super().__init__(config)
        
        # Load IQ Option configuration
        iq_config = config.get("data_feed", {}).get("iq_option_adapter", {})
        global _CANDLES_TIMEOUT_SEC
        _CANDLES_TIMEOUT_SEC = iq_config.get("timeout_sec", 8)
        
        # Priority: explicit args > env vars > config
        if email and password:
            self.email, self.password = email, password
        else:
            from config_setting.config_loader import get_iq_credentials
            self.email, self.password = get_iq_credentials()
        
        if account_type:
            self.account_type = account_type
        else:
            from config_setting.config_loader import get_account_type
            self.account_type = get_account_type()
        
        # Load connection parameters from config
        self.timeout_sec = iq_config.get("timeout_sec", 8)
        self.max_workers = iq_config.get("max_workers", 10)
        
        # Zero Tolerance compliance check
        connection_retries = iq_config.get("connection_retries", 0)
        if connection_retries > 0:
            logger.error(f"[IQOPTION] Zero Tolerance VIOLATION: connection_retries={connection_retries}")
            logger.error(f"[IQOPTION] Config must have connection_retries=0")
            raise RuntimeError("Zero Tolerance: connection retries not allowed")
            
        self.connection_retries = 0  # Zero Tolerance: no retry allowed
        
        logger.info(f"[IQOPTION] Initialized with Zero Tolerance compliance")

        if not self.email or not self.password:
            raise RuntimeError(
                "IQ Option credentials missing. Provide email/password "
                "as arguments or set IQ_EMAIL / IQ_PASSWORD env vars."
            )

        try:
            from iqoptionapi.stable_api import IQ_Option
            self.IQ_Option = IQ_Option
            logger.info("Using stable_api.IQ_Option class")
        except ImportError as e:
            logger.exception("iqoptionapi library structure issue"); raise Exception(f"Cannot import IQ_Option: {e}")

        logger.info(f"[CONN] Connecting to IQ Option ({self.account_type}) as {self.email}...")
        # NOTE: stable_api.IQ_Option takes only (email, password) — no host arg.
        # The low-level iqoptionapi.api.IQOptionAPI("iqoption.com", ...) class posts
        # directly to https://iqoption.com/api/login, which IQ Option retired (404).
        # stable_api routes auth through the still-working v2/websocket flow.
        self.api = self.IQ_Option(self.email, self.password)
        logger.info(f"[CONN] API created, attempting to connect...")
        ok, reason = self.api.connect()
        if not ok:
            raise RuntimeError(f"IQ Option login failed: {reason}")

        balance_mode = "PRACTICE" if str(self.account_type).upper() in ["DEMO", "PRACTICE"] else "REAL"
        self.api.change_balance(balance_mode)

        self._connected = True
        mode = "DEMO" if str(self.account_type).upper() in ["DEMO", "PRACTICE"] else "REAL MONEY"
        logger.info(f"[CONN] IQ Option connected ({mode})")
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self._conn_lock = threading.Lock()
    
    @property
    def connected(self) -> bool:
        """Returns True if the adapter is connected to the broker."""
        return getattr(self, '_connected', False)

    
    @staticmethod
    def _normalize_candle_index(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize candle index to UTC DatetimeIndex."""
        if df is None or df.empty:
            raise ValueError("Empty DataFrame in _normalize_candle_index")
        out = df.copy()
        if not isinstance(out.index, pd.DatetimeIndex):
            if pd.api.types.is_numeric_dtype(out.index):
                out.index = pd.to_datetime(out.index, unit='s', utc=True)
            else:
                out.index = pd.to_datetime(out.index, utc=True)
        elif out.index.tz is None:
            out.index = out.index.tz_localize('UTC')
        else:
            out.index = out.index.tz_convert('UTC')
        return out.sort_index(ascending=True)

    def get_candles(self, symbol: str, timeframe: str = 'M1',
                   count: int = 200, end_time: Optional[Any] = None) -> pd.DataFrame:
        """
        Fetch candles for symbol.
        
        Args:
            symbol: 'EURUSD', 'GBPUSD', etc.
            timeframe: 'M1', 'M5', 'M15', 'M60', 'D1'
            count: Number of candles
            end_time: End time for candle history retrieval
        
        Returns:
            DataFrame [open, high, low, close, volume] indexed by datetime
        """
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if not isinstance(timeframe, str):
            raise TypeError("timeframe must be a string")
        if not isinstance(count, int):
            raise TypeError("count must be an integer")
        if timeframe not in self._TF_SECONDS:
            raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {list(self._TF_SECONDS.keys())}")
        if not self._connected:
            raise RuntimeError("IQ Option not connected")
        return self._normalize_candle_index(
            self._get_from_api(symbol, timeframe, count, end_time)
        )
    
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

    def ensure_connected(self) -> None:
        """Reconnect if the websocket dropped (called before each fetch)."""
        if not self.api:
            raise RuntimeError("API not initialized")
        # Double-checked locking pattern for thread safety
        if not self.api.check_connect():
            with self._conn_lock:
                if not self.api.check_connect():
                    logger.error("[ERROR] IQ Option connection lost — Zero Tolerance: stopping immediately")
                    raise RuntimeError("IQ Option connection lost — no retry allowed")
            
    async def connect(self) -> None:
        """Async connect method for interface compliance."""
        # This adapter uses synchronous connection, so just return
        pass

    def disconnect(self) -> Any:
        """
        Disconnect method for IQ Option adapter.
        Supports both synchronous call and asynchronous call (awaitable)
        to prevent 'RuntimeWarning: coroutine disconnect was never awaited'.
        """
        if hasattr(self, 'api') and self.api:
            try:
                if hasattr(self.api, 'disconnect'):
                    self.api.disconnect()
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
        self._connected = False
        logger.info("[CONN] IQ Option disconnected")

        class _AwaitableNone:
            def __await__(self):
                return asyncio.sleep(0).__await__()

        return _AwaitableNone()

    def start_stream(self, symbol: str, timeframe: str, count: int) -> None:
        """Start WebSocket stream for live data (synchronous version for runner.py)."""
        # Validate timeframe
        if timeframe not in self._TF_SECONDS:
            raise ValueError(f"Unsupported timeframe: {timeframe}. Supported: {list(self._TF_SECONDS.keys())}")

        size = self._TF_SECONDS[timeframe]

        # Start stream synchronously
        self.api.start_candles_stream(symbol, size, count)
        logger.info(f"[WS] Subscribed live candles stream for {symbol} ({timeframe}, count={count})")

    async def get_historical_candles(self, symbol: str, timeframe: int, count: int, end_time: float) -> List[Dict]:
        """Get historical candles for interface compliance."""
        # This adapter uses REST API instead of historical candles
        return []
    
    # Map our timeframe codes to IQ Option candle sizes (seconds)
    _TF_SECONDS = {
        'M1': 60, 'M5': 300, 'M15': 900, 'M30': 1800,
        'M60': 3600, 'H1': 3600, 'H4': 14400, 'D1': 86400,
    }

    def _get_from_api(self, symbol: str, timeframe: str,
                      count: int, end_time: Optional[Any] = None) -> pd.DataFrame:
        """
        Fetch candles from IQ Option (field-tested pattern from BOT_2026).
        """
        if not self.api:
            raise RuntimeError("API not initialized")
        self.ensure_connected()

        size = self._TF_SECONDS[timeframe]
        
        # Parse end_time to epoch timestamp
        end_timestamp = time.time()
        if end_time is not None:
            if isinstance(end_time, datetime):
                end_timestamp = end_time.timestamp()
            elif isinstance(end_time, (int, float)):
                end_timestamp = float(end_time)

        # REST HTTP request (Single Source of Truth), bounded by a hard
        # per-call timeout so a hung websocket can never freeze the loop.
        def _fetch():
            acquired = _CANDLES_LOCK.acquire(timeout=self.timeout_sec)
            if not acquired:
                raise RuntimeError(f"Cannot acquire candle lock for {symbol} within {self.timeout_sec}s")
            try:
                return self.api.get_candles(symbol, size, count, end_timestamp)
            finally:
                _CANDLES_LOCK.release()

        future = self._executor.submit(_fetch)
        try:
            raw = future.result(timeout=self.timeout_sec)
            logger.info(f"[IQOPTION] REST fetch succeeded for {symbol}: {len(raw)} candles")
        except concurrent.futures.TimeoutError:
            future.cancel()
            logger.error(f"[IQOPTION] REST fetch timed out for {symbol} after {self.timeout_sec}s")
            logger.error(f"[IQOPTION] Zero Tolerance: stopping immediately - no retry allowed")
            raise RuntimeError(f"REST fetch timed out for {symbol} after {self.timeout_sec}s")
        except Exception as e:
            logger.error(f"[IQOPTION] REST fetch failed for {symbol}: {e}")
            logger.error(f"[IQOPTION] Zero Tolerance: stopping immediately - no retry allowed")
            raise RuntimeError(f"REST fetch failed for {symbol}: {e}")

        if not raw:
            raise ValueError(f"REST fetch returned no data for {symbol}")

        df = pd.DataFrame(raw)
        if df.empty:
            raise ValueError(f"REST fetch returned empty dataframe for {symbol}")

        df = df.rename(columns={"max": "high", "min": "low"})
        need = {"from", "open", "close", "high", "low"}
        if not need.issubset(df.columns):
            raise ValueError(f"REST fetch missing required columns for {symbol}: {need - set(df.columns)}")
            
        df["timestamp"] = pd.to_datetime(df["from"], unit="s", utc=True)
        for col in ("open", "close", "high", "low"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        
        is_otc = "OTC" in symbol.upper()

        if "volume" in df.columns:
            df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
            if df["volume"].isnull().any():
                raise ValueError(f"Volume contains NaN values for {symbol} - no fallback allowed")
        else:
            # ไม่มี fallback สำหรับ symbol ที่ไม่มี volume column
            raise ValueError(f"Volume column missing for {symbol}")

        df = df.dropna(subset=["open", "close", "high", "low"])
        if df.empty:
            raise ValueError(f"Empty dataframe after dropna for {symbol}")

        # ไม่มี fallback สำหรับ volume error - IQ Option ต้องส่ง volume ที่ถูกต้อง
        if not is_otc and df["volume"].sum() == 0:
            raise ValueError(f"Volume is all zeros for non-OTC symbol {symbol} — broker data error")

        # Sanity check: reject obviously broken price feeds
        median_close = float(df["close"].median())
        is_jpy = "JPY" in symbol.upper()
        if is_jpy and not (50.0 <= median_close <= 300.0):
            raise ValueError(f"{symbol} median {median_close} out of JPY range")
        if not is_jpy and not (0.3 <= median_close <= 10.0):
            raise ValueError(f"{symbol} median {median_close} out of FX range")
            
        res = df[["timestamp", "open", "high", "low", "close", "volume"]].set_index("timestamp")
        res.index = pd.to_datetime(res.index, utc=True)
        return res.sort_index(ascending=True)

    def _start_realtime_stream(self, symbol: str, timeframe: str, count: int) -> None:
        """Start WebSocket streaming for real-time data."""
        try:
            if not self.api:
                raise RuntimeError("API not initialized")
            
            # Start WebSocket stream
            self.api.start_candles_stream(
                ACTIVE=symbol,
                size=self._TF_SECONDS[timeframe],
                maxdict=count
            )
            
            logger.info(f"[WebSocket] Started real-time stream for {symbol} {timeframe}")
            
        except Exception as e:
            logger.error(f"[WebSocket] Failed to start stream for {symbol} {timeframe}: {e}")
            raise RuntimeError(f"Stream setup failed: {e}")
    
    def _get_cached_candles(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Get candles from WebSocket cache."""
        try:
            if not self.api:
                raise RuntimeError("API not initialized")
            
            # Get cached data from WebSocket
            cached_data = self.api.get_realtime_candles(
                ACTIVE=symbol,
                size=self._TF_SECONDS[timeframe]
            )
            
            if not cached_data:
                logger.warning(f"[Cache] No cached data for {symbol} {timeframe}")
                return pd.DataFrame()
            
            # Debug: Print cached data structure
            logger.debug(f"[Cache] Raw cached data for {symbol}: {type(cached_data)} - {len(cached_data)} items")
            if hasattr(cached_data, 'keys'):
                logger.debug(f"[Cache] Cached data keys (first 10): {list(cached_data.keys())[:10]}")
                # If it looks like timestamp keys, show the structure of first value
                if cached_data and isinstance(list(cached_data.values())[0], dict):
                    first_value = list(cached_data.values())[0]
                    logger.debug(f"[Cache] First value structure: {first_value}")
                    # Transform from {timestamp: {ohlc_data}} to DataFrame
                    df = pd.DataFrame.from_dict(cached_data, orient='index')
                    # Reset index to make timestamp a column
                    df = df.reset_index()
                    df = df.rename(columns={'index': 'timestamp'})
                else:
                    # Regular DataFrame
                    df = pd.DataFrame(cached_data)
            else:
                # If it's a list, show first item structure
                if cached_data and isinstance(cached_data[0], dict):
                    logger.debug(f"[Cache] First item keys: {list(cached_data[0].keys())}")
                    df = pd.DataFrame(cached_data)
                else:
                    logger.error(f"[Cache] Unexpected cache data structure: {type(cached_data)}")
                    return pd.DataFrame()
            
            logger.debug(f"[Cache] DataFrame columns after transformation: {list(df.columns)}")
            df = df.rename(columns={"max": "high", "min": "low"})
            
            # Check if we have the required columns
            required_cols = ["open", "close", "high", "low"]
            if not all(col in df.columns for col in required_cols):
                logger.error(f"[Cache] Missing required columns in cached data for {symbol}: {required_cols}")
                logger.error(f"[Cache] Available columns: {list(df.columns)}")
                return pd.DataFrame()
            
            # Handle timestamp - try different possible column names
            timestamp_col = None
            if "from" in df.columns:
                df["timestamp"] = pd.to_datetime(df["from"], unit="s", utc=True)
            elif "time" in df.columns:
                df["timestamp"] = pd.to_datetime(df["time"], unit="s", utc=True)
            elif "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s", utc=True)
            else:
                logger.error(f"[Cache] No timestamp column found in cached data for {symbol}")
                logger.error(f"[Cache] Available columns: {list(df.columns)}")
                return pd.DataFrame()
            
            # Convert numeric columns
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            
            if "volume" in df.columns:
                df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
            
            res = df[["timestamp", "open", "high", "low", "close", "volume"]].set_index("timestamp")
            res.index = pd.to_datetime(res.index, utc=True)
            return res.sort_index(ascending=True)
                    
        except Exception as e:
            logger.error(f"[Cache] Failed to get cached data for {symbol} {timeframe}: {e}")
            raise RuntimeError(f"Cache access failed: {e}")

    def update_with_streaming(self, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
        """
        Update data using WebSocket streaming for better performance.
        
        Args:
            symbol: 'EURUSD', 'GBPUSD', etc.
            timeframe: 'M1', 'M5', 'M15', etc.
            count: Number of candles to maintain
            
        Returns:
            DataFrame with updated data
        """
        total_start = time.time()
        
        try:
            # Measure stream setup time
            stream_start = time.time()
            # Start stream if not already running
            self._start_realtime_stream(symbol, timeframe, count)
            stream_time = time.time() - stream_start
            logger.debug(f"[Streaming] Stream setup took {stream_time:.3f}s")
            
            # Measure cache access time
            cache_start = time.time()
            # Get data from cache
            df = self._get_cached_candles(symbol, timeframe)
            cache_time = time.time() - cache_start
            
            # Check if we have data
            if df.empty:
                logger.error(f"[Streaming] Cache empty for {symbol} — Zero Tolerance: no fallback")
                raise RuntimeError(f"Streaming cache returned empty data for {symbol}")
            
            total_time = time.time() - total_start
            
            # Log detailed timing breakdown
            logger.info(f"[Streaming] Updated {symbol} {timeframe}: {len(df)} candles from cache")
            logger.debug(f"[Streaming] Timing breakdown - Stream: {stream_time:.3f}s, Cache: {cache_time:.3f}s, Total: {total_time:.3f}s")
            
            # Calculate performance metrics
            if len(df) > 0:
                avg_time_per_candle = total_time / len(df)
                logger.debug(f"[Streaming] Average time per candle: {avg_time_per_candle:.4f}s")
                if cache_time > 0:
                    candles_per_second = len(df) / cache_time
                    logger.debug(f"[Streaming] Cache throughput: {candles_per_second:.1f} candles/sec")
            
            return df
            
        except Exception as e:
            logger.error(f"[Streaming] Failed to update with streaming for {symbol}: {e}")
            logger.error(f"[Streaming] Zero Tolerance: no silent fallback allowed")
            raise RuntimeError(f"Streaming update failed for {symbol}: {e}") from e
