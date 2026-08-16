"""
CSV Queue Module.
จัดการ queue สำหรับเขียน CSV แบบ asynchronous ด้วย thread pool
"""

import threading
import queue
import logging
from typing import Optional, Callable
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

from .csv_writer import CSVWriter

logger = logging.getLogger(__name__)

class CSVWriteTask:
    """Task object สำหรับเขียน CSV"""
    
    def __init__(self, filepath: str, df: pd.DataFrame, backup: bool = True):
        self.filepath = filepath
        self.df = df
        self.backup = backup

class CSVQueue:
    """
    Thread-safe queue สำหรับจัดการการเขียน CSV
    ใช้ ThreadPoolExecutor เพื่อเขียนแบบไม่ blocking main thread
    """
    
    def __init__(self, max_workers: int = 3, max_queue_size: int = 100):
        self._queue: queue.Queue[Optional[CSVWriteTask]] = queue.Queue(maxsize=max_queue_size)
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._shutdown = False
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        logger.info(f"CSVQueue started with {max_workers} workers")
    
    def enqueue_write(self, filepath: str, df: pd.DataFrame, backup: bool = True) -> bool:
        """
        เพิ่ม task การเขียนไฟล์ลง queue
        Returns: True ถ้าเพิ่มสำเร็จ, False ถ้า queue เต็มหรือ shutdown
        """
        if self._shutdown:
            logger.warning("CSVQueue is shutting down, cannot enqueue new tasks")
            return False
        
        if df.empty:
            logger.debug(f"Skipping empty DataFrame for {filepath}")
            return False
        
        try:
            task = CSVWriteTask(filepath, df, backup)
            self._queue.put_nowait(task)
            logger.debug(f"Enqueued write task for {filepath} ({len(df)} rows)")
            return True
        except queue.Full:
            logger.warning(f"CSV write queue is full, dropping task for {filepath}")
            return False
    
    def _process_queue(self) -> None:
        """Worker thread ที่ดึง task จาก queue ไปประมวลผล"""
        while not self._shutdown:
            try:
                # ดึง task จาก queue (block ได้สูงสุด 1 วินาที)
                task: Optional[CSVWriteTask] = self._queue.get(timeout=1.0)
                
                if task is None:
                    # Signal shutdown
                    break
                
                # เขียนไฟล์
                success = CSVWriter.write_safe(task.filepath, task.df, task.backup)
                
                if success:
                    logger.debug(f"Completed write task for {task.filepath}")
                else:
                    logger.error(f"Failed to write {task.filepath}")
                
                self._queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing CSV write task: {e}")
    
    def shutdown(self, wait: bool = True) -> None:
        """
        ปิด queue อย่างสวยงาม
        """
        logger.info("Shutting down CSVQueue...")
        self._shutdown = True
        
        # ส่ง signal ให้ worker thread หยุด
        try:
            self._queue.put_nowait(None)
        except:
            pass
        
        if wait:
            self._worker_thread.join(timeout=5.0)
        
        self._executor.shutdown(wait=wait)
        logger.info("CSVQueue shutdown complete")
    
    def get_queue_size(self) -> int:
        """ดึงจำนวน task ที่ค้างอยู่ใน queue"""
        return self._queue.qsize()
