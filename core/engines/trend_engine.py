"""
TIER 1 - TREND ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Detects price direction, trend strength, momentum type, and reversal risk.
Uses: EMA (20/50/100/200), slope calculation, candle momentum.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from core.engines.base_engine import BaseEngine


class TrendEngine(BaseEngine):
    """Tier 1: Trend Intelligence Engine"""
    
    ENGINE_NAME = "trend_engine"
    ENGINE_VERSION = "1.0.0"
    TIER = 1
    MIN_CANDLES = 200
    
    def _analyze(self, candles_df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        """Analyze trend"""
        # Calculate EMAs
        ema_values = self._calculate_emas(candles_df)
        
        # Direction
        direction = self._determine_direction(
            price=candles_df['close'].iloc[-1],
            ema20=ema_values['ema20'].iloc[-1],
            ema50=ema_values['ema50'].iloc[-1],
            ema100=ema_values['ema100'].iloc[-1],
            ema200=ema_values['ema200'].iloc[-1],
        )
        
        # Calculate slope and momentum
        slope = self._calculate_slope(candles_df['close'].tail(20))
        momentum = self._calculate_momentum(candles_df['close'])
        
        # Determine trend type
        trend_type = self._analyze_trend_type(slope, momentum, direction)
        
        # Calculate confidence
        confidence = self._score_confidence(direction, slope, ema_values, momentum, candles_df)
        
        # Reversal risk
        reversal_risk = self._calculate_reversal_risk(
            candles_df, direction, slope, ema_values
        )
        
        # Sustain probability
        sustain_probability = self._calculate_sustain_probability(
            direction, slope, momentum
        )
        
        return {
            'direction': direction,
            'strength': self._slope_to_strength(slope),
            'slope': float(slope),
            'momentum': float(momentum),
            'type': trend_type,
            'confidence': confidence,
            'reversal_risk': reversal_risk,
            'sustain_probability': sustain_probability,
        }
    
    def _calculate_emas(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        return {
            'ema20': df['close'].ewm(span=20, adjust=False).mean(),
            'ema50': df['close'].ewm(span=50, adjust=False).mean(),
            'ema100': df['close'].ewm(span=100, adjust=False).mean(),
            'ema200': df['close'].ewm(span=200, adjust=False).mean(),
        }
    
    def _determine_direction(self, price, ema20, ema50, ema100, ema200) -> str:
        if price > ema20 > ema50 > ema100:
            return 'UP'
        elif price < ema20 < ema50 < ema100:
            return 'DOWN'
        return 'NONE'
    
    def _calculate_slope(self, prices: pd.Series) -> float:
        try:
            x = np.arange(len(prices))
            y = prices.values
            return float(np.polyfit(x, y, 1)[0])
        except:
            return 0.0
    
    def _calculate_momentum(self, prices: pd.Series, period: int = 14) -> float:
        if len(prices) < period + 1:
            return 0.0
        current = prices.iloc[-1]
        past = prices.iloc[-(period + 1)]
        if past == 0:
            return 0.0
        return float(((current - past) / abs(past)) * 100)
    
    def _analyze_trend_type(self, slope, momentum, direction) -> str:
        if direction == 'NONE':
            return 'CHOPPY'
        abs_slope = abs(slope)
        abs_momentum = abs(momentum)
        if abs_slope > 0.0005 and abs_momentum > 1.0:
            return 'IMPULSIVE'
        elif (0.0001 <= abs_slope <= 0.0005) and (0.2 <= abs_momentum <= 1.5):
            return 'CORRECTIVE'
        return 'CHOPPY'
    
    def _score_confidence(self, direction, slope, ema_values, momentum, df) -> int:
        if direction == 'NONE':
            return 20
        score = 50
        abs_slope = abs(slope)
        if abs_slope > 0.001:
            score += 20
        elif abs_slope > 0.0005:
            score += 10
        abs_momentum = abs(momentum)
        if abs_momentum > 2.0:
            score += 15
        elif abs_momentum > 1.0:
            score += 10
        latest_price = df['close'].iloc[-1]
        ema20 = ema_values['ema20'].iloc[-1]
        if ema20 != 0:
            distance = abs(latest_price - ema20) / abs(latest_price)
            if distance < 0.01:
                score += 5
        return min(100, max(20, score))
    
    def _calculate_reversal_risk(self, df, direction, slope, ema_values) -> int:
        if direction == 'NONE':
            return 50
        risk = 30
        try:
            recent_slope = self._calculate_slope(df['close'].tail(10))
            older_slope = self._calculate_slope(df['close'].iloc[-50:-30])
            if abs(recent_slope) < abs(older_slope) * 0.5:
                risk += 20
            latest_price = df['close'].iloc[-1]
            ema20 = ema_values['ema20'].iloc[-1]
            if ema20 != 0:
                distance = abs(latest_price - ema20) / abs(ema20)
                if distance > 0.02:
                    risk += 15
        except:
            pass
        return min(100, max(10, risk))
    
    def _calculate_sustain_probability(self, direction, slope, momentum) -> int:
        if direction == 'NONE':
            return 30
        prob = 50
        abs_slope = abs(slope)
        if abs_slope > 0.001:
            prob += 25
        elif abs_slope > 0.0005:
            prob += 15
        abs_momentum = abs(momentum)
        if abs_momentum > 2.0:
            prob += 20
        elif abs_momentum > 1.0:
            prob += 10
        return min(100, max(20, prob))
    
    def _slope_to_strength(self, slope) -> int:
        abs_slope = abs(slope)
        if abs_slope > 0.002:
            return 100
        elif abs_slope > 0.001:
            return 80
        elif abs_slope > 0.0005:
            return 60
        elif abs_slope > 0.0001:
            return 40
        return 20
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'direction': 'NONE', 'strength': 0, 'slope': 0.0,
            'momentum': 0.0, 'type': 'CHOPPY', 'confidence': 0,
            'reversal_risk': 50, 'sustain_probability': 50,
        }
