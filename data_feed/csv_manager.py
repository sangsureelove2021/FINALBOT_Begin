"""
CSV Manager Module.
Facade สำหรับจัดการ CSV operations ทั้งหมด
รวม CSVWriter และ CSVQueue เข้าด้วยกัน
"""

import logging
import threading
from typing import Optional
import pandas as pd

from .csv_writer import CSVWriter
from .csv_queue import CSVQueue
from .config import DataFeedConfig

logger = logging.getLogger(__name__)

class CSVManager:
    """
    จัดการ CSV operations แบบ end-to-end
    - ใช้ queue สำหรับเขียนแบบ asynchronous
    - มี method สำหรับอ่านและ merge ข้อมูล
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, max_workers: int = 3):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._queue = CSVQueue(max_workers=max_workers)
        self._initialized = True
        logger.info(f"CSVManager initialized with {max_workers} workers")
    
    def write_async(self, filepath: str, df: pd.DataFrame, backup: bool = True) -> bool:
        """เขียนไฟล์แบบ asynchronous (ไม่ blocking)"""
        return self._queue.enqueue_write(filepath, df, backup)
    
    def write_sync(self, filepath: str, df: pd.DataFrame, backup: bool = True) -> bool:
        """เขียนไฟล์แบบ synchronous (blocking)"""
        return CSVWriter.write_safe(filepath, df, backup)
    
    def read(self, filepath: str) -> Optional[pd.DataFrame]:
        """อ่านไฟล์ CSV"""
        return CSVWriter.read_safe(filepath)
    
    def merge_and_write(self, filepath: str, new_df: pd.DataFrame, 
                       backup: bool = True, async_write: bool = True) -> bool:
        """
        อ่านไฟล์เดิม, merge กับข้อมูลใหม่, แล้วเขียนกลับ
        """
        # อ่านไฟล์เดิม
        existing_df = self.read(filepath)
        
        # Merge
        merged_df = CSVWriter.merge_and_deduplicate(existing_df, new_df)
        
        if merged_df.empty:
            logger.warning(f"Merged DataFrame is empty for {filepath}")
            return False
        
        # เขียนกลับ
        if async_write:
            return self.write_async(filepath, merged_df, backup)
        else:
            return self.write_sync(filepath, merged_df, backup)
    
    def shutdown(self, wait: bool = True) -> None:
        """ปิด CSVManager"""
        logger.info("Shutting down CSVManager...")
        self._queue.shutdown(wait=wait)

# Import threading at module level
import threading
