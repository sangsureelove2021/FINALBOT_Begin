"""
Position Sizer

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
from datetime import datetime, timezone, timedelta

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
                 max_daily_risk: float = 9999.0,  # % per day
                 min_amount: float = 10.0,
                 max_per_trade: float = 9999.0):
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
        self.session_start = datetime.now(timezone.utc)
        
        logger.info(f"[STAT] PositionSizer initialized")
        logger.info(f"   Capital: {capital} THB")
        logger.info(f"   Risk per trade: {risk_percent}%")
        logger.info(f"   Max daily risk: {max_daily_risk}%")
    
    def calculate(self, 
                 entry_price: Optional[float] = None,
                 stop_loss_price: Optional[float] = None,
                 direction: str = 'CALL',
                 confidence: Optional[float] = None) -> Any:
        """
        Calculate position size based on risk or confidence.
        
        Supports two modes:
        1. Forex/Stock mode: Returns PositionSize object using entry & stop loss.
        2. Binary Options mode: Returns float stake size using confidence & config settings.

        In confidence mode, the stake is scaled by signal quality and the
        remaining daily risk budget. If a stop loss is supplied, the sizing
        falls back to the explicit risk-based path.
        """
        from typing import Any
        
        if entry_price is not None and stop_loss_price is not None:
            return self._calculate_from_stop_loss(entry_price, stop_loss_price, direction)

        if confidence is not None:
            # Binary Options Mode: Load base stake from config/settings.json.
            from core.config_loader import load_settings
            try:
                base_stake = float(load_settings().get("capital", {}).get("stake_per_trade", 30.0))
            except Exception as e:
                logger.error(f"[ERR] Failed to load stake_per_trade: {e}")
                base_stake = 30.0

            daily_risk_used = self._get_daily_risk_used()
            daily_risk_percent = (daily_risk_used / self.capital) * 100 if self.capital else 0.0
            if daily_risk_percent >= self.max_daily_risk:
                logger.warning(
                    f"[RISK] Daily risk limit reached ({daily_risk_percent:.2f}% >= {self.max_daily_risk:.2f}%)"
                )
                return 0.0

            try:
                conf = max(0.0, min(100.0, float(confidence)))
            except Exception:
                conf = 0.0

            confidence_scale = 0.75 + (conf / 100.0) * 0.75
            remaining_daily_scale = 1.0
            if self.max_daily_risk > 0:
                remaining_daily_scale = max(
                    0.25,
                    min(1.0, (self.max_daily_risk - daily_risk_percent) / self.max_daily_risk),
                )

            amount = base_stake * confidence_scale * remaining_daily_scale
            amount = max(self.min_amount, min(amount, self.max_per_trade))
            return amount

        return self.min_amount

    def _calculate_from_stop_loss(self,
                                  entry_price: float,
                                  stop_loss_price: float,
                                  direction: str) -> PositionSize:
        """Risk-based sizing using entry and stop-loss prices."""
        distance = abs(entry_price - stop_loss_price)

        if distance <= 0:
            return PositionSize(
                amount=0,
                risk_amount=0,
                risk_percent=0,
                daily_risk=0,
                is_valid=False,
                reason="[ERR] Invalid SL: distance is 0",
            )

        max_risk_amount = (self.capital * self.risk_percent) / 100
        amount = max_risk_amount / distance if distance > 0 else 0
        amount = max(self.min_amount, min(amount, self.max_per_trade))

        daily_risk_used = self._get_daily_risk_used()
        daily_risk_percent = (daily_risk_used / self.capital) * 100 if self.capital else 0.0

        if daily_risk_percent >= self.max_daily_risk:
            return PositionSize(
                amount=0,
                risk_amount=max_risk_amount,
                risk_percent=self.risk_percent,
                daily_risk=daily_risk_percent,
                is_valid=False,
                reason=f"[ERR] Daily risk limit ({self.max_daily_risk}%) exceeded",
            )

        return PositionSize(
            amount=amount,
            risk_amount=max_risk_amount,
            risk_percent=self.risk_percent,
            daily_risk=daily_risk_percent,
            is_valid=True,
            reason=f"[OK] {direction} {amount:.0f} contracts (risk: {self.risk_percent}%, daily: {daily_risk_percent:.2f}%)",
        )
    
    def record_trade(self, amount: float, result: float = 0.0) -> None:
        """
        Record a trade for daily tracking.
        
        Args:
            amount: Trade size
            result: Profit/loss in THB (0 for pending)
        """
        self.daily_trades.append({
            'timestamp': datetime.now(timezone.utc),
            'amount': amount,
            'result': result
        })
    
    def reset_daily_tracking(self) -> None:
        """Reset daily trade history."""
        self.daily_trades = []
        self.session_start = datetime.now(timezone.utc)
        logger.info("[LOOP] Daily tracking reset")
    
    def _get_daily_risk_used(self) -> float:
        """Calculate total risk used today."""
        # Filter trades from today
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
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
                                if t['timestamp'] >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)]),
        }
