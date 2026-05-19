"""
TIER 1 - STRUCTURE ENGINE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Detects support/resistance levels, BOS (Break of Structure), and key zones.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

from core.engines.base_engine import BaseEngine


class StructureEngine(BaseEngine):
    """Tier 1: Structure Engine"""
    
    ENGINE_NAME = "structure_engine"
    ENGINE_VERSION = "1.0.0"
    TIER = 1
    MIN_CANDLES = 100
    
    def _analyze(self, candles_df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        support_levels = self._find_support_levels(candles_df)
        resistance_levels = self._find_resistance_levels(candles_df)
        struct_type = self._determine_structure_type(candles_df)
        bos_detected, bos_type = self._detect_bos(candles_df, support_levels, resistance_levels)
        key_zones = self._find_key_zones(support_levels, resistance_levels, candles_df)
        proximity = self._check_proximity(
            candles_df['close'].iloc[-1], support_levels, resistance_levels
        )
        struct_score = self._score_structure(support_levels, resistance_levels)
        
        return {
            'support_levels': support_levels,
            'resistance_levels': resistance_levels,
            'structure_type': struct_type,
            'structure_score': struct_score,
            'bos_detected': bool(bos_detected),
            'bos_type': bos_type,
            'key_zones': key_zones,
            'zone_proximity': proximity,
            'breakout_probability': 60 if bos_detected else 30,
            'reversal_probability': 40 if bos_detected else 50,
            'confidence': min(85, struct_score + 10),
        }
    
    def _find_support_levels(self, df, lookback=50) -> List[float]:
        try:
            lows = df['low'].tail(lookback).values
            support = []
            for i in range(1, len(lows) - 1):
                if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
                    support.append(float(lows[i]))
            return sorted(list(set([round(s, 5) for s in support])))[:3]
        except:
            return []
    
    def _find_resistance_levels(self, df, lookback=50) -> List[float]:
        try:
            highs = df['high'].tail(lookback).values
            resistance = []
            for i in range(1, len(highs) - 1):
                if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
                    resistance.append(float(highs[i]))
            return sorted(list(set([round(r, 5) for r in resistance])))[:3]
        except:
            return []
    
    def _determine_structure_type(self, df) -> str:
        try:
            recent_range = (df['high'].tail(20).max() - df['low'].tail(20).min()) / df['close'].iloc[-1]
            if recent_range > 0.02: return 'BREAKOUT'
            elif recent_range > 0.015: return 'TRENDING'
            return 'RANGING'
        except:
            return 'RANGING'
    
    def _detect_bos(self, df, supports, resistances) -> Tuple[bool, str]:
        try:
            price = df['close'].iloc[-1]
            prev_price = df['close'].iloc[-2]
            for level in supports:
                if prev_price > level and price < level:
                    return True, 'BEARISH'
            for level in resistances:
                if prev_price < level and price > level:
                    return True, 'BULLISH'
            return False, 'NONE'
        except:
            return False, 'NONE'
    
    def _find_key_zones(self, supports, resistances, df) -> Dict[str, float]:
        try:
            return {
                'strong_support': float(supports[0]) if supports else float(df['low'].min()),
                'strong_resistance': float(resistances[0]) if resistances else float(df['high'].max()),
                'middle': float((supports[0] + resistances[0]) / 2) if supports and resistances else float(df['close'].mean()),
            }
        except:
            return {'strong_support': 0, 'strong_resistance': 0, 'middle': 0}
    
    def _check_proximity(self, price, supports, resistances) -> str:
        all_levels = supports + resistances
        if not all_levels:
            return 'FAR'
        try:
            closest = min(all_levels, key=lambda x: abs(x - price))
            distance = abs(price - closest) / abs(price) if price != 0 else 999
            if distance < 0.001: return 'AT_LEVEL'
            elif distance < 0.005: return 'NEAR'
            elif distance < 0.015: return 'MEDIUM'
            return 'FAR'
        except:
            return 'FAR'
    
    def _score_structure(self, supports, resistances) -> int:
        score = 50
        if len(supports) > 1: score += 15
        if len(resistances) > 1: score += 15
        if len(supports) > 0 and len(resistances) > 0: score += 10
        return min(100, score)
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'support_levels': [], 'resistance_levels': [],
            'structure_type': 'RANGING', 'structure_score': 30,
            'bos_detected': False, 'bos_type': 'NONE',
            'key_zones': {'strong_support': 0, 'strong_resistance': 0, 'middle': 0},
            'zone_proximity': 'FAR', 'breakout_probability': 30,
            'reversal_probability': 50, 'confidence': 0,
        }
