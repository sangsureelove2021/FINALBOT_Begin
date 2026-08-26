"""
ML Dispatcher & Payload Reader for FINALBOT
============================================
Location: ai_analysis/ml_model/ml_dispatcher.py
หน้าที่:
1. เปิดอ่านไฟล์ 96 Payload จากดิสก์ (data_base/orchestrator/<SYMBOL>/)
2. ดึงค่าตัวเลข 96 ตัวชี้วัดโดยตรง (ไม่ต้องเขียน Text Prompt)
3. ส่งเข้าคำนวณในโมเดล ML (Mode A: Chronos, Mode B: LightGBM, Mode AB: Dual-Brain)
4. บันทึกผลลัพธ์ลง CSV และส่งคืน JSON Decision ให้ ExecutorManager ทันที
"""

import os
import csv
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from .dual_brain import DualBrainCoordinator
from config_setting.config_loader import load_settings

logger = logging.getLogger("MLDispatcher")


class MLDispatcher:
    """Master ML Pipeline Dispatcher (Reads 96-field disk payload directly into ML)."""

    _INSTANCE: Optional["MLDispatcher"] = None
    AI_DECISION_OUTPUT_BASE_DIR = os.path.join("data_trade", "ai_decision_output")

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.settings = config or load_settings(reload=False)
        cfg_ai = self.settings.get("ai_mode", {})
        self.mode = str(cfg_ai.get("engine", cfg_ai.get("primary_engine", "AB"))).strip().upper()
        self.min_confidence = int(cfg_ai.get("min_confidence", 85))
        self.stake = float(self.settings.get("account", {}).get("stake_per_trade", 35.0))

        self.coordinator = DualBrainCoordinator(
            mode=self.mode if self.mode in ("A", "B", "AB") else "AB",
            min_confidence=self.min_confidence,
            default_stake=self.stake
        )
        logger.info(f"[MLDispatcher] Initialized ML Engine | Mode: {self.mode} | Min Conf: {self.min_confidence}%")

    @classmethod
    def get_instance(cls) -> "MLDispatcher":
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    @staticmethod
    def read_payload_from_disk(prompt_filepath: str) -> Dict[str, Any]:
        """Reads 100-line payload file from disk and parses raw numbers into dictionary (No Text Prompt)."""
        if not prompt_filepath or not os.path.isfile(prompt_filepath):
            raise FileNotFoundError(f"FAIL-FAST: Payload file not found at {prompt_filepath}")

        data: Dict[str, Any] = {}
        with open(prompt_filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("::") or line.startswith("#") or line.startswith("==="):
                    continue
                if ":" in line:
                    parts = line.split(":", 1)
                    k = parts[0].strip()
                    v = parts[1].strip()
                    try:
                        if "." in v:
                            data[k] = float(v)
                        else:
                            data[k] = int(v)
                    except ValueError:
                        data[k] = v
        return data

    @classmethod
    def _save_decision_csv(
        cls,
        symbol: str,
        decision: Dict[str, Any],
        analysis_id: str,
        timestamp_str: str
    ) -> None:
        """Saves audit record to data_trade/ai_decision_output/<SYMBOL>/decisions.csv."""
        try:
            symbol_dir = os.path.join(cls.AI_DECISION_OUTPUT_BASE_DIR, symbol)
            os.makedirs(symbol_dir, exist_ok=True)
            csv_path = os.path.join(symbol_dir, "decisions.csv")

            file_exists = os.path.isfile(csv_path)
            fieldnames = [
                "timestamp", "ID", "symbol", "action", "confidence_score",
                "expiry_minutes", "engine_used", "reason_th"
            ]

            row = {
                "timestamp": timestamp_str,
                "ID": analysis_id,
                "symbol": symbol,
                "action": decision.get("action", "WAIT"),
                "confidence_score": decision.get("confidence_score", 0),
                "expiry_minutes": decision.get("expiry_minutes", 5),
                "engine_used": decision.get("engine_used", "ML"),
                "reason_th": decision.get("reason_th", "")
            }

            with open(csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)
        except Exception as e:
            logger.error(f"[MLDispatcher] Failed to save decision CSV for {symbol}: {e}")

    def process_payload_file(self, symbol: str, prompt_filepath: str) -> Dict[str, Any]:
        """
        Reads 96-payload file from disk, runs ML evaluation directly, and returns structured decision.
        """
        now_utc = datetime.now(timezone.utc)
        utc_timestamp_str = now_utc.strftime("%Y-%m-%d %H:%M:%S+00:00")
        clean_sym = symbol.replace("/", "").replace("-", "").replace("_", "")
        analysis_id = f"{clean_sym}{now_utc.strftime('%m%d%H%M%S')}"

        # 1. Read raw numbers from disk payload (No Natural Language Prompt)
        payload_data = self.read_payload_from_disk(prompt_filepath)

        # 2. Evaluate via Local ML Coordinator (Mode A, B, or AB)
        ml_res = self.coordinator.evaluate_symbol(symbol, payload_dict=payload_data)

        # 3. Format structured decision
        decision = {
            "symbol": symbol,
            "action": ml_res.get("action", "WAIT"),
            "expiry_minutes": ml_res.get("expiry_minutes", 5),
            "confidence_score": float(ml_res.get("confidence", 0)),
            "engine_used": f"ML ({self.mode})",
            "timestamp": utc_timestamp_str,
            "ID": analysis_id,
            "reason_th": ml_res.get("reason", "")
        }

        # 4. Save audit CSV
        self._save_decision_csv(symbol, decision, analysis_id, utc_timestamp_str)

        return decision
