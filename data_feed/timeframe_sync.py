"""
Timeframe Sync

Aligns multi-timeframe candle data so that every timeframe refers
to the same point in time.

Why this matters:
    M1, M5, M15, M60, D1 candles arrive on different clocks. Before
    multi-timeframe engines (e.g. MTF) compare them, they must be
    trimmed to a common "as-of" timestamp — otherwise a higher
    timeframe could leak future information into a lower one.
"""

import pandas as pd
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Minutes per timeframe — used to order timeframes (ใช้งานสำหรับการซิงก์เวลาแท่งเทียนดึงจริงเท่านั้น)
TF_MINUTES = {
    'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30,
    'M60': 60, 'H1': 60, 'H4': 240, 'D1': 1440,
}


class TimeframeSync:
    """
    Aligns multi-timeframe candle data to a common reference time.
    ใช้งานสำหรับการซิงก์เวลาแท่งเทียนดึงจริงเท่านั้น (ดึงข้อมูลสดตรงจาก Broker API 100%)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Configuration from datafeed_config.json timeframe_sync section
        """
        # Load timeframe configuration
        self.tf_config = config
        
        # Load timeframe mapping
        self.tf_minutes = self.tf_config.get("timeframe_minutes", {
            'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30,
            'M60': 60, 'H1': 60, 'H4': 240, 'D1': 1440,
        })
        
        self.primary = self.tf_config.get("primary_timeframe", "M5")
        self.alignment_strategy = self.tf_config.get("alignment_strategy", "truncate")
        
        logger.info(f"[TimeframeSync] Initialized with primary: {self.primary}")

    def sync(self, candles: Dict[str, pd.DataFrame],
             as_of: Optional[pd.Timestamp] = None) -> Dict[str, pd.DataFrame]:
        """
        Trim every timeframe so no candle is newer than the reference time.

        Args:
            candles: dict of {timeframe: DataFrame indexed by datetime}.
            as_of:   reference timestamp. If None, uses the last timestamp
                     of the primary timeframe.

        Returns:
            New dict with each DataFrame trimmed to <= reference time.
        """
        if not candles:
            raise Exception("No candles provided for synchronization")

        ref = as_of or self._reference_time(candles)
        if ref is None:
            raise Exception("Could not determine reference time for synchronization")

        synced: Dict[str, pd.DataFrame] = {}
        for tf, df in candles.items():
            if df is None or df.empty:
                synced[tf] = df
                continue
            synced[tf] = df[df.index <= ref]
        return synced

    def is_aligned(self, candles: Dict[str, pd.DataFrame]) -> bool:
        """True if no timeframe contains a candle newer than the primary."""
        ref = self._reference_time(candles)
        if ref is None:
            return False
        for tf, df in candles.items():
            if df is None or df.empty:
                continue
            if df.index[-1] > ref:
                return False
        return True

    def _reference_time(self, candles: Dict[str, pd.DataFrame]):
        """Last timestamp of the primary timeframe (fallback: earliest last)."""
        primary_df = candles[self.primary]
        if primary_df is not None and not primary_df.empty:
            return primary_df.index[-1]
        # Fallback: the oldest "last candle" among all timeframes
        lasts = []
        for df in candles.values():
            if df is not None and not df.empty:
                lasts.append(df.index[-1])
        return min(lasts) if lasts else None
