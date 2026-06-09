"""
CSV Data Adapter for FINALBOT Offline Simulation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Implements IDataSource interface, reading historical candle data 
from local CSV databases and slicing it according to simulated 
time to prevent look-ahead bias (future leakage).
"""

import os
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

from core.data.data_source import IDataSource

logger = logging.getLogger(__name__)


class CSVDataAdapter(IDataSource):
    """
    Offline data adapter implementing IDataSource.
    Loads historical CSV files and slices candles up to simulated_time.
    """
    
    def __init__(self, data_dir: str = "historical_data"):
        self.data_dir = data_dir
        self.dfs: Dict[str, Dict[str, pd.DataFrame]] = {}
        self.simulated_time: Optional[datetime] = None
        self._connected = True
        
    def load_symbol_data(self, symbol: str, timeframes: List[str]) -> bool:
        """
        Pre-load CSV dataframes into memory for ultra-fast slicing during backtesting.
        """
        self.dfs[symbol] = {}
        safe_sym = symbol.replace("-OTC", "_OTC")
        
        success = False
        for tf in timeframes:
            file_name = f"history_{safe_sym}_{tf}.csv"
            file_path = os.path.join(self.data_dir, file_name)
            
            if not os.path.exists(file_path):
                logger.warning(f"⚠️ CSV file not found: {file_path}")
                continue
                
            try:
                # Load CSV, parse timestamp column as index
                df = pd.read_csv(file_path)
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.set_index("timestamp").sort_index()
                if df.index.tzinfo is None:
                    df.index = df.index.tz_localize(timezone.utc)
                
                # Sanity checking column conversions
                for col in ("open", "high", "low", "close", "volume"):
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                
                self.dfs[symbol][tf] = df
                success = True
                logger.debug(f"[CSV] Pre-loaded {len(df)} candles for {symbol} ({tf}) from {file_path}")
            except Exception as e:
                logger.error(f"❌ Failed to load historical CSV {file_path}: {e}")
                
        return success
        
    def set_simulated_time(self, sim_time: datetime) -> None:
        """
        Advance or set the 'Time Machine' cursor.
        All subsequent candle retrievals will strictly slice up to this timestamp.
        """
        # Ensure timestamp is timezone-aware UTC
        if sim_time.tzinfo is None:
            self.simulated_time = sim_time.replace(tzinfo=timezone.utc)
        else:
            self.simulated_time = sim_time.astimezone(timezone.utc)
            
    def get_candles(self, symbol: str, timeframe: str, 
                    count: int = 200) -> pd.DataFrame:
        """
        Retrieve count recent candles for symbol, sliced strictly up to simulated_time.
        """
        if not self.simulated_time:
            raise RuntimeError("Simulation time not set in CSVDataAdapter")
            
        if symbol not in self.dfs or timeframe not in self.dfs[symbol]:
            # Try to dynamically load if not already in cache
            if not self.load_symbol_data(symbol, [timeframe]):
                logger.error(f"[CSV] No preloaded history available for {symbol} ({timeframe})")
                return pd.DataFrame()
                
        df_full = self.dfs[symbol][timeframe]
        
        # SLICE: Get all candles where index <= simulated_time (No future data leakage!)
        # Use binary search searchsorted on chronologically sorted index for 10x speedup
        pos = df_full.index.searchsorted(self.simulated_time, side='right')
        df_sliced = df_full.iloc[:pos]
        
        if df_sliced.empty:
            logger.warning(f"⚠️ Sliced history is empty for {symbol} ({timeframe}) at {self.simulated_time}")
            return pd.DataFrame()
            
        # Return the last 'count' rows
        return df_sliced.tail(count)
        
    def get_multi_timeframe(self, symbol: str, 
                            timeframes: list, 
                            count: int = 200) -> Dict[str, pd.DataFrame]:
        """
        Retrieve sliced DataFrames for multiple timeframes.
        """
        return {tf: self.get_candles(symbol, tf, count) for tf in timeframes}
        
    def is_connected(self) -> bool:
        """Fully online locally for backtesting."""
        return self._connected
