"""
Broker Adapter
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A thin, broker-agnostic abstraction layer over a concrete executor.

Purpose:
    The rest of the system should not depend directly on IQ Option.
    BrokerAdapter exposes one stable interface (place_order, get_balance,
    close, ...) so a different broker can be swapped in later without
    touching strategy, risk, or runner code.

Default mode is MOCK: no real orders are placed. To trade live, the
concrete executor must be connected with valid credentials.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Optional, List

from execution.iq_option_executor import IQOptionExecutor, OrderResult

logger = logging.getLogger(__name__)


class BrokerAdapter:
    """Broker-agnostic wrapper around a concrete trade executor."""

    def __init__(self,
                 executor: Optional[IQOptionExecutor] = None,
                 use_mock: bool = True,
                 starting_balance: float = 2000.0):
        """
        Args:
            executor: concrete executor. If None, an IQOptionExecutor is built.
            use_mock: when True, no real orders are sent.
            starting_balance: account balance used for mock accounting.
        """
        self.use_mock = use_mock
        self.executor = executor or IQOptionExecutor(use_mock=use_mock)
        self._balance = starting_balance
        self._orders: List[Dict] = []

    # ─── Connection ──────────────────────────────────────────────
    def is_connected(self) -> bool:
        """True if the underlying executor has a live broker connection."""
        try:
            return self.executor.is_connected()
        except Exception:
            return False

    def mode(self) -> str:
        return "MOCK" if (self.use_mock or not self.is_connected()) else "LIVE"

    # ─── Trading ─────────────────────────────────────────────────
    def place_order(self, symbol: str, direction: str,
                    amount: float, expiry: str = "M5") -> OrderResult:
        """
        Place a binary-option order through the executor.

        Args:
            symbol: trading pair, e.g. 'EURUSD-OTC'.
            direction: 'CALL' (up) or 'PUT' (down).
            amount: stake size.
            expiry: option duration, e.g. 'M1', 'M5'.

        Returns:
            OrderResult from the executor.
        """
        if direction not in ("CALL", "PUT"):
            return OrderResult(
                order_id="INVALID", symbol=symbol, direction=direction,
                amount=amount, expiry=expiry, status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                reason=f"Invalid direction: {direction}",
            )

        if amount <= 0:
            return OrderResult(
                order_id="INVALID", symbol=symbol, direction=direction,
                amount=amount, expiry=expiry, status="failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
                reason=f"Invalid amount: {amount}",
            )

        result = self.executor.send_order(symbol, direction, amount, expiry)

        self._orders.append({
            "order_id": result.order_id,
            "symbol": symbol,
            "direction": direction,
            "amount": amount,
            "expiry": expiry,
            "status": result.status,
            "timestamp": result.timestamp,
        })

        # Mock accounting: reserve stake on a pending order
        if self.use_mock and result.status in ("pending", "executed"):
            self._balance -= amount

        return result

    def settle(self, order_id: str, won: bool, payout_ratio: float = 0.85) -> float:
        """
        Settle a mock order and update the mock balance.

        Args:
            order_id: id returned by place_order.
            won: True if the option finished in the money.
            payout_ratio: broker payout on a win (e.g. 0.85 = 85%).

        Returns:
            Net profit/loss applied to the balance for this order.
        """
        order = next((o for o in self._orders if o["order_id"] == order_id), None)
        if order is None:
            return 0.0

        amount = order["amount"]
        if won:
            gain = amount + amount * payout_ratio   # stake back + profit
            self._balance += gain
            pnl = amount * payout_ratio
        else:
            pnl = -amount                           # stake already deducted
        order["status"] = "won" if won else "lost"
        return pnl

    # ─── Account ─────────────────────────────────────────────────
    def get_balance(self) -> float:
        """Current account balance (mock balance in mock mode)."""
        return self._balance

    def get_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Return placed orders, optionally filtered by symbol."""
        if symbol is None:
            return list(self._orders)
        return [o for o in self._orders if o["symbol"] == symbol]

    def get_stats(self) -> Dict:
        """Summary statistics for placed orders."""
        wins = sum(1 for o in self._orders if o["status"] == "won")
        losses = sum(1 for o in self._orders if o["status"] == "lost")
        total = len(self._orders)
        return {
            "total_orders": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / (wins + losses) * 100, 1) if (wins + losses) else 0.0,
            "balance": round(self._balance, 2),
            "mode": self.mode(),
        }
