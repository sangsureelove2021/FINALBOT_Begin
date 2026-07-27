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
from data_feed.candle_validator import CandleValidator
from data_feed.csv_queue import CSVQueue
from data_feed.csv_manager import CSVManager
from data_feed.csv_writer import get_file_lock, read_csv_safe
from data_feed.data_monitor import DataMonitor
from data_feed.anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)

# Gap thresholds (will be loaded from config)
_M1_GAP_SEC = 300    # > 5 min gap on M1 → re-fetch 200 candles
_M5_GAP_SEC = 1500   # > 25 min gap on M5 → re-fetch 200 candles
_M15_GAP_SEC = 4500  # > 75 min gap on M15 → re-fetch 200 candles


class DataAdapter(IDataSource):
    """Adapter for data translation and CSV management."""

    def __init__(self, iq_adapter: IDataSource, base_dir: str = "data_base/csv/iq_option", config: Optional[Dict[str, Any]] = None):
        """
        Initialize DataAdapter.

        Args:
            iq_adapter: IQ Option instance implementing IDataSource
            base_dir: Base directory for CSV files
            config: Configuration from datafeed_config.json
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
        self._data_monitor = DataMonitor(config.get("data_feed", {}).get("data_monitor", {}))

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

        # Track last written block indices to avoid redundant disk writes
        self._last_block_m5: Dict[str, int] = {}
        self._last_block_m15: Dict[str, int] = {}
        self._m5_csv_written: Dict[str, int] = {}
        self._m15_csv_written: Dict[str, int] = {}

        # Initialize anomaly detector
        self._anomaly_detector = AnomalyDetector(config)
        self._anomaly_fail_count = 0
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
        return self.read_csv(file_path, **kwargs)

    def init_symbol(self, symbol: str) -> bool:
        """Warm-up a symbol: fetch 250 candles, validate and write CSVs."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")

        try:
            # Fetch initial candles
            m1 = self._iq.get_candles(symbol, 'M1', 100)
            m5 = self._iq.get_candles(symbol, 'M5', 250)
            m15 = self._iq.get_candles(symbol, 'M15', 50)

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

            # Set up block tracking using broker time offset if available
            time_offset = getattr(self._iq, 'time_offset', 0.0) if hasattr(self._iq, 'time_offset') else 0.0
            epoch_now = int(datetime.now(timezone.utc).timestamp() + time_offset)
            self._last_block_m5[symbol] = epoch_now // self.m5_seconds
            self._last_block_m15[symbol] = epoch_now // self.m15_seconds

            # Enqueue initial writes
            self._csv_queue.enqueue_write(m1, self._csv_manager.get_file_path(symbol, "M1"))
            self._csv_queue.enqueue_write(m5, self._csv_manager.get_file_path(symbol, "M5"))
            self._csv_queue.enqueue_write(m15, self._csv_manager.get_file_path(symbol, "M15"))

            logger.info(f"[DataAdapter] {symbol} initialised — M1:{len(m1)} M5:{len(m5)} M15:{len(m15)}")
            return True

        except Exception as e:
            logger.exception(f"[DataAdapter] Failed to init {symbol}: {e}")
            raise

    def update(self, symbol: str, broker_epoch: float) -> Optional[Tuple[str, float, dict]]:
        """Refresh candle stores and write CSVs via background queue."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if not isinstance(broker_epoch, (int, float)):
            raise TypeError("broker_epoch must be a float or int")

        try:
            logger.info(f"[DataAdapter] Starting update for {symbol}")
            self._data_monitor.update_connection_status(self._iq.is_connected())

            now_naive = datetime.fromtimestamp(broker_epoch, tz=timezone.utc).replace(tzinfo=None)
            current_block_m5 = int(broker_epoch) // self.m5_seconds
            current_block_m15 = int(broker_epoch) // self.m15_seconds

            # Refresh M1 data
            logger.info(f"[DataAdapter] Refreshing M1 data for {symbol}")
            completed_m1 = self._refresh_m1(symbol, now_naive)
            if completed_m1 is None:
                raise ValueError("M1 refresh failed")
            logger.info(f"[DataAdapter] M1 data refresh completed for {symbol}")

            # Refresh M5 data
            logger.info(f"[DataAdapter] Refreshing M5 data for {symbol}")
            completed_m5 = self._refresh_m5(symbol, now_naive, current_block_m5)
            if completed_m5 is None:
                raise ValueError("M5 refresh failed")
            logger.info(f"[DataAdapter] M5 data refresh completed for {symbol}")

            # Refresh M15 (ดึงข้อมูลสดตรงจาก Broker API 100%)
            logger.info(f"[DataAdapter] Refreshing M15 data for {symbol}")
            completed_m15 = self._refresh_m15(symbol, now_naive, current_block_m15)
            logger.info(f"[DataAdapter] M15 data refresh completed for {symbol}")

            # Get latest data
            store_m1_df = self._store_m1[symbol]
            store_m5_df = self._store_m5[symbol]

            m1_last = store_m1_df.iloc[-1]
            m5_last = store_m5_df.iloc[-1]

            # Calculate metrics (convert naive candle timestamps to UTC epoch to avoid local timezone offset errors)
            m1_open = float(m1_last['open'])
            if hasattr(m1_last.name, 'timestamp'):
                m1_ts_utc = m1_last.name.tz_localize(timezone.utc).timestamp() if m1_last.name.tz is None else m1_last.name.timestamp()
            else:
                m1_ts_utc = pd.to_datetime(m1_last.name, utc=True).timestamp()
            m1_age = max(0, int((broker_epoch - m1_ts_utc) * 1000))
            m1_quality = self._calculate_quality(m1_age)
            self._data_monitor.report_latency(symbol, "M1", m1_age)

            m5_open = float(m5_last['open'])
            if hasattr(m5_last.name, 'timestamp'):
                m5_ts_utc = m5_last.name.tz_localize(timezone.utc).timestamp() if m5_last.name.tz is None else m5_last.name.timestamp()
            else:
                m5_ts_utc = pd.to_datetime(m5_last.name, utc=True).timestamp()
            m5_age = max(0, int((broker_epoch - m5_ts_utc) * 1000))
            m5_quality = self._calculate_quality(m5_age)
            self._data_monitor.report_latency(symbol, "M5", m5_age)

            # Rules: OHLCV must NOT be passed via RAM.
            
            # Log anomaly statistics
            try:
                stats = self._anomaly_detector.get_statistics()
                logger.info(f"[DataAdapter] Anomaly statistics for {symbol}: {stats}")
            except Exception as e:
                logger.error(f"[DataAdapter] Failed to get anomaly statistics: {e}")
            
            return symbol

        except Exception as e:
            logger.error(f"[DataAdapter] update failed for {symbol}: {e}")
            logger.error(f"[DataAdapter] Zero Tolerance: stopping immediately - no retry allowed")
            raise Exception(f"Zero Tolerance: update failed for {symbol}: {e}")

    def _refresh_m1(self, symbol: str, now_naive: datetime) -> Optional[pd.DataFrame]:
        if self._store_m1[symbol] is None:
            df = self._iq.get_candles(symbol, 'M1', 100)
            if df is None or df.empty or len(df) < 2:
                raise ValueError("M1 fetch failed")
            self._store_m1[symbol] = df
        else:
            fresh = self._iq.get_candles(symbol, 'M1', 3)
            if fresh is not None and not fresh.empty:
                self._store_m1[symbol] = self._merge(
                    self._store_m1[symbol], fresh,
                    gap_threshold=_M1_GAP_SEC,
                    refetch_fn=lambda: self._iq.get_candles(symbol, 'M1', 100),
                    label=f"M1 {symbol}",
                    timeframe="M1",
                    max_candles=100
                )
            else:
                raise Exception(f"M1 fetch failed for {symbol} — Zero Tolerance: stopping immediately")

        completed = self._drop_forming(self._store_m1[symbol], now_naive, 60)
        if completed.empty:
            raise ValueError("M1 completed is empty")

        # Run anomaly detection on M1 data
        try:
            start_time = time.time()
            completed = self._anomaly_detector.detect_anomalies(completed, symbol)
            end_time = time.time()
            response_time = end_time - start_time

            # Log response time for health check
            self._anomaly_detector.check_health(response_time, symbol)

            logger.info(f"[DataAdapter] M1 anomaly detection completed for {symbol} in {response_time:.3f}s")
        except Exception as e:
            logger.error(f"[DataAdapter] Anomaly detection failed for {symbol}: {e}")
            self._anomaly_fail_count += 1
            if self._anomaly_fail_count > 5:
                logger.warning(f"[DataAdapter] Anomaly detection has failed {self._anomaly_fail_count} times")
            # Zero Tolerance: stop immediately if anomaly detection fails
            raise RuntimeError(f"Zero Tolerance: Anomaly detection failed for {symbol}: {e}")

        self._validator.validate(completed, symbol)
        self._csv_queue.enqueue_write(completed, self._csv_manager.get_file_path(symbol, "M1"))
        return completed

    def _refresh_m5(self, symbol: str, now_naive: datetime, current_block: int) -> Optional[pd.DataFrame]:
        # Note: TimeframeSync is NOT used in this implementation
        # M1, M5, M15 are fetched separately and merged independently
        block = current_block
        block_changed = False

        if self._store_m5[symbol] is None:
            df = self._iq.get_candles(symbol, 'M5', 250)
            if df is None or df.empty or len(df) < self.min_candle_count:
                raise ValueError("M5 fetch failed")
            self._store_m5[symbol] = df
            self._last_block_m5[symbol] = block
            block_changed = True
        elif block != self._last_block_m5.get(symbol):
            fresh = self._iq.get_candles(symbol, 'M5', 3)
            if fresh is not None and not fresh.empty:
                self._store_m5[symbol] = self._merge(
                    self._store_m5[symbol], fresh,
                    gap_threshold=_M5_GAP_SEC,
                    refetch_fn=lambda: self._iq.get_candles(symbol, 'M5', 250),
                    label=f"M5 {symbol}",
                    timeframe="M5",
                    max_candles=250
                )
                self._last_block_m5[symbol] = block
                block_changed = True
            else:
                raise Exception(f"M5 fetch failed for {symbol} — Zero Tolerance: stopping immediately")

        completed = self._drop_forming(self._store_m5[symbol], now_naive, 300)

        # Run anomaly detection on M5 data
        try:
            completed = self._anomaly_detector.detect_anomalies(completed, symbol)
            logger.info(f"[DataAdapter] M5 anomaly detection completed for {symbol}")
        except Exception as e:
            logger.error(f"[DataAdapter] M5 anomaly detection failed for {symbol}: {e}")
            self._anomaly_fail_count += 1
            if self._anomaly_fail_count > 5:
                logger.warning(f"[DataAdapter] M5 anomaly detection has failed {self._anomaly_fail_count} times")

        # Write CSV only when the 5-min block changes or initial store is loaded
        if block_changed:
            self._validator.validate(completed, symbol)
            self._csv_queue.enqueue_write(completed, self._csv_manager.get_file_path(symbol, "M5"))

        return completed

    def _refresh_m15(self, symbol: str, now_naive: datetime, current_block: int) -> Optional[pd.DataFrame]:
        # Note: M15 does NOT resample from M5 - fetched directly from Broker API
        # TimeframeSync is NOT used in this implementation
        block = current_block
        block_changed = False

        if self._store_m15[symbol] is None:
            df = self._iq.get_candles(symbol, 'M15', 50)
            if df is None or df.empty or len(df) < self.min_candle_count:
                raise ValueError("M15 fetch failed")
            self._store_m15[symbol] = df
            self._last_block_m15[symbol] = block
            block_changed = True
        elif block != self._last_block_m15.get(symbol):
            # Fetch M15 directly from Broker API (3 candles for update)
            fresh_m15 = self._iq.get_candles(symbol, 'M15', 3)
            if fresh_m15 is None or fresh_m15.empty:
                raise Exception(f"Fresh M15 fetch failed for {symbol} — Zero Tolerance: stopping immediately")
            
            # Merge with gap check - keep last 50 candles (matching max_candles param)
            self._store_m15[symbol] = self._merge(
                self._store_m15[symbol] if self._store_m15[symbol] is not None else fresh_m15,
                fresh_m15,
                gap_threshold=_M15_GAP_SEC,
                refetch_fn=lambda: self._iq.get_candles(symbol, 'M15', 50),
                label=f"M15 {symbol}",
                timeframe="M15",
                max_candles=50
            )
            self._last_block_m15[symbol] = block
            block_changed = True

        completed = self._drop_forming(self._store_m15[symbol], now_naive, 900)

        # Run anomaly detection on M15 data
        try:
            completed = self._anomaly_detector.detect_anomalies(completed, symbol)
            logger.info(f"[DataAdapter] M15 anomaly detection completed for {symbol}")
        except Exception as e:
            logger.error(f"[DataAdapter] M15 anomaly detection failed for {symbol}: {e}")
            self._anomaly_fail_count += 1
            if self._anomaly_fail_count > 5:
                logger.warning(f"[DataAdapter] M15 anomaly detection has failed {self._anomaly_fail_count} times")

        # Write CSV only when the 15-min block changes or initial store is loaded
        if block_changed:
            self._validator.validate(completed, symbol)
            self._csv_queue.enqueue_write(completed, self._csv_manager.get_file_path(symbol, "M15"))

        return completed

    @staticmethod
    def _calculate_quality(age_ms: int) -> str:
        """Calculate data quality based on age."""
        if age_ms < 360000:
            return "HIGH"
        elif age_ms < 480000:
            return "MEDIUM"
        elif age_ms < 600000:
            return "LOW"
        else:
            return "STALE"

    def _merge(self, stored: Optional[pd.DataFrame], fresh: Optional[pd.DataFrame],
                gap_threshold: float, refetch_fn, label: str, timeframe: str, max_candles: int = 250) -> pd.DataFrame:
        """Merge stored and fresh data with gap detection."""
        if stored is None or stored.empty:
            raise ValueError("Stored DataFrame is empty in _merge")
        if fresh is None or fresh.empty:
            raise ValueError("Fresh DataFrame is empty in _merge")

        last_ts = stored.index[-1]
        first_ts = fresh.index[0]
        gap_sec = (first_ts - last_ts).total_seconds()

        if gap_sec > gap_threshold:
            self._data_monitor.report_gap(label.split()[1], timeframe, gap_sec)
            full = refetch_fn()
            if full is not None and not full.empty:
                return full
            raise ValueError("Refetch failed after gap detection")

        overlap = stored.index.intersection(fresh.index)
        if len(overlap) > 1 and 'close' in stored.columns and 'close' in fresh.columns:
            check = overlap[:-1][-4:]
            if len(check) > 0:
                if not stored.loc[check, 'close'].equals(fresh.loc[check, 'close']):
                    logger.warning(f"[DataAdapter] {label}: broker revised closed candles — corrected")

        combined = pd.concat([stored, fresh])
        combined = combined[~combined.index.duplicated(keep='last')].sort_index()
        return combined.tail(max_candles)

    @staticmethod
    def _drop_forming(df: Optional[pd.DataFrame], now_naive: datetime, tf_seconds: int) -> pd.DataFrame:
        """Drop forming candles (incomplete latest candle)."""
        if df is None or df.empty:
            raise ValueError("DataFrame is empty in _drop_forming")
        age = (now_naive - df.index[-1]).total_seconds()
        if age < tf_seconds:
            return df.iloc[:-1].copy()
        return df.copy()

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
