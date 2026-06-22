"""
Validators

"""

import pandas as pd


def validate_score(value: float, name: str = "score") -> float:
    """Ensure score is in 0-100 range"""
    if value is None:
        return 0.0
    val = float(value)
    if not 0 <= val <= 100:
        return max(0.0, min(100.0, val))
    return val


def validate_confidence(value: int) -> int:
    """Ensure confidence is in 0-100 range"""
    if value is None:
        return 0
    val = int(value)
    return max(0, min(100, val))


def validate_direction(value: str) -> str:
    """Validate direction string"""
    valid = ['UP', 'DOWN', 'NONE']
    return value.upper() if value.upper() in valid else 'NONE'


def has_required_candle_columns(df: pd.DataFrame) -> bool:
    """Check if dataframe has OHLC columns"""
    required = ['open', 'high', 'low', 'close']
    return df is not None and all(col in df.columns for col in required)
