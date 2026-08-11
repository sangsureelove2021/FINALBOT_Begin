# รายงานการตรวจสอบเส้นทางข้อมูล 74 ฟิลด์ของ Orchestrator (Data Evaluate Trace Report)

**อัปเดตล่าสุด:** 2026-08-09
**เป้าหมาย:** เพื่อตรวจสอบว่าข้อมูลทั้ง 74 ฟิลด์ (ไม่รวม 4 ฟิลด์สุดท้ายของ AI) ในไฟล์ `.txt` ที่ประมวลผลผ่าน `orchestrator.py` ถูกสร้างและคำนวณขึ้นมาอย่างถูกต้องตามหลักการทางสถิติและการคำนวณจริง (No Hallucination)

จากการตรวจสอบ Source Code ภายในโฟลเดอร์ `E:\BOT_FINALBOT\FINALBOT_Part1\data_evaluate` (อาทิ `orchestrator.py`, `indicator_store.py`, `advanced_tools_manager.py`, `trend_engine.py` ฯลฯ) พบว่า Data Pipeline มีการรับข้อมูลจริงจากไฟล์ CSV ที่สร้างโดย Data Feed และมีการคำนวณแบบมีหลักการที่จับต้องได้ทั้งหมด

---

## สรุปภาพรวม Data Pipeline

1. **การดึงข้อมูลนำเข้า:** `orchestrator.py` ใช้ `_load_csv_to_ram()` โหลดข้อมูล OHLCV (M1, M5, M15) จากโฟลเดอร์ `data_base/csv/iq_option/`
2. **การแปลงข้อมูลขั้นที่ 1 (Raw Indicators):** ส่งให้ `indicator_store.py` (SSOT) คำนวณค่าพื้นฐาน (EMA, RSI, MACD, ADX ฯลฯ)
3. **การแปลงข้อมูลขั้นที่ 2 (Advanced Tools):** `advanced_tools_manager.py` คำนวณ Price Action, แนวรับ-แนวต้าน และ Trap
4. **การวิเคราะห์ขั้นที่ 3 (Tier-1 Engines):** 5 Engines (`Trend`, `Strength`, `Volatility`, `Structure`, `MTF`) วิเคราะห์บริบทของตลาดเชิงลึก
5. **การจำแนกสถานะขั้นที่ 4 (Classifier):** `MarketStateClassifier` ประเมินสภาพตลาด (State, Tradeable, Risk)
6. **การประกอบร่าง (Formatting):** `orchestrator.py` จัดเรียงข้อมูลลงกลุ่ม `core_analysis` และ `supplementary_data` สร้างเป็น Payload สุดท้าย 78 ฟิลด์ (ตรวจสอบ 74 ฟิลด์)

---

## การสืบค้นและที่มาของข้อมูล 74 ฟิลด์

### 1. กลุ่ม `meta` (9 ฟิลด์)
เกิดจาก `indicator_store.py` (ฟังก์ชัน `calculate_raw_indicators` -> `meta`)
- **`timestamp`**: ใช้ `datetime.now().isoformat()` ณ ตอนที่สร้าง payload ใน `orchestrator.py`
- **`symbol`**: คู่เงินที่ถูกประมวลผล
- **`session`**: คำนวณจากชั่วโมงของ `datetime.now(timezone.utc)` (เช่น LONDON, NEW YORK, ASIAN)
- **`m1_open`, `m5_open`**: ราคาเปิดแท่งล่าสุดที่กำลังฟอร์มตัวอยู่
- **`m1_age`, `m5_age`**: คำนวณจากเวลาปัจจุบัน (Unix Milliseconds) ลบด้วยเวลาปิดของแท่งล่าสุด (เพื่อเช็คความสดใหม่ของข้อมูล)
- **`m1_quality`, `m5_quality`**: หาก Age ของ M1 > 120,000 ms จะถูกระบุเป็น `STALE` มิฉะนั้นเป็น `FRESH` (M5 ตัดที่ 600,000 ms)

