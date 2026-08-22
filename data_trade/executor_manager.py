"""
Executor Manager — Master Controller for Part 3 (Data Trade & Execution)
==========================================================================
หน้าที่: ผู้บัญชาการเทรดเท่านั้น (Trade & Risk Commander)

Flow:
1. รับสะกิดจาก Orchestrator Part 2 ผ่าน on_orchestrator_payload_saved()
2. รวบรวม pending symbols ใน thread-safe queue
3. flush → สั่ง SystemPrompt.process_ai_decisions_concurrent(tasks)
4. รับ decisions กลับ → วน ExecutionGate (confidence >= 70%) → BrokerExecutor

Concurrency: รองรับ 1 ถึง 10+ คู่เงินพร้อมกันโดยไม่รอคิว
"""

import os
import logging
import traceback
import threading
from typing import Dict, Any, Optional, List, Tuple

from config_setting.config_loader import load_settings
from data_trade.ai_decision.system_prompt import SystemPrompt
from data_trade.execution_gate.gate_controller import ExecutionGate
from data_trade.execution_gate.money_manager import MoneyManager
from data_trade.execution_gate.broker_executor import BrokerExecutor
from data_trade.execution_gate.order_tracker import OrderTracker
from monitoring.console_dashboard import thai_console_log, ConsoleUI

logger = logging.getLogger("ExecutorManager")


