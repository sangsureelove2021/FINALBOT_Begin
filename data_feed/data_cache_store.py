"""
Data Cache Store Module.
จัดการ cache ของข้อมูลใน memory แบบ thread-safe
ใช้ dictionary mapping แทน if-else chain เพื่อความสะอาด
"""

import threading
from typing import Dict, Optional, Any
from collections import defaultdict
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataCacheStore:
    """
    Thread-safe in-memory cache สำหรับเก็บข้อมูลล่าสุดของแต่ละ symbol และ timeframe
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        # ใช้ dictionary of dictionaries: {timeframe: {symbol: dataframe}}
        self._stores: Dict[str, Dict[str, pd.DataFrame]] = defaultdict(dict)
        self._last_blocks: Dict[str, Dict[str, int]] = defaultdict(dict)
    
    def get_store(self, timeframe: str) -> Dict[str, pd.DataFrame]:
        """ดึง store ของ timeframe นั้นๆ (สร้างใหม่ถ้ายังไม่มี)"""
        with self._lock:
            return self._stores[timeframe]
    
    def get_last_block(self, timeframe: str) -> Dict[str, int]:
        """ดึง last block number ของ timeframe นั้นๆ"""
        with self._lock:
            return self._last_blocks[timeframe]
    
    def update_store(self, timeframe: str, symbol: str, df: pd.DataFrame) -> None:
        """อัปเดตข้อมูลของ symbol ใน timeframe ที่กำหนด"""
        with self._lock:
            self._stores[timeframe][symbol] = df
            logger.debug(f"[{symbol}] Updated cache for {timeframe} ({len(df)} rows)")
    
    def update_last_block(self, timeframe: str, symbol: str, block_number: int) -> None:
        """อัปเดต block number ล่าสุด"""
        with self._lock:
            self._last_blocks[timeframe][symbol] = block_number
    
    def get_symbol_data(self, timeframe: str, symbol: str) -> Optional[pd.DataFrame]:
        """ดึงข้อมูลของ symbol เดียว"""
        with self._lock:
            return self._stores[timeframe].get(symbol)
    
    def get_last_block_for_symbol(self, timeframe: str, symbol: str) -> Optional[int]:
        """ดึง block number ล่าสุดของ symbol เดียว"""
        with self._lock:
            return self._last_blocks[timeframe].get(symbol)
    
    def remove_symbol(self, timeframe: str, symbol: str) -> bool:
        """ลบข้อมูลของ symbol ออก"""
        with self._lock:
            if symbol in self._stores[timeframe]:
                del self._stores[timeframe][symbol]
                logger.debug(f"[{symbol}] Removed from {timeframe} cache")
                return True
            return False
    
    def clear_all(self) -> None:
        """ล้าง cache ทั้งหมด"""
        with self._lock:
            self._stores.clear()
            self._last_blocks.clear()
            logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """ดึงสถิติของ cache"""
        from typing import Any
        with self._lock:
            stats = {
                'timeframes': list(self._stores.keys()),
                'symbols_per_timeframe': {tf: len(symbols) for tf, symbols in self._stores.items()},
                'total_symbols': sum(len(symbols) for symbols in self._stores.values()),
            }
            return stats
