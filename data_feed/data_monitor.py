"""
Data Monitor

Monitors the state of the data feed: connection status, latency, and gaps.
"""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DataMonitor:
    """Monitors and reports state of data feed operations."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize with monitoring configuration.
        
        Args:
            config: Configuration from datafeed_config.json data_monitor section
        """
        if config is None:
            from config_setting.config_loader import get_data_monitor_config
            config = get_data_monitor_config()
        
        # Load monitoring configuration
        self.gap_thresholds = config.get("gap_thresholds", {
            "M1": 300, "M5": 1500, "M15": 4500
        })
        self.latency_thresholds = config.get("latency_thresholds", {
            "HIGH": 360000, "MEDIUM": 480000, "LOW": 600000, "STALE": 600000
        })
        self.error_threshold = config.get("error_threshold", 10)
        self.enable_connection_monitoring = config.get("enable_connection_monitoring", True)
        self.log_level = config.get("log_level", "WARNING")
        
        # Initialize monitoring state
        self.connection_status = True
        self.gap_count = 0
        self.latency_ms = 0
        self.error_count = 0
        self.queue_length = 0
        self.last_check_time = datetime.now()
        
        logger.info(f"[DataMonitor] Initialized with log level: {self.log_level}")

    def update_connection_status(self, status: bool) -> None:
        """Update connection status."""
        if self.enable_connection_monitoring:
            self.connection_status = status
            if not status:
                logger.warning("[DataMonitor] Data feed connection lost!")
                self._report_error("connection_lost")

    def report_gap(self, symbol: str, timeframe: str, gap_seconds: float) -> None:
        """Log gap detection events."""
        self.gap_count += 1
        threshold = self.gap_thresholds.get(timeframe, 300)
        
        if gap_seconds > threshold:
            level = "ERROR" if gap_seconds > threshold * 2 else "WARNING"
            message = f"[DataMonitor] CRITICAL - Data gap detected for {symbol} ({timeframe}): {gap_seconds}s (threshold: {threshold}s)"
            
            if level == "ERROR":
                logger.critical(message)
            else:
                logger.error(message)
                
            self._report_error("data_gap")
            
            # CRITICAL: หยุดระบบทันที
            raise RuntimeError(f"CRITICAL DATA GAP: {symbol} {timeframe} {gap_seconds}s")

    def report_latency(self, symbol: str, timeframe: str, age_ms: int) -> None:
        """Log quality alerts for stale data."""
        self.latency_ms = age_ms
        
        # Determine quality level based on thresholds
        if age_ms >= self.latency_thresholds["STALE"]:
            level = "CRITICAL"
            message = f"[DataMonitor] CRITICAL - Stale data for {symbol} ({timeframe}): latency {age_ms}ms"
        elif age_ms >= self.latency_thresholds["HIGH"]:
            level = "ERROR"
            message = f"[DataMonitor] CRITICAL - High latency for {symbol} ({timeframe}): {age_ms}ms"
        elif age_ms >= self.latency_thresholds["MEDIUM"]:
            level = "WARNING"
            message = f"[DataMonitor] CRITICAL - Medium latency for {symbol} ({timeframe}): {age_ms}ms"
        else:
            level = "INFO"
            message = f"[DataMonitor] Normal latency for {symbol} ({timeframe}): {age_ms}ms"
        
        # Log according to configured log level
        if level == "CRITICAL":
            logger.critical(message)
        elif level == "ERROR" and self.log_level in ["ERROR", "WARNING", "INFO"]:
            logger.critical(message)
        elif level == "WARNING" and self.log_level in ["WARNING", "INFO"]:
            logger.critical(message)
        elif level == "INFO" and self.log_level == "INFO":
            logger.info(message)
            
        # CRITICAL: หยุดระบบทันที
        if age_ms >= self.latency_thresholds["STALE"]:
            raise RuntimeError(f"CRITICAL LATENCY: {symbol} {timeframe} {age_ms}ms")

    def report_queue_status(self, queue_length: int) -> None:
        """Report queue status and alert if queue grows too large."""
        self.queue_length = queue_length
        
        if queue_length > 1000:
            logger.critical(f"[DataMonitor] CRITICAL - Queue overflow: {queue_length} items pending")
            raise RuntimeError(f"CRITICAL QUEUE OVERFLOW: {queue_length} items")
        elif queue_length > 500:
            logger.critical(f"[DataMonitor] CRITICAL - Queue critical: {queue_length} items pending")
            raise RuntimeError(f"CRITICAL QUEUE SIZE: {queue_length} items")
        elif queue_length > 100:
            logger.info(f"[DataMonitor] INFO - Queue size: {queue_length} items")
    
    def _report_error(self, error_type: str) -> None:
        """Internal error reporting with threshold checking."""
        self.error_count += 1
        
        if self.error_count >= self.error_threshold:
            logger.critical(f"[DataMonitor] CRITICAL - Error threshold exceeded ({self.error_count} errors)")
            raise RuntimeError(f"Critical error threshold exceeded ({self.error_count} errors)")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status summary."""
        return {
            "connection_status": self.connection_status,
            "gap_count": self.gap_count,
            "latency_ms": self.latency_ms,
            "error_count": self.error_count,
            "queue_length": self.queue_length,
            "last_check": self.last_check_time.isoformat()
        }
