"""Pin bar at local S/R — M5 binary reversal."""

from typing import Dict, Any

from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    REVERSAL_STATES, BLOCKED_STATES,
    get_market_state, get_m5_df, calc_atr, calc_rsi,
    is_news_blackout, candle_metrics, apply_lifecycle_penalty,
    confidence_from_components, build_signal, build_no_setup,
)
from core.models.market_context import MarketContext


class PinBarScalper(BaseStrategy):
    STRATEGY_NAME = "pin_bar_scalper"

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        state, lifecycle = get_market_state(context)
        name = self.STRATEGY_NAME

        if state in BLOCKED_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state, hard_block=True)
        if state not in REVERSAL_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state)
        if is_news_blackout(context):
            return build_no_setup(name, "NEWS_BLACKOUT", state)

        df = get_m5_df(context, 20)
        if df is None:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        m = candle_metrics(df)
        if m["height"] <= 0:
            return build_no_setup(name, "ZERO_HEIGHT_CANDLE", state)

        body_ratio = m["body"] / m["height"]
        if body_ratio < 0.08:
            return build_no_setup(name, "DOJI_CANDLE_INVALID", state)

        action, pattern = "NO_SETUP", "NONE"
        if m["lower_wick"] >= m["body"] * 1.8 and m["upper_wick"] <= m["body"] * 0.6 and m["bullish"]:
            action, pattern = "CALL", "Hammer"
        elif m["upper_wick"] >= m["body"] * 1.8 and m["lower_wick"] <= m["body"] * 0.6 and m["bearish"]:
            action, pattern = "PUT", "ShootingStar"

        if action == "NO_SETUP":
            return build_no_setup(name, "NO_PIN_BAR_PATTERN", state)

        rsi3 = float(calc_rsi(df["close"], 3).iloc[-1])
        if action == "CALL" and rsi3 > 35:
            return build_no_setup(name, "RSI_NOT_EXTREME", state)
        if action == "PUT" and rsi3 < 65:
            return build_no_setup(name, "RSI_NOT_EXTREME", state)

        local_sup = float(df["low"].iloc[-10:-1].min())
        local_res = float(df["high"].iloc[-10:-1].max())
        atr_val = float(calc_atr(df).iloc[-1])

        if action == "CALL":
            if abs(m["low"] - local_sup) / local_sup > 0.0008:
                return build_no_setup(name, "OUTSIDE_LOCAL_SR", state)
            level = local_sup
        else:
            if abs(m["high"] - local_res) / local_res > 0.0008:
                return build_no_setup(name, "OUTSIDE_LOCAL_SR", state)
            level = local_res

        wick = m["lower_wick"] if action == "CALL" else m["upper_wick"]
        wick_ratio = wick / m["body"] if m["body"] > 0 else 0.0
        pen = abs((m["low"] if action == "CALL" else m["high"]) - level) / atr_val
        entry_score = apply_lifecycle_penalty(78.0 + min(15.0, wick_ratio * 5.0), lifecycle, state)

        if entry_score < 65:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        conf = confidence_from_components(wick_ratio, pen, 70.0)
        return build_signal(
            name, action, entry_score, 0.0, conf,
            {"level_touched": level, "pattern": pattern, "wick_ratio": wick_ratio, "market_state": state},
        )
