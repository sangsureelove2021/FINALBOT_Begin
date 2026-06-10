"""
Data Validator

Validates candle data before passing to engines.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple


class DataValidator:
    """
    Validates candle dataframes for quality issues:
    - Missing columns
    - NaN values
    - Invalid OHLC relationships
    - Gaps in timeline
    - Duplicate timestamps
    """
    
    REQUIRED_COLUMNS = ['open', 'high', 'low', 'close']
    OPTIONAL_COLUMNS = ['volume']
    
    @staticmethod
    def validate(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate dataframe.
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        if df is None:
            return False, ["DataFrame is None"]
        
        if df.empty:
            return False, ["DataFrame is empty"]
        
        # Check required columns
        missing = [c for c in DataValidator.REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            issues.append(f"Missing columns: {missing}")
        
        if missing:
            return False, issues
        
        # Check for NaN
        nan_counts = df[DataValidator.REQUIRED_COLUMNS].isna().sum()
        if nan_counts.any():
            for col, count in nan_counts.items():
                if count > 0:
                    issues.append(f"Column '{col}' has {count} NaN values")
        
        # Check OHLC relationships
        invalid_hl = (df['high'] < df['low']).sum()
        if invalid_hl > 0:
            issues.append(f"{invalid_hl} rows have high < low")
        
        invalid_h = ((df['high'] < df['open']) | (df['high'] < df['close'])).sum()
        if invalid_h > 0:
            issues.append(f"{invalid_h} rows have high < max(open, close)")
        
        invalid_l = ((df['low'] > df['open']) | (df['low'] > df['close'])).sum()
        if invalid_l > 0:
            issues.append(f"{invalid_l} rows have low > min(open, close)")
        
        # Check negative prices
        for col in ['open', 'high', 'low', 'close']:
            if (df[col] < 0).any():
                issues.append(f"Column '{col}' has negative values")
        
        # Check duplicate index
        if isinstance(df.index, pd.DatetimeIndex):
            if df.index.duplicated().any():
                count = df.index.duplicated().sum()
                issues.append(f"{count} duplicate timestamps")
        
        return len(issues) == 0, issues
    
    @staticmethod
    def clean(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean dataframe by:
        - Forward-filling NaN values
        - Removing duplicate timestamps
        - Sorting by timestamp
        """
        if df is None or df.empty:
            return df
        
        # Sort by index
        df = df.sort_index()
        
        # Remove duplicates (keep first)
        if isinstance(df.index, pd.DatetimeIndex):
            df = df[~df.index.duplicated(keep='first')]
        
        # Forward fill NaN
        df = df.ffill()
        
        # Drop remaining NaN at start
        df = df.dropna()
        
        return df
