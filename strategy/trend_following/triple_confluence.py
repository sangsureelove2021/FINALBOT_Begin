"""EMA + MACD + RSI triple alignment — M5 binary."""

from typing import Dict, Any

from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    MOMENTUM_STATES, BLOCKED_STATES,
    get_market_state, get_m5_df, calc_atr, calc_rsi, calc_adx,
    is_news_blackout, candle_metrics, apply_lifecycle_penalty,
    confidence_from_components, build_signal, build_no_setup,
)
from core.models.market_context import MarketContext


class TripleConfluenceStrategy(BaseStrategy):
    STRATEGY_NAME = "triple_confluence"

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
        ema20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
        price = float(close.iloc[-1])
        rsi = float(calc_rsi(close, 14).iloc[-1])
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        m_now, s_now = float(macd.iloc[-1]), float(signal.iloc[-1])
        m = candle_metrics(df)

        action = "NO_SETUP"
        if price > ema20 and rsi > 48 and m_now > s_now and m["bullish"]:
            action = "CALL"
        elif price < ema20 and rsi < 52 and m_now < s_now and m["bearish"]:
            action = "PUT"

        if action == "NO_SETUP":
            return build_no_setup(name, "NO_CONFLUENCE", state)

        align = (abs(rsi - 50) / 50 + abs(m_now - s_now) / float(calc_atr(df).iloc[-1])) / 2
        entry_score = apply_lifecycle_penalty(72.0 + min(25.0, align * 30), lifecycle, state)
        if entry_score < 65:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        conf = confidence_from_components(align, 0.1, entry_score)
        return build_signal(
            name, action, entry_score, 0.0, conf,
            {"rsi14": rsi, "ema20": ema20, "pattern": "TripleConfluence", "market_state": state},
        )
