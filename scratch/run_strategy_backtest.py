"""
Fast M5-only multi-strategy backtest using CSV historical data.
Usage:
  python scratch/run_strategy_backtest.py GBPUSD 5
  python scratch/run_strategy_backtest.py EURUSD-OTC 5 --per-strategy
"""

import json
import sys
from datetime import timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.config_loader import load_settings
from core.data.csv_data_adapter import CSVDataAdapter
from core.orchestration.context_builder import ContextBuilder
from core.engines.engine_setup import setup_engines
from strategy.reversal_strategy.rejection_5m_pa import Rejection5mPA
from strategy.reversal_strategy.rsi_extreme_bounce import RSIExtremeBounceStrategy
from strategy.reversal_strategy.bb_rsi_confluence import BBRSIConfluenceStrategy
from strategy.reversal_strategy.pin_bar_scalper import PinBarScalper
from strategy.reversal_strategy.sr_fakeout_rejection import SRFakeoutRejection
from strategy.reversal_strategy.stochastic_crossover import StochasticCrossoverStrategy
from strategy.reversal_strategy.engulfing_scalper import EngulfingScalperStrategy
from strategy.reversal_strategy.rsi_reversal import RSIReversalStrategy
from strategy.reversal_strategy.pa_snr_strategy import PASNRStrategy
from strategy.trend_following.ema_crossover import EMACrossoverStrategy
from strategy.trend_following.macd_crossover import MACDCrossoverStrategy
from strategy.trend_following.ema_ribbon_momentum import EMARibbonMomentumStrategy
from strategy.trend_following.triple_confluence import TripleConfluenceStrategy
from strategy.compression_breakout.strategy import CompressionBreakoutStrategy
from strategy.m5_binary_core import passes_quality_gate

STRATEGY_MAP = {
    "rejection_5m_pa": Rejection5mPA,
    "rsi_extreme_bounce": RSIExtremeBounceStrategy,
    "bb_rsi_confluence": BBRSIConfluenceStrategy,
    "pin_bar_scalper": PinBarScalper,
    "sr_fakeout_rejection": SRFakeoutRejection,
    "stochastic_crossover": StochasticCrossoverStrategy,
    "engulfing_scalper": EngulfingScalperStrategy,
    "rsi_reversal": RSIReversalStrategy,
    "pa_snr": PASNRStrategy,
    "ema_crossover": EMACrossoverStrategy,
    "macd_crossover": MACDCrossoverStrategy,
    "ema_ribbon_momentum": EMARibbonMomentumStrategy,
    "triple_confluence": TripleConfluenceStrategy,
    "compression_breakout": CompressionBreakoutStrategy,
}

STAKE = 35.0
PAYOUT = 0.85
MIN_ENTRY = 68.0
MAX_BLOCK = 45.0
MIN_CONF = 72


def load_data(symbol: str):
    for data_dir in ("Active_Pairs_Grabber/historical_data", "historical_data"):
        adapter = CSVDataAdapter(data_dir=str(PROJECT_ROOT / data_dir))
        if adapter.load_symbol_data(symbol, ["M1", "M5", "M15", "M60"]):
            return adapter
    return None


def evaluate_best(strategies, context):
    best = None
    best_score = -1
    for s in strategies:
        try:
            res = s.evaluate(context)
            action = res.get("action", "NO_SETUP")
            if action not in ("CALL", "PUT"):
                continue
            entry = float(res.get("entry_score", 0))
            block = float(res.get("block_score", 100))
            conf = float(res.get("strategy_confidence", 0))
            if not passes_quality_gate(entry, block, conf, MIN_ENTRY, MAX_BLOCK, MIN_CONF):
                continue
            score = entry - block * 0.5
            if score > best_score:
                best_score = score
                conf_pct = int(conf * 100) if conf <= 1 else int(conf)
                best = (s.STRATEGY_NAME, action, entry, conf_pct)
        except Exception:
            pass
    return best


