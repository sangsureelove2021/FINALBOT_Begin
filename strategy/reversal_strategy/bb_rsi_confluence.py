"""Bollinger + RSI confluence reversal — complementary to RSI extreme bounce."""

from typing import Dict, Any

from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    REVERSAL_STATES, BLOCKED_STATES,
    get_market_state, get_m5_df, calc_atr, calc_rsi, calc_bollinger,
    is_news_blackout, candle_metrics, apply_lifecycle_penalty,
    confidence_from_components, build_signal, build_no_setup,
)
from core.models.market_context import MarketContext


class BBRSIConfluenceStrategy(BaseStrategy):
    STRATEGY_NAME = "bb_rsi_confluence"

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
        rsi_prev = float(rsi.iloc[-2])
        mid, bb_upper, bb_lower = calc_bollinger(close)
        upper, lower, mid_val = float(bb_upper.iloc[-1]), float(bb_lower.iloc[-1]), float(mid.iloc[-1])
        bw = (upper - lower) / mid_val if mid_val else 0.0
        atr_val = float(calc_atr(df).iloc[-1])
        m = candle_metrics(df)

        # Require RSI turning + price near band (softer than extreme bounce)
        action = "NO_SETUP"
        near_lower = m["low"] <= lower * 1.0003
        near_upper = m["high"] >= upper * 0.9997

        if near_lower and rsi_val < 35 and rsi_val > rsi_prev and m["close"] > m["open"]:
            action = "CALL"
        elif near_upper and rsi_val > 65 and rsi_val < rsi_prev and m["close"] < m["open"]:
            action = "PUT"

        if action == "NO_SETUP":
            return build_no_setup(name, "NO_CONFLUENCE", state)

        wick = m["lower_wick"] if action == "CALL" else m["upper_wick"]
        band = lower if action == "CALL" else upper
        pen = abs((m["low"] if action == "CALL" else m["high"]) - band) / atr_val
        wick_ratio = wick / m["body"] if m["body"] > 0 else 0.0

        f_rsi = min(100.0, abs(50 - rsi_val) * 2.0)
        f_bw = min(100.0, bw * 5000)  # tighter bands = better for M5
        entry_score = apply_lifecycle_penalty(
            0.35 * f_rsi + 0.30 * min(100.0, wick_ratio * 35) + 0.35 * f_bw,
            lifecycle, state,
        )

        block_score = 15.0 if bw > 0.004 else 0.0
        if entry_score < 65:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        conf = confidence_from_components(wick_ratio, pen, f_rsi)
        return build_signal(
            name, action, entry_score, block_score, conf,
            {"rsi14": rsi_val, "bb_width": bw, "pattern": "BB_RSI_Confluence", "market_state": state},
        )
