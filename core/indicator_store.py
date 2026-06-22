"""
IndicatorStore — Central Indicator Cache for FINALBOT

Flow:
    DataAdapter.update() → candles_dict
        → IndicatorStore.calculate_all(symbol, candles_dict)
            → store._store[symbol]  (ดึงด้วย get_payload)
                → Orchestrator / AI Bridge

Rules:
    • คำนวณแต่ละ timeframe เฉพาะเมื่อมีแท่งใหม่ (ตรวจ last_ts)
    • indicator แต่ละตัวแยก try/except — ตัวหนึ่งพังไม่กระทบตัวอื่น
    • ผล NaN / Inf ถูก sanitize เป็น 0.0 ก่อนส่งออก
"""

import math
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, ROCIndicator
from ta.volatility import BollingerBands, AverageTrueRange

logger = logging.getLogger(__name__)


class IndicatorStore:
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._last_ts: Dict[str, Dict[str, Optional[pd.Timestamp]]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate_all(
        self,
        symbol: str,
        candles_dict: Dict[str, pd.DataFrame],
        session: str = "asian",
    ) -> Dict[str, Any]:
        """คำนวณ indicator ทุก timeframe — ข้ามถ้าแท่งล่าสุดยังเป็น timestamp เดิม"""
        now = datetime.utcnow()

        if symbol not in self._store:
            self._store[symbol] = {
                'm15': {}, 'm5': {}, 'm1': {},
                'price_action': {},
                'market_state': 'UNCLEAR',
                'session': session,
                'timestamp': now.isoformat(),
                'expires_at': now + timedelta(seconds=60),
            }
        if symbol not in self._last_ts:
            self._last_ts[symbol] = {'M1': None, 'M5': None, 'M15': None}

        self._store[symbol]['session'] = session
        self._store[symbol]['timestamp'] = now.isoformat()
        self._store[symbol]['expires_at'] = now + timedelta(seconds=60)

        # ── M15 ─────────────────────────────────────────────────────────
        df15 = candles_dict.get('M15')
        if df15 is not None and not df15.empty:
            ts15 = df15.index[-1]
            if ts15 != self._last_ts[symbol]['M15']:
                self._store[symbol]['m15'] = self._calculate_m15(df15)
                self._last_ts[symbol]['M15'] = ts15

        # ── M5 ──────────────────────────────────────────────────────────
        df5 = candles_dict.get('M5')
        if df5 is not None and not df5.empty:
            ts5 = df5.index[-1]
            if ts5 != self._last_ts[symbol]['M5']:
                self._store[symbol]['m5'] = self._calculate_m5(df5)
                self._store[symbol]['current_price'] = float(df5['close'].iloc[-1])
                self._last_ts[symbol]['M5'] = ts5
                # Price Action ใช้ timestamp cache เดียวกับ M5
                self._store[symbol]['price_action'] = self._calculate_price_action(
                    df5, self._store[symbol].get('m5', {})
                )

        # ── M1 ──────────────────────────────────────────────────────────
        df1 = candles_dict.get('M1')
        if df1 is not None and not df1.empty:
            ts1 = df1.index[-1]
            if ts1 != self._last_ts[symbol]['M1']:
                self._store[symbol]['m1'] = self._calculate_m1(df1)
                self._last_ts[symbol]['M1'] = ts1

        return self._store[symbol]

    def update_market_state(
        self,
        symbol: str,
        m15_bias: str,
        m5_market_state: str,
        price_action_data: Dict[str, Any],
    ) -> None:
        if symbol not in self._store:
            return
        if 'm15' in self._store[symbol]:
            self._store[symbol]['m15']['bias'] = m15_bias
        if 'm5' in self._store[symbol]:
            self._store[symbol]['m5']['market_state'] = m5_market_state
        self._store[symbol]['market_state'] = m5_market_state
        self._store[symbol]['price_action'] = price_action_data

    def get_payload(self, symbol: str) -> Dict[str, Any]:
        """คืนผลลัพธ์ indicator โดย sanitize NaN/Inf เป็น 0.0"""
        return _sanitize(self._store.get(symbol, {}))

    def clear_all(self) -> None:
        self._store.clear()
        self._last_ts.clear()

    # ------------------------------------------------------------------
    # Timeframe calculators
    # ------------------------------------------------------------------

    def _calculate_m15(self, df: pd.DataFrame) -> Dict[str, float]:
        res = self._calculate_basic(df)
        if not res:
            return res
        sup, res_ = _calc_sr(df, lookback=50)
        res['support'] = sup
        res['resistance'] = res_

        # M15 bias จาก EMA20 vs EMA50
        try:
            ema20 = res.get('ema20', 0.0)
            ema50 = res.get('ema50', 0.0)
            if ema20 > ema50:
                res['bias'] = 'BULLISH'
            elif ema20 < ema50:
                res['bias'] = 'BEARISH'
            else:
                res['bias'] = 'NEUTRAL'
        except Exception as e:
            logger.debug(f"M15 bias calc failed: {e}")
            res['bias'] = 'NEUTRAL'

        return res

    def _calculate_m5(self, df: pd.DataFrame) -> Dict[str, float]:
        res = self._calculate_basic(df)
        if not res:
            return res

        _safe(res, 'ema5',  lambda: float(EMAIndicator(close=df['close'], window=5).ema_indicator().iloc[-1]))
        _safe(res, 'ema10', lambda: float(EMAIndicator(close=df['close'], window=10).ema_indicator().iloc[-1]))

        _safe_group(res, {
            'bb_lower': lambda: float(BollingerBands(close=df['close'], window=20, window_dev=2).bollinger_lband().iloc[-1]),
            'bb_upper': lambda: float(BollingerBands(close=df['close'], window=20, window_dev=2).bollinger_hband().iloc[-1]),
            'bb_width': lambda: float(BollingerBands(close=df['close'], window=20, window_dev=2).bollinger_wband().iloc[-1]) / 100.0,
        })

        _safe(res, 'rsi7',  lambda: float(RSIIndicator(close=df['close'], window=7).rsi().iloc[-1]))
        _safe(res, 'rsi14', lambda: float(RSIIndicator(close=df['close'], window=14).rsi().iloc[-1]))

        _safe_group(res, {
            'macd':        lambda: float(MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9).macd().iloc[-1]),
            'macd_hist':   lambda: float(MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9).macd_diff().iloc[-1]),
            'macd_signal': lambda: float(MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9).macd_signal().iloc[-1]),
        })

        _safe_group(res, {
            'adx':      lambda: float(ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=14).adx().iloc[-1]),
            'di_plus':  lambda: float(ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=14).adx_pos().iloc[-1]),
            'di_minus': lambda: float(ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=14).adx_neg().iloc[-1]),
        })

        _safe(res, 'roc10', lambda: float(ROCIndicator(close=df['close'], window=10).roc().iloc[-1]))

        _safe_group(res, {
            'stoch_k': lambda: float(StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=14, smooth_window=3).stoch().iloc[-1]),
            'stoch_d': lambda: float(StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=14, smooth_window=3).stoch_signal().iloc[-1]),
        })

        _safe(res, 'atr14', lambda: float(AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14).average_true_range().iloc[-1]))

        sup, res_ = _calc_sr(df, lookback=20)
        res['support'] = sup
        res['resistance'] = res_

        try:
            h, l, c = float(df['high'].iloc[-2]), float(df['low'].iloc[-2]), float(df['close'].iloc[-2])
            pivot = (h + l + c) / 3
            res['pivot'] = pivot
            res['r1'] = (2 * pivot) - l
            res['s1'] = (2 * pivot) - h
            res['r2'] = pivot + (h - l)
            res['s2'] = pivot - (h - l)
        except Exception as e:
            logger.debug(f"Pivot calc failed: {e}")

        return res

    def _calculate_m1(self, df: pd.DataFrame) -> Dict[str, float]:
        res: Dict[str, float] = {}
        if len(df) < 50:
            return res

        _safe(res, 'ema5',  lambda: float(EMAIndicator(close=df['close'], window=5).ema_indicator().iloc[-1]))
        _safe(res, 'ema20', lambda: float(EMAIndicator(close=df['close'], window=20).ema_indicator().iloc[-1]))

        _safe_group(res, {
            'bb_lower': lambda: float(BollingerBands(close=df['close'], window=20, window_dev=2).bollinger_lband().iloc[-1]),
            'bb_upper': lambda: float(BollingerBands(close=df['close'], window=20, window_dev=2).bollinger_hband().iloc[-1]),
        })

        _safe(res, 'rsi14', lambda: float(RSIIndicator(close=df['close'], window=14).rsi().iloc[-1]))

        _safe_group(res, {
            'macd':        lambda: float(MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9).macd().iloc[-1]),
            'macd_signal': lambda: float(MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9).macd_signal().iloc[-1]),
        })

        _safe_group(res, {
            'stoch_k': lambda: float(StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=14, smooth_window=3).stoch().iloc[-1]),
            'stoch_d': lambda: float(StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=14, smooth_window=3).stoch_signal().iloc[-1]),
        })

        _safe(res, 'atr14', lambda: float(AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14).average_true_range().iloc[-1]))

        sup, res_ = _calc_sr(df, lookback=20)
        res['support'] = sup
        res['resistance'] = res_

        # last_candle สำหรับ M1 entry confirmation
        try:
            c_m1 = float(df['close'].iloc[-1])
            o_m1 = float(df['open'].iloc[-1])
            res['last_candle'] = 'BULLISH' if c_m1 > o_m1 else 'BEARISH' if c_m1 < o_m1 else 'NEUTRAL'
        except Exception:
            res['last_candle'] = 'NEUTRAL'

        return res

    def _calculate_basic(self, df: pd.DataFrame) -> Dict[str, float]:
        """EMA 20/50/100/200 + close — ใช้ร่วมกันทุก timeframe"""
        res: Dict[str, float] = {}
        if len(df) < 50:
            return res
        _safe(res, 'ema20',  lambda: float(EMAIndicator(close=df['close'], window=20).ema_indicator().iloc[-1]))
        _safe(res, 'ema50',  lambda: float(EMAIndicator(close=df['close'], window=50).ema_indicator().iloc[-1]))
        _safe(res, 'ema100', lambda: float(EMAIndicator(close=df['close'], window=100).ema_indicator().iloc[-1]))
        _safe(res, 'ema200', lambda: float(EMAIndicator(close=df['close'], window=200).ema_indicator().iloc[-1]))
        res['close'] = float(df['close'].iloc[-1])
        return res

    def _calculate_price_action(self, df: pd.DataFrame, m5_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        คำนวณ Price Action จาก M5 candles — 9 indicators ทุกตัวแยก try/except
        """
        default: Dict[str, Any] = {
            'pattern':        'NONE',
            'last_candle':    'NEUTRAL',
            'body_strength':  'WEAK',
            'rejection_zone': 'MIDDLE',
            'wick_dominance': 'BALANCED',
            'momentum_bias':  'NEUTRAL',
            'move_quality':   'NORMAL',
            'trap_alert':     'NONE',
            'sr_interaction': 'NONE',
        }

        if df is None or len(df) < 5:
            return default

        res = dict(default)
        m5 = m5_data or {}

        # ── pattern ──────────────────────────────────────────────────────
        try:
            o1 = float(df['open'].iloc[-2]);  h1 = float(df['high'].iloc[-2])
            l1 = float(df['low'].iloc[-2]);   c1 = float(df['close'].iloc[-2])
            o0 = float(df['open'].iloc[-1]);  h0 = float(df['high'].iloc[-1])
            l0 = float(df['low'].iloc[-1]);   c0 = float(df['close'].iloc[-1])

            body0 = abs(c0 - o0)
            body1 = abs(c1 - o1)
            rng0  = (h0 - l0) or 1e-10
            uw0   = h0 - max(o0, c0)
            lw0   = min(o0, c0) - l0

            if body0 < rng0 * 0.1:
                res['pattern'] = 'DOJI'
            elif lw0 >= body0 * 2 and uw0 <= body0 * 0.5 and c0 >= l0 + rng0 * 0.6:
                res['pattern'] = 'HAMMER'
            elif uw0 >= body0 * 2 and lw0 <= body0 * 0.5 and c0 <= l0 + rng0 * 0.4:
                res['pattern'] = 'SHOOTING_STAR'
            elif c1 < o1 and c0 > o0 and o0 <= c1 and c0 >= o1 and body0 > body1:
                res['pattern'] = 'BULLISH_ENGULFING'
            elif c1 > o1 and c0 < o0 and o0 >= c1 and c0 <= o1 and body0 > body1:
                res['pattern'] = 'BEARISH_ENGULFING'
        except Exception as e:
            logger.debug(f"PA pattern: {e}")

        # ── last_candle ───────────────────────────────────────────────────
        try:
            c = float(df['close'].iloc[-1]); o = float(df['open'].iloc[-1])
            res['last_candle'] = 'BULLISH' if c > o else 'BEARISH' if c < o else 'NEUTRAL'
        except Exception as e:
            logger.debug(f"PA last_candle: {e}")

        # ── body_strength (body / ATR) ────────────────────────────────────
        try:
            atr = float(AverageTrueRange(
                high=df['high'], low=df['low'], close=df['close'], window=14
            ).average_true_range().iloc[-1])
            body = abs(float(df['close'].iloc[-1]) - float(df['open'].iloc[-1]))
            r = body / atr if atr > 0 else 0
            res['body_strength'] = 'STRONG' if r > 0.6 else 'MEDIUM' if r >= 0.3 else 'WEAK'
        except Exception as e:
            logger.debug(f"PA body_strength: {e}")

        # ── rejection_zone (vs BB bands) ──────────────────────────────────
        try:
            bb_upper = m5.get('bb_upper', 0.0)
            bb_lower = m5.get('bb_lower', 0.0)
            price = float(df['close'].iloc[-1])
            if bb_upper > bb_lower > 0:
                thr = (bb_upper - bb_lower) * 0.15
                if price >= bb_upper - thr:
                    res['rejection_zone'] = 'NEAR_RESISTANCE'
                elif price <= bb_lower + thr:
                    res['rejection_zone'] = 'NEAR_SUPPORT'
                else:
                    res['rejection_zone'] = 'MIDDLE'
        except Exception as e:
            logger.debug(f"PA rejection_zone: {e}")

        # ── wick_dominance ────────────────────────────────────────────────
        try:
            oc = float(df['open'].iloc[-1]); cc = float(df['close'].iloc[-1])
            hc = float(df['high'].iloc[-1]); lc = float(df['low'].iloc[-1])
            bd = abs(cc - oc)
            uw = hc - max(oc, cc)
            lw = min(oc, cc) - lc
            if uw > bd * 1.5:
                res['wick_dominance'] = 'HIGH_WICK'
            elif lw > bd * 1.5:
                res['wick_dominance'] = 'LOW_WICK'
            else:
                res['wick_dominance'] = 'BALANCED'
        except Exception as e:
            logger.debug(f"PA wick_dominance: {e}")

        # ── momentum_bias (last 3 candles) ────────────────────────────────
        try:
            cls3 = df['close'].values[-3:]
            opn3 = df['open'].values[-3:]
            bulls = sum(1 for i in range(len(cls3)) if cls3[i] > opn3[i])
            bears = sum(1 for i in range(len(cls3)) if cls3[i] < opn3[i])
            res['momentum_bias'] = 'BULLISH' if bulls > bears else 'BEARISH' if bears > bulls else 'NEUTRAL'
        except Exception as e:
            logger.debug(f"PA momentum_bias: {e}")

        # ── move_quality (efficiency) ─────────────────────────────────────
        try:
            closes = df['close'].values[-10:]
            if len(closes) >= 3:
                net   = abs(float(closes[-1]) - float(closes[0]))
                total = sum(abs(float(closes[i+1]) - float(closes[i])) for i in range(len(closes)-1))
                if total > 0:
                    eff = net / total
                    res['move_quality'] = (
                        'CLEAN_TRENDING' if eff >= 0.75
                        else 'NORMAL'    if eff >= 0.50
                        else 'NOISY'     if eff >= 0.25
                        else 'CHAOTIC'
                    )
        except Exception as e:
            logger.debug(f"PA move_quality: {e}")

        # ── trap_alert ────────────────────────────────────────────────────
        try:
            ot = float(df['open'].iloc[-1]); ct = float(df['close'].iloc[-1])
            ht = float(df['high'].iloc[-1]); lt = float(df['low'].iloc[-1])
            rng_t = (ht - lt) or 1e-10
            mid_t = lt + rng_t * 0.5
            uw_t  = ht - max(ot, ct)
            lw_t  = min(ot, ct) - lt
            if uw_t > rng_t * 0.2 and ct < mid_t:
                res['trap_alert'] = 'BULL_TRAP'
            elif lw_t > rng_t * 0.2 and ct > mid_t:
                res['trap_alert'] = 'BEAR_TRAP'
        except Exception as e:
            logger.debug(f"PA trap_alert: {e}")

        # ── sr_interaction ────────────────────────────────────────────────
        try:
            support    = m5.get('support', 0.0)
            resistance = m5.get('resistance', 0.0)
            cp  = float(df['close'].iloc[-1])
            pp  = float(df['close'].iloc[-2]) if len(df) >= 2 else cp
            if support > 0 and resistance > 0:
                thr = (resistance - support) * 0.03
                if cp > resistance and pp <= resistance:
                    res['sr_interaction'] = 'BREAKING_ABOVE_RESISTANCE'
                elif cp < support and pp >= support:
                    res['sr_interaction'] = 'BREAKING_BELOW_SUPPORT'
                elif abs(cp - support) <= thr and cp > pp:
                    res['sr_interaction'] = 'BOUNCING_FROM_SUPPORT'
                elif abs(cp - resistance) <= thr and cp < pp:
                    res['sr_interaction'] = 'BOUNCING_FROM_RESISTANCE'
        except Exception as e:
            logger.debug(f"PA sr_interaction: {e}")

        return res


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _safe(res: dict, key: str, fn) -> None:
    try:
        res[key] = fn()
    except Exception as e:
        logger.debug(f"Indicator '{key}' failed: {e}")
        res[key] = 0.0


def _safe_group(res: dict, mapping: dict) -> None:
    for key, fn in mapping.items():
        _safe(res, key, fn)


def _calc_sr(df: pd.DataFrame, lookback: int = 20) -> Tuple[float, float]:
    try:
        return float(df['low'].tail(lookback).min()), float(df['high'].tail(lookback).max())
    except Exception:
        return 0.0, 0.0


def _sanitize(v: Any) -> Any:
    if isinstance(v, dict):
        return {k: _sanitize(v2) for k, v2 in v.items()}
    if isinstance(v, list):
        return [_sanitize(v2) for v2 in v]
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return 0.0
    return v


# Singleton
store = IndicatorStore()
