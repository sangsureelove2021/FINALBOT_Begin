"""
DataAdapter — Live Price CSV Manager for FINALBOT

Wraps IQOptionAdapter and owns all CSV file I/O for candle data.
Responsibilities:
  • Keep per-symbol in-memory candle stores (M1 / M5 / M15)
  • Detect and repair data gaps automatically
  • Write CSVs to data/csv/<symbol>/ on each update
  • Derive M15 candles by resampling M5 (no extra API call)
  • Track which 5-min / 15-min blocks have already been written

No backtest, no simulated time, no historical-only slicing.
"""

import os
import logging
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Gap thresholds
_M1_GAP_SEC = 300    # > 5 min gap on M1 → re-fetch 200 candles
_M5_GAP_SEC = 1500   # > 25 min gap on M5 → re-fetch 200 candles
_M15_GAP_SEC = 4500  # > 75 min gap on M15 → re-fetch 200 candles


class DataAdapter:
    """
    Manages live candle stores and CSV snapshots for all tracked symbols.

    Usage::

        from core.data.data_adapter import DataAdapter
        from core.data.iq_option_adapter import IQOptionAdapter

        iq = IQOptionAdapter(account_type="PRACTICE")
        adapter = DataAdapter(iq_adapter=iq, base_dir="data/DATA IQ")

        # Warm-up: fetch 200 candles and write initial CSVs
        adapter.init_symbol("EURUSD-OTC")

        # Called every minute by the main loop
        result = adapter.update("EURUSD-OTC", broker_epoch=time.time() + offset)
        if result:
            symbol, m1, m5, m15, price = result
    """

    def __init__(self, iq_adapter, base_dir: str = "data/DATA IQ"):
        self._iq = iq_adapter
        self._base_dir = base_dir

        # Per-symbol candle stores
        self._store_m1:  Dict[str, Optional[pd.DataFrame]] = {}
        self._store_m5:  Dict[str, Optional[pd.DataFrame]] = {}
        self._store_m15: Dict[str, Optional[pd.DataFrame]] = {}

        # Track last written block indices to avoid redundant disk writes
        self._last_block_m5:      Dict[str, int] = {}
        self._last_block_m15:     Dict[str, int] = {}
        self._m5_csv_written:     Dict[str, int] = {}
        self._m15_csv_written:    Dict[str, int] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def init_symbol(self, symbol: str) -> bool:
        """
        Warm-up a symbol: fetch 200 candles for M1, M5, M15, write CSVs.

        Returns True if all three timeframes loaded successfully.
        """
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")

        m1  = self._iq.get_candles(symbol, 'M1',  200)
        m5  = self._iq.get_candles(symbol, 'M5',  200)
        m15 = self._iq.get_candles(symbol, 'M15', 200)

        if (m1 is None  or m1.empty  or len(m1) < 2) or \
           (m5 is None  or m5.empty) or \
           (m15 is None or m15.empty):
            raise ValueError("Incomplete data during init_symbol")

        self._store_m1[symbol]  = m1
        self._store_m5[symbol]  = m5
        self._store_m15[symbol] = m15

        epoch_now = int(datetime.now(timezone.utc).timestamp())
        self._last_block_m5[symbol]  = epoch_now // 300
        self._last_block_m15[symbol] = epoch_now // 900
        self._m5_csv_written[symbol] = epoch_now // 300
        self._m15_csv_written[symbol] = epoch_now // 900

        os.makedirs(self._base_dir, exist_ok=True)
        self._write_csv(m1,  self._base_dir, f"{self._sym_prefix(symbol)}_M1.csv")
        self._write_csv(m5,  self._base_dir, f"{self._sym_prefix(symbol)}_M5.csv")
        self._write_csv(m15, self._base_dir, f"{self._sym_prefix(symbol)}_M15.csv")

        logger.info(f"[DataAdapter] {symbol} initialised — M1:{len(m1)} M5:{len(m5)} M15:{len(m15)}")
        return True

    def update(
        self,
        symbol: str,
        broker_epoch: float,
    ) -> Optional[Tuple[str, pd.DataFrame, pd.DataFrame, pd.DataFrame, float]]:
        """
        Refresh candle stores for *symbol* using the broker-synchronised epoch.

        Returns a tuple ``(symbol, completed_m1, completed_m5, completed_m15, current_price)``
        or ``None`` on failure.
        """
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if not isinstance(broker_epoch, (int, float)):
            raise TypeError("broker_epoch must be a float or int")

        try:
            now_naive = datetime.utcfromtimestamp(broker_epoch)
            current_block_m5 = int(broker_epoch) // 300
            current_block_m15 = int(broker_epoch) // 900
            prefix = self._sym_prefix(symbol)
            os.makedirs(self._base_dir, exist_ok=True)

            # ── M1 ──────────────────────────────────────────────────────
            completed_m1 = self._refresh_m1(symbol, now_naive, prefix)
            if completed_m1 is None:
                raise ValueError("M1 refresh failed")

            # ── M5 ──────────────────────────────────────────────────────
            completed_m5 = self._refresh_m5(symbol, now_naive, current_block_m5, prefix)
            if completed_m5 is None:
                raise ValueError("M5 refresh failed")

            # ── M15 (resampled from M5) ──────────────────────────────────
            completed_m15 = self._refresh_m15(symbol, now_naive, current_block_m15, prefix)

            store_m1_df = self._store_m1[symbol]
            if not isinstance(store_m1_df, pd.DataFrame) or store_m1_df.empty or 'close' not in store_m1_df.columns:
                raise ValueError("M1 store invalid")

            current_price = float(store_m1_df['close'].iloc[-1])
            return (symbol, completed_m1, completed_m5, completed_m15, current_price)

        except Exception as e:
            logger.exception(f"[DataAdapter] update failed: {e}")
            raise Exception(str(e))

    # ------------------------------------------------------------------
    # M1 helpers
    # ------------------------------------------------------------------

    def _refresh_m1(
        self, symbol: str, now_naive: datetime, prefix: str
    ) -> Optional[pd.DataFrame]:
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if not isinstance(now_naive, datetime):
            raise TypeError("now_naive must be a datetime")
        if not isinstance(prefix, str):
            raise TypeError("prefix must be a string")

        if self._store_m1[symbol] is None:
            df = self._iq.get_candles(symbol, 'M1', 200)
            if df is None or df.empty or len(df) < 2:
                raise ValueError("M1 fetch failed")
            self._store_m1[symbol] = df
        else:
            fresh = self._iq.get_candles(symbol, 'M1', 5)
            if fresh is not None and not fresh.empty:
                self._store_m1[symbol] = self._merge(
                    self._store_m1[symbol], fresh,
                    gap_threshold=_M1_GAP_SEC,
                    refetch_fn=lambda: self._iq.get_candles(symbol, 'M1', 200),
                    label=f"M1 {symbol}",
                )

        completed = self._drop_forming(self._store_m1[symbol], now_naive, 60)
        if completed.empty:
            raise ValueError("M1 completed is empty")
        self._write_csv(completed, self._base_dir, f"{prefix}_M1.csv")
        return completed

    # ------------------------------------------------------------------
    # M5 helpers
    # ------------------------------------------------------------------

    def _refresh_m5(
        self, symbol: str, now_naive: datetime, current_block: int, prefix: str
    ) -> Optional[pd.DataFrame]:
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if not isinstance(now_naive, datetime):
            raise TypeError("now_naive must be a datetime")
        if not isinstance(current_block, int):
            raise TypeError("current_block must be an integer")
        if not isinstance(prefix, str):
            raise TypeError("prefix must be a string")

        block = current_block

        if self._store_m5[symbol] is None:
            df = self._iq.get_candles(symbol, 'M5', 200)
            if df is None or df.empty or len(df) < 21:
                raise ValueError("M5 fetch failed")
            self._store_m5[symbol] = df
            self._last_block_m5[symbol] = block
        elif block != self._last_block_m5[symbol]:
            fresh = self._iq.get_candles(symbol, 'M5', 5)
            if fresh is not None and not fresh.empty:
                self._store_m5[symbol] = self._merge(
                    self._store_m5[symbol], fresh,
                    gap_threshold=_M5_GAP_SEC,
                    refetch_fn=lambda: self._iq.get_candles(symbol, 'M5', 200),
                    label=f"M5 {symbol}",
                )
                self._last_block_m5[symbol] = block
            else:
                raise Exception(f"M5 fetch failed for {symbol} — retry next minute")

        completed = self._drop_forming(self._store_m5[symbol], now_naive, 300)

        # Write CSV only when the 5-min block changes
        if block != self._m5_csv_written[symbol]:
            self._write_csv(completed, self._base_dir, f"{prefix}_M5.csv")
            self._m5_csv_written[symbol] = block

        return completed

    # ------------------------------------------------------------------
    # M15 helpers (resampled from M5 — no extra API call)
    # ------------------------------------------------------------------

    def _refresh_m15(
        self, symbol: str, now_naive: datetime, current_block: int, prefix: str
    ) -> Optional[pd.DataFrame]:
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if not isinstance(now_naive, datetime):
            raise TypeError("now_naive must be a datetime")
        if not isinstance(current_block, int):
            raise TypeError("current_block must be an integer")
        if not isinstance(prefix, str):
            raise TypeError("prefix must be a string")

        block = current_block

        if self._store_m15[symbol] is None:
            df = self._iq.get_candles(symbol, 'M15', 200)
            if df is None or df.empty or len(df) < 21:
                raise ValueError("M15 fetch failed")
            self._store_m15[symbol] = df
            self._last_block_m15[symbol] = block
        elif block != self._last_block_m15[symbol]:
            m5_df = self._store_m5[symbol]
            if m5_df is not None and not m5_df.empty:
                from core.data.timeframe_sync import TimeframeSync
                resampled = TimeframeSync().resample(m5_df.tail(15), 'M5', 'M15')
                self._store_m15[symbol] = self._merge(
                    self._store_m15[symbol], resampled,
                    gap_threshold=_M15_GAP_SEC,
                    refetch_fn=lambda: self._iq.get_candles(symbol, 'M15', 200),
                    label=f"M15 {symbol}",
                )
                self._last_block_m15[symbol] = block
            else:
                raise Exception(f"M5 store missing for {symbol} — cannot resample M15")

        completed = self._drop_forming(self._store_m15[symbol], now_naive, 900)

        # Write CSV only when the 15-min block changes
        if block != self._m15_csv_written[symbol]:
            self._write_csv(completed, self._base_dir, f"{prefix}_M15.csv")
            self._m15_csv_written[symbol] = block

        return completed

    # ------------------------------------------------------------------
    # Shared utilities
    # ------------------------------------------------------------------

    def _merge(
        self,
        stored: Optional[pd.DataFrame],
        fresh: Optional[pd.DataFrame],
        gap_threshold: float,
        refetch_fn,
        label: str,
    ) -> pd.DataFrame:
        """
        Merge *fresh* candles into *stored*, auto-refetching 200 candles on gap.
        Verifies closed candles match to catch broker data corrections.
        """
        if stored is not None and not isinstance(stored, pd.DataFrame):
            raise TypeError("stored must be a pandas DataFrame or None")
        if fresh is not None and not isinstance(fresh, pd.DataFrame):
            raise TypeError("fresh must be a pandas DataFrame or None")
        if not isinstance(gap_threshold, (int, float)):
            raise TypeError("gap_threshold must be a float or int")
        if not isinstance(label, str):
            raise TypeError("label must be a string")

        if stored is None or stored.empty:
            raise ValueError("Stored DataFrame is empty in _merge")

        if fresh is None or fresh.empty:
            raise ValueError("Fresh DataFrame is empty in _merge")

        last_ts  = stored.index[-1]
        first_ts = fresh.index[0]
        gap_sec  = (first_ts - last_ts).total_seconds()

        if gap_sec > gap_threshold:
            full = refetch_fn()
            if full is not None and not full.empty:
                return full
            raise ValueError("Refetch failed after gap detection")

        # Verify already-closed candles haven't been revised
        overlap = stored.index.intersection(fresh.index)
        if len(overlap) > 1 and 'close' in stored.columns and 'close' in fresh.columns:
            check = overlap[:-1][-4:]  # last 4 closed candles (exclude forming)
            if len(check) > 0:
                if not stored.loc[check, 'close'].equals(fresh.loc[check, 'close']):
                    logger.warning(f"[DataAdapter] {label}: broker revised closed candles — corrected")

        combined = pd.concat([stored, fresh])
        combined = combined[~combined.index.duplicated(keep='last')].sort_index()
        return combined.tail(200)

    @staticmethod
    def _drop_forming(df: Optional[pd.DataFrame], now_naive: datetime, tf_seconds: int) -> pd.DataFrame:
        """Drop the last (still-forming) candle if it started less than tf_seconds ago."""
        if df is None:
            raise ValueError("DataFrame is None in _drop_forming")
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame or None")
        if not isinstance(now_naive, datetime):
            raise TypeError("now_naive must be a datetime")
        if not isinstance(tf_seconds, int):
            raise TypeError("tf_seconds must be an integer")

        if df.empty:
            raise ValueError("DataFrame is empty in _drop_forming")
        age = (now_naive - df.index[-1]).total_seconds()
        if age < tf_seconds:
            return df.iloc[:-1].copy()
        return df.copy()

    def _sym_prefix(self, symbol: str) -> str:
        """Return the file prefix for a symbol, e.g. 'EURUSD-OTC' → 'EURUSD_OTC'."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        return symbol.replace("-", "_")

    @staticmethod
    def _write_csv(df: Optional[pd.DataFrame], directory: str, filename: str) -> None:
        if df is not None and not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame or None")
        if not isinstance(directory, str):
            raise TypeError("directory must be a string")
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")

        if df is None or df.empty:
            raise ValueError("DataFrame is empty in _write_csv")
        df.to_csv(os.path.join(directory, filename))
