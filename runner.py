"""
PureAIRunner — Main Bot Runner
===============================
Manages the end-to-end bot execution lifecycle:
1. Broker connection & tradable asset discovery
2. Time synchronization & economic news calendar
3. Historical candle warm-up (250 candles for M1, M5, M15)
4. Minute-boundary event loop (:01.500) for candle ingestion (Part 1) and analysis (Part 2)
"""

import sys
import time
import logging
import concurrent.futures
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict

from monitoring.console_dashboard import ConsoleUI, logger, setup_logging
from config_setting.config_loader import load_settings, get_symbols, get_csv_manager_config
from data_feed.bridge_adapter.broker_factory import BrokerFactory
from data_feed.data_adapter import DataAdapter
from data_feed.csv_time_sync import TimeSyncManager
from data_feed.news_calendar import ensure_calendar_news, check_news_impact
from data_evaluate.orchestrator import Orchestrator

setup_logging()


class PureAIRunner:
    """Core coordinator managing data ingestion and analysis execution."""

    def __init__(self):
        self.settings = load_settings(reload=True)
        self.account_type = self.settings.get("account", {}).get("account_type", "PRACTICE")
        
        # 1. Connect to Broker
        ConsoleUI.show_connection_attempt()
        self.data_adapter = BrokerFactory.create_broker(config=self.settings)
        if not self.data_adapter.connected:
            ConsoleUI.show_connection_failed()
            sys.exit(1)
        ConsoleUI.show_connection_success()

        # 2. Discover tradable assets
        configured_symbols = get_symbols()
        self.symbols: List[str] = self.data_adapter.get_open_symbols(configured_symbols)
        if not self.symbols:
            raise RuntimeError("FAIL-FAST: No tradable assets currently open on broker")
        ConsoleUI.show_asset_list(self.symbols)

        # 3. Initialize Time Sync & Server Offset
        self.time_calendar_mgr = TimeSyncManager(data_adapter=self.data_adapter)
        self.time_calendar_mgr.sync_server_time(self.data_adapter)
        self.time_calendar_mgr.start_time_sync_thread()
        ConsoleUI.show_time_offset(self.time_calendar_mgr.time_offset)

        # 4. Initialize Data Adapter (Part 1 Core) & Display Balance
        csv_mgr_cfg = get_csv_manager_config()
        base_dir = csv_mgr_cfg.get("base_dir", "data_base/csv/iq_option")
        self.candle_adapter = DataAdapter(
            broker_adapter=self.data_adapter,
            time_sync_manager=self.time_calendar_mgr,
            base_dir=base_dir
        )
        
        try:
            balance = self.candle_adapter.get_balance()
            ConsoleUI.show_account_info(self.account_type, balance)
        except Exception as e:
            logger.exception("Failed to get account balance from broker")
            raise RuntimeError("FAIL-FAST: Failed to get balance from broker API") from e

        # 5. Load Economic News Calendar for Today
        try:
            ensure_calendar_news(show_ui=True)
        except Exception as e:
            logger.exception(f"[Runner] Economic news calendar check failed: {e}")

        # 6. Historical Data Warm-Up (250 candles for M1, M5, M15)
        ConsoleUI.show_data_prep_start(self.symbols)
        ready_symbols = []
        not_ready_count = 0
        warmup_epoch = self.time_calendar_mgr.get_broker_epoch()

        for sym in self.symbols:
            if self.candle_adapter.init_symbol(sym, broker_epoch=warmup_epoch):
                ready_symbols.append(sym)
            else:
                not_ready_count += 1
                logger.warning(f"[Runner] {sym} data incomplete — skipped.")

        self.symbols = ready_symbols
        if not self.symbols:
            raise RuntimeError("FAIL-FAST: Zero assets passed historical data warm-up")
        ConsoleUI.show_data_prep_result(len(self.symbols), not_ready_count)

        # 7. Start Streaming & Thread Pool Executor
        for sym in self.symbols:
            self.data_adapter.start_stream(sym, 'M1', 255)
            self.data_adapter.start_stream(sym, 'M5', 255)
            self.data_adapter.start_stream(sym, 'M15', 255)

        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max(1, len(self.symbols)),
            thread_name_prefix="FeedWorker"
        )

        # 8. Initialize Orchestrator (Part 2: PROCESS & Data Evaluate)
        self.orchestrator = Orchestrator()

    def _countdown_to_first_candle(self):
        """Sleep directly until the first completed candle minute boundary (:01.500)."""
        tz_thailand = timezone(timedelta(hours=7))
        now = datetime.now(tz_thailand)

        target_time = now.replace(second=1, microsecond=500000)
        if now >= target_time:
            target_time += timedelta(minutes=1)

        total_wait = (target_time - now).total_seconds()
        target_str = target_time.strftime('%H:%M:%S')

        ConsoleUI.show_countdown(f"{total_wait:.1f}", target_str)
        if total_wait > 0:
            time.sleep(total_wait)

    def fetch_and_save_data(self, symbol: str, broker_epoch: Optional[float] = None) -> Optional[str]:
        """Fetch completed candles, update RAM cache, and enqueue CSV write."""
        if broker_epoch is None:
            broker_epoch = self.time_calendar_mgr.get_broker_epoch()
        return self.candle_adapter.update(symbol, broker_epoch=broker_epoch)

    def run_cycle(self):
        """Execute one completed candle cycle at the minute boundary (:01.500)."""
        # Verify broker connection
        self.data_adapter.ensure_connected()

        # Update balance
        try:
            balance = self.candle_adapter.get_balance()
        except Exception as e:
            logger.exception("Failed to update balance during cycle")
            raise RuntimeError("FAIL-FAST: Failed to update balance during cycle") from e

        if not self.symbols:
            return

        cycle_broker_epoch = self.time_calendar_mgr.get_broker_epoch()

        # Ingest candles for all active symbols concurrently
        sym_futures = {
            sym: self.executor.submit(self.fetch_and_save_data, sym, cycle_broker_epoch)
            for sym in self.symbols
        }
        concurrent.futures.wait(sym_futures.values(), timeout=10)

        # Extract latest close prices from RAM
        prices_dict: Dict[str, float] = {}
        for sym in self.symbols:
            try:
                res = sym_futures[sym].result()
                if res and self.candle_adapter.check_warmup(sym):
                    prices_dict[sym] = self.candle_adapter.get_latest_close(sym)
            except Exception as e:
                logger.exception(f"Error reading cycle candle for {sym}: {e}")

        # Display prices & balance on console
        ConsoleUI.show_prices_and_balance(prices_dict, balance)

        # Execute Part 2 (Data Evaluate / Orchestrator) for each active symbol
        for sym in self.symbols:
            if sym in prices_dict:
                try:
                    candles_ram = self.candle_adapter.get_candles_ram(sym)
                    news_impact = check_news_impact(sym)
                    self.orchestrator.process_cycle(symbol=sym, candles_dict=candles_ram, news_impact=news_impact)
                except Exception as e:
                    logger.exception(f"Failed to process Part 2 analysis for {sym}: {e}")

    def start(self):
        """Main Loop: Runs strictly at each minute boundary (:01.500) and sleeps between intervals."""
        self._countdown_to_first_candle()
        tz_thailand = timezone(timedelta(hours=7))

        while True:
            try:
                self.run_cycle()

                # Sleep directly to next minute boundary (:01.500)
                now = datetime.now(tz_thailand)
                target_time = now.replace(second=1, microsecond=500000)
                if target_time <= now:
                    target_time += timedelta(minutes=1)

                sleep_seconds = max(0.5, (target_time - now).total_seconds())
                time.sleep(sleep_seconds)

            except KeyboardInterrupt:
                ConsoleUI.show_stopping()
                break
            except Exception as e:
                logger.exception("Error in runner execution loop")
                raise RuntimeError(f"FAIL-FAST: Error in runner execution loop: {e}") from e


if __name__ == "__main__":
    runner = PureAIRunner()
    runner.start()
