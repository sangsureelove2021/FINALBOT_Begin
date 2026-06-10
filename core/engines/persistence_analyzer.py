"""
TIER 5 - PERSISTENCE ANALYZER


Measures how persistent (sustained) the current move is.
Uses autocorrelation and consecutive-move analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

from core.engines.base_engine import BaseEngine


class PersistenceAnalyzer(BaseEngine):
    """Tier 5: Move Persistence Analyzer"""
    
    ENGINE_NAME = "persistence_analyzer"
    ENGINE_VERSION = "1.0.0"
    TIER = 5
    MIN_CANDLES = 50
    
    def _analyze(self, candles_df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        autocorrelation = self._autocorrelation(candles_df)
        consecutive_run = self._max_consecutive_run(candles_df)
        trend_persistence = self._trend_persistence(candles_df)
        
        persistence_score = self._calculate_persistence(
            autocorrelation, consecutive_run, trend_persistence
        )
        
        expansion_persistence, fatigue_risk = self._calculate_expansion_persistence(candles_df)
        
        return {
            'persistence_score': persistence_score,
            'autocorrelation': float(autocorrelation),
            'max_consecutive_run': consecutive_run,
            'trend_persistence': float(trend_persistence),
            'is_persistent': persistence_score > 60,
            'behavior': self._classify_behavior(autocorrelation),
            'confidence': 70,
            
            # Enhancement 4: Persistence and Fatigue metrics
            'expansion_persistence': expansion_persistence,
            'fatigue_risk': fatigue_risk,
        }
        
    def _calculate_expansion_persistence(self, df: pd.DataFrame) -> Tuple[float, float]:
        """
        Enhancement 4: Expansion Persistence.
        Measures momentum expansion persistence and trend fatigue risk.
        """
        try:
            closes = df['close'].tail(20).values
            
            # Autocorrelation of returns for short-term persistence
            returns = np.diff(closes)
            if len(returns) < 5:
                return 50.0, 0.0
                
            # Autocorrelation lag 1
            r1 = returns[:-1]
            r2 = returns[1:]
            if np.std(r1) == 0 or np.std(r2) == 0:
                corr = 0.0
            else:
                corr = np.corrcoef(r1, r2)[0, 1]
                
            # Calculate momentum slope acceleration
            x = np.arange(len(closes))
            slope = np.polyfit(x, closes, 1)[0]
            
            # Fatigue: If current price deviation from 20 EMA is excessive
            ema = df['close'].ewm(span=20).mean().iloc[-1]
            deviation = abs(closes[-1] - ema) / ema
            
            # Calculate metrics
            expansion_persistence = 50.0 + (corr * 30.0) + (min(1.0, abs(slope) / 0.005) * 20.0)
            expansion_persistence = max(0.0, min(100.0, expansion_persistence))
            
            # Fatigue increases with excessive deviation and negative autocorrelation (whipsaw)
            fatigue_risk = (deviation * 1500.0) + (max(0.0, -corr) * 30.0)
            fatigue_risk = max(0.0, min(100.0, fatigue_risk))
            
            return float(expansion_persistence), float(fatigue_risk)
        except Exception as e:
            return 50.0, 20.0
    
    def _autocorrelation(self, df, lag=1) -> float:
        """Autocorrelation of returns (-1 to 1)"""
        try:
            returns = df['close'].pct_change().dropna().tail(50)
            
            if len(returns) < lag + 2:
                return 0.0
            
            r1 = returns[:-lag].values
            r2 = returns[lag:].values
            
            if np.std(r1) == 0 or np.std(r2) == 0:
                return 0.0
            
            corr = np.corrcoef(r1, r2)[0, 1]
            return float(corr) if not np.isnan(corr) else 0.0
        except Exception as e:
            return 0.0
    
    def _max_consecutive_run(self, df) -> int:
        """Longest run of same-direction candles"""
        try:
            recent = df.tail(30)
            directions = (recent['close'] > recent['open']).astype(int)
            
            max_run = 1
            current_run = 1
            
            for i in range(1, len(directions)):
                if directions.iloc[i] == directions.iloc[i-1]:
                    current_run += 1
                    max_run = max(max_run, current_run)
                else:
                    current_run = 1
            
            return int(max_run)
        except Exception as e:
            return 1
    
    def _trend_persistence(self, df) -> float:
        """How long has trend held (0-100)"""
        try:
            closes = df['close'].tail(40)
            ema = closes.ewm(span=20).mean()
            
            # Count candles on same side of EMA
            above = (closes > ema).astype(int)
            
            # Recent consistency
            recent_consistency = above.tail(20).mean()
            
            # Map to 0-100 (either strongly above or below = persistent)
            persistence = abs(recent_consistency - 0.5) * 200
            return float(min(100, persistence))
        except Exception as e:
            return 50.0
    
    def _calculate_persistence(self, autocorr, run, trend_persist) -> int:
        """Aggregate persistence score 0-100"""
        score = 40
        
        # Positive autocorrelation = trending/persistent
        if autocorr > 0.2:
            score += 25
        elif autocorr > 0:
            score += 12
        elif autocorr < -0.2:
            score -= 15  # Mean-reverting
        
        # Long runs = persistent
        if run >= 5:
            score += 20
        elif run >= 3:
            score += 10
        
        # Trend persistence
        score += (trend_persist / 100) * 15
        
        return int(min(100, max(0, score)))
    
    def _classify_behavior(self, autocorr: float) -> str:
        if autocorr > 0.25:
            return 'TRENDING'
        elif autocorr < -0.25:
            return 'MEAN_REVERTING'
        return 'RANDOM'
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'persistence_score': 40, 'autocorrelation': 0.0,
            'max_consecutive_run': 1, 'trend_persistence': 50.0,
            'is_persistent': False, 'behavior': 'RANDOM',
            'confidence': 0,
        }
