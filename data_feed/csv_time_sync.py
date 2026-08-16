"""
CSV Time Sync Module.
ตรวจสอบและแก้ไข timestamp ของข้อมูลให้ตรงกับเวลาจริง
"""

import pandas as pd
import logging
from typing import Optional, Tuple
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

class TimeSyncManager:
    """
    จัดการเรื่องเวลาและการซิงค์ timestamp
    ไม่ใช้ Singleton แล้ว เพื่อให้ทดสอบง่าย
    """
    
    def __init__(self, tolerance_seconds: int = 30):
        self.tolerance = timedelta(seconds=tolerance_seconds)
        self.time_offset = 0.0  # offset ระหว่าง local time กับ server time
        logger.info(f"TimeSyncManager initialized with {tolerance_seconds}s tolerance")
    
    def sync_server_time(self, broker_adapter) -> None:
        """
        ซิงค์เวลากับ broker server
        คำนวณ time offset และเก็บไว้ใช้
        """
        try:
            local_time = self.get_current_utc()
            server_timestamp_ms = broker_adapter.get_server_timestamp()
            server_time = datetime.fromtimestamp(server_timestamp_ms / 1000, tz=timezone.utc)
            
            self.time_offset = self.detect_clock_drift(local_time, server_time)
            logger.info(f"Time synced with server. Offset: {self.time_offset:.3f}s")
        except Exception as e:
            logger.warning(f"Failed to sync server time: {e}")
            self.time_offset = 0.0
    
    def get_broker_epoch(self) -> float:
        """
        ดึง epoch time ของ broker (เป็นวินาที)
        """
        return datetime.now(timezone.utc).timestamp() + self.time_offset
    
    def get_current_utc(self) -> datetime:
        """ดึงเวลาปัจจุบันแบบ UTC"""
        return datetime.now(timezone.utc)
    
    def validate_timestamp(self, ts: datetime, expected_time: datetime) -> Tuple[bool, str]:
        """
        ตรวจสอบว่า timestamp ตรงกับเวลาที่คาดหวังหรือไม่
        Returns: (is_valid, message)
        """
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        
        if expected_time.tzinfo is None:
            expected_time = expected_time.replace(tzinfo=timezone.utc)
        
        diff = abs((ts - expected_time).total_seconds())
        
        if diff <= self.tolerance.total_seconds():
            return True, f"Timestamp within tolerance ({diff:.1f}s)"
        else:
            return False, f"Timestamp drift too large ({diff:.1f}s)"
    
    def align_to_timeframe(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        ปรับ index timestamp ให้ตรงกับขอบเขตของ timeframe
        เช่น M1 ต้องตรง :00 วินาที, M5 ต้องตรงนาทีที่หาร 5 ลงตัว
        """
        if df.empty:
            return df
        
        df = df.copy()
        
        # คำนวณระยะเวลาของแต่ละ timeframe เป็นนาที
        tf_minutes = int(timeframe.replace('M', '').replace('H', '').replace('D', ''))
        
        if 'H' in timeframe:
            tf_minutes *= 60
        
        # ปรับ timestamp ให้ตรงขอบเขต
        def align_ts(ts):
            # ปัดลงให้ใกล้ขอบเขต timeframe ที่สุด
            minute = ts.minute
            aligned_minute = (minute // tf_minutes) * tf_minutes
            return ts.replace(minute=aligned_minute, second=0, microsecond=0)
        
        new_index = pd.DatetimeIndex([align_ts(ts) for ts in df.index], tz='UTC')
        df.index = new_index
        
        # ลบแถวที่ซ้ำกันหลังจาก align
        df = df[~df.index.duplicated(keep='first')]
        df = df.sort_index()
        
        return df
    
    def detect_clock_drift(self, local_time: datetime, server_time: datetime) -> float:
        """
        คำนวณความแตกต่างระหว่างเวลาท้องถิ่นและเวลาเซิร์ฟเวอร์
        Returns: drift ในหน่วยวินาที (บวก = local เร็วกว่า, ลบ = local ช้ากว่า)
        """
        if local_time.tzinfo is None:
            local_time = local_time.replace(tzinfo=timezone.utc)
        
        if server_time.tzinfo is None:
            server_time = server_time.replace(tzinfo=timezone.utc)
        
        drift_seconds = (local_time - server_time).total_seconds()
        
        if abs(drift_seconds) > 5:
            logger.warning(f"Clock drift detected: {drift_seconds:.1f} seconds")
        
        return drift_seconds
    
    def create_time_index(self, start_time: datetime, periods: int, 
                         timeframe: str) -> pd.DatetimeIndex:
        """
        สร้าง DatetimeIndex สำหรับข้อมูลใหม่
        """
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        
        # คำนวณ frequency
        tf_value = int(timeframe.replace('M', '').replace('H', '').replace('D', ''))
        
        if 'M' in timeframe:
            freq = f'{tf_value}min'
        elif 'H' in timeframe:
            freq = f'{tf_value}h'
        elif 'D' in timeframe:
            freq = f'{tf_value}D'
        else:
            freq = timeframe
        
        return pd.date_range(start=start_time, periods=periods, freq=freq, tz='UTC')
