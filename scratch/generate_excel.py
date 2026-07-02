import pandas as pd
import os

data = [
    # Meta (6 items)
    ("meta", "timestamp", "System Time", "Real Data", "เวลาประมวลผลจริง"),
    ("meta", "symbol", "Market Feed", "Real Data", "ชื่อคู่เงิน"),
    ("meta", "session", "_derive_session()", "Real Data", "เวลาเปิด-ปิดตลาด"),
    ("meta", "price", "Market Feed", "Real Data", "ราคาปิดแท่งล่าสุด"),
    ("meta", "data_age_ms", "Data Adapter", "Real Data", "ความใหม่ของข้อมูล"),
    ("meta", "data_quality", "_derive_data_quality()", "Real Data", "คุณภาพของข้อมูล (เทียบจาก age)"),
    
    # Market Context (5 items)
    ("market_context", "state", "MarketStateClassifier", "Real Data", "สถานะตลาด (เช่น TRENDING_STRONG)"),
    ("market_context", "description", "MarketStateClassifier", "Real Data", "คำอธิบายสถานะตลาด"),
    ("market_context", "volatility_regime", "VolatilityEngine", "Real Data", "ความผันผวน (NORMAL, HIGH)"),
    ("market_context", "news_impact", "News/Calendar Data", "Real Data / Fallback", "ความแรงข่าว (หากเป็น OTC จะถูกบังคับเป็น NONE_OTC)"),
    ("market_context", "expected_volatility_%", "ATR / Close * 100", "Real Data", "ความผันผวนที่คาดหวัง"),
    
    # Timeframes M1 (8 items)
    ("timeframes.m1", "last_candle", "M1 Engine", "Real Data", "ราคาปิด M1"),
    ("timeframes.m1", "ema5", "M1 Engine", "Real Data", "EMA 5"),
    ("timeframes.m1", "ema20", "M1 Engine", "Real Data", "EMA 20"),
    ("timeframes.m1", "rsi", "M1 Engine", "Real Data", "RSI 14"),
    ("timeframes.m1", "stoch_k", "M1 Engine", "Real Data", "Stochastic %K"),
    ("timeframes.m1", "stoch_d", "M1 Engine", "Real Data", "Stochastic %D"),
    ("timeframes.m1", "macd", "M1 Engine", "Real Data", "MACD Line"),
    ("timeframes.m1", "macd_signal", "M1 Engine", "Real Data", "MACD Signal Line"),
    
    # Timeframes M5 (18 items)
    ("timeframes.m5", "bias", "M5 Engine", "Real Data", "ทิศทางอคติ M5"),
    ("timeframes.m5", "ema5", "M5 Engine", "Real Data", "EMA 5"),
    ("timeframes.m5", "ema10", "M5 Engine", "Real Data", "EMA 10"),
    ("timeframes.m5", "ema20", "M5 Engine", "Real Data", "EMA 20"),
    ("timeframes.m5", "ema50", "M5 Engine", "Real Data", "EMA 50"),
    ("timeframes.m5", "bb_upper", "M5 Engine", "Real Data", "Bollinger Upper"),
    ("timeframes.m5", "bb_lower", "M5 Engine", "Real Data", "Bollinger Lower"),
    ("timeframes.m5", "bb_width", "M5 Engine", "Real Data", "Bollinger Width"),
    ("timeframes.m5", "rsi", "M5 Engine", "Real Data", "RSI 14"),
    ("timeframes.m5", "stoch_k", "M5 Engine", "Real Data", "Stochastic %K"),
    ("timeframes.m5", "stoch_d", "M5 Engine", "Real Data", "Stochastic %D"),
    ("timeframes.m5", "macd", "M5 Engine", "Real Data", "MACD Line"),
    ("timeframes.m5", "macd_signal", "M5 Engine", "Real Data", "MACD Signal Line"),
    ("timeframes.m5", "adx", "M5 Engine", "Real Data", "ADX"),
    ("timeframes.m5", "atr", "M5 Engine", "Real Data", "ATR"),
    ("timeframes.m5", "support", "M5 Engine (Structure)", "Real Data", "แนวรับสำคัญล่าสุด"),
    ("timeframes.m5", "resistance", "M5 Engine (Structure)", "Real Data", "แนวต้านสำคัญล่าสุด"),
    ("timeframes.m5", "pivot", "M5 Engine", "Real Data", "จุดหมุน (Pivot)"),
    
    # Timeframes M15 (1 item)
    ("timeframes.m15", "bias", "M15 Engine", "Real Data / Fallback", "หากดึงข้อมูล M15 ไม่ได้จะแสดงเป็น 'NO'"),
    
    # Price Action (8 items)
    ("price_action", "pattern", "PriceActionAnalyzer", "Real Data", "รูปแบบแท่งเทียน"),
    ("price_action", "last_candle_bias", "PriceActionAnalyzer", "Real Data", "ทิศทางแท่งล่าสุด"),
    ("price_action", "body_strength", "PriceActionAnalyzer", "Real Data", "ความแข็งแกร่งของ Body"),
    ("price_action", "wick_dominance", "PriceActionAnalyzer", "Real Data", "อิทธิพลของไส้เทียน"),
    ("price_action", "momentum_bias", "PriceActionAnalyzer", "Real Data", "โมเมนตัมราคาระยะสั้น"),
    ("price_action", "move_quality", "PriceActionAnalyzer", "Real Data", "คุณภาพการเคลื่อนที่"),
    ("price_action", "trap_alert", "PriceActionAnalyzer", "Real Data", "สัญญาณกับดัก (Trap)"),
    ("price_action", "sr_interaction", "PriceActionAnalyzer", "Real Data", "การทดสอบแนวรับ/ต้าน"),
    
    # Volume (3 items)
    ("volume", "tick_volume", "Volume Data", "Real Data / Fallback", "ปริมาณการซื้อขาย (หาก OTC = 1.0)"),
    ("volume", "volume_momentum", "Volume Data", "Real Data / Fallback", "โมเมนตัมวอลุ่ม (หาก OTC = NO_VOLUME_DATA)"),
    ("volume", "volume_vs_average", "Volume Data", "Real Data / Fallback", "สัดส่วนวอลุ่มต่อค่าเฉลี่ย (หาก OTC = 1.0)"),
    
    # Analysis (7 items)
    ("analysis", "trend_direction", "TrendEngine", "Real Data", "ทิศทางเทรนด์หลัก"),
    ("analysis", "trend_type", "TrendEngine", "Real Data", "ชนิดของเทรนด์ (เช่น CHOPPY)"),
    ("analysis", "trend_strength_score", "StrengthEngine", "Real Data", "คะแนนความแข็งแรงเทรนด์"),
    ("analysis", "mtf_alignment_%", "TrendEngine (MTF)", "Real Data", "ความสอดคล้องของหลาย Timeframe (ทศนิยม 3 ตำแหน่ง)"),
    ("analysis", "compression_quality_%", "VolatilityEngine", "Real Data", "คุณภาพการบีบตัวของราคา (ทศนิยม 3 ตำแหน่ง)"),
    ("analysis", "exhaustion_risk_%", "StrengthEngine", "Real Data", "ความเสี่ยงการหมดแรง (ทศนิยม 3 ตำแหน่ง)"),
    ("analysis", "bos_detected", "StructureEngine", "Real Data", "ตรวจพบการเบรกโครงสร้าง (Break of Structure)"),
    
    # Decision Layer (8 items) - 64 items total
    ("decision_layer", "tradeable", "MarketStateClassifier", "Real Data", "สิทธิ์ในการเทรด (True/False) คำนวณจริง"),
    ("decision_layer", "stability_score", "MarketStateClassifier", "Real Data", "คะแนนความเสถียรของกราฟ"),
    ("decision_layer", "quality_score", "MarketStateClassifier", "Real Data", "คะแนนคุณภาพของกราฟ"),
    ("decision_layer", "risk_level", "MarketStateClassifier", "Real Data", "ระดับความเสี่ยง (LOW, MEDIUM, HIGH)"),
    ("decision_layer", "confidence_score", "AI Placeholder", "AI Placeholder", "รอการวิเคราะห์จาก AI (เว้นที่ว่างไว้)"),
    ("decision_layer", "suggested_expiry_minutes", "AI Placeholder", "AI Placeholder", "รอการวิเคราะห์จาก AI (เว้นที่ว่างไว้)"),
    ("decision_layer", "suggested_action", "AI Placeholder", "AI Placeholder", "รอการวิเคราะห์จาก AI (เว้นที่ว่างไว้)"),
    ("decision_layer", "final_reason_th", "AI Placeholder", "AI Placeholder", "รอการวิเคราะห์จาก AI (เว้นที่ว่างไว้)"),
]

df = pd.DataFrame(data, columns=["Category", "Field_Name", "Source", "Status", "Remark"])

output_path = r"E:\BOT_FINALBOT13 STG\BOT_FINALBOT\docs\Validation_Report_65_Items.xlsx"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_excel(output_path, index=False)
print(f"Successfully generated {output_path}")
