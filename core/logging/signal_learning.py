"""
Signal Optimizer (ML Framework)

Optimize signal quality using historical data patterns.
"""

import logging
from typing import List, Dict, Optional
import numpy as np
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SignalRecord:
    """Record of a signal and its outcome."""
    timestamp: datetime
    symbol: str
    direction: str  # CALL or PUT
    entry_confidence: float
    actual_result: str  # WIN or LOSS
    pnl: float


class SignalLearning:
    """
    Optimize signal quality using ML techniques.
    """
    
    def __init__(self, history_size: int = 1000):
        """Initialize optimizer."""
        self.history: List[SignalRecord] = []
        self.history_size = history_size
        self.signal_quality_model = {}
        self.trained = False
    
    def record_signal(self, record: SignalRecord):
        """Add signal to history."""
        self.history.append(record)
        if len(self.history) > self.history_size:
            self.history.pop(0)
    
    def train_model(self) -> Dict:
        """Train ML model on historical signals."""
        if len(self.history) < 50:
            logger.warning(" Not enough data to train (need 50+)")
            return {}
        
        try:
            # Calculate signal quality metrics
            call_signals = [r for r in self.history if r.direction == "CALL"]
            put_signals = [r for r in self.history if r.direction == "PUT"]
            
            call_wr = self._calculate_win_rate(call_signals) if call_signals else 0
            put_wr = self._calculate_win_rate(put_signals) if put_signals else 0
            
            # Confidence thresholds
            optimal_call_threshold = self._find_optimal_threshold(call_signals)
            optimal_put_threshold = self._find_optimal_threshold(put_signals)
            
            self.signal_quality_model = {
                'call_win_rate': call_wr,
                'put_win_rate': put_wr,
                'call_threshold': optimal_call_threshold,
                'put_threshold': optimal_put_threshold,
                'total_signals': len(self.history),
                'overall_win_rate': self._calculate_win_rate(self.history),
                'trained_at': datetime.now().isoformat(),
            }
            
            self.trained = True
            logger.info(f" ML Model trained on {len(self.history)} signals")
            logger.info(f"   Overall WR: {self.signal_quality_model['overall_win_rate']:.1%}")
            
            return self.signal_quality_model
            
        except Exception as e:
            logger.error(f" Model training failed: {e}")
            return {}
    
    def optimize_confidence(self, direction: str, confidence: float) -> float:
        """Adjust confidence based on ML model."""
        if not self.trained:
            return confidence
        
        try:
            if direction == "CALL":
                threshold = self.signal_quality_model.get('call_threshold', 50)
                wr = self.signal_quality_model.get('call_win_rate', 0.5)
            else:
                threshold = self.signal_quality_model.get('put_threshold', 50)
                wr = self.signal_quality_model.get('put_win_rate', 0.5)
            
            # Adjust confidence based on historical performance
            adjustment = (wr - 0.5) * 20  # -20 to +20
            optimized = max(0, min(100, confidence + adjustment))
            
            return optimized
        
        except Exception as e:
            logger.error(f" Confidence optimization failed: {e}")
            return confidence
    
    @staticmethod
    def _calculate_win_rate(signals: List[SignalRecord]) -> float:
        """Calculate win rate from signals."""
        if not signals:
            return 0.5
        
        wins = sum(1 for s in signals if s.actual_result == "WIN")
        return wins / len(signals)
    
    @staticmethod
    def _find_optimal_threshold(signals: List[SignalRecord]) -> float:
        """Find optimal confidence threshold."""
        if not signals or len(signals) < 10:
            return 50
        
        # Find threshold that maximizes Sharpe ratio
        confidences = sorted(set(s.entry_confidence for s in signals))
        best_threshold = 50
        best_wr = 0
        
        for threshold in confidences:
            above = [s for s in signals if s.entry_confidence >= threshold]
            if len(above) >= 5:
                wr = sum(1 for s in above if s.actual_result == "WIN") / len(above)
                if wr > best_wr:
                    best_wr = wr
                    best_threshold = threshold
        
        return best_threshold
