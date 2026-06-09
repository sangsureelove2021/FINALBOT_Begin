"""
Replay Metrics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Performance metrics for backtest / replay runs.

Given a list of completed trades, computes win rate, profit factor,
expectancy, drawdown and streak statistics.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class TradeRecord:
    """One completed trade in a replay run."""
    symbol: str
    direction: str          # 'CALL' or 'PUT'
    pnl: float              # net profit/loss
    won: bool


@dataclass
class ReplayMetrics:
    """Aggregated performance metrics for a replay run."""

    trades: List[TradeRecord] = field(default_factory=list)

    def add(self, trade: TradeRecord) -> None:
        self.trades.append(trade)

    # ─── Core metrics ────────────────────────────────────────────
    @property
    def total_trades(self) -> int:
        return len(self.trades)

    @property
    def wins(self) -> int:
        return sum(1 for t in self.trades if t.won)

    @property
    def losses(self) -> int:
        return sum(1 for t in self.trades if not t.won)

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        return round(self.wins / self.total_trades * 100, 2)

    @property
    def total_pnl(self) -> float:
        return round(sum(t.pnl for t in self.trades), 2)

    @property
    def gross_profit(self) -> float:
        return round(sum(t.pnl for t in self.trades if t.pnl > 0), 2)

    @property
    def gross_loss(self) -> float:
        return round(abs(sum(t.pnl for t in self.trades if t.pnl < 0)), 2)

    @property
    def profit_factor(self) -> float:
        """Gross profit / gross loss. Infinity-safe."""
        if self.gross_loss == 0:
            return float("inf") if self.gross_profit > 0 else 0.0
        return round(self.gross_profit / self.gross_loss, 2)

    @property
    def expectancy(self) -> float:
        """Average pnl per trade."""
        if not self.trades:
            return 0.0
        return round(self.total_pnl / self.total_trades, 2)

    @property
    def max_drawdown(self) -> float:
        """Largest peak-to-trough drop of the cumulative equity curve."""
        peak, dd = 0.0, 0.0
        equity = 0.0
        for t in self.trades:
            equity += t.pnl
            peak = max(peak, equity)
            dd = max(dd, peak - equity)
        return round(dd, 2)

    @property
    def max_win_streak(self) -> int:
        return self._max_streak(won=True)

    @property
    def max_loss_streak(self) -> int:
        return self._max_streak(won=False)

    def _max_streak(self, won: bool) -> int:
        best = cur = 0
        for t in self.trades:
            if t.won == won:
                cur += 1
                best = max(best, cur)
            else:
                cur = 0
        return best

    def summary(self) -> Dict:
        """All metrics as a dict."""
        return {
            "total_trades": self.total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": self.win_rate,
            "total_pnl": self.total_pnl,
            "profit_factor": self.profit_factor,
            "expectancy": self.expectancy,
            "max_drawdown": self.max_drawdown,
            "max_win_streak": self.max_win_streak,
            "max_loss_streak": self.max_loss_streak,
        }
