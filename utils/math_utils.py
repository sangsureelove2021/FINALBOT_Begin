"""
Math Utilities
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Common mathematical functions used across engines.
"""

import numpy as np
import pandas as pd
from typing import Union


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division, returns default if denominator is 0"""
    if denominator == 0 or denominator is None:
        return default
    return numerator / denominator


def clamp(value: float, min_val: float = 0, max_val: float = 100) -> float:
    """Clamp value to range"""
    return max(min_val, min(max_val, value))


def normalize_to_100(value: float, max_value: float) -> float:
    """Normalize value to 0-100 scale"""
    if max_value == 0:
        return 0
    return clamp((value / max_value) * 100, 0, 100)


def percentile_rank(value: float, series: pd.Series) -> float:
    """Calculate percentile rank of value in series (0-100)"""
    if series is None or len(series) == 0:
        return 50.0
    return float((series <= value).sum() / len(series) * 100)


def zscore(value: float, series: pd.Series) -> float:
    """Calculate Z-score"""
    if series is None or len(series) < 2:
        return 0.0
    
    std = series.std()
    if std == 0:
        return 0.0
    
    return float((value - series.mean()) / std)


def rolling_zscore(series: pd.Series, period: int = 20) -> pd.Series:
    """Rolling z-score"""
    rolling_mean = series.rolling(period).mean()
    rolling_std = series.rolling(period).std()
    return (series - rolling_mean) / rolling_std


def slope(values: Union[list, np.ndarray, pd.Series]) -> float:
    """Calculate linear regression slope"""
    if len(values) < 2:
        return 0.0
    
    x = np.arange(len(values))
    y = np.array(values)
    
    try:
        coeffs = np.polyfit(x, y, 1)
        return float(coeffs[0])
    except Exception as e:
        return 0.0


def rate_of_change(current: float, past: float) -> float:
    """ROC = (current - past) / past * 100"""
    if past == 0:
        return 0.0
    return ((current - past) / abs(past)) * 100
