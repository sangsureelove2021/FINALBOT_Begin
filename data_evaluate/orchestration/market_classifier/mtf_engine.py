"""
TIER 1 - MTF (Multi-Timeframe) ENGINE


Analyzes multiple timeframes to detect alignment or conflict.
Critical for binary options to confirm setup across timeframes.
"""

import pandas as pd
from typing import Dict, Any

from data_evaluate.orchestration.base_engine import BaseEngine


class MTFEngine(BaseEngine):
    """Tier 1: Multi-Timeframe Engine"""
    
    ENGINE_NAME = "mtf_engine"
    ENGINE_VERSION = "1.0.0"
    TIER = 1
    MIN_CANDLES = 50
    
    def analyze(self, payload: Dict[str, Any], candles_dict: Dict[str, pd.DataFrame] = None, **kwargs) -> Dict[str, Any]:
        """MTF analyzes across timeframes"""
        try:
            if not candles_dict:
                raise ValueError("FAIL-FAST: Neutral state removed")
            
            directions = {}
            for tf, df in candles_dict.items():
                if df is None or len(df) < 50:
                    continue
                directions[tf] = self._tf_direction(df)
            
            if not directions:
                raise ValueError("FAIL-FAST: Neutral state removed")
            
            # Calculate alignment
            up_count = sum(1 for d in directions.values() if d == 'UP')
            down_count = sum(1 for d in directions.values() if d == 'DOWN')
            total = len(directions)
            
            # Alignment score
            max_count = max(up_count, down_count)
            alignment_score = int((max_count / total) * 100) if total > 0 else 50
            
            # Dominant direction
            if up_count > down_count:
                dominant = 'UP'
            elif down_count > up_count:
                dominant = 'DOWN'
            else:
                dominant = 'NONE'
            
            # HTF direction (highest available timeframe)
            tf_order = ['D1', 'H4', 'H1', 'M60', 'M30', 'M15', 'M5', 'M1']
            htf_direction = 'NONE'
            for tf in tf_order:
                if tf in directions:
                    htf_direction = directions[tf]
                    break
            
            # LTF direction (lowest available)
            ltf_direction = 'NONE'
            for tf in reversed(tf_order):
                if tf in directions:
                    ltf_direction = directions[tf]
                    break
            
            # Conflict detection
            htf_ltf_conflict = (
                htf_direction != 'NONE' and 
                ltf_direction != 'NONE' and
                htf_direction != ltf_direction
            )
            
            return {
                'directions_by_tf': directions,
                'alignment_score': alignment_score,
                'dominant_direction': dominant,
                'htf_direction': htf_direction,
                'ltf_direction': ltf_direction,
                'htf_ltf_conflict': htf_ltf_conflict,
                'timeframes_analyzed': list(directions.keys()),
                'confidence_from_mtf': alignment_score,
                'confidence': alignment_score,
            }
        except Exception as e:
            raise
#             print(f" MTF Engine error: {e}")
    
    def _tf_direction(self, df: pd.DataFrame) -> str:
        """Quick direction check for single timeframe"""
        try:
            ema20 = df['close'].ewm(span=20).mean().iloc[-1]
            ema50 = df['close'].ewm(span=50).mean().iloc[-1]
            close = df['close'].iloc[-1]
            
            if close > ema20 > ema50:
                return 'UP'
            elif close < ema20 < ema50:
                return 'DOWN'
            return 'NONE'
        except Exception as e:
            raise
    
