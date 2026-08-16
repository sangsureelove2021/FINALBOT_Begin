"""
Candle Processor - Candle Data Processing Functions

หน้าที่: จัดการกับ candle data รวมถึงการ drop forming, merge, add age/quality, และ check continuity
ฟังก์ชัน: _drop_forming, _merge, _add_age_and_quality, check continuity
"""

import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Tuple, Any
import logging

from data_feed.data_validator import DataValidator
from data_feed.exceptions import DataFeedError, DataGapError

logger = logging.getLogger(__name__)


def drop_forming(df: Optional[pd.DataFrame], broker_epoch: float, tf_seconds: int) -> pd.DataFrame:
    """
    Drop forming candles (incomplete latest candle).
    
    Args:
        df: DataFrame with candle data
        broker_epoch: Current broker epoch time
        tf_seconds: Timeframe in seconds
        
    Returns:
        pd.DataFrame: DataFrame with forming candle dropped
        
    Raises:
        ValueError: If DataFrame is empty or None
    """
    if df is None or df.empty:
        raise ValueError("DataFrame is empty in drop_forming")
    
    df = DataValidator.ensure_utc_datetime_index(df)
    last_candle_start = df.index[-1].timestamp()
    
    if (broker_epoch - last_candle_start) < tf_seconds:
        if len(df) <= 1:
            raise ValueError("Insufficient candle data: only 1 forming candle available in drop_forming")
        res = df.iloc[:-1].copy()
    else:
        res = df.copy()
    
    return DataValidator.ensure_utc_datetime_index(res)


def merge_candles(stored: pd.DataFrame, fresh: pd.DataFrame, 
                  gap_threshold: int, label: str, timeframe: str, 
                  max_candles: int, validator: DataValidator) -> pd.DataFrame:
    """
    Merge stored and fresh candle data with continuity validation.
    
    Args:
        stored: Existing stored DataFrame
        fresh: New data to merge
        gap_threshold: Maximum allowed gap in seconds
        label: Label for logging
        timeframe: Timeframe string (M1, M5, M15)
        max_candles: Maximum number of candles to keep
        validator: DataValidator instance for validation
        
    Returns:
        pd.DataFrame: Merged DataFrame
        
    Raises:
        DataGapError: If data gap is detected
        ValueError: If merge fails
    """
    if stored is None or stored.empty:
        raise ValueError(f"{label}: stored data is empty")
    
    if fresh is None or fresh.empty:
        raise ValueError(f"{label}: fresh data is empty")
    
    # Ensure both DataFrames have UTC datetime index
    stored = DataValidator.ensure_utc_datetime_index(stored)
    fresh = DataValidator.ensure_utc_datetime_index(fresh)
    
    # Validate price continuity
    validator.validate_continuity(stored, fresh, label.split()[0] if ' ' in label else label, label)
    
    # Check data gap
    last_ts = stored.index[-1]
    first_ts = fresh.index[0]
    gap_sec = (first_ts - last_ts).total_seconds()
    
    if gap_sec > gap_threshold:
        logger.error(f"[DataAdapter] {label}: FAIL-FAST Data gap detected ({gap_sec}s > {gap_threshold}s)")
        raise DataGapError(f"FAIL-FAST: Data gap detected in candles for {label} ({gap_sec}s > {gap_threshold}s)")
    
    # Validate overlap consistency
    validator.validate_overlap(stored, fresh, label.split()[0] if ' ' in label else label, label)
    
    # Combine and deduplicate
    combined = pd.concat([stored, fresh])
    combined = combined[~combined.index.duplicated(keep='last')]
    combined = DataValidator.ensure_utc_datetime_index(combined)
    
    return combined.tail(max_candles)


def add_age_and_quality(df: pd.DataFrame, broker_epoch: float, tf_seconds: int) -> pd.DataFrame:
    """
    Add age (milliseconds: int64) and quality (categorical string: 'FRESH' / 'STALE') columns to candles.
    
    Args:
        df: DataFrame with candle data
        broker_epoch: Current broker epoch time in seconds
        tf_seconds: Timeframe in seconds
        
    Returns:
        pd.DataFrame: DataFrame with age and quality columns added
        
    Raises:
        ValueError: If DataFrame is empty/None or tf_seconds is invalid
        TypeError: If broker_epoch is not numeric or index is not DatetimeIndex
    """
    if df is None or df.empty:
        raise ValueError("FAIL-FAST: DataFrame is empty in add_age_and_quality")
    
    if not isinstance(broker_epoch, (int, float)):
        raise TypeError(f"FAIL-FAST: broker_epoch must be numeric, got {type(broker_epoch).__name__}")
    
    if not isinstance(tf_seconds, (int, float)) or tf_seconds <= 0:
        raise ValueError(f"FAIL-FAST: tf_seconds must be a positive integer, got {tf_seconds}")
    
    df = DataValidator.ensure_utc_datetime_index(df)
    result = df.copy()
    
    if not isinstance(result.index, pd.DatetimeIndex):
        raise TypeError(f"FAIL-FAST: DataFrame index must be DatetimeIndex, got {type(result.index).__name__}")
    
    # Calculate age (milliseconds elapsed since candle start timestamp)
    dtype_str = str(result.index.dtype)
    if 'us' in dtype_str:
        ts_seconds = result.index.astype('int64') / 10**6
    elif 'ms' in dtype_str:
        ts_seconds = result.index.astype('int64') / 10**3
    elif '[s]' in dtype_str or 'datetime64[s' in dtype_str:
        ts_seconds = result.index.astype('int64').astype(float)
    else:
        ts_seconds = result.index.astype('int64') / 10**9

    result['age'] = ((broker_epoch - ts_seconds) * 1000).round().astype('int64')
    
    # Categorical string quality: 'FRESH' if age <= tf_seconds * 2 * 1000, otherwise 'STALE'
    threshold_ms = int(tf_seconds * 2 * 1000)
    result['quality'] = np.where(result['age'] <= threshold_ms, 'FRESH', 'STALE')
    
    return result


