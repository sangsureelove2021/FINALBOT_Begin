"""
TIER 1 - STRENGTH ENGINE


Measure momentum strength using ADX, RSI, MACD, and Rate of Change.
Detects divergence between price and momentum indicators.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

from core.engines.base_engine import BaseEngine


class StrengthEngine(BaseEngine):
    """Tier 1: Momentum Strength Engine"""
    
    ENGINE_NAME = "strength_engine"
    ENGINE_VERSION = "1.0.0"
    TIER = 1
    MIN_CANDLES = 200
    
    def _analyze(self, candles_df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        adx_val, di_plus, di_minus = self._calculate_adx(candles_df)
        rsi_val = self._calculate_rsi(candles_df['close'])
        macd_val, macd_signal, macd_hist = self._calculate_macd(candles_df['close'])
        roc_val = self._calculate_roc(candles_df['close'])
        
        momentum_level = self._classify_momentum_level(adx_val)
        divergence = self._detect_divergence(candles_df, rsi_val, macd_hist)
        strength_score = self._calculate_strength_score(adx_val, rsi_val, abs(macd_val), abs(roc_val))
        exhaustion_risk = self._calculate_exhaustion_risk(adx_val, rsi_val, macd_val, candles_df)
        
        return {
            'adx': float(adx_val),
            'di_plus': float(di_plus),
            'di_minus': float(di_minus),
            'rsi': float(rsi_val),
            'macd': float(macd_val),
            'momentum_level': momentum_level,
            'roc': float(roc_val),
            'divergence': divergence,
            'strength_score': strength_score,
            'exhaustion_risk': exhaustion_risk,
            'confidence': min(100, strength_score + 10),  # Add for compatibility
        }
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> Tuple[float, float, float]:
        try:
            high, low, close = df['high'], df['low'], df['close']
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = np.maximum(tr1, np.maximum(tr2, tr3))
            atr = tr.rolling(period).mean()
            
            up_move = high.diff()
            down_move = -low.diff()
            pos_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
            neg_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
            
            pos_di = 100 * (pd.Series(pos_dm).rolling(period).mean() / atr)
            neg_di = 100 * (pd.Series(neg_dm).rolling(period).mean() / atr)
            
            di_diff = abs(pos_di - neg_di)
            di_sum = pos_di + neg_di
            di_diff_smooth = di_diff.rolling(period).mean()
            adx = 100 * (di_diff_smooth / di_sum).rolling(period).mean()
            
            return (
                float(adx.iloc[-1]) if not np.isnan(adx.iloc[-1]) else 0,
                float(pos_di.iloc[-1]) if not np.isnan(pos_di.iloc[-1]) else 0,
                float(neg_di.iloc[-1]) if not np.isnan(neg_di.iloc[-1]) else 0,
            )
        except Exception as e:
            return 0.0, 0.0, 0.0
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        try:
            deltas = prices.diff()
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = pd.Series(gains).rolling(period).mean()
            avg_loss = pd.Series(losses).rolling(period).mean()
            rs = avg_gain / avg_loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else 50
        except Exception as e:
            return 50.0
    
    def _calculate_macd(self, prices: pd.Series, fast=12, slow=26, signal=9) -> Tuple[float, float, float]:
        try:
            ema_fast = prices.ewm(span=fast).mean()
            ema_slow = prices.ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            return (float(macd_line.iloc[-1]), float(signal_line.iloc[-1]), 
                   float((macd_line - signal_line).iloc[-1]))
        except Exception as e:
            return 0.0, 0.0, 0.0
    
    def _calculate_roc(self, prices: pd.Series, period: int = 14) -> float:
        try:
            if len(prices) < period + 1:
                return 0.0
            current = prices.iloc[-1]
            past = prices.iloc[-(period + 1)]
            if past == 0:
                return 0.0
            return float(((current - past) / abs(past)) * 100)
        except Exception as e:
            return 0.0
    
    def _classify_momentum_level(self, adx: float) -> str:
        if adx > 50: return 'EXTREME'
        elif adx > 35: return 'STRONG'
        elif adx > 20: return 'NORMAL'
        return 'WEAK'
    
    def _detect_divergence(self, df, rsi, macd_hist) -> str:
        try:
            price_trend = df['close'].iloc[-1] > df['close'].iloc[-10]
            rsi_up = rsi > 50
            macd_up = macd_hist > 0
            momentum_up = rsi_up and macd_up
            
            if price_trend and not momentum_up:
                return 'BEARISH'
            elif not price_trend and momentum_up:
                return 'BULLISH'
            return 'NONE'
        except Exception as e:
            return 'NONE'
    
    def _calculate_strength_score(self, adx, rsi, macd_abs, roc_abs) -> int:
        score = 50
        if adx > 40: score += 20
        elif adx > 25: score += 15
        elif adx > 20: score += 10
        if rsi > 70 or rsi < 30: score += 10
        elif rsi > 60 or rsi < 40: score += 5
        if macd_abs > 1.0: score += 10
        elif macd_abs > 0.5: score += 5
        if roc_abs > 3.0: score += 8
        elif roc_abs > 1.5: score += 4
        return min(100, max(20, score))
    
    def _calculate_exhaustion_risk(self, adx, rsi, macd_val, df) -> int:
        risk = 30
        if adx > 50: risk += 20
        elif adx > 40: risk += 10
        if rsi > 80 or rsi < 20: risk += 15
        try:
            if macd_val < 0 and df['close'].iloc[-1] > df['close'].iloc[-10]:
                risk += 10
        except: pass
        return min(100, max(10, risk))
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'adx': 0, 'di_plus': 0, 'di_minus': 0, 'rsi': 50,
            'macd': 0, 'momentum_level': 'NORMAL', 'roc': 0,
            'divergence': 'NONE', 'strength_score': 50,
            'exhaustion_risk': 50, 'confidence': 0,
        }
