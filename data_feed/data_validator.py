"""
Data Validator Module.
ทำหน้าที่ตรวจสอบความถูกต้องของข้อมูล (Validation) เท่านั้น ไม่แก้ไขข้อมูล
"""

import pandas as pd
import logging
from typing import Optional, Tuple
from .exceptions import DataValidationError, DataGapError, DataOverlapError

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ['timestamp', 'open', 'high', 'low', 'close', 'volume']

class DataValidator:
    """ตรวจสอบความถูกต้องของ DataFrame ก่อนใช้งาน"""

    @staticmethod
    def validate_structure(df: pd.DataFrame, symbol: str) -> None:
        """ตรวจสอบว่ามีคอลัมน์ครบถ้วนหรือไม่"""
        if df.empty:
            return  # อนุญาตให้ empty ได้ แต่จะเตือนตอนเรียกใช้
        
        # ตรวจสอบ columns ในข้อมูล (ไม่รวม index เพราะ timestamp เป็น index)
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise DataValidationError(f"[{symbol}] Missing columns: {missing_cols}")

    @staticmethod
    def ensure_utc_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
        """
        รับประกันว่า index เป็น datetime และ timezone เป็น UTC
        ถ้า index เป็น string หรือ int จะแปลงให้เป็น datetime
        """
        if df.empty:
            return df

        # ถ้า index ยังไม่ใช่ datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            try:
                # พยายามแปลง index เป็น datetime
                df.index = pd.to_datetime(df.index, utc=True)
            except Exception as e:
                raise DataValidationError(f"Cannot convert index to datetime: {e}")
        
        # ถ้ามี timezone แต่ไม่ใช่ UTC ให้ convert
        elif df.index.tz is not None and str(df.index.tz) != 'UTC':
            df.index = df.index.tz_convert('UTC')
        
        # ถ้าไม่มี timezone ให้ assume เป็น UTC แล้ว add tz info
        elif df.index.tz is None:
            df.index = df.index.tz_localize('UTC')

        return df

    @staticmethod
    def validate_range(df: pd.DataFrame, symbol: str, timeframe: str) -> None:
        """ตรวจสอบว่าค่า OHLCV อยู่ในช่วงที่สมเหตุสมผล"""
        if df.empty:
            return

        # ตรวจสอบค่าติดลบใน open, high, low, close, volume
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if (df[col] < 0).any():
                logger.warning(f"[{symbol}] Negative values detected in '{col}'")

        # ตรวจสอบว่า high >= low
        if (df['high'] < df['low']).any():
            invalid_count = (df['high'] < df['low']).sum()
            raise DataValidationError(f"[{symbol}] High < Low found in {invalid_count} rows")

        # ตรวจสอบว่า high >= open และ high >= close
        if (df['high'] < df['open']).any() or (df['high'] < df['close']).any():
            raise DataValidationError(f"[{symbol}] High is lower than Open or Close")

        # ตรวจสอบว่า low <= open และ low <= close
        if (df['low'] > df['open']).any() or (df['low'] > df['close']).any():
            raise DataValidationError(f"[{symbol}] Low is higher than Open or Close")

    @staticmethod
    def validate_continuity(stored_df: pd.DataFrame, fresh_df: pd.DataFrame, 
                           symbol: str, timeframe: str) -> Tuple[bool, Optional[str]]:
        """
        ตรวจสอบความต่อเนื่องของเวลา ระหว่างข้อมูลเก่าและใหม่
        Returns: (is_continuous, gap_message)
        """
        if stored_df.empty or fresh_df.empty:
            return True, None

        # เรียงลำดับก่อน (สำคัญมาก แก้ไขจากของเดิมที่ไม่ได้ sort)
        stored_df = stored_df.sort_index()
        fresh_df = fresh_df.sort_index()

        last_stored_time = stored_df.index[-1]
        first_fresh_time = fresh_df.index[0]

        # คำนวณระยะเวลาที่คาดหวังตาม timeframe
        expected_delta = pd.Timedelta(minutes=int(timeframe.replace('M', '')))
        
        # อนุญาตให้มีความคลาดเคลื่อนได้เล็กน้อย (30 วินาที)
        tolerance = pd.Timedelta(seconds=30)
        max_gap = expected_delta + tolerance

        time_diff = first_fresh_time - last_stored_time

        if time_diff > max_gap:
            gap_msg = f"Gap detected: Last stored={last_stored_time}, First fresh={first_fresh_time}"
            logger.error(f"[{symbol}] {gap_msg}")
            raise DataGapError(symbol, timeframe, str(last_stored_time), str(first_fresh_time), gap_msg)
        
        if time_diff < pd.Timedelta(seconds=0):
            # ข้อมูลใหม่มีเวลาเก่ากว่าข้อมูลเก่า (อาจเกิดจาก clock skew)
            logger.warning(f"[{symbol}] Fresh data timestamp ({first_fresh_time}) is older than stored ({last_stored_time})")

        return True, None

    @staticmethod
    def validate_overlap(stored_df: pd.DataFrame, fresh_df: pd.DataFrame,
                        symbol: str, timeframe: str) -> int:
        """
        ตรวจสอบและลบข้อมูลที่ซ้ำซ้อน (overlap)
        Returns: จำนวนแถวที่ถูกลบออก
        """
        if stored_df.empty or fresh_df.empty:
            return 0

        stored_df = stored_df.sort_index()
        fresh_df = fresh_df.sort_index()

        last_stored_time = stored_df.index[-1]
        
        # นับจำนวนแถวใน fresh ที่มีเวลา <= เวลาสุดท้ายของ stored
        overlapping_rows = fresh_df[fresh_df.index <= last_stored_time]
        overlap_count = len(overlapping_rows)

        if overlap_count > 0:
            logger.debug(f"[{symbol}] Found {overlap_count} overlapping candles, removing...")
            # ตัดเฉพาะส่วนที่ไม่ overlap
            fresh_df = fresh_df[fresh_df.index > last_stored_time]

        return overlap_count

    @staticmethod
    def sort_and_deduplicate(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """เรียงลำดับและลบแถวที่ซ้ำกันโดยอ้างอิง index (timestamp)"""
        if df.empty:
            return df

        # ลบแถวที่ index ซ้ำกัน เก็บแถวแรกไว้
        before_count = len(df)
        df = df[~df.index.duplicated(keep='first')]
        after_count = len(df)
        
        if before_count != after_count:
            logger.debug(f"[{symbol}] Removed {before_count - after_count} duplicate rows")

        # เรียงลำดับ
        df = df.sort_index()
        
        return df
