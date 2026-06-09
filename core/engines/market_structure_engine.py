from core.interfaces.engine_interface import EngineInterface
from core.models.candle import Candle
from typing import List, Dict, Any

class MarketStructureEngine(EngineInterface):
    """วิเคราะห์โครงสร้างราคา (HH, HL, LL, LH) เพื่อจำแนกสภาวะตลาด"""
    
    def __init__(self, config: dict = None):
        self.name = "MarketStructure"
        self.lookback = 15  # ดูย้อนหลัง 15 แท่งเพื่อความแม่นยำ

    def calculate(self, candles: List[Candle]) -> Dict[str, Any]:
        if len(candles) < self.lookback:
            return {"status": "INSUFFICIENT_DATA", "regime": "UNKNOWN", "structure": "UNKNOWN"}

        highs = [c.high for c in candles[-self.lookback:]]
        lows = [c.low for c in candles[-self.lookback:]]
        
        # หาจุดสูงสุดและต่ำสุดในช่วง lookback
        recent_highs = highs[-5:]
        recent_lows = lows[-5:]
        prev_highs = highs[-10:-5]
        prev_lows = lows[-10:-5]

        current_high = max(recent_highs)
        prev_high = max(prev_highs)
        current_low = min(recent_lows)
        prev_low = min(prev_lows)

        # วิเคราะห์โครงสร้าง
        if current_high > prev_high and current_low > prev_low:
            structure = "BULLISH"
            regime = "STRONG_TREND" if (current_high - prev_high) > (prev_high - max(prev_highs)) else "WEAK_TREND"
        elif current_high < prev_high and current_low < prev_low:
            structure = "BEARISH"
            regime = "STRONG_TREND" if (prev_low - current_low) > (min(prev_lows) - prev_low) else "WEAK_TREND"
        else:
            structure = "RANGING"
            # เช็ค Choppy
            avg_range = sum(c.high - c.low for c in candles[-5:]) / 5
            if avg_range < (sum(c.high - c.low for c in candles[-15:]) / 15) * 0.8:
                regime = "CHOPPY"
            else:
                regime = "RANGING"

        # เช็ค Breakout
        if abs(current_high - prev_high) > (prev_high * 0.001): # 0.1% move
            if current_high > prev_high and structure == "BULLISH":
                regime = "BREAKOUT"

        return {
            "status": "ACTIVE",
            "regime": regime,
            "structure": structure,
            "last_high": current_high,
            "last_low": current_low,
            "trend_strength": abs(current_high - prev_high) + abs(current_low - prev_low)
        }