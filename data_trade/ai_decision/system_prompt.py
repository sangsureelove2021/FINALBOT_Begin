"""
System Prompt & Prompt Formatter for Part 3 AI Decision Engine
==============================================================
Defines the authoritative System Prompt and Strict JSON Output Specification
for DeepSeek Browser Agent and Google Gemini API, with automatic prompt archiving
to `data_base/trades/<SYMBOL>/` retaining max 30 files per symbol.
"""

import os
import csv
import glob
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """:: คำสั่ง ::
จงทำหน้าที่เป็น Quantitative Trading AI และ Binary Options Expert 
วิเคราะห์ข้อมูลตลาดแบบ Multi-Timeframe (M1, M5, M15) ด้านล่างนี้ โดยประมวลผลทุกตัวชี้วัด (Price Action, Technical Indicators, Volume, Market Context, Multi-Timeframe Alignment) 
เพื่อกำหนด Action, Expiry Minutes (1-5 นาที), Confidence Score และเหตุผลเชิงเทคนิค ไม่เกิน 40 คำ
ให้พิจารณาระยะเวลาถือครอง expiry_minutes 1-5 นาที ซึ่งผลแพ้ชนะเทียบเท่าข้อมูลจากอินดิเคเตอร์

:: ข้อกำหนดการส่งผลลัพธ์ ::
- ตอบกลับในรูปแบบ JSON ตามโครงสร้างนี้เท่านั้น (ห้ามมีข้อความเกริ่นนำหรือปิดท้ายนอก JSON):
{
  "symbol": "string",
  "action": "CALL" | "PUT",
  "expiry_minutes": 1,
  "confidence_score": 0,
  "ai_final_reason_th": "สรุปเหตุผลเชิงเทคนิคแบบกระชับ ครอบคลุม Price Action, Momentum และแนวรับแนวต้าน ไม่เกิน 40 คำ"
}"""


