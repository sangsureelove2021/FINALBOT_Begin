"""EMA ribbon alignment + pullback entry — M5 binary."""

from typing import Dict, Any

from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    MOMENTUM_STATES, BLOCKED_STATES,
    get_market_state, get_m5_df, calc_atr, calc_adx,
    is_news_blackout, candle_metrics, apply_lifecycle_penalty,
    confidence_from_components, build_signal, build_no_setup,
)
from core.models.market_context import MarketContext


class EMARibbonMomentumStrategy(BaseStrategy):
    STRATEGY_NAME = "ema_ribbon_momentum"

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        state, lifecycle = get_market_state(context)
        name = self.STRATEGY_NAME

        if state in BLOCKED_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state, hard_block=True)
        if state not in MOMENTUM_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state)

        df = get_m5_df(context)
        if df is None:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        close = df["close"]
        e8 = close.ewm(span=8, adjust=False).mean()
        e13 = close.ewm(span=13, adjust=False).mean()
        e21 = close.ewm(span=21, adjust=False).mean()
        v8, v13, v21 = float(e8.iloc[-1]), float(e13.iloc[-1]), float(e21.iloc[-1])
        price = float(close.iloc[-1])
        adx = calc_adx(df)
        m = candle_metrics(df)
        atr_val = float(calc_atr(df).iloc[-1])

        if adx < 22:
            return build_no_setup(name, "ADX_TOO_LOW", state)

        action = "NO_SETUP"
        if v8 > v13 > v21 and price >= v13 and m["low"] <= v8 and m["bullish"]:
            action = "CALL"
        elif v8 < v13 < v21 and price <= v13 and m["high"] >= v8 and m["bearish"]:
            action = "PUT"

        if action == "NO_SETUP":
            return build_no_setup(name, "NO_RIBBON_PULLBACK", state)

        entry_score = apply_lifecycle_penalty(74.0 + min(18.0, adx - 20), lifecycle, state)
        if entry_score < 65:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        conf = confidence_from_components((adx - 20) / 20, 0.1, entry_score)
        return build_signal(
            name, action, entry_score, 0.0, conf,
            {"ema8": v8, "ema13": v13, "ema21": v21, "pattern": "RibbonPullback", "market_state": state},
        )
