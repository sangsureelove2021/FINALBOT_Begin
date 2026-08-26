"""
ATHENA SNIPER BOT — Master In-Memory Runner
============================================
สถาปัตยกรรมระบบ 3 ส่วน (Pure In-Memory Pipeline):
- Part 1 (Data Feed): ดึงแท่งเทียนสดจาก IQ Option (M1, M5, M15) เก็บใน RAM 100% (ไม่เขียน CSV)
- Part 2 (Athena Brain): วิเคราะห์ Multi-Timeframe, Price Action Rejection, Stochastic/RSI ใน RAM (< 10 ms)
  และฟันธงสัญญาณ CALL / PUT ทันที
- Part 3 (Athena Guardian): รับสัญญาณ Action ตรง ยิงออเดอร์ไม้ละ 35 บาท (THB)
  ติดตามผลลัพธ์ และควบคุมเป้าหมายรายวัน "ชนะครบ 2 ไม้ ➡️ ล็อคกำไร & หยุดเทรดทันที"
- Telegram Bridge: เชื่อมต่อสนทนาและแจ้งเตือนผลสดเข้ามือถือของบอส 100%
"""

import os
import sys
import time
import signal
import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from monitoring.console_dashboard import ConsoleUI, logger, setup_logging, disable_quick_edit, thai_console_log
from config_setting.config_loader import load_settings, get_symbols
from data_feed.bridge_adapter.broker_factory import BrokerFactory
from data_feed.data_adapter import DataAdapter
from data_evaluate.athena_brain import AthenaBrain
from data_trade.athena_guardian import AthenaGuardian
from monitoring.telegram_bridge import TelegramBridge

setup_logging()
disable_quick_edit()

_ACTIVE_RUNNER: Optional["AthenaSniperRunner"] = None


def graceful_exit(signum=None, frame=None):
    """Handle exit signals cleanly and immediately terminate the process."""
    global _ACTIVE_RUNNER
    try:
        ConsoleUI.show_stopping()
    except Exception:
        pass

    if _ACTIVE_RUNNER is not None:
        try:
            if hasattr(_ACTIVE_RUNNER, "data_feed") and _ACTIVE_RUNNER.data_feed:
                _ACTIVE_RUNNER.data_feed.disconnect()
        except Exception:
            pass

    # Hard exit at OS level
    os._exit(0)


