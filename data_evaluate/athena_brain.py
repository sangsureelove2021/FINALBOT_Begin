"""
Athena Brain Core — Part 2 Pure AI Reasoning Engine (Athena 100%)
==================================================================
สถาปัตยกรรม: Part 2 สมองกลเอเธน่า AI 100% (ไร้สูตรคำนวณตายตัวของบอท)
- ส่งข้อมูลแท่งเทียนสด OHLCV (M15, M5, M1) จาก RAM ให้โมเดล AI ของเอเธน่าวิเคราะห์ตรง 100%
- เอเธน่าเป็นผู้อ่านพฤติกรรมราคา (Price Action), บริบทตลาด และตัดสินใจ CALL / PUT / WAIT ด้วยตนเอง
- คัดเฉพาะจังหวะ A+ Sniper Setup (ความมั่นใจ >= 85%) เพื่อเป้าหมายชนะ 2 ไม้ต่อวัน
- ส่งออก Direct Signal Object ให้ Part 3 ยิงออเดอร์ทันที
"""

import os
import json
import logging
import traceback
import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta

from data_trade.ai_analysis.gemini_bridge import GeminiApiAgent

logger = logging.getLogger("AthenaBrain")


class AthenaBrain:
    """Pure AI In-Memory Decision Engine (Athena 100%)."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.min_confidence = int(self.config.get("min_confidence", 85))
        self.default_stake = float(self.config.get("stake", 35.0))
        self.ai_agent = GeminiApiAgent()
        logger.info(f"[AthenaBrain] Initialized Pure AI Engine | Min Confidence: {self.min_confidence}% | Stake: {self.default_stake} THB")

    @staticmethod
    def _format_candles_summary(symbol: str, candles: Dict[str, pd.DataFrame]) -> str:
        """Formats recent raw OHLCV candles from RAM into a clean, compact text snapshot for Athena AI."""
        df_m15 = candles.get('M15')
        df_m5 = candles.get('M5')
        df_m1 = candles.get('M1')

        lines = [f"=== ตลาดสินทรัพย์: {symbol} ==="]

        # 1. Macro Structure M15 (Last 5 candles)
        if df_m15 is not None and not df_m15.empty:
            lines.append("\n[M15 Macro Frame - 5 แท่งล่าสุด]:")
            for idx, row in df_m15.tail(5).iterrows():
                t_str = str(idx)[-8:] if not isinstance(idx, int) else str(idx)
                lines.append(f"• M15 | O:{row['open']:.5f} H:{row['high']:.5f} L:{row['low']:.5f} C:{row['close']:.5f} V:{int(row.get('volume', 0))}")

        # 2. Primary Trading Frame M5 (Last 8 candles)
        if df_m5 is not None and not df_m5.empty:
            lines.append("\n[M5 Primary Trading Frame - 8 แท่งล่าสุด]:")
            for idx, row in df_m5.tail(8).iterrows():
                t_str = str(idx)[-8:] if not isinstance(idx, int) else str(idx)
                lines.append(f"• M5  | O:{row['open']:.5f} H:{row['high']:.5f} L:{row['low']:.5f} C:{row['close']:.5f} V:{int(row.get('volume', 0))}")

        # 3. Micro Trigger Frame M1 (Last 5 candles)
        if df_m1 is not None and not df_m1.empty:
            lines.append("\n[M1 Micro Timing Frame - 5 แท่งล่าสุด]:")
            for idx, row in df_m1.tail(5).iterrows():
                t_str = str(idx)[-8:] if not isinstance(idx, int) else str(idx)
                lines.append(f"• M1  | O:{row['open']:.5f} H:{row['high']:.5f} L:{row['low']:.5f} C:{row['close']:.5f} V:{int(row.get('volume', 0))}")

        return "\n".join(lines)

    def evaluate_symbol(self, symbol: str, candles: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Sends raw OHLCV market data from RAM directly to Athena AI Model.
        Returns Athena's real-time decision JSON.
        """
        default_result = {
            "symbol": symbol,
            "action": "WAIT",
            "expiry_minutes": 5,
            "stake": self.default_stake,
            "confidence": 0,
            "strategy": "ATHENA_AI_REASONING",
            "reason": "รอจังหวะ A+ Setup ค่ะ",
            "m5_close": 0.0,
            "timestamp": datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            if not isinstance(candles, dict):
                return default_result

            df_m5 = candles.get('M5')
            if df_m5 is None or df_m5.empty or len(df_m5) < 10:
                default_result["reason"] = "ข้อมูลแท่งเทียนยังไม่พร้อมค่ะ"
                return default_result

            latest_close = float(df_m5['close'].iloc[-1])
            default_result["m5_close"] = latest_close

            # Format raw market snapshot for Athena AI
            market_snapshot = self._format_candles_summary(symbol, candles)

            system_instruction = (
                "คุณคือ Athena (เอเธน่า) สมองกลและเลขาธิการ AI ประจำตัวของบอส ผู้เชี่ยวชาญด้านการเทรด Binary Options ขั้นเทพ\n"
                "เป้าหมายสูงสุด: คัดเฉพาะไม้ที่เป็น 'A+ Sniper Setup' (Winrate > 85%) เพื่อพอร์ตเงินบาทไทย (THB ไม้ละ 35 บาท) ชนะครบ 2 ไม้ต่อวัน\n\n"
                "หลักการวิเคราะห์ของเอเธน่า (อ่านกราฟแท่งเทียนโดยตรง 100%):\n"
                "1. วิเคราะห์แนวโน้มใหญ่จาก M15 และหาแนวรับ-แนวต้านสำคัญบน M5\n"
                "2. ตรวจพฤติกรรมแท่งเทียน Price Action (Pin Bar ไส้ยาวปฏิเสธราคา, Rejection, Engulfing, Fakeout Trap)\n"
                "3. ตรวจสอบพื้นที่ว่างให้ราคาวิ่ง (Room-to-Target) ห้ามเข้าออเดอร์ถ้าติดกำแพงราคา\n"
                "4. ถ้าตลาดเป็นไซด์เวย์แคบ (Chop) หรือสัญญาณไม่ชัดเจน ให้เลือก WAIT (confidence < 80)\n\n"
                "ตอบกลับเป็น JSON มาตรฐานเท่านั้น (ห้ามใส่ Markdown หรือข้อความนอก JSON):\n"
                "{\n"
                '  "action": "CALL" หรือ "PUT" หรือ "WAIT",\n'
                '  "confidence": ตัวเลขอัตราความมั่นใจ 0 ถึง 100 (เช่น 90),\n'
                '  "expiry_minutes": 5 หรือ 1,\n'
                '  "reason_th": "สรุปเหตุผลการวิเคราะห์ภาษาไทยกระชับ คมชัด ลงท้ายด้วย ค่ะ เสมอ"\n'
                "}"
            )

            prompt = (
                f"วิเคราะห์สภาวะตลาดสดของคู่เงิน {symbol} ด้านล่างนี้ แล้วตัดสินใจเลือก ACTION ที่ดีที่สุดสำหรับบอส:\n\n"
                f"{market_snapshot}\n\n"
                f"ราคาปิดแท่ง M5 ล่าสุด: {latest_close:.5f}"
            )

            # Call Athena AI Model (Gemini Flash) in RAM
            ai_raw_json = self.ai_agent.send_prompt(user_prompt=prompt, system_instruction=system_instruction)

            parsed = json.loads(ai_raw_json)
            action = str(parsed.get("action", "WAIT")).strip().upper()
            confidence = int(parsed.get("confidence", 0))
            expiry_min = int(parsed.get("expiry_minutes", 5))
            reason_th = str(parsed.get("reason_th", "รอจังหวะ A+ Setup ค่ะ")).strip()

            # Normalize action
            if action not in ("CALL", "PUT", "WAIT"):
                action = "WAIT"

            # Filter with min_confidence
            if action in ("CALL", "PUT") and confidence < self.min_confidence:
                action = "WAIT"
                reason_th = f"ความมั่นใจ {confidence}% ยังไม่ถึงเกณฑ์ A+ ({self.min_confidence}%) ค่ะ"

            return {
                "symbol": symbol,
                "action": action,
                "expiry_minutes": expiry_min,
                "stake": self.default_stake,
                "confidence": confidence,
                "strategy": f"ATHENA_AI_{action}",
                "reason": reason_th,
                "m5_close": latest_close,
                "timestamp": datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            logger.exception(f"[AthenaBrain] Exception in pure AI evaluation for {symbol}: {e}")
            default_result["reason"] = f"Athena AI ติดขัด: {e}"
            return default_result

    def evaluate_all(self, symbols_candles: Dict[str, Dict[str, pd.DataFrame]]) -> List[Dict[str, Any]]:
        """Evaluates multiple symbols concurrently in parallel via Athena AI (< 1.5s)."""
        import concurrent.futures
        decisions: List[Dict[str, Any]] = []
        if not symbols_candles:
            return decisions

        max_workers = max(1, min(len(symbols_candles), 10))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="AthenaAIWorker") as executor:
            future_to_sym = {
                executor.submit(self.evaluate_symbol, sym, candles): sym
                for sym, candles in symbols_candles.items()
            }
            for future in concurrent.futures.as_completed(future_to_sym):
                sym = future_to_sym[future]
                try:
                    res = future.result()
                    decisions.append(res)
                except Exception as e:
                    logger.exception(f"[AthenaBrain] Parallel evaluation exception for {sym}: {e}")

        decisions.sort(key=lambda d: d.get("confidence", 0), reverse=True)
        return decisions
