"""
indicator_store.py
------------------
Single Source of Truth (SSOT) สำหรับ FINALBOT
- คำนวณ Raw Indicators (Layer 1) ครั้งเดียว (รวม ADX, Volume Ratio, Slope)
- ให้ Engine (Layer 2) และ Classifier (Layer 3) อ่าน/เขียน
- บันทึก CSV แบบ Async (ไม่บล็อก Main Loop)
- รองรับ OTC (บังคับ Volume = 1.0)
- รองรับการทำงานแบบ Parallel 5 คู่
"""

import pandas as pd
import numpy as np
import threading
import queue
import csv
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
import logging

# ---------- Logging Setup ----------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------- Configuration ----------
class Config:
    ENABLE_CSV_LOGGING = True
    CSV_LOG_INTERVAL = 1  # บันทึกทุก 1 รอบ (ถ้า 5 = ทุก 5 รอบ)
    CSV_LOG_DIR = "logs/market_snapshots/"
    ROUND_DECIMALS = 6
    ADX_PERIOD = 14
    VOLUME_MA_PERIOD = 20
    SLOPE_PERIOD = 10  # ใช้ 10 แท่งล่าสุดสำหรับ Linear Regression

# ---------- Core Class ----------
class IndicatorStore:
    """
    จัดเก็บ Indicator ทั้งหมด (Layer 1, 2, 3) สำหรับทุกคู่เงิน
    - Layer 1: Raw Indicators (คำนวณจาก OHLCV โดยตรง)
    - Layer 2: Engine Outputs (trend, strength, volatility, structure, mtf)
    - Layer 3: Classified Result (market_state, state_confidence, etc.)
    """

    def __init__(self, enable_csv: bool = True):
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()  # ป้องกันข้อมูลชนกัน (ถ้ามี multi-thread เขียนพร้อมกัน)
        
        # CSV Logger (Async)
        self._csv_queue = queue.Queue()
        self._csv_enabled = enable_csv and Config.ENABLE_CSV_LOGGING
        self._csv_worker_thread = None
        self._csv_counter = 0  # ใช้นับรอบสำหรับ CSV_LOG_INTERVAL

        if self._csv_enabled:
            os.makedirs(Config.CSV_LOG_DIR, exist_ok=True)
            self._csv_worker_thread = threading.Thread(
                target=self._csv_worker, daemon=True, name="CSVLogger"
            )
            self._csv_worker_thread.start()
            logger.info("CSV Logger started (async mode)")

    # ========================
    # LAYER 1: RAW INDICATORS (คำนวณจาก OHLCV)
    # ========================
    @staticmethod
    def calculate_raw_indicators(df_m1: pd.DataFrame, df_m5: pd.DataFrame, symbol: str = "") -> Dict[str, Any]:
        """
        คำนวณ Indicator ดิบ (Layer 1) จาก DataFrame M1 และ M5
        - ใช้ Pandas Vectorization (เร็วมาก)
        - ส่งคืน dict ที่มี structure เหมือน SPEC_INDICATOR_STORE.md
        - รองรับ OTC: ถ้า symbol มี 'OTC' จะบังคับ Volume = 1.0
        """
        # ------------------------------------------------------------
        # 0. OTC Volume Filter
        # ------------------------------------------------------------
        is_otc = "OTC" in symbol.upper() if symbol else False
        if is_otc:
            # ถ้าเป็น OTC ให้เปลี่ยน Volume ทั้งหมดเป็น 1.0 (เพราะไม่มี Volume จริง)
            df_m5 = df_m5.copy()
            df_m5['volume'] = 1.0
            df_m1 = df_m1.copy()
            df_m1['volume'] = 1.0
            logger.debug(f"OTC detected: {symbol} → Volume forced to 1.0")

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

        # Bollinger Bands (20, 2)
        sma20 = close_m5.rolling(window=20).mean()
        std20 = close_m5.rolling(window=20).std()
        m5['bb_upper'] = round((sma20 + 2 * std20).iloc[-1], Config.ROUND_DECIMALS)
        m5['bb_lower'] = round((sma20 - 2 * std20).iloc[-1], Config.ROUND_DECIMALS)
        bbw_series = (sma20 + 2 * std20) - (sma20 - 2 * std20)
        m5['bb_width'] = round(bbw_series.iloc[-1], Config.ROUND_DECIMALS)
        m5['bbw_sma_100'] = round(bbw_series.rolling(window=100).mean().iloc[-1], Config.ROUND_DECIMALS) if len(bbw_series) >= 100 else m5['bb_width']

        # RSI (7, 14)
        def calc_rsi(series, period):
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi.iloc[-1]

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
        low_min = low_m5.rolling(window=14).min()
        high_max = high_m5.rolling(window=14).max()
        stoch_k_raw = 100 * (close_m5 - low_min) / (high_max - low_min)
        stoch_k = stoch_k_raw.rolling(window=3).mean()
        stoch_d = stoch_k.rolling(window=3).mean()
        m5['stoch_k'] = round(stoch_k.iloc[-1], 2)
        m5['stoch_d'] = round(stoch_d.iloc[-1], 2)

        # ATR (14)
        high_low = high_m5 - low_m5
        high_close = np.abs(high_m5 - close_m5.shift())
        low_close = np.abs(low_m5 - close_m5.shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr_series = ranges.rolling(window=14).mean().dropna()
        if len(atr_series) > 0:
            current_atr = atr_series.iloc[-1]
            m5['atr14'] = round(current_atr, Config.ROUND_DECIMALS)
            m5['atr_percentile'] = round((np.sum(atr_series <= current_atr) / len(atr_series)) * 100, 2)
            m5['atr_zscore'] = round((current_atr - atr_series.mean()) / (atr_series.std() + 1e-9), 2)
            
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
        # ✅ ADX, DI+, DI- (Wilder's Smoothing) — ตาม SPEC_ENGINES.md
        # ================================================================
        def calc_adx(high, low, close, period=14):
            """คำนวณ ADX, DI+, DI- แบบ Wilder's Smoothing"""
            # True Range
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            
            # Directional Movement
            up_move = high - high.shift()
            down_move = low.shift() - low
            
            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
            
            # Wilder's Smoothing (EMA with alpha = 1/period)
            tr_smooth = tr.ewm(alpha=1/period, adjust=False).mean()
            plus_dm_smooth = pd.Series(plus_dm).ewm(alpha=1/period, adjust=False).mean()
            minus_dm_smooth = pd.Series(minus_dm).ewm(alpha=1/period, adjust=False).mean()
            
            # DI+
            di_plus = 100 * (plus_dm_smooth / tr_smooth)
            di_minus = 100 * (minus_dm_smooth / tr_smooth)
            
            # DX
            dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus + 0.000001)
            
            # ADX = Smooth DX
            adx = dx.ewm(alpha=1/period, adjust=False).mean()
            
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
        # ✅ ROC (Rate of Change) — ตาม SPEC_ENGINES.md
        # ================================================================
        m5['roc'] = round(((close_m5.iloc[-1] / close_m5.iloc[-10]) - 1) * 100, 4) if len(close_m5) >= 10 else 0.0

        # ================================================================
        # ✅ VOLUME RATIO & MA20 — (ใช้ยืนยัน Breakout, Accumulation)
        # ================================================================
        volume_ma20 = volume_m5.rolling(window=Config.VOLUME_MA_PERIOD).mean()
        current_volume = volume_m5.iloc[-1]
        m5['volume'] = round(current_volume, 2)
        m5['volume_ma20'] = round(volume_ma20.iloc[-1], 2)
        m5['volume_ratio'] = round(current_volume / (volume_ma20.iloc[-1] + 0.000001), 3)  # + epsilon ป้องกัน div by zero
        
        # Volume Spike Detection (ratio > 2.0)
        m5['volume_spike'] = m5['volume_ratio'] > 2.0
        
        # Volume Trend (ใช้ Slope ของ Volume 5 แท่งล่าสุด)
        vol_slice = volume_m5.tail(5)
        if len(vol_slice) >= 5:
            x = np.arange(5)
            slope, _ = np.polyfit(x, vol_slice.values, 1)
            if slope > 0.5:
                m5['volume_trend'] = 'RISING'
            elif slope < -0.5:
                m5['volume_trend'] = 'FALLING'
            else:
                m5['volume_trend'] = 'STABLE'
        else:
            m5['volume_trend'] = 'STABLE'

        # ================================================================
        # ✅ LINEAR REGRESSION SLOPE — (Trend Engine ต้องใช้)
        # ================================================================
        def calc_slope(series, period=Config.SLOPE_PERIOD):
            """คำนวณความชันของ Linear Regression จาก n แท่งล่าสุด"""
            if len(series) < period:
                return 0.0
            y = series.tail(period).values
            x = np.arange(period)
            slope, _ = np.polyfit(x, y, 1)
            return slope
        
        m5['slope_10'] = round(calc_slope(close_m5, 10), Config.ROUND_DECIMALS)
        m5['slope_20'] = round(calc_slope(close_m5, 20), Config.ROUND_DECIMALS)
        m5['slope_50'] = round(calc_slope(close_m5, 50), Config.ROUND_DECIMALS)

        # Support / Resistance (ใช้ Swing High/Low จาก 5 แท่งล่าสุด)
        last_n = df_m5.tail(20)
        swing_high = last_n['high'].max()
        swing_low = last_n['low'].min()
        m5['support'] = round(swing_low, Config.ROUND_DECIMALS)
        m5['resistance'] = round(swing_high, Config.ROUND_DECIMALS)

        # Pivot Points (Standard)
        last_candle = df_m5.iloc[-1]
        pivot = (last_candle['high'] + last_candle['low'] + last_candle['close']) / 3
        m5['pivot'] = round(pivot, Config.ROUND_DECIMALS)
        m5['r1'] = round((2 * pivot) - last_candle['low'], Config.ROUND_DECIMALS)
        m5['r2'] = round(pivot + (last_candle['high'] - last_candle['low']), Config.ROUND_DECIMALS)
        m5['s1'] = round((2 * pivot) - last_candle['high'], Config.ROUND_DECIMALS)
        m5['s2'] = round(pivot - (last_candle['high'] - last_candle['low']), Config.ROUND_DECIMALS)

        # Box Metrics (Duration & Tightness)
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
            m5['box_tightness'] = round(ref_range / (m5.get('atr14', 0.0001) + 1e-9), 2)
        else:
            m5['box_duration'] = 10
            m5['box_tightness'] = 2.5

        # ------------------------------------------------------------
        # 2. M1 Indicators (เฉพาะที่จำเป็น)
        # ------------------------------------------------------------
        m1 = {}
        close_m1 = df_m1['close']
        high_m1 = df_m1['high']
        low_m1 = df_m1['low']
        open_m1 = df_m1['open']
        volume_m1 = df_m1['volume']

        m1['ema5'] = round(close_m1.ewm(span=5, adjust=False).mean().iloc[-1], Config.ROUND_DECIMALS)
        m1['ema20'] = round(close_m1.ewm(span=20, adjust=False).mean().iloc[-1], Config.ROUND_DECIMALS)
        
        m1['rsi14'] = round(calc_rsi(close_m1, 14), 2)

        exp12_m1 = close_m1.ewm(span=12, adjust=False).mean()
        exp26_m1 = close_m1.ewm(span=26, adjust=False).mean()
        macd_line_m1 = exp12_m1 - exp26_m1
        macd_signal_m1 = macd_line_m1.ewm(span=9, adjust=False).mean()
        m1['macd'] = round(macd_line_m1.iloc[-1], Config.ROUND_DECIMALS)
        m1['macd_signal'] = round(macd_signal_m1.iloc[-1], Config.ROUND_DECIMALS)

        low_min_m1 = low_m1.rolling(window=14).min()
        high_max_m1 = high_m1.rolling(window=14).max()
        stoch_k_raw_m1 = 100 * (close_m1 - low_min_m1) / (high_max_m1 - low_min_m1)
        stoch_k_m1 = stoch_k_raw_m1.rolling(window=3).mean()
        stoch_d_m1 = stoch_k_m1.rolling(window=3).mean()
        m1['stoch_k'] = round(stoch_k_m1.iloc[-1], 2)
        m1['stoch_d'] = round(stoch_d_m1.iloc[-1], 2)

        high_low_m1 = high_m1 - low_m1
        high_close_m1 = np.abs(high_m1 - close_m1.shift())
        low_close_m1 = np.abs(low_m1 - close_m1.shift())
        ranges_m1 = pd.concat([high_low_m1, high_close_m1, low_close_m1], axis=1).max(axis=1)
        m1['atr14'] = round(ranges_m1.rolling(window=14).mean().iloc[-1], Config.ROUND_DECIMALS)

        last_n_m1 = df_m1.tail(20)
        m1['support'] = round(last_n_m1['low'].min(), Config.ROUND_DECIMALS)
        m1['resistance'] = round(last_n_m1['high'].max(), Config.ROUND_DECIMALS)
        m1['bb_upper'] = round((close_m1.rolling(20).mean() + 2*close_m1.rolling(20).std()).iloc[-1], Config.ROUND_DECIMALS)
        m1['bb_lower'] = round((close_m1.rolling(20).mean() - 2*close_m1.rolling(20).std()).iloc[-1], Config.ROUND_DECIMALS)
        m1['volume'] = round(volume_m1.iloc[-1], 2)
        m1['volume_ratio'] = round(volume_m1.iloc[-1] / (volume_m1.rolling(20).mean().iloc[-1] + 0.000001), 3)

        # ------------------------------------------------------------
        # 3. Price Action (จาก M5 แท่งล่าสุด 2 แท่ง)
        # ------------------------------------------------------------
        pa = {}
        last = df_m5.iloc[-1]
        prev = df_m5.iloc[-2] if len(df_m5) > 1 else last

        # Last Candle Bias
        if last['close'] > last['open']:
            pa['last_candle'] = 'BULLISH'
        elif last['close'] < last['open']:
            pa['last_candle'] = 'BEARISH'
        else:
            pa['last_candle'] = 'DOJI'

        # Body Strength
        body = abs(last['close'] - last['open'])
        avg_body = abs(df_m5['close'] - df_m5['open']).rolling(20).mean().iloc[-1]
        if body > avg_body * 1.5:
            pa['body_strength'] = 'STRONG'
        elif body > avg_body * 0.8:
            pa['body_strength'] = 'MEDIUM'
        else:
            pa['body_strength'] = 'WEAK'

        # Wick Dominance
        upper_wick = last['high'] - max(last['close'], last['open'])
        lower_wick = min(last['close'], last['open']) - last['low']
        total_wick = upper_wick + lower_wick + 0.000001
        if upper_wick / total_wick > 0.6:
            pa['wick_dominance'] = 'HIGH_UPPER_WICK'
        elif lower_wick / total_wick > 0.6:
            pa['wick_dominance'] = 'HIGH_LOWER_WICK'
        else:
            pa['wick_dominance'] = 'BALANCED'

        # Momentum Bias (ใช้ Volume Ratio ด้วย)
        vol_ratio = m5['volume_ratio']
        if last['close'] > prev['close'] and vol_ratio > 1.2:
            pa['momentum_bias'] = 'BULLISH'
        elif last['close'] < prev['close'] and vol_ratio > 1.2:
            pa['momentum_bias'] = 'BEARISH'
        else:
            pa['momentum_bias'] = 'NEUTRAL'

        # Move Quality
        range_last = last['high'] - last['low']
        avg_range = (df_m5['high'] - df_m5['low']).rolling(20).mean().iloc[-1]
        if range_last > avg_range * 1.3 and pa['body_strength'] == 'STRONG' and vol_ratio > 1.3:
            pa['move_quality'] = 'CLEAN_TRENDING'
        elif range_last > avg_range * 0.8:
            pa['move_quality'] = 'NORMAL'
        else:
            pa['move_quality'] = 'NOISY'

        # Pattern Detection (Engulfing / Doji / Hammer)
        pa['pattern'] = 'NONE'
        if (last['close'] > last['open'] and prev['close'] < prev['open'] and 
            last['close'] > prev['open'] and last['open'] < prev['close']):
            pa['pattern'] = 'BULLISH_ENGULFING'
        elif (last['close'] < last['open'] and prev['close'] > prev['open'] and 
              last['close'] < prev['open'] and last['open'] > prev['close']):
            pa['pattern'] = 'BEARISH_ENGULFING'
        elif body < avg_body * 0.2:
            pa['pattern'] = 'DOJI'
        elif (pa['last_candle'] == 'BULLISH' and lower_wick > body * 2 and upper_wick < body * 0.5):
            pa['pattern'] = 'HAMMER'

        # Trap Alert (ใช้ Volume ด้วย)
        pa['trap_alert'] = 'NONE'
        if (pa['last_candle'] == 'BEARISH' and last['close'] > prev['close'] and 
            last['high'] > prev['high'] and vol_ratio < 1.0):
            pa['trap_alert'] = 'BEAR_TRAP'
        elif (pa['last_candle'] == 'BULLISH' and last['close'] < prev['close'] and 
              last['low'] < prev['low'] and vol_ratio < 1.0):
            pa['trap_alert'] = 'BULL_TRAP'

        # SR Interaction
        price = last['close']
        support = m5['support']
        resistance = m5['resistance']
        range_sr = resistance - support
        if range_sr == 0:
            pa['sr_interaction'] = 'NONE'
        else:
            dist_to_support = (price - support) / range_sr
            if dist_to_support < 0.15:
                pa['sr_interaction'] = 'NEAR_SUPPORT'
            elif dist_to_support > 0.85:
                pa['sr_interaction'] = 'NEAR_RESISTANCE'
            elif price > resistance:
                pa['sr_interaction'] = 'BREAKING_ABOVE_RESISTANCE'
            elif price < support:
                pa['sr_interaction'] = 'BREAKING_BELOW_SUPPORT'
            else:
                pa['sr_interaction'] = 'MIDDLE'

        # Rejection Zone
        pa['rejection_zone'] = 'NONE'
        if pa['sr_interaction'] in ['NEAR_SUPPORT', 'BREAKING_BELOW_SUPPORT']:
            pa['rejection_zone'] = 'SUPPORT_ZONE'
        elif pa['sr_interaction'] in ['NEAR_RESISTANCE', 'BREAKING_ABOVE_RESISTANCE']:
            pa['rejection_zone'] = 'RESISTANCE_ZONE'

        # ------------------------------------------------------------
        # 4. Metadata & Price
        # ------------------------------------------------------------
        meta = {
            'close': round(last['close'], Config.ROUND_DECIMALS),
            'high': round(last['high'], Config.ROUND_DECIMALS),
            'low': round(last['low'], Config.ROUND_DECIMALS),
            'open': round(last['open'], Config.ROUND_DECIMALS)
        }

        # ------------------------------------------------------------
        # สรุป Layer 1
        # ------------------------------------------------------------
        return {
            'm5': m5,
            'm1': m1,
            'price_action': pa,
            'ohlcv': meta
        }

    # ========================
    # CORE METHODS (GET / SET)
    # ========================
    def _ensure_symbol(self, symbol: str):
        """สร้างโครงสร้างข้อมูลของ symbol ถ้ายังไม่มี"""
        with self._lock:
            if symbol not in self._data:
                self._data[symbol] = {
                    'meta': {},
                    'raw': {},
                    'engines': {},
                    'classified': {},
                    'decision': {}
                }

    def set_raw(self, symbol: str, raw_data: Dict[str, Any]):
        """บันทึก Layer 1 (Raw Indicators)"""
        self._ensure_symbol(symbol)
        with self._lock:
            self._data[symbol]['raw'] = raw_data
            # อัปเดต Meta
            self._data[symbol]['meta']['current_price'] = raw_data.get('ohlcv', {}).get('close', 0.0)
            self._data[symbol]['meta']['timestamp'] = datetime.utcnow().isoformat() + 'Z'

    def set_engine_output(self, symbol: str, engine_name: str, data: Dict[str, Any]):
        """บันทึก Output ของ Engine (Layer 2)"""
        self._ensure_symbol(symbol)
        with self._lock:
            if 'engines' not in self._data[symbol]:
                self._data[symbol]['engines'] = {}
            self._data[symbol]['engines'][engine_name] = data

    def set_classified(self, symbol: str, data: Dict[str, Any]):
        """บันทึกผลลัพธ์จาก MarketStateClassifier (Layer 3)"""
        self._ensure_symbol(symbol)
        with self._lock:
            self._data[symbol]['classified'] = data

    def set_decision(self, symbol: str, action: str, confidence: int, expiry: int, reason: str):
        """บันทึก Decision สุดท้าย (จาก AI_BOT หรือ AUTO_BOT)"""
        self._ensure_symbol(symbol)
        with self._lock:
            self._data[symbol]['decision'] = {
                'action': action,
                'confidence': confidence,
                'expiry': expiry,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        # ถ้าเปิด CSV Logging ให้บันทึกอัตโนมัติ
        if self._csv_enabled:
            self._enqueue_csv(symbol)

    def get(self, symbol: str, layer: str, *keys) -> Optional[Any]:
        """
        ดึงข้อมูลจาก Store
        layer: 'raw', 'engines', 'classified', 'decision', 'meta'
        keys: ชื่อฟิลด์ซ้อนกัน เช่น get('EURUSD', 'engines', 'trend', 'direction')
        """
        with self._lock:
            data = self._data.get(symbol, {})
            layer_data = data.get(layer, {})
            for key in keys:
                if isinstance(layer_data, dict):
                    layer_data = layer_data.get(key)
                else:
                    return None
            return layer_data

    def get_full_snapshot(self, symbol: str) -> Dict[str, Any]:
        """ดึงข้อมูลทั้งหมดของ symbol หนึ่ง (ใช้สำหรับสร้าง JSON ส่ง AI)"""
        with self._lock:
            return self._data.get(symbol, {})

    def get_all_symbols(self) -> List[str]:
        """รายชื่อคู่เงินทั้งหมดที่มีข้อมูล"""
        with self._lock:
            return list(self._data.keys())

    # ========================
    # PROCESS PAIR (หลัก)
    # ========================
    def process_pair(self, symbol: str, df_m1: pd.DataFrame, df_m5: pd.DataFrame) -> Dict[str, Any]:
        """
        ขั้นตอนหลัก: คำนวณ Layer 1 (Raw Indicators) จาก DataFrame
        - ใช้สำหรับเรียกในรอบหลัก
        - คืนค่า dict ของ Layer 1 ที่คำนวณได้ (เผื่อต้องการใช้ต่อ)
        """
        logger.debug(f"Processing {symbol} ...")
        
        # คำนวณ Raw Indicators (ส่ง symbol เข้าไปด้วยเพื่อเช็ค OTC)
        raw = self.calculate_raw_indicators(df_m1, df_m5, symbol)
        
        # บันทึกลง Store (Layer 1)
        self.set_raw(symbol, raw)
        
        # คืนค่าให้ Engine ตัวอื่นไปใช้ต่อ
        return raw

    def calculate_all(self, symbol: str, candles_dict: Dict[str, pd.DataFrame], session: str = "asian") -> Dict[str, Any]:
        """
        Backward compatibility wrapper สำหรับ Orchestrator รุ่นเก่า
        เรียกใช้ process_pair อัตโนมัติจาก candles_dict
        """
        df_m1 = candles_dict.get('M1')
        df_m5 = candles_dict.get('M5')
        
        if df_m1 is None or df_m5 is None or df_m1.empty or df_m5.empty:
            logger.warning(f"Missing M1 or M5 data for {symbol} in calculate_all")
            return {}

        return self.process_pair(symbol, df_m1, df_m5)

    def get_payload(self, symbol: str) -> Dict[str, Any]:
        """Backward compatibility wrapper สำหรับเก่าที่เรียก get_payload()"""
        snapshot = self.get_full_snapshot(symbol)
        return snapshot.get('raw', {})

    # ========================
    # ASYNC CSV LOGGING
    # ========================
    def _enqueue_csv(self, symbol: str):
        """ใส่ข้อมูลลง Queue เพื่อให้ CSV Worker เขียนแบบ Async"""
        self._csv_counter += 1
        if self._csv_counter % Config.CSV_LOG_INTERVAL != 0:
            return  # ข้ามรอบตาม Config

        with self._lock:
            full_data = self._data.get(symbol, {})
            if not full_data:
                return

            # Flatten ข้อมูลให้เป็น 1 แถว (Row)
            row = {
                'timestamp': full_data.get('meta', {}).get('timestamp', ''),
                'symbol': symbol,
                'price': full_data.get('meta', {}).get('current_price', 0.0),
                
                # Layer 3: Classified
                'market_state': full_data.get('classified', {}).get('state', 'UNCLEAR'),
                'state_conf': full_data.get('classified', {}).get('state_confidence', 0),
                'regime_quality': full_data.get('classified', {}).get('regime_quality', 0),
                
                # Layer 2: Engines (เฉพาะค่าสำคัญ)
                'trend_dir': full_data.get('engines', {}).get('trend', {}).get('direction', 'NONE'),
                'trend_strength': full_data.get('engines', {}).get('trend', {}).get('strength', 0),
                'adx': full_data.get('raw', {}).get('m5', {}).get('adx', 0),
                'rsi14': full_data.get('raw', {}).get('m5', {}).get('rsi14', 0),
                'vol_regime': full_data.get('engines', {}).get('volatility', {}).get('regime', 'NORMAL'),
                'struct_type': full_data.get('engines', {}).get('structure', {}).get('structure_type', 'NONE'),
                'mtf_harmony': full_data.get('engines', {}).get('mtf', {}).get('harmony', 'MIXED'),
                'bos_detected': full_data.get('engines', {}).get('structure', {}).get('bos_detected', False),
                
                # Volume
                'volume': full_data.get('raw', {}).get('m5', {}).get('volume', 0),
                'volume_ratio': full_data.get('raw', {}).get('m5', {}).get('volume_ratio', 0),
                'volume_trend': full_data.get('raw', {}).get('m5', {}).get('volume_trend', 'STABLE'),
                'volume_spike': full_data.get('raw', {}).get('m5', {}).get('volume_spike', False),
                
                # Decision
                'final_action': full_data.get('decision', {}).get('action', 'PENDING'),
                'final_conf': full_data.get('decision', {}).get('confidence', 0),
                'expiry': full_data.get('decision', {}).get('expiry', 0),
                'reason': full_data.get('decision', {}).get('reason', ''),
            }
            self._csv_queue.put(row)

    def _csv_worker(self):
        """Worker Thread สำหรับเขียน CSV (ทำงานพื้นหลัง)"""
        while True:
            try:
                row = self._csv_queue.get(timeout=1.0)
                if row is None:
                    break
                
                date_str = row['timestamp'][:10] if row['timestamp'] else datetime.utcnow().strftime('%Y-%m-%d')
                symbol = row['symbol']
                
                # สร้างโฟลเดอร์รายวัน
                day_dir = os.path.join(Config.CSV_LOG_DIR, date_str)
                os.makedirs(day_dir, exist_ok=True)
                
                file_path = os.path.join(day_dir, f"{symbol}_{date_str}.csv")
                
                # เขียนไฟล์ (append)
                file_exists = os.path.isfile(file_path)
                with open(file_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=row.keys())
                    if not file_exists:
                        writer.writeheader()
                    writer.writerow(row)
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"CSV Worker error: {e}")

    def shutdown(self):
        """ปิดระบบ (หยุด CSV Worker)"""
        if self._csv_worker_thread and self._csv_worker_thread.is_alive():
            self._csv_queue.put(None)
            self._csv_worker_thread.join(timeout=2.0)
            logger.info("CSV Logger shutdown complete")

    # ========================
    # CLEANUP
    # ========================
    def clear_all(self):
        """ล้างข้อมูลทั้งหมด (ใช้ตอนหมดรอบ)"""
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
# ตัวอย่างการใช้งาน (Parallel Processing สำหรับ 5 คู่)
# =================================================================
def run_parallel_processing(store: IndicatorStore, symbols_data: Dict[str, Tuple[pd.DataFrame, pd.DataFrame]]):
    """
    ฟังก์ชันสำหรับประมวลผล Layer 1 แบบ Parallel (หลายคู่พร้อมกัน)
    symbols_data: {'EURUSD': (df_m1, df_m5), 'GBPUSD': (df_m1, df_m5), ...}
    """
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
                logger.error(f"❌ {symbol} failed: {e}")
                results[symbol] = None

    elapsed = time.perf_counter() - start
    logger.info(f"✨ All pairs processed in {elapsed:.3f} seconds")
    return results


