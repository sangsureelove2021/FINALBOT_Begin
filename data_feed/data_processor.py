"""
Data Processor Module.
ประมวลผลข้อมูลหลังจากรับมาจาก Broker: validate, merge, deduplicate
"""

import pandas as pd
import logging
from typing import Dict, Optional, Tuple

from .data_validator import DataValidator
from .data_cache_store import DataCacheStore
from .exceptions import DataFeedError

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    ประมวลผลข้อมูลจาก Broker ก่อนส่งต่อหรือบันทึก
    """
    
    def __init__(self, cache: DataCacheStore):
        self._cache = cache
        self._validator = DataValidator()
        logger.info("DataProcessor initialized")
    
    def process_new_data(self, df: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
        """
        ประมวลผลข้อมูลใหม่:
        1. ตรวจสอบโครงสร้าง
        2. แปลง index เป็น UTC datetime
        3. เรียงลำดับและลบข้อมูลซ้ำ
        4. ตรวจสอบ range ค่า OHLCV
        
        Returns: DataFrame ที่ผ่านการประมวลผลแล้ว
        """
        if df.empty:
            return df
        
        label = f"[{symbol}/{timeframe}]"
        
        # Step 1: Validate structure
        self._validator.validate_structure(df, symbol)
        
        # Step 2: Ensure UTC datetime index (เรียกครั้งเดียวพอ)
        df = self._validator.ensure_utc_datetime_index(df)
        
        # Step 3: Sort and deduplicate
        df = self._validator.sort_and_deduplicate(df, symbol)
        
        # Step 4: Validate range
        self._validator.validate_range(df, symbol, timeframe)
        
        logger.debug(f"{label} Processed {len(df)} rows")
        return df
    
    def merge_with_cache(self, fresh_df: pd.DataFrame, symbol: str, 
                        timeframe: str) -> pd.DataFrame:
        """
        รวมข้อมูลใหม่กับข้อมูลเก่าใน cache
        - ตรวจสอบความต่อเนื่อง (continuity)
        - ลบข้อมูลที่ซ้ำซ้อน (overlap)
        
        Returns: DataFrame ที่รวมแล้ว
        """
        if fresh_df.empty:
            return fresh_df
        
        label = f"[{symbol}/{timeframe}]"
        
        # ดึงข้อมูลเก่าจาก cache
        stored_df = self._cache.get_symbol_data(timeframe, symbol)
        
        if stored_df is None or stored_df.empty:
            # ไม่มีข้อมูลเก่า เก็บข้อมูลใหม่ลง cache เลย
            logger.info(f"{label} No existing data, using fresh data ({len(fresh_df)} rows)")
            self._cache.update_store(timeframe, symbol, fresh_df)
            return fresh_df
        
        # ตรวจสอบความต่อเนื่อง
        try:
            self._validator.validate_continuity(stored_df, fresh_df, symbol, timeframe)
        except Exception as e:
            logger.warning(f"{label} Continuity check warning: {e}")
            # ไม่ raise ต่อ อนุญาตให้ผ่านแต่ log ไว้
        
        # ตรวจสอบและลบ overlap
        overlap_count = self._validator.validate_overlap(stored_df, fresh_df, symbol, timeframe)
        if overlap_count > 0:
            logger.debug(f"{label} Removed {overlap_count} overlapping rows")
        
        # รวมข้อมูล
        merged_df = pd.concat([stored_df, fresh_df])
        merged_df = self._validator.sort_and_deduplicate(merged_df, symbol)
        
        # อัปเดต cache
        self._cache.update_store(timeframe, symbol, merged_df)
        
        logger.info(f"{label} Merged: {len(stored_df)} + {len(fresh_df)} - {overlap_count} = {len(merged_df)} rows")
        return merged_df
    
    def get_latest_block(self, df: pd.DataFrame, timeframe: str) -> int:
        """
        คำนวณ block number จาก timestamp ล่าสุด
        Block number = จำนวนนาทีตั้งแต่ epoch หารด้วย duration ของ timeframe
        """
        if df.empty:
            return 0
        
        last_ts = df.index[-1]
        
        # คำนวณ duration ของ timeframe เป็นนาที
        duration_minutes = int(timeframe.replace('M', '').replace('H', '').replace('D', ''))
        if 'H' in timeframe:
            duration_minutes *= 60
        elif 'D' in timeframe:
            duration_minutes *= 24 * 60
        
        # คำนวณ block number
        epoch = pd.Timestamp('1970-01-01', tz='UTC')
        total_minutes = int((last_ts - epoch).total_seconds() / 60)
        block_number = total_minutes // duration_minutes
        
        return block_number
    
    def update_cache_and_block(self, df: pd.DataFrame, symbol: str, timeframe: str) -> None:
        """อัปเดตทั้งข้อมูลและ block number ใน cache"""
        self._cache.update_store(timeframe, symbol, df)
        
        block_number = self.get_latest_block(df, timeframe)
        self._cache.update_last_block(timeframe, symbol, block_number)
        
        logger.debug(f"[{symbol}/{timeframe}] Updated cache with block {block_number}")
