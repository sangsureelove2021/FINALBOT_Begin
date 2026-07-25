import sys
import logging
import os
import time
from datetime import datetime, timezone, timedelta
import pandas as pd

from monitoring.console_dashboard import ConsoleUI, logger, setup_logging

setup_logging()

# Core imports
from data_feed.iq_option_adapter import IQOptionAdapter
from data_feed.data_adapter import DataAdapter

class PureAIRunner:
    def __init__(self):
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

        # Calculate time offset between local clock        # 4. Synchronize with broker time
        try:
            server_time = self.data_adapter.api.get_server_timestamp()
            local_time = int(time.time())
            self.time_offset = server_time - local_time
            logger.info(f"Server time offset: {self.time_offset} seconds")
        except Exception as e:
            logger.error(f"Failed to get server time offset")
            self.time_offset = 0.0

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
            self.data_adapter.start_stream(sym, 'M1', 250)
            self.data_adapter.start_stream(sym, 'M5', 250)
        
        self._countdown_to_first_candle()

    def _countdown_to_first_candle(self):
        """แสดงเวลาที่จะเริ่มบันทึกครั้งแรก"""
        now = datetime.now()
        if now.second < 3:
            remaining = 3 - now.second
        else:
            remaining = 60 - now.second + 3

        tz_thailand = timezone(timedelta(hours=7))
        target = datetime.now(tz_thailand) + timedelta(seconds=remaining)
        target_str = target.strftime('%H:%M:%S')

        # Calculate mode_str before using it
        # self.symbols is a list, use the first symbol or default
        symbol_list = self.symbols if hasattr(self, 'symbols') and self.symbols else ["EURGBP"]
        symbol = symbol_list[0] if isinstance(symbol_list, list) else "EURGBP"

        if "OTC" in symbol.upper():
            mode_str = "OTC (Over-The-Counter)"
        else:
            mode_str = "REGULAR (Exchange)"

        ConsoleUI.show_countdown(remaining, target_str)
        # ConsoleUI.show_mode_info(mode_str) # Display the dynamically created mode_str
    def fetch_and_save_data(self, symbol):
        """Delegate all candle management to DataAdapter."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        broker_epoch = time.time() + self.time_offset
        return self.candle_adapter.update(symbol, broker_epoch=broker_epoch)

    def _get_latest_price_from_csv(self, symbol: str) -> float:
        import os
        try:
            csv_path = os.path.join("data_base", "csv", "iq_option", symbol, f"{symbol}_M1.csv")
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        last_line = lines[-1].strip().split(',')
                        return float(last_line[4])
        except Exception as e:
            logger.exception(f"Failed to read latest price from CSV for {symbol}")
        return 0.0

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
        
        # Fetch and save data concurrently (highly optimized, writes CSV only)
        sym_futures = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.symbols)) as executor:
            for sym in self.symbols:
                sym_futures[sym] = executor.submit(self.fetch_and_save_data, sym)
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
                # Calculate seconds until the next minute's 3rd second.
                if now.second < 3:
                    sleep_sec = 3 - now.second
                else:
                    sleep_sec = 60 - now.second + 3
                
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
