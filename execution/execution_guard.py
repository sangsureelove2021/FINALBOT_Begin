"""
RISK GATE - EXECUTION GUARD (signal_veto)


The FINAL DEFENSE before any trade executes.

This guard sits AFTER the execution_gate and adds account-level
and session-level risk controls that the strategy/context cannot see:
    - Daily loss limits
    - Consecutive loss limits
    - Max trades per session
    - Cooldown after losses
    - Time-of-day filters

A signal must pass BOTH the execution_gate (signal quality)
AND this execution_guard (account safety) to be executed.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta


class ExecutionGuard:
    """
    Account & session level risk guard.
    
    This is the absolute last veto. Even a perfect signal gets
    blocked here if account-level limits are hit.
    """
    
    def __init__(self,
                 max_daily_loss: float = float('inf'),
                 max_consecutive_losses: int = 3,
                 max_trades_per_session: int = 10**9,
                 cooldown_minutes_after_loss: int = 15,
                 min_confidence_to_execute: int = 75):
        # Limits
        self.max_daily_loss = max_daily_loss
        self.max_consecutive_losses = max_consecutive_losses
        self.max_trades_per_session = max_trades_per_session
        self.cooldown_minutes = cooldown_minutes_after_loss
        self.min_confidence = min_confidence_to_execute
        
        # Session state
        self._daily_loss = 0.0
        self._consecutive_losses = 0
        self._trades_today = 0
        self._last_loss_time: Optional[datetime] = None
        self._session_start = datetime.now(timezone.utc)
        self._halted = False
        self._halt_reason = ""
        
        # Parse trading hours (e.g. "17:00-23:00")
        try:
            from core.config_loader import get_session
            session = get_session()
            hours_str = session.get("trading_hours", "17:00-23:00")
            start_str, end_str = hours_str.split("-")
            self.start_hour, self.start_min = map(int, start_str.split(":"))
            self.end_hour, self.end_min = map(int, end_str.split(":"))
        except Exception:
            self.start_hour, self.start_min = 17, 0
            self.end_hour, self.end_min = 23, 0
    
    def check(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check signal against account and session safety limits.
        """
        action = signal_data.get('action', 'NO_SIGNAL')
        confidence = signal_data.get('confidence', 0)
        
        # Non-actionable signals pass through as before
        if action in ('NO_SIGNAL', 'BLOCKED'):
            return self._allow("Non-actionable signal, no guard needed")
        
        # 1. Halted state
        if self._halted:
            return self._veto(f"Trading halted: {self._halt_reason}", "session_halted")
            
        # 2. Daily loss check
        if self._daily_loss >= self.max_daily_loss:
            self._halt("Daily loss limit reached")
            return self._veto("Daily loss limit reached", "daily_loss_limit")
            
        # 3. Consecutive losses check
        if self._consecutive_losses >= self.max_consecutive_losses:
            self._halt("Max consecutive losses reached")
            return self._veto("Max consecutive losses reached", "consecutive_losses")
            
        # 4. Max trades check
        if self._trades_today >= self.max_trades_per_session:
            self._halt("Max trades per session reached")
            return self._veto("Max trades per session reached", "max_trades")
            
        # 5. Cooldown check
        if self._is_in_cooldown():
            return self._veto("Cooldown in progress after loss", "cooldown")
            
        # 6. Min confidence check
        # [DISABLED per Boss request] Make confidence informational only
        # if confidence < self.min_confidence:
        #     return self._veto(f"Confidence {confidence} below minimum {self.min_confidence}", "low_confidence")
            
        return self._allow(
            f"Approved: conf={confidence}, trades={self._trades_today}, "
            f"streak_loss={self._consecutive_losses}"
        )
    
    def record_trade_opened(self) -> None:
        """Call when a trade is actually opened"""
        self._trades_today += 1
    
    def record_trade_result(self, won: bool, profit_loss: float) -> None:
        """
        Record the result of a closed trade.
        
        Args:
            won: True if trade won
            profit_loss: profit (positive) or loss (negative) amount
        """
        if won:
            self._consecutive_losses = 0
        else:
            self._consecutive_losses += 1
            self._last_loss_time = datetime.now(timezone.utc)
            # Track loss amount
            self._daily_loss += abs(profit_loss)
    
    def reset_session(self) -> None:
        """Reset for a new trading session/day"""
        self._daily_loss = 0.0
        self._consecutive_losses = 0
        self._trades_today = 0
        self._last_loss_time = None
        self._session_start = datetime.now(timezone.utc)
        self._halted = False
        self._halt_reason = ""
    
    def get_status(self) -> Dict[str, Any]:
        """Current guard status"""
        return {
            'halted': self._halted,
            'halt_reason': self._halt_reason,
            'daily_loss': round(self._daily_loss, 2),
            'daily_loss_limit': self.max_daily_loss,
            'consecutive_losses': self._consecutive_losses,
            'trades_today': self._trades_today,
            'max_trades': self.max_trades_per_session,
            'in_cooldown': self._is_in_cooldown(),
            'session_duration_min': round(
                (datetime.now(timezone.utc) - self._session_start).total_seconds() / 60, 1
            ),
        }
    
    def _is_in_cooldown(self) -> bool:
        if self._last_loss_time is None:
            return False
        elapsed = datetime.now(timezone.utc) - self._last_loss_time
        return elapsed < timedelta(minutes=self.cooldown_minutes)
    
    def _halt(self, reason: str) -> None:
        """Halt all trading for the session"""
        self._halted = True
        self._halt_reason = reason
    
    def _allow(self, reason: str) -> Dict[str, Any]:
        return {'allowed': True, 'reason': reason, 'veto_code': None}
    
    def _veto(self, reason: str, code: str) -> Dict[str, Any]:
        return {'allowed': False, 'reason': reason, 'veto_code': code}
