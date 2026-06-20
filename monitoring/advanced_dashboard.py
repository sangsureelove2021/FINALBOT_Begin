"""
Advanced Analytics Dashboard

Compare strategies, analyze correlation, ML metrics.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class StrategyStats:
    """Statistics for a single strategy."""
    name: str
    version: str
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0
    trades_by_symbol: Dict[str, int] = field(default_factory=dict)
    pnl_by_symbol: Dict[str, float] = field(default_factory=dict)
    
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0
        return self.wins / self.total_trades
    
    @property
    def pnl_per_trade(self) -> float:
        if self.total_trades == 0:
            return 0
        return self.total_pnl / self.total_trades


class AdvancedDashboard:
    """
    Compare multiple strategies and analyze performance.
    """
    
    def __init__(self):
        """Initialize dashboard."""
        self.strategies: Dict[str, StrategyStats] = {}
        self.correlation_data: Dict[str, List[float]] = {}
        self.ml_metrics: Dict[str, float] = {}
    
    def register_strategy(self, name: str, version: str):
        """Register strategy for tracking."""
        key = f"{name}_v{version}"
        self.strategies[key] = StrategyStats(name=name, version=version)
        logger.info(f" Strategy registered: {key}")
    
    def record_trade(self, strategy_key: str, symbol: str, result: str, pnl: float):
        """Record trade result."""
        if strategy_key not in self.strategies:
            return
        
        stats = self.strategies[strategy_key]
        stats.total_trades += 1
        
        if result == "WIN":
            stats.wins += 1
        else:
            stats.losses += 1
        
        stats.total_pnl += pnl
        
        # Track by symbol
        if symbol not in stats.trades_by_symbol:
            stats.trades_by_symbol[symbol] = 0
            stats.pnl_by_symbol[symbol] = 0
        
        stats.trades_by_symbol[symbol] += 1
        stats.pnl_by_symbol[symbol] += pnl
    
    def get_strategy_comparison(self) -> Dict:
        """Compare all strategies."""
        comparison = {}
        
        for key, stats in self.strategies.items():
            comparison[key] = {
                'name': stats.name,
                'version': stats.version,
                'total_trades': stats.total_trades,
                'win_rate': f"{stats.win_rate * 100:.1f}%",
                'total_pnl': f"{stats.total_pnl:.2f}",
                'pnl_per_trade': f"{stats.pnl_per_trade:.2f}",
                'symbol_performance': stats.pnl_by_symbol,
            }
        
        return comparison
    
    def get_symbol_performance(self) -> Dict[str, Dict]:
        """Get performance by symbol across all strategies."""
        symbols_perf = {}
        
        for strat_key, stats in self.strategies.items():
            for symbol, pnl in stats.pnl_by_symbol.items():
                if symbol not in symbols_perf:
                    symbols_perf[symbol] = {
                        'total_pnl': 0,
                        'strategy_count': 0,
                    }
                
                symbols_perf[symbol]['total_pnl'] += pnl
                symbols_perf[symbol]['strategy_count'] += 1
        
        return symbols_perf
    
    def record_ml_metric(self, metric_name: str, value: float):
        """Record ML optimization metric."""
        self.ml_metrics[metric_name] = value
        logger.info(f" ML Metric: {metric_name} = {value:.3f}")
    
    def generate_report(self) -> str:
        """Generate summary report."""
        report = f"\n{'='*60}\n"
        report += " ADVANCED ANALYTICS DASHBOARD\n"
        report += f"{'='*60}\n\n"
        
        # Strategy comparison
        report += " STRATEGY COMPARISON\n"
        report += f"{'-'*60}\n"
        for key, stats in self.strategies.items():
            report += f"{key}:\n"
            report += f"  Trades: {stats.total_trades} | WR: {stats.win_rate*100:.1f}%\n"
            report += f"  P&L: {stats.total_pnl:.2f} | Per Trade: {stats.pnl_per_trade:.2f}\n"
        
        # Symbol performance
        report += f"\n{'='*60}\n"
        report += " SYMBOL PERFORMANCE\n"
        report += f"{'-'*60}\n"
        perf = self.get_symbol_performance()
        for symbol, data in perf.items():
            report += f"{symbol}: P&L={data['total_pnl']:.2f} ({data['strategy_count']} strategies)\n"
        
        # ML metrics
        report += f"\n{'='*60}\n"
        report += " ML OPTIMIZATION METRICS\n"
        report += f"{'-'*60}\n"
        for metric, value in self.ml_metrics.items():
            report += f"{metric}: {value:.3f}\n"
        
        report += f"{'='*60}\n"
        return report
