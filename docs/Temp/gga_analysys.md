# รายงานการตรวจสอบระบบบอทเทรดและวิเคราะห์ข้อผิดพลาดทางเทคนิค (Trading Bot Audit & Code Inspection Report)

**ผู้ตรวจสอบ:** Athena (เอเธน่า) - Trading Bot Auditor & Code Inspector  
**ตำแหน่งเป้าหมาย:** `E:\BOT_FINALBOT\FINALBOT_Part1\data_evaluate` (รวมทุกไฟล์และโฟลเดอร์ย่อยจำนวน 32 ไฟล์)  
**วันที่ตรวจสอบ:** 11 สิงหาคม 2569  
**สถานะการแก้ไขโค้ด:** ไม่มีการแก้ไขโค้ดซอร์สใดๆ (Read-Only Audit & Inspection)

---

## 1. บทสรุปผู้บริหาร (Executive Summary)

เอเธน่าได้ทำการตรวจสอบซอร์สโค้ดทุกไฟล์ในโฟลเดอร์ `E:\BOT_FINALBOT\FINALBOT_Part1\data_evaluate` แบบบรรทัดต่อบรรทัด (Line-by-Line Inspection) ตาม 3 หลักการสำคัญที่ Boss กำหนดไว้อย่างเคร่งครัด ได้แก่:

1. **Data Integrity (ความถูกต้องของข้อมูลราคา):** ตรวจพบจุดที่มีการใช้ค่าคงที่เดาขึ้นเอง (Hardcoded Default/Fallback), ข้อมูล Mock และการใช้ generic `try-except` ปิดบังข้อผิดพลาดซ่อนอยู่
2. **Single Source of Truth - SSOT (การคำนวณอินดิเคเตอร์ 1 ครั้งต่อรอบ):** ตรวจพบโมดูลย่อยและวิเคราะห์ระดับขั้นสูง (Advanced Tools) จำนวนมากแอบคำนวณ EMA, RSI, MACD, Linear Regression Slope, Choppiness Index ฯลฯ ซ้ำซ้อนจาก DataFrame ตรงๆ แทนที่จะดึงจาก `indicator_store`
3. **No Dead Data (การนำอินดิเคเตอร์ไปใช้งานจริง):** ตรวจพบอินดิเคเตอร์จำนวนมากที่ถูกคำนวณและจัดเก็บไว้ใน `indicator_store` แต่ถูกปล่อยทิ้งไว้เฉยๆ (Idle) ไม่เคยถูก Engine หรือ Classifier ใดดึงไปใช้ตัดสินใจจริง

---

## 2. รายละเอียดผลการตรวจสอบตาม 3 หลักการ (Detailed Findings)

### 2.1 หลักการที่ 1: Data Integrity (ความถูกต้องและสมบูรณ์ของข้อมูลราคา)

จากการตรวจทาน พบจุดเสี่ยงและข้อผิดพลาดเกี่ยวกับ Data Integrity ดังต่อไปนี้:

#### 1) การใช้ Hardcoded Fallback / Mock Data เมื่อข้อมูลไม่เพียงพอ
* **[structural_metrics.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/indicator_store/structural_metrics.py#L34-L39)** (บรรทัดที่ 34-39):
  ```python
  else:
      res['atr14'] = 0.0
      res['atr_percentile'] = 50.0
      res['atr_zscore'] = 0.0
      res['atr_recent_avg'] = 0.0
      res['atr_past_avg'] = 0.0
  ```
  *ปัญหา:* เมื่อแถวข้อมูล ATR มีความยาว 0 แทนที่จะยก Exception แบบ Fail-Fast ระบบกลับคืนค่าสมมติ `atr_percentile = 50.0` ซึ่งเป็นการเดาค่าขึ้นเอง
* **[structural_metrics.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/indicator_store/structural_metrics.py#L133-L134)** (บรรทัดที่ 133-134):
  ```python
  else:
      return {'box_duration': 10, 'box_tightness': 2.5}
  ```
  *ปัญหา:* หากข้อมูลราคา High/Low มีน้อยกว่า 20 แท่ง ระบบส่งคืนค่าเดาแบบ Hardcode คือ `box_duration = 10` และ `box_tightness = 2.5` ซึ่งละเมิดกฎ Fail-Fast Policy (กฎข้อ 7)
* **[market_pressure_analyzer.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/market_classifier/market_pressure_analyzer.py#L69-L70)** (บรรทัดที่ 69-70):
  ```python
  if total_weight == 0:
      return 50
  ```
  *ปัญหา:* หาก Volume รวมเป็น 0 คืนค่าแรงซื้อ 50 (Neutral) โดยไม่มีการแจ้งเตือน

#### 2) การใช้ Generic Exception Swallowing (หมกเม็ด Error & ละเมิดวินัย AI กฎข้อ 1 และ 7)
* **[market_state_classifier.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/market_classifier/market_state_classifier.py#L650-L700)** (บรรทัดที่ 650-700):
  ฟังก์ชัน `_calculate_consistency`, `_calculate_cleanliness`, `_calculate_directionality` ใช้โครงสร้าง:
  ```python
  except Exception:
      return 50
  ```
  *ปัญหา:* แอบดักจับทุก Exception แล้วคืนค่า fallback 50 ปิดบังข้อผิดพลาดทางการคำนวณโดยไม่ใช้ `logger.exception()` หรือบันทึก Stack Trace
* **[context_synthesizer.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/context_synthesizer.py#L765-L773)** (บรรทัดที่ 765-773 ใน `orchestrator.py`):
  เมื่อสร้าง `MarketContext` หากฟิลด์ย่อยไม่ถูกคำนวณ มีการสร้างดิคชันนารีสำรอง (Default Dictionary) เช่น `{'continuation_probability': 50, 'bias': 'NONE'}` แทนที่จะบังคับ Fail-Fast

---

### 2.2 หลักการที่ 2: Single Source of Truth - SSOT (การคำนวณอินดิเคเตอร์เพียง 1 ครั้งต่อรอบ)

จากการตรวจทาน พบว่าระบบ `indicator_store.py` ได้ถูกออกแบบให้เป็น Layer 1 (SSOT) แต่โมดูลและ Engine วิเคราะห์หลายตัวกลับ **แอบสั่งคำนวณอินดิเคเตอร์ซ้ำซ้อนด้วยตัวเองจาก DataFrame** โดยไม่ยอมดึงจาก `indicator_store`:

#### 1) การคำนวณ EMA ซ้ำซ้อน (EMA Re-calculation)
* **[mtf_engine.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/market_classifier/mtf_engine.py#L48-L51)** และ **[mtf_engine.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/market_classifier/mtf_engine.py#L118-L126)** (บรรทัดที่ 48-51, 118-126):
  ใน `MTFEngine.analyze` เมื่อประมวลผลไทม์เฟรม M1 และ M15 โค้ดส่ง `payload_m5 = None` ทำให้ฟังก์ชัน `_tf_direction` ตกไปเข้าเงื่อนไข `else` สั่งคำนวณ EMA20 และ EMA50 ใหม่จาก `df['close']` ทุกรอบ:
  ```python
  ema20 = df['close'].ewm(span=20).mean().iloc[-1]
  ema50 = df['close'].ewm(span=50).mean().iloc[-1]
  ```
* **[continuation_analyzer.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/advanced_tools/continuation_analyzer.py#L113)** (บรรทัดที่ 113):
  แอบคำนวณ EMA20 ซ้ำ: `ema = closes.ewm(span=20).mean()`
* **[persistence_analyzer.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/advanced_tools/persistence_analyzer.py#L78)** และ **[persistence_analyzer.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/advanced_tools/persistence_analyzer.py#L142)** (บรรทัดที่ 78, 142):
  แอบคำนวณ EMA20 ซ้ำ 2 จุด: `ema = df['close'].ewm(span=20).mean().iloc[-1]` และ `ema = closes.ewm(span=20).mean()`
* **[conflict_analyzer.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/advanced_tools/conflict_analyzer.py#L30)** และ **[conflict_analyzer.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/advanced_tools/conflict_analyzer.py#L68-L74)** (บรรทัดที่ 30, 68-74):
  `AdvancedToolsManager.analyze_all` เรียก `self.conflict.analyze(df_m5)` โดยไม่ได้ส่ง `payload=basic_payload` ทำให้ `payload` เป็นดิคชันนารีว่างเปล่า บังคับให้ `conflict_analyzer.py` ตกไปใช้ Fallback คำนวณ EMA20/EMA50 ใหม่จาก `df['close']` เอง

#### 2) การคำนวณ RSI และ MACD ซ้ำซ้อน (RSI & MACD Re-calculation)
* **[divergence_analyzer.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/advanced_tools/divergence_analyzer.py#L28-L29)**, **[divergence_analyzer.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/advanced_tools/divergence_analyzer.py#L58-L72)** และ **[divergence_analyzer.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/advanced_tools/divergence_analyzer.py#L74-L84)** (บรรทัดที่ 28-29, 58-84):
  `DivergenceAnalyzer` คำนวณอนุกรม RSI 14 วัน (บรรทัดที่ 58-72) และอนุกรม MACD (Fast 12, Slow 26, Signal 9) (บรรทัดที่ 74-84) จาก `candles_df['close']` ใหม่ทั้งหมด โดยไม่ดึงค่า RSI/MACD ที่ `indicator_store` คำนวณไว้แล้ว

#### 3) การคำนวณ Slope, Volatility & Indicator อื่นๆ ซ้ำซ้อน
* **[continuation_analyzer.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/advanced_tools/continuation_analyzer.py#L195)** (บรรทัดที่ 195):
  แอบคำนวณ Linear Regression Slope ซ้ำซ้อน: `np.polyfit(np.arange(len(closes)), closes.values, 1)[0]`
* **[transition_analyzer.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/advanced_tools/transition_analyzer.py#L115-L116)** (บรรทัดที่ 115-116):
  แอบคำนวณ Slope ซ้ำซ้อนด้วย `np.polyfit`
* **[conflict_analyzer.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/advanced_tools/conflict_analyzer.py#L88-L89)** (บรรทัดที่ 88-89):
  แอบคำนวณ Rate of Change (ROC) ซ้ำซ้อนจาก DataFrame
* **[noise_detector.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/noise_detector.py#L50-L71)** (บรรทัดที่ 50-71):
  คำนวณ Choppiness Index และ True Range Sum จาก `candles_df` ใหม่
* **[price_action_handler.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/advanced_tools/price_action_handler.py#L102-L128)** (บรรทัดที่ 102-128):
  คำนวณ True Range และ Path Efficiency จาก DataFrame ใหม่
* **[efficiency_analyzer.py](file:///E:/BOT_FINALBOT/FINALBOT_Part1/data_evaluate/orchestration/advanced_tools/efficiency_analyzer.py#L49-L65)** (บรรทัดที่ 49-65):
  คำนวณ Kaufman Efficiency Ratio (KER) จาก DataFrame ใหม่

---

### 2.3 หลักการที่ 3: No Dead Data (การนำอินดิเคเตอร์ไปใช้งานจริง)

จากการตรวจสอบเปรียบเทียบระหว่างตัวแปรที่ถูกคำนวณใน `indicator_store.py` (รวมถึง `core_indicators.py` และ `structural_metrics.py`) กับโมดูลที่รับข้อมูลไปใช้งานจริง พบอินดิเคเตอร์และฟิลด์ที่ถูกคำนวณเสร็จแล้วแต่นั่งทิ้งไว้เฉยๆ (Dead/Idle Data) ดังนี้:

#### 1) อินดิเคเตอร์ใน M5 ที่ถูกคำนวณแต่ไม่มี Engine ใดดึงไปใช้งาน (Idle M5 Indicators)
1. **`ema5` & `ema10` (M5):** คำนวณใน `indicator_store.py` (บรรทัดที่ 84) ถูกดึงไปใส่ใน String Report เท่านั้น แต่ **ไม่มี Engine/Classifier ตัวใดนำไปใช้คำนวณหรือตัดสินใจเลย** (`trend_engine` ใช้เฉพาะ EMA20, 50, 100, 200)
2. **`bb_upper` & `bb_lower` (M5):** คำนวณใน `CoreIndicators.calculate_bb` และเก็บใน `m5` แต่ `volatility_engine` ใช้เพียง `bb_width` และ `bbw_sma_100` ส่วน `bb_upper` / `bb_lower` ไม่ถูกใช้งานเลย
3. **`rsi7` (M5):** คำนวณใน `indicator_store.py` (บรรทัดที่ 93) แต่ทุก Engine (`strength_engine`, `market_state_classifier`) ดึงไปใช้เฉพาะ `rsi14` ทำให้ `rsi7` ของ M5 กลายเป็น Dead Data
4. **`macd_signal` (M5):** คำนวณใน `CoreIndicators.calculate_macd` แต่ `strength_engine` ดึงไปใช้เฉพาะ `macd` และ `macd_hist`
5. **`stoch_k` & `stoch_d` (M5):** คำนวณ Stochastic (14, 3, 3) ใน `indicator_store.py` (บรรทัดที่ 100) แต่ **ไม่มี Engine ใดในระบบเรียกใช้งาน `stoch_k` หรือ `stoch_d` เลยแม้แต่ตัวเดียว**
6. **`dx` (M5):** คำนวณใน `StructuralMetrics.calc_adx` (บรรทัดที่ 82) และเก็บใน `m5['dx']` แต่ Engine ดึงไปใช้เฉพาะ `adx`, `di_plus`, `di_minus`
7. **`volume_ma20` & `volume_spike` (M5):** คำนวณใน `StructuralMetrics.calculate_volume_metrics` (บรรทัดที่ 96-97) แต่ไม่มี Engine ดึงไปใช้
8. **`slope_20` & `slope_50` (M5):** คำนวณใน `indicator_store.py` (บรรทัดที่ 120-121) แต่ `trend_engine` ดึงไปใช้เฉพาะ `slope_10`
9. **`r2` & `s2` (M5):** คำนวณใน `indicator_store.py` (บรรทัดที่ 144, 148) แต่ `structure_engine` และ `AdvancedToolsManager` ดึงไปใช้เฉพาะ `r1`, `s1`, `support`, `resistance`
10. **`support_20` & `resistance_20` (M5):** คำนวณใน `indicator_store.py` (บรรทัดที่ 157-158) แต่ไม่มี Engine ใดดึงไปใช้

#### 2) อินดิเคเตอร์ใน M1 และ M15 ที่นั่งทิ้งไว้เฉยๆ (Idle M1 / M15 Indicators)
* **`m1['rsi14']`:** คำนวณใน `indicator_store.py` (บรรทัดที่ 189) แต่ไม่มี Engine ใดดึง `rsi14` ของ M1 ไปใช้งาน (ดึงเฉพาะ M5)
* **`m1['pivot']`, `m1['r1']`, `m1['s1']`, `m1['support']`, `m1['resistance']`:** คำนวณ Floor Pivot ของ M1 ใน `indicator_store.py` (บรรทัดที่ 222-226) แต่ไม่มี Engine ใดดึง Pivot ของ M1 ไปใช้งาน
* **`m15['rsi14']`:** คำนวณใน `indicator_store.py` (บรรทัดที่ 275) แต่ไม่มี Engine ใดดึง `rsi14` ของ M15 ไปใช้งาน

#### 3) สถานะ EMA200 ของ M1, M5 และ M15 (ตามโจทย์เฉพาะของ Boss)
* **EMA200 ของ M1:** **ไม่มีการคำนวณ (Absent)** ใน `indicator_store.py` (M1 คำนวณเฉพาะ EMA20)
* **EMA200 ของ M15:** **ไม่มีการคำนวณ (Absent)** ใน `indicator_store.py` (M15 คำนวณเฉพาะ EMA20)
* **EMA200 ของ M5:** มีการคำนวณใน `indicator_store.py` (`m5['ema200']`) และถูกนำไปใช้งานจริงโดย `trend_engine.py` (บรรทัดที่ 94)

---

## 3. ตารางสรุปหลักฐานและอ้างอิงไฟล์ (File & Code Evidence Matrix)

| ลำดับ | ชื่อไฟล์ (File Name) | ความเกี่ยวพันตามหลักการ | บรรทัดที่พบหลักฐาน (Line Ref) | รายละเอียดข้อผิดพลาด / สิ่งที่ตรวจพบ |
|---|---|---|---|---|
| 1 | `indicator_store/core_indicators.py` | Dead Data | L13-32, L61-70 | คำนวณ BB (`bb_upper/lower`), Stochastic (`stoch_k/d`) แต่ไม่ได้ถูกนำไปใช้ตัดสินใจ |
| 2 | `indicator_store/structural_metrics.py` | Data Integrity / Dead Data | L34-39, L82, L96-97, L133-134 | คืนค่า Mock (`atr14=0.0`, `percentile=50.0`, `box_dur=10`, `tightness=2.5`), คำนวณ `dx`, `volume_ma20/spike` ทิ้งไว้ |
| 3 | `indicator_store/indicator_store.py` | Dead Data | L84, L93, L97, L120-121, L144-158, L189, L222-226, L275 | คำนวณ `ema5`, `ema10`, `rsi7`, `macd_signal`, `slope_20/50`, `r2/s2`, `support/resist_20`, M1 `rsi14/pivot`, M15 `rsi14` แต่ไม่ได้นำไปใช้ใน Engine ใด |
| 4 | `market_classifier/mtf_engine.py` | SSOT Violation | L48-51, L118-126 | คำนวณ EMA20 และ EMA50 ใหม่จาก `df['close']` สำหรับ M1 และ M15 แทนที่จะดึงจาก SSOT |
| 5 | `advanced_tools/divergence_analyzer.py` | SSOT Violation | L28-29, L58-84 | คำนวณอนุกรม RSI และ MACD ใหม่ทั้งหมดจาก DataFrame |
| 6 | `advanced_tools/continuation_analyzer.py` | SSOT Violation | L113, L195 | คำนวณ EMA20 และ Slope ใหม่ด้วย `ewm()` และ `np.polyfit()` |
| 7 | `advanced_tools/persistence_analyzer.py` | SSOT Violation | L78, L142 | คำนวณ EMA20 ใหม่ 2 จุดด้วย `ewm()` |
| 8 | `advanced_tools/conflict_analyzer.py` | SSOT Violation / Defect | L30, L68-74, L88-89 | `AdvancedToolsManager` ไม่ส่ง `payload` ทำให้ต้อง Fallback คำนวณ EMA20/50 และ ROC เองจาก DataFrame |
| 9 | `market_classifier/market_state_classifier.py` | Data Integrity / Rule 1 & 7 | L207, L650-700 | ใช้ generic `except Exception:` คืนค่า fallback 50 ปิดบังข้อผิดพลาด |
| 10 | `market_classifier/market_pressure_analyzer.py` | SSOT Violation / Data Integrity | L47-126, L69-70 | คำนวณแรงซื้อขายและ Effort/Result เองจาก DataFrame, คืนค่า fallback 50 |
| 11 | `advanced_tools/advanced_tools_manager.py` | SSOT Coordination | L153-161 | ส่งเฉพาะ `df_m5` ให้เครื่องมือย่อย โดยไม่ได้ส่ง `basic_payload` เพื่อให้ดึง SSOT |
| 12 | `advanced_tools/price_action_handler.py` | SSOT Violation | L102-128, L235-261 | คำนวณ True Range, Path Efficiency และ Volume Ratio เอง |
| 13 | `advanced_tools/transition_analyzer.py` | SSOT Violation | L57-120 | คำนวณ Volatility shift และ Slope (`np.polyfit`) เอง |
| 14 | `advanced_tools/efficiency_analyzer.py` | SSOT Violation | L49-65 | คำนวณ Kaufman Efficiency Ratio เองจาก DataFrame |
| 15 | `advanced_tools/behavior_analyzer.py` | SSOT Violation | L57-93 | คำนวณ Conviction, Hesitation, Pressure เองจาก DataFrame |
| 16 | `orchestration/noise_detector.py` | SSOT Violation | L50-71 | คำนวณ Choppiness Index และ True Range เอง |
| 17 | `orchestration/trap_detector.py` | SSOT Check | L57-124 | วิเคราะห์ False Breakout, Stop Hunt จาก raw OHLCV |
| 18 | `orchestration/base_engine.py` | Standard Architecture | L47-101 | เป็นคลาสแม่สำหรับ Engine ต่างๆ |
| 19 | `orchestration/context_synthesizer.py` | Data Integrity | L765-773 (in orchestrator) | มีการเติมค่าสำรอง (Default Dict) ให้ฟิลด์ที่ขาดหายไป |
| 20 | `orchestration/explainability_engine.py` | Clean Data Flow | L20-40 | อ่านข้อมูลจาก MarketContext |
| 21 | `orchestration/liquidity_engine.py` | SSOT Check | L47-124 | วิเคราะห์ Equal Highs/Lows จาก raw OHLCV |
| 22 | `orchestration/probability_estimator.py` | Clean Data Flow | L63-132 | วิเคราะห์น้ำหนักความน่าจะเป็นจาก MarketContext |
| 23 | `orchestration/signal_throttle.py` | Operational Logic | L34-56 | จัดการ Cooldown สัญญาณ |
| 24 | `market_classifier/market_structure_engine.py` | SSOT Check | L52-78 | วิเคราะห์สภาวะโครงสร้างจาก OHLCV |
| 25 | `market_classifier/strength_engine.py` | SSOT Compliant | L40-51 | อ่าน ADX, RSI, MACD, ROC ตรงจาก `m5` payload (ปฏิบัติตาม SSOT ถูกต้อง) |
| 26 | `market_classifier/structure_engine.py` | SSOT Compliant | L39-60 | อ่าน Pivot, S1, R1, Box Metrics ตรงจาก `m5` payload |
| 27 | `market_classifier/trend_engine.py` | SSOT Compliant | L84-107 | อ่าน EMA20, 50, 100, 200, Slope_10, ROC ตรงจาก `m5` payload |
| 28 | `market_classifier/volatility_engine.py` | SSOT Compliant | L39-55 | อ่าน ATR14, Percentile, ZScore, BBW ตรงจาก `m5` payload |
| 29 | `orchestrator.py` | Data Pipeline Hub | L119-195, L257-360 | อ่าน CSV เข้า RAM และแจกจ่าย Payload ให้ Engine ต่างๆ |
| 30 | `economic_news_calendar.py` | External News Data | L162-250 | ดึงและวิเคราะห์ข่าวสารเศรษฐกิจ |
| 31 | `exceptions.py` | Custom Exceptions | L5-15 | นิยาม `InvalidInputError`, `ComputationError` |
| 32 | `advanced_tools/candle_pattern_analyzer.py` | Pattern Logic | L36-50 | ตรวจหา Candlestick Patterns จาก OHLCV |

---

## 4. ข้อสรุปและข้อเสนอแนะในการปรับปรุงระบบ (Conclusions & Recommendations)

เพื่อให้ระบบบอทเทรดเป็นไปตามหลักการ **Data Integrity**, **SSOT (Single Source of Truth)** และ **No Dead Data** 100% เอเธน่าขอเสนอแนะแนวทางปรับปรุงในอนาคต (เพื่อรอคำสั่งอนุมัติจาก Boss) ดังนี้ค่ะ:

1. **ขจัด Dead Data ใน `indicator_store.py`:**
   - ตัดการคำนวณ Stochastic (`stoch_k`, `stoch_d`), `rsi7`, `ema5`, `ema10`, `slope_20`, `slope_50`, `r2`, `s2`, `support_20`, `resistance_20`, M1 `rsi14/pivot`, M15 `rsi14` ออก หรือนำไปปรับใช้ใน Engine ให้เกิดประโยชน์จริง
2. **ปรับปรุงเครื่องมือย่อยใน `advanced_tools` ให้ดึงข้อมูลจาก `indicator_store` (SSOT Alignment):**
   - แก้ไข `AdvancedToolsManager` ให้ส่ง `basic_payload` ไปยังเครื่องมือย่อย เช่น `conflict_analyzer`, `divergence_analyzer`, `continuation_analyzer`, `persistence_analyzer` เพื่อหยุดการคำนวณ EMA, RSI, MACD, Slope ซ้ำซ้อนจาก DataFrame
3. **กำจัด Fallback / Mock Values & Generic Except:**
   - แก้ไขจุดคืนค่าเดา เช่น `box_duration=10`, `atr_percentile=50.0` ใน `structural_metrics.py` และเปลี่ยน `except Exception: return 50` ใน `market_state_classifier.py` ให้เป็น Fail-Fast ตามกฎข้อ 1 และ 7
