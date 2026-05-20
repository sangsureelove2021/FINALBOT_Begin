"""
TIER 5 - CONTINUATION ANALYZER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Estimates probability that the current move will continue vs reverse.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

from core.engines.base_engine import BaseEngine


class ContinuationAnalyzer(BaseEngine):
    """Tier 5: Move Continuation Analyzer"""
    
    ENGINE_NAME = "continuation_analyzer"
    ENGINE_VERSION = "1.0.0"
    TIER = 5
    MIN_CANDLES = 50
    
    def _analyze(self, candles_df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        pullback_health = self._assess_pullback(candles_df)
        momentum_intact = self._momentum_intact(candles_df)
        volume_support = self._volume_support(candles_df)
        
        continuation_prob = self._calculate_continuation_probability(
            pullback_health, momentum_intact, volume_support, candles_df
        )
        reversal_prob = 100 - continuation_prob
        
        return {
            'continuation_probability': continuation_prob,
            'reversal_probability': reversal_prob,
            'pullback_health': pullback_health,
            'momentum_intact': bool(momentum_intact),
            'volume_supports_move': bool(volume_support),
            'bias': 'CONTINUATION' if continuation_prob > 55 else (
                    'REVERSAL' if continuation_prob < 45 else 'NEUTRAL'),
            'confidence': 70,
        }
    
    def _assess_pullback(self, df) -> int:
        """Assess if recent pullback is healthy (0-100)"""
        try:
            closes = df['close'].tail(30)
            ema = closes.ewm(span=20).mean()
            
            # Distance from EMA
            last_close = closes.iloc[-1]
            last_ema = ema.iloc[-1]
            
            if last_ema == 0:
                return 50
            
            distance = abs(last_close - last_ema) / last_ema
            
            # Healthy pullback: close to EMA (not overextended)
            if distance < 0.005:
                return 80  # Near EMA = healthy
            elif distance < 0.015:
                return 60
            elif distance < 0.03:
                return 40
            else:
                return 20  # Overextended
        except:
            return 50
    
    def _momentum_intact(self, df) -> bool:
        """Is momentum still supporting the move?"""
        try:
            closes = df['close']
            
            # Recent vs older momentum
            recent_roc = (closes.iloc[-1] - closes.iloc[-7]) / closes.iloc[-7] * 100
            older_roc = (closes.iloc[-7] - closes.iloc[-14]) / closes.iloc[-14] * 100
            
            # Momentum intact if same direction
            return np.sign(recent_roc) == np.sign(older_roc) and abs(recent_roc) > 0.1
        except:
            return False
    
    def _volume_support(self, df) -> bool:
        """Does volume support the move?"""
        try:
            if 'volume' not in df.columns:
                return True  # Assume support if no volume data
            
            recent_vol = df['volume'].tail(10).mean()
            past_vol = df['volume'].tail(30).mean()
            
            # Volume supports if recent >= past
            return recent_vol >= past_vol * 0.8
        except:
            return True
    
    def _calculate_continuation_probability(self, pullback, momentum, 
                                           volume, df) -> int:
        """Continuation probability 0-100"""
        prob = 50
        
        # Pullback health
        prob += (pullback - 50) * 0.3
        
        # Momentum
        if momentum:
            prob += 15
        else:
            prob -= 12
        
        # Volume
        if volume:
            prob += 8
        else:
            prob -= 8
        
        # Trend strength check
        try:
            closes = df['close'].tail(20)
            slope = np.polyfit(np.arange(len(closes)), closes.values, 1)[0]
            if abs(slope) > 0.0005:
                prob += 10
        except:
            pass
        
        return int(min(95, max(5, prob)))
    
    def get_neutral_state(self) -> Dict[str, Any]:
        return {
            'continuation_probability': 50, 'reversal_probability': 50,
            'pullback_health': 50, 'momentum_intact': False,
            'volume_supports_move': False, 'bias': 'NEUTRAL',
            'confidence': 0,
        }
