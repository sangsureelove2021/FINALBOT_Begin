"""
Score Normalizer

Normalizes raw engine outputs to 0-100 score range.
"""

import numpy as np
from typing import Union


class ScoreNormalizer:
    """Normalize values to 0-100 scoring range"""
    
    @staticmethod
    def linear(value: float, min_val: float, max_val: float, 
               clamp: bool = True) -> float:
        """
        Linear normalization from [min_val, max_val] to [0, 100]
        """
        if max_val == min_val:
            return 50.0
        
        normalized = ((value - min_val) / (max_val - min_val)) * 100
        
        if clamp:
            normalized = max(0.0, min(100.0, normalized))
        
        return float(normalized)
    
    @staticmethod
    def sigmoid(value: float, midpoint: float = 0, steepness: float = 1) -> float:
        """
        Sigmoid normalization (S-curve) to 0-100
        """
        try:
            x = (value - midpoint) * steepness
            return 100.0 / (1.0 + np.exp(-x))
        except OverflowError as e:
            import traceback
            traceback.print_exc()
            return 100.0 if value > midpoint else 0.0
    
    @staticmethod
    def from_percentile(value: float, percentile: float) -> float:
        """
        Convert percentile rank to score
        """
        return float(np.clip(percentile, 0, 100))
    
    @staticmethod
    def inverse(value: float, max_val: float = 100) -> float:
        """
        Invert score (high -> low, low -> high)
        Useful for risk scores (high risk = low desirability)
        """
        return max(0.0, min(100.0, max_val - value))
    
    @staticmethod
    def threshold(value: float, threshold: float = 50) -> int:
        """
        Binary threshold (1 if above, 0 if below)
        """
        return 1 if value >= threshold else 0
    
    @staticmethod
    def categorize(value: float) -> str:
        """Categorize score into named tier"""
        if value >= 90:
            return 'PREMIUM'
        elif value >= 75:
            return 'HIGH'
        elif value >= 60:
            return 'MEDIUM'
        elif value >= 40:
            return 'LOW'
        else:
            return 'VERY_LOW'