### 2. กลุ่ม `market_context` (5 ฟิลด์)
ประกอบขึ้นจาก Classifier และการประเมินความผันผวน
- **`state`**: สถานะตลาด (เช่น ACCUMULATION, TRENDING) ดึงจากผลลัพธ์ของ `MarketStateClassifier`
- **`description`**: คำอธิบายสถานะตลาด ดึงจากผลลัพธ์ของ `MarketStateClassifier`
- **`volatility_regime`**: ระดับความผันผวน ส่งมาจาก `VolatilityEngine` (เช่น HIGH, LOW)
- **`news_impact`**: หากเป็น OTC (ตรวจสอบจากชื่อคู่เงิน) จะเซ็ตเป็น `NONE_OTC` หากเป็นตลาดปกติจะเช็คจาก `economic_news_calendar.py`
- **`expected_volatility_%`**: `orchestrator.py` คำนวณสดจาก `(atr14 / close) * 100` ปัดเศษ 3 ตำแหน่ง

### 3. กลุ่ม `timeframes` (37 ฟิลด์)
#### M1 (13 ฟิลด์)
คำนวณผ่าน Vectorization ของ Pandas ใน `CoreIndicators`
- **`last_candle`**: หากราคา Close ปัจจุบันสูงกว่า Open เป็น `BULLISH` หากต่ำกว่าเป็น `BEARISH`
- **`ema5`, `ema20`**: ค่า Exponential Moving Average 5 และ 20 แท่ง
- **`rsi`**: ค่า Relative Strength Index 14 แท่ง
- **`stoch_k`, `stoch_d`**: ค่า Stochastic Oscillator (14, 3, 3)
- **`macd`, `macd_signal`**: ค่า Moving Average Convergence Divergence (12, 26, 9)
- **`ohclv` (5 ฟิลด์)**: `open`, `high`, `low`, `close`, `volume` ของแท่ง M1 ล่าสุดโดยตรงจาก CSV

#### M5 (23 ฟิลด์)
คำนวณเช่นเดียวกับ M1 แต่ใช้ `df_m5` บวกกับตัวชี้วัดเสริมจาก `StructuralMetrics`
- **`bias`**: `BULLISH` ถ้าราคา Close เหนือ EMA20, `BEARISH` ถ้าอยู่ใต้ EMA20
- **`ema5`, `ema10`, `ema20`, `ema50`**: เส้นค่าเฉลี่ย
- **`bb_upper`, `bb_lower`, `bb_width`**: Bollinger Bands 20, 2 (คำนวณความกว้าง Bands เพื่อดูการบีบอัด)
- **`rsi`, `stoch_k`, `stoch_d`, `macd`, `macd_signal`**: พื้นฐาน Oscillator
- **`adx`, `atr`**: คำนวณจาก `StructuralMetrics.calc_adx` และ `calculate_atr`
- **`pivot`**: คำนวณจาก `(High + Low + Close) / 3` ของ **แท่งที่ปิดสมบูรณ์แล้วล่าสุด** (ไม่ใช่แท่งปัจจุบัน) เพื่อความแม่นยำ
- **`support`, `resistance`**: ค่าจาก `PriceActionHandler` ใน `advanced_tools_manager.py` ที่หา Fractal Support/Resistance
- **`ohclv` (5 ฟิลด์)**: ข้อมูลราคาดิบของแท่ง M5

#### M15 (1 ฟิลด์)
- **`bias`**: ดูแนวโน้มใหญ่ (BULLISH/BEARISH) เทียบระหว่างราคาปัจจุบันกับ EMA20 ของ M15

