"""
Gate Controller — The Ultimate Decider for Part 3
=================================================
กฎเดียวเท่านั้น: ถ้าคะแนน AI มากกว่า 60 คือ เทรดเลย!
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("ExecutionGate")


class ExecutionGate:
    """The Single Decisive Authority in Part 3."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        pass

    def evaluate_decision(
        self,
        symbol: str,
        ai_decision: Dict[str, Any],
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        กฎชี้ขาดหนึ่งเดียว:
        - คะแนน AI (confidence_score) มากกว่า 60 และมีคำสั่ง CALL/PUT -> เทรดเลย (APPROVED)
        - นอกนั้น -> ไม่เทรด (REJECTED)
        """
        if not isinstance(ai_decision, dict):
            raise TypeError(f"FAIL-FAST: ai_decision must be a dict, got {type(ai_decision)}")

        action = str(ai_decision.get("action", "WAIT")).upper().strip()
        expiry_minutes = int(ai_decision.get("expiry_minutes", 1))
        confidence_score = float(ai_decision.get("confidence_score", 0.0))
        reason_th = str(ai_decision.get("ai_final_reason_th") or ai_decision.get("reason_th") or "").strip()
        engine_used = str(ai_decision.get("engine_used", "AI_ENGINE"))

        # ── กฎชี้ขาด: คะแนน AI ตั้งแต่ 60 ขึ้นไป (>= 60) และเป็น CALL/PUT ➡️ เทรดเลย! ──
        if action in ("CALL", "PUT") and confidence_score >= 60.0:
            logger.info(
                f"[ExecutionGate] {symbol} => APPROVED: {action} "
                f"({expiry_minutes}m, คะแนน {confidence_score:.1f} >= 60) -> เทรดเลย!"
            )
            return {
                "approved": True,
                "action": action,
                "expiry_minutes": expiry_minutes,
                "confidence_score": confidence_score,
                "reason": reason_th or f"อนุมัติเข้าเทรด {action} (คะแนน AI {confidence_score:.1f} >= 60)",
                "engine_used": engine_used
            }

        # ── คะแนนต่ำกว่า 60 (< 60) หรือไม่ใช่ CALL/PUT ➡️ ไม่เทรด ───────────
        logger.info(
            f"[ExecutionGate] {symbol} => NOT APPROVED: {action} "
            f"(คะแนน {confidence_score:.1f} < 60) -> ไม่เทรด"
        )
        return {
            "approved": False,
            "action": action if action in ("CALL", "PUT") else "WAIT",
            "expiry_minutes": expiry_minutes,
            "confidence_score": confidence_score,
            "reason": f"ไม่อนุมัติ: คะแนน AI {confidence_score:.1f} ต่ำกว่า 60 ({reason_th})",
            "engine_used": engine_used
        }
