"""
Timeframe Sync
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Aligns multi-timeframe candle data so that every timeframe refers
to the same point in time.

Why this matters:
    M1, M5, M15, M60, D1 candles arrive on different clocks. Before
    multi-timeframe engines (e.g. MTF) compare them, they must be
    trimmed to a common "as-of" timestamp — otherwise a higher
    timeframe could leak future information into a lower one.
"""

import pandas as pd
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Minutes per timeframe — used to order timeframes and resample
TF_MINUTES = {
    'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30,
    'M60': 60, 'H1': 60, 'H4': 240, 'D1': 1440,
}


class TimeframeSync:
    """Aligns multi-timeframe candle data to a common reference time."""

    def __init__(self, primary: str = 'M5'):
        """
        Args:
            primary: timeframe whose latest candle defines the reference time.
        """
        self.primary = primary

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
            return {}

        ref = as_of or self._reference_time(candles)
        if ref is None:
            return candles

        synced: Dict[str, pd.DataFrame] = {}
        for tf, df in candles.items():
            if df is None or df.empty:
                synced[tf] = df
                continue
            try:
                synced[tf] = df[df.index <= ref]
            except TypeError:
                # Index not datetime-comparable — pass through untouched
                synced[tf] = df
        return synced

    def is_aligned(self, candles: Dict[str, pd.DataFrame]) -> bool:
        """True if no timeframe contains a candle newer than the primary."""
        ref = self._reference_time(candles)
        if ref is None:
            return False
        for tf, df in candles.items():
            if df is None or df.empty:
                continue
            try:
                if df.index[-1] > ref:
                    return False
            except (TypeError, IndexError):
                continue
        return True

    def resample(self, base_df: pd.DataFrame,
                 from_tf: str, to_tf: str) -> pd.DataFrame:
        """
        Resample candles from a lower timeframe up to a higher one.

        Args:
            base_df: OHLCV DataFrame at `from_tf`.
            from_tf: source timeframe (e.g. 'M1').
            to_tf:   target timeframe (e.g. 'M5'). Must be larger.

        Returns:
            Resampled OHLCV DataFrame.
        """
        from_m = TF_MINUTES.get(from_tf)
        to_m = TF_MINUTES.get(to_tf)
        if not from_m or not to_m or to_m <= from_m:
            raise ValueError(f"Cannot resample {from_tf} -> {to_tf}")

        rule = f"{to_m}min"
        agg = {
            'open': 'first', 'high': 'max', 'low': 'min',
            'close': 'last', 'volume': 'sum',
        }
        cols = {c: agg[c] for c in base_df.columns if c in agg}
        return base_df.resample(rule).agg(cols).dropna()

    def _reference_time(self, candles: Dict[str, pd.DataFrame]):
        """Last timestamp of the primary timeframe (fallback: earliest last)."""
        primary_df = candles.get(self.primary)
        if primary_df is not None and not primary_df.empty:
            try:
                return primary_df.index[-1]
            except IndexError:
                pass
        # Fallback: the oldest "last candle" among all timeframes
        lasts = []
        for df in candles.values():
            if df is not None and not df.empty:
                try:
                    lasts.append(df.index[-1])
                except IndexError:
                    continue
        return min(lasts) if lasts else None
