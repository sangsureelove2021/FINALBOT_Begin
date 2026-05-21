"""
Candle Buffer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Maintains rolling buffer of recent candles per symbol/timeframe.
Auto-detects incomplete candles (in-progress bar).
"""

import pandas as pd
from collections import defaultdict
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CandleBuffer:
    """
    Maintains N most recent candles per symbol/timeframe.
    
    Usage:
        buffer = CandleBuffer(size=500)
        buffer.append('EURUSD', 'M5', df)  # Full candle
        current_candles = buffer.get('EURUSD', 'M5')
        
        # Check if last candle is incomplete
        is_incomplete = buffer.is_incomplete('EURUSD', 'M5')
    """
    
    def __init__(self, size: int = 500):
        """
        Initialize buffer.
        
        Args:
            size: Max candles to keep per symbol/timeframe
        """
        self.size = size
        self.buffers: Dict[str, Dict[str, pd.DataFrame]] = defaultdict(dict)
        self.incomplete_flags: Dict[str, Dict[str, bool]] = defaultdict(dict)
    
    def append(self, symbol: str, timeframe: str, candles: pd.DataFrame) -> None:
        """
        Append candles to buffer. Auto-manages size.
        
        Args:
            symbol: 'EURUSD'
            timeframe: 'M1', 'M5', etc.
            candles: DataFrame with [open, high, low, close, volume]
        """
        key = f"{symbol}_{timeframe}"
        
        if key in self.buffers:
            # Merge with existing
            df = pd.concat([self.buffers[key], candles])
            # Remove duplicates by index, keep last
            df = df[~df.index.duplicated(keep='last')]
        else:
            df = candles.copy()
        
        # Keep only recent N candles
        if len(df) > self.size:
            df = df.iloc[-self.size:]
        
        self.buffers[key] = df.sort_index()
        logger.debug(f"📊 Buffer {symbol}/{timeframe}: {len(df)} candles")
    
    def get(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Get all buffered candles for symbol/timeframe.
        
        Returns:
            DataFrame or None if not found
        """
        key = f"{symbol}_{timeframe}"
        return self.buffers.get(key)
    
    def get_recent(self, symbol: str, timeframe: str, 
                  count: int = 100) -> Optional[pd.DataFrame]:
        """
        Get last N candles.
        
        Args:
            count: Number of recent candles to return
        
        Returns:
            DataFrame or None if not enough data
        """
        df = self.get(symbol, timeframe)
        if df is None or len(df) < count:
            return df
        return df.iloc[-count:]
    
    def set_incomplete(self, symbol: str, timeframe: str, 
                      is_incomplete: bool) -> None:
        """
        Mark last candle as incomplete (still forming).
        
        Args:
            is_incomplete: True if last bar is still open
        """
        key = f"{symbol}_{timeframe}"
        self.incomplete_flags[key] = is_incomplete
        logger.debug(f"🔄 {symbol}/{timeframe} incomplete: {is_incomplete}")
    
    def is_incomplete(self, symbol: str, timeframe: str) -> bool:
        """Check if last candle is still forming."""
        key = f"{symbol}_{timeframe}"
        return self.incomplete_flags.get(key, False)
    
    def clear(self, symbol: Optional[str] = None, 
             timeframe: Optional[str] = None) -> None:
        """
        Clear buffer.
        
        Args:
            symbol: If None, clear all symbols
            timeframe: If None, clear all timeframes for symbol
        """
        if symbol is None:
            self.buffers.clear()
            self.incomplete_flags.clear()
            logger.info("🗑️ All buffers cleared")
        elif timeframe is None:
            to_delete = [k for k in self.buffers.keys() if k.startswith(f"{symbol}_")]
            for k in to_delete:
                del self.buffers[k]
            logger.info(f"🗑️ Buffer for {symbol} cleared")
        else:
            key = f"{symbol}_{timeframe}"
            if key in self.buffers:
                del self.buffers[key]
            logger.info(f"🗑️ Buffer {symbol}/{timeframe} cleared")
    
    def size_info(self) -> Dict[str, int]:
        """Get info about buffer sizes."""
        return {key: len(df) for key, df in self.buffers.items()}
