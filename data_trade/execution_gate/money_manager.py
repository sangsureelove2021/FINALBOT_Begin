"""
Money Manager & Risk Control Engine for Part 3
==============================================
Manages position sizing (Fixed 35 THB), daily profit/loss limits,
consecutive loss protections, cooldown timers, and concurrent order limits.
"""

import os
import csv
import logging
from typing import Dict, Any, Optional, Tuple, Set
from datetime import datetime, timezone, timedelta

from config_setting.config_loader import load_settings

logger = logging.getLogger("MoneyManager")


class MoneyManager:
    """Calculates stake sizes and enforces strict capital preservation limits in Part 3."""

    DEFAULT_STAKE_PER_TRADE: float = 35.0
    DEFAULT_MAX_DAILY_PROFIT: float = 999999.0
    DEFAULT_MAX_DAILY_LOSS: float = 999999.0
    DEFAULT_MAX_CONSECUTIVE_LOSSES: int = 999999
    DEFAULT_MAX_CONCURRENT: int = 999999
    DEFAULT_COOLDOWN_MINUTES: int = 0

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.settings = config or {}
        acc_cfg = self.settings.get("account", {})
        
        # Native Part 3 Risk Limits
        self.stake_per_trade = float(acc_cfg.get("stake_per_trade", self.DEFAULT_STAKE_PER_TRADE))
        self.max_daily_profit = self.DEFAULT_MAX_DAILY_PROFIT
        self.max_daily_loss = self.DEFAULT_MAX_DAILY_LOSS
        self.max_consecutive_losses = self.DEFAULT_MAX_CONSECUTIVE_LOSSES
        self.max_concurrent = self.DEFAULT_MAX_CONCURRENT
        self.cooldown_minutes = self.DEFAULT_COOLDOWN_MINUTES

        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.active_orders: Set[str] = set()
        self.last_loss_time: Optional[datetime] = None
        self.trade_history_file = os.path.join("logs", "logs_data_trade", "trades_history.csv")

        self._load_today_history()

    def _load_today_history(self) -> None:
        """Parses today's trade records to initialize daily PnL and loss counters."""
        if not os.path.exists(self.trade_history_file):
            return

        tz_thailand = timezone(timedelta(hours=7))
        today_str = datetime.now(tz_thailand).strftime("%Y-%m-%d")

        try:
            with open(self.trade_history_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                today_pnl = 0.0
                consec_loss = 0
                last_loss = None

                for row in reader:
                    ts = row.get("timestamp", "")
                    if ts.startswith(today_str):
                        try:
                            profit = float(row.get("profit_amount", 0.0))
                            today_pnl += profit
                            res = str(row.get("result", "")).upper()
                            if res == "LOSE":
                                consec_loss += 1
                                last_loss = datetime.fromisoformat(ts)
                            elif res == "WIN":
                                consec_loss = 0
                        except (ValueError, TypeError):
                            pass

                self.daily_pnl = today_pnl
                self.consecutive_losses = consec_loss
                self.last_loss_time = last_loss
                logger.info(f"[MoneyManager] Synced today's history: PnL={self.daily_pnl:.2f}, ConsecLosses={self.consecutive_losses}")
        except Exception as e:
            logger.warning(f"[MoneyManager] Could not parse trade history file: {e}")

    def can_trade(self) -> Tuple[bool, str]:
        """
        Evaluates risk management constraints.
        
        Returns:
            Tuple[bool, str]: (is_allowed, reason_message)
        """
        # 1. Max Concurrent Trades
        if len(self.active_orders) >= self.max_concurrent:
            return False, f"ถึงจำนวนออเดอร์พร้อมกันสูงสุดแล้ว ({len(self.active_orders)}/{self.max_concurrent})"

        # 2. Daily Loss Limit
        if self.daily_pnl <= -abs(self.max_daily_loss):
            return False, f"แตะขีดจำกัดขาดทุนรายวัน (-{abs(self.daily_pnl):.2f} / Max -{self.max_daily_loss:.2f})"

        # 3. Daily Profit Limit
        if self.daily_pnl >= abs(self.max_daily_profit):
            return False, f"แตะเป้าหมายกำไรรายวัน (+{self.daily_pnl:.2f} / Target +{self.max_daily_profit:.2f})"

        # 4. Consecutive Loss Limit
        if self.consecutive_losses >= self.max_consecutive_losses:
            return False, f"แพ้ติดต่อกันเกินขีดจำกัด ({self.consecutive_losses}/{self.max_consecutive_losses})"

        # 5. Cooldown Timer
        if self.cooldown_minutes > 0 and self.last_loss_time is not None:
            tz_thailand = timezone(timedelta(hours=7))
            now = datetime.now(tz_thailand)
            diff_min = (now - self.last_loss_time).total_seconds() / 60.0
            if diff_min < self.cooldown_minutes:
                remaining = self.cooldown_minutes - diff_min
                return False, f"อยู่ในช่วง Cooldown หลังขาดทุน (เหลืออีก {remaining:.1f} นาที)"

        return True, "RISK_GATES_PASSED"

    def get_stake(self, symbol: str) -> float:
        """Returns the configured fixed stake for the order."""
        return float(self.stake_per_trade)

    def register_open_trade(self, order_id: str, symbol: str) -> None:
        """Registers a newly opened order in active orders tracking."""
        self.active_orders.add(str(order_id))

    def record_trade_result(self, order_id: str, profit_amount: float, result_status: str) -> None:
        """
        Updates internal risk metrics when an order finishes.
        
        Args:
            order_id: Order identifier.
            profit_amount: Net profit (positive) or loss (negative).
            result_status: 'WIN', 'LOSE', or 'EQUAL'.
        """
        order_str = str(order_id)
        if order_str in self.active_orders:
            self.active_orders.remove(order_str)

        self.daily_pnl += profit_amount
        norm_res = str(result_status).upper()

        if norm_res == "LOSE":
            self.consecutive_losses += 1
            tz_thailand = timezone(timedelta(hours=7))
            self.last_loss_time = datetime.now(tz_thailand)
        elif norm_res == "WIN":
            self.consecutive_losses = 0

        logger.info(
            f"[MoneyManager] Order {order_id} recorded: Result={norm_res}, "
            f"Profit={profit_amount:+.2f}, DailyPnL={self.daily_pnl:+.2f}, ConsecLoss={self.consecutive_losses}"
        )

    def get_risk_status(self) -> Dict[str, Any]:
        """Returns current risk status summary."""
        return {
            "stake_per_trade": self.stake_per_trade,
            "daily_pnl": round(self.daily_pnl, 2),
            "consecutive_losses": self.consecutive_losses,
            "active_orders_count": len(self.active_orders),
            "max_daily_loss": self.max_daily_loss,
            "max_daily_profit": self.max_daily_profit,
        }
