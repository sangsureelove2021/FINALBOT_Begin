"""
TIER 4 - DIVERGENCE ANALYZER


Detects divergence between price and momentum indicators (RSI, MACD).
Divergence often precedes reversals.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

from core.orchestration.base_engine import BaseEngine


class DivergenceAnalyzer(BaseEngine):
    """Tier 4: Divergence Analyzer"""
    
    ENGINE_NAME = "divergence_analyzer"
    ENGINE_VERSION = "1.0.0"
    TIER = 4
    MIN_CANDLES = 60
    
    def _analyze(self, candles_df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        rsi = self._calculate_rsi(candles_df['close'])
        macd_hist = self._calculate_macd_hist(candles_df['close'])
        
        rsi_div, rsi_div_type = self._check_divergence(candles_df['close'], rsi)
        macd_div, macd_div_type = self._check_divergence(candles_df['close'], macd_hist)
        
        # Overall divergence
        divergence_detected = rsi_div or macd_div
        
        # Determine type (prioritize agreement)
        div_type = 'NONE'
        if rsi_div_type == macd_div_type and rsi_div_type != 'NONE':
            div_type = rsi_div_type  # Both agree - strong
        elif rsi_div:
            div_type = rsi_div_type
        elif macd_div:
            div_type = macd_div_type
        
        strength = self._divergence_strength(rsi_div, macd_div, rsi_div_type, macd_div_type)
        
        return {
            'divergence_detected': bool(divergence_detected),
            'divergence_type': div_type,
            'rsi_divergence': bool(rsi_div),
            'macd_divergence': bool(macd_div),
            'divergence_strength': strength,
            'both_confirm': bool(rsi_div and macd_div and rsi_div_type == macd_div_type),
            'confidence': 70 if divergence_detected else 60,
        }
    
    def _calculate_rsi(self, prices, period=14) -> pd.Series:
        try:
            deltas = prices.diff()
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = pd.Series(gains, index=prices.index).rolling(period).mean()
            avg_loss = pd.Series(losses, index=prices.index).rolling(period).mean()
            rs = avg_gain / avg_loss.replace(0, np.nan)
            return 100 - (100 / (1 + rs))
        except Exception as e:
            return pd.Series([50] * len(prices), index=prices.index)
    
    def _calculate_macd_hist(self, prices) -> pd.Series:
        try:
            ema_fast = prices.ewm(span=12).mean()
            ema_slow = prices.ewm(span=26).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=9).mean()
            return macd_line - signal_line
        except Exception as e:
            return pd.Series([0] * len(prices), index=prices.index)
    
    def _check_divergence(self, prices, indicator):
        """
        Compare price swings vs indicator swings.
        Bullish div: price lower low, indicator higher low.
        Bearish div: price higher high, indicator lower high.
        """
        try:
            p = prices.tail(40).reset_index(drop=True)
            ind = indicator.tail(40).reset_index(drop=True)
            
            if ind.isna().all():
                return False, 'NONE'
            
            # Find two recent swing points (split into halves)
            mid = len(p) // 2
            
            p_first_low = p[:mid].min()
            p_second_low = p[mid:].min()
            p_first_high = p[:mid].max()
            p_second_high = p[mid:].max()
            
            ind_first_low = ind[:mid].min()
            ind_second_low = ind[mid:].min()
            ind_first_high = ind[:mid].max()
            ind_second_high = ind[mid:].max()
            
            # Bullish divergence
            if p_second_low < p_first_low and ind_second_low > ind_first_low:
                return True, 'BULLISH'
            
            # Bearish divergence
            if p_second_high > p_first_high and ind_second_high < ind_first_high:
                return True, 'BEARISH'
            
            return False, 'NONE'
        except Exception as e:
            return False, 'NONE'
    
    def _divergence_strength(self, rsi_div, macd_div, rsi_type, macd_type) -> int:
        """Score 0-100 for divergence strength"""
        if rsi_div and macd_div and rsi_type == macd_type:
            return 90  # Both confirm
        elif rsi_div and macd_div:
            return 55  # Both detect but conflicting types
        elif rsi_div or macd_div:
            return 50  # Single indicator
        return 0
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'divergence_detected': False, 'divergence_type': 'NONE',
            'rsi_divergence': False, 'macd_divergence': False,
            'divergence_strength': 0, 'both_confirm': False,
            'confidence': 0,
        }
