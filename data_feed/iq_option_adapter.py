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
                 account_type: str = "PRACTICE",
                 api_token: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize adapter.

        Args:
            email: IQ Option login email (or via IQ_EMAIL env var).
            password: IQ Option password (or via IQ_PASSWORD env var).
            account_type: 'PRACTICE' (demo) or 'REAL'.
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
        self.account_type = account_type or iq_config.get("account_type", "PRACTICE")
        
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

        balance_mode = "PRACTICE" if self.account_type.upper() in ["DEMO", "PRACTICE"] else "REAL"
        self.api.change_balance(balance_mode)

        self._connected = True
        mode = "DEMO" if self.account_type == "PRACTICE" else "REAL MONEY"
        logger.info(f"[CONN] IQ Option connected ({mode})")
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        self._conn_lock = threading.Lock()
    
    @property
    def connected(self) -> bool:
        """Returns True if the adapter is connected to the broker."""
        return getattr(self, '_connected', False)

    
    @staticmethod
    def _normalize_candle_index(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize candle index to naive UTC (WS and REST feeds differ otherwise)."""
        if df is None or df.empty:
            raise ValueError("Empty DataFrame in _normalize_candle_index")
        out = df.copy()
        out.index = pd.to_datetime(out.index, utc=True).tz_localize(None)
        return out.sort_index()

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
                    logger.warning("[WARN]  IQ Option connection lost — reconnecting...")
                    ok, reason = self.api.connect()
                    if ok:
                        # Wait 5 seconds for connection to stabilize
                        time.sleep(5)
                        # Verify connection is stable
                        if not self.api.check_connect():
                            logger.error(f"[ERROR] Connection still not stable after reconnect: {reason}")
                            raise RuntimeError(f"Connection failed: {reason}")
                        balance_mode = "PRACTICE" if str(self.account_type).upper() in ["DEMO", "PRACTICE"] else "REAL"
                        self.api.change_balance(balance_mode)
                        logger.info(" Reconnected successfully")
                    else:
                        logger.error(f"[ERROR] Reconnect failed: {reason}")
                        raise RuntimeError(f"Reconnect failed: {reason}")
            
    async def connect(self) -> None:
        """Async connect method for interface compliance."""
        # This adapter uses synchronous connection, so just return
        pass

    async def disconnect(self) -> None:
        """Async disconnect method for interface compliance."""
        # This adapter doesn't have explicit disconnect in IQ Option API
        pass

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
            with _CANDLES_LOCK:
                return self.api.get_candles(symbol, size, count, end_timestamp)

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
            
        df["timestamp"] = pd.to_datetime(df["from"], unit="s")
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
            
        return (df[["timestamp", "open", "high", "low", "close", "volume"]]
                .set_index("timestamp").sort_index())
