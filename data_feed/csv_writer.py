"""
CSV Writer Module.
เขียนข้อมูลลง CSV ไฟล์อย่างปลอดภัย พร้อมจัดการ timezone ถูกต้อง
"""

import pandas as pd
import os
import logging
from typing import Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class CSVWriter:
    """จัดการเขียน DataFrame ลง CSV ไฟล์"""
    
    @staticmethod
    def prepare_for_csv(df: pd.DataFrame) -> pd.DataFrame:
        """
        เตรียม DataFrame สำหรับเขียนลง CSV
        - แปลง index กลับเป็น column 'timestamp' 
        - Format timestamp เป็น string ที่ถูกต้อง
        """
        if df.empty:
            return df
        
        df_copy = df.copy()
        
        # Reset index เพื่อทำให้ timestamp เป็น column
        df_copy = df_copy.reset_index()
        
        # ตรวจสอบว่า column ชื่อ 'timestamp' มีอยู่แล้วหรือไม่
        if 'index' in df_copy.columns:
            df_copy.rename(columns={'index': 'timestamp'}, inplace=True)
        
        # Format timestamp เป็น string แบบ ISO format พร้อม UTC
        if 'timestamp' in df_copy.columns:
            # ถ้าเป็น datetime object ให้ format เป็น string
            if pd.api.types.is_datetime64_any_dtype(df_copy['timestamp']):
                df_copy['timestamp'] = df_copy['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S+00:00')
        
        return df_copy
    
    @staticmethod
    def write_safe(filepath: str, df: pd.DataFrame, backup: bool = True) -> bool:
        """
        เขียน DataFrame ลง CSV อย่างปลอดภัย
        - สร้าง backup ก่อนเขียน (ถ้าเปิดใช้งาน)
        - ใช้ atomic write (เขียนไฟล์ชั่วคราวแล้ว rename)
        """
        if df.empty:
            logger.warning(f"Attempted to write empty DataFrame to {filepath}")
            return False
        
        try:
            # สร้าง directory ถ้ายังไม่มี
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # ทำ backup ถ้าไฟล์เดิมมีอยู่
            if backup and os.path.exists(filepath):
                backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.replace(filepath, backup_path)
                logger.debug(f"Created backup: {backup_path}")
            
            # เตรียมข้อมูลสำหรับเขียน
            df_to_write = CSVWriter.prepare_for_csv(df)
            
            # เขียนไฟล์ชั่วคราวก่อน
            temp_filepath = f"{filepath}.tmp"
            df_to_write.to_csv(temp_filepath, index=False, mode='a', header=not os.path.exists(filepath))
            
            # Rename ไฟล์ชั่วคราวเป็นไฟล์จริง (atomic operation)
            os.replace(temp_filepath, filepath)
            
            logger.debug(f"Successfully wrote {len(df)} rows to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write CSV {filepath}: {e}")
            # ลองลบไฟล์ชั่วคราวถ้ามี
            temp_filepath = f"{filepath}.tmp"
            if os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except:
                    pass
            return False
    
    @staticmethod
    def read_safe(filepath: str) -> Optional[pd.DataFrame]:
        """
        อ่าน CSV ไฟล์กลับมาเป็น DataFrame
        - แปลง timestamp column กลับเป็น datetime index
        - Handle กรณีไฟล์ไม่มีหรือเสียหาย
        """
        if not os.path.exists(filepath):
            logger.debug(f"CSV file not found: {filepath}")
            return None
        
        try:
            df = pd.read_csv(filepath)
            
            if df.empty:
                return df
            
            # แปลง timestamp column เป็น datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to read CSV {filepath}: {e}")
            return None
    
    @staticmethod
    def merge_and_deduplicate(existing_df: pd.DataFrame, new_df: pd.DataFrame) -> pd.DataFrame:
        """
        รวมข้อมูลเก่าและใหม่ ลบแถวที่ซ้ำกัน
        """
        if existing_df is None or existing_df.empty:
            return new_df
        
        if new_df is None or new_df.empty:
            return existing_df
        
        # รวมข้อมูล
        combined = pd.concat([existing_df, new_df])
        
        # ลบแถวที่ index ซ้ำกัน (เก็บแถวแรก)
        combined = combined[~combined.index.duplicated(keep='first')]
        
        # เรียงลำดับ
        combined = combined.sort_index()
        
        return combined
