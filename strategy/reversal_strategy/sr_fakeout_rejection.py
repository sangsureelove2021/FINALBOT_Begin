"""Liquidity sweep / fakeout rejection at S/R — M5 binary."""

from typing import Dict, Any

from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    REVERSAL_STATES, BLOCKED_STATES,
    get_market_state, get_m5_df, calc_atr, cluster_sr_levels,
    is_news_blackout, candle_metrics, apply_lifecycle_penalty,
    confidence_from_components, build_signal, build_no_setup,
)
from core.models.market_context import MarketContext


class SRFakeoutRejection(BaseStrategy):
    STRATEGY_NAME = "sr_fakeout_rejection"

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        state, lifecycle = get_market_state(context)
        name = self.STRATEGY_NAME

        if state in BLOCKED_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state, hard_block=True)
        if state not in REVERSAL_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state)
        if is_news_blackout(context):
            return build_no_setup(name, "NEWS_BLACKOUT", state)

        df = get_m5_df(context)
        if df is None:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        supports, resistances = cluster_sr_levels(df)
        m = candle_metrics(df)
        atr_val = float(calc_atr(df).iloc[-1])
        prev = df.iloc[-2]

        action = "NO_SETUP"
        level = 0.0

        for sup in supports:
            if float(prev["low"]) > sup and m["low"] < sup and m["close"] > sup:
                action, level = "CALL", sup
                break

        if action == "NO_SETUP":
            for res in resistances:
                if float(prev["high"]) < res and m["high"] > res and m["close"] < res:
                    action, level = "PUT", res
                    break

        if action == "NO_SETUP":
            return build_no_setup(name, "NO_FAKEOUT", state)

        wick = m["lower_wick"] if action == "CALL" else m["upper_wick"]
        pen = abs((m["low"] if action == "CALL" else m["high"]) - level) / atr_val
        wick_ratio = wick / m["body"] if m["body"] > 0 else 0.0
        entry_score = apply_lifecycle_penalty(72.0 + min(20.0, pen * 40.0), lifecycle, state)

        if entry_score < 65:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        conf = confidence_from_components(wick_ratio, pen, entry_score)
        return build_signal(
            name, action, entry_score, 0.0, conf,
            {"level_touched": level, "pattern": "FakeoutRejection", "market_state": state},
        )
