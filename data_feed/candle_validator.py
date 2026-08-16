"""
data_feed/candle_validator.py

Candle Validator - Market Data Validation Core
หน้าที่: ตรวจสอบความถูกต้องสมบูรณ์ของโครงสร้างราคาแท่งเทียน (OHLCV)
ตามกฎ Strict Fail-Fast (Rule 7) และ Rule 2 (Strict Type Hinting & Validation)
"""

import logging
import pandas as pd
from typing import Dict, Any, Optional
from data_feed.exceptions import ValidationError

logger = logging.getLogger(__name__)


class CandleValidator:
    """
    คลาสสำหรับตรวจสอบโครงสร้างและความถูกต้องของแท่งเทียน OHLCV
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize CandleValidator.

        Args:
            config (Optional[Dict[str, Any]]): Validation configuration settings.
        """
        self.config = config or {}
        logger.info("[CandleValidator] Initialized with validation configuration")

    def validate(self, df: pd.DataFrame, symbol: Optional[str] = None) -> bool:
        """
        ตรวจสอบโครงสร้างแท่งเทียนใน DataFrame (OHLCV)
        
        เงื่อนไขความถูกต้อง:
        1. open, high, low, close > 0
        2. high >= low
        3. high >= open
        4. high >= close
        5. low <= open
        6. low <= close
        7. volume >= 0 (หากมีคอลัมน์ volume)

        Args:
            df (pd.DataFrame): DataFrame ที่ต้องการตรวจสอบ
            symbol (Optional[str]): ชื่อสินทรัพย์ (สำหรับแสดงใน log)

        Returns:
            bool: True หากข้อมูลถูกต้องทั้งหมด

        Raises:
            TypeError: หาก df ไม่ใช่ pd.DataFrame (Rule 2)
            ValueError: หากพบแท่งเทียนผิดรูปแม้แต่แท่งเดียว (Rule 7 Fail-Fast)
        """
        # Rule 2: Strict Type Hinting & Validation
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Invalid input type: Expected pd.DataFrame, got {type(df).__name__}")

        if df.empty:
            logger.error("[CandleValidator] FAIL-FAST: Empty DataFrame received for validation")
            raise ValidationError("FAIL-FAST: Empty DataFrame — cannot validate empty candle data")

        # Map column names (support case-insensitive matching for open, high, low, close, volume)
        col_map = {col.lower(): col for col in df.columns}
        required_cols = ['open', 'high', 'low', 'close']
        missing_cols = [c for c in required_cols if c not in col_map]
        
        if missing_cols:
            symbol_str = f" for symbol {symbol}" if symbol else ""
            logger.error(f"[CandleValidator] Missing required columns {missing_cols}{symbol_str}. Available: {list(df.columns)}")
            raise ValueError("FAIL-FAST: Invalid OHLC candle structure detected")

        open_col = col_map['open']
        high_col = col_map['high']
        low_col = col_map['low']
        close_col = col_map['close']

        open_s = df[open_col]
        high_s = df[high_col]
        low_s = df[low_col]
        close_s = df[close_col]

        # Check for NaN values in OHLC columns
        for col_name, series in [('open', open_s), ('high', high_s), ('low', low_s), ('close', close_s)]:
            nan_count = series.isna().sum()
            if nan_count > 0:
                symbol_str = f" for symbol {symbol}" if symbol else ""
                logger.error(f"[CandleValidator] FAIL-FAST: {nan_count} NaN values found in '{col_name}'{symbol_str}")
                raise ValidationError(f"FAIL-FAST: NaN values detected in '{col_name}' column")

        # Vectorized check for valid candle structure
        valid_mask = (
            (open_s > 0) &
            (high_s > 0) &
            (low_s > 0) &
            (close_s > 0) &
            (high_s >= low_s) &
            (high_s >= open_s) &
            (high_s >= close_s) &
            (low_s <= open_s) &
            (low_s <= close_s)
        )

        if 'volume' in col_map:
            vol_s = df[col_map['volume']]
            valid_mask &= (vol_s >= 0)

        # Rule 7: Strict Fail-Fast Policy
        if not valid_mask.all():
            invalid_rows = df[~valid_mask]
            symbol_str = f" for symbol {symbol}" if symbol else ""
            logger.error(
                f"[CandleValidator] FAIL-FAST: Detected {len(invalid_rows)} invalid candle(s){symbol_str}.\n"
                f"Sample invalid rows:\n{invalid_rows.head()}"
            )
            raise ValueError("FAIL-FAST: Invalid OHLC candle structure detected")

        return True

    def validate_single_candle(
        self,
        open_p: float,
        high_p: float,
        low_p: float,
        close_p: float,
        volume: Optional[float] = 0.0
    ) -> bool:
        """
        ตรวจสอบโครงสร้างแท่งเทียนเดี่ยว (Single Candle Check)

        Args:
            open_p (float): ราคา Open
            high_p (float): ราคา High
            low_p (float): ราคา Low
            close_p (float): ราคา Close
            volume (Optional[float]): วอลลุ่ม (default: 0.0)

        Returns:
            bool: True หากแท่งเทียนถูกต้อง

        Raises:
            ValueError: หากพบโครงสร้างแท่งเทียนผิดรูป (Rule 7 Fail-Fast)
        """
        try:
            o = float(open_p)
            h = float(high_p)
            l = float(low_p)
            c = float(close_p)
            v = float(volume) if volume is not None else 0.0
        except (ValueError, TypeError) as e:
            logger.error(f"[CandleValidator] Non-numeric input in single candle: O={open_p}, H={high_p}, L={low_p}, C={close_p}, V={volume}")
            raise ValueError("FAIL-FAST: Invalid OHLC candle structure detected") from e

        is_valid = (
            o > 0 and
            h > 0 and
            l > 0 and
            c > 0 and
            h >= l and
            h >= o and
            h >= c and
            l <= o and
            l <= c and
            v >= 0
        )

        if not is_valid:
            logger.error(
                f"[CandleValidator] FAIL-FAST: Invalid single candle structure detected -> "
                f"Open={o}, High={h}, Low={l}, Close={c}, Volume={v}"
            )
            raise ValueError("FAIL-FAST: Invalid OHLC candle structure detected")

        return True
