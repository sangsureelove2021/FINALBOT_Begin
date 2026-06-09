"""
Test Fixture: Sample Candles
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Deterministic OHLCV DataFrames for use in unit/integration tests.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timezone


def make_candles(count: int = 250, base_price: float = 1.0850,
                 trend: float = 0.0, seed: int = 42,
                 timeframe_minutes: int = 5) -> pd.DataFrame:
    """
    Build a deterministic OHLCV DataFrame.

    Args:
        count: number of candles.
        base_price: starting price.
        trend: per-candle drift (positive = uptrend).
        seed: RNG seed for reproducibility.
        timeframe_minutes: spacing between candles.

    Returns:
        DataFrame [open, high, low, close, volume] indexed by datetime.
    """
    rng = np.random.default_rng(seed)
    end = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    idx = pd.date_range(end=end, periods=count, freq=f"{timeframe_minutes}min")

    noise = rng.normal(0, 0.0009, count)
    returns = trend + noise
    closes = base_price * np.exp(np.cumsum(returns))
    opens = np.concatenate([[base_price], closes[:-1]])

    spread = np.abs(rng.normal(0, 0.0003, count))
    highs = np.maximum(opens, closes) + spread
    lows = np.minimum(opens, closes) - spread
    volumes = rng.integers(800, 2000, count).astype(float)

    return pd.DataFrame(
        {"open": opens, "high": highs, "low": lows,
         "close": closes, "volume": volumes},
        index=idx,
    )


def make_uptrend(count: int = 250) -> pd.DataFrame:
    """Clean uptrend dataset."""
    return make_candles(count=count, trend=0.0006, seed=1)


def make_downtrend(count: int = 250) -> pd.DataFrame:
    """Clean downtrend dataset."""
    return make_candles(count=count, trend=-0.0006, seed=2)


def make_ranging(count: int = 250) -> pd.DataFrame:
    """Flat / ranging dataset."""
    return make_candles(count=count, trend=0.0, seed=3)


def make_multi_timeframe(count: int = 250, seed: int = 42) -> dict:
    """Dict of {timeframe: DataFrame} for MTF tests."""
    tfs = {"M1": 1, "M5": 5, "M15": 15, "M60": 60, "D1": 1440}
    return {
        tf: make_candles(count=count, seed=seed + i, timeframe_minutes=m)
        for i, (tf, m) in enumerate(tfs.items())
    }
