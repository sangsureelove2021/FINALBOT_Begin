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

from core.data.data_source import IDataSource

logger = logging.getLogger(__name__)

# Global lock — iqoptionapi shares a single websocket buffer
_CANDLES_LOCK = threading.Lock()
_CANDLES_TIMEOUT_SEC = 8


class IQOptionAdapter(IDataSource):
    """IQ Option broker adapter — live API only."""

    def __init__(self, email: Optional[str] = None,
                 password: Optional[str] = None,
                 account_type: str = "PRACTICE",
                 api_token: Optional[str] = None):
        """
        Initialize adapter.

        Args:
            email: IQ Option login email (or via IQ_EMAIL env var).
            password: IQ Option password (or via IQ_PASSWORD env var).
            account_type: 'PRACTICE' (demo) or 'REAL'.
            api_token: legacy, unused.
        """
        # Priority: explicit args > env vars > config/settings.json
        if email and password:
            self.email, self.password = email, password
        else:
            from config.config_loader import get_iq_credentials
            self.email, self.password = get_iq_credentials()
        self.account_type = account_type
        self._connected = False
        self.api = None

        if not self.email or not self.password:
            raise RuntimeError(
                "IQ Option credentials missing. Provide email/password "
                "as arguments or set IQ_EMAIL / IQ_PASSWORD env vars."
            )

        try:
            from iqoptionapi.stable_api import IQ_Option
        except ImportError as e:
            logger.exception("iqoptionapi library not installed"); raise Exception(str(e))

        logger.info(f"[CONN] Connecting to IQ Option ({account_type}) as {self.email}...")
        self.api = IQ_Option(self.email, self.password)
        ok, reason = self.api.connect()
        if not ok:
            raise RuntimeError(f"IQ Option login failed: {reason}")

        self.api.change_balance(account_type)

        self._connected = True
        mode = "DEMO" if account_type == "PRACTICE" else "REAL MONEY"
        logger.info(f"[CONN] IQ Option connected ({mode})")
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        self._conn_lock = threading.Lock()
    
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
                        self.api.change_balance(self.account_type)
                        logger.info(" Reconnected")
                    else:
                        logger.error(f"[ERROR] Reconnect failed: {reason}")
                        raise RuntimeError(f"Reconnect failed: {reason}")
            
    def start_stream(self, symbol: str, timeframe: str, count: int) -> None:
        """Subscribe to live websocket stream of candles for this pair and timeframe."""
        if not self._connected or not self.api:
            raise RuntimeError("Cannot start stream: IQ Option not connected or API not initialized")
        size = self._TF_SECONDS[timeframe]
        # start_candles_stream subscribes and seeds maxdict = count candles
        self.api.start_candles_stream(symbol, size, count)
        logger.info(f"[WS] Subscribed live candles stream for {symbol} ({timeframe}, count={count})")
    
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

        # 1. Try fetching from live WebSocket Stream buffer first (0ms latency fallback)
        # Bypass WS stream if we want historical pagination (end_time is set)
        if end_time is None:
            try:
                raw_dict = self.api.get_realtime_candles(symbol, size)
                if raw_dict and isinstance(raw_dict, dict) and len(raw_dict) >= count * 0.8:
                    raw = list(raw_dict.values())
                    df = pd.DataFrame(raw)
                    if not df.empty:
                        df = df.rename(columns={"max": "high", "min": "low"})
                        need = {"from", "open", "close", "high", "low"}
                        if need.issubset(df.columns):
                            df["timestamp"] = pd.to_datetime(df["from"], unit="s")
                            for col in ("open", "close", "high", "low"):
                                df[col] = pd.to_numeric(df[col], errors="coerce")
                            df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0.0)
                            df = df.dropna(subset=["open", "close", "high", "low"])
                            if not df.empty:
                                median_close = float(df["close"].median())
                                symbol_upper = symbol.upper()
                                if "JPY" in symbol_upper:
                                    valid = (50.0 <= median_close <= 300.0)
                                elif "BTC" in symbol_upper:
                                    valid = (1000.0 <= median_close <= 250000.0)
                                elif "ETH" in symbol_upper:
                                    valid = (100.0 <= median_close <= 15000.0)
                                elif "XAU" in symbol_upper or "GOLD" in symbol_upper:
                                    valid = (500.0 <= median_close <= 5000.0)
                                else:
                                    valid = (0.3 <= median_close <= 10.0)
                                
                                if valid:
                                    logger.debug(f"[WS] Retrieved {len(df)} live candles for {symbol} ({timeframe})")
                                    return (df[["timestamp", "open", "high", "low", "close", "volume"]]
                                            .set_index("timestamp").sort_index())
                                else:
                                    raise ValueError("Price out of expected range")
            except Exception as e:
                logger.exception(f"WebSocket fetch failed for {symbol}: {e}"); raise Exception(str(e))
            raise Exception("WebSocket fetch failed: no valid data returned")

        # 2. Fallback to standard REST HTTP request
        def _fetch() -> Optional[pd.DataFrame]:
            with _CANDLES_LOCK:
                try:
                    raw = self.api.get_candles(symbol, size, count, end_timestamp)
                except Exception as e:
                    logger.exception(f"REST fetch failed for {symbol}: {e}"); raise Exception(str(e))
            if not raw:
                raise Exception("REST fetch failed: no data returned")
            df = pd.DataFrame(raw)
            if df.empty:
                raise Exception("REST fetch failed: empty dataframe")
            df = df.rename(columns={"max": "high", "min": "low"})
            need = {"from", "open", "close", "high", "low"}
            if not need.issubset(df.columns):
                raise Exception("REST fetch failed: missing columns")
            df["timestamp"] = pd.to_datetime(df["from"], unit="s")
            for col in ("open", "close", "high", "low"):
                df[col] = pd.to_numeric(df[col], errors="coerce")
            if "volume" in df.columns:
                df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0.0)
            else:
                df["volume"] = 0.0
            df = df.dropna(subset=["open", "close", "high", "low"])
            if df.empty:
                raise Exception("REST fetch failed: empty dataframe after dropna")
            # Sanity check: reject obviously broken price feeds
            median_close = float(df["close"].median())
            is_jpy = "JPY" in symbol.upper()
            if is_jpy and not (50.0 <= median_close <= 300.0):
                raise Exception(f"{symbol} median {median_close} out of JPY range")
            if not is_jpy and not (0.3 <= median_close <= 10.0):
                raise Exception(f"{symbol} median {median_close} out of FX range")
            return (df[["timestamp", "open", "high", "low", "close", "volume"]]
                    .set_index("timestamp").sort_index())

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                df = ex.submit(_fetch).result(timeout=_CANDLES_TIMEOUT_SEC)
        except concurrent.futures.TimeoutError as e:
            logger.exception(f"REST fetch timeout for {symbol}: {e}"); raise Exception(str(e))
        if df is None:
            raise Exception("REST fetch returned None")
        return df
