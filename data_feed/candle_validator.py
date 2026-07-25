"""
Candle Validator

Checks data quality before usage or writing to CSV:
  • Null / NaN checks
  • Price sanity checks (JPY pairs 50-300, others 0.3-10)
  • Volume validation (must be non-zero for non-OTC pairs)
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class CandleValidator:
    """Validator for candle dataframes."""

    def __init__(self, config=None):
        """
        Initialize with validation configuration.
        
        Args:
            config: Configuration from datafeed_config.json candle_validator section
        """
        if config is None:
            from config_setting.config_loader import get_candle_validator_config
            config = get_candle_validator_config()
        
        self.validation_config = config.get("validation", {})
        
        # Load validation ranges
        self.price_ranges = self.validation_config.get("price_ranges", {
            "JPY": [50.0, 300.0],
            "NON_JPY": [0.3, 10.0],
            "OTC": [0.3, 10.0]
        })
        
        # Load required columns
        self.required_columns = set(self.validation_config.get("required_columns", ["open", "close", "high", "low"]))
        
        # Load NaN threshold
        self.nan_threshold = self.validation_config.get("nan_threshold", "strict")
        
        logger.info("[CandleValidator] Initialized with validation configuration")

    def validate(self, df: pd.DataFrame, symbol: str) -> None:
        """
        Validate OHLCV candle dataframe.
        Raises ValueError if data is invalid.
        """
        if df is None or df.empty:
            raise ValueError(f"Empty dataframe for symbol {symbol}")

        # Check required columns
        missing_cols = self.required_columns - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns for symbol {symbol}: {missing_cols}")

        # Check for NaNs in price
        if df[["open", "close", "high", "low"]].isnull().any().any():
            if self.nan_threshold == "strict":
                raise ValueError(f"NaN values found in prices for {symbol}")
            elif self.nan_threshold == "warn":
                logger.warning(f"NaN values found in prices for {symbol} — data quality issue")

        is_otc = "OTC" in symbol.upper()
        if "volume" in df.columns:
            if not is_otc and df["volume"].sum() == 0:
                raise ValueError(f"Volume is all zeros for non-OTC symbol {symbol} — broker data error")
        else:
            if not is_otc:
                raise ValueError(f"Volume column missing for non-OTC symbol {symbol}")

        # OHLC Price boundary validation
        invalid_high = (df['high'] < df['open']) | (df['high'] < df['close']) | (df['high'] < df['low'])
        if invalid_high.any():
            raise ValueError(f"High price boundary violation detected in {invalid_high.sum()} rows for {symbol}")

        invalid_low = (df['low'] > df['open']) | (df['low'] > df['close']) | (df['low'] > df['high'])
        if invalid_low.any():
            raise ValueError(f"Low price boundary violation detected in {invalid_low.sum()} rows for {symbol}")

        # Timestamp monotonicity check
        if isinstance(df.index, pd.DatetimeIndex) and not df.index.is_monotonic_increasing:
            raise ValueError(f"Timestamps out of order for {symbol}")

        # Sanity check: reject obviously broken price feeds
        median_close = float(df["close"].median())
        is_jpy = "JPY" in symbol.upper()
        
        if is_otc:
            min_val, max_val = self.price_ranges["OTC"]
        elif is_jpy:
            min_val, max_val = self.price_ranges["JPY"]
        else:
            min_val, max_val = self.price_ranges["NON_JPY"]
            
        if not (min_val <= median_close <= max_val):
            raise ValueError(f"{symbol} median {median_close:.6f} out of range [{min_val}, {max_val}]")
