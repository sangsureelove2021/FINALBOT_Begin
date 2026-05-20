"""
TIER 8 - PERFORMANCE TRACKER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tracks signal history and performance statistics over time.
Stateful - accumulates data across multiple analyses.
"""

from typing import Dict, Any, List
from datetime import datetime
from collections import deque


class PerformanceTracker:
    """Tier 8: Performance Tracker (stateful, not an engine)"""
    
    ENGINE_NAME = "performance_tracker"
    ENGINE_VERSION = "1.0.0"
    TIER = 8
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._signals: deque = deque(maxlen=max_history)
        self._outcomes: deque = deque(maxlen=max_history)
    
    def record_signal(self, signal_data: Dict[str, Any]) -> None:
        """Record a generated signal"""
        self._signals.append({
            'timestamp': datetime.utcnow().isoformat(),
            'action': signal_data.get('action', 'UNKNOWN'),
            'confidence': signal_data.get('confidence', 0),
            'quality': signal_data.get('quality', 'UNKNOWN'),
            'symbol': signal_data.get('symbol', ''),
            'strategy': signal_data.get('strategy_name', ''),
        })
    
    def record_outcome(self, signal_id: str, won: bool, 
                      profit: float = 0.0) -> None:
        """Record the outcome of a signal (win/loss)"""
        self._outcomes.append({
            'signal_id': signal_id,
            'won': won,
            'profit': profit,
            'timestamp': datetime.utcnow().isoformat(),
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """Compute performance statistics"""
        total_signals = len(self._signals)
        total_outcomes = len(self._outcomes)
        
        # Signal breakdown
        actions = {}
        for sig in self._signals:
            a = sig['action']
            actions[a] = actions.get(a, 0) + 1
        
        # Win rate
        wins = sum(1 for o in self._outcomes if o['won'])
        win_rate = (wins / total_outcomes * 100) if total_outcomes > 0 else 0.0
        
        # Profit
        total_profit = sum(o['profit'] for o in self._outcomes)
        
        # Average confidence
        avg_confidence = (
            sum(s['confidence'] for s in self._signals) / total_signals
            if total_signals > 0 else 0.0
        )
        
        return {
            'total_signals': total_signals,
            'total_outcomes': total_outcomes,
            'action_breakdown': actions,
            'wins': wins,
            'losses': total_outcomes - wins,
            'win_rate': round(win_rate, 2),
            'total_profit': round(total_profit, 2),
            'average_confidence': round(avg_confidence, 2),
        }
    
    def get_recent_signals(self, n: int = 10) -> List[Dict]:
        """Get the n most recent signals"""
        return list(self._signals)[-n:]
    
    def win_rate_by_confidence(self) -> Dict[str, float]:
        """Win rate bucketed by confidence level"""
        buckets = {'75-80': [], '80-85': [], '85-90': [], '90-100': []}
        
        # Match outcomes to signals would need signal_id linkage
        # Simplified: return structure for future use
        return {k: 0.0 for k in buckets}
    
    def reset(self) -> None:
        """Clear all history"""
        self._signals.clear()
        self._outcomes.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Export current state"""
        return {
            'statistics': self.get_statistics(),
            'recent_signals': self.get_recent_signals(5),
        }
