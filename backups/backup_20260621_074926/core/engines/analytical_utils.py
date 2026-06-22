"""
TIER 8 - ANALYTICAL UTILITIES


Shared analytical helper functions used across the system.
Statistical and technical analysis utilities.
"""

import numpy as np
import pandas as pd
from typing import List, Union, Tuple


class AnalyticalUtils:
    """Tier 8: Static analytical utilities"""
    
    @staticmethod
    def linear_regression(values: Union[list, np.ndarray]) -> Tuple[float, float]:
        """
        Linear regression. Returns (slope, intercept).
        """
        try:
            y = np.array(values, dtype=float)
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            return float(slope), float(intercept)
        except Exception as e:
            return 0.0, 0.0
    
    @staticmethod
    def r_squared(values: Union[list, np.ndarray]) -> float:
        """
        R-squared of linear fit (0-1). How well a line fits the data.
        High R² = clean trend.
        """
        try:
            y = np.array(values, dtype=float)
            if len(y) < 3:
                return 0.0
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            y_pred = slope * x + intercept
            
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            
            if ss_tot == 0:
                return 0.0
            
            return float(max(0, 1 - ss_res / ss_tot))
        except Exception as e:
            return 0.0
    
    @staticmethod
    def standard_deviation(values: Union[list, np.ndarray]) -> float:
        """Standard deviation"""
        try:
            return float(np.std(np.array(values, dtype=float)))
        except Exception as e:
            return 0.0
    
    @staticmethod
    def zscore(value: float, series: Union[list, np.ndarray]) -> float:
        """Z-score of value relative to series"""
        try:
            arr = np.array(series, dtype=float)
            mean = np.mean(arr)
            std = np.std(arr)
            if std == 0:
                return 0.0
            return float((value - mean) / std)
        except Exception as e:
            return 0.0
    
    @staticmethod
    def percentile_rank(value: float, series: Union[list, np.ndarray]) -> float:
        """Percentile rank (0-100)"""
        try:
            arr = np.array(series, dtype=float)
            if len(arr) == 0:
                return 50.0
            return float((np.sum(arr <= value) / len(arr)) * 100)
        except Exception as e:
            return 50.0
    
    @staticmethod
    def correlation(series_a: Union[list, np.ndarray],
                   series_b: Union[list, np.ndarray]) -> float:
        """Pearson correlation (-1 to 1)"""
        try:
            a = np.array(series_a, dtype=float)
            b = np.array(series_b, dtype=float)
            if len(a) != len(b) or len(a) < 2:
                return 0.0
            if np.std(a) == 0 or np.std(b) == 0:
                return 0.0
            corr = np.corrcoef(a, b)[0, 1]
            return float(corr) if not np.isnan(corr) else 0.0
        except Exception as e:
            return 0.0
    
    @staticmethod
    def smooth(values: Union[list, np.ndarray], window: int = 3) -> np.ndarray:
        """Simple moving average smoothing"""
        try:
            arr = np.array(values, dtype=float)
            if len(arr) < window:
                return arr
            return np.convolve(arr, np.ones(window) / window, mode='valid')
        except Exception as e:
            return np.array(values)
    
    @staticmethod
    def normalize_series(values: Union[list, np.ndarray]) -> np.ndarray:
        """Normalize series to 0-1 range"""
        try:
            arr = np.array(values, dtype=float)
            min_v, max_v = arr.min(), arr.max()
            if max_v == min_v:
                return np.full_like(arr, 0.5)
            return (arr - min_v) / (max_v - min_v)
        except Exception as e:
            return np.array(values)
    
    @staticmethod
    def detect_outliers(values: Union[list, np.ndarray], 
                       threshold: float = 3.0) -> List[int]:
        """Return indices of outliers (z-score > threshold)"""
        try:
            arr = np.array(values, dtype=float)
            mean = np.mean(arr)
            std = np.std(arr)
            if std == 0:
                return []
            z_scores = np.abs((arr - mean) / std)
            return [int(i) for i in np.where(z_scores > threshold)[0]]
        except Exception as e:
            return []
    
    @staticmethod
    def weighted_average(values: List[float], weights: List[float]) -> float:
        """Weighted average"""
        try:
            v = np.array(values, dtype=float)
            w = np.array(weights, dtype=float)
            if w.sum() == 0:
                return 0.0
            return float(np.average(v, weights=w))
        except Exception as e:
            return 0.0
