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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def init_symbol(self, symbol: str) -> bool:
        """
        Warm-up a symbol: fetch 200 candles for M1, M5, M15, write CSVs.

        Returns True if all three timeframes loaded successfully.
        """
        m1  = self._iq.get_candles(symbol, 'M1',  200)
        m5  = self._iq.get_candles(symbol, 'M5',  200)
        m15 = self._iq.get_candles(symbol, 'M15', 200)

        if (m1 is None  or m1.empty  or len(m1) < 2) or \
           (m5 is None  or m5.empty) or \
           (m15 is None or m15.empty):
            logger.warning(f"[DataAdapter] init_symbol: incomplete data for {symbol}")
            return False

        self._store_m1[symbol]  = m1
        self._store_m5[symbol]  = m5
        self._store_m15[symbol] = m15

        current_min = datetime.now(timezone.utc).minute
        self._last_block_m5[symbol]  = current_min // 5
        self._last_block_m15[symbol] = current_min // 15
        self._m5_csv_written[symbol] = current_min // 5

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
        try:
            now_naive = datetime.utcfromtimestamp(broker_epoch)
            current_min = now_naive.minute
            prefix = self._sym_prefix(symbol)
            os.makedirs(self._base_dir, exist_ok=True)

            # ── M1 ──────────────────────────────────────────────────────
            completed_m1 = self._refresh_m1(symbol, now_naive, prefix)
            if completed_m1 is None:
                return None

            # ── M5 ──────────────────────────────────────────────────────
            completed_m5 = self._refresh_m5(symbol, now_naive, current_min, prefix)
            if completed_m5 is None:
                return None

            # ── M15 (resampled from M5) ──────────────────────────────────
            completed_m15 = self._refresh_m15(symbol, now_naive, current_min, prefix)

            current_price = float(self._store_m1[symbol]['close'].iloc[-1])
            return (symbol, completed_m1, completed_m5, completed_m15, current_price)

        except Exception as exc:
            logger.error(f"[DataAdapter] update({symbol}) failed: {exc}")
            return None

    # ------------------------------------------------------------------
    # M1 helpers
    # ------------------------------------------------------------------

    def _refresh_m1(
        self, symbol: str, now_naive: datetime, prefix: str
    ) -> Optional[pd.DataFrame]:
        if self._store_m1.get(symbol) is None:
            df = self._iq.get_candles(symbol, 'M1', 200)
            if df is None or df.empty or len(df) < 2:
                return None
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
            return None
        self._write_csv(completed, self._base_dir, f"{prefix}_M1.csv")
        return completed

    # ------------------------------------------------------------------
    # M5 helpers
    # ------------------------------------------------------------------

    def _refresh_m5(
        self, symbol: str, now_naive: datetime, current_min: int, prefix: str
    ) -> Optional[pd.DataFrame]:
        block = current_min // 5

        if self._store_m5.get(symbol) is None:
            df = self._iq.get_candles(symbol, 'M5', 200)
            if df is None or df.empty or len(df) < 21:
                return None
            self._store_m5[symbol] = df
            self._last_block_m5[symbol] = block
        elif block != self._last_block_m5.get(symbol, -1):
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
                logger.warning(f"[DataAdapter] M5 fetch failed for {symbol} — retry next minute")

        completed = self._drop_forming(self._store_m5[symbol], now_naive, 300)

        # Write CSV only when the 5-min block changes
        if block != self._m5_csv_written.get(symbol, -1):
            self._write_csv(completed, self._base_dir, f"{prefix}_M5.csv")
            self._m5_csv_written[symbol] = block

        return completed

    # ------------------------------------------------------------------
    # M15 helpers (resampled from M5 — no extra API call)
    # ------------------------------------------------------------------

    def _refresh_m15(
        self, symbol: str, now_naive: datetime, current_min: int, prefix: str
    ) -> pd.DataFrame:
        block = current_min // 15
        m5_block = self._last_block_m5.get(symbol, -1)
        m5_current = current_min // 5
        m5_updated = (m5_block == m5_current)

        needs_update = (
            self._store_m15.get(symbol) is None
            or (block != self._last_block_m15.get(symbol, -1) and m5_updated)
        )

        if needs_update and self._store_m5.get(symbol) is not None:
            resampled = (
                self._store_m5[symbol]
                .resample('15min')
                .agg({'open': 'first', 'high': 'max', 'low': 'min',
                      'close': 'last', 'volume': 'sum'})
                .dropna()
            )
            if not resampled.empty:
                completed_calc = self._drop_forming(resampled, now_naive, 900)
                if self._store_m15.get(symbol) is None:
                    self._store_m15[symbol] = completed_calc
                else:
                    combined = pd.concat([self._store_m15[symbol], completed_calc])
                    combined = combined[~combined.index.duplicated(keep='last')].sort_index()
                    self._store_m15[symbol] = combined.tail(200)

                self._last_block_m15[symbol] = block
                self._write_csv(self._store_m15[symbol], self._base_dir, f"{prefix}_M15.csv")
            else:
                logger.warning(f"[DataAdapter] M15 resample empty for {symbol} — retry next minute")

        store_m15 = self._store_m15.get(symbol)
        if store_m15 is not None and not store_m15.empty:
            return self._drop_forming(store_m15, now_naive, 900)
        return pd.DataFrame()

    # ------------------------------------------------------------------
    # Shared utilities
    # ------------------------------------------------------------------

    def _merge(
        self,
        stored: pd.DataFrame,
        fresh: pd.DataFrame,
        gap_threshold: float,
        refetch_fn,
        label: str,
    ) -> pd.DataFrame:
        """
        Merge *fresh* candles into *stored*, auto-refetching 200 candles on gap.
        Verifies closed candles match to catch broker data corrections.
        """
        last_ts  = stored.index[-1]
        first_ts = fresh.index[0]
        gap_sec  = (first_ts - last_ts).total_seconds()

        if gap_sec > gap_threshold:
            logger.warning(f"[DataAdapter] {label}: {gap_sec:.0f}s gap — re-fetching 200 candles")
            full = refetch_fn()
            if full is not None and not full.empty:
                return full
            return stored  # keep old data if refetch fails

        # Verify already-closed candles haven't been revised
        overlap = stored.index.intersection(fresh.index)
        if len(overlap) > 1:
            check = overlap[:-1][-4:]  # last 4 closed candles (exclude forming)
            if not stored.loc[check, 'close'].equals(fresh.loc[check, 'close']):
                logger.warning(f"[DataAdapter] {label}: broker revised closed candles — corrected")

        combined = pd.concat([stored, fresh])
        combined = combined[~combined.index.duplicated(keep='last')].sort_index()
        return combined.tail(200)

    @staticmethod
    def _drop_forming(df: pd.DataFrame, now_naive: datetime, tf_seconds: int) -> pd.DataFrame:
        """Drop the last (still-forming) candle if it started less than tf_seconds ago."""
        if df is None or df.empty:
            return pd.DataFrame()
        age = (now_naive - df.index[-1]).total_seconds()
        if age < tf_seconds:
            return df.iloc[:-1]
        return df

    def _sym_prefix(self, symbol: str) -> str:
        """Return the file prefix for a symbol, e.g. 'EURUSD-OTC' → 'EURUSD_OTC'."""
        return symbol.replace("-", "_")

    @staticmethod
    def _write_csv(df: pd.DataFrame, directory: str, filename: str) -> None:
        if df is None or df.empty:
            return
        try:
            df.to_csv(os.path.join(directory, filename))
        except Exception as exc:
            logger.error(f"[DataAdapter] CSV write failed ({filename}): {exc}")
