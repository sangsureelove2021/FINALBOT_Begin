"""
Reporter
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generate daily/weekly reports.
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class Reporter:
    """Generate bot reports."""
    
    def __init__(self, report_dir: str = "./reports"):
        """
        Initialize reporter.
        
        Args:
            report_dir: Directory for reports
        """
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)
    
    def generate_daily_report(self, 
                             order_manager=None,
                             performance_monitor=None,
                             health_monitor=None) -> Dict:
        """
        Generate daily report.
        
        Args:
            order_manager: OrderManager instance
            performance_monitor: PerformanceMonitor instance
            health_monitor: HealthMonitor instance
        
        Returns:
            Report dictionary
        """
        om_stats = order_manager.get_stats() if order_manager else {}
        perf_metrics = (performance_monitor.get_metrics() 
                       if performance_monitor else None)
        health_status = health_monitor.get_status() if health_monitor else {}
        
        report = {
            'date': datetime.utcnow().date().isoformat(),
            'timestamp': datetime.utcnow().isoformat(),
            'trading_stats': {
                'total_trades': om_stats.get('total_trades', 0),
                'wins': om_stats.get('wins', 0),
                'losses': om_stats.get('losses', 0),
                'win_rate': f"{om_stats.get('win_rate', 0):.1f}%",
                'total_pnl': f"{om_stats.get('total_pnl', 0):+.2f} THB",
                'avg_win': f"{om_stats.get('avg_win', 0):+.2f} THB",
                'avg_loss': f"{om_stats.get('avg_loss', 0):+.2f} THB",
                'largest_win': f"{om_stats.get('largest_win', 0):+.2f} THB",
                'largest_loss': f"{om_stats.get('largest_loss', 0):+.2f} THB",
            },
            'performance': {
                'cycles': perf_metrics.cycle_count if perf_metrics else 0,
                'signals': perf_metrics.signal_count if perf_metrics else 0,
                'signals_per_hour': f"{perf_metrics.signals_per_hour:.2f}" if perf_metrics else "N/A",
                'avg_cycle_time': f"{perf_metrics.avg_cycle_time:.3f}s" if perf_metrics else "N/A",
            },
            'health': {
                'overall': health_status.get('overall_health', 'N/A'),
                'data_connected': health_status.get('data_connected', False),
                'executor_connected': health_status.get('executor_connected', False),
                'error_count': health_status.get('error_count', 0),
            }
        }
        
        return report
    
    def save_report(self, report: Dict, filename: Optional[str] = None) -> str:
        """
        Save report to file.
        
        Args:
            report: Report dictionary
            filename: Custom filename (default: daily_YYYYMMDD.json)
        
        Returns:
            Path to saved file
        """
        if filename is None:
            date_str = datetime.utcnow().strftime('%Y%m%d')
            filename = f"daily_{date_str}.json"
        
        filepath = self.report_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Report saved: {filepath}")
        return str(filepath)
    
    def print_report(self, report: Dict) -> None:
        """Pretty print report."""
        print("\n" + "="*80)
        print("📄 DAILY REPORT")
        print("="*80)
        print(f"Date: {report['date']}\n")
        
        print("TRADING STATS:")
        for key, value in report['trading_stats'].items():
            print(f"  {key}: {value}")
        
        print("\nPERFORMANCE:")
        for key, value in report['performance'].items():
            print(f"  {key}: {value}")
        
        print("\nHEALTH:")
        for key, value in report['health'].items():
            print(f"  {key}: {value}")
        
        print("\n" + "="*80 + "\n")