# =================================================================
# EXAMPLE USAGE (ถ้ารันไฟล์นี้โดยตรง)
# =================================================================
if __name__ == "__main__":
    """
    ตัวอย่างการใช้งาน (สำหรับทดสอบ)
    """
    print("=" * 50)
    print("INDICATOR STORE - TEST MODE (WITH ADX, VOLUME, SLOPE)")
    print("=" * 50)

    # สร้างข้อมูลตัวอย่าง
    from datetime import datetime, timedelta
    import random

    def generate_sample_data(symbol: str, base_price: float):
        """สร้าง Dataframe ตัวอย่าง 200 แถว"""
        np.random.seed(42)
        dates = pd.date_range(end=datetime.utcnow(), periods=200, freq='1min')
        prices = base_price + np.cumsum(np.random.normal(0, 0.0003, 200))
        df = pd.DataFrame({
            'open': prices + np.random.normal(0, 0.0001, 200),
            'high': prices + np.abs(np.random.normal(0.0002, 0.0002, 200)),
            'low': prices - np.abs(np.random.normal(0.0002, 0.0002, 200)),
            'close': prices,
            'volume': np.random.randint(100, 500, 200)
        }, index=dates)
        df['open'] = df['open'].shift(1).fillna(df['close'])
        return df

    # สร้าง Store
    store = IndicatorStore(enable_csv=True)

    # สร้างข้อมูล 5 คู่ (รวม OTC)
    pairs = {
        'EURUSD': (generate_sample_data('EURUSD', 1.1054), generate_sample_data('EURUSD', 1.1054).resample('5min').last().ffill()),
        'GBPUSD': (generate_sample_data('GBPUSD', 1.2650), generate_sample_data('GBPUSD', 1.2650).resample('5min').last().ffill()),
        'USDJPY-OTC': (generate_sample_data('USDJPY-OTC', 155.20), generate_sample_data('USDJPY-OTC', 155.20).resample('5min').last().ffill()),  # ← OTC
        'AUDUSD': (generate_sample_data('AUDUSD', 0.6650), generate_sample_data('AUDUSD', 0.6650).resample('5min').last().ffill()),
        'NZDUSD': (generate_sample_data('NZDUSD', 0.6150), generate_sample_data('NZDUSD', 0.6150).resample('5min').last().ffill()),
    }

    # แก้ไข M5 ให้เป็นช่วง 5 นาทีจริงๆ
    for k in pairs:
        m1 = pairs[k][0]
        m5 = m1.resample('5min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        pairs[k] = (m1, m5)

    # รัน Parallel Processing
    print("\n🔄 Processing 5 pairs in parallel (including OTC)...")
    results = run_parallel_processing(store, pairs)

    # ตรวจสอบผลลัพธ์
    print("\n📊 RESULTS (Check ADX, Volume Ratio, Slope):")
    for symbol in pairs.keys():
        snapshot = store.get_full_snapshot(symbol)
        raw = snapshot.get('raw', {})
        m5 = raw.get('m5', {})
        pa = raw.get('price_action', {})
        print(f"\n  {symbol}:")
        print(f"    Price: {m5.get('ema5', 'N/A')}")
        print(f"    RSI14: {m5.get('rsi14', 'N/A')}")
        print(f"    ADX: {m5.get('adx', 'N/A')} (DI+: {m5.get('di_plus', 'N/A')}, DI-: {m5.get('di_minus', 'N/A')})")
        print(f"    Volume Ratio: {m5.get('volume_ratio', 'N/A')} (Spike: {m5.get('volume_spike', 'N/A')})")
        print(f"    Volume Trend: {m5.get('volume_trend', 'N/A')}")
        print(f"    Slope (10): {m5.get('slope_10', 'N/A')}")
        print(f"    Pattern: {pa.get('pattern', 'NONE')}")

    # ทดสอบ Set Engine Output และ Classified
    store.set_engine_output('EURUSD', 'trend', {'direction': 'UP', 'strength': 70, 'type': 'IMPULSIVE'})
    store.set_engine_output('EURUSD', 'strength', {'adx': 32, 'momentum_level': 'STRONG'})
    store.set_engine_output('EURUSD', 'volatility', {'regime': 'NORMAL'})
    store.set_engine_output('EURUSD', 'structure', {'structure_type': 'TRENDING', 'bos_detected': False})
    store.set_engine_output('EURUSD', 'mtf', {'harmony': 'GOOD'})
    store.set_classified('EURUSD', {'state': 'TRENDING_STRONG', 'state_confidence': 85})
    
    # บันทึก Decision (จะ Trigger CSV Logging)
    store.set_decision('EURUSD', 'CALL', 85, 3, 'Strong trend confirmed with volume')
    
    # ดึงข้อมูลเพื่อแสดง
    print("\n📈 EURUSD Full Snapshot (ตัวอย่าง):")
    snapshot = store.get_full_snapshot('EURUSD')
    print(json.dumps({
        'price': snapshot.get('meta', {}).get('current_price'),
        'market_state': snapshot.get('classified', {}).get('state'),
        'trend_dir': snapshot.get('engines', {}).get('trend', {}).get('direction'),
        'adx': snapshot.get('raw', {}).get('m5', {}).get('adx'),
        'volume_ratio': snapshot.get('raw', {}).get('m5', {}).get('volume_ratio'),
        'final_action': snapshot.get('decision', {}).get('action')
    }, indent=2))

    # ปิดระบบ
    store.shutdown()
    print("\n✅ Test complete. Check CSV logs in:", Config.CSV_LOG_DIR)
