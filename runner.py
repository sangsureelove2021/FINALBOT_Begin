import sys
import logging
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional
from monitoring.console_dashboard import ConsoleUI, logger, setup_logging
import concurrent.futures

# Logging should only be setup once in main.py
# setup_logging() is called in main.py, not here

# Core imports (Part 1: Data Feed System only)
from data_feed.bridge_adapter.broker_factory import BrokerFactory
from data_feed.data_adapter import DataAdapter
from data_feed.csv_time_sync import TimeSyncManager

# Load settings and symbols at the module level for clarity
from config_setting.config_loader import load_settings, get_symbols, get_csv_manager_config


class PureAIRunner:
    def __init__(self):
        self.time_calendar_mgr = TimeSyncManager()

        # Track last displayed minute for M1 boundary console output
        self.last_displayed_minute = -1
        self.last_minute_lock = threading.Lock()  # แก้ไข: เพิ่ม lock เพื่อป้องกัน race condition

        # Load settings and symbols
        self.settings = load_settings(reload=False)
        account_cfg = self.settings.get("account", {})
        self.account_type = account_cfg.get("account_type", "PRACTICE")
        
        # Load symbols from config, ensuring it's done once
        try:
            self.symbols = get_symbols()
        except Exception as e:
            logger.exception("Failed to load symbols — Zero Tolerance: stopping immediately")
            raise Exception("Configuration error: symbols not loaded — bot stopped")
        
        # Initialize adapter
        ConsoleUI.show_connection_attempt()
        self.data_adapter = BrokerFactory.create_broker(config=self.settings)
        if not self.data_adapter.connected:
            ConsoleUI.show_connection_failed()
            sys.exit(1)
            
        ConsoleUI.show_connection_success()
        # Load CSV manager configuration from datafeed_config.json
        csv_manager_config = get_csv_manager_config()
        base_dir = csv_manager_config.get("base_dir", "data_base/csv/iq_option")
        
        self.candle_adapter = DataAdapter(broker_adapter=self.data_adapter, time_sync_manager=self.time_calendar_mgr, base_dir=base_dir)
        
        # รายงานขั้นตอน 1: ล็อกอินและรายงานข้อมูลบัญชี
        logger.info("🚀 [STEP 1] ระบบกำลังเชื่อมต่อกับ IQ Option...")
        try:
            balance = self.candle_adapter.get_balance()
            self.balance = balance  # Store balance as an instance attribute
            ConsoleUI.show_account_info(self.account_type, balance)
            ConsoleUI.show_balance(balance)
            logger.info(f"✅ [STEP 1] ล็อกอินสำเร็จ | บัญชี: {self.account_type} | ยอดเงิน: ${self.balance:.2f}")
        except Exception as e:
            logger.error(f"❌ [STEP 1] ล็อกอินล้มเหลว: {e}")
            import traceback; traceback.print_exc()
            raise RuntimeError("FAIL-FAST: Failed to get balance from broker API") from e

        # รายงานขั้นตอน 2: ซิงเวลา
        logger.info("⏰ [STEP 2] กำลังซิงโครงเวลากับบรูกเกอร์...")
        self.time_calendar_mgr.sync_server_time(self.data_adapter)
        logger.info("✅ [STEP 2] ซิงเวลาเสร็จเรียบร้อย")

        # รายงานขั้นตอน 3: ตรวจสอบคู่เงิน
        logger.info(f"💱 [STEP 3] ตรวจสอบคู่เงินที่เปิดให้เทรด...")
        logger.info(f"📋 [STEP 3] คู่เงินที่จะเทรด: {self.symbols}")
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
        # Note: M1 stream is already started inside init_symbol() above.
        # Only start M5 and M15 here to avoid duplicate M1 subscription.
        for sym in self.symbols:
            self.data_adapter.start_stream(sym, 'M5', 250)
            self.data_adapter.start_stream(sym, 'M15', 70)

        # Initialize a reusable ThreadPoolExecutor
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=len(self.symbols) if self.symbols else 1)
        
        # ── Part 2: Orchestrator (Data Evaluate) will be added later ──────────
        # self.orchestrator = Orchestrator()
        # logger.info("[Runner] Orchestrator (Part 2) initialized")
        self.orchestrator = None  # Placeholder for Part 2
        logger.info("[Runner] Part 1 complete - CSV files ready for Part 2")

    def _countdown_to_first_candle(self):
        """คำนวณเวลาถอยหลังรอขอบนาทีถัดไป (วินาทีที่ :01.500) เพื่อให้แท่งเทียนปิดสมบูรณ์ก่อนเริ่มรอบทำงานสด พร้อม Second-by-Second Tracking"""
        tz_thailand = timezone(timedelta(hours=7))
        now = datetime.now(tz_thailand)

        target_time = now.replace(second=1, microsecond=500000)
        if now >= target_time:
            target_time += timedelta(minutes=1)

        total_wait = (target_time - now).total_seconds()
        target_str = target_time.strftime('%H:%M:%S')

        log_msg = f"⏳ [STEP 6] รอแท่งปัจจุบันจบอีก {total_wait:.1f} วินาที... (เริ่มรัน Data Feed สด ณ {target_str})"
        logger.info(log_msg)
        logger.info("💡 [STEP 6] หลังจานี้บอทจะดาวน์โหลดแค่ 2 แท่งเทียนในทุกรอบ!")
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

    def run_cycle(self):
        cycle_start = time.time()
        
        # รายงานขั้นตอน 4: ดาวน์โหลดข้อมูลประวัติ (2 แท่งเทียนต่อรอบ)
        logger.info("📊 [STEP 4] ดาวน์โหลดข้อมูลประวัติราคา (2 แท่งเทียนต่อรอบ)...")
        
        # Ensure connection is active before processing
        try:
            self.data_adapter.ensure_connected()
            logger.info("✅ [STEP 4] เชื่อมต่อเบอร์เกอร์สำเร็จ")
        except Exception as e:
            logger.error(f"❌ [STEP 4] เชื่อมต่อเบอร์เกอร์ล้มเหลว: {e}")
            raise

        if not self.symbols:
            logger.warning("⚠️ [STEP 4] ไม่มีคู่เงินในการทำงาน")
            return

        cycle_broker_epoch = self.time_calendar_mgr.get_broker_epoch()

        # Fetch and save data concurrently (writes 8-column CSVs to SSD)
        sym_futures = {}
        for sym in self.symbols:
            logger.info(f"🔄 [STEP 4] ดาวน์โหลดข้อมูลสำหรับคู่เงิน: {sym}")
            sym_futures[sym] = self.executor.submit(self.candle_adapter.update, sym, broker_epoch=cycle_broker_epoch)
        concurrent.futures.wait(sym_futures.values(), timeout=10)
        logger.info("✅ [STEP 4] ดาวน์โหลดข้อมูลเสร็จเรียบร้อย")

        # Verify results and log prices, but don't pass them to Orchestrator
        # This aligns with the Zero RAM Data Leakage principle.
        processed_symbols = set()
        for sym in self.symbols:
            try:
                # .result() will re-raise exceptions from the thread
                sym_futures[sym].result()
                processed_symbols.add(sym)
            except Exception as e:
                logger.exception(f"Error getting result for {sym}")
                continue

        tz_thailand = timezone(timedelta(hours=7))
        now_dt = datetime.now(tz_thailand)
        now_str = now_dt.strftime('%H:%M:%S')
        time_offset = getattr(self.time_calendar_mgr, 'time_offset', 0)
        latency_ms = (time.time() - cycle_start) * 1000

        sec_msg = f"[SEC_TRACK] {now_str} | Balance: ${self.balance:.2f} | Latency: {latency_ms:.1f}ms | Offset: {time_offset:.3f}s"
        logger.info(sec_msg)

        current_minute = now_dt.minute
        with self.last_minute_lock:
            if current_minute != self.last_displayed_minute:
                ConsoleUI.show_prices_and_balance({}, self.balance) # Don't show prices here anymore
                self.last_displayed_minute = current_minute
            
            # ── Part 2: Run Orchestrator for each symbol (read CSV → analyze → output .txt) ──
            # Part 2 is not implemented yet, this section is disabled
            # logger.info("🤖 [STEP 5] เริ่มการวิเคราะห์ข้อมูลด้วย AI...")
            # for sym in processed_symbols:
            #     try:
            #         self.orchestrator.process_cycle(symbol=sym)
            #     except Exception as e:
            #         logger.exception(f"❌ [STEP 5] AI วิเคราะห์ล้มเหลว: {sym} - {e}")
            
            # Part 1 complete: CSV files have been written successfully
            logger.info(f"✅ [STEP 5] Part 1 complete - CSV files updated for {len(processed_symbols)} symbols")

    def start(self):
        logger.info("🎯 [STEP 6] เริ่มการทำงานของบอทที่แท้จริง (ดาวน์โหลด 2 แท่งเทียนต่อรอบ)...")
        self._countdown_to_first_candle()

        while True:
            try:
                self.run_cycle()
                time.sleep(1.0)

            except KeyboardInterrupt:
                logger.info("🛑 [STEP 6] ผู้ใช้ปิดบอท")
                ConsoleUI.show_stopping()
                break
            except Exception as e:
                logger.exception(f"❌ [STEP 6] เกิดข้อผิดพลาดในการทำงาน: {e}")
                raise RuntimeError(f"FAIL-FAST: Error in runner execution loop: {e}") from e

if __name__ == "__main__":
    runner = PureAIRunner()
    runner.start()
