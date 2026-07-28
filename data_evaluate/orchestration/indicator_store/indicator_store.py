"""
indicator_store.py
------------------
Single Source of Truth (SSOT) สำหรับ FINALBOT
- คำนวณ Raw Indicators (Layer 1) ครั้งเดียว (รวม ADX, Volume Ratio, Slope)
- ให้ Engine (Layer 2) และ Classifier (Layer 3) ใช้งาน
- รองรับการทำงานแบบ Parallel
"""

import pandas as pd
import numpy as np
import threading
import copy
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import logging

try:
    from .core_indicators import CoreIndicators
    from .structural_metrics import StructuralMetrics
except ImportError:
    from core_indicators import CoreIndicators
    from structural_metrics import StructuralMetrics

# ---------- Logging Setup ----------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------- Configuration ----------
class Config:
    ROUND_DECIMALS = 6
    ADX_PERIOD = 14
    VOLUME_MA_PERIOD = 20
    SLOPE_PERIOD = 10  # ใช้ 10 แท่งล่าสุดสำหรับ Linear Regression

# ---------- Core Class ----------
class IndicatorStore:
    """
    จัดเก็บ Indicator เฉพาะ Layer 1 สำหรับทุกคู่เงิน
    - Layer 1: Raw Indicators (คำนวณจาก OHLCV โดยตรง)
    """

    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    # ========================
    # LAYER 1: RAW INDICATORS (คำนวณจาก OHLCV)
    # ========================
    @staticmethod
    def calculate_raw_indicators(df_m1: pd.DataFrame, df_m5: pd.DataFrame, df_m15: Optional[pd.DataFrame] = None, forming_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        คำนวณ Indicator ดิบ (Layer 1) จาก DataFrame M1, M5 และ M15
        - ใช้ Pandas Vectorization (เร็วมาก)
        - ส่งคืน dict ที่มีเฉพาะ 'm5', 'm1', 'ohlcv'
        """
        # ------------------------------------------------------------
        # 0. Warm-up Candle Lookback Check (Fail-Fast: 100/250/50)
        # ------------------------------------------------------------
        if df_m1 is None or df_m1.empty or len(df_m1) < 100:
            raise ValueError("FAIL-FAST: Insufficient M1 warm-up candles (minimum 100 required)")
        if df_m5 is None or df_m5.empty or len(df_m5) < 250:
            raise ValueError("FAIL-FAST: Insufficient M5 warm-up candles (minimum 250 required)")
        if df_m15 is None or df_m15.empty or len(df_m15) < 50:
            raise ValueError("FAIL-FAST: Insufficient M15 warm-up candles (minimum 50 required)")

        # ------------------------------------------------------------
        # 1. M5 Indicators
        # ------------------------------------------------------------
        m5 = {}
        close_m5 = df_m5['close']
        high_m5 = df_m5['high']
        low_m5 = df_m5['low']
        open_m5 = df_m5['open']
        volume_m5 = df_m5['volume']

        # EMA
        m5.update(CoreIndicators.calculate_ema(close_m5, [5, 10, 20, 50, 100, 200], Config.ROUND_DECIMALS))
        
        # M5 Bias
        m5['bias'] = 'BULLISH' if close_m5.iloc[-1] > m5['ema20'] else 'BEARISH'

        # Bollinger Bands (20, 2)
        m5.update(CoreIndicators.calculate_bb(close_m5, 20, Config.ROUND_DECIMALS, require_100=True))

        # RSI (7, 14)
        m5['rsi7'] = CoreIndicators.calc_rsi(close_m5, 7)
        m5['rsi14'] = CoreIndicators.calc_rsi(close_m5, 14)

        # MACD (12, 26, 9)
        m5.update(CoreIndicators.calculate_macd(close_m5, Config.ROUND_DECIMALS, include_hist=True))

        # Stochastic (14, 3, 3)
        m5.update(CoreIndicators.calculate_stochastic(close_m5, high_m5, low_m5))

        # ATR (14)
        m5.update(StructuralMetrics.calculate_atr(high_m5, low_m5, close_m5, Config.ROUND_DECIMALS, extended=True))

        # ================================================================
        # ADX, DI+, DI- (Wilder's Smoothing)
        # ================================================================
        m5.update(StructuralMetrics.calc_adx(high_m5, low_m5, close_m5, Config.ADX_PERIOD))

        # ================================================================
        # ROC (Rate of Change)
        # ================================================================
        if len(close_m5) < 10:
            raise ValueError("Not enough data to calculate ROC")
        m5['roc'] = round(((close_m5.iloc[-1] / (close_m5.iloc[-10] + 1e-9)) - 1) * 100, 4)

        # ================================================================
        # VOLUME RATIO & MA20
        # ================================================================
        m5.update(StructuralMetrics.calculate_volume_metrics(volume_m5, Config.VOLUME_MA_PERIOD, extended=True))

        # ================================================================
        # LINEAR REGRESSION SLOPE
        # ================================================================
        m5['slope_10'] = round(StructuralMetrics.calc_slope(close_m5, 10), Config.ROUND_DECIMALS)
        m5['slope_20'] = round(StructuralMetrics.calc_slope(close_m5, 20), Config.ROUND_DECIMALS)
        m5['slope_50'] = round(StructuralMetrics.calc_slope(close_m5, 50), Config.ROUND_DECIMALS)

        # Fix M5 Pivot Algorithm - Use completed candle only (per SPEC)
        if len(df_m5) < 1:
            raise ValueError("FAIL-FAST: Insufficient M5 candles for Pivot Point calculation (minimum 1 required)")
        
        # Use the last completed candle (iloc[-1] is forming, iloc[-2] is completed)
        # SPEC: "ส่งเฉพาะแท่งที่ปิดสมบูรณ์ 100%"
        completed_high = high_m5.iloc[-1] if len(df_m5) == 1 else high_m5.iloc[-2]
        completed_low = low_m5.iloc[-1] if len(df_m5) == 1 else low_m5.iloc[-2]
        completed_close = close_m5.iloc[-1] if len(df_m5) == 1 else close_m5.iloc[-2]
        
        pivot = (completed_high + completed_low + completed_close) / 3
        m5['pivot'] = round(pivot, Config.ROUND_DECIMALS)
        m5['r1'] = round((2 * pivot) - completed_low, Config.ROUND_DECIMALS)
        m5['r2'] = round(pivot + (completed_high - completed_low), Config.ROUND_DECIMALS)
        m5['s1'] = round((2 * pivot) - completed_high, Config.ROUND_DECIMALS)
        m5['s2'] = round(pivot - (completed_high - completed_low), Config.ROUND_DECIMALS)
        m5['support'] = round(float(low_m5.tail(20).min()), Config.ROUND_DECIMALS)
        m5['resistance'] = round(float(high_m5.tail(20).max()), Config.ROUND_DECIMALS)

        # Box Metrics
        m5.update(StructuralMetrics.calculate_box_metrics(high_m5, low_m5, m5['atr14']))

        # Save actual OHLCV values in m5 dictionary for orchestrator to consume
        m5['open'] = round(open_m5.iloc[-1], Config.ROUND_DECIMALS)
        m5['high'] = round(high_m5.iloc[-1], Config.ROUND_DECIMALS)
        m5['low'] = round(low_m5.iloc[-1], Config.ROUND_DECIMALS)
        m5['close'] = round(close_m5.iloc[-1], Config.ROUND_DECIMALS)

        # ------------------------------------------------------------
        # 2. M1 Indicators
        # ------------------------------------------------------------
        m1 = {}
        close_m1 = df_m1['close']
        high_m1 = df_m1['high']
        low_m1 = df_m1['low']
        open_m1 = df_m1['open']
        volume_m1 = df_m1['volume']

        m1.update(CoreIndicators.calculate_ema(close_m1, [5, 10, 20, 50], Config.ROUND_DECIMALS))
        
        m1['rsi7'] = CoreIndicators.calc_rsi(close_m1, 7)
        m1['rsi14'] = CoreIndicators.calc_rsi(close_m1, 14)

        m1.update(CoreIndicators.calculate_macd(close_m1, Config.ROUND_DECIMALS, include_hist=False))
        m1.update(CoreIndicators.calculate_stochastic(close_m1, high_m1, low_m1))
        m1.update(StructuralMetrics.calculate_atr(high_m1, low_m1, close_m1, Config.ROUND_DECIMALS, extended=False))
        m1.update(CoreIndicators.calculate_bb(close_m1, 20, Config.ROUND_DECIMALS, require_100=False))
        
        last_candle_m1 = df_m1.iloc[-1]
        pivot_m1 = (last_candle_m1['high'] + last_candle_m1['low'] + last_candle_m1['close']) / 3
        m1['pivot'] = round(pivot_m1, Config.ROUND_DECIMALS)
        m1['r1'] = round((2 * pivot_m1) - last_candle_m1['low'], Config.ROUND_DECIMALS)
        m1['s1'] = round((2 * pivot_m1) - last_candle_m1['high'], Config.ROUND_DECIMALS)
        
        m1.update(StructuralMetrics.calculate_volume_metrics(volume_m1, Config.VOLUME_MA_PERIOD, extended=False))

        # Save actual OHLCV values in m1 dictionary for orchestrator to consume
        m1['open'] = round(open_m1.iloc[-1], Config.ROUND_DECIMALS)
        m1['high'] = round(high_m1.iloc[-1], Config.ROUND_DECIMALS)
        m1['low'] = round(low_m1.iloc[-1], Config.ROUND_DECIMALS)
        m1['close'] = round(close_m1.iloc[-1], Config.ROUND_DECIMALS)

        # ------------------------------------------------------------
        # 2.5. M15 Indicators
        # ------------------------------------------------------------
        m15 = {}
        import time
        from datetime import timezone
        if df_m15 is not None and not df_m15.empty:
            try:
                last_ts_m15 = df_m15.index[-1]
                if hasattr(last_ts_m15, 'tz_localize') and getattr(last_ts_m15, 'tz', None) is None:
                    last_ts_m15_utc = last_ts_m15.tz_localize(timezone.utc)
                elif hasattr(last_ts_m15, 'tz_convert') and getattr(last_ts_m15, 'tz', None) is not None:
                    last_ts_m15_utc = last_ts_m15.tz_convert(timezone.utc)
                else:
                    last_ts_m15_utc = pd.to_datetime(last_ts_m15, utc=True)
                m15_age_ms = int((time.time() - last_ts_m15_utc.timestamp()) * 1000)
            except Exception as e:
                import traceback
                traceback.print_exc()
                logger.warning(f"Error parsing M15 timestamp: {e}")
                m15_age_ms = 0
                
            if m15_age_ms > 2400000:
                raise ValueError(f"FAIL-FAST: M15 data is STALE (age: {m15_age_ms} ms). No fallback allowed.")
                
            close_m15 = df_m15['close']
            if len(close_m15) >= 20:
                ema20_m15 = close_m15.ewm(span=20, adjust=False).mean().iloc[-1]
                m15['bias'] = 'BULLISH' if close_m15.iloc[-1] > ema20_m15 else 'BEARISH'
            else:
                raise ValueError("Insufficient M15 data for bias calculation")
        else:
            raise ValueError("Insufficient M15 data for bias calculation")

        # ------------------------------------------------------------
        # 3. Metadata & Price
        # ------------------------------------------------------------
        now_ms = time.time() * 1000
        last_m1_candle = df_m1.iloc[-1]
        last_m5_candle = df_m5.iloc[-1]

        def _get_utc_timestamp_ms(idx_val) -> float:
            if hasattr(idx_val, 'tz_localize') and getattr(idx_val, 'tz', None) is None:
                ts = idx_val.tz_localize(timezone.utc)
            elif hasattr(idx_val, 'tz_convert') and getattr(idx_val, 'tz', None) is not None:
                ts = idx_val.tz_convert(timezone.utc)
            else:
                ts = pd.to_datetime(idx_val, utc=True)
            return ts.timestamp() * 1000

        try:
            last_ts_m1_ms = _get_utc_timestamp_ms(last_m1_candle.name)
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.warning(f"Error parsing last M1 candle timestamp: {e}")
            last_ts_m1_ms = now_ms

        try:
            last_ts_m5_ms = _get_utc_timestamp_ms(last_m5_candle.name)
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.warning(f"Error parsing last M5 candle timestamp: {e}")
            last_ts_m5_ms = now_ms

        # Calculate age in milliseconds
        now_ms = time.time() * 1000
        m1_age_ms = max(0, int(now_ms - last_ts_m1_ms))
        m5_age_ms = max(0, int(now_ms - last_ts_m5_ms))

        # Calculate quality based on age (M1 stale > 120,000 ms, M5 stale > 600,000 ms)
        m1_quality = 'STALE' if m1_age_ms > 120000 else 'FRESH'
        m5_quality = 'STALE' if m5_age_ms > 600000 else 'FRESH'

        utc_hour = datetime.now(timezone.utc).hour
        if 0 <= utc_hour < 8:
            session_name = "ASIAN"
        elif 8 <= utc_hour < 14:
            session_name = "LONDON"
        elif 14 <= utc_hour < 21:
            session_name = "NEW YORK"
        else:
            session_name = "ASIAN"

        if forming_data is None:
            forming_data = {
                'm1_open': round(last_m1_candle['open'], Config.ROUND_DECIMALS),
                'm1_age': m1_age_ms,
                'm1_quality': m1_quality,
                'm5_open': round(last_m5_candle['open'], Config.ROUND_DECIMALS),
                'm5_age': m5_age_ms,
                'm5_quality': m5_quality
            }

        meta = {
            'close': round(last_m1_candle['close'], Config.ROUND_DECIMALS),
            'high': round(last_m1_candle['high'], Config.ROUND_DECIMALS),
            'low': round(last_m1_candle['low'], Config.ROUND_DECIMALS),
            'open': forming_data['m1_open'],
            'session': session_name,
            'm1_open': forming_data['m1_open'],
            'm1_age': forming_data['m1_age'],
            'm1_quality': forming_data['m1_quality'],
            'm5_open': forming_data['m5_open'],
            'm5_age': forming_data['m5_age'],
            'm5_quality': forming_data['m5_quality']
        }

        # ------------------------------------------------------------
        # สรุป Layer 1
        # ------------------------------------------------------------
        return {
            'm15': m15,
            'm5': m5,
            'm1': m1,
            'meta': meta,
            'ohlcv': meta  # Keep ohlcv for backward compatibility with older engines
        }

    # ========================
    # CORE METHODS (GET / SET)
    # ========================
    def _ensure_symbol(self, symbol: str):
        """สร้างโครงสร้างข้อมูลของ symbol ถ้ายังไม่มี"""
        with self._lock:
            if symbol not in self._data:
                self._data[symbol] = {
                    'raw': {}
                }

    def set_raw(self, symbol: str, raw_data: Dict[str, Any]):
        """บันทึก Layer 1 (Raw Indicators)"""
        self._ensure_symbol(symbol)
        with self._lock:
            self._data[symbol]['raw'] = raw_data

    def get(self, symbol: str, layer: str, *keys) -> Any:
        """ดึงข้อมูลจาก Store"""
        with self._lock:
            if symbol not in self._data:
                raise KeyError(f"Symbol '{symbol}' not found in IndicatorStore")
            data = self._data[symbol]
            if layer not in data:
                raise KeyError(f"Layer '{layer}' not found for symbol '{symbol}'")
            layer_data = data[layer]
            for key in keys:
                if isinstance(layer_data, dict):
                    if key not in layer_data:
                        raise KeyError(f"Key '{key}' not found")
                    layer_data = layer_data[key]
                else:
                    raise ValueError(f"Expected dict but got {type(layer_data).__name__} when accessing '{key}'")
            if isinstance(layer_data, dict):
                return copy.deepcopy(layer_data)
            return layer_data

    def get_full_snapshot(self, symbol: str) -> Dict[str, Any]:
        """ดึงข้อมูลทั้งหมดของ symbol หนึ่ง"""
        with self._lock:
            return copy.deepcopy(self._data[symbol])

    def get_all_symbols(self) -> List[str]:
        """รายชื่อคู่เงินทั้งหมดที่มีข้อมูล"""
        with self._lock:
            return list(self._data.keys())

    def get_payload(self, symbol: str) -> Dict[str, Any]:
        """คืนค่า Raw Indicator ({'m5': ..., 'm1': ..., 'ohlcv': ...})"""
        snapshot = self.get_full_snapshot(symbol)
        return snapshot['raw']

    # ========================
    # PROCESS PAIR (หลัก)
    # ========================
    def process_pair(self, symbol: str, df_m1: pd.DataFrame, df_m5: pd.DataFrame, df_m15: Optional[pd.DataFrame] = None, forming_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        ขั้นตอนหลัก: คำนวณ Layer 1 (Raw Indicators) จาก DataFrame
        """
        logger.debug(f"Processing {symbol} ...")
        
        # คำนวณ Raw Indicators
        raw = self.calculate_raw_indicators(df_m1, df_m5, df_m15, forming_data)
        
        # บันทึกลง Store
        self.set_raw(symbol, raw)
        
        return raw

    def calculate_all(self, symbol: str, candles_dict: Dict[str, pd.DataFrame], session: str = "asian", forming_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Backward compatibility wrapper"""
        df_m1 = candles_dict['M1']
        df_m5 = candles_dict['M5']
        df_m15 = candles_dict['M15']
        
        if df_m1 is None or df_m5 is None or df_m1.empty or df_m5.empty:
            logger.error(f"Missing M1 or M5 data for {symbol} in calculate_all")
            raise Exception(f"Missing M1 or M5 data for {symbol}")

        return self.process_pair(symbol, df_m1, df_m5, df_m15, forming_data)

    # ========================
    # CLEANUP
    # ========================
    def clear_all(self):
        """ล้างข้อมูลทั้งหมด"""
        with self._lock:
            self._data.clear()
        logger.debug("IndicatorStore cleared")

    def clear_symbol(self, symbol: str):
        """ล้างข้อมูลเฉพาะคู่"""
        with self._lock:
            if symbol in self._data:
                del self._data[symbol]

# Global Singleton Instance สำหรับให้ไฟล์อื่น import ไปใช้
store = IndicatorStore()

# =================================================================
# ตัวอย่างการใช้งาน
# =================================================================
def run_parallel_processing(store: IndicatorStore, symbols_data: Dict[str, Tuple[pd.DataFrame, pd.DataFrame]]):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time

    results = {}
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=len(symbols_data)) as executor:
        future_to_symbol = {
            executor.submit(store.process_pair, symbol, df_m1, df_m5): symbol
            for symbol, (df_m1, df_m5) in symbols_data.items()
        }
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                raw = future.result()
                results[symbol] = raw
                logger.info(f"✅ {symbol} processed in {time.perf_counter() - start:.3f}s")
            except Exception as e:
                raise

    elapsed = time.perf_counter() - start
    logger.info(f"✨ All pairs processed in {elapsed:.3f} seconds")
    return results

if __name__ == "__main__":
    from datetime import datetime
    print("INDICATOR STORE - REFACTORED (PURE LAYER 1)")
