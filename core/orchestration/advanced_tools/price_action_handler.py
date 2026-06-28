"""
TIER 3 - PRICE ACTION HANDLER


Analyzes raw price action: candle body sizes, wicks, momentum,
breakouts, pullbacks.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

from core.orchestration.base_engine import BaseEngine


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
        
        # Fractal S/R
        fractal_sr = self._fractal_support_resistance(candles_df)
        
        # Relative Volume Momentum
        vol_momentum = self._relative_volume_momentum(candles_df)
        
        return {
            'recent_body_size': float(recent_body_size),
            'wick_to_body_ratio': float(wick_dominance),
            'momentum_strength': momentum_strength,
            'move_type': move_type,
            'directional_bias': directional_bias,
            'fractal_support': fractal_sr['support'],
            'fractal_resistance': fractal_sr['resistance'],
            'volume_momentum': vol_momentum,
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
            import logging
            logging.getLogger(__name__).exception(f"Error: {e}")
            raise Exception(str(e))
    
    def _wick_to_body_ratio(self, df: pd.DataFrame) -> float:
        try:
            bodies = (df['close'] - df['open']).abs()
            ranges = df['high'] - df['low']
            wicks = ranges - bodies
            sum_bodies = bodies.sum()
            if sum_bodies == 0:
                avg_price = df['close'].mean()
                return float((wicks.sum() / avg_price * 100) if avg_price > 0 else 0.0)
            return float(wicks.sum() / sum_bodies)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception(f"Error: {e}")
            raise Exception(str(e))
    
    def _candle_momentum(self, df: pd.DataFrame) -> int:
        """How much directional momentum (0-100)"""
        try:
            bull_ranges = df.loc[df['close'] > df['open']].apply(lambda r: r['close'] - r['open'], axis=1).sum()
            bear_ranges = df.loc[df['close'] < df['open']].apply(lambda r: r['open'] - r['close'], axis=1).sum()
            total_range = bull_ranges + bear_ranges
            if total_range == 0:
                return 0
            
            dominance = max(bull_ranges, bear_ranges) / total_range
            return int(dominance * 100)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception(f"Error: {e}")
            raise Exception(str(e))
    
    def _classify_move(self, df: pd.DataFrame) -> str:
        try:
            closes = df['close'].tail(20)
            highs = df['high'].tail(20)
            lows = df['low'].tail(20)
            
            total_move = abs(closes.iloc[-1] - closes.iloc[0])
            
            tr1 = highs - lows
            tr2 = (highs - closes.shift()).abs()
            tr3 = (lows - closes.shift()).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            path_length = tr.sum()
            
            if path_length == 0:
                return 'STAGNANT'
            
            efficiency = total_move / path_length
            
            if efficiency > 0.6:
                return 'CLEAN_TRENDING'
            elif efficiency > 0.3:
                return 'NORMAL'
            elif efficiency > 0.15:
                return 'NOISY'
            else:
                return 'CHAOTIC'
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception(f"Error: {e}")
            raise Exception(str(e))
    
    def _recent_directional_bias(self, df: pd.DataFrame) -> str:
        try:
            bull_range = df.loc[df['close'] > df['open']].apply(lambda r: r['close'] - r['open'], axis=1).sum()
            bear_range = df.loc[df['close'] < df['open']].apply(lambda r: r['open'] - r['close'], axis=1).sum()
            
            if bull_range > bear_range * 1.5:
                return 'BULLISH'
            elif bear_range > bull_range * 1.5:
                return 'BEARISH'
            return 'NEUTRAL'
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception(f"Error: {e}")
            raise Exception(str(e))
            
    def _fractal_support_resistance(self, df: pd.DataFrame) -> Dict[str, float]:
        """Finds Proper Fractal Highs and Lows (2 lower highs before/after)"""
        try:
            if len(df) < 5:
                return {'support': float(df['low'].min()), 'resistance': float(df['high'].max())}
                
            highs = df['high'].values
            lows = df['low'].values
            
            resistances = []
            supports = []
            
            for i in range(2, len(df) - 2):
                if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                    resistances.append(highs[i])
                if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                    supports.append(lows[i])
                    
            return {
                'support': float(supports[-1]) if supports else float(df['low'].min()),
                'resistance': float(resistances[-1]) if resistances else float(df['high'].max())
            }
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception(f"Error: {e}")
            raise Exception(str(e))
            
    def _relative_volume_momentum(self, df: pd.DataFrame) -> str:
        """Compares current volume to a rolling median/percentile instead of a static slope"""
        try:
            if 'volume' not in df.columns or len(df) < 20:
                return 'NEUTRAL'
                
            rolling_median_vol = df['volume'].rolling(window=20).median()
            current_vol = df['volume'].iloc[-1]
            median_vol = rolling_median_vol.iloc[-1]
            
            if pd.isna(median_vol) or median_vol == 0:
                return 'NEUTRAL'
                
            vol_ratio = current_vol / median_vol
            
            if vol_ratio >= 1.5:
                return 'HIGH_MOMENTUM'
            elif vol_ratio <= 0.5:
                return 'LOW_MOMENTUM'
            else:
                return 'NORMAL'
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception(f"Error: {e}")
            raise Exception(str(e))
    
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
    
