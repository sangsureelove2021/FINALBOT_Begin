import subprocess
import json
import time
import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class AIInsight:
    action: str  # "CALL", "PUT", "NO_TRADE"
    confidence: int  # 0-100
    reason: str
    raw_response: str


class AIAnalysisEngine:
    """
    Uses deepseek-agent CLI via subprocess instead of HTTP API.
    Zero cost, runs offline (agent runs locally).
    """

    def __init__(self, agent_command: str = "deepseek-agent", timeout_seconds: int = 10):
        """
        Args:
            agent_command: command name or path to deepseek-agent executable
            timeout_seconds: timeout waiting for agent response (seconds)
        """
        self.agent_command = agent_command
        self.timeout = timeout_seconds
        self.cache = {}  # store last result if market similar
        self._failure_count = 0

    def analyze_market(self, context) -> AIInsight:
        """
        Call deepseek-agent via subprocess and return analysis.

        Args:
            context: MarketContext object (needs attributes: symbol, current_price, trend, rsi, macd, etc.)

        Returns:
            AIInsight
        """
        # 1. Build prompt from MarketContext
        prompt = self._build_prompt(context)

        # 2. Call agent via subprocess (send prompt to STDIN)
        try:
            result = subprocess.run(
                [self.agent_command],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding='utf-8',
                shell=(os.name == 'nt')
            )

            if result.returncode != 0:
                # Agent returned error
                print(f"⚠️ Agent error (code {result.returncode}): {result.stderr}")
                self._failure_count += 1
                return self._fallback_insight()

            # 3. Parse output (should be JSON) into AIInsight
            insight = self._parse_response(result.stdout)
            self._failure_count = 0  # reset failure count on success
            return insight

        except subprocess.TimeoutExpired:
            print(f"⏱️ Agent timeout after {self.timeout} seconds")
            self._failure_count += 1
            return self._fallback_insight()
        except Exception as e:
            print(f"❌ subprocess failed: {e}")
            self._failure_count += 1
            return self._fallback_insight()

    def _build_prompt(self, context) -> str:
        """Create prompt for deepseek-agent to respond only with JSON."""
        # Extract attributes safely
        symbol = getattr(context, 'symbol', 'UNKNOWN')
        current_price = getattr(context, 'current_price', 0.0)
        trend = getattr(context, 'trend', 'neutral')
        volatility = getattr(context, 'volatility', 'medium')
        support_resistance = getattr(context, 'support_resistance', 'ไม่ระบุ')
        rsi = getattr(context, 'rsi', 50)
        macd = getattr(context, 'macd', 0)
        market_state = getattr(context, 'market_state', 'normal')
        if isinstance(market_state, dict):
            market_state = market_state.get('state', 'normal')

        return f"""คุณคือนักวิเคราะห์ตลาด Forex ระดับผู้เชี่ยวชาญ โปรดวิเคราะห์ข้อมูลต่อไปนี้สำหรับ Binary Option M5

ข้อมูลตลาด:
- คู่เงิน: {symbol}
- ราคาปัจจุบัน: {current_price}
- แนวโน้ม (trend): {trend}
- ความผันผวน: {volatility}
- แนวรับ/แนวต้าน: {support_resistance}
- RSI (14): {rsi}
- MACD histogram: {macd}
- สภาวะตลาด: {market_state}

คำสั่ง: ให้ตอบเป็น JSON เท่านั้น ตามรูปแบบนี้:
{{"action": "CALL/PUT/NO_TRADE", "confidence": 0-100, "reason": "เหตุผลสั้นๆ ภาษาไทย"}}

ห้ามมีข้อความอื่นนอกเหนือจาก JSON"""

    def _parse_response(self, raw_output: str) -> AIInsight:
        """Extract JSON from agent output."""
        raw_output = raw_output.strip()

        # Find first JSON block in output (in case agent speaks before)
        start_idx = raw_output.find('{')
        end_idx = raw_output.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = raw_output[start_idx:end_idx+1]
        else:
            json_str = raw_output

        try:
            data = json.loads(json_str)
            action = data.get('action', 'NO_TRADE')
            if action not in ['CALL', 'PUT', 'NO_TRADE']:
                action = 'NO_TRADE'
            confidence = int(data.get('confidence', 50))
            confidence = max(0, min(100, confidence))
            reason = data.get('reason', 'Agent ไม่ให้เหตุผล')

            return AIInsight(
                action=action,
                confidence=confidence,
                reason=reason,
                raw_response=raw_output
            )
        except json.JSONDecodeError:
            print(f"⚠️ Agent sent invalid JSON: {raw_output[:200]}")
            return self._fallback_insight()

    def _fallback_insight(self) -> AIInsight:
        """When agent fails, use fallback (NO_TRADE with low confidence)."""
        return AIInsight(
            action="NO_TRADE",
            confidence=30,
            reason="Agent ไม่ตอบสนอง ใช้ fallback",
            raw_response=""
        )

    @property
    def consecutive_failures(self) -> int:
        return self._failure_count

    def reset_failure_count(self):
        self._failure_count = 0
