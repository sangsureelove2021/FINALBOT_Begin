"""RSI(7) reversal from midline stretch — lighter trigger than extreme bounce."""

from typing import Dict, Any

from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    REVERSAL_STATES, BLOCKED_STATES,
    get_market_state, get_m5_df, calc_rsi, calc_atr,
    is_news_blackout, candle_metrics, apply_lifecycle_penalty,
    confidence_from_components, build_signal, build_no_setup,
)
from core.models.market_context import MarketContext


class RSIReversalStrategy(BaseStrategy):
    STRATEGY_NAME = "rsi_reversal"

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        state, lifecycle = get_market_state(context)
        name = self.STRATEGY_NAME

        if state in BLOCKED_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state, hard_block=True)
        if state not in REVERSAL_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state)

        df = get_m5_df(context)
        if df is None:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        rsi = calc_rsi(df["close"], 7)
        r_now, r_prev = float(rsi.iloc[-1]), float(rsi.iloc[-2])
        m = candle_metrics(df)

        action = "NO_SETUP"
        if r_prev < 32 and r_now > r_prev and r_now < 45 and m["bullish"]:
            action = "CALL"
        elif r_prev > 68 and r_now < r_prev and r_now > 55 and m["bearish"]:
            action = "PUT"

        if action == "NO_SETUP":
            return build_no_setup(name, "NO_RSI_REVERSAL", state)

        stretch = abs(50 - r_prev) / 50
        entry_score = apply_lifecycle_penalty(70.0 + stretch * 25.0, lifecycle, state)
        if entry_score < 65:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        conf = confidence_from_components(stretch * 2, 0.1, entry_score)
        return build_signal(
            name, action, entry_score, 0.0, conf,
            {"rsi7": r_now, "pattern": "RSI_Reversal", "market_state": state},
        )
