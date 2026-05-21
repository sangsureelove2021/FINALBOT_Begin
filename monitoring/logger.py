"""
Logger System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Unified logging for bot. Logs to file + console with levels.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class BotLogger:
    """Centralized logging configuration."""
    
    def __init__(self, name: str = "FINALBOT", 
                 log_dir: str = "./logs",
                 level: str = "INFO"):
        """
        Initialize logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.name = name
        self.level = getattr(logging, level)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Console handler (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (daily log file)
        log_file = self.log_dir / f"{name.lower()}_{datetime.utcnow().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(self.level)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Signal log (separate file for trades only)
        signal_file = self.log_dir / f"signals_{datetime.utcnow().strftime('%Y%m%d')}.log"
        signal_handler = logging.FileHandler(signal_file, mode='a')
        signal_handler.setLevel(logging.INFO)
        signal_handler.setFormatter(file_formatter)
        self.signal_logger = logging.getLogger(f"{name}.SIGNALS")
        self.signal_logger.addHandler(signal_handler)
        self.signal_logger.setLevel(logging.INFO)
    
    def debug(self, msg: str) -> None:
        """Log debug message."""
        self.logger.debug(msg)
    
    def info(self, msg: str) -> None:
        """Log info message."""
        self.logger.info(msg)
    
    def warning(self, msg: str) -> None:
        """Log warning message."""
        self.logger.warning(msg)
    
    def error(self, msg: str) -> None:
        """Log error message."""
        self.logger.error(msg)
    
    def critical(self, msg: str) -> None:
        """Log critical message."""
        self.logger.critical(msg)
    
    def log_signal(self, symbol: str, direction: str, amount: float,
                   confidence: int, order_id: str = "") -> None:
        """Log trade signal."""
        msg = f"SIGNAL | {symbol} | {direction} | {amount:.0f} | confidence={confidence}% | {order_id}"
        self.signal_logger.info(msg)
        self.logger.info(f"✅ {msg}")
    
    def log_trade_closed(self, order_id: str, pnl: float, 
                        pnl_percent: float) -> None:
        """Log closed trade."""
        icon = "✅" if pnl > 0 else "❌"
        msg = f"CLOSED | {order_id} | P&L={pnl:+.2f} THB ({pnl_percent:+.2f}%)"
        self.signal_logger.info(msg)
        self.logger.info(f"{icon} {msg}")
    
    def get_logger(self) -> logging.Logger:
        """Get underlying logger object."""
        return self.logger


# Global logger instance
_logger_instance: Optional[BotLogger] = None


def get_logger(name: str = "FINALBOT") -> BotLogger:
    """Get or create global logger."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = BotLogger(name)
    return _logger_instance


def setup_logging(level: str = "INFO", log_dir: str = "./logs") -> BotLogger:
    """Setup logging system."""
    global _logger_instance
    _logger_instance = BotLogger(level=level, log_dir=log_dir)
    return _logger_instance
