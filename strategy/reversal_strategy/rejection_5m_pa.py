"""S/R Rejection — primary M5 binary mean-reversion strategy."""

import math
from typing import Dict, Any

import numpy as np
import pandas as pd

from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    REVERSAL_STATES, BLOCKED_STATES,
    get_market_state, get_m5_df, calc_atr, cluster_sr_levels,
    is_news_blackout, is_broker_feed_stale, candle_metrics,
    apply_lifecycle_penalty, confidence_from_components,
    build_signal, build_no_setup,
)
from core.models.market_context import MarketContext


class Rejection5mPA(BaseStrategy):
    STRATEGY_NAME = "rejection_5m_pa"

    def _calculate_s_level(self, level: float, df: pd.DataFrame, atr_val: float) -> float:
        if level <= 0 or atr_val <= 0:
            return 0.0
        touches, sum_react, last_touch_idx = 0, 0.0, 0
        highs, lows = df["high"].values, df["low"].values
        n = len(df)
        for i in range(n - 1):
            if abs(lows[i] - level) <= 0.1 * atr_val or abs(highs[i] - level) <= 0.1 * atr_val:
                touches += 1
                last_touch_idx = i
                react = max(abs(highs[i + 1] - level), abs(lows[i + 1] - level))
                sum_react += react
        c_touch = min(50.0, touches * 20.0)
        avg_react = sum_react / touches if touches else 0.0
        d_react = min(30.0, (avg_react / atr_val) * 10.0 if atr_val > 0 else 0.0)
        s_base = c_touch + d_react + 20.0
        age = (n - 1) - last_touch_idx if touches else n
        return s_base * math.exp(-0.02 * age)

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        state, lifecycle = get_market_state(context)
        name = self.STRATEGY_NAME

        if state in BLOCKED_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state, hard_block=True)
        if state not in REVERSAL_STATES:
            return build_no_setup(name, "MARKET_STATE_BLOCKED", state)
        if is_news_blackout(context):
            return build_no_setup(name, "NEWS_BLACKOUT", state)
        if is_broker_feed_stale(context):
            return build_no_setup(name, "BROKER_FEED_FREEZE", state)

        df = get_m5_df(context, 50)
        if df is None:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        atr_series = calc_atr(df)
        atr_val = float(atr_series.iloc[-1])
        avg_atr = float(atr_series.iloc[-20:].mean())
        vol = df["volume"]
        avg_vol = float(vol.iloc[-20:].mean()) or 1.0

        m = candle_metrics(df)
        supports, resistances = cluster_sr_levels(df)
        if not supports:
            supports = [float(df["low"].iloc[-20:-1].min())]
        if not resistances:
            resistances = [float(df["high"].iloc[-20:-1].max())]

        action = "NO_SETUP"
        level_touched, wick_target, wick_opposite, s_level = 0.0, 0.0, 0.0, 0.0
        touch_tol = 0.15 * atr_val

        nearest_sup = min(supports, key=lambda x: abs(x - m["low"]))
        nearest_res = min(resistances, key=lambda x: abs(x - m["high"]))

        if abs(m["low"] - nearest_sup) <= touch_tol and m["close"] > nearest_sup:
            if m["lower_wick"] >= m["body"] * 0.5 and m["lower_wick"] > m["upper_wick"]:
                action, level_touched = "CALL", nearest_sup
                wick_target, wick_opposite = m["lower_wick"], m["upper_wick"]
                s_level = self._calculate_s_level(nearest_sup, df, atr_val)

        if action == "NO_SETUP" and abs(m["high"] - nearest_res) <= touch_tol and m["close"] < nearest_res:
            if m["upper_wick"] >= m["body"] * 0.5 and m["upper_wick"] > m["lower_wick"]:
                action, level_touched = "PUT", nearest_res
                wick_target, wick_opposite = m["upper_wick"], m["lower_wick"]
                s_level = self._calculate_s_level(nearest_res, df, atr_val)

        if action == "NO_SETUP":
            return build_no_setup(name, "CANDLE_STRUCTURE_INVALID", state)
        if s_level < 10:
            return build_no_setup(name, "LEVEL_TOO_WEAK", state)
        if m["body"] <= 0.03 * atr_val:
            return build_no_setup(name, "DOJI_SETUP_INVALID", state)

        r_wick = wick_target / m["body"] if m["body"] > 0 else 0.0
        d_pen = (abs(m["low"] - level_touched) if action == "CALL" else abs(m["high"] - level_touched)) / atr_val
        d_close = abs(m["close"] - level_touched) / atr_val

        f_wick = min(100.0, ((r_wick - 0.5) / 1.2) * 50.0 + 50.0) if r_wick >= 0.5 else 0.0
        f_pen = min(100.0, (d_pen / 0.4) * 100.0)
        f_close = max(0.0, 100.0 - (d_close / 0.3) * 100.0)
        entry_score = apply_lifecycle_penalty(
            0.25 * f_wick + 0.30 * f_pen + 0.15 * f_close + 0.30 * s_level,
            lifecycle, state,
        )

        block_score = 0.0
        if atr_val > 1.6 * avg_atr:
            block_score += 25.0
        if d_close > 0.35:
            block_score += 20.0
        if wick_opposite > wick_target:
            block_score = 100.0
        if lifecycle == "EXHAUSTED":
            block_score = 100.0

        c_vol = float(vol.iloc[-1])
        if c_vol > 1.8 * avg_vol and (
            (action == "CALL" and m["close"] < level_touched) or
            (action == "PUT" and m["close"] > level_touched)
        ):
            return build_no_setup(name, "BREAKOUT_CLOSED_OUTSIDE", state, hard_block=True)

        if block_score >= 100.0:
            return build_no_setup(name, "RISK_BLOCKED", state)

        conf = confidence_from_components(r_wick, d_pen, s_level)
        return build_signal(
            name, action, entry_score, block_score, conf,
            {"level_touched": float(level_touched), "pattern": "Rejection",
             "wick_ratio": float(r_wick), "s_level": float(s_level), "market_state": state},
        )
