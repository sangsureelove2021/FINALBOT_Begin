"""RSI + Bollinger extreme bounce — M5 binary mean reversion."""

from typing import Dict, Any

from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    REVERSAL_STATES, BLOCKED_STATES,
    get_market_state, get_m5_df, calc_atr, calc_rsi, calc_bollinger,
    is_news_blackout, candle_metrics, apply_lifecycle_penalty,
    confidence_from_components, build_signal, build_no_setup,
)
from core.models.market_context import MarketContext


class RSIExtremeBounceStrategy(BaseStrategy):
    STRATEGY_NAME = "rsi_extreme_bounce"

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

        close = df["close"]
        rsi = calc_rsi(close, 14)
        rsi_val = float(rsi.iloc[-1])
        _, bb_upper, bb_lower = calc_bollinger(close)
        upper, lower = float(bb_upper.iloc[-1]), float(bb_lower.iloc[-1])
        atr_val = float(calc_atr(df).iloc[-1])
        m = candle_metrics(df)

        action = "NO_SETUP"
        if rsi_val <= 28 and m["low"] <= lower and m["close"] > lower and m["bullish"]:
            action = "CALL"
        elif rsi_val >= 72 and m["high"] >= upper and m["close"] < upper and m["bearish"]:
            action = "PUT"

        if action == "NO_SETUP":
            return build_no_setup(name, "NO_EXTREME_BOUNCE", state)

        band = lower if action == "CALL" else upper
        wick = m["lower_wick"] if action == "CALL" else m["upper_wick"]
        pen = abs((m["low"] if action == "CALL" else m["high"]) - band) / atr_val
        wick_ratio = wick / m["body"] if m["body"] > 0 else 0.0

        rsi_extreme = (28 - rsi_val) / 28 if action == "CALL" else (rsi_val - 72) / 28
        f_rsi = min(100.0, max(0.0, rsi_extreme * 100.0))
        f_wick = min(100.0, wick_ratio * 40.0)
        f_pen = min(100.0, pen / 0.25 * 100.0)
        entry_score = apply_lifecycle_penalty(0.40 * f_rsi + 0.35 * f_wick + 0.25 * f_pen, lifecycle, state)

        block_score = 0.0
        if state == "EXHAUSTION_ZONE" and entry_score < 75:
            block_score += 15.0
        if m["body"] < 0.03 * atr_val:
            block_score += 30.0

        if entry_score < 65 or block_score >= 45:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        conf = confidence_from_components(wick_ratio, pen, f_rsi)
        return build_signal(
            name, action, entry_score, block_score, conf,
            {"rsi14": rsi_val, "pattern": "RSI_BB_Bounce", "market_state": state},
        )
