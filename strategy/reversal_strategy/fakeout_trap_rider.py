"""
Fakeout Trap Rider - Extreme M5 Fakeout Reversal
Targets LIQUIDITY_VOID or VOLATILITY_EXPANDING markets where price fakes through support/resistance.
Uses wick rejection + volume profile to detect traps and ride the reversal.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from core.models.market_context import MarketContext
from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    get_m5_df, calc_atr, get_market_state,
    build_signal, build_no_setup, apply_lifecycle_penalty,
    candle_metrics, cluster_sr_levels
)


class FakeoutTrapRiderStrategy(BaseStrategy):
    STRATEGY_NAME = "fakeout_trap_rider"
    REQUIRED_MARKET_STATE = "LIQUIDITY_VOID"  # or VOLATILITY_EXPANDING - both trap-prone

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        state, lifecycle = get_market_state(context)
        name = self.STRATEGY_NAME

        # Only LIQUIDITY_VOID per strategy locking
        if state != "LIQUIDITY_VOID":
            return build_no_setup(name, f"WRONG_MARKET_STATE:{state}", state)

        df = get_m5_df(context, 60)
        if df is None:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        # --- Detect fakeout ---
        # 1. Look for a candle that breaks above recent high but closes below it
        lookback = 10
        recent_high = max(high[-lookback:-2])
        recent_low = min(low[-lookback:-2])
        
        curr = candle_metrics(df)
        prev = candle_metrics(df.iloc[:-1]) if len(df) > 1 else curr
        
        action = "NO_SETUP"
        fakeout_score = 0.0
        
        # Upper fakeout (bull trap): breaks above resistance, closes below
        if curr['high'] > recent_high and curr['close'] < recent_high and curr['upper_wick'] > curr['body'] * 1.5:
            action = "PUT"
            fakeout_score = min(100.0, (curr['high'] - recent_high) / (recent_high + 1e-9) * 1000 + 50)
        
        # Lower fakeout (bear trap): breaks below support, closes above
        elif curr['low'] < recent_low and curr['close'] > recent_low and curr['lower_wick'] > curr['body'] * 1.5:
            action = "CALL"
            fakeout_score = min(100.0, (recent_low - curr['low']) / (recent_low + 1e-9) * 1000 + 50)
        
        if action == "NO_SETUP":
            return build_no_setup(name, "NO_FAKEOUT_DETECTED", state)
        
        # --- Additional confirmation: ATR expansion (volatility spike) ---
        atr = calc_atr(df)
        atr_val = float(atr.iloc[-1])
        atr_prev = float(atr.iloc[-2]) if len(atr) > 1 else atr_val
        atr_spike = (atr_val - atr_prev) / (atr_prev + 1e-9)
        
        # Wick-to-body ratio strength
        if action == "PUT":
            wick_ratio = curr['upper_wick'] / (curr['body'] + 1e-9)
        else:
            wick_ratio = curr['lower_wick'] / (curr['body'] + 1e-9)
        wick_score = min(30.0, wick_ratio * 20)
        
        # --- Entry score ---
        entry_score = apply_lifecycle_penalty(
            fakeout_score * 0.7 + wick_score + (atr_spike * 20),
            lifecycle, state
        )
        
        if entry_score < 68:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)
        
        # Confidence: wick ratio treated as penetration for reversal
        penetration = wick_ratio / 3.0  # normalize
        conf = min(0.95, 0.6 + 0.3 * (fakeout_score / 100) + 0.1 * min(1.0, atr_spike))
        
        return build_signal(
            name, action, entry_score, 15.0, conf,
            {
                "fakeout_magnitude": round(fakeout_score, 1),
                "wick_ratio": round(wick_ratio, 2),
                "atr_spike": round(atr_spike, 3),
                "pattern": "FakeoutReversal",
                "market_state": state
            }
        )