def check_continuity(df: pd.DataFrame, required_count: int) -> bool:
    """
    Check if candle data has continuity (no gaps in time).
    
    Args:
        df: DataFrame with candle data
        required_count: Minimum number of candles required
        
    Returns:
        bool: True if data has continuity and meets requirements
        
    Raises:
        ValueError: If DataFrame is invalid
    """
    if df is None or df.empty:
        raise ValueError("DataFrame is empty in check_continuity")
    
    if len(df) < required_count:
        logger.warning(f"Insufficient candles: {len(df)} < {required_count}")
        return False
    
    df = DataValidator.ensure_utc_datetime_index(df)
    
    # Check for gaps in index (assuming regular timeframe)
    if len(df) > 1:
        # Calculate expected time difference
        time_diffs = df.index.to_series().diff().dropna()
        
        # Get the most common time difference (should be the timeframe)
        if len(time_diffs) > 0:
            # Check if there are any large gaps
            median_diff = time_diffs.median()
            max_allowed_diff = median_diff * 1.5  # Allow up to 50% deviation
            large_gaps = time_diffs[time_diffs > max_allowed_diff]
            
            if len(large_gaps) > 0:
                logger.warning(f"Found {len(large_gaps)} gaps in candle data")
                # Accept with warning if we have enough data
                # But return False if there are too many gaps
                if len(large_gaps) > len(df) * 0.1:  # More than 10% gaps
                    logger.warning("Too many gaps in candle data")
                    return False
    
    return True


def process_candle_refresh(symbol: str, broker_epoch: float, 
                          store_dict: Dict[str, Optional[pd.DataFrame]],
                          last_block_dict: Dict[str, int],
                          data_source, timeframe: str, 
                          tf_seconds: int, max_candles: int,
                          gap_threshold: int,
                          validator: DataValidator,
                          current_block: int) -> Optional[pd.DataFrame]:
    """
    Generic function to refresh candle data for a specific timeframe.
    
    Args:
        symbol: Trading symbol
        broker_epoch: Current broker epoch time
        store_dict: Dictionary storing candle data for this timeframe
        last_block_dict: Dictionary tracking last block index
        data_source: Data source to fetch from
        timeframe: Timeframe string (M1, M5, M15)
        tf_seconds: Timeframe in seconds
        max_candles: Maximum candles to keep
        gap_threshold: Maximum allowed gap in seconds
        validator: DataValidator instance
        current_block: Current block index
        
    Returns:
        Optional[pd.DataFrame]: Completed candles after processing
        
    Raises:
        DataFeedError: If data fetch fails
        ValueError: If processing fails
    """
    block = current_block
    block_changed = False
    
    # Check if we need to fetch new data
    if store_dict.get(symbol) is None:
        logger.info(f"[DataAdapter] Initializing {timeframe} data for {symbol}")
        
        # Fetch data
        if hasattr(data_source, 'update_with_streaming'):
            df = data_source.update_with_streaming(symbol, timeframe, max_candles + 10)
        else:
            df = data_source.get_candles(symbol, timeframe, max_candles + 10, end_time=broker_epoch)
        
        if df is None or df.empty or len(df) < 2:
            raise ValueError(f"{timeframe} fetch failed for {symbol}")
        
        store_dict[symbol] = DataValidator.ensure_utc_datetime_index(df)
        last_block_dict[symbol] = block
        block_changed = True
    
    # Check if block has changed
    elif block != last_block_dict.get(symbol):
        logger.info(f"[DataAdapter] Refreshing {timeframe} data for {symbol}")
        
        # Fetch fresh data
        if hasattr(data_source, 'update_with_streaming'):
            fresh = data_source.update_with_streaming(symbol, timeframe, max_candles + 10)
        else:
            fresh = data_source.get_candles(symbol, timeframe, max_candles + 10, end_time=broker_epoch)
        
        if fresh is not None and not fresh.empty:
            # Merge data
            store_dict[symbol] = merge_candles(
                store_dict[symbol], fresh,
                gap_threshold=gap_threshold,
                label=f"{timeframe} {symbol}",
                timeframe=timeframe,
                max_candles=max_candles + 10,
                validator=validator
            )
            last_block_dict[symbol] = block
            block_changed = True
        else:
            raise DataFeedError(f"{timeframe} fetch failed for {symbol} — Zero Tolerance: stopping immediately")
    
    # Drop forming candle
    completed = drop_forming(store_dict[symbol], broker_epoch, tf_seconds)
    if completed.empty:
        raise ValueError(f"{timeframe} completed is empty for {symbol}")
    
    # Add age and quality
    completed = add_age_and_quality(completed, broker_epoch, tf_seconds)
    
    # Validate if data changed
    if block_changed:
        validator.validate(completed, symbol)
    
    return completed
