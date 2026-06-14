"""
Range Bounce Arbitrage - Support/Resistance Bounce with Arbitrage Edge
Targets CHOPPY_UNCERTAIN or RANGE_BOUND markets.
Uses cluster support/resistance levels and requires bounce confirmation with stochastic divergence.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from core.models.market_context import MarketContext
from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    get_m5_df, calc_atr, get_market_state,
    build_signal, build_no_setup, apply_lifecycle_penalty,
    candle_metrics, cluster_sr_levels, calc_stochastic, confidence_from_components
)


class RangeBounceArbitrageStrategy(BaseStrategy):
    STRATEGY_NAME = "range_bounce_arbitrage"
    REQUIRED_MARKET_STATE = "CHOPPY_UNCERTAIN"  # also works with RANGE_BOUND

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        state, lifecycle = get_market_state(context)
        name = self.STRATEGY_NAME

        # Only CHOPPY_UNCERTAIN per strategy locking
        if state != "CHOPPY_UNCERTAIN":
            return build_no_setup(name, f"WRONG_MARKET_STATE:{state}", state)

        df = get_m5_df(context, 80)
        if df is None:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        close = df['close'].values
        low = df['low'].values
        high = df['high'].values
        
        # --- Detect support/resistance clusters ---
        supports, resistances = cluster_sr_levels(df, lookback=40, threshold=0.0003)
        
        if not supports and not resistances:
            return build_no_setup(name, "NO_SR_LEVELS", state)
        
        curr_price = close[-1]
        atr = calc_atr(df)
        atr_val = float(atr.iloc[-1])
        
        # --- Find nearest support and resistance ---
        nearest_support = None
        nearest_resistance = None
        support_distance = float('inf')
        resistance_distance = float('inf')
        
        for sup in supports:
            dist = curr_price - sup
            if 0 < dist < support_distance and dist < atr_val * 0.5:  # within 0.5 ATR
                nearest_support = sup
                support_distance = dist
        
        for res in resistances:
            dist = res - curr_price
            if 0 < dist < resistance_distance and dist < atr_val * 0.5:
                nearest_resistance = res
                resistance_distance = dist
        
        # --- Stochastic confirmation ---
        k, d = calc_stochastic(df)
        k_val = float(k.iloc[-1])
        d_val = float(d.iloc[-1])
        k_prev = float(k.iloc[-2]) if len(k) > 1 else k_val
        
        # --- Detect bounce signals ---
        curr = candle_metrics(df)
        action = "NO_SETUP"
        bounce_strength = 0.0
        
        # Support bounce (CALL)
        if nearest_support is not None and support_distance < atr_val * 0.3:
            # Check for bullish rejection candle
            if curr['lower_wick'] > curr['body'] * 1.2 and curr['close'] > nearest_support:
                # Stochastic oversold and turning up
                if k_val < 30 and k_val > k_prev:
                    action = "CALL"
                    bounce_strength = min(100.0, (curr['close'] - nearest_support) / (nearest_support + 1e-9) * 1000 + 50)
        
        # Resistance bounce (PUT)
        if nearest_resistance is not None and resistance_distance < atr_val * 0.3:
            if curr['upper_wick'] > curr['body'] * 1.2 and curr['close'] < nearest_resistance:
                if k_val > 70 and k_val < k_prev:  # overbought and turning down
                    action = "PUT"
                    bounce_strength = min(100.0, (nearest_resistance - curr['close']) / (nearest_resistance + 1e-9) * 1000 + 50)
        
        if action == "NO_SETUP":
            return build_no_setup(name, "NO_BOUNCE_DETECTED", state)
        
        # --- Entry score ---
        wick_ratio = curr['upper_wick'] / (curr['body'] + 1e-9) if action == "PUT" else curr['lower_wick'] / (curr['body'] + 1e-9)
        wick_score = min(30.0, wick_ratio * 15)
        stoch_score = 20.0 if (k_val < 30 or k_val > 70) else 10.0
        
        entry_score = apply_lifecycle_penalty(
            bounce_strength * 0.6 + wick_score + stoch_score,
            lifecycle, state
        )
        
        if entry_score < 68:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)
        
        # Confidence
        penetration = (support_distance / (atr_val + 1e-9)) if action == "CALL" else (resistance_distance / (atr_val + 1e-9))
        conf = confidence_from_components(
            wick_ratio=min(1.0, wick_ratio / 2.0),
            penetration_atr=min(1.0, 1.0 - penetration),  # closer to level = higher confidence
            level_strength=bounce_strength
        )
        
        return build_signal(
            name, action, entry_score, 12.0, conf,
            {
                "support": round(nearest_support, 5) if nearest_support else None,
                "resistance": round(nearest_resistance, 5) if nearest_resistance else None,
                "distance_atr": round(support_distance / atr_val if action == "CALL" else resistance_distance / atr_val, 2),
                "stoch_k": round(k_val, 1),
                "wick_ratio": round(wick_ratio, 2),
                "pattern": "RangeBounce",
                "market_state": state
            }
        )
