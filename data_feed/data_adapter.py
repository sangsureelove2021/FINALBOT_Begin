"""
Data Adapter Module.
เชื่อมต่อและดึงข้อมูลจาก Broker (IQ Option, Quotex, Pocket Option)
ใช้ config แทน hardcoded values
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta

from .config import DataFeedConfig
from .data_validator import DataValidator
from .data_processor import DataProcessor
from .data_cache_store import DataCacheStore
from .csv_manager import CSVManager
from .exceptions import ConnectionLostError, DataFeedError

logger = logging.getLogger(__name__)

class DataAdapter:
    """
    Adapter สำหรับดึงข้อมูลจาก Broker และประมวลผล
    """
    
    def __init__(self, broker_adapter: Any, csv_manager: Optional[CSVManager] = None):
        """
        Args:
            broker_adapter: Adapter สำหรับเชื่อมต่อกับ Broker (เช่น IQOptionAdapter)
            csv_manager: ตัวจัดการ CSV (ถ้ามี)
        """
        self._broker = broker_adapter
        self._csv_manager = csv_manager
        self._validator = DataValidator()
        self._cache = DataCacheStore()
        self._processor = DataProcessor(self._cache)
        
        logger.info("DataAdapter initialized")
    
    def init_symbol(self, symbol: str, timeframes: List[str] = None) -> bool:
        """
        เริ่มต้นการติดตาม symbol ใหม่
        ดึงข้อมูลย้อนหลังสำหรับทุก timeframe ที่กำหนด
        
        Args:
            symbol: ชื่อ symbol (เช่น "EURUSD")
            timeframes: รายการ timeframe ที่ต้องการ (default: ทุก timeframe ใน config)
        
        Returns:
            True ถ้าสำเร็จ, False ถ้าล้มเหลว
        """
        if timeframes is None:
            timeframes = DataFeedConfig.TIMEFRAMES
        
        logger.info(f"Initializing symbol: {symbol} for timeframes: {timeframes}")
        
        try:
            # ดึงเวลาปัจจุบันจาก broker (เป็น epoch milliseconds)
            broker_epoch = self._get_broker_timestamp()
            
            for tf in timeframes:
                limit = DataFeedConfig.get_candle_limit(tf)
                
                # ดึงข้อมูลจาก broker
                df = self._fetch_candles(symbol, tf, limit, broker_epoch)
                
                if df is None or df.empty:
                    logger.warning(f"[{symbol}/{tf}] No data received from broker")
                    continue
                
                # ประมวลผลข้อมูล
                df = self._processor.process_new_data(df, symbol, tf)
                
                # อัปเดต cache
                self._processor.update_cache_and_block(df, symbol, tf)
                
                # เขียนลง CSV (ถ้ามี csv_manager)
                if self._csv_manager:
                    filepath = self._get_csv_path(symbol, tf)
                    self._csv_manager.write_async(filepath, df)
                
                logger.info(f"[{symbol}/{tf}] Initialized with {len(df)} candles")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize {symbol}: {e}")
            return False
    
    def update(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        อัปเดตข้อมูลล่าสุดสำหรับ symbol และ timeframe ที่กำหนด
        
        Returns:
            DataFrame ที่อัปเดตแล้ว หรือ None ถ้าล้มเหลว
        """
        label = f"[{symbol}/{timeframe}]"
        
        try:
            # ดึง block number ล่าสุด
            last_block = self._cache.get_last_block_for_symbol(timeframe, symbol)
            
            # ดึงข้อมูลเก่าจาก cache
            stored_df = self._cache.get_symbol_data(timeframe, symbol)
            
            # คำนวณเวลาสิ้นสุดสำหรับการดึงข้อมูลใหม่
            broker_epoch = self._get_broker_timestamp()
            
            # ดึงข้อมูลใหม่
            limit = DataFeedConfig.get_candle_limit(timeframe)
            fresh_df = self._fetch_candles(symbol, timeframe, limit, broker_epoch)
            
            if fresh_df is None or fresh_df.empty:
                logger.warning(f"{label} No new data from broker")
                return stored_df
            
            # ประมวลผลข้อมูลใหม่
            fresh_df = self._processor.process_new_data(fresh_df, symbol, timeframe)
            
            # รวมกับข้อมูลเก่า
            merged_df = self._processor.merge_with_cache(fresh_df, symbol, timeframe)
            
            # อัปเดต block number
            self._processor.update_cache_and_block(merged_df, symbol, timeframe)
            
            # เขียนลง CSV
            if self._csv_manager:
                filepath = self._get_csv_path(symbol, timeframe)
                self._csv_manager.write_async(filepath, merged_df)
            
            logger.debug(f"{label} Updated: {len(merged_df)} total rows")
            return merged_df
            
        except Exception as e:
            logger.error(f"{label} Update failed: {e}")
            return None
    
    def _fetch_candles(self, symbol: str, timeframe: str, 
                      limit: int, end_time: int) -> Optional[pd.DataFrame]:
        """
        ดึงข้อมูล candles จาก broker
        
        Args:
            symbol: ชื่อ symbol
            timeframe: timeframe (M1, M5, etc.)
            limit: จำนวนแท่งที่ต้องการ
            end_time: เวลาสิ้นสุด (epoch milliseconds)
        
        Returns:
            DataFrame ของ candles หรือ None ถ้าล้มเหลว
        """
        try:
            # เรียก broker adapter เพื่อดึงข้อมูล
            # สมมติว่า broker adapter มี method get_candles(symbol, timeframe, limit, end_time)
            candles = self._broker.get_candles(symbol, timeframe, limit, end_time=end_time)
            
            if not candles:
                return None
            
            # แปลงเป็น DataFrame
            df = pd.DataFrame(candles)
            
            # ตรวจสอบว่ามีคอลัมน์ครบ
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                logger.warning(f"Missing columns in candle data: {df.columns}")
                return None
            
            # แปลง timestamp เป็น datetime index
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch candles for {symbol}/{timeframe}: {e}")
            return None
    
    def _get_broker_timestamp(self) -> int:
        """ดึงเวลาปัจจุบันจาก broker (epoch milliseconds)"""
        try:
            return self._broker.get_server_timestamp()
        except Exception:
            # Fallback ใช้เวลาท้องถิ่น
            return int(datetime.now(timezone.utc).timestamp() * 1000)
    
    def _get_csv_path(self, symbol: str, timeframe: str) -> str:
        """สร้าง path สำหรับไฟล์ CSV"""
        return f"./data/{symbol}_{timeframe}.csv"
    
    def get_cached_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """ดึงข้อมูลจาก cache"""
        return self._cache.get_symbol_data(timeframe, symbol)
    
    def shutdown(self) -> None:
        """ปิด adapter และล้างทรัพยากร"""
        logger.info("Shutting down DataAdapter...")
        
        if self._csv_manager:
            self._csv_manager.shutdown(wait=True)
        
        self._cache.clear_all()
        logger.info("DataAdapter shutdown complete")
