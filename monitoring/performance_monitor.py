"""
Performance Monitor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Real-time performance tracking during execution.
"""

import logging
from typing import Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""
    timestamp: datetime
    cycle_count: int
    signal_count: int
    trade_count: int
    total_pnl: float
    win_rate: float
    avg_cycle_time: float  # seconds
    signals_per_hour: float


class PerformanceMonitor:
    """Monitor bot performance in real-time."""
    
    def __init__(self):
        """Initialize monitor."""
        self.start_time = datetime.utcnow()
        self.cycle_times: List[float] = []  # Per-cycle times in seconds
        self.cycle_count = 0
        self.signal_count = 0
        self.trade_count = 0
        self.total_pnl = 0.0
        self.wins = 0
        self.losses = 0
        self.last_metric_time = datetime.utcnow()
    
    def record_cycle(self, cycle_time: float, 
                    signals_this_cycle: int = 0) -> None:
        """
        Record cycle execution.
        
        Args:
            cycle_time: Time to execute cycle (seconds)
            signals_this_cycle: Number of signals in this cycle
        """
        self.cycle_count += 1
        self.cycle_times.append(cycle_time)
        self.signal_count += signals_this_cycle
        
        if self.cycle_count % 100 == 0:
            avg_time = sum(self.cycle_times) / len(self.cycle_times)
            logger.debug(f"📈 Cycle {self.cycle_count}: avg time {avg_time:.3f}s/cycle")
    
    def record_trade(self, pnl: float) -> None:
        """
        Record trade result.
        
        Args:
            pnl: Profit/Loss (THB)
        """
        self.trade_count += 1
        self.total_pnl += pnl
        
        if pnl > 0:
            self.wins += 1
        else:
            self.losses += 1
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        elapsed = datetime.utcnow() - self.start_time
        elapsed_hours = elapsed.total_seconds() / 3600
        
        avg_cycle_time = (sum(self.cycle_times) / len(self.cycle_times) 
                         if self.cycle_times else 0.0)
        
        win_rate = (self.wins / self.trade_count * 100 
                   if self.trade_count > 0 else 0.0)
        
        signals_per_hour = (self.signal_count / elapsed_hours 
                           if elapsed_hours > 0 else 0.0)
        
        return PerformanceMetrics(
            timestamp=datetime.utcnow(),
            cycle_count=self.cycle_count,
            signal_count=self.signal_count,
            trade_count=self.trade_count,
            total_pnl=self.total_pnl,
            win_rate=win_rate,
            avg_cycle_time=avg_cycle_time,
            signals_per_hour=signals_per_hour,
        )
    
    def print_stats(self) -> None:
        """Print current statistics."""
        metrics = self.get_metrics()
        elapsed = datetime.utcnow() - self.start_time
        
        logger.info("\n" + "="*80)
        logger.info("📊 PERFORMANCE MONITOR")
        logger.info("="*80)
        logger.info(f"Elapsed: {elapsed}")
        logger.info(f"Cycles: {metrics.cycle_count}")
        logger.info(f"Signals: {metrics.signal_count} ({metrics.signals_per_hour:.1f}/hour)")
        logger.info(f"Trades: {metrics.trade_count} (W: {self.wins}, L: {self.losses})")
        logger.info(f"Win Rate: {metrics.win_rate:.1f}%")
        logger.info(f"Total P&L: {metrics.total_pnl:+.2f} THB")
        logger.info(f"Avg Cycle Time: {metrics.avg_cycle_time:.3f}s")
        logger.info("="*80 + "\n")
    
    def check_health(self) -> Dict[str, bool]:
        """
        Check if bot is running healthily.
        
        Returns:
            Dictionary of health checks
        """
        metrics = self.get_metrics()
        
        health = {
            'performance': metrics.avg_cycle_time < 1.0,  # Cycles < 1 second
            'signals': metrics.signals_per_hour > 0.1,  # At least some signals
            'profitability': metrics.total_pnl >= 0,  # Not negative
            'all_ok': True,
        }
        
        health['all_ok'] = all(v for k, v in health.items() if k != 'all_ok')
        
        return health
