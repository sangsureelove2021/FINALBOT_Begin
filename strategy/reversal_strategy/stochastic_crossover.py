"""Stochastic crossover from OB/OS zones — M5 binary."""

from typing import Dict, Any

from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    REVERSAL_STATES, BLOCKED_STATES,
    get_market_state, get_m5_df, calc_atr, calc_stochastic,
    is_news_blackout, candle_metrics, apply_lifecycle_penalty,
    confidence_from_components, build_signal, build_no_setup,
)
from core.models.market_context import MarketContext


class StochasticCrossoverStrategy(BaseStrategy):
    STRATEGY_NAME = "stochastic_crossover"

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

        k, d = calc_stochastic(df)
        k_now, d_now = float(k.iloc[-1]), float(d.iloc[-1])
        k_prev, d_prev = float(k.iloc[-2]), float(d.iloc[-2])
        atr_val = float(calc_atr(df).iloc[-1])
        m = candle_metrics(df)

        action = "NO_SETUP"
        if k_prev < d_prev and k_now > d_now and k_prev < 25 and k_now < 35:
            action = "CALL"
        elif k_prev > d_prev and k_now < d_now and k_prev > 75 and k_now > 65:
            action = "PUT"

        if action == "NO_SETUP":
            return build_no_setup(name, "NO_STOCH_CROSS", state)

        wick = m["lower_wick"] if action == "CALL" else m["upper_wick"]
        opp_wick = m["upper_wick"] if action == "CALL" else m["lower_wick"]
        if opp_wick > wick:
            return build_no_setup(name, "OPPOSITE_WICK_DOMINANCE", state, hard_block=True)

        wick_ratio = wick / m["body"] if m["body"] > 0 else 0.0
        depth = (25 - k_prev) / 25 if action == "CALL" else (k_prev - 75) / 25
        entry_score = apply_lifecycle_penalty(
            70.0 + depth * 20.0 + min(10.0, wick_ratio * 3.0), lifecycle, state
        )

        if entry_score < 65:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        conf = confidence_from_components(wick_ratio, depth * 0.2, entry_score)
        return build_signal(
            name, action, entry_score, 0.0, conf,
            {"stoch_k": k_now, "stoch_d": d_now, "pattern": "StochCross", "market_state": state},
        )
