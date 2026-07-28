"""
CSV Queue

Provides a thread-safe background worker queue to write CSVs to disk without blocking the main execution thread.
"""

import queue
import threading
import pandas as pd
import logging
import traceback
from typing import Dict, Any
from data_feed.csv_writer import CSVWriter

logger = logging.getLogger(__name__)

class CSVQueue:
    """Thread-safe queue for asynchronous CSV writing."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize with queue configuration.
        
        Args:
            config: Configuration from datafeed_config.json csv_queue section
        """
        if config is None:
            from config_setting.config_loader import get_csv_queue_config
            config = get_csv_queue_config()
        
        # Load queue configuration
        self.max_workers = config.get("max_workers", 1)
        self.daemon = config.get("daemon", True)
        self.queue_timeout = config.get("queue_timeout", 30)
        self.max_queue_size = config.get("max_queue_size", 1000)
        self.enable_logging = config.get("enable_logging", True)
        
        self._error_count = 0
        self._writer = CSVWriter()
        self._queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._worker, daemon=self.daemon)
        self._worker_thread.start()
        
        if self.enable_logging:
            logger.info(f"[CSVQueue] Initialized with {self.max_workers} worker(s)")

    def enqueue_write(self, df: pd.DataFrame, file_path: str) -> None:
        """Add a dataframe and target path to the write queue."""
        if df is not None and not df.empty:
            # Check queue size to prevent memory issues
            if self._queue.qsize() >= self.max_queue_size:
                raise RuntimeError(f"FAIL-FAST: CSVQueue size exceeded max limit ({self.max_queue_size}) - write blocked for {file_path}")
            
            logger.info(f"[CSVQueue] Enqueuing write for {file_path} - Queue size: {self._queue.qsize()}")
            self._queue.put((df.copy(), file_path))

    def _worker(self):
        """Worker thread loop to process CSV writes."""
        while True:
            file_path = "UNKNOWN"
            try:
                df, file_path = self._queue.get(timeout=self.queue_timeout)
                logger.info(f"[CSVQueue] Processing write for {file_path}")
                
                # Use shared CSVWriter instance
                self._writer.write(df, file_path)
                
                self._queue.task_done()
                logger.info(f"[CSVQueue] Successfully processed write for {file_path}")
                
                if self.enable_logging and self._queue.qsize() % 100 == 0:
                    logger.info(f"[CSVQueue] Queue size: {self._queue.qsize()}")
                    
            except queue.Empty:
                # This is normal timeout for daemon thread
                continue
            except Exception as e:
                self._error_count += 1
                traceback.print_exc()
                if self.enable_logging:
                    logger.error(f"[CSVQueue] Asynchronous write failed for {file_path}: {e}")
                    logger.error(f"[CSVQueue] Error details: {type(e).__name__}: {e}")
                    logger.error(f"[CSVQueue] Total errors: {self._error_count}")
                self._queue.task_done()
                raise RuntimeError(f"FAIL-FAST: CSVQueue worker write error: {e}")
