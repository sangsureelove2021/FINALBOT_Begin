"""
Data Adapter - Market Ingestion Core (Coordinator)

หน้าที่: ประสานงานระหว่าง DataValidator, CandleProcessor, และ RAMCacheStore
ฟังก์ชัน: Mapping Field, Timestamp, Symbol, Timeframe, Type Conversion
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import threading
import time

from data_feed.bridge_adapter.abstract_class import IDataSource
from data_feed.csv_queue import CSVQueue
from data_feed.csv_manager import CSVManager
from data_feed.csv_writer import get_file_lock, read_csv_safe
from data_feed.exceptions import DataFeedError, DataGapError

# Import new modular components
from data_feed.data_validator import DataValidator, CandleValidator
from data_feed.data_processor import (
    drop_forming,
    merge_candles,
    add_age_and_quality,
    check_continuity,
    process_candle_refresh
)
from data_feed.data_cache_store import RAMCacheStore

logger = logging.getLogger(__name__)

# Gap thresholds are loaded from config inside DataAdapter.__init__


class DataAdapter(IDataSource):
    """
    Adapter for data translation and CSV management.
    Acts as a Coordinator orchestrating DataValidator, CandleProcessor, and RAMCacheStore.
    """

    def __init__(self, broker_adapter: IDataSource, time_sync_manager: Any, base_dir: str = "data_base/csv/iq_option", config: Optional[Dict[str, Any]] = None):
        """
        Initialize DataAdapter.

        Args:
            broker_adapter: Broker adapter instance implementing IDataSource
            time_sync_manager: TimeSyncManager instance
            base_dir: Base directory for CSV files
            config: Configuration from datafeed_config.json
        """
        # Load data adapter configuration from centralized config
        adapter_config = config.get("data_feed", {}).get("data_adapter", {})
        
        self._broker = broker_adapter
        self._csv_manager = CSVManager(base_dir, config.get("data_feed", {}).get("csv_manager", {}))
        self._csv_queue = CSVQueue(config.get("data_feed", {}).get("csv_queue", {}))
        
        if time_sync_manager is None:
            raise ValueError("FAIL-FAST: time_sync_manager is a required argument.")
        self.time_calendar_mgr = time_sync_manager

        # Load configuration parameters
        self.default_candle_count = adapter_config.get("default_candle_count", 250)
        self.min_candle_count = adapter_config.get("min_candle_count", 21)
        self.m5_seconds = adapter_config.get("m5_seconds", 300)
        self.m15_seconds = adapter_config.get("m15_seconds", 900)
        self.auto_reconnect = adapter_config.get("auto_reconnect", True)
        
        self.m1_gap_sec = adapter_config.get("m1_gap_sec", 300)
        self.m5_gap_sec = adapter_config.get("m5_gap_sec", 1500)
        self.m15_gap_sec = adapter_config.get("m15_gap_sec", 4500)
        
        # Zero Tolerance compliance check - reject retry mechanisms
        retry_attempts = adapter_config.get("retry_attempts", 0)
        retry_delay = adapter_config.get("retry_delay", 0)
        if retry_attempts > 0 or retry_delay > 0:
            logger.error(f"[DataAdapter] Zero Tolerance VIOLATION: retry_attempts={retry_attempts}, retry_delay={retry_delay}")
            logger.error(f"[DataAdapter] Config must have retry_attempts=0 and retry_delay=0")
            raise RuntimeError("Zero Tolerance: retry mechanisms not allowed in config")
        
        self.retry_attempts = 0  # Zero Tolerance: no retry allowed
        self.retry_delay = 0  # Zero Tolerance: no retry delay
        self.enable_cache = adapter_config.get("enable_cache", True)
        self.cache_size = adapter_config.get("cache_size", 1000)
        
        # Initialize RAM cache store
        self._cache = RAMCacheStore()
        
        # Initialize validator
        self._validator = DataValidator()
        
        logger.info("[DataAdapter] Initialized with Zero Tolerance compliance using modular components")

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
        return DataValidator.ensure_utc_datetime_index(df)

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
            # Fetch initial candles (extra buffer so after drop_forming, count >= 100/250/50)
            m1 = self._broker.get_candles(symbol, 'M1', 110, end_time=broker_epoch)
            m5 = self._broker.get_candles(symbol, 'M5', 260, end_time=broker_epoch)
            m15 = self._broker.get_candles(symbol, 'M15', 60, end_time=broker_epoch)

            if (m1 is None or m1.empty or len(m1) < 2) or \
               (m5 is None or m5.empty) or \
               (m15 is None or m15.empty):
                raise ValueError(f"Incomplete data during init_symbol for {symbol} — M1:{len(m1) if m1 is not None else 0}, M5:{len(m5) if m5 is not None else 0}, M15:{len(m15) if m15 is not None else 0}")

            # Pre-warm WebSocket Stream for M1
            self.start_stream(symbol, 'M1', 120)

            # Validate data using DataValidator
            self._validator.validate(m1, symbol)
            self._validator.validate(m5, symbol)
            self._validator.validate(m15, symbol)

            # Store data in cache
            self._cache.set_store_data('M1', symbol, m1)
            self._cache.set_store_data('M5', symbol, m5)
            self._cache.set_store_data('M15', symbol, m15)

            # Set initial last_block to -1 to force fresh fetch on first cycle
            self._cache.set_last_block_value('M1', symbol, -1)
            self._cache.set_last_block_value('M5', symbol, -1)
            self._cache.set_last_block_value('M15', symbol, -1)

            # Drop the still-forming last candle on each timeframe using broker_epoch
            m1_completed = drop_forming(m1, broker_epoch, 60)
            m5_completed = drop_forming(m5, broker_epoch, 300)
            m15_completed = drop_forming(m15, broker_epoch, 900)

            # Add age and quality columns to initial candles using broker_epoch
            m1_completed = add_age_and_quality(m1_completed, broker_epoch, 60)
            m5_completed = add_age_and_quality(m5_completed, broker_epoch, 300)
            m15_completed = add_age_and_quality(m15_completed, broker_epoch, 900)

            # Store completed candles in RAM cache
            self._cache.set_completed_candles(symbol, {
                'M1': m1_completed,
                'M5': m5_completed,
                'M15': m15_completed
            })

            # Enqueue write to CSV files on SSD disk for all 3 timeframes
            for tf, df in [('M1', m1_completed), ('M5', m5_completed), ('M15', m15_completed)]:
                file_path = self._csv_manager.get_file_path(symbol, tf)
                self._csv_queue.enqueue_write(df, file_path)

            logger.info(f"[DataAdapter] {symbol} initialised in RAM & CSV written — M1:{len(m1_completed)} M5:{len(m5_completed)} M15:{len(m15_completed)}")
            return True

        except Exception as e:
            logger.exception(f"[DataAdapter] Failed to init {symbol}: {e}")
            raise

    initialize = init_symbol

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

            # Refresh M1 data using process_candle_refresh
            completed_m1 = process_candle_refresh(
                symbol=symbol,
                broker_epoch=broker_epoch,
                store_dict=self._cache.get_store('M1'),
                last_block_dict=self._cache.get_last_block('M1'),
                data_source=self._broker,
                timeframe='M1',
                tf_seconds=60,
                max_candles=110,
                gap_threshold=self.m1_gap_sec,
                validator=self._validator,
                current_block=current_block_m1
            )
            if completed_m1 is None:
                raise ValueError("M1 refresh failed")

            # Refresh M5 data using process_candle_refresh
            completed_m5 = process_candle_refresh(
                symbol=symbol,
                broker_epoch=broker_epoch,
                store_dict=self._cache.get_store('M5'),
                last_block_dict=self._cache.get_last_block('M5'),
                data_source=self._broker,
                timeframe='M5',
                tf_seconds=300,
                max_candles=260,
                gap_threshold=self.m5_gap_sec,
                validator=self._validator,
                current_block=current_block_m5
            )
            if completed_m5 is None:
                raise ValueError("M5 refresh failed")

            # Refresh M15 data using process_candle_refresh
            completed_m15 = process_candle_refresh(
                symbol=symbol,
                broker_epoch=broker_epoch,
                store_dict=self._cache.get_store('M15'),
                last_block_dict=self._cache.get_last_block('M15'),
                data_source=self._broker,
                timeframe='M15',
                tf_seconds=900,
                max_candles=60,
                gap_threshold=self.m15_gap_sec,
                validator=self._validator,
                current_block=current_block_m15
            )
            if completed_m15 is None:
                raise ValueError("M15 refresh failed")

            # Store completed candles in RAM cache
            self._cache.set_completed_candles(symbol, {
                'M1': completed_m1,
                'M5': completed_m5,
                'M15': completed_m15
            })

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

    # ── RAM Access Methods (No Disk I/O) ─────────────────────────────
    def get_candles_ram(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """Return completed candles directly from RAM. No CSV read."""
        return self._cache.get_candles_ram(symbol)
    
    def get_candles(self, symbol: str, timeframe: str = 'M1', 
                    count: int = 100, end_time: Optional[float] = None) -> pd.DataFrame:
        """Fetch candle data from broker adapter.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe ('M1', 'M5', 'M15')
            count: Number of candles to fetch
            end_time: End timestamp for fetching
            
        Returns:
            DataFrame with candle data
        """
        return self._broker.get_candles(symbol, timeframe, count, end_time)
    
    def get_server_timestamp(self) -> float:
        """Get server timestamp (delegated to broker adapter)."""
        return self._broker.get_server_timestamp()

    def get_latest_close(self, symbol: str) -> float:
        """Return latest M1 close price from RAM. No CSV read."""
        return self._cache.get_latest_close(symbol)

    def check_warmup(self, symbol: str) -> bool:
        """Check warmup data sufficiency from RAM. No CSV read."""
        return self._cache.check_warmup(symbol)

    def is_connected(self) -> bool:
        """Check connection status."""
        return self._broker.is_connected()

    def connect(self) -> None:
        """Connect to data source."""
        return self._broker.connect()

    def disconnect(self) -> None:
        """Disconnect from data source."""
        return self._broker.disconnect()

    def start_stream(self, symbol: str, timeframe: str, count: int) -> None:
        """Start streaming for symbol and timeframe."""
        return self._broker.start_stream(symbol, timeframe, count)

    def ensure_connected(self) -> bool:
        """Ensure connection is active, reconnect if needed"""
        return self._broker.ensure_connected()

    def get_balance(self) -> float:
        """Get account balance (delegated to broker adapter)."""
        return self._broker.get_balance()

    async def get_historical_candles(self, symbol: str, timeframe: int, count: int, end_time: float):
        """Get historical candles (delegated to IQ adapter)."""
        # Convert timeframe string to int if needed
        if isinstance(timeframe, str):
            from config_setting.config_loader import get_timeframe_sync_config
            tf_config = get_timeframe_sync_config()
            timeframe_seconds = tf_config["timeframe_minutes"].get(timeframe, 60) * 60
        else:
            timeframe_seconds = timeframe
            
        return await self._broker.get_historical_candles(symbol, timeframe_seconds, count, end_time)