class SystemPrompt:
    """
    Prompt Orchestrator & Response Parser for Part 3.
    Receives 100-line payload, formats complete prompt, archives prompt to
    data_base/trades/<SYMBOL>/, sends to AI transport agent, parses raw response,
    and returns validated decision JSON.
    """

    MAX_RETENTION_FILES = 30
    TRADES_PROMPT_BASE_DIR = os.path.join("data_base", "trades")

    @staticmethod
    def get_system_prompt() -> str:
        """Returns the master system prompt for AI analysis."""
        return SYSTEM_PROMPT.strip()

    @staticmethod
    def build_user_prompt(symbol: str, prompt_text: str) -> str:
        """
        Builds the complete user prompt to be dispatched to DeepSeek or Gemini.
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("FAIL-FAST: symbol must be a non-empty string")
        if not prompt_text or not isinstance(prompt_text, str):
            raise ValueError("FAIL-FAST: prompt_text must be a non-empty string")

        return (
            f":: ข้อมูลตลาดสำหรับวิเคราะห์ ::\n"
            f"{prompt_text.strip()}\n"
        )

    @classmethod
    def save_prompt_file(cls, symbol: str, full_prompt_content: str) -> str:
        """
        Saves the assembled prompt file to `data_base/trades/<SYMBOL>/<FILENAME>.txt`
        and enforces the 30-file retention policy.
        """
        symbol_dir = os.path.join(cls.TRADES_PROMPT_BASE_DIR, symbol)
        os.makedirs(symbol_dir, exist_ok=True)

        timestamp_str = datetime.now().strftime("%m%d%H%M%S")
        filename = f"{symbol}{timestamp_str}.txt"
        file_path = os.path.join(symbol_dir, filename)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_prompt_content)
            logger.info(f"[SystemPrompt] Archived prompt to {file_path}")
        except Exception as e:
            logger.error(f"[SystemPrompt] Failed to archive prompt to {file_path}: {e}")

        # Enforce 30-file retention
        cls._enforce_retention(symbol_dir)
        return file_path

    @classmethod
    def _enforce_retention(cls, symbol_dir: str) -> None:
        """Keeps at most MAX_RETENTION_FILES in the symbol directory."""
        try:
            files = sorted(
                glob.glob(os.path.join(symbol_dir, "*.txt")),
                key=os.path.getmtime
            )
            while len(files) > cls.MAX_RETENTION_FILES:
                oldest = files.pop(0)
                try:
                    os.remove(oldest)
                    logger.debug(f"[SystemPrompt] Retention cleanup removed: {oldest}")
                except Exception as e:
                    logger.warning(f"[SystemPrompt] Could not remove old file {oldest}: {e}")
        except Exception as e:
            logger.warning(f"[SystemPrompt] Error during retention cleanup: {e}")

    @classmethod
    def process_ai_decision(cls, symbol: str, payload_text: str, ai_agent: Any) -> Dict[str, Any]:
        """
        Main Engine Flow:
        1. Takes 100 payload from executor_manager.
        2. Builds complete prompt with system rules.
        3. Archives assembled prompt to data_base/trades/<SYMBOL>/<FILENAME>.txt.
        4. Sends to ai_gemini_api or ai_deepseek_browser transport.
        5. Receives raw output and parses into structured JSON.
        6. Returns structured JSON to executor_manager.
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("FAIL-FAST: symbol must be a non-empty string")
        if not payload_text or not isinstance(payload_text, str):
            raise ValueError("FAIL-FAST: payload_text must be a non-empty string")

        if ai_agent is None:
            return {
                "symbol": symbol,
                "action": "WAIT",
                "expiry_minutes": 1,
                "confidence_score": 0,
                "reason_th": "AI Agent is not initialized or disabled",
                "ai_final_reason_th": "AI Agent is not initialized or disabled",
                "engine_used": "DISABLED"
            }

        system_instruction = cls.get_system_prompt()
        user_prompt = cls.build_user_prompt(symbol, payload_text)
        full_assembled_prompt = f"{system_instruction}\n\n{user_prompt}"

        # ── Step 0: Archive prompt file to data_base/trades/<SYMBOL>/ ────────
        saved_file_path = cls.save_prompt_file(symbol=symbol, full_prompt_content=full_assembled_prompt)

        # ── Step 1 & 2: Send prompt to AI Transport Agent ────────────────────
        try:
            raw_output = ai_agent.send_prompt(user_prompt=user_prompt, system_instruction=system_instruction)
        except TypeError:
            # Fallback for CLI transport drivers that take full combined prompt string
            raw_output = ai_agent.send_prompt(full_assembled_prompt)

        # ── Step 3: Parse raw text and extract JSON decision ─────────────
        parsed_decision = cls.parse_json_decision(raw_output=raw_output, symbol=symbol, ai_agent=ai_agent)

        # ── Step 4: Record AI Response back into the archived trade txt file ─
        try:
            tz_thailand = timezone(timedelta(hours=7))
            resp_time = datetime.now(tz_thailand).strftime("%Y-%m-%d %H:%M:%S")
            with open(saved_file_path, "a", encoding="utf-8") as f:
                f.write("\n\n" + "=" * 64 + "\n")
                f.write(f":: สิ่งที่ AI ตอบกลับมา (AI RESPONSE) ::\n")
                f.write(f"เวลาตอบกลับ: {resp_time}\n")
                f.write(f"เครื่องยนต์/โมเดล: {parsed_decision.get('engine_used')}\n")
                f.write(f"ผลลัพธ์ดิบ (Raw Response):\n{raw_output.strip()}\n\n")
                f.write("สรุปผลการวิเคราะห์ (Parsed JSON):\n")
                f.write(json.dumps(parsed_decision, ensure_ascii=False, indent=2))
                f.write("\n" + "=" * 64 + "\n")
            logger.info(f"[SystemPrompt] Appended AI response into: {saved_file_path}")
        except Exception as e:
            logger.warning(f"[SystemPrompt] Could not append AI response to {saved_file_path}: {e}")

        # ── Step 5: Save AI Decision to Symbol-Separated CSV File ─────────────
        cls._save_decision_csv(symbol=symbol, decision=parsed_decision)

        return parsed_decision

    @classmethod
    def _save_decision_csv(cls, symbol: str, decision: Dict[str, Any]) -> str:
        """Appends the AI decision record into logs/logs_data_trade/ai_decisions/<SYMBOL>/<SYMBOL>_decisions.csv."""
        try:
            symbol_dir = os.path.join("logs", "logs_data_trade", "ai_decisions", symbol)
            os.makedirs(symbol_dir, exist_ok=True)
            csv_path = os.path.join(symbol_dir, f"{symbol}_decisions.csv")

            file_exists = os.path.isfile(csv_path)
            tz_thailand = timezone(timedelta(hours=7))
            now_str = datetime.now(tz_thailand).strftime("%Y-%m-%d %H:%M:%S")

            raw_conf = decision.get("confidence_score", 0)
            try:
                conf_val = int(round(float(raw_conf)))
            except (ValueError, TypeError):
                conf_val = int(raw_conf) if isinstance(raw_conf, int) else 0

            fieldnames = ["timestamp", "symbol", "action", "expiry", "confidence"]
            row = {
                "timestamp": now_str,
                "symbol": symbol,
                "action": decision.get("action", ""),
                "expiry": int(decision.get("expiry_minutes", 1)),
                "confidence": conf_val
            }

            with open(csv_path, mode="a", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)

            logger.info(f"[SystemPrompt] Appended decision to CSV: {csv_path}")
            return csv_path
        except Exception as e:
            logger.warning(f"[SystemPrompt] Could not write decision CSV for {symbol}: {e}")
            return ""

    @classmethod
    def parse_json_decision(cls, raw_output: str, symbol: str, ai_agent: Any) -> Dict[str, Any]:
        """Extracts, parses, and normalizes JSON decision."""
        if not raw_output or not isinstance(raw_output, str):
            raise ValueError("FAIL-FAST: Received empty text response from AI transport agent")

        clean_text = raw_output.strip()
        start_idx = clean_text.find('{')
        end_idx = clean_text.rfind('}')

        if start_idx == -1 or end_idx == -1:
            raise ValueError(f"FAIL-FAST: No JSON object found in AI response: {clean_text}")

        json_str = clean_text[start_idx:end_idx + 1]
        try:
            decision = json.loads(json_str)
        except Exception as e:
            raise ValueError(f"FAIL-FAST: Invalid JSON format from AI response ({json_str}): {e}") from e

        if not isinstance(decision, dict):
            raise TypeError(f"FAIL-FAST: Expected JSON dictionary from AI, got {type(decision)}")

        # ── Action Resolution ────────────────────────────────────────────────
        raw_act = decision.get("action") or decision.get("direction") or decision.get("signal") or ""
        norm_action = str(raw_act).upper().strip()
        if "CALL" in norm_action or "BUY" in norm_action:
            norm_action = "CALL"
        elif "PUT" in norm_action or "SELL" in norm_action:
            norm_action = "PUT"
        else:
            norm_action = "WAIT"

        # ── Confidence Score Resolution ──────────────────────────────────────
        raw_conf = decision.get("confidence_score")
        if raw_conf is None:
            raw_conf = decision.get("confidence") or decision.get("score") or 50.0
        try:
            norm_confidence = float(raw_conf)
            norm_confidence = max(0.0, min(100.0, norm_confidence))
        except (ValueError, TypeError):
            norm_confidence = 50.0

        # ── Expiry Resolution ────────────────────────────────────────────────
        raw_expiry = decision.get("expiry_minutes") or decision.get("expiry") or 1
        try:
            norm_expiry = int(raw_expiry)
            norm_expiry = max(1, min(5, norm_expiry))
        except (ValueError, TypeError):
            norm_expiry = 1

        # ── Reason Resolution ────────────────────────────────────────────────
        norm_reason = str(
            decision.get("ai_final_reason_th") or 
            decision.get("reason_th") or 
            decision.get("reason") or 
            decision.get("recommendation") or ""
        ).strip()
        if not norm_reason:
            norm_reason = "AI วิเคราะห์ผลลัพธ์สำเร็จ"

        model_label = getattr(ai_agent, "model_name", type(ai_agent).__name__)

        return {
            "symbol": str(decision.get("symbol") or decision.get("asset") or symbol).strip(),
            "action": norm_action,
            "expiry_minutes": norm_expiry,
            "confidence_score": norm_confidence,
            "reason_th": norm_reason,
            "ai_final_reason_th": norm_reason,
            "engine_used": f"AI ({model_label})"
        }
