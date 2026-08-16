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
    """Thread-safe queue for asynchronous CSV writing - Singleton Pattern"""
    
    _instances = {}
    
    def __new__(cls, config: Dict[str, Any] = None):
        """Ensure singleton pattern for CSVQueue"""
        key = f"{hash(str(config))}"
        if key not in cls._instances:
            cls._instances[key] = super().__new__(cls)
        return cls._instances[key]

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with queue configuration."""
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self._initialized = True
        if config is None:
            from config_setting.config_loader import get_csv_queue_config
            config = get_csv_queue_config()
        
        # Load queue configuration
        self.max_workers = config.get("max_workers", 1)
        self.daemon = config.get("daemon", True)
        self.queue_timeout = config.get("queue_timeout", 30)
        self.max_queue_size = config.get("max_queue_size", 1000)
        self.enable_logging = config.get("enable_logging", True)
        self.max_consecutive_errors = config.get("max_consecutive_errors", 5)
        
        self._error_count = 0
        self._consecutive_errors = 0
        self._writer = CSVWriter()
        self._queue = queue.Queue()
        self._worker_thread = None
        self._is_running = False
        self._stop_event = threading.Event()
        
        self.start_worker()
        
        if self.enable_logging:
            logger.info(f"[CSVQueue] Initialized with {self.max_workers} worker(s)")

    def start_worker(self):
        """Start the background worker thread with proper lifecycle management."""
        if self._is_running and self._worker_thread is not None and self._worker_thread.is_alive():
            logger.debug("[CSVQueue] Worker thread is already running.")
            return
        
        self._is_running = True
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._worker, daemon=self.daemon, name="CSVQueue-Worker")
        self._worker_thread.start()
        logger.info("[CSVQueue] Worker thread started")

    def shutdown(self, wait=True, timeout=30):
        """
        Gracefully shutdown the worker thread to prevent resource leak.
        
        Args:
            wait: If True, wait for the thread to finish
            timeout: Maximum seconds to wait for thread termination
        """
        if not self._is_running:
            logger.debug("[CSVQueue] Worker thread is not running, nothing to shutdown.")
            return
        
        logger.info("[CSVQueue] Shutting down worker thread...")
        self._is_running = False
        self._stop_event.set()
        
        # Try to drain the queue before stopping
        if wait:
            try:
                # Wait for queue to be processed
                remaining = self._queue.qsize()
                if remaining > 0:
                    logger.info(f"[CSVQueue] Waiting for {remaining} items in queue to be processed...")
                    self._queue.join()
            except Exception as e:
                logger.warning(f"[CSVQueue] Error while waiting for queue to drain: {e}")
        
        # Wait for thread to terminate
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=timeout)
            if self._worker_thread.is_alive():
                logger.warning(f"[CSVQueue] Worker thread did not terminate within {timeout}s, forcing stop.")
            else:
                logger.info("[CSVQueue] Worker thread terminated gracefully.")
        
        self._worker_thread = None
        logger.info("[CSVQueue] Shutdown complete.")

    def enqueue_write(self, df: pd.DataFrame, file_path: str) -> None:
        """Add a dataframe and target path to the write queue."""
        if df is not None and not df.empty:
            # Check queue size to prevent memory issues
            if self._queue.qsize() >= self.max_queue_size:
                raise RuntimeError(f"FAIL-FAST: CSVQueue size exceeded max limit ({self.max_queue_size}) - write blocked for {file_path}")
            
            logger.info(f"[CSVQueue] Enqueuing write for {file_path} - Queue size: {self._queue.qsize()}")
            self._queue.put((df.copy(), file_path))

    def _worker(self):
        """Worker thread loop to process CSV writes with proper lifecycle management."""
        while self._is_running or not self._queue.empty():
            file_path = "UNKNOWN"
            try:
                # Check stop event before blocking on queue.get
                if self._stop_event.is_set() and self._queue.empty():
                    logger.info("[CSVQueue] Worker thread received stop signal and queue is empty, exiting.")
                    break
                    
                df, file_path = self._queue.get(timeout=self.queue_timeout)
                logger.info(f"[CSVQueue] Processing write for {file_path}")
                
                # Use shared CSVWriter instance
                self._writer.write(df, file_path)
                
                self._queue.task_done()
                self._consecutive_errors = 0
                logger.info(f"[CSVQueue] Successfully processed write for {file_path}")
                
                if self.enable_logging and self._queue.qsize() % 100 == 0:
                    logger.info(f"[CSVQueue] Queue size: {self._queue.qsize()}")
                    
            except queue.Empty:
                # This is normal timeout for daemon thread
                if self._stop_event.is_set():
                    logger.info("[CSVQueue] Worker thread received stop signal during timeout, exiting.")
                    break
                continue
            except Exception as e:
                self._error_count += 1
                self._consecutive_errors += 1
                traceback.print_exc()
                logger.error(f"[CSVQueue] Asynchronous write failed for {file_path}: {e}")
                logger.error(f"[CSVQueue] Error details: {type(e).__name__}: {e}")
                logger.error(f"[CSVQueue] Total errors: {self._error_count}, consecutive: {self._consecutive_errors}")
                self._queue.task_done()
                
                # Circuit breaker: หยุด worker เมื่อ error ติดต่อกันเกิน threshold
                if self._consecutive_errors >= self.max_consecutive_errors:
                    logger.critical(
                        f"[CSVQueue] CIRCUIT BREAKER: {self._consecutive_errors} consecutive errors exceeded "
                        f"threshold ({self.max_consecutive_errors}). Worker stopping."
                    )
                    self._is_running = False
                    break
                continue
        
        logger.info("[CSVQueue] Worker thread loop exited.")
