"""
TIER 2 - REGIME QUALITY SCORER


Scores how favorable the current regime is for trading.
"""

import pandas as pd
from typing import Dict, Any

from core.orchestration.base_engine import BaseEngine


class RegimeQualityScorer(BaseEngine):
    """Tier 2: Regime Quality Scorer"""
    
    ENGINE_NAME = "regime_quality_scorer"
    ENGINE_VERSION = "1.0.0"
    TIER = 2
    MIN_CANDLES = 100
    
    def _analyze(self, candles_df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        # Calculate regime metrics
        consistency = self._calculate_consistency(candles_df)
        cleanliness = self._calculate_cleanliness(candles_df)
        directionality = self._calculate_directionality(candles_df)
        
        overall_quality = int((consistency + cleanliness + directionality) / 3)
        
        return {
            'consistency_score': consistency,
            'cleanliness_score': cleanliness,
            'directionality_score': directionality,
            'overall_quality': overall_quality,
            'is_tradeable_regime': overall_quality >= 60,
            'confidence': min(100, overall_quality + 10),
        }
    
    def _calculate_consistency(self, df: pd.DataFrame) -> int:
        """How consistent are recent moves?"""
        try:
            returns = df['close'].pct_change().tail(50)
            if returns.std() == 0:
                return 50
            
            # Lower std = more consistent
            std = returns.std()
            mean = abs(returns.mean())
            
            # Sharpe-like metric
            if std > 0:
                ratio = mean / std
                return min(100, int(50 + ratio * 100))
            return 50
        except Exception as e:
            return 50
    
    def _calculate_cleanliness(self, df: pd.DataFrame) -> int:
        """How clean (vs noisy) is the price action?"""
        try:
            highs = df['high'].tail(30)
            lows = df['low'].tail(30)
            closes = df['close'].tail(30)
            
            # Calculate average wick size relative to body
            wicks = (highs - lows) - abs(closes - closes.shift(1).fillna(closes.iloc[0]))
            wick_ratio = wicks.mean() / (highs.mean() - lows.mean() + 0.00001)
            
            # Lower wicks = cleaner
            cleanliness = max(20, min(100, 100 - wick_ratio * 100))
            return int(cleanliness)
        except Exception as e:
            return 50
    
    def _calculate_directionality(self, df: pd.DataFrame) -> int:
        """How directional are moves?"""
        try:
            closes = df['close'].tail(30)
            total_move = abs(closes.iloc[-1] - closes.iloc[0])
            path_length = closes.diff().abs().sum()
            
            if path_length == 0:
                return 50
            
            efficiency = (total_move / path_length) * 100
            return int(min(100, efficiency))
        except Exception as e:
            return 50
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'consistency_score': 50, 'cleanliness_score': 50,
            'directionality_score': 50, 'overall_quality': 50,
            'is_tradeable_regime': False, 'confidence': 0,
        }
