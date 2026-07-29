"""
CSV Writer

Writes candle dataframes to CSV files.
"""

import os
import time
import threading
import traceback
import pandas as pd
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Global Per-File Lock Dictionary & Mutex
_FILE_LOCKS: Dict[str, threading.Lock] = {}
_LOCKS_MUTEX = threading.Lock()

def get_file_lock(file_path: str) -> threading.Lock:
    """
    Get or create a thread lock per absolute file path.
    Ensures per-file thread synchronization across all readers and writers.
    """
    abs_path = os.path.abspath(file_path)
    with _LOCKS_MUTEX:
        if abs_path not in _FILE_LOCKS:
            _FILE_LOCKS[abs_path] = threading.Lock()
        return _FILE_LOCKS[abs_path]

def read_csv_safe(file_path: str, **kwargs) -> pd.DataFrame:
    """
    Read CSV file safely using the per-file thread lock to ensure zero-lock/zero-error reads.
    """
    file_lock = get_file_lock(file_path)
    with file_lock:
        return pd.read_csv(file_path, **kwargs)

class CSVWriter:
    """Writes candle dataframes to CSV files with Thread-Safe synchronization."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize with writer configuration.
        
        Args:
            config: Configuration from datafeed_config.json csv_writer section
        """
        if config is None:
            from config_setting.config_loader import get_csv_writer_config
            config = get_csv_writer_config()
        
        # Load writer configuration
        self.encoding = config.get("encoding", "utf-8")
        self.index_format = config.get("index_format", "timestamp")
        self.date_format = config.get("date_format", "%Y-%m-%d %H:%M:%S")
        self.include_header = config.get("include_header", True)
        self.decimal_places = config.get("decimal_places", 6)
        
        logger.info(f"[CSVWriter] Initialized with encoding: {self.encoding}, decimals: {self.decimal_places}")

    def read(self, file_path: str, **kwargs) -> pd.DataFrame:
        """Read CSV file safely using per-file synchronization lock."""
        kwargs.setdefault("encoding", self.encoding)
        return read_csv_safe(file_path, **kwargs)

    def write(self, df: pd.DataFrame, file_path: str) -> None:
        """Write DataFrame to the specified file path inside a Per-File Lock."""
        if df is None or df.empty:
            logger.warning(f"[CSVWriter] Attempted to write empty dataframe to {file_path}")
            raise ValueError(f"Cannot write empty dataframe to {file_path}")
            
        file_lock = get_file_lock(file_path)
        with file_lock:
            try:
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)

                logger.info(f"[CSVWriter] Writing {len(df)} rows to {file_path}")
                
                # Prepare dataframe for writing
                df_to_write = df.copy()
                
                # Select ALL standard columns including timestamp (8 columns total)
                cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'age', 'quality']
                df_to_write = df_to_write[[c for c in cols if c in df_to_write.columns]]
                
                # Format index according to configuration (keep index as Datetime for processing)
                # Note: timestamp column contains the actual timestamp data
                
                # Round decimal places for numeric OHLCV columns
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df_to_write.columns:
                        df_to_write[col] = df_to_write[col].round(self.decimal_places)
                
                # Write to CSV
                # Read existing file if present, merge and deduplicate
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    try:
                        existing_df = pd.read_csv(file_path, index_col=0, encoding=self.encoding)
                        existing_cols = [c for c in cols if c in existing_df.columns]
                        existing_df = existing_df[existing_cols]
                        
                        combined_df = pd.concat([existing_df, df_to_write])
                        combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
                        combined_df.sort_index(inplace=True)
                        df_to_write = combined_df
                    except Exception as e:
                        logger.error(f"[CSVWriter] Could not merge with existing file {file_path}: {e}")
                        traceback.print_exc()
                        raise

                # Write to temporary file and replace atomically
                tmp_path = f"{file_path}.{threading.get_ident()}.tmp"
                df_to_write.to_csv(
                    path_or_buf=tmp_path,
                    encoding=self.encoding,
                    header=self.include_header,
                    index=False,
                    mode='w',
                    date_format=self.date_format
                )
                # No retry - immediate failure on os.replace per Strict No Fallback policy
                try:
                    os.replace(tmp_path, file_path)
                except Exception as e:
                    logger.error(f"[CSVWriter] os.replace failed for {file_path}: {e}")
                    if os.path.exists(tmp_path):
                        try:
                            os.remove(tmp_path)
                        except Exception as rm_err:
                            logger.warning(f"[CSVWriter] Failed to remove tmp file {tmp_path}: {rm_err}")
                    raise
                
                logger.info(f"[CSVWriter] Successfully wrote {len(df_to_write)} rows to {file_path}")
                
            except Exception as e:
                logger.error(f"[CSVWriter] Failed to write to {file_path}: {e}")
                raise

