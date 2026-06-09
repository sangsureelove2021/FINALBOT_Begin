"""Diagnose market states and raw strategy signals."""

import json
import sys
from collections import Counter, defaultdict
from datetime import timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.data.csv_data_adapter import CSVDataAdapter
from core.orchestration.context_builder import ContextBuilder
from core.engines.engine_setup import setup_engines
from scratch.run_strategy_backtest import STRATEGY_MAP, load_data

SAMPLE_EVERY = 6  # every 30 min on M5


def diagnose(symbol: str, days: int = 5):
    adapter = load_data(symbol)
    if not adapter:
        return {"error": "no data"}

    for tf in ("M1", "M5", "M15", "M60"):
        df = adapter.dfs[symbol][tf]
        if df.index.tzinfo is None:
            df.index = df.index.tz_localize(timezone.utc)

    builder = ContextBuilder(setup_engines())
    m5 = adapter.dfs[symbol]["M5"]
    end_ts = m5.index[-1]
    start_ts = end_ts - timedelta(days=days)
    window = m5.loc[start_ts:end_ts]

    states = Counter()
    raw_signals = Counter()
    filtered_signals = Counter()
    fail_reasons = defaultdict(Counter)
    strategies = [STRATEGY_MAP[n]() for n in STRATEGY_MAP]

    for i, ts in enumerate(window.index):
        if i % SAMPLE_EVERY != 0:
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

        state = "UNKNOWN"
        if isinstance(context.market_state, dict):
            state = context.market_state.get("state", "UNKNOWN")
        states[state] += 1

        m5_len = len(context.candles.get("M5", [])) if context.candles else 0

        for s in strategies:
            try:
                res = s.evaluate(context)
                action = res.get("action", "NO_SETUP")
                reason = res.get("fail_reason_code") or "OK"
                if action in ("CALL", "PUT"):
                    raw_signals[s.STRATEGY_NAME] += 1
                    entry = float(res.get("entry_score", 0))
                    block = float(res.get("block_score", 100))
                    conf = res.get("strategy_confidence", 0)
                    conf_pct = int(conf * 100) if conf <= 1 else int(conf)
                    if entry >= 72 and block < 40 and conf_pct >= 75:
                        filtered_signals[s.STRATEGY_NAME] += 1
                    else:
                        if entry < 72:
                            fail_reasons[s.STRATEGY_NAME]["LOW_ENTRY"] += 1
                        if block >= 40:
                            fail_reasons[s.STRATEGY_NAME]["HIGH_BLOCK"] += 1
                        if conf_pct < 75:
                            fail_reasons[s.STRATEGY_NAME]["LOW_CONF"] += 1
                elif reason != "OK":
                    fail_reasons[s.STRATEGY_NAME][reason] += 1
            except Exception as e:
                fail_reasons[s.STRATEGY_NAME][f"ERR:{e}"] += 1

    return {
        "symbol": symbol,
        "samples": sum(states.values()),
        "market_states": dict(states),
        "m5_candles_in_context_note": "checked per sample",
        "raw_call_put_signals": dict(raw_signals),
        "filtered_signals": dict(filtered_signals),
        "top_fail_reasons": {
            k: dict(v.most_common(5)) for k, v in fail_reasons.items() if v
        },
    }


if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "GBPUSD"
    print(json.dumps(diagnose(sym, 5), indent=2))