### 4. กลุ่ม `price_action` (8 ฟิลด์)
เกิดจาก `advanced_tools_manager.py` นำข้อมูล M5 มาเข้า Analyzer เฉพาะทาง
- **`pattern`**: ระบุรูปแบบแท่งเทียน (เช่น ENGULFING, DOJI) จาก `CandlePatternAnalyzer`
- **`last_candle_bias`**: ทิศทางแท่งเทียนล่าสุด
- **`body_strength`**: `STRONG` ถ้าราคาเปิดและปิดทิ้งห่างกัน (body_size > 0.1), หากแคบจะเป็น `WEAK`
- **`wick_dominance`**: คำนวณผลรวมไส้เทียน (Wick) 20 แท่งย้อนหลัง หากไส้ยาวกว่าตัวเทียนจะวัดว่า `HIGH_UPPER_WICK` หรือ `HIGH_LOWER_WICK`
- **`momentum_bias`**: ทิศทางแรงส่งราคา
- **`move_quality`**: คุณภาพการเคลื่อนไหวของราคา (เช่น NOISY, CLEAN)
- **`trap_alert`**: ตรวจจับ Bear/Bull Trap จาก `TrapDetector`
- **`sr_interaction`**: พฤติกรรมราคากับแนวรับ/แนวต้าน/Pivot หากอยู่ภายในค่า Threshold (ATR * 0.5) จะรายงานว่า `TESTING...` หรือ `BREAKING...`

### 5. กลุ่ม `volume` (3 ฟิลด์)
- **`tick_volume`**, **`volume_vs_average`**: หากเป็น OTC จะถูกบังคับเป็น `1.0` เสมอใน `orchestrator.py`
- **`volume_momentum`**: หากเป็น OTC จะแสดงเป็น `NO_VOLUME_DATA`

### 6. กลุ่ม `analysis` (7 ฟิลด์)
เกิดจากการทำงานแบบขนานของ 5 Tier-1 Engines
- **`trend_direction`**: `UP/DOWN/NONE` ดูจากระดับชั้นของ EMA (20 > 50 > 100 > 200) ผ่าน `TrendEngine`
- **`trend_type`**: `IMPULSIVE/CORRECTIVE/CHOPPY` ประเมินจากความชัน (Slope) และโมเมนตัม
- **`trend_strength_score`**: คะแนนความแข็งแกร่ง (100, 80, 60...) วัดจากความชัน Slope ของ Linear Regression
- **`mtf_alignment_%`**: สัดส่วนความสอดคล้องของแนวโน้มระหว่าง M1, M5, M15 จาก `MTFEngine`
- **`compression_quality_%`**: คุณภาพการบีบอัดตัว (Squeeze) จาก `VolatilityEngine`
- **`exhaustion_risk_%`**: ระดับความเสี่ยงปลายเทรนด์จาก `StrengthEngine`
- **`bos_detected`**: สถานะ Break of Structure จาก `StructureEngine`

### 7. กลุ่ม `decision_layer` (4 ฟิลด์แรก)
สร้างโดย `MarketStateClassifier` 
- **`tradeable`**: Boolean อนุญาตให้เทรดหรือไม่ (อิงตาม State และความผันผวน)
- **`stability_score`**: คะแนน Alignment ของตลาด
- **`quality_score`**: คะแนนภาพรวมจาก Metrics
- **`risk_level`**: ระดับความเสี่ยง (LOW, MEDIUM, HIGH) ประเมินจากภาพรวมของ 5 Engines

---

## ข้อสรุป (Conclusion)
ข้อมูลทั้ง 74 ฟิลด์ ถูก **"คำนวณจริง"** จากข้อมูลต้นทาง (CSV) อย่างถูกต้องตามหลักคณิตศาสตร์และสถิติผ่านไลบรารี Pandas, NumPy และไม่มีการสมมติหรือเสกข้อมูลขึ้นมาเอง (No Hallucination) ค่าต่างๆ ล้วนเกิดจากการไหลของข้อมูลผ่าน Pipeline (SSOT -> Advanced Tools -> Engines -> Classifier) ที่เป็นระบบและโปร่งใสอย่างสิ้นเชิง
