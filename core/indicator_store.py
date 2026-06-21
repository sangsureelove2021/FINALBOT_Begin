import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any

from ta.trend import EMAIndicator, MACD, ADXIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, ROCIndicator
from ta.volatility import BollingerBands, AverageTrueRange

class IndicatorStore:
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def calculate_all(self, symbol: str, candles_dict: Dict[str, pd.DataFrame], session: str = "asian") -> Dict[str, Any]:
        current_time = datetime.utcnow()
        
        self._store[symbol] = {
            'm15': {},
            'm5': {},
            'm1': {},
            'price_action': {},
            'market_state': 'UNCLEAR',
            'session': session,
            'timestamp': current_time.isoformat(),
            'expires_at': current_time + timedelta(seconds=60)
        }

        # M15
        if 'M15' in candles_dict and not candles_dict['M15'].empty:
            self._store[symbol]['m15'] = self._calculate_m15(candles_dict['M15'])

        # M5
        if 'M5' in candles_dict and not candles_dict['M5'].empty:
            df5 = candles_dict['M5']
            self._store[symbol]['m5'] = self._calculate_m5(df5)
            self._store[symbol]['current_price'] = float(df5['close'].iloc[-1])

        # M1
        if 'M1' in candles_dict and not candles_dict['M1'].empty:
            self._store[symbol]['m1'] = self._calculate_m1(candles_dict['M1'])

        return self._store[symbol]

    def _calculate_basic(self, df: pd.DataFrame) -> Dict[str, float]:
        res = {}
        if len(df) < 50:
            return res
        # EMAs used for trend
        res['ema20'] = float(EMAIndicator(close=df['close'], window=20).ema_indicator().iloc[-1])
        res['ema50'] = float(EMAIndicator(close=df['close'], window=50).ema_indicator().iloc[-1])
        res['ema100'] = float(EMAIndicator(close=df['close'], window=100).ema_indicator().iloc[-1])
        res['ema200'] = float(EMAIndicator(close=df['close'], window=200).ema_indicator().iloc[-1])
        # Need close for slope calculations later
        res['close'] = float(df['close'].iloc[-1])
        return res

    def _calculate_m15(self, df: pd.DataFrame) -> Dict[str, float]:
        res = self._calculate_basic(df)
        if not res: return res
        sup, res_ = self._calculate_sr(df, lookback=50)
        res['support'] = float(sup)
        res['resistance'] = float(res_)
        return res

    def _calculate_m5(self, df: pd.DataFrame) -> Dict[str, float]:
        res = self._calculate_basic(df)
        if not res: return res
        res['ema5'] = float(EMAIndicator(close=df['close'], window=5).ema_indicator().iloc[-1])
        res['ema10'] = float(EMAIndicator(close=df['close'], window=10).ema_indicator().iloc[-1])
        
        bb = BollingerBands(close=df['close'], window=20, window_dev=2)
        res['bb_lower'] = float(bb.bollinger_lband().iloc[-1])
        res['bb_upper'] = float(bb.bollinger_hband().iloc[-1])
        res['bb_width'] = float(bb.bollinger_wband().iloc[-1]) / 100.0
            
        res['rsi7'] = float(RSIIndicator(close=df['close'], window=7).rsi().iloc[-1])
        res['rsi14'] = float(RSIIndicator(close=df['close'], window=14).rsi().iloc[-1])

        macd = MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9)
        res['macd'] = float(macd.macd().iloc[-1])
        res['macd_hist'] = float(macd.macd_diff().iloc[-1])
        res['macd_signal'] = float(macd.macd_signal().iloc[-1])

        # ADX (14) & DI
        adx_ind = ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=14)
        res['adx'] = float(adx_ind.adx().iloc[-1])
        res['di_plus'] = float(adx_ind.adx_pos().iloc[-1])
        res['di_minus'] = float(adx_ind.adx_neg().iloc[-1])

        # ROC (10)
        roc = ROCIndicator(close=df['close'], window=10)
        res['roc10'] = float(roc.roc().iloc[-1])

        stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=14, smooth_window=3)
        res['stoch_k'] = float(stoch.stoch().iloc[-1])
        res['stoch_d'] = float(stoch.stoch_signal().iloc[-1])

        atr = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14)
        res['atr14'] = float(atr.average_true_range().iloc[-1])

        sup, res_ = self._calculate_sr(df, lookback=20)
        res['support'] = float(sup)
        res['resistance'] = float(res_)

        high, low, close = df['high'].iloc[-2], df['low'].iloc[-2], df['close'].iloc[-2]
        pivot = (high + low + close) / 3
        res['pivot'], res['r1'], res['s1'] = float(pivot), float((2*pivot)-low), float((2*pivot)-high)
        res['r2'], res['s2'] = float(pivot + (high-low)), float(pivot - (high-low))
        return res

    def _calculate_m1(self, df: pd.DataFrame) -> Dict[str, float]:
        res = {}
        if len(df) < 50: return res
        res['ema5'] = float(EMAIndicator(close=df['close'], window=5).ema_indicator().iloc[-1])
        res['ema20'] = float(EMAIndicator(close=df['close'], window=20).ema_indicator().iloc[-1])
        
        bb = BollingerBands(close=df['close'], window=20, window_dev=2)
        res['bb_lower'], res['bb_upper'] = float(bb.bollinger_lband().iloc[-1]), float(bb.bollinger_hband().iloc[-1])
        res['rsi14'] = float(RSIIndicator(close=df['close'], window=14).rsi().iloc[-1])
        
        macd = MACD(close=df['close'], window_slow=26, window_fast=12, window_sign=9)
        res['macd'], res['macd_signal'] = float(macd.macd().iloc[-1]), float(macd.macd_signal().iloc[-1])
        
        stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'], window=14, smooth_window=3)
        res['stoch_k'], res['stoch_d'] = float(stoch.stoch().iloc[-1]), float(stoch.stoch_signal().iloc[-1])
        
        atr = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14)
        res['atr14'] = float(atr.average_true_range().iloc[-1])
        
        sup, res_ = self._calculate_sr(df, lookback=20)
        res['support'], res['resistance'] = float(sup), float(res_)
        return res

    def _calculate_sr(self, df: pd.DataFrame, lookback: int = 20) -> tuple[float, float]:
        try:
            return float(df['low'].tail(lookback).min()), float(df['high'].tail(lookback).max())
        except Exception:
            return 0.0, 0.0

    def update_market_state(self, symbol: str, m15_bias: str, m5_market_state: str, price_action_data: Dict[str, Any]):
        if symbol in self._store:
            if 'm15' in self._store[symbol]: self._store[symbol]['m15']['bias'] = m15_bias
            if 'm5' in self._store[symbol]: self._store[symbol]['m5']['market_state'] = m5_market_state
            self._store[symbol]['market_state'] = m5_market_state
            self._store[symbol]['price_action'] = price_action_data

    def get_payload(self, symbol: str) -> Dict[str, Any]:
        raw = self._store.get(symbol, {})
        import math
        def sanitize(v):
            if isinstance(v, dict):
                return {k: sanitize(v2) for k, v2 in v.items()}
            elif isinstance(v, list):
                return [sanitize(v2) for v2 in v]
            elif isinstance(v, float):
                if math.isnan(v) or math.isinf(v):
                    return 0.0
                return v
            return v
        return sanitize(raw)

    def clear_all(self):
        self._store.clear()

store = IndicatorStore()