class AthenaSniperRunner:
    """Master In-Memory Coordinator for ATHENA SNIPER BOT (3-Part Direct Pipeline)."""

    def __init__(self):
        global _ACTIVE_RUNNER
        _ACTIVE_RUNNER = self

        self.settings = load_settings(reload=True)
        self.account_type = self.settings.get("account", {}).get("account_type", "DEMO")
        self.stake = float(self.settings.get("account", {}).get("stake_per_trade", 35.0))
        self.target_wins = int(self.settings.get("account", {}).get("target_wins", 2))

        thai_console_log("=" * 70)
        thai_console_log("👑 ATHENA SNIPER BOT — 2-WINS DAILY PROFIT LOCK (THB)")
        thai_console_log(f"   ขนาดไม้ลงทุน: {self.stake:.2f} บาท | เป้าหมาย: ชนะ {self.target_wins} ไม้/วัน ล็อคกำไรทันที")
        thai_console_log("   โหมดการทำงาน: Pure In-Memory Pipeline (Zero Latency - No SSD I/O)")
        thai_console_log("=" * 70)

        # ── 1. Part 1: Connect Broker and Ingest Data in RAM ──────────────────
        ConsoleUI.show_connection_attempt()
        self.data_feed: DataAdapter = BrokerFactory.create_broker(config=self.settings)
        if not self.data_feed.connected:
            ConsoleUI.show_connection_failed()
            os._exit(1)
        ConsoleUI.show_connection_success()

        # Dynamically register active asset IDs
        try:
            import iqoptionapi.constants as OP_code
            if hasattr(self.data_feed, "api") and self.data_feed.api:
                init_data = self.data_feed.api.get_all_init() or {}
                for cat in ["turbo", "binary"]:
                    for aid, ainfo in init_data.get("result", {}).get(cat, {}).get("actives", {}).items():
                        name = ainfo.get("name", "").replace("front.", "")
                        if name:
                            OP_code.ACTIVES[name] = int(aid)
        except Exception as e:
            logger.warning(f"[AthenaSniperRunner] Dynamic active registration note: {e}")

        # Load trading symbols
        self.symbols: List[str] = get_symbols()
        ConsoleUI.show_asset_list(self.symbols)
        ConsoleUI.show_time_offset(self.data_feed.time_calendar_mgr.time_offset)

        # Display Account Balance
        try:
            balance = self.data_feed.get_balance()
            ConsoleUI.show_account_info(self.account_type, balance)
        except Exception as e:
            logger.exception("Failed to get balance from broker API")
            raise RuntimeError("FAIL-FAST: Failed to get balance from broker API") from e

        # ── 2. Start Telegram AI Bridge (Background Thread) ───────────────────
        try:
            self.telegram_bridge = TelegramBridge()
            telegram_thread = threading.Thread(
                target=self.telegram_bridge.start_polling,
                daemon=True,
                name="TelegramBridgeWorker"
            )
            telegram_thread.start()
            logger.info("[AthenaSniperRunner] Telegram AI Bridge started in background thread.")
        except Exception as e:
            logger.warning(f"[AthenaSniperRunner] Telegram bridge note: {e}")
            self.telegram_bridge = None

        # ── 3. Part 2: Initialize Athena Brain Core ───────────────────────────
        min_conf = self.settings.get("ai_mode", {}).get("min_confidence", 85)
        self.athena_brain = AthenaBrain(config={"min_confidence": min_conf, "stake": self.stake})

        # ── 4. Part 3: Initialize Athena Guardian & Execution ─────────────────
        self.athena_guardian = AthenaGuardian(
            config={"stake": self.stake, "target_wins": self.target_wins},
            telegram_bridge=self.telegram_bridge
        )

        # ── 5. Part 1 Historical Warm-Up (250 completed candles in RAM) ────────
        ConsoleUI.show_data_prep_start(self.symbols)
        self.data_feed.warmup_all_symbols(self.symbols)
        self.symbols = getattr(self.data_feed, "ready_symbols", self.symbols)
        ConsoleUI.show_data_prep_result(len(self.symbols), 0)

    def _countdown_to_first_candle(self):
        """Sleep directly until the first completed candle minute boundary (:01.500)."""
        tz_thailand = timezone(timedelta(hours=7))
        now = datetime.now(tz_thailand)

        target_time = now.replace(second=1, microsecond=500000)
        if now >= target_time:
            target_time += timedelta(minutes=1)

        total_wait = (target_time - now).total_seconds()
        target_str = target_time.strftime("%H:%M:%S")

        ConsoleUI.show_countdown(f"{total_wait:.1f}", target_str)
        if total_wait > 0:
            time.sleep(total_wait)

    def run_cycle(self):
        """Execute one complete In-Memory Ingestion, Athena Evaluation, and Trade Cycle."""
        self.data_feed.ensure_connected()
        if not self.symbols:
            return

        # 1. Check if Daily Target has been reached
        if self.athena_guardian.target_reached or self.athena_guardian.daily_wins >= self.target_wins:
            thai_console_log(f"👑 [DAILY TARGET LOCKED] ชนะครบ {self.athena_guardian.daily_wins}/{self.target_wins} ไม้แล้วค่ะ (+{self.athena_guardian.daily_pnl:.2f} THB) — หยุดพักระบบ")
            return

        # 2. Part 1: Ingest candles into RAM
        prices_dict = self.data_feed.ingest_cycle(self.symbols)

        # 3. Part 2: Athena Parallel In-Memory AI Evaluation (Gemini 3.5 Flash Lite)
        symbols_candles = {sym: self.data_feed.get_candles_ram(sym) for sym in self.symbols}
        evaluations: List[Dict[str, Any]] = self.athena_brain.evaluate_all(symbols_candles)

        # Display Live Telemetry on Console Dashboard
        thai_console_log("-" * 70)
        thai_console_log(f"🧠 [ATHENA AI DECISION ENGINE] ผลการวิเคราะห์สด {len(evaluations)} คู่เงิน (Gemini 3.5 Flash Lite):")
        for ev in evaluations:
            sym = ev.get("symbol")
            act = ev.get("action")
            conf = ev.get("confidence", 0)
            price = ev.get("m5_close", 0.0)
            reason = ev.get("reason", "")
            
            icon = "⚡" if act in ("CALL", "PUT") else "⏳"
            thai_console_log(f"  {icon} {sym:<12} | Action: {act:<4} | Conf: {conf:>2}% | Price: {price:.5f} | {reason[:45]}")
        thai_console_log("-" * 70)

        # 4. Part 3: Execution Check (Pick highest confidence A+ signal)
        best_signal = evaluations[0] if evaluations else None
        if best_signal and best_signal.get("action") in ("CALL", "PUT") and best_signal.get("confidence", 0) >= self.athena_brain.min_confidence:
            thai_console_log(f"🎯 [A+ SNIPER ENTRY] ยิงออเดอร์ {best_signal.get('symbol')} {best_signal.get('action')} (มั่นใจ {best_signal.get('confidence')}%)")
            exec_res = self.athena_guardian.execute_signal(best_signal, broker_adapter=self.data_feed._broker)
            if exec_res.get("status") == "SUCCESS":
                ConsoleUI.show_order_success(exec_res.get("order_id"))
            else:
                thai_console_log(f"   ⚠️ ผลการยิงออเดอร์: {exec_res.get('status')} ({exec_res.get('message') or exec_res.get('error')})")

    def start(self):
        """Main Loop: Runs strictly at each minute boundary (:01.500) and sleeps between intervals."""
        self._countdown_to_first_candle()
        tz_thailand = timezone(timedelta(hours=7))

        while True:
            try:
                self.run_cycle()

                # If target reached, sleep longer or gracefully hold
                if self.athena_guardian.target_reached:
                    time.sleep(60)
                    continue

                # Sleep to next minute boundary (:01.500)
                now = datetime.now(tz_thailand)
                target_time = now.replace(second=1, microsecond=500000)
                if target_time <= now:
                    target_time += timedelta(minutes=1)

                sleep_seconds = max(0.5, (target_time - now).total_seconds())
                time.sleep(sleep_seconds)

            except KeyboardInterrupt:
                graceful_exit()
            except Exception as e:
                logger.exception(f"[AthenaSniperRunner] Error in execution loop: {e}")
                time.sleep(5)


# Compatibility alias
DataFeedRunner = AthenaSniperRunner
PureAIRunner = AthenaSniperRunner


if __name__ == "__main__":
    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, graceful_exit)

    runner = AthenaSniperRunner()
    runner.start()