def _simulate(symbol: str, days: int, strategies, strategy_label: str):
    adapter = load_data(symbol)
    if adapter is None:
        return {"error": f"No CSV data for {symbol}"}

    for tf in ("M1", "M5", "M15", "M60"):
        df = adapter.dfs[symbol][tf]
        if df.index.tzinfo is None:
            df.index = df.index.tz_localize(timezone.utc)
        else:
            df.index = df.index.tz_convert(timezone.utc)

    builder = ContextBuilder(setup_engines())
    m5 = adapter.dfs[symbol]["M5"]
    m1 = adapter.dfs[symbol]["M1"]
    end_ts = m5.index[-1]
    start_ts = end_ts - timedelta(days=days)
    m5_window = m5.loc[start_ts:end_ts]

    balance = 2000.0
    wins = losses = 0
    open_trade = None

    for ts in m5_window.index:
        if open_trade:
            expiry_ts = open_trade["entry_ts"] + timedelta(minutes=5)
            if ts >= expiry_ts:
                idx = m1.index.searchsorted(expiry_ts, side="right") - 1
                idx = max(0, min(idx, len(m1) - 1))
                exit_price = float(m1.iloc[idx]["close"])
                won = (
                    exit_price > open_trade["entry"]
                    if open_trade["action"] == "CALL"
                    else exit_price < open_trade["entry"]
                )
                pnl = STAKE * PAYOUT if won else -STAKE
                balance += pnl
                if won:
                    wins += 1
                else:
                    losses += 1
                open_trade = None

        if open_trade:
            continue

        adapter.set_simulated_time(ts.to_pydatetime())
        candles = {
            tf: adapter.get_candles(symbol, tf, 300 if tf in ("M1", "M5") else 100)
            for tf in ("M1", "M5", "M15", "M60")
        }
        from core.data.timeframe_sync import TimeframeSync
        synced = TimeframeSync(primary="M1").sync(candles)
        for tf in list(synced.keys()):
            if len(synced[tf]) > 1:
                synced[tf] = synced[tf].iloc[:-1]

        context = builder.build(symbol, synced, "M1")
        if not context:
            continue

        best = evaluate_best(strategies, context)
        if not best:
            continue

        _, action, _, _ = best
        entry_idx = m1.index.searchsorted(ts, side="right") - 1
        entry_idx = max(0, min(entry_idx, len(m1) - 1))
        entry_price = float(m1.iloc[entry_idx]["close"])
        open_trade = {
            "action": action,
            "entry": entry_price,
            "entry_ts": ts.to_pydatetime().replace(tzinfo=timezone.utc),
        }

    total = wins + losses
    return {
        "strategy": strategy_label,
        "trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / total * 100, 2) if total else 0.0,
        "pnl": round(balance - 2000.0, 2),
    }


def run_backtest(symbol: str, days: int = 5, per_strategy: bool = False):
    settings = load_settings()
    names = settings.get("active_strategies", ["rejection_5m_pa"])

    if per_strategy:
        results = []
        for n in STRATEGY_MAP:
            if n not in STRATEGY_MAP:
                continue
            r = _simulate(symbol, days, [STRATEGY_MAP[n]()], n)
            if r.get("trades", 0) > 0:
                results.append(r)
        results.sort(key=lambda x: (-x["win_rate"], -x["pnl"]))
        combined = _simulate(symbol, days, [STRATEGY_MAP[n]() for n in names if n in STRATEGY_MAP], "combined_active")
        return {
            "symbol": symbol,
            "days": days,
            "active_strategies": names,
            "combined": combined,
            "per_strategy": results,
            "breakeven_wr": 54.05,
        }

    strategies = [STRATEGY_MAP[n]() for n in names if n in STRATEGY_MAP]
    r = _simulate(symbol, days, strategies, "combined")
    return {
        "symbol": symbol,
        "days": days,
        "strategies_active": names,
        "trades": r["trades"],
        "wins": r["wins"],
        "losses": r["losses"],
        "win_rate": r["win_rate"],
        "pnl": r["pnl"],
        "balance": round(2000.0 + r["pnl"], 2),
        "breakeven_wr": 54.05,
    }


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    per_strategy = "--per-strategy" in sys.argv
    symbol = args[0] if args else "GBPUSD"
    days = int(args[1]) if len(args) > 1 else 5
    print(json.dumps(run_backtest(symbol, days, per_strategy), indent=2, ensure_ascii=False))
