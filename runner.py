import sys
import logging
import os
import time
import threading
from datetime import datetime, timezone, timedelta
import pandas as pd

from monitoring.console_dashboard import ConsoleUI, logger, setup_logging

setup_logging()

# Core imports
from data_feed.iq_option_adapter import IQOptionAdapter
from data_feed.data_adapter import DataAdapter
from data_feed.time_calendar_manager import TimeCalendarManager

class PureAIRunner:
    def __init__(self):
        # Auto-run calendar_news.py on startup if today's calendar file is missing
        self.time_calendar_mgr = TimeCalendarManager()

        # Load settings
        from config_setting.config_loader import load_settings
        self.settings = load_settings(reload=False)
        
        # Initialize Orchestrator
        from data_evaluate.orchestrator import Orchestrator
        self.orchestrator = Orchestrator()
        
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
        self.data_adapter = IQOptionAdapter(account_type=self.account_type)
        if not self.data_adapter.connected:
            ConsoleUI.show_connection_failed()
            sys.exit(1)
            
        ConsoleUI.show_connection_success()
        # Load CSV manager configuration from datafeed_config.json
        from config_setting.config_loader import get_csv_manager_config
        csv_manager_config = get_csv_manager_config()
        base_dir = csv_manager_config.get("base_dir", "data_base/csv/iq_option")
        
        self.candle_adapter = DataAdapter(iq_adapter=self.data_adapter, base_dir=base_dir)
        
        # Display balance
        try:
            balance = self.data_adapter.api.get_balance()
        except Exception as e:
            logger.error(f"Failed to initialize runner: {e}")
            import traceback; traceback.print_exc()
            balance = 0.0
            
        ConsoleUI.show_account_info(self.account_type, balance)

        # Synchronize with broker server time and start background time sync thread
        self.time_calendar_mgr.sync_server_time(self.data_adapter)
        self.time_calendar_mgr.start_time_sync_thread()

        # Display assets
        ConsoleUI.show_asset_list(self.symbols)
        ConsoleUI.show_data_prep_start(self.symbols)
        
        # Warm-up: fetch 250 candles per symbol and write initial CSVs via DataAdapter
        ready_symbols = []
        not_ready_count = 0
        for sym in self.symbols:
            if self.candle_adapter.init_symbol(sym):
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
        
        self._countdown_to_first_candle()

    def _countdown_to_first_candle(self):
        """แสดงเวลาที่จะเริ่มบันทึกครั้งแรก"""
        now = datetime.now()
        if now.second < 1:
            remaining = 1 - now.second
        else:
            remaining = 60 - now.second + 1

        tz_thailand = timezone(timedelta(hours=7))
        target = datetime.now(tz_thailand) + timedelta(seconds=remaining)
        target_str = target.strftime('%H:%M:%S')

        # Calculate mode_str by evaluating all active symbols
        symbol_list = self.symbols if hasattr(self, 'symbols') and isinstance(self.symbols, list) and self.symbols else []
        if not symbol_list:
            mode_str = "UNKNOWN (No Symbols)"
        else:
            otc_symbols = [s for s in symbol_list if "OTC" in s.upper()]
            if len(otc_symbols) == len(symbol_list):
                mode_str = "OTC (Over-The-Counter)"
            elif len(otc_symbols) == 0:
                mode_str = "REGULAR (Exchange)"
            else:
                mode_str = "MIXED (OTC & REGULAR)"

        ConsoleUI.show_countdown(remaining, target_str)
        # ConsoleUI.show_mode_info(mode_str) # Display the dynamically created mode_str


    def fetch_and_save_data(self, symbol: str, broker_epoch: float | None = None):
        """Delegate all candle management to DataAdapter."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if broker_epoch is not None and not isinstance(broker_epoch, (int, float)):
            raise TypeError("broker_epoch must be a float or int")
        if broker_epoch is None:
            broker_epoch = self.time_calendar_mgr.get_broker_epoch()
        return self.candle_adapter.update(symbol, broker_epoch=broker_epoch)

    def _find_csv_path(self, symbol: str, timeframe: str) -> str | None:
        """Helper to find the correct path for a symbol's CSV file."""
        import os
        base_dir = os.path.join("data_base", "csv", "iq_option")
        symbol_hyphenated = symbol.replace('_', '-')
        symbol_underscored = symbol.replace('-', '_')

        # Check for directory variations
        for sym_variant in [symbol, symbol_hyphenated, symbol_underscored]:
            symbol_dir = os.path.join(base_dir, sym_variant)
            if os.path.exists(symbol_dir):
                # Check for file variations
                for file_sym_variant in [symbol, symbol_hyphenated, symbol_underscored]:
                    path = os.path.join(symbol_dir, f"{file_sym_variant}_{timeframe}.csv")
                    if os.path.exists(path):
                        return path
        return None

    def _get_latest_price_from_csv(self, symbol: str) -> float:
        import os
        from data_feed.csv_writer import read_csv_safe
        try:
            csv_path = self._find_csv_path(symbol, "M1")
            if csv_path:
                df = read_csv_safe(csv_path)
                if not df.empty and 'close' in df.columns:
                    return float(df['close'].iloc[-1])
        except Exception as e:
            logger.exception(f"Failed to read latest price from CSV for {symbol}")
        return 0.0

    def _check_warmup_data(self, symbol: str) -> bool:
        """
        Gatekeeper function to ensure we have enough CSV data before calling orchestrator.
        """
        import os
        from data_feed.csv_writer import read_csv_safe
        reqs = {"M1": 100, "M5": 250, "M15": 50}
        for tf, req_len in reqs.items():
            csv_path = self._find_csv_path(symbol, tf)
            if not csv_path:
                logger.warning(f"[{symbol}] Missing {tf} CSV file.")
                return False
            try:
                df = read_csv_safe(csv_path)
                line_count = len(df)
                if line_count < req_len:
                    logger.warning(f"[{symbol}] Insufficient {tf} data: has {line_count}, required >={req_len}")
                    return False
            except Exception as e:
                logger.exception(f"[{symbol}] Error checking {tf} CSV length.")
                return False
        return True

    def run_cycle(self):
        # Ensure connection is active before processing (handles WinError 10054 drops)
        try:
            self.data_adapter.ensure_connected()
        except Exception as e:
            logger.exception("Failed to check/restore connection — stopping cycle")
            raise

        try:
            balance = self.data_adapter.api.get_balance()
        except Exception as e:
            logger.exception("Failed to get balance in run_cycle")
            balance = None
            
        # Run all symbols concurrently for data fetching and CSV writing
        if not self.symbols:
            logger.warning("[WARN] ไม่มีคู่เงินใดๆ ที่พร้อมทำงานในรอบนี้")
            return
            
        import concurrent.futures
        
        # Calculate consistent broker epoch for all symbols in this cycle
        cycle_broker_epoch = self.time_calendar_mgr.get_broker_epoch()

        # Fetch and save data concurrently (highly optimized, writes CSV only)
        sym_futures = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.symbols)) as executor:
            for sym in self.symbols:
                sym_futures[sym] = executor.submit(self.fetch_and_save_data, sym, cycle_broker_epoch)
            concurrent.futures.wait(sym_futures.values())

        prices_dict = {}
        for sym in self.symbols:
            try:
                result_val = sym_futures[sym].result()
            except Exception as e:
                logger.exception(f"Error getting future result for {sym}")
                continue

            if not result_val:
                continue

            # Check if warmup data is met before populating prices or calling Orchestrator
            if not self._check_warmup_data(sym):
                continue

            # บังคับดึงข้อมูล OHLCV (ราคา) จากโฟลเดอร์เท่านั้น ห้ามส่งทาง RAM
            prices_dict[sym] = self._get_latest_price_from_csv(sym)
            
            # Trigger Orchestrator without passing any data via RAM
            try:
                self.orchestrator.process_cycle(sym)
            except Exception as e:
                logger.exception(f"Orchestrator failed for {sym}")

        # แสดงสรุปราคาและยอดเงินบรรทัดเดียว
        if prices_dict:
            ConsoleUI.show_prices_and_balance(prices_dict, balance)

    def start(self):
        import time
        from datetime import datetime
        while True:
            try:
                now = datetime.now()
                # Sleep until the 1st second of the next minute to allow broker candle closure
                sleep_sec = (1 - now.second) % 60
                if sleep_sec == 0:
                    sleep_sec = 60
                time.sleep(sleep_sec)
                self.run_cycle()

            except KeyboardInterrupt:
                ConsoleUI.show_stopping()
                break
            except Exception as e:
                logger.exception("Error in main loop")
                time.sleep(5)

if __name__ == "__main__":
    runner = PureAIRunner()
    runner.start()
