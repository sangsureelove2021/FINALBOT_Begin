"""
Data Adapter - Market Ingestion Core

หน้าที่: แปลงข้อมูลดิบจาก Broker เป็น Standard Candle Model
ฟังก์ชัน: Mapping Field, Timestamp, Symbol, Timeframe, Type Conversion
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import threading
import time

from data_feed.data_source import IDataSource
from data_feed.csv_queue import CSVQueue
from data_feed.csv_manager import CSVManager
from data_feed.csv_writer import get_file_lock, read_csv_safe
from data_feed.candle_validator import CandleValidator
from data_feed.exceptions import DataFeedError, DataGapError

logger = logging.getLogger(__name__)

# Gap thresholds (will be loaded from config)
_M1_GAP_SEC = 300    # > 5 min gap on M1 → re-fetch 200 candles
_M5_GAP_SEC = 1500   # > 25 min gap on M5 → re-fetch 200 candles
_M15_GAP_SEC = 4500  # > 75 min gap on M15 → re-fetch 200 candles


class DataAdapter(IDataSource):
    """Adapter for data translation and CSV management."""

    def __init__(self, iq_adapter: IDataSource, base_dir: str = "data_base/csv/iq_option", config: Optional[Dict[str, Any]] = None, time_calendar_mgr: Optional[Any] = None):
        """
        Initialize DataAdapter.

        Args:
            iq_adapter: IQ Option instance implementing IDataSource
            base_dir: Base directory for CSV files
            config: Configuration from datafeed_config.json
            time_calendar_mgr: TimeSyncManager instance
        """
        # Initialize with configuration
        if config is None:
            from config_setting.config_loader import load_datafeed_settings
            config = load_datafeed_settings()
        
        super().__init__(config)
        
        # Load data adapter configuration
        adapter_config = config.get("data_feed", {}).get("data_adapter", {})
        
        self._iq = iq_adapter
        self._csv_manager = CSVManager(base_dir, config.get("data_feed", {}).get("csv_manager", {}))
        self._csv_queue = CSVQueue(config.get("data_feed", {}).get("csv_queue", {}))
        
        if time_calendar_mgr is not None:
            self.time_calendar_mgr = time_calendar_mgr
        else:
            from data_feed.time_sync_manager import TimeSyncManager
            self.time_calendar_mgr = TimeSyncManager(data_adapter=self._iq)

        # Load configuration parameters
        self.default_candle_count = adapter_config.get("default_candle_count", 250)
        self.min_candle_count = adapter_config.get("min_candle_count", 21)
        self.m5_seconds = adapter_config.get("m5_seconds", 300)
        self.m15_seconds = adapter_config.get("m15_seconds", 900)
        self.auto_reconnect = adapter_config.get("auto_reconnect", True)
        
        # Zero Tolerance compliance check
        retry_attempts = adapter_config.get("retry_attempts", 0)
        retry_delay = adapter_config.get("retry_delay", 0)
        if retry_attempts > 0 or retry_delay > 0:
            logger.error(f"[DataAdapter] Zero Tolerance VIOLATION: retry_attempts={retry_attempts}, retry_delay={retry_delay}")
            logger.error(f"[DataAdapter] Config must have retry_attempts=0 and retry_delay=0")
            raise RuntimeError("Zero Tolerance: retry mechanisms not allowed")
        
        self.retry_attempts = 0  # Zero Tolerance: no retry allowed
        self.retry_delay = 0  # Zero Tolerance: no retry delay
        self.enable_cache = adapter_config.get("enable_cache", True)
        self.cache_size = adapter_config.get("cache_size", 1000)
        
        logger.info(f"[DataAdapter] Initialized with Zero Tolerance compliance")

        # Per-symbol candle stores
        self._store_m1: Dict[str, Optional[pd.DataFrame]] = {}
        self._store_m5: Dict[str, Optional[pd.DataFrame]] = {}
        self._store_m15: Dict[str, Optional[pd.DataFrame]] = {}

        # Completed candles cache — RAM-only, no disk write
        self._completed_candles: Dict[str, Dict[str, pd.DataFrame]] = {}

        # Track last written block indices to avoid redundant disk writes
        self._last_block_m1: Dict[str, int] = {}
        self._last_block_m5: Dict[str, int] = {}
        self._last_block_m15: Dict[str, int] = {}
        self._m5_csv_written: Dict[str, int] = {}
        self._m15_csv_written: Dict[str, int] = {}

        self._validator = CandleValidator()
        
        logger.info("[DataAdapter] Initialized with configuration")

    def read_csv(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Read CSV file using thread synchronization lock.
        Ensures thread-safe read while CSVWriter or other threads perform writes.
        """
        if not isinstance(file_path, str):
            raise TypeError("file_path must be a string")
        return read_csv_safe(file_path, **kwargs)

    def read_symbol_csv(self, symbol: str, timeframe: str, **kwargs) -> pd.DataFrame:
        """
        Read CSV file for a given symbol and timeframe in a thread-safe manner.
        """
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if not isinstance(timeframe, str):
            raise TypeError("timeframe must be a string")
        file_path = self._csv_manager.get_file_path(symbol, timeframe)
        df = self.read_csv(file_path, **kwargs)
        return self._ensure_utc_datetime_index(df)

    def init_symbol(self, symbol: str, broker_epoch: Optional[float] = None) -> bool:
        """Warm-up a symbol: fetch candles, validate, store in RAM, and write CSV.

        Args:
            symbol: Trading symbol.
            broker_epoch: Broker-synced epoch (from TimeSyncManager.get_broker_epoch()).
                If None, uses self.time_calendar_mgr.get_broker_epoch().
        """
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if broker_epoch is None:
            broker_epoch = self.time_calendar_mgr.get_broker_epoch()

        try:
            # Fetch initial candles (extra buffer so after _drop_forming, count >= 100/250/50)
            m1 = self._iq.get_candles(symbol, 'M1', 110, end_time=broker_epoch)
            m5 = self._iq.get_candles(symbol, 'M5', 260, end_time=broker_epoch)
            m15 = self._iq.get_candles(symbol, 'M15', 60, end_time=broker_epoch)

            if (m1 is None or m1.empty or len(m1) < 2) or \
               (m5 is None or m5.empty) or \
               (m15 is None or m15.empty):
                raise ValueError("Incomplete data during init_symbol — M15 must be fetched directly from broker")

            # Validate data
            self._validator.validate(m1, symbol)
            self._validator.validate(m5, symbol)
            self._validator.validate(m15, symbol)

            # Store data
            self._store_m1[symbol] = m1
            self._store_m5[symbol] = m5
            self._store_m15[symbol] = m15

            # Set initial last_block to -1 to force fresh fetch on first cycle
            self._last_block_m1[symbol] = -1
            self._last_block_m5[symbol] = -1
            self._last_block_m15[symbol] = -1

            # Drop the still-forming last candle on each timeframe using broker_epoch
            m1 = self._drop_forming(m1, broker_epoch, 60)
            m5 = self._drop_forming(m5, broker_epoch, 300)
            m15 = self._drop_forming(m15, broker_epoch, 900)

            # Add age and quality columns to initial candles using broker_epoch
            m1 = self._add_age_and_quality(m1, broker_epoch, 60)
            m5 = self._add_age_and_quality(m5, broker_epoch, 300)
            m15 = self._add_age_and_quality(m15, broker_epoch, 900)

            # Store completed candles in RAM cache
            self._completed_candles[symbol] = {
                'M1': m1,
                'M5': m5,
                'M15': m15
            }

            # Enqueue write to CSV files on SSD disk for all 3 timeframes
            for tf, df in [('M1', m1), ('M5', m5), ('M15', m15)]:
                file_path = self._csv_manager.get_file_path(symbol, tf)
                self._csv_queue.enqueue_write(df, file_path)

            logger.info(f"[DataAdapter] {symbol} initialised in RAM & CSV written — M1:{len(m1)} M5:{len(m5)} M15:{len(m15)}")
            return True

        except Exception as e:
            logger.exception(f"[DataAdapter] Failed to init {symbol}: {e}")
            raise

    def update(self, symbol: str, broker_epoch: Optional[float] = None) -> str:
        """Refresh candle stores, update RAM cache, and write CSV files. Returns symbol string on success."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if broker_epoch is None:
            broker_epoch = self.time_calendar_mgr.get_broker_epoch()
        if not isinstance(broker_epoch, (int, float)):
            raise TypeError("broker_epoch must be a float or int")

        try:
            logger.info(f"[DataAdapter] Starting update for {symbol}")

            current_block_m1 = int(broker_epoch) // 60
            current_block_m5 = int(broker_epoch) // self.m5_seconds
            current_block_m15 = int(broker_epoch) // self.m15_seconds

            # Refresh M1 data
            completed_m1 = self._refresh_m1(symbol, broker_epoch, current_block_m1)
            if completed_m1 is None:
                raise ValueError("M1 refresh failed")

            # Refresh M5 data
            completed_m5 = self._refresh_m5(symbol, broker_epoch, current_block_m5)
            if completed_m5 is None:
                raise ValueError("M5 refresh failed")

            # Refresh M15 (ดึงข้อมูลสดตรงจาก Broker API 100%)
            completed_m15 = self._refresh_m15(symbol, broker_epoch, current_block_m15)
            if completed_m15 is None:
                raise ValueError("M15 refresh failed")

            # Store completed candles in RAM cache
            self._completed_candles[symbol] = {
                'M1': completed_m1,
                'M5': completed_m5,
                'M15': completed_m15
            }

            # Enqueue write to CSV files on SSD disk for all 3 timeframes (8 standard columns)
            for tf, df in [('M1', completed_m1), ('M5', completed_m5), ('M15', completed_m15)]:
                file_path = self._csv_manager.get_file_path(symbol, tf)
                self._csv_queue.enqueue_write(df, file_path)

            # Return symbol string on successful update
            return symbol

        except Exception as e:
            logger.error(f"[DataAdapter] update failed for {symbol}: {e}")
            logger.error(f"[DataAdapter] Zero Tolerance: stopping immediately - no retry allowed")
            raise DataFeedError(f"Zero Tolerance: update failed for {symbol}: {e}") from e

    @staticmethod
    def _ensure_utc_datetime_index(df: Optional[pd.DataFrame]) -> pd.DataFrame:
        """Ensure DataFrame has a valid UTC DatetimeIndex sorted ascending."""
        if df is None or df.empty:
            return df
        out = df.copy()
        
        if 'timestamp' in out.columns and not isinstance(out.index, pd.DatetimeIndex):
            if pd.api.types.is_numeric_dtype(out['timestamp']):
                out['timestamp'] = pd.to_datetime(out['timestamp'], unit='s', utc=True)
            else:
                out['timestamp'] = pd.to_datetime(out['timestamp'], utc=True)
            out = out.set_index('timestamp', drop=False)
            
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

    def _refresh_m1(self, symbol: str, broker_epoch: float, current_block: int) -> Optional[pd.DataFrame]:
        block = current_block
        block_changed = False

        if self._store_m1.get(symbol) is None:
            logger.info(f"[DataAdapter] Initializing M1 data for {symbol}")
            if hasattr(self._iq, 'update_with_streaming'):
                df = self._iq.update_with_streaming(symbol, 'M1', 110)
            else:
                df = self._iq.get_candles(symbol, 'M1', 110, end_time=broker_epoch)
            if df is None or df.empty or len(df) < 2:
                raise ValueError("M1 fetch failed")
            self._store_m1[symbol] = self._ensure_utc_datetime_index(df)
            self._last_block_m1[symbol] = block
            block_changed = True
        elif block != self._last_block_m1.get(symbol):
            logger.info(f"[DataAdapter] Refreshing M1 data for {symbol}")
            if hasattr(self._iq, 'update_with_streaming'):
                fresh = self._iq.update_with_streaming(symbol, 'M1', 110)
            else:
                fresh = self._iq.get_candles(symbol, 'M1', 110, end_time=broker_epoch)
            if fresh is not None and not fresh.empty:
                self._store_m1[symbol] = self._merge(
                    self._store_m1[symbol], fresh,
                    gap_threshold=_M1_GAP_SEC,
                    label=f"M1 {symbol}",
                    timeframe="M1",
                    max_candles=110
                )
                self._last_block_m1[symbol] = block
                block_changed = True
            else:
                raise DataFeedError(f"M1 fetch failed for {symbol} — Zero Tolerance: stopping immediately")

        completed = self._drop_forming(self._store_m1[symbol], broker_epoch, 60)
        if completed.empty:
            raise ValueError("M1 completed is empty")

        completed = self._add_age_and_quality(completed, broker_epoch, 60)

        if block_changed:
            self._validator.validate(completed, symbol)

        return completed

    def _refresh_m5(self, symbol: str, broker_epoch: float, current_block: int) -> Optional[pd.DataFrame]:
        # Note: TimeframeSync is NOT used in this implementation
        # M1, M5, M15 are fetched separately and merged independently
        block = current_block
        block_changed = False

        if self._store_m5.get(symbol) is None:
            logger.info(f"[DataAdapter] Initializing M5 data for {symbol}")
            if hasattr(self._iq, 'update_with_streaming'):
                df = self._iq.update_with_streaming(symbol, 'M5', 260)
            else:
                df = self._iq.get_candles(symbol, 'M5', 260, end_time=broker_epoch)
            if df is None or df.empty or len(df) < self.min_candle_count:
                raise ValueError("M5 fetch failed")
            self._store_m5[symbol] = self._ensure_utc_datetime_index(df)
            self._last_block_m5[symbol] = block
            block_changed = True
        elif block != self._last_block_m5.get(symbol):
            logger.info(f"[DataAdapter] Refreshing M5 data for {symbol}")
            if hasattr(self._iq, 'update_with_streaming'):
                fresh = self._iq.update_with_streaming(symbol, 'M5', 260)
            else:
                fresh = self._iq.get_candles(symbol, 'M5', 260, end_time=broker_epoch)
            if fresh is not None and not fresh.empty:
                self._store_m5[symbol] = self._merge(
                    self._store_m5[symbol], fresh,
                    gap_threshold=_M5_GAP_SEC,
                    label=f"M5 {symbol}",
                    timeframe="M5",
                    max_candles=260
                )
                self._last_block_m5[symbol] = block
                block_changed = True
            else:
                raise DataFeedError(f"M5 fetch failed for {symbol} — Zero Tolerance: stopping immediately")

        completed = self._drop_forming(self._store_m5[symbol], broker_epoch, 300)
        completed = self._add_age_and_quality(completed, broker_epoch, 300)

        if block_changed:
            self._validator.validate(completed, symbol)

        return completed

    def _refresh_m15(self, symbol: str, broker_epoch: float, current_block: int) -> Optional[pd.DataFrame]:
        # Note: M15 does NOT resample from M5 - fetched directly from Broker API
        # TimeframeSync is NOT used in this implementation
        block = current_block
        block_changed = False

        if self._store_m15.get(symbol) is None:
            logger.info(f"[DataAdapter] Initializing M15 data for {symbol}")
            df = self._iq.get_candles(symbol, 'M15', 60, end_time=broker_epoch)
            if df is None or df.empty or len(df) < self.min_candle_count:
                raise ValueError("M15 fetch failed")
            self._store_m15[symbol] = self._ensure_utc_datetime_index(df)
            self._last_block_m15[symbol] = block
            block_changed = True
        elif block != self._last_block_m15.get(symbol):
            logger.info(f"[DataAdapter] Refreshing M15 data for {symbol}")
            fresh_m15 = self._iq.get_candles(symbol, 'M15', 10, end_time=broker_epoch)
            if fresh_m15 is not None and not fresh_m15.empty:
                # Merge with gap check - keep last 60 candles for more historical context
                self._store_m15[symbol] = self._merge(
                    self._store_m15[symbol],
                    fresh_m15,
                    gap_threshold=_M15_GAP_SEC,
                    label=f"M15 {symbol}",
                    timeframe="M15",
                    max_candles=60
                )
                self._last_block_m15[symbol] = block
                block_changed = True
            else:
                raise DataFeedError(f"M15 fetch failed for {symbol} — Zero Tolerance: stopping immediately")

        completed = self._drop_forming(self._store_m15[symbol], broker_epoch, 900)
        if completed.empty:
            raise ValueError(f"M15 completed is empty for {symbol}")

        completed = self._add_age_and_quality(completed, broker_epoch, 900)

        if block_changed:
            self._validator.validate(completed, symbol)

        return completed

    @staticmethod
    def _add_age_and_quality(df: pd.DataFrame, broker_epoch: float, tf_seconds: int) -> pd.DataFrame:
        """
        Calculate age (ms) from actual candle close time (candle start + tf_seconds) using broker_epoch
        and quality ('FRESH' if age <= threshold else 'STALE').
        Threshold: 2 * tf_seconds * 1000 ms (M1: 120,000ms, M5: 600,000ms, M15: 1,800,000ms)
        Also formats the DataFrame into standard 8 columns:
        ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'age', 'quality']
        """
        if df is None or df.empty:
            return df

        df_copy = DataAdapter._ensure_utc_datetime_index(df)

        # Convert index to array of epoch timestamps in seconds
        dt_index = df_copy.index
        start_epochs = np.array([ts.timestamp() for ts in dt_index])

        close_epochs = start_epochs + tf_seconds
        age_ms_array = np.maximum(0, ((broker_epoch - close_epochs) * 1000)).astype(int)

        # Threshold for FRESH vs STALE (2 * tf_seconds * 1000 ms)
        threshold_ms = tf_seconds * 2 * 1000
        quality_array = np.where(age_ms_array <= threshold_ms, 'FRESH', 'STALE')

        df_copy['age'] = age_ms_array
        df_copy['quality'] = quality_array

        # Ensure 'timestamp' column exists and is UTC datetime while preserving DatetimeIndex
        if 'timestamp' not in df_copy.columns:
            df_copy['timestamp'] = df_copy.index
        else:
            df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'], utc=True)

        # Ensure exact standard 8 columns order
        standard_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'age', 'quality']
        df_copy = df_copy[[c for c in standard_cols if c in df_copy.columns]]
        return DataAdapter._ensure_utc_datetime_index(df_copy)

    @staticmethod
    def _calculate_quality(age_ms: int, threshold_ms: int = 120000) -> str:
        """Calculate data quality based on age (FRESH or STALE only)."""
        if not isinstance(age_ms, (int, float)):
            raise TypeError("age_ms must be an int or float")
        return "FRESH" if age_ms <= threshold_ms else "STALE"

    def _merge(self, stored: Optional[pd.DataFrame], fresh: Optional[pd.DataFrame],
                gap_threshold: float, label: str, timeframe: str, max_candles: int = 250) -> pd.DataFrame:
        """Merge stored and fresh data with gap detection."""
        if stored is None or stored.empty:
            raise ValueError("Stored DataFrame is empty in _merge")
        if fresh is None or fresh.empty:
            raise ValueError("Fresh DataFrame is empty in _merge")

        stored = self._ensure_utc_datetime_index(stored)
        fresh = self._ensure_utc_datetime_index(fresh)

        last_ts = stored.index[-1]
        first_ts = fresh.index[0]
        gap_sec = (first_ts - last_ts).total_seconds()

        if gap_sec > gap_threshold:
            logger.error(f"[DataAdapter] {label}: FAIL-FAST Data gap detected ({gap_sec}s > {gap_threshold}s)")
            raise DataGapError(f"FAIL-FAST: Data gap detected in candles for {label} ({gap_sec}s > {gap_threshold}s)")

        overlap = stored.index.intersection(fresh.index)
        if len(overlap) > 1 and 'close' in stored.columns and 'close' in fresh.columns:
            check = overlap[:-1][-4:]
            if len(check) > 0:
                if not stored.loc[check, 'close'].equals(fresh.loc[check, 'close']):
                    logger.warning(f"[DataAdapter] {label}: broker revised closed candles — corrected")

        combined = pd.concat([stored, fresh])
        combined = combined[~combined.index.duplicated(keep='last')]
        combined = self._ensure_utc_datetime_index(combined)
        return combined.tail(max_candles)

    @staticmethod
    def _drop_forming(df: Optional[pd.DataFrame], broker_epoch: float, tf_seconds: int) -> pd.DataFrame:
        """Drop forming candles (incomplete latest candle)."""
        if df is None or df.empty:
            raise ValueError("DataFrame is empty in _drop_forming")
        df = DataAdapter._ensure_utc_datetime_index(df)
        last_candle_start = df.index[-1].timestamp()
        if (broker_epoch - last_candle_start) < tf_seconds:
            res = df.iloc[:-1].copy()
        else:
            res = df.copy()
        return DataAdapter._ensure_utc_datetime_index(res)

    # ── RAM Access Methods (No Disk I/O) ─────────────────────────────
    def get_candles_ram(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Return completed candles directly from RAM. No CSV read."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if symbol not in self._completed_candles:
            raise ValueError(f"FAIL-FAST: No candle data in RAM for {symbol}")
        result = {}
        for tf, df in self._completed_candles[symbol].items():
            clean = df[~df.index.duplicated(keep='last')]
            result[tf] = clean
        return result

    def get_latest_close(self, symbol: str) -> float:
        """Return latest M1 close price from RAM. No CSV read."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        candles = self._completed_candles.get(symbol)
        if candles is None or 'M1' not in candles:
            raise ValueError(f"FAIL-FAST: No M1 data in RAM for {symbol}")
        m1 = candles['M1']
        if m1.empty or 'close' not in m1.columns:
            raise ValueError(f"FAIL-FAST: M1 data empty or missing 'close' column for {symbol}")
        return float(m1['close'].iloc[-1])

    def check_warmup(self, symbol: str) -> bool:
        """Check warmup data sufficiency from RAM. No CSV read."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        reqs = {"M1": 100, "M5": 250, "M15": 50}
        candles = self._completed_candles.get(symbol)
        if candles is None:
            logger.warning(f"[{symbol}] No candle data in RAM")
            return False
        for tf, req_len in reqs.items():
            df = candles.get(tf)
            if df is None or len(df) < req_len:
                logger.warning(f"[{symbol}] Insufficient {tf} data in RAM: has {len(df) if df is not None else 0}, required >={req_len}")
                return False
        return True

    def is_connected(self) -> bool:
        """Check connection status."""
        return self._iq.is_connected()

    def connect(self) -> None:
        """Connect to data source."""
        return self._iq.connect()

    def disconnect(self) -> None:
        """Disconnect from data source."""
        return self._iq.disconnect()

    def start_stream(self, symbol: str, timeframe: str, count: int) -> None:
        """Start streaming for symbol and timeframe."""
        return self._iq.start_stream(symbol, timeframe, count)

    async def get_historical_candles(self, symbol: str, timeframe: int, count: int, end_time: float):
        """Get historical candles (delegated to IQ adapter)."""
        # Convert timeframe string to int if needed
        if isinstance(timeframe, str):
            from config_setting.config_loader import get_timeframe_sync_config
            tf_config = get_timeframe_sync_config()
            timeframe_seconds = tf_config["timeframe_minutes"].get(timeframe, 60) * 60
        else:
            timeframe_seconds = timeframe
            
        return await self._iq.get_historical_candles(symbol, timeframe_seconds, count, end_time)
