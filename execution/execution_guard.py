"""
RISK GATE - EXECUTION GUARD (signal_veto)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The FINAL DEFENSE before any trade executes.
Philosophy: "The Art of Saying NO"

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
from datetime import datetime, timedelta


class ExecutionGuard:
    """
    Account & session level risk guard.
    
    This is the absolute last veto. Even a perfect signal gets
    blocked here if account-level limits are hit.
    """
    
    def __init__(self,
                 max_daily_loss: float = 100.0,
                 max_consecutive_losses: int = 3,
                 max_trades_per_session: int = 20,
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
        self._session_start = datetime.utcnow()
        self._halted = False
        self._halt_reason = ""
    
    def check(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a signal is allowed to execute.
        
        Args:
            signal_data: dict with 'action', 'confidence', etc.
        
        Returns:
            {
                'allowed': bool,
                'reason': str,
                'veto_code': str or None
            }
        """
        action = signal_data.get('action', 'NO_SIGNAL')
        confidence = signal_data.get('confidence', 0)
        
        # === NON-ACTIONABLE: pass through ===
        if action in ('NO_SIGNAL', 'BLOCKED'):
            return self._allow("Non-actionable signal, no guard needed")
        
        # === HARD HALT ===
        if self._halted:
            return self._veto(f"Trading halted: {self._halt_reason}", 'session_halted')
        
        # === CHECK 1: Daily loss limit ===
        if self._daily_loss >= self.max_daily_loss:
            self._halt(f"Daily loss limit reached (${self._daily_loss:.2f})")
            return self._veto(
                f"Daily loss limit hit: ${self._daily_loss:.2f} >= ${self.max_daily_loss:.2f}",
                'daily_loss_limit'
            )
        
        # === CHECK 2: Consecutive losses ===
        if self._consecutive_losses >= self.max_consecutive_losses:
            return self._veto(
                f"Consecutive loss limit: {self._consecutive_losses} losses in a row",
                'consecutive_losses'
            )
        
        # === CHECK 3: Max trades per session ===
        if self._trades_today >= self.max_trades_per_session:
            return self._veto(
                f"Max trades reached: {self._trades_today}/{self.max_trades_per_session}",
                'max_trades'
            )
        
        # === CHECK 4: Cooldown after loss ===
        if self._last_loss_time is not None:
            elapsed = datetime.utcnow() - self._last_loss_time
            cooldown = timedelta(minutes=self.cooldown_minutes)
            if elapsed < cooldown:
                remaining = (cooldown - elapsed).total_seconds() / 60
                return self._veto(
                    f"Cooldown active: {remaining:.1f} min remaining after last loss",
                    'cooldown'
                )
        
        # === CHECK 5: Confidence floor ===
        if confidence < self.min_confidence:
            return self._veto(
                f"Confidence {confidence} below execution floor {self.min_confidence}",
                'low_confidence'
            )
        
        # === ALL CHECKS PASSED ===
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
            self._last_loss_time = datetime.utcnow()
            # Track loss amount
            self._daily_loss += abs(profit_loss)
    
    def reset_session(self) -> None:
        """Reset for a new trading session/day"""
        self._daily_loss = 0.0
        self._consecutive_losses = 0
        self._trades_today = 0
        self._last_loss_time = None
        self._session_start = datetime.utcnow()
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
                (datetime.utcnow() - self._session_start).total_seconds() / 60, 1
            ),
        }
    
    def _is_in_cooldown(self) -> bool:
        if self._last_loss_time is None:
            return False
        elapsed = datetime.utcnow() - self._last_loss_time
        return elapsed < timedelta(minutes=self.cooldown_minutes)
    
    def _halt(self, reason: str) -> None:
        """Halt all trading for the session"""
        self._halted = True
        self._halt_reason = reason
    
    def _allow(self, reason: str) -> Dict[str, Any]:
        return {'allowed': True, 'reason': reason, 'veto_code': None}
    
    def _veto(self, reason: str, code: str) -> Dict[str, Any]:
        return {'allowed': False, 'reason': reason, 'veto_code': code}
