"""MACD signal-line crossover — M5 binary momentum."""

from typing import Dict, Any

from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    MOMENTUM_STATES, BLOCKED_STATES,
    get_market_state, get_m5_df, calc_atr, calc_adx,
    is_news_blackout, candle_metrics, apply_lifecycle_penalty,
    confidence_from_components, build_signal, build_no_setup,
)
from core.models.market_context import MarketContext


class MACDCrossoverStrategy(BaseStrategy):
    STRATEGY_NAME = "macd_crossover"

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
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal

        m_now, s_now, h_now = float(macd.iloc[-1]), float(signal.iloc[-1]), float(hist.iloc[-1])
        m_prev, s_prev, h_prev = float(macd.iloc[-2]), float(signal.iloc[-2]), float(hist.iloc[-2])
        adx = calc_adx(df)
        m = candle_metrics(df)

        if adx < 20 or adx > 38:
            return build_no_setup(name, "ADX_OUT_OF_RANGE", state)

        action = "NO_SETUP"
        if m_prev <= s_prev and m_now > s_now and h_now > h_prev and m["bullish"]:
            action = "CALL"
        elif m_prev >= s_prev and m_now < s_now and h_now < h_prev and m["bearish"]:
            action = "PUT"

        if action == "NO_SETUP":
            return build_no_setup(name, "NO_MACD_CROSS", state)

        hist_gain = abs(h_now - h_prev)
        atr_val = float(calc_atr(df).iloc[-1])
        entry_score = apply_lifecycle_penalty(73.0 + min(22.0, hist_gain / atr_val * 200), lifecycle, state)
        if entry_score < 65:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        conf = confidence_from_components(hist_gain / atr_val, 0.1, entry_score)
        return build_signal(
            name, action, entry_score, 0.0, conf,
            {"macd": m_now, "macd_signal": s_now, "pattern": "MACD_Cross", "market_state": state},
        )
