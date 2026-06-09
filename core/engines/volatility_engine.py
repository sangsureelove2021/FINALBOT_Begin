"""
TIER 1 - VOLATILITY ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Measure market volatility using ATR, Bollinger Bands, and historical percentile.
Classify volatility regime and detect compression/expansion.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

from core.engines.base_engine import BaseEngine


class VolatilityEngine(BaseEngine):
    """Tier 1: Volatility Engine"""
    
    ENGINE_NAME = "volatility_engine"
    ENGINE_VERSION = "1.0.0"
    TIER = 1
    MIN_CANDLES = 200
    
    def _analyze(self, candles_df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        atr_val = self._calculate_atr(candles_df)
        atr_historical = self._calculate_atr_historical(candles_df)
        atr_percentile = self._calculate_percentile(atr_val, atr_historical)
        
        bbw, stddev = self._calculate_bollinger_bands(candles_df['close'])
        regime = self._classify_regime(atr_percentile)
        volatility_score = self._calculate_volatility_score(
            atr_percentile, bbw, stddev, candles_df
        )
        
        expansion_prob, contraction_prob = self._detect_expansion_contraction(
            atr_historical, atr_val
        )
        
        zscore = self._calculate_zscore(atr_val, atr_historical)
        spike_detected = abs(zscore) > 2.0
        
        bbw_ratio, compression_quality = self._calculate_compression_quality(atr_percentile, bbw, candles_df)
        
        return {
            'atr': float(atr_val),
            'atr_percentile': float(atr_percentile),
            'bbw': float(bbw),
            'stddev': float(stddev),
            'regime': regime,
            'volatility_score': volatility_score,
            'expansion_probability': expansion_prob,
            'contraction_probability': contraction_prob,
            'volatility_zscore': float(zscore),
            'spike_detected': bool(spike_detected),
            'confidence': self._calculate_confidence(atr_val, regime),
            
            # Enhancement 2: Compression metrics
            'bbw_compression_ratio': bbw_ratio,
            'compression_quality': compression_quality,
        }
        
    def _calculate_compression_quality(self, atr_pct: float, bbw: float, df: pd.DataFrame) -> Tuple[float, float]:
        """Calculate Bollinger Bands squeeze ratio and Compression Squeeze Quality score"""
        try:
            closes = df['close']
            sma = closes.rolling(20).mean()
            std = closes.rolling(20).std()
            bbw_series = (sma + 2*std) - (sma - 2*std)
            
            current_bbw = bbw_series.iloc[-1]
            historical_bbw_sma = bbw_series.rolling(100).mean().iloc[-1]
            
            if historical_bbw_sma == 0 or np.isnan(historical_bbw_sma):
                bbw_compression_ratio = 1.0
            else:
                bbw_compression_ratio = float(current_bbw / historical_bbw_sma)
                
            # Compute quality 0-100: lower ratio & lower atr_pct = higher quality squeeze
            quality = 100.0
            if bbw_compression_ratio > 0.8:
                quality -= (bbw_compression_ratio - 0.8) * 100
            quality -= max(0.0, (atr_pct - 20.0) * 0.8)
            
            compression_quality = float(max(0.0, min(100.0, quality)))
            return bbw_compression_ratio, compression_quality
        except Exception as e:
            return 1.0, 50.0
    
    def _calculate_atr(self, df, period=14) -> float:
        try:
            high, low, close = df['high'], df['low'], df['close']
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = np.maximum(tr1, np.maximum(tr2, tr3))
            atr = tr.rolling(period).mean()
            return float(atr.iloc[-1]) if not np.isnan(atr.iloc[-1]) else 0.0
        except Exception as e:
            return 0.0
    
    def _calculate_atr_historical(self, df, period=14):
        try:
            high = df['high'].tail(120)
            low = df['low'].tail(120)
            close = df['close'].tail(120)
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = np.maximum(tr1, np.maximum(tr2, tr3))
            atr_values = tr.rolling(period).mean().dropna().values
            return atr_values[-100:] if len(atr_values) > 0 else np.array([0.0])
        except Exception as e:
            return np.array([0.0])
    
    def _calculate_percentile(self, current_atr, historical_atr) -> float:
        try:
            if len(historical_atr) == 0 or current_atr == 0:
                return 50.0
            return float((np.sum(historical_atr <= current_atr) / len(historical_atr)) * 100)
        except Exception as e:
            return 50.0
    
    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2) -> Tuple[float, float]:
        try:
            sma = prices.rolling(period).mean()
            std = prices.rolling(period).std()
            upper = sma + (std_dev * std)
            lower = sma - (std_dev * std)
            bbw = upper - lower
            return (float(bbw.iloc[-1]) if not np.isnan(bbw.iloc[-1]) else 0.0,
                    float(std.iloc[-1]) if not np.isnan(std.iloc[-1]) else 0.0)
        except Exception as e:
            return 0.0, 0.0
    
    def _classify_regime(self, atr_percentile) -> str:
        if atr_percentile > 75: return 'EXTREME'
        elif atr_percentile > 50: return 'HIGH'
        elif atr_percentile > 25: return 'NORMAL'
        return 'LOW'
    
    def _calculate_volatility_score(self, atr_percentile, bbw, stddev, df) -> int:
        score = 50
        if atr_percentile > 75: score += 30
        elif atr_percentile > 50: score += 15
        if bbw > stddev * 4: score += 15
        elif bbw > stddev * 2: score += 8
        try:
            recent_range = (df['high'].tail(10).max() - df['low'].tail(10).min()) / df['close'].iloc[-1]
            if recent_range > 0.02: score += 10
            elif recent_range > 0.01: score += 5
        except: pass
        return min(100, max(20, score))
    
    def _detect_expansion_contraction(self, historical, current_atr) -> Tuple[int, int]:
        try:
            if len(historical) < 20:
                return 50, 50
            recent = historical[-10:]
            past = historical[-20:-10]
            recent_avg = np.mean(recent)
            past_avg = np.mean(past)
            
            if recent_avg < past_avg:
                ratio = recent_avg / (past_avg + 0.00001)
                if ratio < 0.8:
                    return 70, 30
                return 55, 45
            return 40, 60
        except Exception as e:
            return 50, 50
    
    def _calculate_zscore(self, current_atr, historical_atr) -> float:
        try:
            if len(historical_atr) < 2 or current_atr == 0:
                return 0.0
            mean = np.mean(historical_atr)
            std = np.std(historical_atr)
            if std == 0:
                return 0.0
            return float((current_atr - mean) / std)
        except Exception as e:
            return 0.0
    
    def _calculate_confidence(self, atr_val, regime) -> int:
        if regime == 'EXTREME': return 40  # Less reliable in extremes
        elif regime == 'LOW': return 65
        return 80  # Normal/High volatility = good info
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'atr': 0.0, 'atr_percentile': 50.0, 'bbw': 0.0, 'stddev': 0.0,
            'regime': 'NORMAL', 'volatility_score': 50,
            'expansion_probability': 50, 'contraction_probability': 50,
            'volatility_zscore': 0.0, 'spike_detected': False,
            'confidence': 0,
        }
