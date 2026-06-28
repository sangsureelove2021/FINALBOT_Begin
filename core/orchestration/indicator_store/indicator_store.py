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
from typing import Dict, Any, Optional, List, Tuple
import logging

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
    def calculate_raw_indicators(df_m1: pd.DataFrame, df_m5: pd.DataFrame, df_m15: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        คำนวณ Indicator ดิบ (Layer 1) จาก DataFrame M1, M5 และ M15
        - ใช้ Pandas Vectorization (เร็วมาก)
        - ส่งคืน dict ที่มีเฉพาะ 'm5', 'm1', 'ohlcv'
        """
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
        m5['ema5'] = round(close_m5.ewm(span=5, adjust=False).mean().iloc[-1], Config.ROUND_DECIMALS)
        m5['ema10'] = round(close_m5.ewm(span=10, adjust=False).mean().iloc[-1], Config.ROUND_DECIMALS)
        m5['ema20'] = round(close_m5.ewm(span=20, adjust=False).mean().iloc[-1], Config.ROUND_DECIMALS)
        m5['ema50'] = round(close_m5.ewm(span=50, adjust=False).mean().iloc[-1], Config.ROUND_DECIMALS)
        m5['ema100'] = round(close_m5.ewm(span=100, adjust=False).mean().iloc[-1], Config.ROUND_DECIMALS)
        m5['ema200'] = round(close_m5.ewm(span=200, adjust=False).mean().iloc[-1], Config.ROUND_DECIMALS)
        
        # M5 Bias
        m5['bias'] = 'BULLISH' if close_m5.iloc[-1] > m5['ema20'] else 'BEARISH'

        # Bollinger Bands (20, 2)
        sma20 = close_m5.rolling(window=20, min_periods=1).mean()
        std20 = close_m5.rolling(window=20, min_periods=1).std(ddof=0).fillna(0)
        m5['bb_upper'] = round((sma20 + 2 * std20).iloc[-1], Config.ROUND_DECIMALS)
        m5['bb_lower'] = round((sma20 - 2 * std20).iloc[-1], Config.ROUND_DECIMALS)
        bbw_series = (sma20 + 2 * std20) - (sma20 - 2 * std20)
        m5['bb_width'] = round(bbw_series.iloc[-1], Config.ROUND_DECIMALS)
        m5['bbw_sma_100'] = round(bbw_series.rolling(window=100, min_periods=1).mean().iloc[-1], Config.ROUND_DECIMALS) if len(bbw_series) >= 100 else m5['bb_width']

        # RSI (7, 14)
        def calc_rsi(series, period):
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean().fillna(0)
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean().replace(0, 1e-9).fillna(1e-9)
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0

        m5['rsi7'] = round(calc_rsi(close_m5, 7), 2)
        m5['rsi14'] = round(calc_rsi(close_m5, 14), 2)

        # MACD (12, 26, 9)
        exp12 = close_m5.ewm(span=12, adjust=False).mean()
        exp26 = close_m5.ewm(span=26, adjust=False).mean()
        macd_line = exp12 - exp26
        macd_signal = macd_line.ewm(span=9, adjust=False).mean()
        m5['macd'] = round(macd_line.iloc[-1], Config.ROUND_DECIMALS)
        m5['macd_signal'] = round(macd_signal.iloc[-1], Config.ROUND_DECIMALS)
        m5['macd_hist'] = round((macd_line - macd_signal).iloc[-1], Config.ROUND_DECIMALS)

        # Stochastic (14, 3, 3)
        low_min = low_m5.rolling(window=14, min_periods=1).min()
        high_max = high_m5.rolling(window=14, min_periods=1).max()
        stoch_k_raw = 100 * (close_m5 - low_min) / (high_max - low_min + 1e-9)
        stoch_k = stoch_k_raw.rolling(window=3, min_periods=1).mean()
        stoch_d = stoch_k.rolling(window=3, min_periods=1).mean()
        m5['stoch_k'] = round(stoch_k.iloc[-1], 2)
        m5['stoch_d'] = round(stoch_d.iloc[-1], 2)

        # ATR (14)
        high_low = high_m5 - low_m5
        high_close = np.abs(high_m5 - close_m5.shift())
        low_close = np.abs(low_m5 - close_m5.shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr_series = ranges.ewm(alpha=1/14, adjust=False).mean().dropna()
        if len(atr_series) > 0:
            current_atr = atr_series.iloc[-1]
            m5['atr14'] = round(current_atr, Config.ROUND_DECIMALS)
            m5['atr_percentile'] = round((np.sum(atr_series <= current_atr) / len(atr_series)) * 100, 2)
            atr_std = atr_series.std()
            atr_std = 0 if pd.isna(atr_std) else atr_std
            m5['atr_zscore'] = round((current_atr - atr_series.mean()) / (atr_std + 1e-9), 2)
            
            recent_atr_avg = atr_series.tail(10).mean()
            past_atr_avg = atr_series.iloc[-20:-10].mean() if len(atr_series) >= 20 else recent_atr_avg
            m5['atr_recent_avg'] = round(recent_atr_avg, Config.ROUND_DECIMALS)
            m5['atr_past_avg'] = round(past_atr_avg, Config.ROUND_DECIMALS)
        else:
            m5['atr14'] = 0.0
            m5['atr_percentile'] = 50.0
            m5['atr_zscore'] = 0.0
            m5['atr_recent_avg'] = 0.0
            m5['atr_past_avg'] = 0.0

        # ================================================================
        # ADX, DI+, DI- (Wilder's Smoothing)
        # ================================================================
        def calc_adx(high, low, close, period=14):
            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Directional Movement
            up_move = high - high.shift()
            down_move = low.shift() - low
            
            plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
            minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
            
            # Wilder's Smoothing (EMA with alpha = 1/period)
            tr_smooth = tr.ewm(alpha=1/period, adjust=False).mean()
            plus_dm_smooth = pd.Series(plus_dm).ewm(alpha=1/period, adjust=False).mean()
            minus_dm_smooth = pd.Series(minus_dm).ewm(alpha=1/period, adjust=False).mean()
            
            # DI+
            di_plus = 100 * (plus_dm_smooth / (tr_smooth + 1e-9))
            di_minus = 100 * (minus_dm_smooth / (tr_smooth + 1e-9))
            
            # DX
            dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus + 0.000001)
            
            # ADX = Smooth DX
            adx = dx.ewm(alpha=1/period, adjust=False).mean()
            
            # Fill NaN
            adx = adx.fillna(0)
            di_plus = di_plus.fillna(0)
            di_minus = di_minus.fillna(0)
            dx = dx.fillna(0)
            
            return {
                'adx': round(adx.iloc[-1], 2),
                'di_plus': round(di_plus.iloc[-1], 2),
                'di_minus': round(di_minus.iloc[-1], 2),
                'dx': round(dx.iloc[-1], 2)
            }
        
        adx_result = calc_adx(high_m5, low_m5, close_m5, Config.ADX_PERIOD)
        m5['adx'] = adx_result['adx']
        m5['di_plus'] = adx_result['di_plus']
        m5['di_minus'] = adx_result['di_minus']
        m5['dx'] = adx_result['dx']

        # ================================================================
        # ROC (Rate of Change)
        # ================================================================
        m5['roc'] = round(((close_m5.iloc[-1] / (close_m5.iloc[-10] + 1e-9)) - 1) * 100, 4) if len(close_m5) >= 10 else 0.0

        # ================================================================
        # VOLUME RATIO & MA20
        # ================================================================
        volume_ma20 = volume_m5.rolling(window=Config.VOLUME_MA_PERIOD, min_periods=1).mean()
        current_volume = volume_m5.iloc[-1]
        m5['volume'] = current_volume
        m5['volume_ma20'] = round(volume_ma20.iloc[-1], 2)
        m5['volume_ratio'] = min(round(current_volume / (volume_ma20.iloc[-1] + 0.000001), 3), 10.0)
        
        # Volume Spike Detection
        m5['volume_spike'] = bool(m5['volume_ratio'] > 2.0)
        


        # ================================================================
        # LINEAR REGRESSION SLOPE
        # ================================================================
        def calc_slope(series, period=Config.SLOPE_PERIOD):
            if len(series) < period:
                return 0.0
            y = series.tail(period).values
            x = np.arange(period)
            slope, _ = np.polyfit(x, y, 1)
            return slope
        
        m5['slope_10'] = round(calc_slope(close_m5, 10), Config.ROUND_DECIMALS)
        m5['slope_20'] = round(calc_slope(close_m5, 20), Config.ROUND_DECIMALS)
        m5['slope_50'] = round(calc_slope(close_m5, 50), Config.ROUND_DECIMALS)



        # Pivot Points
        last_candle = df_m5.iloc[-1]
        pivot = (last_candle['high'] + last_candle['low'] + last_candle['close']) / 3
        m5['pivot'] = round(pivot, Config.ROUND_DECIMALS)
        m5['r1'] = round((2 * pivot) - last_candle['low'], Config.ROUND_DECIMALS)
        m5['r2'] = round(pivot + (last_candle['high'] - last_candle['low']), Config.ROUND_DECIMALS)
        m5['s1'] = round((2 * pivot) - last_candle['high'], Config.ROUND_DECIMALS)
        m5['s2'] = round(pivot - (last_candle['high'] - last_candle['low']), Config.ROUND_DECIMALS)

        # Box Metrics
        highs = df_m5['high'].tail(50).values
        lows = df_m5['low'].tail(50).values
        if len(highs) >= 20:
            ref_high = max(highs[-20:])
            ref_low = min(lows[-20:])
            ref_range = ref_high - ref_low
            box_dur = 0
            for i in range(len(highs) - 1, -1, -1):
                if ref_low <= highs[i] <= ref_high and ref_low <= lows[i] <= ref_high:
                    box_dur += 1
                else:
                    break
            m5['box_duration'] = box_dur
            m5['box_tightness'] = round(ref_range / (m5['atr14'] + 1e-9), 2)
        else:
            m5['box_duration'] = 10
            m5['box_tightness'] = 2.5

        # ------------------------------------------------------------
        # 2. M1 Indicators
        # ------------------------------------------------------------
        m1 = {}
        close_m1 = df_m1['close']
        high_m1 = df_m1['high']
        low_m1 = df_m1['low']
        open_m1 = df_m1['open']
        volume_m1 = df_m1['volume']

        m1['ema5'] = round(close_m1.ewm(span=5, adjust=False).mean().iloc[-1], Config.ROUND_DECIMALS)
        m1['ema10'] = round(close_m1.ewm(span=10, adjust=False).mean().iloc[-1], Config.ROUND_DECIMALS)
        m1['ema20'] = round(close_m1.ewm(span=20, adjust=False).mean().iloc[-1], Config.ROUND_DECIMALS)
        m1['ema50'] = round(close_m1.ewm(span=50, adjust=False).mean().iloc[-1], Config.ROUND_DECIMALS)
        
        m1['rsi7'] = round(calc_rsi(close_m1, 7), 2)
        m1['rsi14'] = round(calc_rsi(close_m1, 14), 2)

        exp12_m1 = close_m1.ewm(span=12, adjust=False).mean()
        exp26_m1 = close_m1.ewm(span=26, adjust=False).mean()
        macd_line_m1 = exp12_m1 - exp26_m1
        macd_signal_m1 = macd_line_m1.ewm(span=9, adjust=False).mean()
        m1['macd'] = round(macd_line_m1.iloc[-1], Config.ROUND_DECIMALS)
        m1['macd_signal'] = round(macd_signal_m1.iloc[-1], Config.ROUND_DECIMALS)

        low_min_m1 = low_m1.rolling(window=14, min_periods=1).min()
        high_max_m1 = high_m1.rolling(window=14, min_periods=1).max()
        stoch_k_raw_m1 = 100 * (close_m1 - low_min_m1) / (high_max_m1 - low_min_m1 + 1e-9)
        stoch_k_m1 = stoch_k_raw_m1.rolling(window=3, min_periods=1).mean()
        stoch_d_m1 = stoch_k_m1.rolling(window=3, min_periods=1).mean()
        m1['stoch_k'] = round(stoch_k_m1.iloc[-1], 2)
        m1['stoch_d'] = round(stoch_d_m1.iloc[-1], 2)

        high_low_m1 = high_m1 - low_m1
        high_close_m1 = np.abs(high_m1 - close_m1.shift())
        low_close_m1 = np.abs(low_m1 - close_m1.shift())
        ranges_m1 = pd.concat([high_low_m1, high_close_m1, low_close_m1], axis=1).max(axis=1)
        m1['atr14'] = round(ranges_m1.ewm(alpha=1/14, adjust=False).mean().iloc[-1], Config.ROUND_DECIMALS)

        m1['bb_upper'] = round((close_m1.rolling(20, min_periods=1).mean() + 2*close_m1.rolling(20, min_periods=1).std(ddof=0).fillna(0)).iloc[-1], Config.ROUND_DECIMALS)
        m1['bb_lower'] = round((close_m1.rolling(20, min_periods=1).mean() - 2*close_m1.rolling(20, min_periods=1).std(ddof=0).fillna(0)).iloc[-1], Config.ROUND_DECIMALS)
        
        last_candle_m1 = df_m1.iloc[-1]
        pivot_m1 = (last_candle_m1['high'] + last_candle_m1['low'] + last_candle_m1['close']) / 3
        m1['pivot'] = round(pivot_m1, Config.ROUND_DECIMALS)
        m1['r1'] = round((2 * pivot_m1) - last_candle_m1['low'], Config.ROUND_DECIMALS)
        m1['s1'] = round((2 * pivot_m1) - last_candle_m1['high'], Config.ROUND_DECIMALS)
        
        m1['volume'] = volume_m1.iloc[-1]
        m1['volume_ratio'] = min(round(volume_m1.iloc[-1] / (volume_m1.rolling(20, min_periods=1).mean().iloc[-1] + 0.000001), 3), 10.0)

        # ------------------------------------------------------------
        # 2.5. M15 Indicators
        # ------------------------------------------------------------
        m15 = {}
        if df_m15 is not None and not df_m15.empty:
            close_m15 = df_m15['close']
            if len(close_m15) >= 20:
                ema20_m15 = close_m15.ewm(span=20, adjust=False).mean().iloc[-1]
                m15['bias'] = 'BULLISH' if close_m15.iloc[-1] > ema20_m15 else 'BEARISH'
            else:
                m15['bias'] = 'NO'
        else:
            m15['bias'] = 'NO'

        # ------------------------------------------------------------
        # 3. Metadata & Price
        # ------------------------------------------------------------
        import time
        from datetime import datetime, timezone
        
        last_m1_candle = df_m1.iloc[-1]
        
        utc_hour = datetime.now(timezone.utc).hour
        if 0 <= utc_hour < 8:
            session_name = "ASIAN"
        elif 8 <= utc_hour < 14:
            session_name = "LONDON"
        elif 14 <= utc_hour < 21:
            session_name = "NEW YORK"
        else:
            session_name = "ASIAN"
            
        try:
            last_ts = df_m1.index[-1]
            if hasattr(last_ts, 'timestamp'):
                data_age_ms = int((time.time() - last_ts.timestamp()) * 1000)
            else:
                data_age_ms = 0
        except:
            raise
            
        data_quality = "HIGH" if data_age_ms < 120000 else "LOW" # 2 mins threshold

        meta = {
            'close': round(last_m1_candle['close'], Config.ROUND_DECIMALS),
            'high': round(last_m1_candle['high'], Config.ROUND_DECIMALS),
            'low': round(last_m1_candle['low'], Config.ROUND_DECIMALS),
            'open': round(last_m1_candle['open'], Config.ROUND_DECIMALS),
            'session': session_name,
            'data_age_ms': max(0, data_age_ms),
            'data_quality': data_quality
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
    def process_pair(self, symbol: str, df_m1: pd.DataFrame, df_m5: pd.DataFrame, df_m15: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        ขั้นตอนหลัก: คำนวณ Layer 1 (Raw Indicators) จาก DataFrame
        """
        logger.debug(f"Processing {symbol} ...")
        
        # คำนวณ Raw Indicators
        raw = self.calculate_raw_indicators(df_m1, df_m5, df_m15)
        
        # บันทึกลง Store
        self.set_raw(symbol, raw)
        
        return raw

    def calculate_all(self, symbol: str, candles_dict: Dict[str, pd.DataFrame], session: str = "asian") -> Dict[str, Any]:
        """Backward compatibility wrapper"""
        df_m1 = candles_dict['M1']
        df_m5 = candles_dict['M5']
        df_m15 = candles_dict['M15']
        
        if df_m1 is None or df_m5 is None or df_m1.empty or df_m5.empty:
            logger.error(f"Missing M1 or M5 data for {symbol} in calculate_all")
            raise Exception(f"Missing M1 or M5 data for {symbol}")

        return self.process_pair(symbol, df_m1, df_m5, df_m15)

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
