"""EMA 8/21 crossover with momentum — M5 binary mild-trend plays."""

from typing import Dict, Any

from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    MOMENTUM_STATES, BLOCKED_STATES,
    get_market_state, get_m5_df, calc_atr, calc_adx,
    is_news_blackout, candle_metrics, apply_lifecycle_penalty,
    confidence_from_components, build_signal, build_no_setup,
)
from core.models.market_context import MarketContext


class EMACrossoverStrategy(BaseStrategy):
    STRATEGY_NAME = "ema_crossover"

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        state, lifecycle = get_market_state(context)
        name = self.STRATEGY_NAME

        if state in BLOCKED_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state, hard_block=True)
        if state not in MOMENTUM_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state)
        if is_news_blackout(context):
            return build_no_setup(name, "NEWS_BLACKOUT", state)

        df = get_m5_df(context)
        if df is None:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        close = df["close"]
        ema8 = close.ewm(span=8, adjust=False).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()
        e8_now, e21_now = float(ema8.iloc[-1]), float(ema21.iloc[-1])
        e8_prev, e21_prev = float(ema8.iloc[-2]), float(ema21.iloc[-2])
        adx = calc_adx(df)
        m = candle_metrics(df)
        atr_val = float(calc_atr(df).iloc[-1])

        if adx < 18 or adx > 35:
            return build_no_setup(name, "ADX_OUT_OF_RANGE", state)
        if m["body"] < 0.12 * atr_val:
            return build_no_setup(name, "CANDLE_BODY_TOO_SMALL", state)

        action = "NO_SETUP"
        if e8_prev <= e21_prev and e8_now > e21_now and m["bullish"]:
            action = "CALL"
        elif e8_prev >= e21_prev and e8_now < e21_now and m["bearish"]:
            action = "PUT"

        if action == "NO_SETUP":
            return build_no_setup(name, "NO_CROSSOVER_DETECTED", state)

        sep = abs(e8_now - e21_now) / atr_val
        entry_score = apply_lifecycle_penalty(72.0 + min(20.0, sep * 80.0), lifecycle, state)
        if entry_score < 65:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        conf = confidence_from_components(sep * 3, sep, entry_score)
        return build_signal(
            name, action, entry_score, 0.0, conf,
            {"ema8": e8_now, "ema21": e21_now, "adx": adx, "pattern": "EMA_Cross", "market_state": state},
        )
