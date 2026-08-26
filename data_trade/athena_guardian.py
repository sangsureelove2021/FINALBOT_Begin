"""
Athena Guardian & Execution Core — Part 3
=========================================
สถาปัตยกรรม: Part 3 จัดการยิงออเดอร์ ติดตามผล และคุมเป้าหมาย 2-Wins Daily Lock
- ยิงออเดอร์เข้า IQ Option ตรงตามคำสั่งจาก Part 2
- ควบคุมขนาดไม้เริ่มต้น 35 บาท (THB)
- ติดตามผลลัพธ์การหมดเวลาสัญญา (Win / Loss / PnL)
- ระบบคุมเป้าหมายรายวัน: ชนะครบ 2 ไม้ ➡️ ล็อคกำไร & สั่งปิดระบบทันที
- ส่งรายงานความคืบหน้าสดเข้า Telegram ของบอสอัตโนมัติ
"""

import os
import time
import json
import logging
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta

from data_trade.execution_gate.broker_executor import BrokerExecutor, resolve_api
from monitoring.telegram_bridge import TelegramBridge

logger = logging.getLogger("AthenaGuardian")


class AthenaGuardian:
    """Master Trade Execution & Daily 2-Win Lock Guardian (Part 3)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, telegram_bridge: Optional[TelegramBridge] = None):
        self.config = config or {}
        self.stake = float(self.config.get("stake", 35.0))
        self.target_wins = int(self.config.get("target_wins", 2))
        self.max_daily_losses = int(self.config.get("max_daily_losses", 2))
        
        self.broker_executor = BrokerExecutor()
        self.telegram_bridge = telegram_bridge
        
        # State tracking
        self.daily_wins = 0
        self.daily_losses = 0
        self.daily_pnl = 0.0
        self.active_trades: Dict[str, Dict[str, Any]] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self.target_reached = False
        
        # Default Telegram Chat ID from environment or auto-detected
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if self.chat_id:
            try:
                self.chat_id = int(self.chat_id)
            except ValueError:
                pass

        logger.info(
            f"[AthenaGuardian] Initialized | Stake: {self.stake} THB | Target Wins: {self.target_wins} | "
            f"Max Losses: {self.max_daily_losses}"
        )

    def set_telegram_chat_id(self, chat_id: int):
        """Set or update target Telegram chat ID for notifications."""
        self.chat_id = chat_id
        logger.info(f"[AthenaGuardian] Telegram notifications linked to chat_id: {chat_id}")

    def notify_boss(self, message: str):
        """Send formatted message to Boss via Telegram if chat_id is available."""
        if self.telegram_bridge and self.chat_id:
            try:
                self.telegram_bridge.send_message(self.chat_id, message, parse_mode="Markdown")
            except Exception as e:
                logger.warning(f"[AthenaGuardian] Telegram notification error: {e}")

    def execute_signal(self, signal: Dict[str, Any], broker_adapter: Any) -> Dict[str, Any]:
        """
        Processes a signal from Part 2 AthenaBrain.
        Places order if A+ setup and daily target not reached.
        """
        with self._lock:
            symbol = signal.get("symbol", "")
            action = signal.get("action", "WAIT").upper()
            confidence = signal.get("confidence", 0)
            expiry_minutes = signal.get("expiry_minutes", 5)
            reason = signal.get("reason", "")
            stake = float(signal.get("stake", self.stake))

            # 1. Check if Daily Win Target is already reached
            if self.target_reached or self.daily_wins >= self.target_wins:
                logger.info(f"[AthenaGuardian] Target already reached ({self.daily_wins}/{self.target_wins} Wins). Skipping signal.")
                return {"status": "TARGET_REACHED", "message": "Daily 2-win target completed"}

            # 2. Check Action
            if action not in ("CALL", "PUT"):
                return {"status": "SKIPPED", "message": f"Action is {action}"}

            # 3. Check Active Trades (Prevent duplicate entries on same symbol)
            if symbol in self.active_trades:
                logger.warning(f"[AthenaGuardian] Trade already active for {symbol}. Skipping.")
                return {"status": "BUSY", "message": f"Active trade in progress for {symbol}"}

            logger.info(f"[AthenaGuardian] ⚡ EXECUTING A+ SIGNAL: {symbol} {action} | Stake: {stake} THB | Confidence: {confidence}%")

            # 4. Place Order via BrokerExecutor
            try:
                exec_result = self.broker_executor.execute_order(
                    symbol=symbol,
                    action=action,
                    expiry_minutes=expiry_minutes,
                    stake=stake,
                    broker_adapter=broker_adapter
                )

                if exec_result.get("status") != "SUCCESS":
                    logger.error(f"[AthenaGuardian] Order placement failed for {symbol}: {exec_result.get('error')}")
                    return exec_result

                order_id = exec_result.get("order_id")
                trade_info = {
                    "order_id": order_id,
                    "symbol": symbol,
                    "action": action,
                    "stake": stake,
                    "expiry_minutes": expiry_minutes,
                    "confidence": confidence,
                    "reason": reason,
                    "entry_time": datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S"),
                    "start_epoch": time.time(),
                    "broker_adapter": broker_adapter
                }

                self.active_trades[symbol] = trade_info

                # Notify Boss on Telegram
                msg = (
                    f"🎯 *เอเธน่ายิงออเดอร์แล้วค่ะบอส!*\n\n"
                    f"• *คู่เงิน:* `{symbol}`\n"
                    f"• *ทิศทาง:* *{action}* ⚡\n"
                    f"• *ขนาดไม้:* `{stake:.2f}` บาท (THB)\n"
                    f"• *สัญญา:* `{expiry_minutes}` นาที\n"
                    f"• *ความมั่นใจ:* `{confidence}%` (A+ Sniper Setup)\n"
                    f"• *เหตุผล:* _{reason}_\n\n"
                    f"⏳ กำลังติดตามผลลัพธ์อย่างใกล้ชิดค่ะ..."
                )
                self.notify_boss(msg)

                # Spawn background thread to wait and resolve trade outcome
                resolver_thread = threading.Thread(
                    target=self._wait_and_resolve_trade,
                    args=(trade_info,),
                    daemon=True,
                    name=f"TradeResolver-{symbol}-{order_id}"
                )
                resolver_thread.start()

                return {"status": "SUCCESS", "order_id": order_id, "trade_info": trade_info}

            except Exception as e:
                logger.exception(f"[AthenaGuardian] Exception executing order for {symbol}: {e}")
                return {"status": "ERROR", "error": str(e)}

    def _wait_and_resolve_trade(self, trade_info: Dict[str, Any]):
        """Background worker that waits for candle expiry and checks win/loss."""
        symbol = trade_info["symbol"]
        order_id = trade_info["order_id"]
        expiry_minutes = trade_info["expiry_minutes"]
        stake = trade_info["stake"]
        broker_adapter = trade_info["broker_adapter"]
        api = resolve_api(broker_adapter)

        # Wait for expiration duration + small buffer
        wait_seconds = (expiry_minutes * 60) + 3
        logger.info(f"[AthenaGuardian] Monitoring trade {symbol} (Order ID: {order_id}) for {wait_seconds}s...")
        time.sleep(wait_seconds)

        # Query result from broker API
        outcome = "UNKNOWN"
        pnl = 0.0
        try:
            if api and hasattr(api, "check_win_v3"):
                pnl = api.check_win_v3(order_id)
                if pnl > 0:
                    outcome = "WIN"
                elif pnl < 0:
                    outcome = "LOSS"
                else:
                    outcome = "EQUAL"
            elif api and hasattr(api, "get_optioninfo"):
                info = api.get_optioninfo(1)
                outcome = "WIN" if info.get("result") == "win" else "LOSS"
                pnl = float(info.get("profit", 0.0))
        except Exception as e:
            logger.warning(f"[AthenaGuardian] Could not retrieve trade result automatically for {order_id}: {e}")
            outcome = "COMPLETED"

        with self._lock:
            if symbol in self.active_trades:
                del self.active_trades[symbol]

            if outcome == "WIN":
                self.daily_wins += 1
                self.daily_pnl += (pnl if pnl > 0 else stake * 0.85)
                win_text = f"🏆 *ผลการเทรด: ชนะ (WIN) +{self.daily_pnl:.2f} บาท!*"
            elif outcome == "LOSS":
                self.daily_losses += 1
                self.daily_pnl -= stake
                win_text = f"🛑 *ผลการเทรด: แพ้ (LOSS) -{stake:.2f} บาท*"
            else:
                win_text = f"⚖️ *ผลการเทรด: เสมอ / จบสัญญา*"

            trade_record = {
                **trade_info,
                "outcome": outcome,
                "pnl": pnl,
                "close_time": datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")
            }
            self.trade_history.append(trade_record)

            # Check if 2 Wins Target Achieved
            if self.daily_wins >= self.target_wins:
                self.target_reached = True
                summary_msg = (
                    f"👑 *บอสคะ! บอทชนะครบ 2 ไม้ตามเป้าหมายรายวันแล้วค่ะ!* 🇹🇭🎉\n\n"
                    f"{win_text}\n\n"
                    f"📊 *สรุปผลงานวันนี้:*\n"
                    f"• ชนะสะสม: `{self.daily_wins}/{self.target_wins}` ไม้ (100% Target Met)\n"
                    f"• กำไรสุทธิวันนี้: `+{self.daily_pnl:.2f}` บาท (THB)\n\n"
                    f"🔒 *ระบบทำการล็อคกำไรและหยุดการเทรดสำหรับวันนี้เรียบร้อยค่ะ!*"
                )
                self.notify_boss(summary_msg)
                logger.info(f"[AthenaGuardian] 👑 DAILY 2-WINS TARGET ACHIEVED! (+{self.daily_pnl:.2f} THB). SHUTTING DOWN TRADING.")
            else:
                progress_msg = (
                    f"{win_text}\n\n"
                    f"• คู่เงิน: `{symbol}`\n"
                    f"• ความคืบหน้าเป้าหมาย: `{self.daily_wins}/{self.target_wins}` ไม้ชนะ\n"
                    f"• กำไรสะสม: `{self.daily_pnl:+.2f}` บาท\n\n"
                    f"🔍 เอเธน่ากำลังสแกนหา A+ Setup ไม้ถัดไปค่ะ..."
                )
                self.notify_boss(progress_msg)
