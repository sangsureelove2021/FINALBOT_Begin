"""Engulfing pattern at range boundary — M5 binary."""

from typing import Dict, Any

from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    REVERSAL_STATES, BLOCKED_STATES,
    get_market_state, get_m5_df, calc_atr, calc_bollinger,
    is_news_blackout, apply_lifecycle_penalty,
    confidence_from_components, build_signal, build_no_setup,
)
from core.models.market_context import MarketContext


class EngulfingScalperStrategy(BaseStrategy):
    STRATEGY_NAME = "engulfing_scalper"

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        state, lifecycle = get_market_state(context)
        name = self.STRATEGY_NAME

        if state in BLOCKED_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state, hard_block=True)
        if state not in REVERSAL_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state)
        if is_news_blackout(context):
            return build_no_setup(name, "NEWS_BLACKOUT", state)

        df = get_m5_df(context, 25)
        if df is None:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        prev, curr = df.iloc[-2], df.iloc[-1]
        prev_body = abs(prev["close"] - prev["open"])
        curr_body = abs(curr["close"] - curr["open"])
        atr_val = float(calc_atr(df).iloc[-1])
        _, bb_upper, bb_lower = calc_bollinger(df["close"])
        upper, lower = float(bb_upper.iloc[-1]), float(bb_lower.iloc[-1])

        action = "NO_SETUP"
        bullish_engulf = (
            prev["close"] < prev["open"]
            and curr["close"] > curr["open"]
            and curr["open"] <= prev["close"]
            and curr["close"] >= prev["open"]
            and curr_body > prev_body * 1.1
            and float(curr["low"]) <= lower * 1.0005
        )
        bearish_engulf = (
            prev["close"] > prev["open"]
            and curr["close"] < curr["open"]
            and curr["open"] >= prev["close"]
            and curr["close"] <= prev["open"]
            and curr_body > prev_body * 1.1
            and float(curr["high"]) >= upper * 0.9995
        )

        if bullish_engulf:
            action = "CALL"
        elif bearish_engulf:
            action = "PUT"

        if action == "NO_SETUP":
            return build_no_setup(name, "NO_ENGULFING", state)

        engulf_ratio = curr_body / prev_body if prev_body > 0 else 0.0
        entry_score = apply_lifecycle_penalty(68.0 + min(25.0, engulf_ratio * 8.0), lifecycle, state)

        if entry_score < 65 or curr_body < 0.12 * atr_val:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        conf = confidence_from_components(engulf_ratio, 0.15, entry_score)
        return build_signal(
            name, action, entry_score, 0.0, conf,
            {"engulf_ratio": engulf_ratio, "pattern": "Engulfing", "market_state": state},
        )
