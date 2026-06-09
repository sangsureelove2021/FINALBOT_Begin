"""
Replay Report Generator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generate performance reports from replay results.
"""

import logging
from typing import Dict, List
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


class ReplayReport:
    """Generate trading performance reports."""
    
    def __init__(self, bot_runner=None):
        """
        Initialize report generator.
        
        Args:
            bot_runner: BotRunner instance (for trade history)
        """
        self.bot = bot_runner
    
    def generate_summary(self, replay_metrics: Dict,
                        order_manager=None) -> Dict:
        """
        Generate summary report.
        
        Args:
            replay_metrics: Metrics from ReplayEngine
            order_manager: OrderManager instance (for P&L)
        
        Returns:
            Report dictionary
        """
        om_stats = order_manager.get_stats() if order_manager else {}
        
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'replay_metrics': replay_metrics,
            'trading_performance': {
                'total_trades': om_stats.get('total_trades', 0),
                'active_trades': om_stats.get('active_trades', 0),
                'win_rate': f"{om_stats.get('win_rate', 0):.1f}%",
                'total_pnl': f"{om_stats.get('total_pnl', 0):+.2f} THB",
                'avg_win': f"{om_stats.get('avg_win', 0):+.2f} THB",
                'avg_loss': f"{om_stats.get('avg_loss', 0):+.2f} THB",
                'largest_win': f"{om_stats.get('largest_win', 0):+.2f} THB",
                'largest_loss': f"{om_stats.get('largest_loss', 0):+.2f} THB",
            },
            'signal_quality': {
                'total_signals': replay_metrics.get('total_signals', 0),
                'call_ratio': f"{replay_metrics.get('call_ratio', 0):.1f}%",
                'put_ratio': f"{replay_metrics.get('put_ratio', 0):.1f}%",
                'avg_confidence': f"{replay_metrics.get('avg_confidence', 0):.0f}%",
                'signals_per_cycle': f"{replay_metrics.get('signals_per_cycle', 0):.4f}",
            },
        }
        
        return report
    
    def print_summary(self, report: Dict) -> None:
        """Pretty print summary report."""
        print("\n" + "="*80)
        print("📊 REPLAY REPORT")
        print("="*80)
        print(f"Generated: {report['timestamp']}\n")
        
        # Replay Metrics
        print("SIGNAL GENERATION:")
        for key, value in report['signal_quality'].items():
            print(f"  {key}: {value}")
        
        print("\nTRADING PERFORMANCE:")
        for key, value in report['trading_performance'].items():
            print(f"  {key}: {value}")
        
        print("\n" + "="*80 + "\n")
    
    def export_json(self, report: Dict, filepath: str) -> None:
        """Export report to JSON."""
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"✅ Report exported to {filepath}")
    
    def export_txt(self, report: Dict, filepath: str) -> None:
        """Export report to text file."""
        with open(filepath, 'w') as f:
            f.write("="*80 + "\n")
            f.write("REPLAY REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Generated: {report['timestamp']}\n\n")
            
            f.write("SIGNAL GENERATION:\n")
            for key, value in report['signal_quality'].items():
                f.write(f"  {key}: {value}\n")
            
            f.write("\nTRADING PERFORMANCE:\n")
            for key, value in report['trading_performance'].items():
                f.write(f"  {key}: {value}\n")
            
            f.write("\n" + "="*80 + "\n")
        
        logger.info(f"✅ Report exported to {filepath}")
