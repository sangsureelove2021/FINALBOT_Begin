"""
TIER 3 - PRICE ACTION HANDLER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyzes raw price action: candle body sizes, wicks, momentum,
breakouts, pullbacks.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

from core.engines.base_engine import BaseEngine


class PriceActionHandler(BaseEngine):
    """Tier 3: Price Action Handler"""
    
    ENGINE_NAME = "price_action_handler"
    ENGINE_VERSION = "1.0.0"
    TIER = 3
    MIN_CANDLES = 30
    
    def _analyze(self, candles_df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        # Recent candle analysis
        recent_body_size = self._average_body_size(candles_df.tail(10))
        wick_dominance = self._wick_to_body_ratio(candles_df.tail(20))
        momentum_strength = self._candle_momentum(candles_df.tail(10))
        
        # Move quality
        move_type = self._classify_move(candles_df)
        
        # Recent direction
        directional_bias = self._recent_directional_bias(candles_df.tail(20))
        
        return {
            'recent_body_size': float(recent_body_size),
            'wick_to_body_ratio': float(wick_dominance),
            'momentum_strength': momentum_strength,
            'move_type': move_type,
            'directional_bias': directional_bias,
            'price_action_quality': self._quality_score(
                recent_body_size, wick_dominance, momentum_strength
            ),
            'confidence': 70,
        }
    
    def _average_body_size(self, df: pd.DataFrame) -> float:
        try:
            bodies = (df['close'] - df['open']).abs()
            avg_price = df['close'].mean()
            if avg_price == 0:
                return 0.0
            return float(bodies.mean() / avg_price * 100)
        except Exception as e:
            return 0.0
    
    def _wick_to_body_ratio(self, df: pd.DataFrame) -> float:
        try:
            bodies = (df['close'] - df['open']).abs()
            ranges = df['high'] - df['low']
            wicks = ranges - bodies
            if bodies.sum() == 0:
                return 0.0
            return float(wicks.sum() / bodies.sum())
        except Exception as e:
            return 0.0
    
    def _candle_momentum(self, df: pd.DataFrame) -> int:
        """How much directional momentum (0-100)"""
        try:
            bullish_count = (df['close'] > df['open']).sum()
            bearish_count = (df['close'] < df['open']).sum()
            total = len(df)
            if total == 0:
                return 0
            
            # If one side dominates
            dominance = max(bullish_count, bearish_count) / total
            return int(dominance * 100)
        except Exception as e:
            return 50
    
    def _classify_move(self, df: pd.DataFrame) -> str:
        try:
            closes = df['close'].tail(20)
            total_move = abs(closes.iloc[-1] - closes.iloc[0])
            path_length = closes.diff().abs().sum()
            
            if path_length == 0:
                return 'STAGNANT'
            
            efficiency = total_move / path_length
            
            if efficiency > 0.7:
                return 'CLEAN_TRENDING'
            elif efficiency > 0.4:
                return 'NORMAL'
            elif efficiency > 0.2:
                return 'NOISY'
            else:
                return 'CHAOTIC'
        except Exception as e:
            return 'NORMAL'
    
    def _recent_directional_bias(self, df: pd.DataFrame) -> str:
        try:
            bullish = (df['close'] > df['open']).sum()
            bearish = (df['close'] < df['open']).sum()
            
            if bullish > bearish * 1.5:
                return 'BULLISH'
            elif bearish > bullish * 1.5:
                return 'BEARISH'
            return 'NEUTRAL'
        except Exception as e:
            return 'NEUTRAL'
    
    def _quality_score(self, body_size: float, wick_ratio: float, 
                      momentum: int) -> int:
        score = 50
        if body_size > 0.1:
            score += 10
        if wick_ratio < 1.0:
            score += 15
        if momentum > 70:
            score += 20
        elif momentum > 60:
            score += 10
        return min(100, score)
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'recent_body_size': 0.0, 'wick_to_body_ratio': 0.0,
            'momentum_strength': 0, 'move_type': 'NORMAL',
            'directional_bias': 'NEUTRAL', 'price_action_quality': 50,
            'confidence': 0,
        }
