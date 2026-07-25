"""
TIER 5 - ANOMALY DETECTOR


Detects statistical anomalies: unusual candles, gaps, volume spikes.
Anomalies are signals to be cautious.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

from data_evaluate.orchestration.base_engine import BaseEngine


class AnomalyDetector(BaseEngine):
    """Tier 5: Statistical Anomaly Detector"""
    
    ENGINE_NAME = "anomaly_detector"
    ENGINE_VERSION = "1.0.0"
    TIER = 5
    MIN_CANDLES = 50
    
    def get_neutral_state(self) -> dict:
        return {}

    def _analyze(self, candles_df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
        anomalies = []
        
        # Check various anomalies
        range_anomaly = self._detect_range_anomaly(candles_df)
        if range_anomaly:
            anomalies.append('ABNORMAL_RANGE')
        
        gap_anomaly = self._detect_gap(candles_df)
        if gap_anomaly:
            anomalies.append('PRICE_GAP')
        
        volume_anomaly = self._detect_volume_anomaly(candles_df)
        if volume_anomaly:
            anomalies.append('VOLUME_SPIKE')
        
        body_anomaly = self._detect_body_anomaly(candles_df)
        if body_anomaly:
            anomalies.append('ABNORMAL_BODY')
        
        anomaly_detected = len(anomalies) > 0
        anomaly_score = self._calculate_anomaly_score(anomalies)
        
        return {
            'anomaly_detected': bool(anomaly_detected),
            'anomalies': anomalies,
            'anomaly_count': len(anomalies),
            'anomaly_score': anomaly_score,
            'range_anomaly': bool(range_anomaly),
            'gap_anomaly': bool(gap_anomaly),
            'volume_anomaly': bool(volume_anomaly),
            'severity': self._severity(anomaly_score),
            'confidence': 75,
        }
    
    def _detect_range_anomaly(self, df) -> bool:
        """Detect candle with abnormally large range"""
        try:
            ranges = df['high'] - df['low']
            recent_range = ranges.iloc[-1]
            
            mean_range = ranges.tail(50).mean()
            std_range = ranges.tail(50).std()
            
            if std_range == 0:
                return False
            
            zscore = (recent_range - mean_range) / std_range
            return abs(zscore) > 3.0
        except Exception as e:
            raise Exception(str(e))

    
    def _detect_gap(self, df) -> bool:
        """Detect price gap between candles"""
        try:
            recent = df.tail(10)
            
            for i in range(1, len(recent)):
                prev_close = recent['close'].iloc[i-1]
                curr_open = recent['open'].iloc[i]
                
                if prev_close == 0:
                    continue
                
                gap = abs(curr_open - prev_close) / prev_close
                
                # Gap > 0.3% is notable
                if gap > 0.003:
                    return True
            
            return False
        except Exception as e:
            raise Exception(str(e))

    
    def _detect_volume_anomaly(self, df) -> bool:
        """Detect abnormal volume spike"""
        try:
            if 'volume' not in df.columns:
                return False
            
            volumes = df['volume']
            recent_vol = volumes.iloc[-1]
            
            mean_vol = volumes.tail(50).mean()
            std_vol = volumes.tail(50).std()
            
            if std_vol == 0:
                return False
            
            zscore = (recent_vol - mean_vol) / std_vol
            return zscore > 3.0
        except Exception as e:
            raise Exception(str(e))

    
    def _detect_body_anomaly(self, df) -> bool:
        """Detect abnormally large candle body"""
        try:
            bodies = (df['close'] - df['open']).abs()
            recent_body = bodies.iloc[-1]
            
            mean_body = bodies.tail(50).mean()
            std_body = bodies.tail(50).std()
            
            if std_body == 0:
                return False
            
            zscore = (recent_body - mean_body) / std_body
            return zscore > 3.0
        except Exception as e:
            raise Exception(str(e))

    
    def _calculate_anomaly_score(self, anomalies: List[str]) -> int:
        """Score 0-100 for anomaly severity"""
        return min(100, len(anomalies) * 30)
    
    def _severity(self, score: int) -> str:
        if score >= 70:
            return 'HIGH'
        elif score >= 40:
            return 'MEDIUM'
        elif score > 0:
            return 'LOW'
        return 'NONE'
    