class ExecutorManager:
    """Central entry point for Part 3 trade decision and execution pipeline."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.settings = config or load_settings(reload=False)
        self.execution_gate = ExecutionGate(config=self.settings)
        self.money_manager = MoneyManager(config=self.settings)
        self.broker_executor = BrokerExecutor()
        self.order_tracker = OrderTracker(money_manager=self.money_manager)

        # ── Trading Mode ────────────────────────────────────────────────────
        self.trading_mode = str(
            self.settings.get("account", {}).get("trading_mode", "AI AUTO_BOT")
        ).strip().upper()

        # ── Concurrent Dispatch State (thread-safe) ─────────────────────────
        self._pending_lock = threading.Lock()
        self._pending_tasks: Dict[str, str] = {}   # {symbol: prompt_filepath}
        self._flush_lock = threading.Lock()         # ป้องกัน concurrent flush ซ้อน
        self._broker_adapter: Optional[Any] = None  # เก็บ broker adapter ล่าสุด

        logger.info(
            f"[ExecutorManager] Initialized | Mode: '{self.trading_mode}' | "
            f"N-Symbol Concurrent Dispatch: ENABLED | Confidence Gate: >= 70%"
        )

    def on_orchestrator_payload_saved(
        self,
        prompt_filepath: str,
        symbol: str,
        broker_adapter: Optional[Any] = None
    ) -> None:
        """
        Event Handler: เรียกทันทีที่ Orchestrator Part 2 บันทึก payload เสร็จ.
        เพิ่ม symbol เข้า pending queue แล้ว flush ทันทีใน background thread.
        """
        if not symbol or not isinstance(symbol, str):
            logger.error(f"[ExecutorManager] Invalid symbol in nudge: {symbol!r}")
            return
        if not prompt_filepath or not isinstance(prompt_filepath, str):
            logger.error(f"[ExecutorManager] Invalid filepath for symbol {symbol}")
            return

        if broker_adapter is not None:
            self._broker_adapter = broker_adapter

        with self._pending_lock:
            self._pending_tasks[symbol] = prompt_filepath
            queue_size = len(self._pending_tasks)

        logger.info(
            f"[ExecutorManager] Queued '{symbol}' "
            f"(pending queue: {queue_size} symbol(s))"
        )

        # Flush ใน daemon thread เพื่อไม่บล็อก Orchestrator
        flush_thread = threading.Thread(
            target=self._flush_pending,
            kwargs={"triggering_symbol": symbol},
            daemon=True,
            name=f"FlushThread-{symbol}"
        )
        flush_thread.start()

    def _flush_pending(self, triggering_symbol: str = "") -> None:
        """
        ดึง pending tasks ทั้งหมดออกจาก queue แล้วยิง concurrent dispatch ทีเดียว.
        ถ้า flush กำลังทำงานอยู่ จะ skip (non-blocking acquire).
        """
        if not self._flush_lock.acquire(blocking=False):
            logger.debug(
                f"[ExecutorManager] Flush already running (triggered by {triggering_symbol}), skip."
            )
            return

        try:
            with self._pending_lock:
                if not self._pending_tasks:
                    return
                tasks: List[Tuple[str, str]] = list(self._pending_tasks.items())
                self._pending_tasks.clear()

            logger.info(
                f"[ExecutorManager] Concurrent flush: {len(tasks)} symbol(s) → "
                f"{[t[0] for t in tasks]}"
            )

            # ── AI Decision: N-Symbol Concurrent Dispatch ───────────────────
            try:
                decisions: Dict[str, Dict[str, Any]] = \
                    SystemPrompt.process_ai_decisions_concurrent(tasks)
            except Exception as e:
                logger.exception(
                    f"[ExecutorManager] process_ai_decisions_concurrent crashed: {e}"
                )
                traceback.print_exc()
                decisions = {
                    sym: {
                        "symbol": sym,
                        "action": "WAIT",
                        "expiry_minutes": 1,
                        "confidence_score": 0,
                        "ai_final_reason_th": f"Concurrent AI crashed: {e}",
                        "engine_used": "FALLBACK_SAFE_WAIT"
                    }
                    for sym, _ in tasks
                }

            # ── Process each decision: ExecutionGate → BrokerExecutor ────────
            for symbol, ai_decision in decisions.items():
                try:
                    self._execute_single_decision(
                        symbol=symbol,
                        ai_decision=ai_decision,
                        broker_adapter=self._broker_adapter
                    )
                except Exception as e:
                    logger.exception(
                        f"[ExecutorManager] _execute_single_decision failed for {symbol}: {e}"
                    )
                    traceback.print_exc()

        finally:
            self._flush_lock.release()

    def _execute_single_decision(
        self,
        symbol: str,
        ai_decision: Dict[str, Any],
        broker_adapter: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        รัน ExecutionGate + BrokerExecutor สำหรับคู่เงินเดียว.
        เกณฑ์: confidence_score >= 70 → ยิงออเดอร์ | < 70 → งด
        """
        # ── Step 1: Pre-Trade Risk Gate ──────────────────────────────────────
        can_trade, risk_reason = self.money_manager.can_trade()
        if not can_trade:
            logger.info(f"[ExecutorManager] {symbol} blocked by risk gate: {risk_reason}")
            action = str(ai_decision.get("action", "WAIT")).upper().strip()
            confidence = ai_decision.get("confidence_score", 0)
            if isinstance(confidence, float) and confidence.is_integer():
                confidence = int(confidence)
            thai_console_log(
                f"[AI Skipped] {symbol} -> {action} | Conf: {confidence}% | Reason: {risk_reason}"
            )
            return {
                "symbol": symbol,
                "action": "BLOCKED_BY_RISK",
                "reason": risk_reason,
                "order_executed": False
            }

        # ── Step 2: Execution Gate (confidence >= 70%) ───────────────────────
        try:
            gate_verdict = self.execution_gate.evaluate_decision(
                symbol=symbol,
                ai_decision=ai_decision,
                payload=None
            )
        except Exception as e:
            logger.exception(f"[ExecutorManager] ExecutionGate failed for {symbol}: {e}")
            traceback.print_exc()
            raise RuntimeError(f"FAIL-FAST: Execution Gate failed for {symbol}: {e}") from e

        # ── Step 3: Trading Mode Enforcement ────────────────────────────────
        should_execute_order = bool(gate_verdict.get("approved", False))

        if self.trading_mode == "AI SIGNAL_BOT":
            should_execute_order = False
            logger.info(
                f"[ExecutorManager] [SIGNAL_BOT] {symbol}: "
                f"Action={gate_verdict.get('action')} "
                f"Confidence={gate_verdict.get('confidence_score')}% "
                f"Expiry={gate_verdict.get('expiry_minutes')}m"
            )

        # ── Step 4: Broker Order Execution ───────────────────────────────────
        order_data = None
        if should_execute_order:
            action = gate_verdict["action"]
            expiry_minutes = gate_verdict["expiry_minutes"]
            stake = self.money_manager.get_stake(symbol)

            if broker_adapter is None:
                logger.warning(
                    f"[ExecutorManager] No broker_adapter — simulated execution for {symbol}"
                )
                order_data = {
                    "status": "SIMULATED",
                    "order_id": "SIM_ORDER_001",
                    "symbol": symbol,
                    "action": action,
                    "stake": stake,
                    "expiry_minutes": expiry_minutes
                }
            else:
                try:
                    order_data = self.broker_executor.execute_order(
                        symbol=symbol,
                        action=action,
                        expiry_minutes=expiry_minutes,
                        stake=stake,
                        broker_adapter=broker_adapter
                    )
                    if order_data.get("status") == "SUCCESS":
                        self.order_tracker.track_order(
                            order_data=order_data,
                            ai_decision=ai_decision,
                            broker_adapter=broker_adapter
                        )
                except Exception as e:
                    logger.exception(
                        f"[ExecutorManager] Broker execution failed for {symbol}: {e}"
                    )
                    traceback.print_exc()
                    raise

        # ── Step 5: Console Output Reporting (Real Processed Decision Output) ──
        action = gate_verdict.get("action", "WAIT")
        expiry_minutes = gate_verdict.get("expiry_minutes", 1)
        confidence = gate_verdict.get("confidence_score", 0)
        if isinstance(confidence, float) and confidence.is_integer():
            confidence = int(confidence)
        reason = gate_verdict.get("reason", "")

        if gate_verdict.get("approved", False):
            if self.trading_mode == "AI SIGNAL_BOT" or "SIGNAL_BOT" in self.trading_mode:
                ConsoleUI.show_signal_only(
                    action=action,
                    symbol=symbol,
                    expiry_time=expiry_minutes,
                    mode=self.trading_mode
                )
            else:
                order_id = order_data.get("order_id", "N/A") if order_data else "N/A"
                thai_console_log(
                    f"[AI Executed] {symbol} -> {action} ({expiry_minutes}m) | Conf: {confidence}% | OrderID: {order_id}"
                )
        else:
            thai_console_log(
                f"[AI Skipped] {symbol} -> {action} | Conf: {confidence}% | Reason: {reason}"
            )

        result = {
            "symbol": symbol,
            "action": gate_verdict.get("action", "WAIT"),
            "expiry_minutes": gate_verdict.get("expiry_minutes", 1),
            "confidence_score": gate_verdict.get("confidence_score", 0),
            "reason": gate_verdict.get("reason", ""),
            "should_execute": should_execute_order,
            "order_executed": (
                order_data is not None and order_data.get("status") == "SUCCESS"
            ),
            "order_data": order_data,
            "ai_decision": ai_decision,
            "risk_status": self.money_manager.get_risk_status()
        }

        logger.info(
            f"[ExecutorManager] {symbol} complete: "
            f"Action={result['action']} "
            f"Confidence={result['confidence_score']}% "
            f"Executed={result['order_executed']}"
        )
        return result

    def process_cycle_decision(
        self,
        symbol: str,
        prompt_filepath: str,
        payload: Optional[Dict[str, Any]] = None,
        broker_adapter: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Legacy single-symbol entry point (backward compatible).
        Uses concurrent dispatch internally with a single-item task list.
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("FAIL-FAST: symbol must be a non-empty string")
        if not prompt_filepath or not isinstance(prompt_filepath, str):
            raise ValueError("FAIL-FAST: prompt_filepath must be a non-empty string")

        if not os.path.exists(prompt_filepath):
            raise FileNotFoundError(f"FAIL-FAST: Prompt file not found at {prompt_filepath}")

        can_trade, risk_reason = self.money_manager.can_trade()
        if not can_trade:
            thai_console_log(
                f"[AI Skipped] {symbol} -> WAIT | Conf: 0% | Reason: {risk_reason}"
            )
            return {
                "symbol": symbol,
                "action": "BLOCKED_BY_RISK",
                "reason": risk_reason,
                "order_executed": False,
                "order_data": None,
                "ai_decision": None,
                "risk_status": self.money_manager.get_risk_status()
            }

        try:
            decisions = SystemPrompt.process_ai_decisions_concurrent([(symbol, prompt_filepath)])
            ai_decision = decisions.get(symbol, {
                "symbol": symbol, "action": "WAIT",
                "expiry_minutes": 1, "confidence_score": 0,
                "ai_final_reason_th": "AI decision missing from concurrent result",
                "engine_used": "FALLBACK_SAFE_WAIT"
            })
        except Exception as e:
            logger.exception(f"[ExecutorManager] AI analysis failed for {symbol}: {e}")
            traceback.print_exc()
            ai_decision = {
                "symbol": symbol, "action": "WAIT",
                "expiry_minutes": 1, "confidence_score": 0,
                "reason_th": f"AI ขัดข้อง ({e})",
                "engine_used": "FALLBACK_SAFE_WAIT"
            }

        return self._execute_single_decision(
            symbol=symbol,
            ai_decision=ai_decision,
            broker_adapter=broker_adapter or self._broker_adapter
        )


