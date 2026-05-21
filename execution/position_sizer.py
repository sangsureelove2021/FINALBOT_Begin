"""
Position Sizer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Calculate trade size based on risk management rules.

Risk Formula:
  amount = capital × (risk_percent / 100) / distance_to_sl
  
  Example:
    capital = 2000 THB
    risk_percent = 2% (max per trade)
    distance_to_sl = 0.0010 (0.10%)
    → amount = 2000 × (2 / 100) / 0.0010 = 4000 (contracts)
    
    Capped at max_per_trade and daily max
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class PositionSize:
    """Result of position sizing calculation."""
    amount: float  # Trade size (contracts or currency units)
    risk_amount: float  # Money at risk (THB)
    risk_percent: float  # As % of capital
    daily_risk: float  # Cumulative daily risk
    is_valid: bool  # Passes all checks
    reason: str  # Why approved or rejected


class PositionSizer:
    """
    Calculate trade size with money management.
    
    Rules:
    - Max risk per trade: risk_percent (e.g. 2%)
    - Max risk per day: max_daily_risk (e.g. 5%)
    - Min trade size: min_amount (e.g. 10)
    - Max trade size: max_per_trade (e.g. 500)
    - Prevent over-leverage
    """
    
    def __init__(self, 
                 capital: float = 2000.0,  # THB
                 risk_percent: float = 2.0,  # % per trade
                 max_daily_risk: float = 5.0,  # % per day
                 min_amount: float = 10.0,
                 max_per_trade: float = 500.0):
        """
        Initialize sizer.
        
        Args:
            capital: Account balance (THB)
            risk_percent: Max risk per trade (%)
            max_daily_risk: Max cumulative daily risk (%)
            min_amount: Minimum trade size
            max_per_trade: Maximum trade size
        """
        self.capital = capital
        self.risk_percent = risk_percent
        self.max_daily_risk = max_daily_risk
        self.min_amount = min_amount
        self.max_per_trade = max_per_trade
        
        # Track daily P&L
        self.daily_trades = []  # List of (timestamp, amount, result)
        self.session_start = datetime.utcnow()
        
        logger.info(f"📊 PositionSizer initialized")
        logger.info(f"   Capital: {capital} THB")
        logger.info(f"   Risk per trade: {risk_percent}%")
        logger.info(f"   Max daily risk: {max_daily_risk}%")
    
    def calculate(self, 
                 entry_price: float,
                 stop_loss_price: float,
                 direction: str = 'CALL') -> PositionSize:
        """
        Calculate position size based on risk.
        
        Args:
            entry_price: Entry price (e.g. 1.0850)
            stop_loss_price: Stop loss price
            direction: 'CALL' or 'PUT' (for logging)
        
        Returns:
            PositionSize object with calculated amount and validity
        """
        # Calculate distance to SL
        distance = abs(entry_price - stop_loss_price)
        
        if distance <= 0:
            return PositionSize(
                amount=0, risk_amount=0, risk_percent=0,
                daily_risk=0, is_valid=False,
                reason="❌ Invalid SL: distance is 0"
            )
        
        # Risk amount in THB
        max_risk_amount = (self.capital * self.risk_percent) / 100
        
        # Calculate position size
        # amount = risk_amount / distance
        amount = max_risk_amount / distance if distance > 0 else 0
        amount = max(self.min_amount, min(amount, self.max_per_trade))
        
        # Check daily risk limit
        daily_risk_used = self._get_daily_risk_used()
        daily_risk_percent = (daily_risk_used / self.capital) * 100
        
        if daily_risk_percent >= self.max_daily_risk:
            return PositionSize(
                amount=0, risk_amount=max_risk_amount, 
                risk_percent=self.risk_percent,
                daily_risk=daily_risk_percent, is_valid=False,
                reason=f"❌ Daily risk limit ({self.max_daily_risk}%) exceeded"
            )
        
        return PositionSize(
            amount=amount,
            risk_amount=max_risk_amount,
            risk_percent=self.risk_percent,
            daily_risk=daily_risk_percent,
            is_valid=True,
            reason=f"✅ {direction} {amount:.0f} contracts (risk: {self.risk_percent}%, daily: {daily_risk_percent:.2f}%)"
        )
    
    def record_trade(self, amount: float, result: float = 0.0) -> None:
        """
        Record a trade for daily tracking.
        
        Args:
            amount: Trade size
            result: Profit/loss in THB (0 for pending)
        """
        self.daily_trades.append({
            'timestamp': datetime.utcnow(),
            'amount': amount,
            'result': result
        })
    
    def reset_daily_tracking(self) -> None:
        """Reset daily trade history."""
        self.daily_trades = []
        self.session_start = datetime.utcnow()
        logger.info("🔄 Daily tracking reset")
    
    def _get_daily_risk_used(self) -> float:
        """Calculate total risk used today."""
        # Filter trades from today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        daily_pnl = 0.0
        for trade in self.daily_trades:
            if trade['timestamp'] >= today_start:
                daily_pnl += abs(trade['result'])  # Count losses only
        
        return daily_pnl
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        daily_risk = self._get_daily_risk_used()
        daily_risk_percent = (daily_risk / self.capital) * 100
        
        return {
            'capital': self.capital,
            'risk_percent_per_trade': self.risk_percent,
            'max_daily_risk_percent': self.max_daily_risk,
            'daily_risk_used': daily_risk,
            'daily_risk_percent': daily_risk_percent,
            'daily_risk_remaining': self.max_daily_risk - daily_risk_percent,
            'trades_today': len([t for t in self.daily_trades 
                                if t['timestamp'] >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)]),
        }
