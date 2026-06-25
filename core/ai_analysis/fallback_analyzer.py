"""
Fallback Market Analyzer
ใช้เมื่อ DeepSeek Agent เรียกไม่ได้
วิเคราะห์ด้วย RSI, MACD, EMA แทน AI
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger("FallbackAnalyzer")

@dataclass
class FallbackInsight:
    action: str          # "CALL", "PUT", or "NO_TRADE"
    confidence: int      # 0-100
    expiry: int          # minutes
    reason: str
    timestamp: str
    symbol: str
    raw_response: str = "Fallback analysis (no AI)"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FallbackAnalyzer:
    """
    วิเคราะห์ตลาดโดยใช้ indicators แทน AI
    ใช้เมื่อ DeepSeek Agent ไม่ทำงาน
    """

    def __init__(self):
        self.name = "FallbackAnalyzer"
        logger.info("[FALLBACK] Initialized")

    def analyze(self, context) -> FallbackInsight:
        """
        วิเคราะห์จาก MarketContext
        """
        if context is None:
            raise TypeError("context cannot be None")

        symbol = getattr(context, 'symbol', 'unknown')
        rsi = getattr(context, 'rsi', 50)
        macd = getattr(context, 'macd', 0)
        trend = getattr(context, 'trend', 'neutral')
        current_price = getattr(context, 'current_price', 0)
        support_resistance = getattr(context, 'support_resistance', '')

        confidence = 0
        action = "NO_TRADE"
        reason_parts = []

        # 1. วิเคราะห์ RSI
        if rsi < 30:
            confidence += 20
            action = "CALL"
            reason_parts.append(f"RSI {rsi:.1f} < 30 (oversold)")
        elif rsi > 70:
            confidence += 20
            action = "PUT"
            reason_parts.append(f"RSI {rsi:.1f} > 70 (overbought)")
        else:
            reason_parts.append(f"RSI {rsi:.1f} (neutral)")

        # 2. วิเคราะห์ MACD
        if macd > 0:
            confidence += 15
            if action == "CALL":
                action = "CALL"
            elif action == "NO_TRADE":
                action = "CALL"
            reason_parts.append(f"MACD {macd:.5f} > 0 (bullish)")
        elif macd < 0:
            confidence += 15
            if action == "PUT":
                action = "PUT"
            elif action == "NO_TRADE":
                action = "PUT"
            reason_parts.append(f"MACD {macd:.5f} < 0 (bearish)")
        else:
            reason_parts.append("MACD neutral")

        # 3. วิเคราะห์แนวโน้ม
        if trend == "bullish":
            confidence += 10
            if action == "NO_TRADE":
                action = "CALL"
            reason_parts.append("Trend: bullish")
        elif trend == "bearish":
            confidence += 10
            if action == "NO_TRADE":
                action = "PUT"
            reason_parts.append("Trend: bearish")
        else:
            reason_parts.append("Trend: neutral")

        # 4. ตรวจสอบแนวรับ/แนวต้าน (ถ้ามี)
        if support_resistance and "Resistance" in support_resistance:
            # ถ้าราคาใกล้แนวต้าน → PUT
            if current_price > 0:
                try:
                    # หาค่าแนวต้านจากข้อความ
                    import re
                    resist_match = re.search(r'Resistance:\s*([\d.]+)', support_resistance)
                    if resist_match:
                        resist = float(resist_match.group(1))
                        if current_price >= resist * 0.995:  # ใกล้แนวต้าน
                            confidence += 10
                            action = "PUT"
                            reason_parts.append(f"Near resistance {resist}")
                except Exception as e:
                    logger.exception(f"Error parsing resistance level: {e}")

        # 5. จำกัด confidence
        confidence = min(100, confidence)

        # 6. ถ้าความเชื่อมั่นต่ำเกินไป → NO_TRADE
        if confidence < 40:
            action = "NO_TRADE"
            reason_parts.append(f"Confidence {confidence}% < 40%")

        # 7. กำหนด expiry
        if action != "NO_TRADE":
            expiry = 5  # default 5 นาที
            if confidence >= 80:
                expiry = 2
            elif confidence >= 60:
                expiry = 3
            else:
                expiry = 5
        else:
            expiry = 5

        reason = " | ".join(reason_parts)

        logger.info(f"[FALLBACK] Action: {action}, Confidence: {confidence}%, Reason: {reason}")

        return FallbackInsight(
            action=action,
            confidence=confidence,
            expiry=expiry,
            reason=reason,
            timestamp=datetime.now().isoformat(),
            symbol=symbol
        )
