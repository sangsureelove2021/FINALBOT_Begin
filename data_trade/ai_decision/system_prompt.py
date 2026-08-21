"""
System Prompt & Prompt Formatter for Part 3 AI Decision Engine
==============================================================
Defines the authoritative System Prompt and Strict JSON Output Specification
for DeepSeek Browser Agent and Google Gemini API, with automatic prompt archiving
to `data_trade/ai_decision/ai_prompt_output/<SYMBOL>/` retaining max 30 files per symbol.
"""

import os
import asyncio
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
หากสัญญาณไม่ชัดเจนหรือมีความเสี่ยงสูง ให้ตอบ "action": "WAIT"

:: ข้อกำหนดการส่งผลลัพธ์ ::
- ตอบกลับในรูปแบบ JSON ตามโครงสร้างนี้เท่านั้น (ห้ามมีข้อความเกริ่นนำหรือปิดท้ายนอก JSON):
{
  "symbol": "string",
  "action": "CALL" | "PUT" | "WAIT",
  "expiry_minutes": 1,
  "confidence_score": 0,
  "ai_final_reason_th": "สรุปเหตุผลเชิงเทคนิคแบบกระชับ ครอบคลุม Price Action, Momentum และแนวรับแนวต้าน ไม่เกิน 40 คำ"
}"""


class SystemPrompt:
    """
    Prompt Orchestrator & Response Parser for Part 3.
    Receives 100-line payload, formats complete prompt, archives prompt to
    data_trade/ai_decision/ai_prompt_output/<SYMBOL>/, sends to AI transport agent, parses raw response,
    and returns validated decision JSON.
    """

    MAX_RETENTION_FILES = 30
    TRADES_PROMPT_BASE_DIR = os.path.join("data_trade", "ai_decision", "ai_prompt_output")
    AI_OUTPUT_BASE_DIR = os.path.join("data_trade", "ai_output")
    _GEMINI_AGENT: Optional[Any] = None

    @classmethod
    def get_ai_agent(cls) -> Any:
        """Initializes and returns the dedicated Gemini AI Transport Driver (Lazy-loaded Singleton)."""
        if cls._GEMINI_AGENT is None:
            from data_trade.ai_decision.ai_gemini_api import GeminiApiAgent
            from config_setting.config_loader import load_settings
            cfg = load_settings(reload=False).get("ai_mode", {})
            model_name = cfg.get("gemini_model", "gemini-3.5-flash-lite")
            cls._GEMINI_AGENT = GeminiApiAgent(model_name=model_name)
            logger.info(f"[SystemPrompt] Initialized Dedicated Gemini Agent ({model_name})")
        return cls._GEMINI_AGENT

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
        Saves the assembled prompt file to `data_trade/ai_decision/ai_prompt_output/<SYMBOL>/<FILENAME>.txt`
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
    def read_payload_from_disk(cls, prompt_filepath: str) -> str:
        """Reads 100-line prompt text from Part 2 output file on disk."""
        if not prompt_filepath or not isinstance(prompt_filepath, str):
            raise ValueError("FAIL-FAST: prompt_filepath must be a non-empty string")
        if not os.path.isfile(prompt_filepath):
            raise FileNotFoundError(f"FAIL-FAST: Payload file not found at {prompt_filepath}")

        with open(prompt_filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()

        if not content:
            raise ValueError(f"FAIL-FAST: Payload file is empty at {prompt_filepath}")
        return content

    @classmethod
    def process_ai_decision(
        cls,
        symbol: str,
        payload_text: Optional[str] = None,
        ai_agent: Any = None,
        prompt_filepath: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main Engine Flow:
        1. Reads 100-line payload from disk (prompt_filepath) if provided, or uses payload_text.
        2. Builds complete prompt with system rules.
        3. Archives assembled prompt to data_trade/ai_decision/ai_prompt_output/<SYMBOL>/<FILENAME>.txt.
        4. Sends to ai_gemini_api or ai_deepseek_browser transport.
        5. Receives raw output and parses into structured JSON.
        6. Returns structured JSON to executor_manager.
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("FAIL-FAST: symbol must be a non-empty string")

        if prompt_filepath:
            payload_text = cls.read_payload_from_disk(prompt_filepath)
        elif not payload_text or not isinstance(payload_text, str):
            raise ValueError("FAIL-FAST: Either prompt_filepath or non-empty payload_text must be provided")

        target_agent = ai_agent or cls.get_ai_agent()
        if target_agent is None:
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

        # ── Step 0: Archive prompt file ──────────────────────────────────────
        saved_file_path = cls.save_prompt_file(symbol=symbol, full_prompt_content=full_assembled_prompt)

        # ── Step 1 & 2: Send prompt directly to Gemini AI Transport Agent ────
        try:
            raw_output = target_agent.send_prompt(user_prompt=user_prompt, system_instruction=system_instruction)
        except TypeError:
            raw_output = target_agent.send_prompt(full_assembled_prompt)

        # ── Step 3: Parse raw text and extract JSON decision ─────────────────
        parsed_decision = cls.parse_json_decision(raw_output=raw_output, symbol=symbol, ai_agent=target_agent)

        # ── Step 4: Save AI Order Decision as File ───────────────────────────
        cls._save_decision_file(symbol=symbol, decision=parsed_decision, raw_output=raw_output)

        # ── Step 5: Save AI Decision to Symbol CSV Record ─────────────────────
        cls._save_decision_csv(symbol=symbol, decision=parsed_decision)

        return parsed_decision

    @classmethod
    def _save_decision_file(cls, symbol: str, decision: Dict[str, Any], raw_output: str) -> str:
        """Saves the structured AI order decision file to data_trade/ai_output/<SYMBOL>/<FILENAME>.json."""
        try:
            symbol_dir = os.path.join(cls.AI_OUTPUT_BASE_DIR, symbol)
            os.makedirs(symbol_dir, exist_ok=True)

            tz_thailand = timezone(timedelta(hours=7))
            now = datetime.now(tz_thailand)
            timestamp_str = now.strftime("%Y%m%d_%H%M%S")
            filename = f"decision_{symbol}_{timestamp_str}.json"
            file_path = os.path.join(symbol_dir, filename)

            decision_record = {
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                "symbol": symbol,
                "action": decision.get("action", "WAIT"),
                "expiry_minutes": decision.get("expiry_minutes", 1),
                "confidence_score": decision.get("confidence_score", 0),
                "ai_final_reason_th": decision.get("ai_final_reason_th", ""),
                "engine_used": decision.get("engine_used", "AI (Gemini)"),
                "raw_response": raw_output.strip()
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(decision_record, f, ensure_ascii=False, indent=2)

            logger.info(f"[SystemPrompt] Saved AI Order Decision file to: {file_path}")

            # Enforce 30-file retention for decision files
            cls._enforce_retention_pattern(symbol_dir, "*.json")
            return file_path
        except Exception as e:
            logger.error(f"[SystemPrompt] Could not save AI Order Decision file for {symbol}: {e}", exc_info=True)
            return ""

    @classmethod
    def _enforce_retention_pattern(cls, symbol_dir: str, pattern: str) -> None:
        """Keeps at most MAX_RETENTION_FILES in the symbol directory for the specified pattern."""
        try:
            files = sorted(
                glob.glob(os.path.join(symbol_dir, pattern)),
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
    async def _process_single_async(
        cls,
        symbol: str,
        prompt_filepath: str,
        agent: Any
    ) -> Dict[str, Any]:
        """
        Async coroutine: processes one currency pair concurrently.
        Reads Part 2 payload → builds prompt → saves to ai_prompt_output
        → sends to Gemini async → saves to ai_output → returns decision.
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError(f"FAIL-FAST [async]: symbol must be non-empty string, got: {symbol!r}")
        if not prompt_filepath or not isinstance(prompt_filepath, str):
            raise ValueError(f"FAIL-FAST [async]: prompt_filepath must be non-empty string for {symbol}")

        payload_text = cls.read_payload_from_disk(prompt_filepath)
        system_instruction = cls.get_system_prompt()
        user_prompt = cls.build_user_prompt(symbol, payload_text)
        full_assembled_prompt = f"{system_instruction}\n\n{user_prompt}"

        cls.save_prompt_file(symbol=symbol, full_prompt_content=full_assembled_prompt)

        raw_output = await agent.send_prompt_async(
            user_prompt=user_prompt,
            system_instruction=system_instruction
        )

        decision = cls.parse_json_decision(raw_output=raw_output, symbol=symbol, ai_agent=agent)
        cls._save_decision_file(symbol=symbol, decision=decision, raw_output=raw_output)
        cls._save_decision_csv(symbol=symbol, decision=decision)

        logger.info(
            f"[SystemPrompt Concurrent] {symbol} ✓ "
            f"Action={decision.get('action')} Confidence={decision.get('confidence_score')}"
        )
        return decision

    @classmethod
    def process_ai_decisions_concurrent(
        cls,
        tasks: list
    ) -> Dict[str, Dict[str, Any]]:
        """
        N-Symbol Concurrent Dispatch:
        Fires Gemini API for ALL symbols simultaneously via asyncio.gather().
        Works for N=1 to N=10+ symbols — no sequential waiting.
        """
        import concurrent.futures
        import traceback

        if not tasks or not isinstance(tasks, list):
            raise ValueError("FAIL-FAST: tasks must be a non-empty list of (symbol, filepath) tuples")

        agent = cls.get_ai_agent()
        symbols_list = [t[0] for t in tasks]
        logger.info(
            f"[SystemPrompt Concurrent] Dispatching {len(tasks)} symbol(s) simultaneously: {symbols_list}"
        )

        async def _gather_all():
            coroutines = [
                cls._process_single_async(sym, fp, agent)
                for sym, fp in tasks
            ]
            return await asyncio.gather(*coroutines, return_exceptions=True)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(asyncio.run, _gather_all())
                    raw_results = future.result(timeout=60)
            else:
                raw_results = loop.run_until_complete(_gather_all())
        except RuntimeError:
            raw_results = asyncio.run(_gather_all())

        output: Dict[str, Dict[str, Any]] = {}
        for (symbol, _), result in zip(tasks, raw_results):
            if isinstance(result, Exception):
                logger.error(
                    f"[SystemPrompt Concurrent] {symbol} FAILED during concurrent dispatch: {result}",
                    exc_info=(type(result), result, result.__traceback__)
                )
                traceback.print_exception(type(result), result, result.__traceback__)
                output[symbol] = {
                    "symbol": symbol,
                    "action": "WAIT",
                    "expiry_minutes": 1,
                    "confidence_score": 0,
                    "reason_th": f"AI concurrent dispatch ขัดข้อง: {result}",
                    "ai_final_reason_th": f"AI concurrent dispatch ขัดข้อง: {result}",
                    "engine_used": "FALLBACK_SAFE_WAIT"
                }
            else:
                output[symbol] = result

        logger.info(
            f"[SystemPrompt Concurrent] Completed {len(output)} symbol(s): {list(output.keys())}"
        )
        return output

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
