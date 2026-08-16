import sys
import logging
import os
import time
import threading
from datetime import datetime, timezone, timedelta
import pandas as pd
from typing import Optional
from monitoring.console_dashboard import ConsoleUI, logger, setup_logging, thai_console_log
import concurrent.futures

setup_logging()

# Core imports (Part 1: Data Feed System only)
from data_feed.bridge_adapter.broker_factory import BrokerFactory
from data_feed.data_adapter import DataAdapter
from data_feed.csv_time_sync import TimeSyncManager


class PureAIRunner:
    def __init__(self):
        self.time_calendar_mgr = TimeSyncManager()
        
        # Track last displayed minute for M1 boundary console output
        self.last_displayed_minute = -1

        # Load settings
        from config_setting.config_loader import load_settings
        self.settings = load_settings(reload=False)
        self.config = self.settings
        
        account_cfg = self.settings.get("account", {})
        self.account_type = account_cfg.get("account_type", "PRACTICE")
        
        # Load symbols from config
        from main import load_symbols
        try:
            self.symbols = load_symbols()
        except Exception as e:
            logger.exception("Failed to load symbols — Zero Tolerance: stopping immediately")
            raise Exception("Configuration error: symbols not loaded — bot stopped")
        
        # Initialize adapter
        ConsoleUI.show_connection_attempt()
        self.data_adapter = BrokerFactory.create_broker(config=self.config)
        if not self.data_adapter.connected:
            ConsoleUI.show_connection_failed()
            sys.exit(1)
            
        ConsoleUI.show_connection_success()
        # Load CSV manager configuration from datafeed_config.json
        from config_setting.config_loader import get_csv_manager_config
        csv_manager_config = get_csv_manager_config()
        base_dir = csv_manager_config.get("base_dir", "data_base/csv/iq_option")
        
        self.candle_adapter = DataAdapter(broker_adapter=self.data_adapter, time_sync_manager=self.time_calendar_mgr, base_dir=base_dir)
        
        # Display balance
        try:
            balance = self.candle_adapter.get_balance()
            ConsoleUI.show_account_info(self.account_type, balance)
            ConsoleUI.show_balance(balance)
        except Exception as e:
            logger.error(f"Failed to initialize runner: {e}")
            import traceback; traceback.print_exc()
            raise RuntimeError("FAIL-FAST: Failed to get balance from broker API") from e

        # Synchronize with broker server time (sync once at startup) - Silent
        self.time_calendar_mgr.sync_server_time(self.data_adapter)

        # Display assets
        ConsoleUI.show_asset_list(self.symbols)
        ConsoleUI.show_data_prep_start(self.symbols)
        
        # Warm-up: fetch 250 candles per symbol and write initial CSVs via DataAdapter
        ready_symbols = []
        not_ready_count = 0
        warmup_broker_epoch = self.time_calendar_mgr.get_broker_epoch()
        for sym in self.symbols:
            if self.candle_adapter.init_symbol(sym, broker_epoch=warmup_broker_epoch):
                ready_symbols.append(sym)
            else:
                not_ready_count += 1
                logger.warning(f"{sym} data incomplete. Dropped.")
                
        self.symbols = ready_symbols # Update symbols to only include ready ones
        ConsoleUI.show_data_prep_result(len(self.symbols), not_ready_count)
        
        # Subscribe to WebSocket streams for live data (only for ready symbols)
        for sym in self.symbols:
            self.data_adapter.start_stream(sym, 'M1', 100)
            self.data_adapter.start_stream(sym, 'M5', 250)
            self.data_adapter.start_stream(sym, 'M15', 70)

        # Initialize a reusable ThreadPoolExecutor
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(self.symbols) if self.symbols else 1)

    def _countdown_to_first_candle(self):
        """คำนวณเวลาถอยหลังรอขอบนาทีถัดไป (วินาทีที่ :01.500) เพื่อให้แท่งเทียนปิดสมบูรณ์ก่อนเริ่มรอบทำงานสด พร้อม Second-by-Second Tracking"""
        tz_thailand = timezone(timedelta(hours=7))
        now = datetime.now(tz_thailand)

        target_time = now.replace(second=1, microsecond=500000)
        if now >= target_time:
            target_time += timedelta(minutes=1)

        total_wait = (target_time - now).total_seconds()
        target_str = target_time.strftime('%H:%M:%S')

        log_msg = f"⏳ [STARTUP] รอแท่งปัจจุบันจบอีก {total_wait:.1f} วินาที... (เริ่มรัน Data Feed สด ณ {target_str})"
        logger.info(log_msg)
        ConsoleUI.show_countdown(f"{total_wait:.1f}", target_str)

        while True:
            now = datetime.now(tz_thailand)
            remaining = (target_time - now).total_seconds()
            if remaining <= 0:
                break

            time_offset = getattr(self.time_calendar_mgr, 'time_offset', 0)
            now_str = now.strftime('%H:%M:%S')
            logger.info(f"[SEC_TRACK] {now_str} | Countdown: {remaining:.1f}s | Offset: {time_offset:.3f}s")
            time.sleep(min(1.0, max(0.1, remaining)))

    def fetch_and_save_data(self, symbol: str, broker_epoch: Optional[float] = None):
        """Delegate candle management to DataAdapter."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if broker_epoch is not None and not isinstance(broker_epoch, (int, float)):
            raise TypeError("broker_epoch must be a float or int")
        if broker_epoch is None:
            broker_epoch = self.time_calendar_mgr.get_broker_epoch()
        return self.candle_adapter.update(symbol, broker_epoch=broker_epoch)

    def run_cycle(self):
        cycle_start = time.time()
        # Ensure connection is active before processing
        try:
            self.data_adapter.ensure_connected()
        except Exception as e:
            logger.error("Connection check failed — stopping cycle")
            raise

        try:
            balance = self.candle_adapter.get_balance()
        except Exception as e:
            logger.exception("Failed to get balance in run_cycle")
            raise RuntimeError("FAIL-FAST: Failed to update balance during cycle") from e
            
        if not self.symbols:
            return
            
        cycle_broker_epoch = self.time_calendar_mgr.get_broker_epoch()

        # Fetch and save data concurrently (writes 8-column CSVs to SSD)
        sym_futures = {}
        for sym in self.symbols:
            sym_futures[sym] = self.executor.submit(self.fetch_and_save_data, sym, cycle_broker_epoch)
        concurrent.futures.wait(sym_futures.values(), timeout=10)

        prices_dict = {}
        for sym in self.symbols:
            try:
                result_val = sym_futures[sym].result()
            except Exception as e:
                logger.exception(f"Error getting future result for {sym}")
                continue

            if not result_val:
                continue

            if not self.candle_adapter.check_warmup(sym):
                continue

            # Read latest close price from RAM cache (Zero Disk I/O)
            try:
                latest_price = self.candle_adapter.get_latest_close(sym)
                prices_dict[sym] = latest_price
            except Exception as e:
                logger.error(f"Failed to get RAM price for {sym}: {e}")
                continue

        tz_thailand = timezone(timedelta(hours=7))
        now_dt = datetime.now(tz_thailand)
        now_str = now_dt.strftime('%H:%M:%S')
        time_offset = getattr(self.time_calendar_mgr, 'time_offset', 0)
        price_parts = [f"{sym}:{price:.5f}" for sym, price in sorted(prices_dict.items())]
        price_str = " | ".join(price_parts) if price_parts else "N/A"
        latency_ms = (time.time() - cycle_start) * 1000

        sec_msg = f"[SEC_TRACK] {now_str} | Prices: [{price_str}] | Balance: ${balance:.2f} | Latency: {latency_ms:.1f}ms | Offset: {time_offset:.3f}s"
        logger.info(sec_msg)

        current_minute = now_dt.minute
        if current_minute != self.last_displayed_minute:
            ConsoleUI.show_prices_and_balance(prices_dict, balance)
            self.last_displayed_minute = current_minute

    def start(self):
        self._countdown_to_first_candle()

        while True:
            try:
                self.run_cycle()
                time.sleep(1.0)

            except KeyboardInterrupt:
                ConsoleUI.show_stopping()
                break
            except Exception as e:
                logger.exception("Error in main loop")
                raise RuntimeError(f"FAIL-FAST: Error in runner execution loop: {e}") from e

if __name__ == "__main__":
    runner = PureAIRunner()
    runner.start()
