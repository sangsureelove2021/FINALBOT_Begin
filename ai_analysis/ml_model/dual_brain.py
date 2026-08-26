"""
Dual-Brain Master Coordinator — Local AI Core for ATHENA SNIPER BOT
====================================================================
Location: ai_analysis/ml_model/dual_brain.py
Manages Multi-Engine Decision Flow (100% In-Memory):
- Mode 'A' : Amazon Chronos Time-Series Quantile Forecaster
- Mode 'B' : LightGBM Multi-Timeframe Price Action Classifier
- Mode 'AB': Dual-Brain Ensemble (Both A & B MUST agree 100% on CALL/PUT)
Outputs standardized A+ Sniper Action Payload to Part 3 Execution Gate.
"""

import time
import logging
import concurrent.futures
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple

from .chronos_engine import ChronosEngine
from .lightgbm_engine import LightGBMEngine

logger = logging.getLogger("DualBrainCoordinator")


class DualBrainCoordinator:
    """Master In-Memory AI Coordinator supporting Mode A, Mode B, and Mode AB."""

    def __init__(self, mode: str = "AB", min_confidence: int = 85, default_stake: float = 35.0):
        self.mode = str(mode).strip().upper()
        if self.mode not in ("A", "B", "AB"):
            logger.warning(f"[DualBrainCoordinator] Unknown mode '{mode}', defaulting to 'AB'")
            self.mode = "AB"

        self.min_confidence = int(min_confidence)
        self.default_stake = float(default_stake)

        logger.info(f"[DualBrainCoordinator] Initializing Engines for Mode '{self.mode}'...")
        self.engine_a = ChronosEngine(min_confidence=self.min_confidence)
        self.engine_b = LightGBMEngine(min_confidence=self.min_confidence)
        logger.info(f"[DualBrainCoordinator] Ready | Mode: {self.mode} | Min Conf: {self.min_confidence}% | Stake: {self.default_stake} THB")

    def set_mode(self, mode: str):
        """Dynamically switch between mode A, B, or AB."""
        clean_mode = str(mode).strip().upper()
        if clean_mode in ("A", "B", "AB"):
            self.mode = clean_mode
            logger.info(f"[DualBrainCoordinator] Switched mode to: {self.mode}")

    def evaluate_symbol(
        self,
        symbol: str,
        candles: Optional[Dict[str, pd.DataFrame]] = None,
        payload_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a single symbol according to active mode ('A', 'B', or 'AB').
        Returns: Standardized Athena Action JSON.
        """
        start_t = time.perf_counter()

        df_m5 = candles.get("M5") if isinstance(candles, dict) else None
        latest_close = float(df_m5["close"].iloc[-1]) if (df_m5 is not None and not df_m5.empty) else float(payload_dict.get("m5_close", 0.0) if payload_dict else 0.0)

        base_res = {
            "symbol": symbol,
            "action": "WAIT",
            "expiry_minutes": 5,
            "stake": self.default_stake,
            "confidence": 0,
            "strategy": f"LOCAL_AI_{self.mode}",
            "reason": "รอจังหวะสัญญาณค่ะ",
            "m5_close": latest_close,
            "mode": self.mode,
            "details": {}
        }

        # ── 1. Mode A: Chronos Only ──────────────────────────────────────────
        if self.mode == "A":
            res_a = self.engine_a.evaluate(symbol, candles=candles)
            base_res["action"] = res_a.get("action", "WAIT")
            base_res["confidence"] = res_a.get("confidence", 0)
            base_res["reason"] = res_a.get("reason", "")
            base_res["strategy"] = f"CHRONOS_A_{base_res['action']}"
            base_res["details"] = {"engine_a": res_a}
            base_res["latency_ms"] = round((time.perf_counter() - start_t) * 1000.0, 2)
            return base_res

        # ── 2. Mode B: LightGBM Only ─────────────────────────────────────────
        if self.mode == "B":
            res_b = self.engine_b.evaluate(symbol, candles=candles, payload_dict=payload_dict)
            base_res["action"] = res_b.get("action", "WAIT")
            base_res["confidence"] = res_b.get("confidence", 0)
            base_res["reason"] = res_b.get("reason", "")
            base_res["strategy"] = f"LIGHTGBM_B_{base_res['action']}"
            base_res["details"] = {"engine_b": res_b}
            base_res["latency_ms"] = round((time.perf_counter() - start_t) * 1000.0, 2)
            return base_res

        # ── 3. Mode AB: Dual-Brain Ensemble (A & B must agree 100%) ───────────
        res_a = self.engine_a.evaluate(symbol, candles=candles)
        res_b = self.engine_b.evaluate(symbol, candles=candles, payload_dict=payload_dict)

        act_a = res_a.get("action", "WAIT")
        act_b = res_b.get("action", "WAIT")
        conf_a = res_a.get("confidence", 0)
        conf_b = res_b.get("confidence", 0)

        base_res["details"] = {"engine_a": res_a, "engine_b": res_b}

        # Check if both agree on CALL or PUT
        if act_a == act_b and act_a in ("CALL", "PUT"):
            combined_conf = int((conf_a + conf_b) / 2.0)
            if combined_conf >= self.min_confidence:
                base_res["action"] = act_a
                base_res["confidence"] = combined_conf
                base_res["strategy"] = f"DUAL_BRAIN_AB_{act_a}"
                base_res["reason"] = (
                    f"👑 Dual-Brain AB เห็นพ้องตรงกัน: {act_a} "
                    f"(Chronos: {conf_a}% + LightGBM: {conf_b}% ➡️ เฉลี่ย {combined_conf}%) ค่ะ"
                )
            else:
                base_res["action"] = "WAIT"
                base_res["confidence"] = combined_conf
                base_res["reason"] = (
                    f"Dual-Brain AB: ทิศทางตรงกัน ({act_a}) แต่ความมั่นใจเฉลี่ย {combined_conf}% "
                    f"ยังไม่ถึงเกณฑ์ A+ ({self.min_confidence}%) ค่ะ"
                )
        else:
            base_res["action"] = "WAIT"
            base_res["confidence"] = max(conf_a, conf_b)
            base_res["reason"] = (
                f"Dual-Brain AB ขัดแย้ง: Model A ให้ {act_a} ({conf_a}%) แต่ Model B ให้ {act_b} ({conf_b}%) ➡️ สั่ง WAIT เพื่อความปลอดภัยค่ะ"
            )

        base_res["latency_ms"] = round((time.perf_counter() - start_t) * 1000.0, 2)
        return base_res

    def evaluate_all(self, symbols_candles: Dict[str, Dict[str, pd.DataFrame]]) -> List[Dict[str, Any]]:
        """Evaluates multiple symbols concurrently in RAM (< 10 ms)."""
        decisions: List[Dict[str, Any]] = []
        if not symbols_candles:
            return decisions

        max_workers = max(1, min(len(symbols_candles), 8))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="DualBrainWorker") as executor:
            future_to_sym = {
                executor.submit(self.evaluate_symbol, sym, candles=candles): sym
                for sym, candles in symbols_candles.items()
            }
            for future in concurrent.futures.as_completed(future_to_sym):
                sym = future_to_sym[future]
                try:
                    res = future.result()
                    decisions.append(res)
                except Exception as e:
                    logger.exception(f"[DualBrainCoordinator] Exception evaluating {sym}: {e}")

        decisions.sort(key=lambda d: d.get("confidence", 0), reverse=True)
        return decisions
