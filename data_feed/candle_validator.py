"""
Candle Validator Module for Part 1 (data_feed)

Provides real-time validation of OHLCV candle structures.
Enforces Fail-Fast policy: raises ValueError immediately if OHLC constraints are violated.
"""

import pandas as pd
import logging

logger = logging.getLogger("CandleValidator")


class CandleValidator:
    """
    Validates OHLCV candle data structures for Part 1 data feed.
    """

    def __init__(self, min_candles: int = 10):
        self.min_candles = min_candles

    def validate(self, df: pd.DataFrame, symbol: str = "UNKNOWN") -> bool:
        """
        Validate DataFrame against standard OHLCV rules.
        Raises ValueError immediately if rules are broken (Fail-Fast).
        """
        if df is None or df.empty:
            raise ValueError(f"FAIL-FAST: [CandleValidator] DataFrame for {symbol} is empty or None")

        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"FAIL-FAST: [CandleValidator] Missing required column '{col}' for {symbol}")

        # Rule 1: High >= Low
        if (df['high'] < df['low']).any():
            raise ValueError(f"FAIL-FAST: [CandleValidator] High < Low detected for {symbol}")

        # Rule 2: High >= Open and High >= Close
        if (df['high'] < df['open']).any() or (df['high'] < df['close']).any():
            raise ValueError(f"FAIL-FAST: [CandleValidator] High < Open/Close detected for {symbol}")

        # Rule 3: Low <= Open and Low <= Close
        if (df['low'] > df['open']).any() or (df['low'] > df['close']).any():
            raise ValueError(f"FAIL-FAST: [CandleValidator] Low > Open/Close detected for {symbol}")

        # Rule 4: Non-negative prices
        if (df[['open', 'high', 'low', 'close']] <= 0).any().any():
            raise ValueError(f"FAIL-FAST: [CandleValidator] Non-positive price detected for {symbol}")

        logger.debug(f"[CandleValidator] Validation passed for {symbol} ({len(df)} rows)")
        return True
