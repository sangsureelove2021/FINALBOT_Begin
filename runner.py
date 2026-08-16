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
from data_feed.time_sync_manager import TimeSyncManager
from data_evaluate.economic_news_calendar import ensure_calendar_news, update_all_news_impact

class PureAIRunner:
    def __init__(self):
        self.time_calendar_mgr = TimeSyncManager()
        # Auto-run calendar_news.py on startup if today's calendar file is missing
        self.ensure_calendar_news()
        
        # Initialize price display timer - show prices every 15 seconds
        self.last_display_time = 0.0
        self.last_processed_m1_ts = {}

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
        
        self.candle_adapter = DataAdapter(iq_adapter=self.data_adapter, base_dir=base_dir, time_calendar_mgr=self.time_calendar_mgr)
        
        # Display balance
        try:
            balance = self.data_adapter.api.get_balance()
            ConsoleUI.show_account_info(self.account_type, balance)
            ConsoleUI.show_balance(balance)
        except Exception as e:
            logger.error(f"Failed to initialize runner: {e}")
            import traceback; traceback.print_exc()
            raise RuntimeError("FAIL-FAST: Failed to get balance from broker API") from e

        # Synchronize with broker server time (sync once at startup) - Silent
        self.time_calendar_mgr.sync_server_time(self.data_adapter)
        # Boss: silent mode - no time sync display

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
        
        # Calculate/Evaluate news impact once at startup - DISABLED for silent mode
        # update_all_news_impact(self.symbols)
        
        # Boss: silent mode - no news impact display

    def ensure_calendar_news(self):
        """ตรวจสอบและดึงปฏิทินข่าวประจำวัน"""
        try:
            today_date = datetime.now().date()
            yyyy_mm_dd = today_date.strftime("%Y-%m-%d")
            dd_mm_yyyy = today_date.strftime("%d/%m/%Y")
            txt_filename = f"calendar_{yyyy_mm_dd}.txt"
            txt_path = os.path.join("data_base", "calendar", txt_filename)

            if not os.path.exists(txt_path):
                saved_path = ensure_calendar_news(today_date)
            else:
                saved_path = txt_path

            console_msg = f"ตรวจสอบข่าวและส่งออกไฟล์ปฏิทินข่าว วันที่ {dd_mm_yyyy} แล้ว ชื่อไฟล์ {txt_filename}"
            logger.info(f"[NEWS] {console_msg} -> {saved_path}")
            ConsoleUI.show_calendar_status(console_msg)
        except Exception as e:
            logger.exception(f"Failed to ensure calendar news: {e}")
            raise RuntimeError(f"Failed to ensure calendar news: {e}") from e

    def _countdown_to_first_candle(self):
        """ปรับปรุงสำหรับการรันครั้งแรก: คำนวณเวลาถอยหลังรอขอบนาทีถัดไป (วินาทีที่ :01.500) เพื่อให้แท่งเทียนปิดสมบูรณ์ก่อนเริ่มวิเคราะห์ครั้งแรก"""
        tz_thailand = timezone(timedelta(hours=7))
        now = datetime.now(tz_thailand)

        # คำนวณเวลา target คือ วินาทีที่ 1.500 ของนาทีถัดไป
        target_time = now.replace(second=1, microsecond=500000)
        if now >= target_time:
            target_time += timedelta(minutes=1)

        wait_seconds = (target_time - now).total_seconds()
        target_str = target_time.strftime('%H:%M:%S')

        log_msg = f"⏳ [STARTUP] รอแท่งปัจจุบันจบอีก {wait_seconds:.1f} วินาที... (เริ่มวิเคราะห์แท่งสดใหม่ ณ {target_str})"
        logger.info(log_msg)
        ConsoleUI.show_countdown(f"{wait_seconds:.1f}", target_str)

        if wait_seconds > 0:
            time.sleep(wait_seconds)


    def fetch_and_save_data(self, symbol: str, broker_epoch: float | None = None):
        """Delegate all candle management to DataAdapter - Silent mode."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if broker_epoch is not None and not isinstance(broker_epoch, (int, float)):
            raise TypeError("broker_epoch must be a float or int")
        if broker_epoch is None:
            broker_epoch = self.time_calendar_mgr.get_broker_epoch()
        # Boss: silent mode - no fetch_and_save_data logging
        return self.candle_adapter.update(symbol, broker_epoch=broker_epoch)



    def run_cycle(self):
        # Ensure connection is active before processing (handles WinError 10054 drops) - Silent
        try:
            self.data_adapter.ensure_connected()
        except Exception as e:
            # Only show error on connection failure, not routine checks
            logger.error("Connection check failed — stopping cycle")
            raise

        try:
            balance = self.data_adapter.api.get_balance()
        except Exception as e:
            logger.exception("Failed to get balance in run_cycle")
            raise RuntimeError("FAIL-FAST: Failed to update balance during cycle") from e
            
        # Run all symbols concurrently for data fetching and CSV writing - Silent mode
        if not self.symbols:
            # Boss: silent mode - no warning for empty symbols
            return
            
        import concurrent.futures
        
        # Calculate consistent broker epoch for all symbols in this cycle - Silent
        cycle_broker_epoch = self.time_calendar_mgr.get_broker_epoch()

        # Fetch and save data concurrently (highly optimized, writes CSV only) - Silent
        sym_futures = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.symbols)) as executor:
            for sym in self.symbols:
                sym_futures[sym] = executor.submit(self.fetch_and_save_data, sym, cycle_broker_epoch)
            concurrent.futures.wait(sym_futures.values(), timeout=10)
            
        # Boss: silent mode - no concurrent futures logging

        prices_dict = {}
        for sym in self.symbols:
            try:
                result_val = sym_futures[sym].result()
            except Exception as e:
                logger.exception(f"Error getting future result for {sym}")
                continue

            if not result_val:
                continue

            # Check warmup data
            if not self.candle_adapter.check_warmup(sym):
                continue

            # อ่านไฟล์ CSV จาก disk สำหรับ M1, M5, M15 (สลับกลับมาใช้วิธีเดิมตามคำสั่งบอส)
            try:
                candles_dict = {
                    'M1': self.candle_adapter.read_symbol_csv(sym, 'M1'),
                    'M5': self.candle_adapter.read_symbol_csv(sym, 'M5'),
                    'M15': self.candle_adapter.read_symbol_csv(sym, 'M15')
                }
            except Exception as e:
                logger.error(f"Failed to read CSV files for {sym}: {e}")
                continue

            if 'M1' in candles_dict and not candles_dict['M1'].empty:
                prices_dict[sym] = float(candles_dict['M1']['close'].iloc[-1])

            # ส่วนงานที่ 2 (Orchestrator) — ส่ง candles_dict จากการอ่านไฟล์ CSV (ประมวลผลเมื่อมีแท่ง M1 ใหม่เท่านั้น)
            try:
                if 'M1' in candles_dict and not candles_dict['M1'].empty:
                    latest_m1_ts = candles_dict['M1'].index[-1]
                    if self.last_processed_m1_ts.get(sym) != latest_m1_ts:
                        self.orchestrator.process_cycle(sym, candles_dict=candles_dict)
                        self.last_processed_m1_ts[sym] = latest_m1_ts
            except Exception as e:
                logger.error(f"Orchestrator failed for {sym}: {e}")
                raise RuntimeError(f"FAIL-FAST: Orchestrator failed for {sym}") from e

        # แสดงสรุปราคาและยอดเงินบรรทัดเดียว - อัพเดททุก 15 วินาที
        current_time = time.time()
        if prices_dict and (current_time - self.last_display_time >= 15.0):
            ConsoleUI.show_prices_and_balance(prices_dict, balance)
            self.last_display_time = current_time

    def start(self):
        import time
        from datetime import datetime
        
        # รอกระทั่งถึงขอบนาทีถัดไปที่วินาที :01.500 ก่อนเริ่ม Cycle แรก
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
