"""Price action at S/R levels — M5 binary."""

from typing import Dict, Any

from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    REVERSAL_STATES, BLOCKED_STATES,
    get_market_state, get_m5_df, calc_atr, cluster_sr_levels,
    is_news_blackout, candle_metrics, apply_lifecycle_penalty,
    confidence_from_components, build_signal, build_no_setup,
)
from core.models.market_context import MarketContext


class PASNRStrategy(BaseStrategy):
    STRATEGY_NAME = "pa_snr"

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        state, lifecycle = get_market_state(context)
        name = self.STRATEGY_NAME

        if state in BLOCKED_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state, hard_block=True)
        if state not in REVERSAL_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state)
        if is_news_blackout(context):
            return build_no_setup(name, "NEWS_BLACKOUT", state)

        df = get_m5_df(context, 35)
        if df is None:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        supports, resistances = cluster_sr_levels(df, lookback=35)
        m = candle_metrics(df)
        atr_val = float(calc_atr(df).iloc[-1])

        action = "NO_SETUP"
        level = 0.0
        for sup in supports:
            if abs(m["low"] - sup) / sup <= 0.0006 and m["close"] > sup and m["bullish"]:
                action, level = "CALL", sup
                break
        if action == "NO_SETUP":
            for res in resistances:
                if abs(m["high"] - res) / res <= 0.0006 and m["close"] < res and m["bearish"]:
                    action, level = "PUT", res
                    break

        if action == "NO_SETUP":
            return build_no_setup(name, "NO_PA_SNR", state)

        pen = abs((m["low"] if action == "CALL" else m["high"]) - level) / atr_val
        wick = m["lower_wick"] if action == "CALL" else m["upper_wick"]
        wick_ratio = wick / m["body"] if m["body"] > 0 else 0.0
        entry_score = apply_lifecycle_penalty(70.0 + min(25.0, wick_ratio * 6.0), lifecycle, state)

        if entry_score < 65:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        conf = confidence_from_components(wick_ratio, pen, entry_score)
        return build_signal(
            name, action, entry_score, 0.0, conf,
            {"level_touched": level, "pattern": "PA_SNR", "market_state": state},
        )
