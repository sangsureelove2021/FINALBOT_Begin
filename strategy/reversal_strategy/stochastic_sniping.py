"""
Stochastic Sniping - Precision Entry on Exhaustion Zones
Targets EXHAUSTION_ZONE or TRENDING_OVEREXTENDED markets.
Uses stochastic oscillator with multi-timeframe confirmation to snipe exhaustion reversals.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np

from core.models.market_context import MarketContext
from strategy.base_strategy import BaseStrategy
from strategy.m5_binary_core import (
    get_m5_df, calc_atr, get_market_state,
    build_signal, build_no_setup, apply_lifecycle_penalty,
    candle_metrics, calc_stochastic, calc_rsi
)


class StochasticSnipingStrategy(BaseStrategy):
    STRATEGY_NAME = "stochastic_sniping"
    REQUIRED_MARKET_STATE = "EXHAUSTION_ZONE"  # also works with TRENDING_OVEREXTENDED

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        state, lifecycle = get_market_state(context)
        name = self.STRATEGY_NAME

        # Only EXHAUSTION_ZONE per strategy locking
        if state != "EXHAUSTION_ZONE":
            return build_no_setup(name, f"WRONG_MARKET_STATE:{state}", state)

        df = get_m5_df(context, 80)
        if df is None:
            return build_no_setup(name, "INSUFFICIENT_DATA", state)

        close = df['close'].values
        
        # --- Multi-timeframe stochastic (simulate M1 and M5) ---
        # M5 stochastic
        k5, d5 = calc_stochastic(df, k_period=14, d_period=3)
        k5_val = float(k5.iloc[-1])
        d5_val = float(d5.iloc[-1])
        k5_prev = float(k5.iloc[-2]) if len(k5) > 1 else k5_val
        d5_prev = float(d5.iloc[-2]) if len(d5) > 1 else d5_val
        
        # Simulate M1 by using 5-period rolling on M5 data (rough proxy)
        # Actually use a shorter period stochastic to simulate faster timeframe
        k1, d1 = calc_stochastic(df, k_period=5, d_period=2)
        k1_val = float(k1.iloc[-1])
        d1_val = float(d1.iloc[-1])
        
        # --- RSI for additional exhaustion confirmation ---
        rsi = calc_rsi(pd.Series(close), period=14)
        rsi_val = float(rsi.iloc[-1])
        rsi_prev = float(rsi.iloc[-2]) if len(rsi) > 1 else rsi_val
        
        # --- ATR to check if volatility is normal (not exploding) ---
        atr = calc_atr(df)
        atr_val = float(atr.iloc[-1])
        atr_pct = atr_val / (close[-1] + 1e-9) * 100
        
        # --- Detect exhaustion signals ---
        action = "NO_SETUP"
        signal_strength = 0.0
        
        # Bearish exhaustion (overbought -> PUT)
        if k5_val > 80 and k1_val > 80 and k5_val < k5_prev:  # Stochastic turning down
            # RSI also overbought and turning
            if rsi_val > 70 and rsi_val < rsi_prev:
                action = "PUT"
                signal_strength = (k5_val - 80) * 2 + (rsi_val - 70)
        
        # Bullish exhaustion (oversold -> CALL)
        elif k5_val < 20 and k1_val < 20 and k5_val > k5_prev:  # Stochastic turning up
            if rsi_val < 30 and rsi_val > rsi_prev:
                action = "CALL"
                signal_strength = (20 - k5_val) * 2 + (30 - rsi_val)
        
        if action == "NO_SETUP":
            return build_no_setup(name, "NO_STOCHASTIC_EXHAUSTION", state)
        
        # --- Candle confirmation (rejection) ---
        curr = candle_metrics(df)
        if action == "PUT":
            wick_ratio = curr['upper_wick'] / (curr['body'] + 1e-9)
            # Need upper wick for bearish rejection
            if wick_ratio < 0.8:
                return build_no_setup(name, "NO_REJECTION_CANDLE", state)
        else:
            wick_ratio = curr['lower_wick'] / (curr['body'] + 1e-9)
            if wick_ratio < 0.8:
                return build_no_setup(name, "NO_REJECTION_CANDLE", state)
        
        # --- Entry score ---
        # Scale signal strength (max 100)
        signal_score = min(70.0, 50.0 + signal_strength)
        wick_score = min(20.0, wick_ratio * 10)
        stoch_alignment = 10.0 if (k5_val > 80 and k1_val > 80) or (k5_val < 20 and k1_val < 20) else 0.0
        
        entry_score = apply_lifecycle_penalty(
            signal_score + wick_score + stoch_alignment,
            lifecycle, state
        )
        
        if entry_score < 68:
            return build_no_setup(name, "LOW_ENTRY_SCORE", state)
        
        # --- Confidence ---
        # Use divergence between k5 and d5
        divergence = (k5_val - d5_val) / 100.0  # positive if k > d
        if action == "PUT":
            # For PUT, we want k crossing down through d
            alignment = 1.0 if (k5_val < d5_val and k5_prev > d5_prev) else 0.5
        else:
            alignment = 1.0 if (k5_val > d5_val and k5_prev < d5_prev) else 0.5
        
        conf = min(0.95, 0.4 + 0.3 * (signal_strength / 100) + 0.3 * alignment)
        
        return build_signal(
            name, action, entry_score, 10.0, conf,
            {
                "stoch_k5": round(k5_val, 1),
                "stoch_d5": round(d5_val, 1),
                "stoch_k1": round(k1_val, 1),
                "rsi": round(rsi_val, 1),
                "wick_ratio": round(wick_ratio, 2),
                "pattern": "StochasticSniping",
                "market_state": state
            }
        )
