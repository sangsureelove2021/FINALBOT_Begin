"""
Velocity Layer Strategy - Extreme M5 Momentum Burst
Targets trending-overextended markets where price velocity accelerates.
Uses rate-of-change and ATR velocity to snipe continuation bursts.
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
    confidence_from_components
)


class VelocityLayerStrategy(BaseStrategy):
    STRATEGY_NAME = "velocity_layer"
    REQUIRED_MARKET_STATE = "TRENDING_OVEREXTENDED"

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        state, lifecycle = get_market_state(context)
        name = self.STRATEGY_NAME

        # Block if wrong market state
        if state != self.REQUIRED_MARKET_STATE.upper():
            return build_no_setup(name, f"WRONG_MARKET_STATE:{state}", state)

        df = get_m5_df(context, 60)
        if df is None:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        close = df['close'].values
        if len(close) < 30:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        # --- Velocity indicators ---
        # 1. Rate of change (ROC) over 5 periods
        roc5 = (close[-1] - close[-6]) / (close[-6] + 1e-9) * 100
        # 2. Momentum acceleration: difference between ROC5 and ROC10
        roc10 = (close[-1] - close[-11]) / (close[-11] + 1e-9) * 100
        accel = roc5 - roc10

        # 3. Volume velocity proxy: range expansion
        atr = calc_atr(df)
        atr_val = float(atr.iloc[-1])
        atr_prev = float(atr.iloc[-2]) if len(atr) > 1 else atr_val
        atr_expansion = (atr_val - atr_prev) / (atr_prev + 1e-9)

        # 4. Price position relative to EMA21
        ema21 = pd.Series(close).ewm(span=21, adjust=False).mean().iloc[-1]
        price_vs_ema = (close[-1] - ema21) / (ema21 + 1e-9) * 100

        # Determine action based on velocity direction
        action = "NO_SETUP"
        if roc5 > 0.15 and accel > 0.05 and price_vs_ema > 0.3:
            action = "CALL"
        elif roc5 < -0.15 and accel < -0.05 and price_vs_ema < -0.3:
            action = "PUT"

        if action == "NO_SETUP":
            return build_no_setup(name, "VELOCITY_INSUFFICIENT", state)

        # --- Compute entry score ---
        # Scale velocity magnitude (0.15% ROC = 50, 0.5% ROC = 85)
        velocity_strength = min(85.0, 50.0 + abs(roc5) * 200)
        accel_strength = min(20.0, max(0.0, abs(accel) * 100))
        atr_score = min(15.0, atr_expansion * 100)
        entry_score = apply_lifecycle_penalty(
            velocity_strength + accel_strength + atr_score,
            lifecycle, state
        )

        if entry_score < 68:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)

        # Confidence using wick ratio and penetration
        # For velocity, we treat roc5 as "penetration"
        penetration = abs(roc5) / 0.5  # normalize to max 0.5% move
        conf = confidence_from_components(
            wick_ratio=min(1.0, abs(accel) / 0.3),
            penetration_atr=min(1.0, penetration),
            level_strength=velocity_strength
        )

        return build_signal(
            name, action, entry_score, 10.0, conf,
            {
                "roc5": round(roc5, 3),
                "accel": round(accel, 3),
                "atr_expansion": round(atr_expansion, 3),
                "pattern": "VelocityBurst",
                "market_state": state
            }
        )
