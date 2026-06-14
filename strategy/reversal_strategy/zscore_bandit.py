"""
Z-Score Bandit - Mean Reversion with Statistical Arbitrage
Targets RANGE_BOUND or MEAN_REVERSION_ZONE markets.
Uses rolling z-score of price vs. moving average to detect extreme deviations.
"""

import math
from typing import Dict, Any
import pandas as pd
import numpy as np

from core.models.market_context import MarketContext
from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    get_m5_df, calc_atr, get_market_state,
    build_signal, build_no_setup, apply_lifecycle_penalty,
    candle_metrics
)


class ZScoreBanditStrategy(BaseStrategy):
    STRATEGY_NAME = "zscore_bandit"
    REQUIRED_MARKET_STATE = "RANGE_BOUND"  # also works with MEAN_REVERSION_ZONE

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        state, lifecycle = get_market_state(context)
        name = self.STRATEGY_NAME

        # Only RANGE_BOUND per strategy locking
        if state != "RANGE_BOUND":
            return build_no_setup(name, f"WRONG_MARKET_STATE:{state}", state)

        df = get_m5_df(context, 60)
        if df is None:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        close = df['close'].values
        if len(close) < 30:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        # --- Z-Score calculations ---
        # 1. Rolling mean and std over 20 periods
        window = 20
        mean_20 = pd.Series(close).rolling(window).mean().iloc[-1]
        std_20 = pd.Series(close).rolling(window).std().iloc[-1]
        zscore_20 = (close[-1] - mean_20) / (std_20 + 1e-9)

        # 2. Z-score using shorter window for sensitivity
        window_short = 10
        mean_10 = pd.Series(close).rolling(window_short).mean().iloc[-1]
        std_10 = pd.Series(close).rolling(window_short).std().iloc[-1]
        zscore_10 = (close[-1] - mean_10) / (std_10 + 1e-9)

        # 3. Confirm range-bound: ATR low relative to price
        atr = calc_atr(df)
        atr_val = float(atr.iloc[-1])
        atr_pct = atr_val / (close[-1] + 1e-9) * 100
        is_range = atr_pct < 0.4  # ATR < 0.4% of price

        # --- Determine action based on z-score extremes ---
        action = "NO_SETUP"
        
        # Overbought (zscore > +1.5) -> sell (PUT for binary options)
        if zscore_20 > 1.5 and zscore_10 > 1.2 and is_range:
            action = "PUT"
            deviation_strength = zscore_20
        # Oversold (zscore < -1.5) -> buy (CALL)
        elif zscore_20 < -1.5 and zscore_10 < -1.2 and is_range:
            action = "CALL"
            deviation_strength = -zscore_20
        else:
            return build_no_setup(name, "NO_EXTREME_ZSCORE", state)

        # --- Entry score based on z-score magnitude ---
        # Scale: 1.5 zscore = 60, 2.5 zscore = 90
        raw_score = min(90.0, 50.0 + abs(zscore_20) * 20)
        range_bonus = 10.0 if atr_pct < 0.3 else 0.0
        entry_score = apply_lifecycle_penalty(raw_score + range_bonus, lifecycle, state)

        if entry_score < 68:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        # --- Confidence component ---
        # Use zscore magnitude as "penetration" from mean
        penetration = abs(zscore_20) / 2.5  # normalize to 2.5 sigma max
        # Wick ratio from recent candles to confirm reversal
        curr = candle_metrics(df)
        if action == "PUT":
            wick_ratio = curr['upper_wick'] / (curr['body'] + 1e-9)
        else:
            wick_ratio = curr['lower_wick'] / (curr['body'] + 1e-9)
        wick_normalized = min(1.0, wick_ratio / 2.0)
        
        conf = min(0.95, 0.5 + 0.3 * penetration + 0.2 * wick_normalized)

        return build_signal(
            name, action, entry_score, 10.0, conf,
            {
                "zscore_20": round(zscore_20, 2),
                "zscore_10": round(zscore_10, 2),
                "atr_pct": round(atr_pct, 3),
                "pattern": "ZScoreReversion",
                "market_state": state
            }
        )
