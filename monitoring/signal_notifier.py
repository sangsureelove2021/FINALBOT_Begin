"""
Signal Notifier

Send notifications for signals (console, file, Telegram placeholder).
"""

import logging
from typing import Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class SignalNotifier:
    """Send notifications for trading signals."""
    
    def __init__(self, telegram_token: Optional[str] = None,
                 telegram_chat_id: Optional[str] = None):
        """
        Initialize notifier.
        
        Args:
            telegram_token: Telegram bot token (optional)
            telegram_chat_id: Telegram chat ID (optional)
        """
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.telegram_enabled = bool(telegram_token and telegram_chat_id)
        
        if self.telegram_enabled:
            logger.info(" Telegram notifications enabled")
        else:
            logger.info(" Telegram notifications disabled")
    
    def notify_signal(self, symbol: str, direction: str, 
                     amount: float, confidence: int,
                     order_id: str = "") -> None:
        """
        Notify of new signal.
        
        Args:
            symbol: Trading pair
            direction: CALL or PUT
            amount: Trade size
            confidence: Confidence (0-100)
            order_id: Order identifier
        """
        msg = f" SIGNAL: {direction} {amount:.0f}x {symbol} | confidence {confidence}%"
        
        logger.info(msg)
        
        if self.telegram_enabled:
            self._send_telegram(msg)
    
    def notify_trade_closed(self, symbol: str, direction: str,
                           pnl: float, pnl_percent: float) -> None:
        """
        Notify of closed trade.
        
        Args:
            symbol: Trading pair
            direction: CALL or PUT
            pnl: Profit/Loss (THB)
            pnl_percent: Percentage return
        """
        icon = "" if pnl > 0 else ""
        msg = f"{icon} CLOSED: {direction} {symbol} | P&L {pnl:+.2f} THB ({pnl_percent:+.2f}%)"
        
        logger.info(msg)
        
        if self.telegram_enabled:
            self._send_telegram(msg)
    
    def notify_error(self, error_msg: str, context: str = "") -> None:
        """
        Notify of error.
        
        Args:
            error_msg: Error message
            context: Additional context
        """
        msg = f" ERROR: {error_msg}"
        if context:
            msg += f" | {context}"
        
        logger.error(msg)
        
        if self.telegram_enabled:
            self._send_telegram(msg)
    
    def notify_summary(self, total_pnl: float, win_rate: float,
                      trade_count: int) -> None:
        """
        Notify of session summary.
        
        Args:
            total_pnl: Total profit/loss (THB)
            win_rate: Win rate (%)
            trade_count: Number of trades
        """
        msg = (f" SUMMARY: P&L {total_pnl:+.2f} THB | "
               f"Win Rate {win_rate:.1f}% | Trades {trade_count}")
        
        logger.info(msg)
        
        if self.telegram_enabled:
            self._send_telegram(msg)
    
    def _send_telegram(self, message: str) -> None:
        """
        Send message via Telegram.
        
        Args:
            message: Message to send
        
        Note:
            Requires iqoptionapi or requests library
            Currently placeholder - implement when needed
        """
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, data=data, timeout=5)
            
            if response.status_code != 200:
                logger.warning(f"Telegram send failed: {response.status_code}")
        
        except ImportError:
            logger.warning("requests library not installed for Telegram")
        except Exception as e:
            logger.warning(f"Telegram notification failed: {e}")
