"""
Health Monitor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Monitor bot health (connections, errors, alerts).
"""

import logging
from typing import Dict, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HealthAlert:
    """Health alert item."""
    timestamp: datetime
    level: str  # 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    component: str
    message: str


class HealthMonitor:
    """Monitor system health."""
    
    def __init__(self):
        """Initialize health monitor."""
        self.alerts: List[HealthAlert] = []
        self.data_connected = False
        self.executor_connected = False
        self.last_cycle_time = None
        self.error_count = 0
    
    def log_alert(self, level: str, component: str, message: str) -> None:
        """
        Log health alert.
        
        Args:
            level: Alert level (INFO, WARNING, ERROR, CRITICAL)
            component: Component name
            message: Alert message
        """
        alert = HealthAlert(
            timestamp=datetime.utcnow(),
            level=level,
            component=component,
            message=message
        )
        self.alerts.append(alert)
        
        if level == 'CRITICAL':
            logger.critical(f"🚨 {component}: {message}")
        elif level == 'ERROR':
            logger.error(f"❌ {component}: {message}")
            self.error_count += 1
        elif level == 'WARNING':
            logger.warning(f"⚠️ {component}: {message}")
        else:
            logger.info(f"ℹ️ {component}: {message}")
    
    def set_data_connected(self, connected: bool) -> None:
        """Set data source connection status."""
        self.data_connected = connected
        status = "connected" if connected else "disconnected"
        self.log_alert(
            level='ERROR' if not connected else 'INFO',
            component='DataSource',
            message=f"IQ Option adapter {status}"
        )
    
    def set_executor_connected(self, connected: bool) -> None:
        """Set executor connection status."""
        self.executor_connected = connected
        status = "connected" if connected else "disconnected"
        self.log_alert(
            level='WARNING' if not connected else 'INFO',
            component='Executor',
            message=f"IQ Option executor {status}"
        )
    
    def record_cycle_time(self, cycle_time: float) -> None:
        """Record cycle execution time."""
        self.last_cycle_time = cycle_time
        
        if cycle_time > 5.0:
            self.log_alert(
                level='WARNING',
                component='Performance',
                message=f"Slow cycle: {cycle_time:.2f}s"
            )
    
    def get_status(self) -> Dict:
        """Get overall health status."""
        status = {
            'timestamp': datetime.utcnow().isoformat(),
            'data_connected': self.data_connected,
            'executor_connected': self.executor_connected,
            'last_cycle_time': self.last_cycle_time,
            'error_count': self.error_count,
            'alert_count': len(self.alerts),
            'critical_alerts': len([a for a in self.alerts if a.level == 'CRITICAL']),
            'error_alerts': len([a for a in self.alerts if a.level == 'ERROR']),
            'overall_health': self._assess_health(),
        }
        return status
    
    def _assess_health(self) -> str:
        """Assess overall health."""
        critical_count = len([a for a in self.alerts if a.level == 'CRITICAL'])
        error_count = len([a for a in self.alerts if a.level == 'ERROR'])
        
        if critical_count > 0:
            return 'CRITICAL'
        elif error_count > 3 or not (self.data_connected and self.executor_connected):
            return 'ERROR'
        elif error_count > 0:
            return 'WARNING'
        else:
            return 'OK'
    
    def print_status(self) -> None:
        """Print health status."""
        status = self.get_status()
        
        logger.info("\n" + "="*80)
        logger.info("🏥 HEALTH MONITOR")
        logger.info("="*80)
        logger.info(f"Data Connected: {'✅' if status['data_connected'] else '❌'}")
        logger.info(f"Executor Connected: {'✅' if status['executor_connected'] else '❌'}")
        logger.info(f"Overall Health: {status['overall_health']}")
        logger.info(f"Error Count: {status['error_count']}")
        logger.info(f"Alert Count: {status['alert_count']}")
        logger.info("="*80 + "\n")
    
    def get_recent_alerts(self, count: int = 10) -> List[HealthAlert]:
        """Get recent alerts."""
        return self.alerts[-count:] if self.alerts else []
