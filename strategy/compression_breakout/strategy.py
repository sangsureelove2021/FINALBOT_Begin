"""Bollinger squeeze breakout — M5 binary momentum burst."""

from typing import Dict, Any

from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    MOMENTUM_STATES, BLOCKED_STATES,
    get_market_state, get_m5_df, calc_atr, calc_bollinger,
    is_news_blackout, candle_metrics, apply_lifecycle_penalty,
    confidence_from_components, build_signal, build_no_setup,
)
from core.models.market_context import MarketContext


class CompressionBreakoutStrategy(BaseStrategy):
    STRATEGY_NAME = "compression_breakout"

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        state, lifecycle = get_market_state(context)
        name = self.STRATEGY_NAME

        if state in BLOCKED_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state, hard_block=True)
        if state not in MOMENTUM_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state)

        df = get_m5_df(context, 60)
        if df is None:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        close = df["close"]
        mid, upper, lower = calc_bollinger(close)
        bw = (upper - lower) / mid.replace(0, 1e-9)
        curr_bw = float(bw.iloc[-1])
        avg_bw = float(bw.iloc[-20:-1].mean())
        prev_bw = float(bw.iloc[-2])
        atr_val = float(calc_atr(df).iloc[-1])
        m = candle_metrics(df)

        if curr_bw > avg_bw * 0.95:
            return build_no_setup(name, "NOT_COMPRESSED", state)
        if curr_bw <= prev_bw:
            return build_no_setup(name, "NO_EXPANSION", state)

        u, l, mid_val = float(upper.iloc[-1]), float(lower.iloc[-1]), float(mid.iloc[-1])
        action = "NO_SETUP"
        if m["close"] > u and m["body"] > 0.25 * atr_val and m["bullish"]:
            action = "CALL"
        elif m["close"] < l and m["body"] > 0.25 * atr_val and m["bearish"]:
            action = "PUT"

        if action == "NO_SETUP":
            return build_no_setup(name, "NO_BREAKOUT", state)

        expansion = (curr_bw - prev_bw) / (prev_bw + 1e-9)
        entry_score = apply_lifecycle_penalty(75.0 + min(20.0, expansion * 100), lifecycle, state)
        if entry_score < 68:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        conf = confidence_from_components(expansion * 5, m["body"] / atr_val, entry_score)
        return build_signal(
            name, action, entry_score, 10.0, conf,
            {"bb_width": curr_bw, "pattern": "CompressionBreakout", "market_state": state},
        )
