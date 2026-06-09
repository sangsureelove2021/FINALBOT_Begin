# ?? FINALBOT MASTER BLUEPRINT: THE DEFINITIVE ARCHITECTURE MANUAL

> [!IMPORTANT]
> This is the unabridged, comprehensive technical specification for FINALBOT. It contains 100% of the mathematical scoring formulas, Intelligence OS definitions, Pipeline orchestration rules, and exhaustive details of all 14 execution strategies.

## 1. ?? Core Architecture

### Intelligence OS & Pipeline OS
The Intelligence OS continuously analyzes multi-dimensional market data (Volatility, Trend, Momentum, Structure, Multi-Timeframe) to classify real-time Market States. The Pipeline OS dictates the sequential orchestration from data ingestion to signal generation.

### Market States ??
- **Suitable States:** BREAKOUT_EMERGING, ACCUMULATION, SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION
- **Blocked States:** TRENDING_STRONG, TRENDING_WEAK, LIQUIDITY_VOID, CHOPPY_UNCERTAIN, TRANSITIONAL, UNCLEAR

---

## 2. ?? The Universal Scoring System

### ?? Entry Score (0-100)
- **Base Score:** 50 points.
- **Bonus Factors:**
  - F_trend = Min(20, trend_strength / 5)
  - F_expansion = Min(15, expansion_probability / 7)
  - F_mtf = Min(10, alignment_score / 10)
  - *Further quality bonuses apply based on strategy specifics.*

### ?? Block Score (0-100)
- **Soft Blocks:** Trap (+30), Noise (+20), Exhaustion (+15), Reversal (+15), Fatigue (+20).
- **Hard Blocks:** Market State Blocked, Extreme Volatility, High Impact News, Anomaly, Feed Freeze -> Block Score = 100.
- **Confidence Formula:** Confidence = Entry_Score * (1 - Block_Score / 200)

---

## 3. ?? Exhaustive Strategy Specifications (14 Strategies)

### ?? STRATEGY: Breakout Group COMPRESSION BREAKOUT

# FINAL SPECIFICATION: COMPRESSION BREAKOUT (compression_breakout)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

******************************************************************************--
#### 1. STRATEGY OVERVIEW
******************************************************************************--
ชื่อกลยุทธ์:
  Compression Breakout
  (5M Volatility Compression Breakout Strategy)

วัตถุประสงค์:
  ตรวจจับสภาวะราคาบีบอัดตัวเป็นกรอบสะสมพลังงาน (Volatility Compression) บนแท่งเทียน M5
  และประเมินคุณภาพแรงระเบิดทะลุกรอบ (Breakout) เพื่อเข้าซื้อขายตามทิศทางที่มีแนวโน้มดำเนินต่อเชิงโมเมนตัม
  กลยุทธ์จะประเมินสัญญาณ ณ วินาทีเปิดของแท่ง M5 ถัดไปทันทีหลังจากจุดทะลุกรอบได้รับการยืนยัน
  โดยกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — มีสิทธิ์สร้างสัญญาณหลักด้วยตัวเองโดยไม่ต้องรอสัญญาณจากส่วนงานอื่น
  เนื่องจากใช้พฤทีกรรมความผันผวนร่วมกับโมเมนตัมโครงสร้างราคา

ประเภทสัญญาณ:
  Breakout / Momentum Continuation — ตามแนวโน้มหลังจากการระเบิดทะลุกรอบความผันผวน

Market States ที่เหมาะสม:
  BREAKOUT_EMERGING — ราคาทะลุกรอบและเริ่มเคลื่อนไหวอย่างมีทิศทางชัดเจน    [★★★★★]
  ACCUMULATION      — ช่วงราคารวบรวมพลังงานและบีบอัดตัวต่ำสุดขีด           [★★★★☆]

Market States ที่ห้ามใช้เด็ดขาด:
  TRENDING_STRONG   — เทรนด์เคลื่อนที่ไปไกลและกระจายความผันผวนไปหมดแล้ว โอกาสติดจุดสิ้นสุดสูง
  SIDEWAY_RANGE    — ราคาแกว่งตัวกว้าง ไม่มีระดับความบีบอัดตัวที่เพียงพอ
  REVERSAL_FORMING — สภาวะตลาดกำลังเกิดการปฏิเสธทิศทางเดิม สวนทางกับกลยุทธ์เบรกเอาต์
  TRENDING_WEAK     — เทรนด์เริ่มหมดแรงขับเคลื่อนและมีความเสี่ยงเปลี่ยนทิศทางสูง
  LIQUIDITY_VOID    — ตลาดขาดสภาพคล่องและทิศทางมีความผันผวนจาก Noise สูง
  CHOPPY_UNCERTAIN  — ราคาขึ้นลงอย่างไร้ทิศทางในระยะสั้นมาก
  DISTRIBUTION     — ราคาแกว่งตัวผันผวนที่ขอบเขตด้านบนเพื่อระบายสัญญา
  TRANSITIONAL     — ช่วงกำลังเปลี่ยนสถานะตลาด ซึ่งสัญญาณเบรกเอาต์มักจะเป็นสัญญาณหลอก (Fakeout)
  UNCLEAR          — ข้อมูลดิบขัดแย้งเชิงโครงสร้าง ห้ามยิงสัญญาณ

******************************************************************************--
#### 2. REQUIRED INPUTS
******************************************************************************--
1. M5 OHLCV Candles (ย้อนหลัง 100 แท่ง)
   เหตุผล: ตรวจจับทิศทางแนวโน้ม ดึงค่าตัวแปร และใช้วิเคราะห์ขนาดแท่งเทียน

2. ATR(14) บน M5
   เหตุผล: ใช้ normalize ความกว้างกรอบราคาและระยะการตัดความผันผวน

3. ATR Percentile (จาก Volatility Intelligence)
   เหตุผล: ระบุระดับการบีบอัดของความผันผวนเทียบกับข้อมูลย้อนหลัง

4. Volatility Expansion Probability และ Spike Detection
   เหตุผล: ระบุความน่าจะเป็นในการเกิดขยายตัวของความผันผวนและระดับแรงสไปก์

5. Trend Direction & Trend Strength (จาก Trend Intelligence)
   เหตุผล: ยืนยันแนวโน้มฝั่งทิศทาง และใช้เป็นค่า fallback ร่วมกับ BOS

6. Structure Info (Swing Points, box_duration, bos_type)
   เหตุผล: วิเคราะห์ระยะเวลากล่องและรูปแบบการหักล้างโครงสร้างราคาก่อนเบรกเอาต์

7. Multi-Timeframe (MTF) Alignment Score & HTF Direction
   เหตุผล: การหลีกเลี่ยงการเทรดที่ขัดแย้งกับทิศทางหลักของกรอบเวลาที่ใหญ่กว่า (HTF)

8. Real-Time Tick Feed
   เหตุผล: ตรวจจับสภาวะการหยุดนิ่งของ feed ข้อมูลโบรกเกอร์ (Broker Feed Validity)

9. High Impact News Calendar
   เหตุผล: สกัดกั้นการเข้าเทรดในช่วงเวลาที่มีข่าวสารที่มีผลกระทบรุนแรง ±15 นาที

******************************************************************************--
#### 3. ENTRY CONDITIONS
******************************************************************************--
ลำดับขั้นการประเมิน — ต้องผ่านทุกขั้นตามลำดับ หากขั้นใดล้มเหลวให้หยุดทันที

CONDITION 1 — Market State Eligibility
  ตรวจว่า Market State ปัจจุบันอยู่ใน Suitable States หรือไม่
  ผ่าน: BREAKOUT_EMERGING, ACCUMULATION
  ไม่ผ่าน: หยุดทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — Volatility Compression Check
  ตรวจว่าความผันผวนตลาดอดีตมีการบีบอัดตัวที่หนาแน่นพอหรือไม่
  เกณฑ์: atr_percentile <= 30
  ไม่ผ่าน: หยุดทันที → fail_reason_code: ATR_NOT_COMPRESSED

CONDITION 3 — Volatility Expansion Check
  ตรวจจับสภาวะการปะทุและขยายตัวของระดับความผันผวนในปัจจุบัน
  เกณฑ์: expansion_probability >= 60 OR spike_detected == True
  ไม่ผ่าน: หยุดทันที → fail_reason_code: NO_EXPANSION_DETECTED

CONDITION 4 — Direction / Breakout Confirmation Check
  ยืนยันว่าทิศทางการวิ่งทะลุมีความชัดเจน
  สำหรับ CALL (เบรกเอาต์ขาขึ้น):
    4a. trend_direction == 'UP'
    4b. trend_strength >= 50
    * กรณี trend_direction == 'NONE' หรือ trend_strength < 50 (Squeeze Breakout Fallback):
      - ตรวจจับโครงสร้างการเบรกเอาต์: bos_type == 'BULLISH'
      - กำหนดให้ trend_direction = 'UP' และจัดสรรความแรงชั่วคราว: trend_strength = Max(trend_strength, 60)
  สำหรับ PUT (เบรกเอาต์ขาลง):
    4a. trend_direction == 'DOWN'
    4b. trend_strength >= 50
    * กรณี trend_direction == 'NONE' หรือ trend_strength < 50 (Squeeze Breakout Fallback):
      - ตรวจจับโครงสร้างการเบรกเอาต์: bos_type == 'BEARISH'
      - กำหนดให้ trend_direction = 'DOWN' และจัดสรรความแรงชั่วคราว: trend_strength = Max(trend_strength, 60)
  ไม่ผ่านข้อกำหนดทิศทางหลัก → fail_reason_code: NO_CLEAR_DIRECTION

CONDITION 5 — MTF Alignment Quality Check
  ตรวจสอบความสอดคล้องกันระหว่างกรอบเวลาหลักและกรอบเวลาที่ใหญ่กว่า (HTF)
  เกณฑ์: alignment_score >= 70 AND htf_ltf_conflict == False
  ไม่ผ่าน → fail_reason_code: MTF_ALIGNMENT_FAILED

CONDITION 6 — Broker Feed Validity
  ตรวจสอบว่าการรับส่งข้อมูลของ Feed ไม่ค้างนานเกิน 10 วินาที
  ไม่ผ่าน → fail_reason_code: BROKER_FEED_FREEZE

******************************************************************************--
#### 4. ENTRY SCORE LOGIC
******************************************************************************--
Entry Score (สเกล 0–100) คำนวณจากคะแนนฐานร่วมกับ 7 ปัจจัยถ่วงน้ำหนัก ดังนี้:

คะแนนตั้งต้น (Base Score) = 50 คะแนน

ปัจจัยบวก (Entry Factor additions):
  1. Trend Strength (F_trend)
     สูตร: F_trend = Min(20, trend_strength / 5)             (เพิ่มได้สูงสุด +20)
  2. Expansion Probability (F_expansion)
     สูตร: F_expansion = Min(15, expansion_probability / 7)    (เพิ่มได้สูงสุด +15)
  3. MTF Alignment Score (F_mtf)
     สูตร: F_mtf = Min(10, alignment_score / 10)             (เพิ่มได้สูงสุด +10)
  4. Momentum Level (F_momentum)
     สูตร: F_momentum = 5 (ถ้า momentum_level เป็น 'STRONG' หรือ 'NORMAL') มิฉะนั้น = 0
  5. Box Duration Enhancement (F_duration)
     สูตร: F_duration = Min(15, (box_duration - 15) * 0.8)   (เพิ่มได้สูงสุด +15 เฉพาะเมื่อ box_duration > 15)
  6. Compression Quality (F_quality)
     สูตร: F_quality = 10 (ถ้า compression_quality > 75)      มิฉะนั้น = 0
  7. Breakout Retest Analyzer (F_retest)
     สูตร: F_retest = 15 (ถ้า retest_detected == True และ retest_quality > 70) มิฉะนั้น = 0

สูตรรวมคะแนนดิบ (Raw Entry Score):
  Raw Entry Score = Base Score + F_trend + F_expansion + F_mtf + F_momentum + F_duration + F_quality + F_retest

สูตรคะแนนสุดท้ายก่อนปรับความเสี่ยง (Final Entry Score):
  Final Entry Score = Min(100, Raw Entry Score)

การปรับลดน้ำหนักคะแนนตามสถานะช่วงอายุตลาด (State Lifecycle):
  - Fresh / Active: คงคะแนน Final Entry Score ไว้ที่ 100% ของค่าที่คำนวณได้
  - Late: หักคะแนนลงเหลือ 80% (Final Entry Score = Final Entry Score * 0.80)
  - Exhausted: ตั้งค่า Block Score = 100 ทันที (ระงับสัญญาณถาวร)

******************************************************************************--
#### 5. BLOCK SCORE LOGIC
******************************************************************************--
Block Score เริ่มต้นที่ 0 คะแนน และจะสะสมจาก Soft Block และ Hard Block ดังต่อไปนี้:

*** SOFT BLOCK FACTORS (สะสมคะแนนเพิ่มความเสี่ยงสูงสุด 100 คะแนน) ***
  SF-1: ตลาดมีสัญญาณกับดักราคา (Trap Detected)
        → +30 คะแนน
        เหตุผล: ราคาทำสัญญาณลวงให้รู้สึกเหมือนหลุดพ้นจากกรอบแล้วสะท้อนกลับทันที
  SF-2: ระดับเสียงรบกวนตลาดในกรอบปัจจุบัน (Noise Level) > 60
        → +20 คะแนน
        เหตุผล: การเบรกเอาต์อาจเป็นเพียงการแกว่งตัวผันผวนอย่างไร้ทิศทาง
  SF-3: ความเสี่ยงจากการหมดกำลังของแท่งสัญญาณ (Exhaustion Risk) > 60
        → +15 คะแนน
        เหตุผล: โมเมนตัมเบรกเอาต์อาจถึงจุดสิ้นสุดของแรงส่ง
  SF-4: ความเสี่ยงการเปลี่ยนแนวโน้มกลับทิศทาง (Reversal Risk) > 60
        → +15 คะแนน
        เหตุผล: แนวโน้มใหญ่มีแนวโน้มเปลี่ยนทางสวนกับทางที่หลุดกรอบออกไป
  SF-5: ความเสี่ยงความล้าในการขยายโมเมนตัมสะสม (Fatigue Risk) > 60
        → +20 คะแนน
        เหตุผล: แรงโมเมนตัมกำลังเกิดสภาวะบั่นทอนหลังจากปะทุ

*** HARD BLOCK FACTORS (เมื่อเงื่อนไขตรง จะปรับ Block Score = 100 ทันทีและปฏิเสธคำสั่งซื้อ) ***
  HB-1: สภาวะตลาด (Market State) เป็นกลุ่มที่ถูกแบล็กลิสต์:
        TRENDING_STRONG, SIDEWAY_RANGE, REVERSAL_FORMING, TRENDING_WEAK, LIQUIDITY_VOID, CHOPPY_UNCERTAIN, DISTRIBUTION, TRANSITIONAL, UNCLEAR
        → Block Score = 100
  HB-2: ตรวจพบความผิดปกติของโครงสร้างราคารุนแรง (Anomaly Detected)
        → Block Score = 100
  HB-3: โครงสร้างความผันผวนอยู่ในระดับรุนแรงสุดขีด (Volatility Regime == 'EXTREME')
        → Block Score = 100
  HB-4: ระดับ Noise ของตลาดอยู่ในเกณฑ์สูงมาก (Noise Level > 65)
        → Block Score = 100
  HB-5: ความเสี่ยงการเหนื่อยล้าของโมเมนตัมสูงมาก (Exhaustion Risk > 70)
        → Block Score = 100
  HB-6: อยู่ในช่วงเวลาประกาศข่าวเศรษฐกิจที่รุนแรง (High Impact News) ±15 นาที
        → Block Score = 100
  HB-7: อายุการทำงานของตลาดหมดสิ้นแล้ว (State Lifecycle == Exhausted)
        → Block Score = 100

*** สูตรคำนวณ Block Score ท้ายสุด ***
  IF มีการตรวจพบเงื่อนไข Hard Block ข้อใดข้อหนึ่ง → Block Score = 100
  ELSE → Block Score = Sum(Soft Block คะแนนที่ติดทั้งหมด) โดยมีค่าสูงสุดจำกัดที่ 100 คะแนน

******************************************************************************--
#### 6. STRATEGY CONFIDENCE
******************************************************************************--
C_strategy คำนวณแบบค่าต่อเนื่องอยู่ในช่วงสเกล [0.0 - 1.0]:

  C_strategy = (0.40 × S_vol) + (0.30 × S_str) + (0.30 × S_mtf)

ค่าคะแนนย่อย (Sub-scores):
  1. Volatility Compression/Expansion Score (S_vol)
     สูตร: S_vol = Min(1.0, (100 - atr_percentile) / 70) * (expansion_probability / 100)
     คำอธิบาย: วัดคุณภาพความหนาแน่นของการบีบอัดร่วมกับพลังงานของการแตกกรอบ
  2. Breakout Trend Strength Score (S_str)
     สูตร: S_str = trend_strength / 100
     คำอธิบาย: ความแข็งแรงของเทรนด์หรือโครงสร้างราคาที่เบรกเอาต์
  3. Multi-Timeframe Alignment Score (S_mtf)
     สูตร: S_mtf = alignment_score / 100
     คำอธิบาย: ความสอดคล้องของกรอบเวลากับแนวโน้มหลักของ HTF

ตัวอย่างการประเมินคะแนน:
  ข้อมูลตลาด: atr_percentile = 25, expansion_probability = 80, trend_strength = 70, alignment_score = 90
  S_vol = Min(1.0, (100 - 25) / 70) * (80 / 100) = Min(1.0, 1.07) * 0.80 = 1.0 * 0.80 = 0.80
  S_str = 70 / 100 = 0.70
  S_mtf = 90 / 100 = 0.90
  C_strategy = (0.40 × 0.80) + (0.30 × 0.70) + (0.30 × 0.90) = 0.32 + 0.21 + 0.27 = 0.80 (คุณภาพสัญญาณดีเลิศ)

******************************************************************************--
#### 7. FAIL CONDITIONS
******************************************************************************--
กลยุทธ์จะเปลี่ยนสถานะการประเมินเป็น NO_SETUP ทันที และส่งคืน รหัสล้มเหลว (fail_reason_code) ดังนี้:

  MARKET_STATE_BLOCKED   : สภาวะตลาดปัจจุบันไม่เข้าเกณฑ์ที่เหมาะสม (Condition 1)
  ATR_NOT_COMPRESSED     : ตลาดไม่อยู่ในระดับการบีบอัดตัวทางโครงสร้างราคาที่เพียงพอ (Condition 2)
  NO_EXPANSION_DETECTED  : ความน่าจะเป็นในการระเบิดความผันผวนน้อยกว่าเกณฑ์ที่ยอมรับได้ (Condition 3)
  NO_CLEAR_DIRECTION     : ข้อมูลแนวโน้มขาดความชัดเจนเชิงทิศทางและไม่มีการยืนยัน BOS (Condition 4)
  MTF_ALIGNMENT_FAILED   : ความสอดคล้องข้ามกรอบเวลาน้อยกว่าเป้าหมายหรือขัดแย้งกับ HTF (Condition 5)
  BROKER_FEED_FREEZE     : ข้อมูลราคาระบบฟีดของโบรกเกอร์ค้างเกินกว่าเกณฑ์ 10 วินาที (Condition 6)
  NEWS_BLACKOUT          : การทำงานหลีกเลี่ยงข่าวรุนแรงระดับสูงในช่วงเวลาเป้าหมาย ±15 นาที
  ANOMALY_DETECTED       : โครงสร้างราคาปัจจุบันมีความสับสนทางเทคนิค
  EXTREME_VOLATILITY     : ความผันผวนอยู่ในระดับสูงสุดของเกณฑ์ความกลัว
  EXHAUSTION_RISK_HIGH   : สภาพตลาดมีความเสี่ยงจะหยุดยั้งและเข้าสู่ช่วงหมดกำลัง
  NOISE_LEVEL_HIGH       : คลื่นรบกวนตลาดสูงเกินกว่าเป้าหมายความแม่นยำ

******************************************************************************--
#### 8. EXPECTED BEHAVIOR
******************************************************************************--
High Quality Breakout (สัญญาณระดับคุณภาพสูง):
  เกิดขึ้นเมื่อกรอบระยะเวลาบีบอัดตัวแคบสะสมพลังงานยาวนาน (box_duration > 20 แท่ง)
  การระเบิดความผันผวนเกิดขึ้นฉับพลันด้วยเนื้อแท่งเทียนที่เต็มและแข็งแรง ทิศทางสอดคล้องกับ MTF 100%
  คะแนนความเชื่อมั่นรวม C_strategy > 0.80 และ Entry Score > 80 คะแนน
  ความคาดหวัง: ราคาจะเคลื่อนไหวผลักดันไปในทิศทางของสัญญาณต่อเนื่องอย่างมีเสถียรภาพจนจบแท่ง M5 ถัดไป

Weak Breakout (สัญญาณระดับคุณภาพระดับปานกลาง):
  ตลาดสะสมแรงกดบีบอัดในช่วงเวลาสั้น (box_duration อยู่ระหว่าง 10 ถึง 15 แท่ง)
  การเบรกเอาต์มีเนื้อแท่งเทียนสั้นและมีไส้บน/ล่างยาวแทรกซึมขึ้นมา
  คะแนนความเชื่อมั่นรวม C_strategy อยู่ในช่วง 0.60–0.79 และ Entry Score อยู่ในช่วง 75-79 คะแนน
  ความคาดหวัง: ราคามีแนวโน้มที่จะทำการย่อตัวหรือสะสมพลังงานทดสอบแนว (Retest) ก่อนที่จะสามารถยืนยันจุดเบรกเอาต์

False Breakout (การหลุดเอาต์ลวง):
  ราคาเบรกเอาต์หลุดนอกกรอบความผันผวนแต่ดีดตัวกลับเข้าสู่กล่องสะสมอย่างรวดเร็ว (เกิดกับดักราคา Trap)
  ระบบจะสามารถดักกรองความเสี่ยงนี้ได้จากดัชนีคะแนนความเสี่ยง Soft Block ที่จะพุ่งสูงขึ้น
  หรือการบล็อกทันทีจากระบบความไม่มั่นคงเชิงข้อมูลผ่าน Hard Block
  ทำให้ไม่เกิดการส่งคำสั่งผิดพลาด และหลีกเลี่ยงการขาดทุนได้อย่างสมบูรณ์

******************************************************************************--
#### 9. AUDIT REQUIREMENTS
******************************************************************************--
บันทึกข้อมูลและส่งค่าต่อไปนี้บันทึกลงสู่ระบบจัดเก็บฐานข้อมูล WORM ทุกรอบการทดสอบสัญญาณ:

  - audit_id             : รหัสยืนยันตัวตน UUIDv4 ประจำรอบการประเมิน
  - timestamp            : เวลาที่ระบบบันทึกคำสั่งสัญญาณ (UTC)
  - symbol               : สัญลักษณ์ของคู่เงินเป้าหมาย
  - market_state         : สถานะตลาดที่ประเมินร่วมกับช่วงอายุข้อมูลหลัก
  - candle_ohlcv         : ข้อมูล OHLCV บนกรอบระยะเวลา M5[-1]
  - atr_m5               : ค่าความผันผวนเฉลี่ย ATR_M5 ปัจจุบัน
  - atr_percentile       : ระดับเปอร์เซ็นไทล์ของ ATR ปัจจุบัน
  - expansion_probability : โอกาสความน่าจะเป็นที่จะเกิดการขยายตัวความผันผวน
  - alignment_score      : คะแนนเป้าหมายความสอดคล้องกันของเฟรมเวลา MTF
  - trend_strength       : ความมั่นคงแข็งแกร่งของทิศทางแนวโน้มราคา
  - box_duration         : ระยะจำนวนแท่งเทียนสะสมที่ทำงานอยู่ในกรอบบีบอัด
  - compression_quality  : ระดับคะแนนคุณภาพของการบีบอัดทางทัศนศาสตร์ราคา
  - retest_detected      : การพบเจอพฤติกรรมการทดสอบย้ำระดับราคา (Retest)
  - retest_quality       : ดัชนีคุณภาพความแข็งแกร่งของพฤติกรรมการ Retest
  - entry_score_raw      : คะแนนการเข้าเทรดระดับแรกเริ่มก่อนปรับสภาพตลาด
  - entry_score          : คะแนนสุดท้ายที่สรุปประเมินความเสี่ยงแล้ว
  - block_score          : คะแนนการขัดขวางและดักกรองสัญญาณไม่พึงประสงค์
  - c_strategy           : ระดับความมั่นใจทางคณิตศาสตร์ความสัมพันธ์ของกลยุทธ์
  - eligible             : การผ่านเกณฑ์ความเหมาะสมหลักของระบบ (true/false)
  - action               : ประเภทการออกสัญญาณซื้อขาย (CALL / PUT / NO_SETUP)
  - fail_reason_code     : รหัสชี้บ่งรายละเอียดขัดข้องของการประเมินสัญญาณ

******************************************************************************--
#### 10. OUTPUT CONTRACT (FROZEN SCHEMA)
******************************************************************************--
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_CompressionBreakout_R1",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "compression_breakout" },
    "eligible":            { "type": "BOOLEAN" },
    "action":              { "type": "STRING", "enum": ["CALL", "PUT", "NO_SETUP"] },
    "entry_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "block_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "strategy_confidence": { "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "direction_confidence":{ "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "expected_state":      { "type": "STRING",
                             "enum": ["BREAKOUT_EMERGING","ACCUMULATION",
                                      "TRENDING_STRONG","TRENDING_WEAK","UNCLEAR"] },
    "fail_reason_code":    { "type": "STRING" },
    "audit_id":            { "type": "STRING",
                             "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[4][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$" },
    "expiry":              { "type": "STRING", "const": "M5" },
    "details": {
      "type": "OBJECT",
      "properties": {
        "atr_percentile":        { "type": "NUMBER" },
        "expansion_probability": { "type": "NUMBER" },
        "mtf_alignment":         { "type": "NUMBER" },
        "trend_strength":        { "type": "NUMBER" },
        "compression_quality":   { "type": "NUMBER" }
      },
      "required": ["atr_percentile", "expansion_probability", "mtf_alignment", "trend_strength", "compression_quality"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}

---

### ?? STRATEGY: Reversal Group A PA SNR STRATEGY

# FINAL SPECIFICATION: PA SNR STRATEGY (pa_snr)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

******************************************************************************--
#### 1. STRATEGY OVERVIEW
******************************************************************************--
ชื่อกลยุทธ์:
  PA SNR Strategy
  (Price Action and Dynamic Support & Resistance Reversal Strategy)

วัตถุประสงค์:
  ตรวจจับรูปแบบแท่งเทียนกลับตัว (Price Action Candle Patterns) ณ บริเวณแนวรับและแนวต้านพลวัต (Dynamic S&R Levels) 
  ที่สร้างขึ้นจาก Swing Points ในอดีตบนกรอบเวลา M5 กลยุทธ์นี้มุ่งเน้นการจับสัญญาณกลับตัวแบบ Mean Reversion 
  ณ จุดสิ้นสุดของรอบราคาเพื่อเปิดสถานะออปชันประเภท M5 Expiry ทันทีเมื่อเปิดแท่งเทียนใหม่

บทบาทในระบบ:
  Leading Strategy — สามารถส่งสัญญาณการเทรดได้ด้วยตัวเองเมื่อผ่านเงื่อนไขโครงสร้างราคาและ S&R โดยไม่ต้องรออินดิเคเตอร์ตัวอื่นยืนยัน

ประเภทสัญญาณ:
  Reversal — กลับตัวระยะสั้นภายใน 1-3 แท่ง M5 (5-15 นาที)

Market States ที่เหมาะสม:
  SIDEWAY_RANGE    — ตลาดวิ่งในกรอบแนวรับ/แนวต้านชัดเจน            [★★★★★]
  REVERSAL_FORMING — ตลาดกำลังแสดงสัญญาณสร้างจุดกลับตัว            [★★★★★]
  DISTRIBUTION     — ตลาดอยู่ในโซนกระจายของสะสม พร้อมกลับตัวลง    [★★★★★]
  TRANSITIONAL     — สภาวะคาบเกี่ยว ใช้ได้แต่ลดน้ำหนัก Entry Score 30% [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  TRENDING_STRONG   — สภาวะแนวโน้มแข็งแกร่ง การสวนพฤติกรรมราคาเสี่ยงสูง
  BREAKOUT_EMERGING — ตลาดกำลังเบรคทะลุแนวระดับสำคัญ
  ACCUMULATION      — ตลาดบีบตัวรอการเลือกทาง
  TRENDING_WEAK     — สภาวะแนวโน้มอ่อนแรงแต่ยังมีทิศทางชัดเจน
  LIQUIDITY_VOID    — ตลาดขาดสภาพคล่องและปริมาณซื้อขายหนาแน่น
  CHOPPY_UNCERTAIN  — ตลาดผันผวนไร้ทิศทางและมีสัญญาณหลอกสูง
  UNCLEAR           — ข้อมูลตลาดไม่ชัดเจนหรือไม่ครบถ้วน

******************************************************************************--
#### 2. REQUIRED INPUTS
******************************************************************************--
1. M5 OHLCV Candles (ย้อนหลังอย่างน้อย 35 แท่ง เพื่อใช้ประมวลผล Swing Points ย้อนหลัง 30 แท่ง + Window 3 แท่ง)
   เหตุผล: ตรวจสอบและหาแนว Swing High / Swing Low และยืนยันรูปแบบแท่งเทียนย้อนหลัง 3 แท่ง

2. Dynamic Support & Resistance Levels ( Swing Highs / Swing Lows )
   เหตุผล: ใช้คำนวณตำแหน่งแนวรับและแนวต้านพลวัต

3. Candle Structure Metrics (คำนวณบนแท่ง M5[-1], M5[-2], M5[-3])
   - Body Size = |Close - Open|
   - Upper Wick = High - Max(Open, Close)
   - Lower Wick = Min(Open, Close) - Low
   - Candle Height (Total Range) = High - Low
   เหตุผล: ตรวจจับสัดส่วนพฤติกรรมราคาเชิงโครงสร้างแท่งเทียน (Candle Geometry)

4. Real-Time Tick Feed (ปัจจุบัน)
   เหตุผล: ยืนยันความเสถียรของราคาป้อนเข้า (Broker Feed Check)

5. Market State + State Age (จาก Intelligence OS)
   เหตุผล: ใช้กรองสัญญาณในกลุ่ม Suitable States และควบคุมการปรับคะแนนตามอายุรอบตลาด (State Age)

******************************************************************************--
#### 3. ENTRY CONDITIONS
******************************************************************************--
ลำดับขั้นการประเมิน — ต้องผ่านทุกขั้นตามลำดับ หากขั้นใดล้มเหลวให้หยุดทันที

CONDITION 1 — Market State Eligibility
  ตรวจสอบ Market State ปัจจุบันจาก Intelligence OS
  ผ่าน: SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION, TRANSITIONAL
  ไม่ผ่าน: หยุดการทำงานทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — Dynamic S&R Detection (Swing Points Engine)
  หา Swing Highs (แนวต้าน) และ Swing Lows (แนวรับ) จาก M5 Candles ย้อนหลัง SWING_LOOKBACK = 30 แท่ง
  โดยใช้หน้าต่างตรวจสอบ SWING_WINDOW = 3 แท่ง (ต้องเป็นจุดสูงสุดหรือต่ำสุดสัมพัทธ์ในหน้าต่าง 3 แท่งด้านซ้ายและขวา)
  
  สูตร Swing High (จุดสูงสุดท้องถิ่น):
    High[i] > High[i-j] และ High[i] > High[i+j] สำหรับ j ∈ [1, SWING_WINDOW]
  
  สูตร Swing Low (จุดต่ำสุดท้องถิ่น):
    Low[i] < Low[i-j] และ Low[i] < Low[i+j] สำหรับ j ∈ [1, SWING_WINDOW]

  การจัดกลุ่มโซนระดับราคา (Clustering):
    ระดับราคาที่อยู่ห่างกันน้อยกว่าหรือเท่ากับ 0.03% (SR_CLUSTER_PCT = 0.0003) จะถูกยุบรวมเป็นระดับเดียวโดยใช้ค่าเฉลี่ย:
    |Level_A - Level_B| / Level_B <= 0.0003
    คัดกรองเฉพาะระดับที่มี Swing Point มาจัดกลุ่มตั้งแต่ 1 จุดขึ้นไป (len(c) >= 1)

  เกณฑ์: หากไม่พบแนวรับหรือแนวต้านที่ผ่านการคัดกรองในรอบนี้ → หยุดการทำงานทันที → fail_reason_code: NO_SR_LEVELS_DETECTED

CONDITION 3 — Price Proximity (การทดสอบโซนราคา)
  ราคาปัจจุบัน (Low[-1] สำหรับ CALL หรือ High[-1] สำหรับ PUT) ต้องอยู่ภายในขอบเขต Proximity 0.04% (SR_PROXIMITY_PCT = 0.0004) ของแนวระดับที่ใกล้ที่สุด
  
  สำหรับ CALL (ทดสอบแนวรับ Support_Level):
    |Low[-1] - Support_Level| / Support_Level <= 0.0004
    
  สำหรับ PUT (ทดสอบแนวต้าน Resistance_Level):
    |High[-1] - Resistance_Level| / Resistance_Level <= 0.0004
    
  ไม่ผ่านเกณฑ์ → หยุดการทำงานทันที → fail_reason_code: PRICE_OUTSIDE_SR_PROXIMITY

CONDITION 4 — Price Action Pattern Recognition
  ตรวจจับรูปแบบแท่งเทียนกลับตัว ณ แท่ง M5[-1] และประวัติย้อนหลัง 3 แท่งดังนี้:

  4a. รูปแบบกลับตัวขาขึ้น (BULLISH PATTERNS AT SUPPORT) - สำหรับการเข้าซื้อ CALL:
    - Bullish Pin Bar (Hammer):
      * Lower_Wick[-1] >= Body_Size[-1] * 2.0 (PIN_WICK_RATIO = 2.0)
      * Upper_Wick[-1] <= Body_Size[-1] * 0.5 (PIN_OPP_WICK_RATIO = 0.5)
      * Close[-1] > Open[-1] (เนื้อเทียนปิดสีเขียว)
    - Bullish Engulfing:
      * แท่งก่อนหน้าเป็นสีแดง: Close[-2] < Open[-2]
      * แท่งปัจจุบันเป็นสีเขียว: Close[-1] > Open[-1]
      * ขนาดเนื้อเทียนแท่งปัจจุบันครอบคลุมเนื้อเทียนแท่งก่อนหน้า:
        Open[-1] <= Close[-2] * 1.0002 (ENGULF_TOLERANCE = 1.0002)
        Close[-1] >= Open[-2] / 1.0002
      * สัดส่วนเนื้อเทียนแท่งปัจจุบันเทียบกับความสูงแท่งเทียนรวม: Body_Size[-1] / Height[-1] >= 0.15 (MIN_BODY_PCT = 0.15)
    - Morning Star (รูปแบบ 3 แท่งเทียน):
      * แท่ง M5[-3]: Bearish แข็งแกร่ง (Close[-3] < Open[-3] และ Body_Size[-3] > 0)
      * แท่ง M5[-2]: เนื้อเทียนเล็กแสดงความลังเล (Body_Size[-2] < Body_Size[-3] * 0.5)
      * แท่ง M5[-1]: Bullish แข็งแกร่ง (Close[-1] > Open[-1] และ Body_Size[-1] > Body_Size[-3] * 0.5)
      * ปิดเหนือครึ่งหนึ่งของแท่งที่สามย้อนหลัง: Close[-1] > (Open[-3] + Close[-3]) / 2
    - Three White Soldiers (ทหารสีขาวสามนาย):
      * สีเขียว 3 แท่งติดต่อกัน: Close[-3] > Open[-3] และ Close[-2] > Open[-2] และ Close[-1] > Open[-1]
      * ราคาปิดยกสูงขึ้นเรื่อยๆ: Close[-1] > Close[-2] > Close[-3]

  4b. รูปแบบกลับตัวขาลง (BEARISH PATTERNS AT RESISTANCE) - สำหรับการเข้าซื้อ PUT:
    - Bearish Pin Bar (Shooting Star):
      * Upper_Wick[-1] >= Body_Size[-1] * 2.0 (PIN_WICK_RATIO = 2.0)
      * Lower_Wick[-1] <= Body_Size[-1] * 0.5 (PIN_OPP_WICK_RATIO = 0.5)
      * Close[-1] < Open[-1] (เนื้อเทียนปิดสีแดง)
    - Bearish Engulfing:
      * แท่งก่อนหน้าเป็นสีเขียว: Close[-2] > Open[-2]
      * แท่งปัจจุบันเป็นสีแดง: Close[-1] < Open[-1]
      * ขนาดเนื้อเทียนแท่งปัจจุบันครอบคลุมเนื้อเทียนแท่งก่อนหน้า:
        Open[-1] >= Close[-2] / 1.0002 (ENGULF_TOLERANCE = 1.0002)
        Close[-1] <= Open[-2] * 1.0002
      * สัดส่วนเนื้อเทียนแท่งปัจจุบันเทียบกับความสูงแท่งเทียนรวม: Body_Size[-1] / Height[-1] >= 0.15 (MIN_BODY_PCT = 0.15)
    - Evening Star (รูปแบบ 3 แท่งเทียน):
      * แท่ง M5[-3]: Bullish แข็งแกร่ง (Close[-3] > Open[-3] และ Body_Size[-3] > 0)
      * แท่ง M5[-2]: เนื้อเทียนเล็กแสดงความลังเล (Body_Size[-2] < Body_Size[-3] * 0.5)
      * แท่ง M5[-1]: Bearish แข็งแกร่ง (Close[-1] < Open[-1] และ Body_Size[-1] > Body_Size[-3] * 0.5)
      * ปิดต่ำกว่าครึ่งหนึ่งของแท่งที่สามย้อนหลัง: Close[-1] < (Open[-3] + Close[-3]) / 2
    - Three Black Crows (อีกาสามตัว):
      * สีแดง 3 แท่งติดต่อกัน: Close[-3] < Open[-3] และ Close[-2] < Open[-2] และ Close[-1] < Open[-1]
      * ราคาปิดลดต่ำลงเรื่อยๆ: Close[-1] < Close[-2] < Close[-3]

  ไม่พบรูปแบบการกลับตัวใดๆ หรือรูปทรงแท่งเทียนไม่สมบูรณ์ตามเกณฑ์ → หยุดการทำงานทันที → fail_reason_code: NO_PA_PATTERN_DETECTED

CONDITION 5 — Broker Feed Validity
  ตรวจสอบข้อมูล Tick Feed ไม่หยุดค้างเกิน 10 วินาที
  ไม่ผ่านเกณฑ์ → หยุดการทำงานทันที → fail_reason_code: BROKER_FEED_FREEZE

******************************************************************************--
#### 4. ENTRY SCORE LOGIC
******************************************************************************--
ในเวอร์ชันพิมพ์เขียวพื้นฐาน (Baseline Specs) คะแนนการเทรดจะกำหนดเป็นคะแนนแบบไม่ต่อเนื่อง (Discrete Score) ตามระดับความน่าเชื่อถือของรูปแบบราคาที่ตรวจจับได้ (Pattern Confidence):

  - Morning Star / Evening Star            → Raw Score = 92
  - Bullish Engulfing / Bearish Engulfing   → Raw Score = 90
  - Bullish Pin Bar / Bearish Pin Bar       → Raw Score = 88
  - Three White Soldiers / Three Black Crows → Raw Score = 85
  - ไม่พบรูปแบบการกลับตัวที่ระบุ           → Raw Score = 0

การปรับคะแนนตามช่วงเวลาและสภาวะตลาด (State & Lifecycle Adjustments):
  - Fresh / Active State Lifecycle → Entry Score = Raw Score
  - Late State Lifecycle           → Entry Score = Raw Score * 0.80
  - Exhausted State Lifecycle      → Entry Score = 0 (และบล็อกการเข้าเทรด)
  - TRANSITIONAL Market State      → Entry Score = Entry Score * 0.70

******************************************************************************--
#### 5. BLOCK SCORE LOGIC
******************************************************************************--
Block Score ของกลยุทธ์ถูกออกแบบไว้ที่ 0 สำหรับทุกกรณีหากผ่านเงื่อนไขบังคับเชิงลบ (Hard Block) ขั้นพื้นฐานเรียบร้อยแล้ว:

*** SOFT BLOCK FACTORS ***
  * ไม่มีตัวแปร Soft Block คะแนนสะสมในเวอร์ชันนี้ (Block Score = 0 เสมอหากผ่าน Hard Block)

*** HARD BLOCK FACTORS ***
  * HB-1: Market State อยู่ในกลุ่มบล็อก (TRENDING_STRONG, BREAKOUT_EMERGING, ACCUMULATION, TRENDING_WEAK, LIQUIDITY_VOID, CHOPPY_UNCERTAIN, UNCLEAR)
          → Block Score = 100
  * HB-2: ความยาวแท่งเทียนล่าสุดเป็นศูนย์ (Candle Height = 0)
          → Block Score = 100
  * HB-3: สถานะรอบตลาด (State Lifecycle) อยู่ในระดับ Exhausted
          → Block Score = 100

*** สูตรคำนวณ Block Score สุดท้าย ***
  IF เกิดเงื่อนไข Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = 0

******************************************************************************--
#### 6. STRATEGY CONFIDENCE
******************************************************************************--
ความมั่นใจเชิงกลยุทธ์ (C_strategy) มีค่าระหว่าง 0.0 ถึง 1.0 คำนวณจากการแปลงสเกลคะแนนความน่าเชื่อถือของรูปแบบเชิงทฤษฎี:

  C_strategy = Raw Score / 100.0

ตัวอย่างการคำนวณ:
  - หากระบบตรวจพบรูปแบบ Morning Star ณ แนวรับ:
    Raw Score = 92
    C_strategy = 92 / 100.0 = 0.92
    
  - หากระบบตรวจพบรูปแบบ Three White Soldiers ณ แนวรับ:
    Raw Score = 85
    C_strategy = 85 / 100.0 = 0.85

******************************************************************************--
#### 7. FAIL CONDITIONS
******************************************************************************--
กลยุทธ์จะคืนค่า NO_SETUP ทันทีพร้อมตั้งค่ารหัสล้มเหลว (fail_reason_code) เมื่อพบสถานการณ์ดังต่อไปนี้:

  - MARKET_STATE_BLOCKED      : Market State ไม่ได้อยู่ในเกณฑ์ Suitable States
  - NO_SR_LEVELS_DETECTED     : ไม่พบแนวต้านหรือแนวรับที่ผ่านเกณฑ์การทำ Swing Point ย้อนหลัง 30 แท่ง
  - PRICE_OUTSIDE_SR_PROXIMITY: จุดสูงสุด/ต่ำสุดของแท่งล่าสุด ไม่อยู่ในระยะ Proximity 0.04% ของแนวระดับ
  - NO_PA_PATTERN_DETECTED    : โครงสร้างแท่งเทียนไม่สอดคล้องกับพฤติกรรมราคากลับตัวใดๆ ที่สนับสนุน
  - BROKER_FEED_FREEZE        : การป้อนข้อมูล Tick ค้างเกิน 10 วินาที
  - INSUFFICIENT_DATA         : ข้อมูลแท่งเทียนต่ำกว่าความต้องการขั้นต่ำ (35 แท่ง)
  - ZERO_HEIGHT_CANDLE        : ความยาวแท่งเทียน High - Low มีค่าเท่ากับ 0

******************************************************************************--
#### 8. EXPECTED BEHAVIOR
******************************************************************************--
High-Quality Signal (สัญญาณกลับตัวความเชื่อมั่นสูง):
  เกิดรูปแบบ Morning/Evening Star หรือ Engulfing ณ แนวต้าน/แนวรับหลักที่ผ่านการทดสอบมาอย่างน้อย 3 รอบขึ้นไป
  คะแนนความมั่นใจ C_strategy >= 0.90 และมีค่าระดับสเปรดปกติ
  คาดหวัง: เกิดการดีดกลับของราคาเพื่อเปลี่ยนทิศทางในระยะสั้นอย่างน้อย 1-2 แท่งเทียน M5 ถัดไป

Normal Signal (สัญญาณระดับปานกลาง):
  เกิดรูปแบบ Pin Bar หรือ Three Soldiers/Crows ณ แนวราคาปกติที่มี Swing Point เดี่ยว
  คะแนนความมั่นใจ C_strategy อยู่ในช่วง 0.85 - 0.88
  คาดหวัง: ราคามีการฟอร์มตัวกลับตัว แต่อาจเกิดลักษณะ Sideway หรือ Retest ซ้ำของราคาก่อนเปลี่ยนทิศทางจริง

False Signal (สัญญาณหลอก):
  เกิดลักษณะทะลุหลอก (Fakeout) ที่ราคาเบรคผ่านแนวต้าน/รับแบบเต็มแท่ง (Close ปิดนอกแนว) แต่ยังจัดว่ามีรูปแบบกลับตัวหลอก
  ระบบจะบล็อกสัญญาณนี้ผ่านเงื่อนไข Proximity และ Market State ที่เปลี่ยนไปเป็น BREAKOUT_EMERGING

******************************************************************************--
#### 9. AUDIT REQUIREMENTS
******************************************************************************--
ระบบประเมินผล WORM Database ต้องบันทึกตัวแปรสำหรับการวิเคราะห์หลังการเทรด (Post-Trade Analysis) ดังต่อไปนี้:
  - audit_id             : รหัสตรวจสอบเฉพาะรอบการประเมิน (UUIDv4)
  - timestamp            : เวลาประเมินผลของระบบ (UTC)
  - symbol               : คู่เงินหรือสินทรัพย์
  - market_state         : สภาวะตลาด ณ เวลาประเมิน
  - state_age            : อายุรอบตลาด
  - nearest_support      : ระดับแนวรับใกล้ที่สุด
  - nearest_resistance   : ระดับแนวต้านใกล้ที่สุด
  - pattern_detected     : ชื่อรูปแบบราคาที่ตรวจจับได้
  - current_candle_ohlcv : ค่า OHLCV ของแท่งเทียน M5[-1]
  - raw_confidence       : คะแนนความเชื่อมั่นดิบจากรูปแบบ (85-92)
  - entry_score          : คะแนนสุดท้ายเข้าซื้อขาย
  - block_score          : คะแนนบล็อกสัญญาณ
  - c_strategy           : ความมั่นใจเชิงกลยุทธ์ (0.0-1.0)
  - eligible             : สถานะผ่านเงื่อนไขการประเมินเบื้องต้น (true/false)
  - action               : ทิศทางการส่งคำสั่ง (CALL / PUT / NO_SETUP)
  - fail_reason_code     : รหัสระบุสาเหตุข้อขัดข้อง

******************************************************************************--
#### 10. OUTPUT CONTRACT (FROZEN SCHEMA)
******************************************************************************--
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_PASNR_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "pa_snr" },
    "eligible":            { "type": "BOOLEAN" },
    "action":              { "type": "STRING", "enum": ["CALL", "PUT", "NO_SETUP"] },
    "entry_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "block_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "strategy_confidence": { "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "direction_confidence":{ "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "expected_state":      { "type": "STRING",
                             "enum": ["SIDEWAY_RANGE", "REVERSAL_FORMING",
                                      "DISTRIBUTION", "TRANSITIONAL", "UNCLEAR"] },
    "fail_reason_code":    { "type": "STRING" },
    "audit_id":            { "type": "STRING",
                             "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[4][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$" },
    "expiry":              { "type": "STRING", "const": "M5" },
    "details": {
      "type": "OBJECT",
      "properties": {
        "level_touched":        { "type": "NUMBER" },
        "pattern_detected":     { "type": "STRING" },
        "calculated_wick_ratio":{ "type": "NUMBER" }
      },
      "required": ["level_touched", "pattern_detected", "calculated_wick_ratio"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}

---

### ?? STRATEGY: Reversal Group A PIN BAR SCALPER

# FINAL SPECIFICATION: PIN BAR SCALPER (pin_bar_scalper)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

******************************************************************************--
#### 1. STRATEGY OVERVIEW
******************************************************************************--
ชื่อกลยุทธ์:
  Pin Bar Reversal Scalper Strategy
  (Pin Bar Reversal Scalper with RSI-3 and Local Support/Resistance)

วัตถุประสงค์:
  ตรวจจับสภาวะกลับตัวระดับสแคลเปอร์ในกรอบสั้น M5 (Scalping Reversal) 
  โดยผสมผสานการเกิดโครงสร้างแท่งเทียนประเภท Pin Bar (Hammer / Shooting Star) 
  ร่วมกับดัชนีโมเมนตัม RSI กรอบเวลาสั้นพิเศษ RSI(3) ที่อยู่ในโซนสุดโต่ง (Extreme Oversold / Overbought) 
  ณ จุดที่ราคาประชิดแนวรับและแนวต้านท้องถิ่นระยะสั้น 8 แท่งเทียน 
  เพื่อส่งสัญญาณเข้าทำสัญญาทันทีเมื่อเริ่มต้นแท่งเทียนใหม่โดยปิดสัญญาที่สิ้นสุดแท่ง M5 (5 นาที)

บทบาทในระบบ:
  Leading Strategy — สร้างสัญญาณเทรดได้ด้วยตนเองเมื่อเงื่อนไขโครงสร้างราคาและโมเมนตัมสอดคล้องกันอย่างครบถ้วน

ประเภทสัญญาณ:
  Reversal — กลับตัวระยะสั้นพิเศษภายใน 1 แท่ง M5 (5 นาที)

Market States ที่เหมาะสม:
  SIDEWAY_RANGE    — ราคาแกว่งในกรอบ คลื่นราคาโต้ตอบดีกับ RSI        [★★★★★]
  REVERSAL_FORMING — เกิดสัญญาณกลับตัว Pin Bar ในช่วงสิ้นสุดเทรนด์ย่อย   [★★★★★]
  DISTRIBUTION     — ราคาแกว่งตัวในขอบเขตกระจาย ดัก PUT ความมั่นใจสูง    [★★★★★]
  TRANSITIONAL     — สภาพรอยต่อของตลาด ใช้ได้แต่ลดน้ำหนัก Entry Score 30% [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  TRENDING_STRONG   — สวนเทรนด์แรงจะถูกลากทะลุเนื่องจาก RSI(3) จะติดโซนค้าง (RSI Pegging)
  BREAKOUT_EMERGING — ราคาเพิ่งหลุดโซนต้าน/รับและเคลื่อนที่ด้วยความเร็ว
  ACCUMULATION      — ตลาดสงบรอสะสมกำลัง ไม่เหมาะกับกลยุทธ์ Reversal
  TRENDING_WEAK     — แนวโน้มทั่วไป
  LIQUIDITY_VOID    — ตลาดขาดปริมาณซื้อขาย ราคาขยับเป็นขั้นบันไดสัญญาณหลอกสูง
  CHOPPY_UNCERTAIN  — ตลาดผันผวนและไม่มีทิศทางแน่นอน
  UNCLEAR           — ข้อมูลตลาดไม่สมบูรณ์

******************************************************************************--
#### 2. REQUIRED INPUTS
******************************************************************************--
1. M5 OHLCV Candles (ย้อนหลังอย่างน้อย 20 แท่ง เพื่อประมวลผลอินดิเคเตอร์และแนวรับ/ต้าน)
   เหตุผล: คำนวณ RSI(3) และหาแนวต้าน/แนวรับท้องถิ่นระยะย้อนหลัง 8 แท่ง

2. Relative Strength Index - RSI(3) บน M5
   เหตุผล: ตรวจวัดระดับความร้อนแรงของโมเมนตัมระยะสั้นพิเศษเพื่อระบุสภาวะ Extreme Oversold/Overbought

3. Local Support & Resistance (ย้อนหลัง 8 แท่ง ไม่รวมแท่งประเมินปัจจุบัน)
   - Local Support = Min(Low[-9], Low[-8], ..., Low[-2])
   - Local Resistance = Max(High[-9], High[-8], ..., High[-2])
   เหตุผล: กำหนดระดับแนวราคาปิดและราคาสัมผัสชั่วคราวเพื่ออ้างอิงแรงผลักกลับของราคา

4. Candle Structure Metrics (คำนวณบนแท่ง M5[-1])
   - Body Size = |Close - Open|
   - Upper Wick = High - Max(Open, Close)
   - Lower Wick = Min(Open, Close) - Low
   - Candle Height = High - Low
   - Body Ratio = Body Size / Candle Height
   เหตุผล: ตรวจจับสัดส่วนแท่งเทียนประเภท Pin Bar และตัดสัญญาณโดจิที่ไร้ทิศทางออก

5. Real-Time Tick Feed (ปัจจุบัน)
   เหตุผล: ยืนยันความต่อเนื่องของ Broker Data Feed

6. Market State + State Age (จาก Intelligence OS)
   เหตุผล: กรองทิศทางการทำกำไรในSuitable States และปรับคะแนนตามอายุตลาด

******************************************************************************--
#### 3. ENTRY CONDITIONS
******************************************************************************--
ลำดับขั้นการประเมิน — ต้องผ่านทุกขั้นตามลำดับ หากขั้นใดล้มเหลวให้หยุดทันที

CONDITION 1 — Market State Eligibility
  ตรวจสอบ Market State ปัจจุบันจาก Intelligence OS
  ผ่าน: SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION, TRANSITIONAL
  ไม่ผ่าน: หยุดการทำงานทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — Candle Geometry Verification
  ตรวจสอบความสูงรวมแท่งเทียน (Candle Height) ต้องมากกว่า 0 (ป้องกันความผิดพลาดทางเทคนิค)
  
  ตรวจสอบความหนาแน่นเนื้อเทียน (Body Ratio):
    Body_Ratio = Body_Size[-1] / Candle_Height[-1]
    เกณฑ์: Body_Ratio < 0.05 (MIN_BODY_RATIO = 0.05) → ถือว่าเป็น Doji → หยุดการทำงานทันที → fail_reason_code: DOJI_CANDLE_INVALID

CONDITION 3 — Pin Bar Pattern Recognition
  ประเมินพฤติกรรมการทดสอบและปฏิเสธราคาล่าสุด:

  3a. ตรวจจับ Bullish Pin Bar ( Hammer ) - ฝั่ง CALL:
    - Lower_Wick[-1] >= Body_Size[-1] * 2.0 (WICK_TO_BODY_RATIO = 2.0)
    - Upper_Wick[-1] <= Body_Size[-1] * 0.5 (OPPOSITE_WICK_RATIO = 0.5)
    - Close[-1] > Open[-1] (เนื้อเทียนปิดเป็นสีเขียว)
    
  3b. ตรวจจับ Bearish Pin Bar ( Shooting Star ) - ฝั่ง PUT:
    - Upper_Wick[-1] >= Body_Size[-1] * 2.0 (WICK_TO_BODY_RATIO = 2.0)
    - Lower_Wick[-1] <= Body_Size[-1] * 0.5 (OPPOSITE_WICK_RATIO = 0.5)
    - Close[-1] < Open[-1] (เนื้อเทียนปิดเป็นสีแดง)

  ไม่พบรูปทรง Pin Bar ตามเกณฑ์ 3a หรือ 3b → หยุดการทำงานทันที → fail_reason_code: NO_PIN_BAR_PATTERN

CONDITION 4 — RSI(3) Extreme Check
  คำนวณ RSI(3) ของแท่งเทียนล่าสุด:
  
  สำหรับ CALL (Bullish Reversal):
    RSI(3)[-1] < 20 (RSI_OVERSOLD = 20)
    
  สำหรับ PUT (Bearish Reversal):
    RSI(3)[-1] > 80 (RSI_OVERBOUGHT = 80)
    
  หากไม่อยู่ในโซนกลับตัวสุดโต่ง → หยุดการทำงานทันที → fail_reason_code: RSI_NOT_EXTREME

CONDITION 5 — Local S/R Proximity
  หาระดับแนวรับ/ต้านใน 8 แท่งเทียนที่ผ่านมา (ไม่นับรวมแท่งล่าสุด M5[-1])
  
  สำหรับ CALL (ความใกล้ชิดแนวรับ Support ท้องถิ่น):
    - Local_Support = Min(Low[-2], Low[-3], ..., Low[-9])
    - ระยะห่าง: |Low[-1] - Local_Support| / Local_Support <= 0.0005 (SR_PROXIMITY_PCT = 0.0005, อยู่ในระยะ 0.05%)
    
  สำหรับ PUT (ความใกล้ชิดแนวต้าน Resistance ท้องถิ่น):
    - Local_Resistance = Max(High[-2], High[-3], ..., High[-9])
    - ระยะห่าง: |High[-1] - Local_Resistance| / Local_Resistance <= 0.0005 (SR_PROXIMITY_PCT = 0.0005, อยู่ในระยะ 0.05%)

  ไม่ผ่านเกณฑ์ → หยุดการทำงานทันที → fail_reason_code: OUTSIDE_LOCAL_SR_PROXIMITY

******************************************************************************--
#### 4. ENTRY SCORE LOGIC
******************************************************************************--
ในเวอร์ชันพิมพ์เขียวพื้นฐาน (Baseline Specs) คะแนนการเทรดจะถูกกำหนดคงที่หากผ่านทุกข้อกำหนดของเงื่อนไขการเปิดสัญญาณ:

  - Raw Score = 88 (คะแนนความเสถียรรูปทรง Pin Bar ร่วมกับ RSI)

การปรับคะแนนตามช่วงเวลาและสภาวะตลาด (State & Lifecycle Adjustments):
  - Fresh / Active State Lifecycle → Entry Score = Raw Score
  - Late State Lifecycle           → Entry Score = Raw Score * 0.80
  - Exhausted State Lifecycle      → Entry Score = 0 (และบล็อกการเข้าเทรด)
  - TRANSITIONAL Market State      → Entry Score = Entry Score * 0.70

******************************************************************************--
#### 5. BLOCK SCORE LOGIC
******************************************************************************--
Block Score ของกลยุทธ์ถูกออกแบบไว้ที่ 0 สำหรับทุกกรณีที่ผ่านเงื่อนไขการกรองเบื้องต้น:

*** SOFT BLOCK FACTORS ***
  * ไม่มีตัวแปร Soft Block คะแนนสะสมในเวอร์ชันนี้ (Block Score = 0 เสมอหากผ่าน Hard Block)

*** HARD BLOCK FACTORS ***
  * HB-1: Market State อยู่ในกลุ่มบล็อก (TRENDING_STRONG, BREAKOUT_EMERGING, ACCUMULATION, TRENDING_WEAK, LIQUIDITY_VOID, CHOPPY_UNCERTAIN, UNCLEAR)
          → Block Score = 100
  * HB-2: ความสูงแท่งเทียนต่ำกว่าหรือเท่ากับศูนย์ (Candle Height <= 0)
          → Block Score = 100
  * HB-3: สถานะรอบตลาด (State Lifecycle) อยู่ในระดับ Exhausted
          → Block Score = 100

*** สูตรคำนวณ Block Score สุดท้าย ***
  IF เกิดเงื่อนไข Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = 0

******************************************************************************--
#### 6. STRATEGY CONFIDENCE
******************************************************************************--
ความมั่นใจเชิงกลยุทธ์ (C_strategy) มีค่าคงที่ระหว่าง 0.0 ถึง 1.0 ตามระบบคะแนนดิบที่แปลงสเกล:

  C_strategy = Raw Score / 100.0 = 0.88

ตัวอย่างการคำนวณ:
  - สัญญาณเทรดเกิดขึ้นสมบูรณ์ผ่านเงื่อนไข Pin Bar + RSI + S/R Proximity:
    C_strategy = 0.88
    direction_confidence = 0.88

******************************************************************************--
#### 7. FAIL CONDITIONS
******************************************************************************--
กลยุทธ์จะคืนค่า NO_SETUP ทันทีพร้อมตั้งค่ารหัสล้มเหลว (fail_reason_code) เมื่อพบสถานการณ์ดังต่อไปนี้:

  - MARKET_STATE_BLOCKED      : Market State ไม่ได้อยู่ในเกณฑ์ Suitable States
  - DOJI_CANDLE_INVALID       : แท่งเทียนมีสัดส่วนเนื้อเทียนน้อยเกินไป (น้อยกว่า 5% ของความสูงรวม)
  - NO_PIN_BAR_PATTERN        : โครงสร้างแท่งเทียนไม่ผ่านเกณฑ์การทำรูปทรง Pin Bar ที่ระบุ
  - RSI_NOT_EXTREME           : ค่าดัชนี RSI(3) ไม่ถึงขีดสุดขอบ (20 สำหรับ CALL / 80 สำหรับ PUT)
  - OUTSIDE_LOCAL_SR_PROXIMITY: ขอบราคาต่ำสุด/สูงสุดอยู่ห่างแนวรับ/ต้านในระยะ 8 แท่ง เกินกว่า 0.05%
  - BROKER_FEED_FREEZE        : การป้อนข้อมูล Tick ค้างเกิน 10 วินาที
  - INSUFFICIENT_DATA         : ข้อมูลแท่งเทียนต่ำกว่าความต้องการขั้นต่ำ (20 แท่ง)
  - ZERO_HEIGHT_CANDLE        : ความยาวแท่งเทียนล่าสุดมีค่าเท่ากับ 0

******************************************************************************--
#### 8. EXPECTED BEHAVIOR
******************************************************************************--
High-Quality Scalp Reversal (สัญญาณกลับตัวความเชื่อมั่นปกติ):
  ราคาขึ้นแตะแนวต้าน/แนวรับท้องถิ่น 8 แท่งเทียนพอดี พร้อมเกิดรูปทรง Pin Bar ข้ามแนวต้านและดึงกลับมาทิ้งไส้ยาว 
  โดย RSI(3) มีค่าน้อยกว่า 10 หรือมากกว่า 90 (Extreme Overbought)
  คะแนนความมั่นใจ C_strategy = 0.88
  คาดหวัง: ราคาเกิดการกลับตัวและปิดทางตรงกันข้ามทันทีในแท่งเทียน M5 ถัดไป 1 แท่ง (5 นาที)

Weak Reversal Setup (สัญญาณอ่อนแอกว่าปกติ):
  เกิดขึ้นเมื่อรูปทรง Pin Bar ผ่านเกณฑ์ขั้นต่ำพอดี (เช่น ไส้เทียนยาว 2 เท่าของเนื้อพอดี) และค่า RSI อยู่ใกล้ขอบแดนพอดี (เช่น RSI = 19.5 หรือ 80.5)
  คะแนนความมั่นใจ C_strategy = 0.88
  คาดหวัง: ราคาอาจเด้งกลับแต่มีความเสี่ยงถูกลากทะลุเนื่องจากแรงส่งโมเมนตัมยังมีหลงเหลืออยู่

RSI Pegging (สภาวะลากเลื้อยเทรนด์แรง):
  เกิดขึ้นเมื่อตลาดมีความเป็นแนวโน้มแข็งแกร่ง (Strong Trend) แต่โปรแกรม Intelligence OS ประมวลสภาวะพลาด 
  ราคาจะดันทะลุแนวต้าน/รับท้องถิ่นไปเรื่อยๆ และดัชนี RSI(3) ค้างอยู่นอกเขตขอบเขตด้านบน/ล่าง (Pegging) 
  ส่งผลให้เกิดจังหวะแพ้แบบต่อเนื่องเนื่องจากการฝืนเทรนด์

******************************************************************************--
#### 9. AUDIT REQUIREMENTS
******************************************************************************--
ระบบประเมินผล WORM Database ต้องจัดเก็บข้อมูลชุดนี้ทุกครั้งที่มีการรันกระบวนการ:
  - audit_id             : รหัสตรวจสอบเฉพาะรอบการประเมิน (UUIDv4)
  - timestamp            : เวลาประเมินผลของระบบ (UTC)
  - symbol               : คู่เงินหรือสินทรัพย์
  - market_state         : สภาวะตลาด ณ เวลาประเมิน
  - state_age            : อายุรอบตลาด
  - rsi3_value           : ค่าดัชนี RSI(3) ณ แท่งล่าสุด
  - local_support        : แนวรับท้องถิ่นระยะ 8 แท่ง
  - local_resistance     : แนวต้านท้องถิ่นระยะ 8 แท่ง
  - current_candle_ohlcv : ค่า OHLCV ของแท่งเทียน M5[-1]
  - raw_confidence       : คะแนนความเชื่อมั่นดิบ (88)
  - entry_score          : คะแนนสุดท้ายเข้าซื้อขาย
  - block_score          : คะแนนบล็อกสัญญาณ (0 หรือ 100)
  - c_strategy           : ความมั่นใจเชิงกลยุทธ์ (0.0-1.0)
  - eligible             : สถานะผ่านเงื่อนไขการประเมินเบื้องต้น (true/false)
  - action               : ทิศทางการส่งคำสั่ง (CALL / PUT / NO_SETUP)
  - fail_reason_code     : รหัสระบุสาเหตุข้อขัดข้อง

******************************************************************************--
#### 10. OUTPUT CONTRACT (FROZEN SCHEMA)
******************************************************************************--
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_PinBarScalper_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "pin_bar_scalper" },
    "eligible":            { "type": "BOOLEAN" },
    "action":              { "type": "STRING", "enum": ["CALL", "PUT", "NO_SETUP"] },
    "entry_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "block_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "strategy_confidence": { "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "direction_confidence":{ "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "expected_state":      { "type": "STRING",
                             "enum": ["SIDEWAY_RANGE", "REVERSAL_FORMING",
                                      "DISTRIBUTION", "TRANSITIONAL", "UNCLEAR"] },
    "fail_reason_code":    { "type": "STRING" },
    "audit_id":            { "type": "STRING",
                             "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[4][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$" },
    "expiry":              { "type": "STRING", "const": "M5" },
    "details": {
      "type": "OBJECT",
      "properties": {
        "level_touched":        { "type": "NUMBER" },
        "pattern_detected":     { "type": "STRING" },
        "calculated_wick_ratio":{ "type": "NUMBER" }
      },
      "required": ["level_touched", "pattern_detected", "calculated_wick_ratio"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}

---

### ?? STRATEGY: Reversal Group A REJECTION 5M PA

# FINAL SPECIFICATION: REJECTION 5M PA (rejection_5m_pa)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

******************************************************************************--
#### 1. STRATEGY OVERVIEW
******************************************************************************--
ชื่อกลยุทธ์:
  Rejection 5m PA
  (Rejection 5-Minute Price Action at Key S/R Levels)

วัตถุประสงค์:
  ตรวจจับการปฏิเสธราคา (Price Rejection) ที่เกิดขึ้นบนแท่งเทียน M5 ล่าสุด
  ณ แนวรับหรือแนวต้านที่ผ่านการยืนยันคุณภาพเชิงสถิติแล้ว
  กลยุทธ์ไม่ทำนายทิศทางตลาด แต่ตรวจจับพฤติกรรมโครงสร้างแท่งเทียนที่วัดได้
  และส่งสัญญาณ ณ วินาทีเปิดของแท่งถัดไปทันที
  โดยกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — มีสิทธิ์สร้างสัญญาณหลักด้วยตัวเองโดยไม่ต้องรอ
  Indicator ยืนยัน เนื่องจากสัญญาณมาจากโครงสร้างราคาโดยตรง

ประเภทสัญญาณ:
  Reversal — กลับตัวระยะสั้นภายใน 1-3 แท่ง M5

Market States ที่เหมาะสม:
  SIDEWAY_RANGE    — แนวรับ/ต้านชัดเจน ราคาเด้งในกรอบ           [★★★★★]
  REVERSAL_FORMING — มีสัญญาณกลับตัว Rejection ยืนยันได้ดี      [★★★★★]
  DISTRIBUTION     — ราคาแตะขอบกรอบผันผวน ระวัง False Rejection  [★★★★★]
  TRANSITIONAL     — ใช้ได้แต่ลดน้ำหนัก Entry Score 30%          [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  TRENDING_STRONG   — Rejection สวนเทรนด์แรง โอกาสแพ้สูงมาก
  BREAKOUT_EMERGING — ราคากำลังทะลุ Rejection เป็นสัญญาณหลอก
  ACCUMULATION      — ตลาดบีบอัด รอทิศทาง ยังไม่มีแนวรับ/ต้านชัด
  TRENDING_WEAK     — เทรนด์ยังมีอยู่ Rejection สวนทิศทาง
  LIQUIDITY_VOID    — ตลาดหยุดนิ่ง ราคาไม่มีแรงขับ
  CHOPPY_UNCERTAIN  — Rejection ไม่มีความหมายในตลาดสับสน
  UNCLEAR           — ข้อมูลขัดแย้ง ห้ามส่งสัญญาณ

******************************************************************************--
#### 2. REQUIRED INPUTS
******************************************************************************--
1. M5 OHLCV Candles (ย้อนหลัง 100 แท่ง)
   เหตุผล: คำนวณแนวระดับ S/R, Volume Profile และ ATR

2. ATR(14) บน M5
   เหตุผล: Normalize ระยะทุกค่าให้ไม่ขึ้นกับความผันผวนสัมบูรณ์ของคู่เงิน

3. S/R Level Database (คำนวณจาก Swing Points ย้อนหลัง 20 แท่ง)
   เหตุผล: ระบุพิกัดแนวรับ/ต้านที่ผ่านการยืนยัน พร้อมคะแนนคุณภาพ S_level

4. Volume Profile (ย้อนหลัง 100 แท่ง)
   เหตุผล: ระบุโซนราคาที่มีปริมาณสะสมสูง ใช้คำนวณ V_profile ใน S_level

5. Candle Structure Metrics (คำนวณบนแท่ง M5[-1])
   - Body Size    = |Close - Open|
   - Upper Wick   = High - Max(Open, Close)
   - Lower Wick   = Min(Open, Close) - Low
   เหตุผล: วัดการปฏิเสธราคาเชิงโครงสร้างแท่งเทียน

6. Average Volume (เฉลี่ย 20 แท่ง M5)
   เหตุผล: ตรวจ Volume Climax Exception และ Hard Block Volume Breakout

7. Real-Time Tick Feed (ปัจจุบัน)
   เหตุผล: ตรวจ Price Velocity ณ จุดสัมผัสแนวระดับ และ Broker Feed Freeze

8. Market State + State Age (จาก Intelligence OS)
   เหตุผล: กลยุทธ์ต้องทราบทั้งสภาวะตลาดและช่วงอายุ (Fresh/Active/Late/Exhausted)
   เพื่อปรับ Entry Score ตาม State Lifecycle

9. High Impact News Calendar (+/- 15 นาที)
   เหตุผล: Hard Block ช่วงก่อน/หลังข่าว

******************************************************************************--
#### 3. ENTRY CONDITIONS
******************************************************************************--
ลำดับขั้นการประเมิน — ต้องผ่านทุกขั้นตามลำดับ หากขั้นใดล้มเหลวให้หยุดทันที

CONDITION 1 — Market State Eligibility
  ตรวจว่า Market State ปัจจุบันอยู่ใน Suitable States หรือไม่
  ผ่าน: SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION, TRANSITIONAL
  ไม่ผ่าน: หยุดทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — S/R Level Quality Check (S_level Engine)
  คำนวณ S_level_base (สูงสุด 100):
    C_touch   (50%): แท่งที่แตะระดับ ±0.1*ATR → แต่ละแตะ = 20 คะแนน, Max 50
    D_react   (30%): ระยะดีดกลับเฉลี่ยหลังสัมผัส → Normalize เทียบ ATR, Max 30
    V_profile (20%): หากระดับนี้อยู่ใน High Volume Node ย้อนหลัง 100 แท่ง → +20

  คำนวณ Age Decay:
    S_level = S_level_base × exp(−0.015 × age)
    age = จำนวนแท่ง M5 นับจากจุดสัมผัสล่าสุด

  เกณฑ์: S_level < 40 → หยุดทันที → fail_reason_code: LEVEL_TOO_WEAK

CONDITION 3 — Candle Structure Validity
  Body Size ต้องมากกว่า 0.05 × ATR_M5
  ไม่ผ่าน → fail_reason_code: DOJI_SETUP_INVALID

CONDITION 4 — Price Touch and Close (ทิศทางเฉพาะ)
  สำหรับ CALL (กลับตัวขึ้นที่แนวรับ):
    4a. Low[-1] <= Support Level
    4b. Close[-1] > Support Level
    4c. Lower Wick > Body Size (ไส้เทียนล่างยาวกว่าเนื้อเทียน)
    4d. Lower Wick > Upper Wick (ไส้ล่างต้องยาวกว่าไส้บน)

  สำหรับ PUT (กลับตัวลงที่แนวต้าน):
    4a. High[-1] >= Resistance Level
    4b. Close[-1] < Resistance Level
    4c. Upper Wick > Body Size
    4d. Upper Wick > Lower Wick

  ไม่ผ่านข้อใดข้อหนึ่ง → fail_reason_code: CANDLE_STRUCTURE_INVALID

CONDITION 5 — Volume Climax Exception Check
  IF Volume[-1] > 1.5 × Avg_Volume AND Close[-1] อยู่ภายในขอบแนวระดับ
  → ถือว่าเป็น Buying/Selling Climax → อนุญาตผ่าน Hard Block Volume ได้
  IF Volume[-1] > 1.5 × Avg_Volume AND Close[-1] ทะลุออกนอกแนวระดับ
  → Hard Block ทันที → fail_reason_code: BREAKOUT_CLOSED_OUTSIDE

CONDITION 6 — Broker Feed Validity
  ตรวจว่า Tick Feed ไม่หยุดค้างเกิน 10 วินาที
  ไม่ผ่าน → fail_reason_code: BROKER_FEED_FREEZE

******************************************************************************--
#### 4. ENTRY SCORE LOGIC
******************************************************************************--
Entry Score (สเกล 0–100) คำนวณจาก 4 ปัจจัยถ่วงน้ำหนัก รวม 100%:

Factor 1 — Wick Ratio Factor (F_wick) น้ำหนัก 30%
  R_wick = Wick_target / Body Size
  IF R_wick < 1.0 → F_wick = 0
  IF R_wick >= 1.0 → F_wick = Min(100, ((R_wick − 1.0) / (2.0 − 1.0)) × 50 + 50)
  ตีความ: R_wick = 1.0 → F_wick = 50, R_wick = 2.0 → F_wick = 100

Factor 2 — Penetration Depth Factor (F_pen) น้ำหนัก 20%
  D_pen = |จุดสัมผัสแนวระดับ − พิกัดแนวระดับ| / ATR_M5
  F_pen = Min(100, (D_pen / 0.5) × 100)
  ตีความ: ทะลุเข้าไป 0.5×ATR = คะแนนเต็ม

Factor 3 — Close Proximity Factor (F_close) น้ำหนัก 20%
  D_close = |Close[-1] − พิกัดแนวระดับ| / ATR_M5
  F_close = Max(0, 100 − (D_close / 0.25) × 100)
  ตีความ: ปิดห่างแนว 0.25×ATR = คะแนน 0

Factor 4 — Location Quality Factor (F_location) น้ำหนัก 30%
  F_location = S_level (ดึงตรงจาก Condition 2)
  ตีความ: แนวยิ่งแข็งแกร่ง คะแนนยิ่งสูง

สูตรรวม:
  Raw Entry Score = (0.30 × F_wick) + (0.20 × F_pen) + (0.20 × F_close) + (0.30 × F_location)

ปรับตาม State Lifecycle:
  Fresh / Active   → ใช้ Raw Entry Score ตรง
  Late             → Entry Score = Raw Entry Score × 0.80
  Exhausted        → Block Score = 100 ทันที (ห้ามเข้า)

ปรับตาม TRANSITIONAL State:
  Entry Score = Raw Entry Score × 0.70

******************************************************************************--
#### 5. BLOCK SCORE LOGIC
******************************************************************************--
Block Score เริ่มที่ 0 สะสมจาก Soft Block และ Hard Block

*** SOFT BLOCK FACTORS (สะสมคะแนนความเสี่ยง) ***

  SF-1: ATR ปัจจุบัน > 1.5 × ATR เฉลี่ย 20 แท่ง
        → +30 คะแนน
        เหตุผล: ตลาดผันผวนสูง Rejection อาจเป็น Noise

  SF-2: Close[-1] ห่างจากแนวระดับ > 0.3 × ATR_M5
        → +25 คะแนน
        เหตุผล: ปิดห่างแนวมาก ราคากลับมาสัมผัสได้ยาก

  SF-3: Market State เป็น DISTRIBUTION หรือ ACCUMULATION
        → +20 คะแนน
        เหตุผล: สภาวะเสี่ยง False Rejection สูง

*** HARD BLOCK FACTORS (Block Score = 100 ทันที) ***

  HB-1: Market State เป็น TRENDING_STRONG
        → Block Score = 100

  HB-2: Market State เป็น BREAKOUT_EMERGING
        → Block Score = 100

  HB-3: Volume[-1] > 1.5 × Avg_Volume AND Close[-1] ทะลุออกนอกแนวระดับ
        → Block Score = 100 (ยกเว้น Climax Exception ใน Condition 5)

  HB-4: Wick ฝั่งตรงข้ามยาวกว่า Wick ฝั่งเป้าหมาย
        (Wick_opposite > Wick_target)
        → Block Score = 100

  HB-5: อยู่ในช่วงข่าว High Impact ±15 นาที
        → Block Score = 100

  HB-6: State Lifecycle = Exhausted
        → Block Score = 100

*** สูตร Block Score สุดท้าย ***
  IF มี Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = Sum(Soft Block คะแนนที่ติด), Max = 100

******************************************************************************--
#### 6. STRATEGY CONFIDENCE
******************************************************************************--
C_strategy คำนวณแบบค่าต่อเนื่อง (สเกล 0.0–1.0):

  C_strategy = (0.30 × S_ST) + (0.40 × S_WR) + (0.30 × S_WD)

Sub-scores:

  S_ST (Structural Touch Score):
    S_ST = Max(0, 1.0 − (|Low[-1]/High[-1] − พิกัดแนวระดับ| / (0.1 × ATR_M5)))
    ตีความ: สัมผัสแนวระดับแม่นยำแค่ไหน 1.0 = แม่นมาก, 0.0 = ไม่สัมผัส

  S_WR (Wick Ratio Score):
    S_WR = Min(1.0, Wick_target / (1.5 × Body Size))
    ตีความ: ไส้เทียนยาวกว่าเนื้อ 1.5 เท่า = S_WR เต็ม 1.0

  S_WD (Wick Dominance Score):
    S_WD = Min(1.0, Wick_target / (2.0 × Wick_opposite))
    ตีความ: ไส้เป้าหมายยาวกว่าไส้ตรงข้าม 2 เท่า = S_WD เต็ม 1.0

ตัวอย่างการคำนวณ:
  แท่งเทียน: Body = 0.0005, Lower Wick = 0.0012, Upper Wick = 0.0002, ATR = 0.0010
  Low แตะ Support แม่นมาก → S_ST = 1.0
  S_WR = Min(1.0, 0.0012 / (1.5 × 0.0005)) = Min(1.0, 1.6) = 1.0
  S_WD = Min(1.0, 0.0012 / (2.0 × 0.0002)) = Min(1.0, 3.0) = 1.0
  C_strategy = (0.30×1.0) + (0.40×1.0) + (0.30×1.0) = 1.0 (สัญญาณสมบูรณ์แบบ)

******************************************************************************--
#### 7. FAIL CONDITIONS
******************************************************************************--
กลยุทธ์คืนค่า NO_SETUP ทันทีเมื่อเกิดกรณีต่อไปนี้:

  MARKET_STATE_BLOCKED   : Market State ไม่อยู่ใน Suitable States
  LEVEL_TOO_WEAK         : S_level < 40 หลังคำนวณ Age Decay
  DOJI_SETUP_INVALID     : Body Size < 0.05 × ATR_M5
  CANDLE_STRUCTURE_INVALID: เงื่อนไขโครงสร้างแท่งเทียนไม่ผ่าน (Condition 4)
  BREAKOUT_CLOSED_OUTSIDE : Volume สูง + ปิดทะลุออกนอกแนวระดับ
  BROKER_FEED_FREEZE     : Tick Feed หยุดค้างเกิน 10 วินาที
  NEWS_BLACKOUT          : อยู่ในช่วงข่าว High Impact ±15 นาที

******************************************************************************--
#### 8. EXPECTED BEHAVIOR
******************************************************************************--
Strong Rejection (สัญญาณคุณภาพสูง):
  ราคาพุ่งชนแนวต้าน/รับที่สะสม Volume หนาแน่น เกิดแรงปฏิเสธรวดเร็ว
  ทิ้งไส้เทียนยาว > 2× Body Size ปิดแท่งกลับเข้ากรอบอย่างชัดเจน
  C_strategy > 0.80, Entry Score > 75
  คาดหวัง: ราคาเคลื่อนที่ตามทิศทาง Rejection อย่างน้อย 1 แท่ง M5

Weak Rejection (สัญญาณคุณภาพปานกลาง):
  ราคาแตะแนวระดับที่ผ่านการทดสอบซ้ำหลายรอบแล้ว ไส้เทียนยาวปานกลาง
  C_strategy 0.50–0.79, Entry Score 60–74
  คาดหวัง: ราคาอาจเด้งกลับหรือ Retest ก่อนไปต่อ ผลลัพธ์ผันแปร

False Rejection (Breakout):
  ราคาทะลุผ่านแนวระดับและปิดออกนอกกรอบ พร้อม Volume สูง
  ระบบตรวจพบใน Condition 5 → Hard Block ทันที
  fail_reason_code: BREAKOUT_CLOSED_OUTSIDE
  ไม่ส่งสัญญาณ

******************************************************************************--
#### 9. AUDIT REQUIREMENTS
******************************************************************************--
บันทึกข้อมูลต่อไปนี้ลง WORM Database ทุกรอบการประเมิน:

  - audit_id        : UUIDv4 ของรอบนี้
  - timestamp       : แสตมป์เวลาระบบ (UTC)
  - symbol          : ชื่อคู่เงิน
  - market_state    : สภาวะตลาดและ State Age ณ รอบนั้น
  - candle_ohlcv    : OHLCV ของแท่ง M5[-1]
  - atr_m5          : ค่า ATR_M5 ณ รอบนั้น
  - level_touched   : พิกัดแนวรับ/ต้านที่ถูกสัมผัส
  - s_level_base    : คะแนน S/R ก่อน Age Decay
  - s_level_final   : คะแนน S/R หลัง Age Decay
  - level_age       : อายุแนวระดับ (จำนวนแท่ง)
  - f_wick          : คะแนน Wick Ratio Factor
  - f_pen           : คะแนน Penetration Depth Factor
  - f_close         : คะแนน Close Proximity Factor
  - f_location      : คะแนน Location Quality Factor
  - entry_score_raw : คะแนนก่อนปรับ Lifecycle
  - entry_score     : คะแนนหลังปรับ Lifecycle และ State
  - block_score     : คะแนน Block Score รวม
  - s_st            : Structural Touch Score
  - s_wr            : Wick Ratio Score
  - s_wd            : Wick Dominance Score
  - c_strategy      : คะแนน Strategy Confidence รวม
  - eligible        : true/false
  - action          : CALL / PUT / NO_SETUP
  - fail_reason_code: รหัสล้มเหลว (null ถ้าผ่าน)

******************************************************************************--
#### 10. OUTPUT CONTRACT (FROZEN SCHEMA)
******************************************************************************--
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_Rejection5mPA_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "rejection_5m_pa" },
    "eligible":            { "type": "BOOLEAN" },
    "action":              { "type": "STRING", "enum": ["CALL", "PUT", "NO_SETUP"] },
    "entry_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "block_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "strategy_confidence": { "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "direction_confidence":{ "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "expected_state":      { "type": "STRING",
                             "enum": ["SIDEWAY_RANGE","REVERSAL_FORMING",
                                      "DISTRIBUTION","TRANSITIONAL","UNCLEAR"] },
    "fail_reason_code":    { "type": "STRING" },
    "audit_id":            { "type": "STRING",
                             "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[4][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$" },
    "expiry":              { "type": "STRING", "const": "M5" },
    "details": {
      "type": "OBJECT",
      "properties": {
        "level_touched":        { "type": "NUMBER" },
        "pattern_detected":     { "type": "STRING" },
        "calculated_wick_ratio":{ "type": "NUMBER" }
      },
      "required": ["level_touched", "pattern_detected", "calculated_wick_ratio"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}

---

### ?? STRATEGY: Reversal Group A SR FAKEOUT REJECTION

# FINAL SPECIFICATION: SR FAKEOUT REJECTION (sr_fakeout_rejection)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

******************************************************************************--
#### 1. STRATEGY OVERVIEW
******************************************************************************--
ชื่อกลยุทธ์:
  SR Fakeout Rejection Strategy
  (Support & Resistance Fakeout Rejection / Liquidity Sweep Reversal)

วัตถุประสงค์:
  ตรวจจับสภาวะเบรคทะลุหลอกหรือการกวาดสภาพคล่อง (Spring และ Upthrust Patterns) ณ แนวรับและแนวต้านในอดีต 
  ที่ระบุได้ด้วยระดับ Swing Points บนกรอบเวลา M5 กลยุทธ์จะเน้นการตรวจจับจังหวะที่ราคาวิ่งข้ามแนวไปเก็บสภาพคล่อง 
  ก่อนจะดึงกลับเข้ามาปิดในกรอบอย่างรวดเร็วและทิ้งไส้เทียนยาวแสดงแรงปฏิเสธราคา (Price Rejection) 
  โดยกำหนดการส่งคำสั่ง ณ วินาทีแรกที่เปิดแท่งเทียนถัดไปโดยอิง Expiry ปิดแท่ง M5 (5 นาที)

บทบาทในระบบ:
  Leading Strategy — สัญญาณเกิดขึ้นจากพฤติกรรมการกวาดสภาพคล่องของราคากับระดับแนวระดับโดยตรง จึงส่งคำสั่งได้ทันทีเมื่อผ่านเกณฑ์

ประเภทสัญญาณ:
  Reversal — การกลับตัวทันทีหลังจากการกวาดสภาพคล่อง (Mean Reversion ในรอบ 1-2 แท่ง M5)

Market States ที่เหมาะสม:
  SIDEWAY_RANGE    — ตลาดวิ่งในกรอบ มีการทำ Fakeout ที่ขอบบ่อยครั้ง   [★★★★★]
  REVERSAL_FORMING — ตลาดแสดงสัญญาณทำจุดกลับตัวชัดเจน             [★★★★★]
  DISTRIBUTION     — การกวาดสภาพคล่องขอบบนเพื่อกลับตัวลง           [★★★★★]
  TRANSITIONAL     — ตลาดก้ำกึ่ง ใช้ได้แต่ลดน้ำหนัก Entry Score 30%    [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  TRENDING_STRONG   — สภาวะแนวโน้มรุนแรง (การเบรคมีโอกาสเป็นของจริงสูง)
  BREAKOUT_EMERGING — ตลาดเพิ่งทะลุกรอบและเริ่มเคลื่อนที่อย่างมีแรงส่ง
  ACCUMULATION      — ตลาดบีบตัวพักฐานรอการระเบิดทิศทาง
  TRENDING_WEAK     — แนวโน้มทั่วไป
  LIQUIDITY_VOID    — ตลาดไม่มีปริมาณซื้อขายรองรับ
  CHOPPY_UNCERTAIN  — สภาวะราคาผันผวนไร้ทิศทางและเต็มไปด้วย Noise
  UNCLEAR           — สถานะข้อมูลจาก intelligence OS ไม่ชัดเจน

******************************************************************************--
#### 2. REQUIRED INPUTS
******************************************************************************--
1. M5 OHLCV Candles (ย้อนหลังอย่างน้อย 45 แท่ง เพื่อรองรับ Swing Lookback 40 แท่ง + Window 3 แท่ง)
   เหตุผล: ใช้ค้นหา Swing High / Swing Low ประวัติศาสตร์และตรวจสอบโครงสร้างแท่งเทียนปัจจุบัน

2. Dynamic Support & Resistance Levels ( Swing Highs / Swing Lows )
   เหตุผล: กำหนดระดับอ้างอิงเพื่อประเมินจุดกวาดสภาพคล่อง (Liquidity Sweep)

3. Candle Structure Metrics (คำนวณบนแท่ง M5[-1] ล่าสุดที่เพิ่งปิด)
   - Body Size = |Close - Open|
   - Upper Wick = High - Max(Open, Close)
   - Lower Wick = Min(Open, Close) - Low
   - Candle Height = High - Low
   เหตุผล: วิเคราะห์ความยาวไส้เทียบกับโครงสร้างเนื้อแท่งเทียนเชิงสถิติ

4. Real-Time Tick Feed (ปัจจุบัน)
   เหตุผล: ตรวจสอบความถูกต้องสมบูรณ์ของระบบรับข้อมูลราคาโบรกเกอร์ (Feed Validation)

5. Market State + State Age (จาก Intelligence OS)
   เหตุผล: ใช้กรองสภาพแวดล้อมตลาดที่อนุญาตให้เทรดและปรับคะแนนตามวงจรชีวิตของสภาวะตลาด

******************************************************************************--
#### 3. ENTRY CONDITIONS
******************************************************************************--
ลำดับขั้นการประเมิน — ต้องผ่านทุกขั้นตามลำดับ หากขั้นใดล้มเหลวให้หยุดทันที

CONDITION 1 — Market State Eligibility
  ตรวจสอบ Market State ปัจจุบันจาก Intelligence OS
  ผ่าน: SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION, TRANSITIONAL
  ไม่ผ่าน: หยุดการทำงานทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — Dynamic S&R Detection (Historical Swing Points)
  คำนวณหา Swing Highs (แนวต้าน) และ Swing Lows (แนวรับ) จาก M5 Candles ย้อนหลัง SWING_LOOKBACK = 40 แท่ง
  โดยกรองข้อมูลไม่รวมแท่งล่าสุดที่เพิ่งปิดตัว (df.iloc[-1]) เพื่อป้องกันการทับซ้อนและอ้างอิงระดับประวัติศาสตร์ที่แท้จริง
  ใช้หน้าต่างทดสอบ SWING_WINDOW = 3 แท่ง (ต้องเป็นค่าขอบสุดในกรอบ j ∈ [1, 3] ทั้งสองข้าง)
  
  การจัดกลุ่มโซนระดับราคา (Clustering):
    ระดับราคาที่อยู่ใกล้กันไม่เกิน 0.03% (SR_CLUSTER_PCT = 0.0003) จะถูกยุบรวมเป็นระดับเดียวโดยใช้ค่าเฉลี่ย:
    |Level_A - Level_B| / Level_B <= 0.0003
    
  เกณฑ์: หากคำนวณแล้วไม่พบแนวรับหรือแนวต้านในอดีต → หยุดการทำงานทันที → fail_reason_code: NO_SR_LEVELS_DETECTED

CONDITION 3 — Spring & Upthrust Pattern Check (เงื่อนไขทิศทาง)
  ประเมินความสอดคล้องของแท่งเทียนล่าสุด M5[-1] กับระดับราคาอ้างอิง:

  3a. สำหรับสัญญาณ CALL (SPRING - Bullish Fakeout Rejection at Support):
    ราคาผ่านแนวรับลงไปต่ำชั่วคราวแต่สามารถดึงตัวกลับมาปิดเหนือแนวรับได้สำเร็จ:
    - Low[-1] < Support_Level
    - Close[-1] > Support_Level
    - Open[-1] > Support_Level - (Support_Level * 0.0005) (เปิดต้องไม่อยู่ต่ำกว่าแนวรับมากเกิน 0.05%)
    - เกณฑ์ไส้เทียนล่างดึงกลับ (Rejection Wick):
      * Lower_Wick[-1] >= Candle_Height[-1] * 0.45 (MIN_WICK_PCT = 0.45, ไส้ล่างต้องยาวอย่างน้อย 45% ของความสูงแท่งทั้งหมด)
      * Lower_Wick[-1] >= Body_Size[-1] * 1.5 (WICK_TO_BODY_RATIO = 1.5, ไส้ล่างต้องยาวไม่น้อยกว่า 1.5 เท่าของเนื้อเทียน)
      
  3b. สำหรับสัญญาณ PUT (UPTHRUST - Bearish Fakeout Rejection at Resistance):
    ราคาผ่านแนวต้านขึ้นไปชั่วคราวแต่สามารถดึงตัวกลับมาปิดใต้แนวต้านได้สำเร็จ:
    - High[-1] > Resistance_Level
    - Close[-1] < Resistance_Level
    - Open[-1] < Resistance_Level + (Resistance_Level * 0.0005) (เปิดต้องไม่อยู่สูงกว่าแนวต้านมากเกิน 0.05%)
    - เกณฑ์ไส้เทียนบนดึงกลับ (Rejection Wick):
      * Upper_Wick[-1] >= Candle_Height[-1] * 0.45 (MIN_WICK_PCT = 0.45, ไส้บนต้องยาวอย่างน้อย 45% ของความสูงแท่งทั้งหมด)
      * Upper_Wick[-1] >= Body_Size[-1] * 1.5 (WICK_TO_BODY_RATIO = 1.5, ไส้บนต้องยาวไม่น้อยกว่า 1.5 เท่าของเนื้อเทียน)

  หากไม่เข้าข่ายเกณฑ์ข้อ 3a หรือ 3b ข้างต้น → หยุดการทำงานทันที → fail_reason_code: FAKEOUT_PATTERN_NOT_MATCHED

CONDITION 4 — Broker Feed Validity
  ตรวจสอบข้อมูล Tick Feed ไม่หยุดค้างเกิน 10 วินาที
  ไม่ผ่านเกณฑ์ → หยุดการทำงานทันที → fail_reason_code: BROKER_FEED_FREEZE

******************************************************************************--
#### 4. ENTRY SCORE LOGIC
******************************************************************************--
ในเวอร์ชันพิมพ์เขียวพื้นฐาน (Baseline Specs) คะแนนการเทรดจะถูกกำหนดเป็นคะแนนแบบไม่ต่อเนื่อง (Discrete Score) โดยแยกตามความสอดคล้องของสีแท่งเทียนปิดทิศทาง (Directional Candlestick Confirmation):

  - สำหรับสัญญาณ CALL (SPRING):
    * แท่งเทียนปิดตัวเป็นสีเขียว (Close[-1] > Open[-1]) → Raw Score = 90 (มีความเชื่อมั่นทิศทางสูงเนื่องจากแรงซื้อหนุนจนปิดบวก)
    * แท่งเทียนปิดตัวเป็นสีแดง (Close[-1] < Open[-1]) → Raw Score = 80 (ความเชื่อมั่นปานกลางเนื่องจากราคายังปิดลบแม้ดึงกลับเหนือแนว)

  - สำหรับสัญญาณ PUT (UPTHRUST):
    * แท่งเทียนปิดตัวเป็นสีแดง (Close[-1] < Open[-1]) → Raw Score = 90 (มีความเชื่อมั่นทิศทางสูงเนื่องจากแรงขายกดดันปิดลบ)
    * แท่งเทียนปิดตัวเป็นสีเขียว (Close[-1] > Open[-1]) → Raw Score = 80 (ความเชื่อมั่นปานกลางเนื่องจากราคายังปิดบวกแม้ดึงกลับใต้แนว)

การปรับคะแนนตามช่วงเวลาและสภาวะตลาด (State & Lifecycle Adjustments):
  - Fresh / Active State Lifecycle → Entry Score = Raw Score
  - Late State Lifecycle           → Entry Score = Raw Score * 0.80
  - Exhausted State Lifecycle      → Entry Score = 0 (และบล็อกการเข้าเทรด)
  - TRANSITIONAL Market State      → Entry Score = Entry Score * 0.70

******************************************************************************--
#### 5. BLOCK SCORE LOGIC
******************************************************************************--
Block Score ของกลยุทธ์ถูกกำหนดไว้ที่ 0 สำหรับกรณีทั่วไปที่ผ่านเงื่อนไขการบล็อกระดับ Hard Block:

*** SOFT BLOCK FACTORS ***
  * ไม่มีตัวแปร Soft Block คะแนนสะสมในเวอร์ชันนี้ (Block Score = 0 เสมอหากผ่าน Hard Block)

*** HARD BLOCK FACTORS ***
  * HB-1: Market State อยู่ในกลุ่มบล็อก (TRENDING_STRONG, BREAKOUT_EMERGING, ACCUMULATION, TRENDING_WEAK, LIQUIDITY_VOID, CHOPPY_UNCERTAIN, UNCLEAR)
          → Block Score = 100
  * HB-2: ความยาวแท่งเทียนปัจจุบันมีค่าเป็นศูนย์ (Candle Height = 0)
          → Block Score = 100
  * HB-3: สถานะรอบตลาด (State Lifecycle) อยู่ในระดับ Exhausted
          → Block Score = 100

*** สูตรคำนวณ Block Score สุดท้าย ***
  IF เกิดเงื่อนไข Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = 0

******************************************************************************--
#### 6. STRATEGY CONFIDENCE
******************************************************************************--
ความมั่นใจเชิงกลยุทธ์ (C_strategy) มีค่าระหว่าง 0.0 ถึง 1.0 คำนวณจากการแปลงสเกลคะแนนความน่าเชื่อถือของการดึงกลับเชิงทิศทาง:

  C_strategy = Raw Score / 100.0

ตัวอย่างการคำนวณ:
  - เกิดสัญญาณ SPRING และปิดด้วยแท่งสีเขียว:
    Raw Score = 90
    C_strategy = 90 / 100.0 = 0.90
    
  - เกิดสัญญาณ SPRING แต่ปิดด้วยแท่งสีแดง:
    Raw Score = 80
    C_strategy = 80 / 100.0 = 0.80

******************************************************************************--
#### 7. FAIL CONDITIONS
******************************************************************************--
กลยุทธ์จะคืนค่า NO_SETUP ทันทีพร้อมตั้งค่ารหัสล้มเหลว (fail_reason_code) เมื่อพบสถานการณ์ดังต่อไปนี้:

  - MARKET_STATE_BLOCKED      : Market State ไม่ได้อยู่ในเกณฑ์ Suitable States
  - NO_SR_LEVELS_DETECTED     : ไม่พบแนวต้านหรือแนวรับที่ผ่านเกณฑ์ Swing Point ย้อนหลัง 40 แท่ง
  - FAKEOUT_PATTERN_NOT_MATCHED: โครงสร้างแท่งเทียนขัดแย้งกับตรรกะเบรคทะลุหลอก หรือสัดส่วนไส้เทียนไม่ได้ตามกำหนด
  - BROKER_FEED_FREEZE        : การป้อนข้อมูล Tick ค้างเกิน 10 วินาที
  - INSUFFICIENT_DATA         : ข้อมูลแท่งเทียนต่ำกว่าความต้องการขั้นต่ำ (45 แท่ง)
  - ZERO_HEIGHT_CANDLE        : ความสูงแท่งเทียนเป็น 0 (High = Low)

******************************************************************************--
#### 8. EXPECTED BEHAVIOR
******************************************************************************--
High-Quality Fakeout (สัญญาณระดับสูง):
  ราคามีลักษณะสะบัดหลุดแนวอย่างรวดเร็ว (Liquidity Sweep) แล้วดึงกลับมาปิดในแนวเดิมในเวลาอันรวดเร็ว 
  ทิ้งไส้เทียนยาว > 60% ของแท่งเทียน และปิดยืนยันทิศทางด้วยสีแท่งกลับตัว (เช่น เขียวสำหรับ SPRING)
  คะแนนความมั่นใจ C_strategy = 0.90
  คาดหวัง: ราคาเกิดการเด้งกลับทันทีในแท่ง M5 ถัดไป เพื่อหาศูนย์กลางของกรอบ Sideway เดิม

Normal Fakeout (สัญญาณระดับทั่วไป):
  ราคาค่อยๆ ขยับข้ามเส้นแนวรับ/ต้าน แล้วปิดตัวแบบเฉียดฉิว โดยดึงกลับทิ้งไส้ยาวปานกลาง (45%-55%) และปิดสีแท่งไม่เป็นใจ (เช่น แดงสำหรับ SPRING)
  คะแนนความมั่นใจ C_strategy = 0.80
  คาดหวัง: ราคาอาจเด้งกลับแต่มีความเสี่ยงที่จะทดสอบซ้ำ (Retest) หรือสไลด์เลื่อนออกข้าง

False Rejection (การเบรคจริง):
  ราคาปิดทะลุขอบแนวรับหรือต้านแบบชัดเจนโดยไม่มีแรงดึงกลับ
  ระบบจะคัดกรองสัญญาณนี้ออกทันทีเนื่องจากไม่ผ่านเกณฑ์การปิดข้ามเส้น (Close > Support สำหรับ CALL หรือ Close < Resistance สำหรับ PUT)

******************************************************************************--
#### 9. AUDIT REQUIREMENTS
******************************************************************************--
ระบบบันทึกผล WORM Database ต้องจัดเก็บข้อมูลเหล่านี้ทุกครั้งที่ทำการประเมิน:
  - audit_id             : รหัสตรวจสอบเฉพาะรอบการประเมิน (UUIDv4)
  - timestamp            : เวลาประเมินผลของระบบ (UTC)
  - symbol               : คู่เงินหรือสินทรัพย์
  - market_state         : สภาวะตลาด ณ เวลาประเมิน
  - state_age            : อายุรอบตลาด
  - triggered_level      : พิกัดระดับ S&R ที่เกิด Fakeout
  - lower_wick_pct       : อัตราส่วนความยาวไส้ล่างต่อความสูงรวม
  - upper_wick_pct       : อัตราส่วนความยาวไส้บนต่อความสูงรวม
  - current_candle_ohlcv : ค่า OHLCV ของแท่งเทียน M5[-1]
  - raw_confidence       : คะแนนความเชื่อมั่นดิบ (80 หรือ 90)
  - entry_score          : คะแนนสุดท้ายเข้าซื้อขาย
  - block_score          : คะแนนบล็อกสัญญาณ (0 หรือ 100)
  - c_strategy           : ความมั่นใจเชิงกลยุทธ์ (0.0-1.0)
  - eligible             : สถานะผ่านเงื่อนไขการประเมินเบื้องต้น (true/false)
  - action               : ทิศทางการส่งคำสั่ง (CALL / PUT / NO_SETUP)
  - fail_reason_code     : รหัสระบุสาเหตุข้อขัดข้อง

******************************************************************************--
#### 10. OUTPUT CONTRACT (FROZEN SCHEMA)
******************************************************************************--
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_SRFakeoutRejection_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "sr_fakeout_rejection" },
    "eligible":            { "type": "BOOLEAN" },
    "action":              { "type": "STRING", "enum": ["CALL", "PUT", "NO_SETUP"] },
    "entry_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "block_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "strategy_confidence": { "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "direction_confidence":{ "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "expected_state":      { "type": "STRING",
                             "enum": ["SIDEWAY_RANGE", "REVERSAL_FORMING",
                                      "DISTRIBUTION", "TRANSITIONAL", "UNCLEAR"] },
    "fail_reason_code":    { "type": "STRING" },
    "audit_id":            { "type": "STRING",
                             "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[4][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$" },
    "expiry":              { "type": "STRING", "const": "M5" },
    "details": {
      "type": "OBJECT",
      "properties": {
        "level_touched":        { "type": "NUMBER" },
        "pattern_detected":     { "type": "STRING" },
        "calculated_wick_ratio":{ "type": "NUMBER" }
      },
      "required": ["level_touched", "pattern_detected", "calculated_wick_ratio"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}

---

### ?? STRATEGY: Reversal Group B BB RSI CONFLUENCE

# FINAL SPECIFICATION: BB RSI CONFLUENCE (bb_rsi_confluence)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

******************************************************************************--
#### 1. STRATEGY OVERVIEW
******************************************************************************--
ชื่อกลยุทธ์:
  Bollinger Bands + RSI Confluence
  (Bollinger Bands and RSI Confluence Extreme Reversal Strategy)

วัตถุประสงค์:
  ตรวจจับจุดกลับตัวรุนแรง (Extreme Reversal) บนแท่งเทียน M5 ล่าสุด
  เมื่อราคาปิดทะลุขอบนอกของ Bollinger Bands ร่วมกับตัวบ่งชี้ RSI(7) ที่อยู่ในสภาวะ Overbought/Oversold
  และยืนยันด้วยการสัมผัสพิกัดแนวรับ/แนวต้านในอดีต (Local Support/Resistance)
  ส่งสัญญาณ ณ วินาทีเปิดของแท่งถัดไปทันที โดยกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — มีสิทธิ์สร้างสัญญาณหลักด้วยตัวเองจากการเกิด Confluence เชิงโครงสร้างราคาและ Momentum

ประเภทสัญญาณ:
  Reversal — กลับตัวระยะสั้นภายใน 1 แท่ง M5 (5 นาที)

Market States ที่เหมาะสม:
  SIDEWAY_RANGE    — แนวรับ/ต้านชัดเจน ราคาเด้งในกรอบและแบนด์       [★★★★★]
  REVERSAL_FORMING — เกิดการปฏิเสธราคาบริเวณขอบแบนด์ชัดเจน      [★★★★★]
  DISTRIBUTION     — ราคาแตะขอบบนของกรอบสะสมเตรียมกลับตัว       [★★★★★]
  TRANSITIONAL     — ใช้ได้แต่ลดน้ำหนัก Entry Score 30%          [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  TRENDING_STRONG   — ราคาวิ่งเกาะขอบแบนด์เหนียวแน่น (Band Walking) โอกาสแพ้สูงมาก
  BREAKOUT_EMERGING — ราคากำลังฉีกแบนด์ทะลุแนวต้าน/รับแบบรุนแรง
  ACCUMULATION      — ตลาดกำลังบีบตัวแคบ (Squeeze) เพื่อรอระเบิดทิศทาง
  TRENDING_WEAK     — แนวโน้มอ่อนแรงแต่ยังไหลไปตามทิศทางแบนด์
  LIQUIDITY_VOID    — ปริมาณซื้อขายต่ำเกินไป แบนด์แคบและราคาไม่มีนัยสำคัญ
  CHOPPY_UNCERTAIN  — ตลาดผันผวนสับสนในกรอบแคบเกินไป
  UNCLEAR           — สภาวะตลาดคลุมเครือ

******************************************************************************--
#### 2. REQUIRED INPUTS
******************************************************************************--
1. M5 OHLCV Candles (ย้อนหลัง 100 แท่ง)
   เหตุผล: ใช้คำนวณ Bollinger Bands, RSI(7), พิกัดแนวรับ/ต้านท้องถิ่น (Local S/R) และ ATR

2. ATR(14) บน M5
   เหตุผล: Normalize ระยะการคำนวณและเกณฑ์การยอมรับค่าเผื่อให้ไม่ขึ้นกับคู่เงิน

3. Bollinger Bands ( window, std_dev )
   เหตุผล: กำหนดขอบเขตความผันผวนทางสถิติของราคาในรอบเวลาที่กำหนด (14 หรือ 20)

4. RSI(7) พร้อม Wilder's Smoothing
   เหตุผล: วัดแรงขับเคลื่อน (Momentum) ในระยะสั้นเพื่อหาจุด Overbought/Oversold

5. Local Support & Resistance (คำนวณจาก Swing High/Low ย้อนหลังช่วง 10 แท่งก่อนหน้า)
   เหตุผล: ตรวจจับแนวราคาที่มีนัยสำคัญซึ่งอยู่นอกเขตสัญญาณ 3 แท่งล่าสุด

6. Average Volume (เฉลี่ย 20 แท่ง M5)
   เหตุผล: ตรวจสอบปริมาณซื้อขายประกอบเพื่อกรองการเบรคเอาท์ปลอม

7. Real-Time Tick Feed
   เหตุผล: ตรวจสอบสถานะการเชื่อมต่อและความสมบูรณ์ของราคา ณ วินาทีเปิดออเดอร์

8. Market State + State Age (จาก Intelligence OS)
   เหตุผล: ตรวจสอบสภาวะตลาดตามมาตรฐานความปลอดภัยเพื่อบล็อกสภาวะเทรนด์

9. High Impact News Calendar (+/- 15 นาที)
   เหตุผล: หลีกเลี่ยงความผันผวนที่สูญเสียความแม่นยำทางสถิติในช่วงข่าวสำคัญ

******************************************************************************--
#### 3. ENTRY CONDITIONS
******************************************************************************--
การประเมินสัญญาณต้องดำเนินการตามลำดับขั้นตอน (Evaluation Pipeline) หากไม่ผ่านขั้นตอนใดให้หยุดการทำงานทันที

CONDITION 1 — Market State Eligibility
  ตรวจเช็คว่า Market State ปัจจุบันอยู่ในสภาวะที่เหมาะสมหรือไม่
  ผ่าน: SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION, TRANSITIONAL
  ไม่ผ่าน: หยุดการทำงานทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — S/R Level Quality Check (S_level Engine)
  คำนวณระดับแนวรับและแนวต้านในอดีต (Local Support & Resistance):
    - local_support = ค่าต่ำสุดของราคา Low ในช่วงแท่งที่ -13 ถึง -4 ( low_prices.iloc[-13:-3].min() )
    - local_resistance = ค่าสูงสุดของราคา High ในช่วงแท่งที่ -13 ถึง -4 ( high_prices.iloc[-13:-3].max() )

  การคำนวณความแข็งแกร่งแนวราคา (S_level_base, สูงสุด 100):
    - C_touch (50 คะแนน): จำนวนครั้งที่ราคาสัมผัสระดับภายในค่าเผื่อ ±0.1*ATR โดยให้สัมผัสละ 25 คะแนน (สูงสุด 50)
    - D_react (30 คะแนน): ระยะการดีดกลับเฉลี่ยหลังสัมผัสแนวเมื่อเทียบกับ ATR (สูงสุด 30)
    - V_profile (20 คะแนน): การทับซ้อนกับโซนปริมาณซื้อขายหนาแน่นย้อนหลัง 100 แท่ง (+20 คะแนน)

  คำนวณการลดทอนคะแนนตามเวลา (Age Decay):
    - S_level = S_level_base * exp(-0.015 * age)
    - age คือจำนวนแท่ง M5 ที่ห่างจากจุดที่เกิดแนวสัมผัสล่าสุด
  เกณฑ์การอนุมัติ: S_level ต้องไม่ต่ำกว่า 40 คะแนน
  ไม่ผ่าน → fail_reason_code: LEVEL_TOO_WEAK

CONDITION 3 — Price Touch Local Levels (การสัมผัสแนวราคาใน 3 แท่งล่าสุด)
  สำหรับ CALL (กลับตัวขึ้น):
    - ต้องมีอย่างน้อยหนึ่งแท่งในช่วง 3 แท่งล่าสุด ([-3, -2, -1]) ที่ Low[-k] <= local_support * 1.0002
  สำหรับ PUT (กลับตัวลง):
    - ต้องมีอย่างน้อยหนึ่งแท่งในช่วง 3 แท่งล่าสุด ([-3, -2, -1]) ที่ High[-k] >= local_resistance * 0.9998
  ไม่ผ่าน → fail_reason_code: LEVEL_NOT_TOUCHED

CONDITION 4 — Bollinger Bands Penetration
  สำหรับ CALL:
    - Close[-1] <= Lower Band[-1] (ราคาปิดทะลุหรือสัมผัสขอบล่าง Bollinger Band)
  สำหรับ PUT:
    - Close[-1] >= Upper Band[-1] (ราคาปิดทะลุหรือสัมผัสขอบบน Bollinger Band)
  ไม่ผ่าน → fail_reason_code: BB_PENETRATION_INVALID

CONDITION 5 — RSI Extreme Oversold/Overbought
  สำหรับ CALL:
    - RSI(7)[-1] < config['rsi_oversold'] (เช่น ต่ำกว่า 30 หรือ 35 ตามเงื่อนไขคู่เงิน)
  สำหรับ PUT:
    - RSI(7)[-1] > config['rsi_overbought'] (เช่น สูงกว่า 70 หรือ 65 ตามเงื่อนไขคู่เงิน)
  ไม่ผ่าน → fail_reason_code: RSI_NOT_EXTREME

CONDITION 6 — Broker Feed Validity
  ตรวจสอบอัตราการส่งข้อมูลราคาของโบรกเกอร์ (Tick Update Rate) ต้องมีการขยับราคาภายใน 10 วินาทีล่าสุด
  ไม่ผ่าน → fail_reason_code: BROKER_FEED_FREEZE

******************************************************************************--
#### 4. ENTRY SCORE LOGIC
******************************************************************************--
Entry Score (สเกล 0–100) คำนวณจากค่าน้ำหนัก 4 ปัจจัย รวม 100% ดังนี้:

Factor 1 — RSI Deviation Factor (F_rsi) น้ำหนัก 30%
  วัดความลึกของ RSI(7) ที่เกินเกณฑ์ขีดสุดเข้าไป
  สำหรับ CALL:
    - R_rsi = rsi_oversold_threshold - RSI(7)[-1]
    - IF RSI(7)[-1] >= rsi_oversold_threshold → F_rsi = 0
    - IF RSI(7)[-1] < rsi_oversold_threshold → F_rsi = Min(100, (R_rsi / rsi_oversold_threshold) * 100 * 3.0)
  สำหรับ PUT:
    - R_rsi = RSI(7)[-1] - rsi_overbought_threshold
    - IF RSI(7)[-1] <= rsi_overbought_threshold → F_rsi = 0
    - IF RSI(7)[-1] > rsi_overbought_threshold → F_rsi = Min(100, (R_rsi / (100 - rsi_overbought_threshold)) * 100 * 3.0)

Factor 2 — Bollinger Bands Penetration Factor (F_bb) น้ำหนัก 30%
  วัดระยะของราคาปิดที่เบี่ยงเบนทะลุขอบนอกของ Bollinger Band normalized ด้วย ATR
  - D_pen = |Close[-1] - BB_Band[-1]| / ATR_M5  (BB_Band คือ Lower Band สำหรับ CALL และ Upper Band สำหรับ PUT)
  - F_bb = Min(100, (D_pen / 0.3) * 100)
  (หมายเหตุ: หากราคาปิดทะลุขอบแบนด์ไป 0.3 เท่าของ ATR จะได้คะแนนเต็ม)

Factor 3 — Level Contact Precision Factor (F_sr) น้ำหนัก 20%
  วัดความแม่นยำในการทดสอบแนวรับ/ต้านใน 3 แท่งล่าสุด
  - D_sr = Min( |Low[-k] - local_support| สำหรับ k=1,2,3 ) / ATR_M5 (สำหรับ CALL)
  - D_sr = Min( |High[-k] - local_resistance| สำหรับ k=1,2,3 ) / ATR_M5 (สำหรับ PUT)
  - F_sr = Max(0, 100 - (D_sr / 0.1) * 100)
  (หมายเหตุ: ยิ่งราคาดิ่งไปสัมผัสใกล้แนวมากที่สุด คะแนนส่วนนี้ยิ่งเข้าใกล้ 100)

Factor 4 — Volumetric Confirmation Factor (F_vol) น้ำหนัก 20%
  ประเมินความมั่นคงผ่านปริมาณซื้อขายเปรียบเทียบกับค่าเฉลี่ย
  - R_vol = Volume[-1] / Avg_Volume(20)
  - F_vol = Min(100, Max(0, ((R_vol - 0.5) / 1.5) * 100))

สูตรคำนวณคะแนนดิบ (Raw Entry Score):
  Raw Entry Score = (0.30 * F_rsi) + (0.30 * F_bb) + (0.20 * F_sr) + (0.20 * F_vol)

การปรับตามวงจรอายุของสภาวะตลาด (State Lifecycle Adjustment):
  - Fresh / Active   → ใช้ Raw Entry Score ตรง
  - Late             → Entry Score = Raw Entry Score * 0.80
  - Exhausted        → บล็อกสัญญาณทันที (Block Score = 100)
  - TRANSITIONAL     → ปรับลดคะแนนลงโดยคุณตัวคูณพิเศษ: Entry Score = Raw Entry Score * 0.70

******************************************************************************--
#### 5. BLOCK SCORE LOGIC
******************************************************************************--
Block Score (สเกล 0–100) ใช้สำหรับสะกัดกั้นสัญญาณที่มีความเสี่ยงสูง

*** SOFT BLOCK FACTORS (สะสมคะแนนเพิ่มความเสี่ยง) ***
  SF-1: ATR ปัจจุบัน > 1.8 * Average ATR(20)
        → +35 คะแนน (สภาวะความผันผวนที่สูงเกินกว่าโครงสร้างเชิงสถิติทั่วไป)
  SF-2: Close[-1] ปิดห่างจาก Local Level มากกว่า 0.3 * ATR_M5
        → +25 คะแนน (ราคาไม่สามารถประคองตัวอยู่ใกล้แนวระดับสำคัญได้)
  SF-3: Market State เป็น TRANSITIONAL หรือ DISTRIBUTION
        → +20 คะแนน (ความไม่แน่นอนในการสลับรูปแบบสภาวะตลาด)

*** HARD BLOCK FACTORS (Block Score = 100 ทันที) ***
  HB-1: Market State เป็น TRENDING_STRONG หรือ BREAKOUT_EMERGING
        → Block Score = 100
  HB-2: ปริมาณซื้อขายเกินขีดสุดโดยปิดทะลุขอบนอกและเปิดห่างด้วยช่องว่างสเปรด (Gap)
        (Volume[-1] > 2.0 * Avg_Volume(20) และ Close[-1] ทะลุนอก Bollinger Band เกิน 0.5*ATR)
        → Block Score = 100
  HB-3: มีแท่งเทียนก่อนหน้าเกิดทิศทางตรงกันข้ามที่มีไส้เทียนยาวเด่นชัดเจนข่มทิศทางเป้าหมาย
        (Wick_opposite > Wick_target * 1.5)
        → Block Score = 100
  HB-4: ช่วงเวลามีข่าวรุนแรง High Impact News (ในกรอบ +/- 15 นาที)
        → Block Score = 100
  HB-5: วงจรสภาวะตลาดเสื่อมสภาพ (State Lifecycle = Exhausted)
        → Block Score = 100
  HB-6: ไม่มีการอัปเดตราคาจากฟีดเกินกว่า 10 วินาที (Broker Feed Freeze)
        → Block Score = 100

สูตร Block Score สุดท้าย:
  IF มี Hard Block ใดๆ เกิดขึ้น → Block Score = 100
  ELSE → Block Score = Min(100, Sum(คะแนนของ Soft Block ที่พบ))

******************************************************************************--
#### 6. STRATEGY CONFIDENCE
******************************************************************************--
C_strategy คำนวณในรูปของค่าต่อเนื่องทางคณิตศาสตร์ (สเกล 0.0–1.0):
  C_strategy = (0.40 * S_rsi) + (0.40 * S_bb) + (0.20 * S_sr)

คะแนนย่อย (Sub-scores):
  1. RSI Extent Score (S_rsi):
     - สำหรับ CALL: S_rsi = Min(1.0, (rsi_oversold_threshold - RSI(7)[-1]) / 10.0)
     - สำหรับ PUT: S_rsi = Min(1.0, (RSI(7)[-1] - rsi_overbought_threshold) / 10.0)
     (หมายเหตุ: หาก RSI ลึกเข้าไปในแนวเขตเกินกว่าเกณฑ์ 10 จุดขึ้นไป จะได้คะแนนเต็ม 1.0)

  2. Bollinger Band Penetration Score (S_bb):
     - S_bb = Min(1.0, |Close[-1] - BB_Band[-1]| / (0.20 * ATR_M5))
     (หมายเหตุ: ยิ่งราคาปิดทะลุแบนด์ออกไปมากกว่า 0.2 เท่าของ ATR จะได้คะแนนเต็ม 1.0)

  3. Level Contact Score (S_sr):
     - S_sr = Max(0.0, 1.0 - (D_sr / 0.08))
     (หมายเหตุ: ระยะห่างที่สัมผัสแนวต่ำกว่า 0.08 * ATR_M5 จะสะท้อนคะแนนความแม่นยำสูงขึ้น)

ตัวอย่างการคำนวณ (CALL สำหรับ EURUSD):
  RSI(7) ปัจจุบัน = 28.0 (เกณฑ์คือ 35), Close = 1.08500, Lower BB = 1.08510, ATR = 0.00100, local_support = 1.08495, Low[-1] = 1.08496
  - S_rsi = Min(1.0, (35.0 - 28.0) / 10.0) = 0.70
  - S_bb = Min(1.0, |1.08500 - 1.08510| / (0.20 * 0.00100)) = Min(1.0, 0.00010 / 0.00020) = 0.50
  - D_sr = |1.08496 - 1.08495| / 0.00100 = 0.01
  - S_sr = Max(0.0, 1.0 - (0.01 / 0.08)) = 0.875
  - C_strategy = (0.40 * 0.70) + (0.40 * 0.50) + (0.20 * 0.875) = 0.28 + 0.20 + 0.175 = 0.655

******************************************************************************--
#### 7. FAIL CONDITIONS
******************************************************************************--
กลยุทธ์จะกำหนดให้สัญญาณเป็น NO_SETUP ทันทีเมื่อเกิดประเด็นต่อไปนี้:
  MARKET_STATE_BLOCKED      : สภาวะตลาดไม่อยู่ในกลุ่มที่อนุญาต
  LEVEL_TOO_WEAK            : คะแนนความแข็งแกร่งของแนวราคาสะสม S_level < 40
  LEVEL_NOT_TOUCHED         : ไม่มีราคาใน 3 แท่งล่าสุดสัมผัสแนวราคา
  BB_PENETRATION_INVALID    : ราคาปิดไม่แตะหรือทะลุขอบนอกของแบนด์ตามทิศทาง
  RSI_NOT_EXTREME           : RSI(7) ไม่ผ่านเงื่อนไขขอบเขตการกลับตัวขั้นต่ำ
  BROKER_FEED_FREEZE        : การหน่วงค้างหรือขาดหาย of สัญญาณราคามากกว่า 10 วินาที
  NEWS_BLACKOUT             : อยู่ในรัศมีช่วงเวลาเผยแพร่ข่าวเศรษฐกิจระดับสูง +/- 15 นาที

******************************************************************************--
#### 8. EXPECTED BEHAVIOR
******************************************************************************--
Strong Confluence (สัญญาณกลับตัวคุณภาพสูง):
  ราคาปิดทะลุผ่านขอบของ Bollinger Band ชัดเจนและสัมผัสแนวรับ/แนวต้านที่แข็งแกร่ง (S_level > 70) 
  โดย RSI(7) เข้าลึกในโซนวิกฤต (เช่น <20 สำหรับ CALL หรือ >80 สำหรับ PUT)
  ค่า C_strategy > 0.80, Entry Score > 75
  คาดหวัง: ราคาดีดตัวกลับเข้ามาในแบนด์และปิดทิศทางตรงกันข้ามในแท่งถัดไปอย่างรวดเร็ว

Weak Confluence (สัญญาณกลับตัวคุณภาพต่ำ):
  ราคาเกือบไม่พ้นขอบแบนด์หรือขอบแบนด์ค่อนข้างแคบ แนวรับ/แนวต้านมีอายุนานเกินไป (S_level 40-55)
  ค่า C_strategy 0.50–0.70, Entry Score 60–74
  คาดหวัง: ราคาอาจเคลื่อนตัวออกด้านข้าง (Sideway) หรือเบรกเอาท์ผ่านแนวได้ง่าย

False Confluence (Breakout / Trend Start):
  ราคามีลักษณะการวิ่งไล่ราคาแบบ Momentum สูง ดึงขอบแบนด์ให้ฉีกขยายตัวกว้างขึ้นและราคาปิดนอกแบนด์ต่อเนื่อง
  ระบบจะสามารถดักจับสภาวะนี้ได้ทางโครงสร้างเทรนด์และการบล็อก Volume ใน Condition 1 & 5
  ผลลัพธ์: สัญญาณถูกบล็อกทันที (fail_reason_code: MARKET_STATE_BLOCKED)

******************************************************************************--
#### 9. AUDIT REQUIREMENTS
******************************************************************************--
บันทึกข้อมูลและประทับเวลาลงใน WORM Database ทุกครั้งที่มีการประเมินสัญญาณ:
  - audit_id              : UUIDv4 อ้างอิงสิทธิ์เฉพาะของรอบสัญญาณ
  - timestamp             : วันที่และเวลาประเมินผลในรูปแบบมาตรฐาน UTC
  - symbol                : ชื่อคู่เงินเป้าหมาย
  - market_state          : สภาวะตลาดและอายุของสภาวะตลาด
  - candle_ohlcv          : ข้อมูลราคาทั้งหมดของแท่ง M5 ย้อนหลัง 100 แท่ง
  - atr_m5                : ค่า ATR ของรอบเวลานั้น
  - local_support         : พิกัดแนวรับที่ใช้อ้างอิง
  - local_resistance      : พิกัดแนวต้านที่ใช้อ้างอิง
  - s_level_final         : คะแนนระดับความแข็งแกร่งของแนวราคาหลังคิดค่าเสื่อมถอย
  - rsi_value             : ค่าดัชนี RSI(7) ล่าสุด
  - upper_band            : พิกัดขอบบน Bollinger Band
  - lower_band            : พิกัดขอบล่าง Bollinger Band
  - f_rsi                 : คะแนนจากปัจจัย RSI
  - f_bb                  : คะแนนจากปัจจัย Bollinger Bands
  - f_sr                  : คะแนนจากปัจจัยแนวรับ/แนวต้าน
  - f_vol                 : คะแนนจากปริมาณซื้อขายสะสม
  - entry_score           : คะแนนเข้าซื้อขายสุดท้ายที่ผ่านตัวคูณสภาวะแล้ว
  - block_score           : คะแนนการบล็อกรวม
  - c_strategy            : ความมั่นใจสุดท้ายของกลยุทธ์ (Strategy Confidence)
  - eligible              : ผลความเหมาะสมของสัญญาณ (true/false)
  - action                : ทิศทางการส่งคำสั่ง (CALL / PUT / NO_SETUP)
  - fail_reason_code      : รหัสที่ล้มเหลวในการส่งสัญญาณ

******************************************************************************--
#### 10. OUTPUT CONTRACT (FROZEN SCHEMA)
******************************************************************************--
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_BBRSIConfluence_M5_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "bb_rsi_confluence" },
    "eligible":            { "type": "BOOLEAN" },
    "action":              { "type": "STRING", "enum": ["CALL", "PUT", "NO_SETUP"] },
    "entry_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "block_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "strategy_confidence": { "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "direction_confidence":{ "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "expected_state":      { "type": "STRING",
                             "enum": ["SIDEWAY_RANGE","REVERSAL_FORMING",
                                      "DISTRIBUTION","TRANSITIONAL","UNCLEAR"] },
    "fail_reason_code":    { "type": "STRING" },
    "audit_id":            { "type": "STRING",
                             "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[4][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$" },
    "expiry":              { "type": "STRING", "const": "M5" },
    "details": {
      "type": "OBJECT",
      "properties": {
        "level_touched":        { "type": "NUMBER" },
        "pattern_detected":     { "type": "STRING" },
        "calculated_wick_ratio":{ "type": "NUMBER" }
      },
      "required": ["level_touched", "pattern_detected", "calculated_wick_ratio"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}

---

### ?? STRATEGY: Reversal Group B RSI EXTREME BOUNCE

# FINAL SPECIFICATION: RSI EXTREME BOUNCE (rsi_extreme_bounce)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

******************************************************************************--
#### 1. STRATEGY OVERVIEW
******************************************************************************--
ชื่อกลยุทธ์:
  RSI Extreme Bounce
  (RSI Extreme Bounce Reversal Strategy)

วัตถุประสงค์:
  ตรวจจับสภาวะกลับตัวฉับพลันที่มีความน่าจะเป็นสูงมาก (Ultra-Extreme Bounce) บนแท่งเทียน M5 ล่าสุด
  เมื่อตัวบ่งชี้ RSI(3) ดีดตัวจากพื้นที่ระดับขีดสุด (น้อยกว่า 10 หรือมากกว่า 90) กลับเข้ามาในขอบเขตการเทรดปกติ
  โดยได้รับการยืนยันการเด้งจากแนวโมเมนตัมของ Stochastic(5,3,3) และการทะลุขอบนอกของ Bollinger Band(10, 2.0)
  ส่งสัญญาณ ณ วินาทีเปิดของแท่งถัดไปทันที โดยกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — สร้างสัญญาณกลับตัวประสิทธิภาพสูงแต่มีความถี่ต่ำ (High Accuracy, Low Frequency) จากการบรรจบกันของสภาวะสุดขีดของแนวต้านโมเมนตัมและราคา

ประเภทสัญญาณ:
  Reversal — กลับตัวระยะสั้นภายใน 1 แท่ง M5 (5 นาที)

Market States ที่เหมาะสม:
  SIDEWAY_RANGE    — แนวราคาเด้งไปมาในกรอบของ Bollinger Bands   [★★★★★]
  REVERSAL_FORMING — ราคาเริ่มหมดแรงและเกิดการดีดตัวกลับจากโซนขีดสุด [★★★★★]
  DISTRIBUTION     — สภาวะการแจกจ่ายหุ้นที่มีความผันผวนสูงแถบขีดสุด   [★★★★★]
  TRANSITIONAL     — ใช้ได้แต่ลดน้ำหนัก Entry Score 30%          [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  TRENDING_STRONG   — สภาวะตลาดมีเทรนด์รุนแรง โมเมนตัม RSI จะค้างในระดับขีดสุดต่อเนื่อง
  BREAKOUT_EMERGING — ราคาตัดทะลุขอบแบนด์และเบรคเอาท์ยาวอย่างรุนแรง
  ACCUMULATION      — ตลาดบีบอัดตัวแคบ รอระเบิดทิศทาง
  TRENDING_WEAK     — เทรนด์ค่อนข้างชัดเจนแต่มีทิศทางเอียงไปข้างใดข้างหนึ่ง
  LIQUIDITY_VOID    — ขาดปริมาณซื้อขายทำให้โครงสร้าง Bollinger Band ผิดเพี้ยน
  CHOPPY_UNCERTAIN  — ราคาขึ้นลงสะเปะสะปะโดยไร้ทิศทางและสอดคล้องกับอินดิเคเตอร์
  UNCLEAR           — ข้อมูลอินดิเคเตอร์และราคาขัดแย้งกันเอง

******************************************************************************--
#### 2. REQUIRED INPUTS
******************************************************************************--
1. M5 OHLCV Candles (ย้อนหลัง 100 แท่ง)
   เหตุผล: ใช้คำนวณ RSI(3), Stochastic(5,3,3), Bollinger Bands(10, 2.0) และ ATR(14)

2. ATR(14) บน M5
   เหตุผล: Normalize ระยะการคำนวณและเกณฑ์เปรียบเทียบในแบนด์ให้สม่ำเสมอในทุกสินทรัพย์

3. RSI(3) พร้อม Wilder's Smoothing (ช่วงเวลาระยะสั้นมาก)
   เหตุผล: หาการเปลี่ยนสภาวะสวิงราคาสุดโต่งในกรอบสั้นระดับ 1-2 แท่งเทียน

4. Fast Stochastic Oscillator (5, 3, 3)
   เหตุผล: ยืนยันสภาวะ Oversold/Overbought ของโมเมนตัมในแท่งปัจจุบัน

5. Bollinger Bands (10, 2.0)
   เหตุผล: ระบุจุดพิกัดขีดจำกัดความผันผวนของราคาปิดแท่งย้อนหลังแบบรวดเร็ว

6. Average Volume (เฉลี่ย 20 แท่ง M5)
   เหตุผล: กรองสัญญาณหลอกในช่วงที่ปริมาณซื้อขายเบาบางหรือเบรคเอาท์รุนแรง

7. Real-Time Tick Feed
   เหตุผล: ตรวจความเสถียรของฟีดโบรกเกอร์และป้องกันออเดอร์ค้างสะสม

8. Market State + State Age (จาก Intelligence OS)
   เหตุผล: บล็อกการเข้าเทรดสวนแนวโน้มขนาดใหญ่

9. High Impact News Calendar (+/- 15 นาที)
   เหตุผล: ป้องกันความเสียหายจากการสเปรดขยายตัวและการไหลผ่านแนวราคาช่วงข่าวเศรษฐกิจ

******************************************************************************--
#### 3. ENTRY CONDITIONS
******************************************************************************--
ลำดับการตรวจสอบเงื่อนไข (Evaluation Pipeline) โดยต้องผ่านทุกเงื่อนไขอย่างราบรื่น:

CONDITION 1 — Market State Eligibility
  ตรวจเช็คว่า Market State ปัจจุบันจัดอยู่ใน Suitable States
  ผ่าน: SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION, TRANSITIONAL
  ไม่ผ่าน: หยุดทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — RSI(3) Extreme Bounce Reentry
  สำหรับ CALL:
    - RSI(3)[-2] < 10 (แท่งก่อนหน้าอยู่ในสภาวะดิ่งสุดขีด)
    - RSI(3)[-1] >= 10 (แท่งปัจจุบันขยับตัวกลับเข้ามาข้ามเกณฑ์ขีดสุด)
  สำหรับ PUT:
    - RSI(3)[-2] > 90 (แท่งก่อนหน้าอยู่ในสภาวะพีคสุดขีด)
    - RSI(3)[-1] <= 90 (แท่งปัจจุบันย่อตัวกลับเข้ามาใต้เกณฑ์ขีดสุด)
  ไม่ผ่าน → fail_reason_code: RSI_EXTREME_BOUNCE_NOT_MET

CONDITION 3 — Stochastic Momentum Confirmation
  สำหรับ CALL:
    - Stochastic %K[-1] < 20 (ตัวชี้วัดความเร็วปัจจุบันสะท้อนพลังฝั่งซื้อยังไม่เร่งเกินไปและอยู่ในขอบเขตสะสมพลัง)
  สำหรับ PUT:
    - Stochastic %K[-1] > 80 (ตัวชี้วัดความเร็วปัจจุบันสะท้อนพลังฝั่งขายยังไม่กดตัวต่ำเกินไป)
  ไม่ผ่าน → fail_reason_code: STOCHASTIC_CONFIRMATION_FAILED

CONDITION 4 — Bollinger Bands Penetration on Previous Candle
  คำนวณ Bollinger Bands(10, 2.0) บนแท่งปัจจุบัน:
    - MA_10 = ค่าเฉลี่ยเคลื่อนที่ 10 แท่งล่าสุด
    - Std_10 = ส่วนเบี่ยงเบนมาตรฐาน (ddof=0)
    - Upper Band = MA_10 + 2.0 * Std_10
    - Lower Band = MA_10 - 2.0 * Std_10

  สำหรับ CALL:
    - Close[-2] <= Lower Band[-1] (ราคาปิดของแท่งก่อนหน้าดิ่งหลุดขอบล่างของแถบแบนด์ล่าสุด)
  สำหรับ PUT:
    - Close[-2] >= Upper Band[-1] (ราคาปิดของแท่งก่อนหน้าดึงตัวหลุดขอบบนของแถบแบนด์ล่าสุด)
  ไม่ผ่าน → fail_reason_code: BB_PREV_CLOSE_NOT_PENETRATED

CONDITION 5 — Broker Feed Validity
  ราคาปัจจุบันต้องมีระดับการตอบสนองภายใน 10 วินาทีจากเซิร์ฟเวอร์
  ไม่ผ่าน → fail_reason_code: BROKER_FEED_FREEZE

******************************************************************************--
#### 4. ENTRY SCORE LOGIC
******************************************************************************--
Entry Score (สเกล 0–100) ประเมินความแข็งแกร่งของสัญญาณเด้งจาก 4 ปัจจัยถ่วงน้ำหนักดังนี้:

Factor 1 — RSI Reentry Slope (F_rsi_slope) น้ำหนัก 35%
  วัดอัตราความชันการเด้งของ RSI(3) ในช่วง 2 แท่งล่าสุด
  - D_rsi = |RSI(3)[-1] - RSI(3)[-2]|
  - F_rsi_slope = Min(100, (D_rsi / 15.0) * 100)
  (หมายเหตุ: การดีดกลับของ RSI เกิน 15 จุดขึ้นไปสะท้อนกำลังดีดกลับสูงสุด ได้ 100 คะแนน)

Factor 2 — Stochastic Deepness (F_stoch) น้ำหนัก 25%
  วัดระดับความลึกของ Stochastic %K ในโซนกลับตัว
  สำหรับ CALL:
    - F_stoch = Max(0, 100 - (Stochastic_%K[-1] / 20.0) * 100)
  สำหรับ PUT:
    - F_stoch = Max(0, 100 - ((100.0 - Stochastic_%K[-1]) / 20.0) * 100)

Factor 3 — Bollinger Band Previous Penetration Depth (F_bb_prev) น้ำหนัก 20%
  วัดความลึกที่ราคา Close[-2] แทงทะลุออกไปนอกแบนด์
  สำหรับ CALL:
    - D_bb = (Lower_Band[-1] - Close[-2]) / ATR_M5
    - IF Close[-2] > Lower_Band[-1] → F_bb_prev = 0
    - ELSE → F_bb_prev = Min(100, (D_bb / 0.25) * 100)
  สำหรับ PUT:
    - D_bb = (Close[-2] - Upper_Band[-1]) / ATR_M5
    - IF Close[-2] < Upper_Band[-1] → F_bb_prev = 0
    - ELSE → F_bb_prev = Min(100, (D_bb / 0.25) * 100)

Factor 4 — Volumetric Confirmation (F_vol) น้ำหนัก 20%
  วัดสัดส่วนการเร่งของปริมาณซื้อขาย ณ แท่งกลับตัว
  - R_vol = Volume[-1] / Avg_Volume(20)
  - F_vol = Min(100, Max(0, ((R_vol - 0.5) / 1.5) * 100))

สูตรคำนวณคะแนนดิบ (Raw Entry Score):
  Raw Entry Score = (0.35 * F_rsi_slope) + (0.25 * F_stoch) + (0.20 * F_bb_prev) + (0.20 * F_vol)

การปรับลดคะแนนตามสภาวะและวงจรอายุตลาด (State Lifecycle Adjustment):
  - Fresh / Active   → ใช้ Raw Entry Score ตรง
  - Late             → Entry Score = Raw Entry Score * 0.80
  - Exhausted        → บล็อกสัญญาณทันที (Block Score = 100)
  - TRANSITIONAL     → Entry Score = Raw Entry Score * 0.70

******************************************************************************--
#### 5. BLOCK SCORE LOGIC
******************************************************************************--
Block Score (สเกล 0–100) ดำเนินการบล็อกออเดอร์ความเสี่ยงสูง

*** SOFT BLOCK FACTORS (สะสมคะแนนเพิ่มความเสี่ยง) ***
  SF-1: ATR ปัจจุบัน > 1.8 * Average ATR(20)
        → +30 คะแนน (ตลาดกำลังขยายความผันผวนสูงเกินไป เสี่ยงเกิดกระชากราคา)
  SF-2: สัญญาณ Stochastic %K และ %D มีทิศทางสวนทางกันในจังหวะเด้ง
        (เช่น สำหรับ CALL: %K[-1] < %D[-1] หรือ สำหรับ PUT: %K[-1] > %D[-1])
        → +25 คะแนน (ความเฉื่อยของโมเมนตัมขัดแย้งกับการกลับตัวเรียลไทม์)
  SF-3: Market State อยู่ในกลุ่ม TRANSITIONAL
        → +15 คะแนน

*** HARD BLOCK FACTORS (Block Score = 100 ทันที) ***
  HB-1: Market State เป็น TRENDING_STRONG หรือ BREAKOUT_EMERGING
        → Block Score = 100
  HB-2: ราคาปิด Close[-2] หลุดนอกแบนด์ลึกมากเกินไปจนเหมือนการระเบิดช่องว่างราคา (Breakout)
        (|Close[-2] - BB_Band[-1]| > 0.5 * ATR_M5)
        → Block Score = 100
  HB-3: มีแท่งก่อนหน้ามีขนาดเนื้อเทียน (Body Size) ยาวมากกว่า 1.5 * ATR (เสี่ยงเป็นแท่งข่าวรุนแรง)
        → Block Score = 100
  HB-4: ข้อมูลโบรกเกอร์ราคาหน่วงเกิดอาการสเปรดและราคาค้าง (Broker Feed Freeze > 10 วินาที)
        → Block Score = 100
  HB-5: วงจรสภาวะตลาดเสื่อมสภาพ (State Lifecycle = Exhausted)
        → Block Score = 100
  HB-6: อยู่ในช่วงประกาศข่าวสารเศรษฐกิจระดับสูง (+/- 15 นาที)
        → Block Score = 100

สูตร Block Score สุดท้าย:
  IF มี Hard Block ใดๆ เกิดขึ้น → Block Score = 100
  ELSE → Block Score = Min(100, Sum(คะแนนของ Soft Block ที่เกิดขึ้นจริง))

******************************************************************************--
#### 6. STRATEGY CONFIDENCE
******************************************************************************--
C_strategy คำนวณแบบจำลองค่าต่อเนื่อง (สเกล 0.0–1.0):
  C_strategy = (0.40 * S_rsi_reentry) + (0.30 * S_stoch_conf) + (0.30 * S_bb_prev)

คะแนนย่อย (Sub-scores):
  1. RSI Reentry Score (S_rsi_reentry):
     - S_rsi_reentry = Min(1.0, |RSI(3)[-1] - RSI(3)[-2]| / 12.0)

  2. Stochastic Alignment Score (S_stoch_conf):
     - สำหรับ CALL: S_stoch_conf = Max(0.0, 1.0 - (Stochastic_%K[-1] / 20.0))
     - สำหรับ PUT: S_stoch_conf = Max(0.0, 1.0 - ((100.0 - Stochastic_%K[-1]) / 20.0))

  3. BB Previous Close Penetration Score (S_bb_prev):
     - สำหรับ CALL: S_bb_prev = Min(1.0, Max(0.0, Lower_Band[-1] - Close[-2]) / (0.15 * ATR_M5))
     - สำหรับ PUT: S_bb_prev = Min(1.0, Max(0.0, Close[-2] - Upper_Band[-1]) / (0.15 * ATR_M5))

ตัวอย่างการคำนวณ (CALL):
  RSI(3) ของสองแท่งล่าสุด: 6.0 → 12.0 (ดีดตัวขึ้น), %K = 12.0, Close[-2] = 1.25050, Lower Band[-1] = 1.25070, ATR = 0.00100
  - S_rsi_reentry = Min(1.0, |12.0 - 6.0| / 12.0) = 0.50
  - S_stoch_conf = Max(0.0, 1.0 - (12.0 / 20.0)) = 0.40
  - S_bb_prev = Min(1.0, Max(0.0, 1.25070 - 1.25050) / (0.15 * 0.00100)) = Min(1.0, 0.00020 / 0.00015) = 1.0
  - C_strategy = (0.40 * 0.50) + (0.30 * 0.40) + (0.30 * 1.0) = 0.20 + 0.12 + 0.30 = 0.62

******************************************************************************--
#### 7. FAIL CONDITIONS
******************************************************************************--
ระบบจะส่งผลลัพธ์เป็น NO_SETUP ทันทีในสภาวะดังนี้:
  MARKET_STATE_BLOCKED      : สภาวะตลาดไม่เหมาะสมในการเล่นกลับตัวสั้น
  RSI_EXTREME_BOUNCE_NOT_MET: สัญญาณ RSI(3) ไม่กระโดดออกจากโซนสุดขีดอย่างถูกต้อง
  STOCHASTIC_CONFIRMATION_FAILED: Stochastic %K อยู่ในเกณฑ์เร่งตัวเกินไป
  BB_PREV_CLOSE_NOT_PENETRATED: ราคาปิดแท่งก่อนหน้าไม่สัมผัส/ปิดทะลุขอบนอกของ Bollinger Band ล่าสุด
  BROKER_FEED_FREEZE        : การสื่อสารราคากับโบรกเกอร์ค้างเกิน 10 วินาที
  NEWS_BLACKOUT             : อยู่ในช่วงระยะเตือนข่าวระดับสูง +/- 15 นาที

******************************************************************************--
#### 8. EXPECTED BEHAVIOR
******************************************************************************--
Strong Extreme Bounce (สัญญาณแม่นยำสูง):
  เกิดการกระชากของราคาอย่างแรงหลุด Bollinger Band พร้อม RSI(3) ต่ำกว่า 5 แล้วในแท่งถัดมา
  ราคาปิดดึงกลับอย่างรวดเร็วเข้าสู่แบนด์และ Stochastic ดีดไขว้ทิศทางในเขตลึกมาก
  C_strategy > 0.85, Entry Score > 80
  คาดหวัง: ราคาดีดกลับรวดเร็วและปิดเป็นแท่งสีตรงกันข้ามอย่างสมบูรณ์แบบในแท่งถัดไป

Weak Extreme Bounce (สัญญาณมีความเสี่ยงสูง):
  ราคามีลักษณะการเด้งยึกยัก แบนด์แคบ และ RSI(3) เด้งพ้นแนวแบบเชื่องช้า
  C_strategy 0.50-0.70, Entry Score 60-74
  คาดหวัง: ราคาอาจเด้งสั้นมากแต่กลับมาเคลียร์ออเดอร์แพ้เนื่องจากไม่มีแรงดีดกลับเชิงโครงสร้าง

False Extreme Bounce (Squeeze Breakout):
  ราคาปิดนอกแบนด์แล้วแบนด์เปิดอ้าและไหลไปตามแบนด์เรื่อยๆ โดยที่ Stochastic ลากยาวอยู่ในเขตสุดขีด (Stochastic Cable)
  ดักจับทาง: Hard Block ในข้อ HB-2 และ Condition 1
  ผลลัพธ์: ถูกบล็อกจากการประเมินและตั้งให้เป็น NO_SETUP

******************************************************************************--
#### 9. AUDIT REQUIREMENTS
******************************************************************************--
บันทึกพารามิเตอร์เพื่อตรวจสอบย้อนหลังลงสู่ระบบ WORM Database:
  - audit_id              : UUIDv4 รหัสอ้างอิงของชุดสัญญาณ
  - timestamp             : ประทับวันเวลา UTC
  - symbol                : คู่เงินที่ทำการสแกน
  - market_state          : สถานะของตลาดและอายุสถานะปัจจุบัน
  - candle_ohlcv          : ข้อมูล OHLCV M5 ย้อนหลัง 100 แท่ง
  - rsi3_current          : ค่าดัชนี RSI(3) แท่งปัจจุบัน
  - rsi3_previous         : ค่าดัชนี RSI(3) แท่งก่อนหน้า
  - stoch_k               : ค่า Stochastic %K
  - stoch_d               : ค่า Stochastic %D
  - upper_band            : ขอบบนของ Bollinger Band(10, 2.0)
  - lower_band            : ขอบล่างของ Bollinger Band(10, 2.0)
  - prev_close            : ราคาปิดแท่งก่อนหน้า [-2]
  - f_rsi_slope           : คะแนนองค์ประกอบความชัน RSI
  - f_stoch               : คะแนนองค์ประกอบ Stochastic
  - f_bb_prev             : คะแนนการเจาะทะลุแบนด์แท่งก่อน
  - f_vol                 : คะแนนปริมาณซื้อขาย
  - entry_score           : คะแนนทางสถิติในการเปิดคำสั่งสะสม
  - block_score           : คะแนนบล็อกประเมินความเสี่ยงรวม
  - c_strategy            : ความมั่นใจเชิงระบบ
  - eligible              : ผลอนุมัติเทรด (true/false)
  - action                : ทิศทางการประเมิน (CALL / PUT / NO_SETUP)
  - fail_reason_code      : รหัสวิเคราะห์ข้อผิดพลาด

******************************************************************************--
#### 10. OUTPUT CONTRACT (FROZEN SCHEMA)
******************************************************************************--
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_RSIExtremeBounce_M5_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "rsi_extreme_bounce" },
    "eligible":            { "type": "BOOLEAN" },
    "action":              { "type": "STRING", "enum": ["CALL", "PUT", "NO_SETUP"] },
    "entry_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "block_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "strategy_confidence": { "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "direction_confidence":{ "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "expected_state":      { "type": "STRING",
                             "enum": ["SIDEWAY_RANGE","REVERSAL_FORMING",
                                      "DISTRIBUTION","TRANSITIONAL","UNCLEAR"] },
    "fail_reason_code":    { "type": "STRING" },
    "audit_id":            { "type": "STRING",
                             "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[4][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$" },
    "expiry":              { "type": "STRING", "const": "M5" },
    "details": {
      "type": "OBJECT",
      "properties": {
        "level_touched":        { "type": "NUMBER" },
        "pattern_detected":     { "type": "STRING" },
        "calculated_wick_ratio":{ "type": "NUMBER" }
      },
      "required": ["level_touched", "pattern_detected", "calculated_wick_ratio"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}

---

### ?? STRATEGY: Reversal Group B RSI REVERSAL

# FINAL SPECIFICATION: RSI REVERSAL (rsi_reversal)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

******************************************************************************--
#### 1. STRATEGY OVERVIEW
******************************************************************************--
ชื่อกลยุทธ์:
  RSI Reversal
  (RSI Oversold/Overbought Reentry Reversal Strategy)

วัตถุประสงค์:
  ตรวจจับสัญญาณกลับตัวแบบยืนยันความเร็ว (Momentum Reentry) บนแท่งเทียน M5 ล่าสุด
  เมื่อค่า RSI(7) วิ่งข้ามเกณฑ์ขีดสุด (น้อยกว่า 30 หรือมากกว่า 70) ในแท่งก่อนหน้า แล้วหักหัวกลับเข้ามาในเกณฑ์ปกติ
  ร่วมกับการยืนยันการสัมผัสแนวราคาที่มีนัยสำคัญในอดีต (Local Support/Resistance)
  ส่งสัญญาณ ณ วินาทีเปิดของแท่งถัดไปทันที โดยกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — สร้างสัญญาณกลับตัวพื้นฐาน (Core Reversal) จากการเปลี่ยนผ่านแนวโน้มระยะสั้นในกรอบแนวรับ/แนวต้านสำคัญ

ประเภทสัญญาณ:
  Reversal — กลับตัวระยะสั้นภายใน 1 แท่ง M5 (5 นาที)

Market States ที่เหมาะสม:
  SIDEWAY_RANGE    — ตลาดแกว่งตัวในกรอบรับต้านชัดเจน              [★★★★★]
  REVERSAL_FORMING — เกิดรูปแบบกลับตัวหลังจากราคาออกนอกเกณฑ์     [★★★★★]
  DISTRIBUTION     — ราคาอยู่ในเขตบนสะสมและเตรียมเทขาย          [★★★★★]
  TRANSITIONAL     — ใช้ได้แต่ลดน้ำหนัก Entry Score 30%          [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  TRENDING_STRONG   — ตลาดรันเทรนด์ยาวนาน โมเมนตัมหักหัวกลับได้ยากและสเปรดกว้าง
  BREAKOUT_EMERGING — ราคาตัดผ่านระดับอย่างรุนแรงและเกิดการเริ่มเทรนด์ใหม่
  ACCUMULATION      — ตลาดบีบตัวไม่แสดงแนวรับ/ต้านที่ชัดเจน
  TRENDING_WEAK     — สภาวะมีเทรนด์อ่อนๆ แต่ราคาไม่ยอมกลับทิศทาง
  LIQUIDITY_VOID    — การขาดหายของปริมาณซื้อขายทำให้ตัวชี้วัดเพี้ยน
  CHOPPY_UNCERTAIN  — ราคาเปลี่ยนทิศทางอย่างไร้ระเบียบ
  UNCLEAR           — ค่าอินดิเคเตอร์ขัดแย้งเชิงโครงสร้างราคา

******************************************************************************--
#### 2. REQUIRED INPUTS
******************************************************************************--
1. M5 OHLCV Candles (ย้อนหลัง 100 แท่ง)
   เหตุผล: ใช้คำนวณ RSI(7), แนวรับ/แนวต้าน (Local S/R) และค่า ATR

2. ATR(14) บน M5
   เหตุผล: Normalize ระยะห่างของราคาเทียบกับแนวระดับสำคัญเพื่อวัดพิกัดที่แท้จริง

3. RSI(7) พร้อม Wilder's Smoothing
   เหตุผล: วัดการไหลเข้าออกของแรงซื้อและแรงขาย (Momentum) เพื่อหาจังหวะไหลกลับ (Reentry)

4. Local Support & Resistance (คำนวณจาก Swing Points ช่วงแท่งที่ -13 ถึง -4)
   เหตุผล: ระบุแนวอ้างอิงราคาที่มีประวัติการทดสอบผ่านการยอมรับจากระบบ

5. Average Volume (เฉลี่ย 20 แท่ง M5)
   เหตุผล: ใช้กรองความเสี่ยงในการทะลุผ่าน (Breakout) และยืนยันความแข็งแรงของแท่งยืนยัน

6. Real-Time Tick Feed
   เหตุผล: ตรวจสอบความถูกต้องของค่าราคากับระบบในหน่วยมิลลิวินาที

7. Market State + State Age (จาก Intelligence OS)
   เหตุผล: ใช้ระงับสัญญาณเทรดเมื่อสภาวะตลาดก้าวสู่สถานะมีเทรนด์

8. High Impact News Calendar (+/- 15 นาที)
   เหตุผล: บล็อกการเกิดสัญญาณหลอกในช่วงที่สถิติทางเทคนิคสูญเสียความแม่นยำ

******************************************************************************--
#### 3. ENTRY CONDITIONS
******************************************************************************--
กระบวนการวิเคราะห์สัญญาณเป็นไปตามขั้นตอนการทดสอบ (Evaluation Pipeline) ดังนี้:

CONDITION 1 — Market State Eligibility
  ตรวจสอบสถานะตลาดปัจจุบันใน Suitable States
  ผ่าน: SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION, TRANSITIONAL
  ไม่ผ่าน: หยุดการทำงานทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — S/R Level Quality Check (S_level Engine)
  คำนวณหาแนวรับ/ต้านในอดีต:
    - local_support = ค่าต่ำสุดของราคา Low ในช่วงแท่งที่ -13 ถึง -4
    - local_resistance = ค่าสูงสุดของราคา High ในช่วงแท่งที่ -13 ถึง -4

  การประเมินคะแนนความแข็งแกร่ง (S_level_base, สูงสุด 100):
    - C_touch (50 คะแนน): จำนวนรอบการสัมผัสแนวราคาอดีต โดยให้รอบละ 25 คะแนน (สูงสุด 50)
    - D_react (30 คะแนน): ขนาดการดีดตัวกลับของราคาหลังทดสอบแนวนั้น (สูงสุด 30)
    - V_profile (20 คะแนน): การทับซ้อนกับโซนที่มีปริมาณซื้อขายสะสมสูงสุดย้อนหลัง 100 แท่ง

  การคิดค่าลดทอนเสื่อมเวลา (Age Decay):
    - S_level = S_level_base * exp(-0.015 * age)
    - age คือจำนวนแท่ง M5 ตั้งแต่การทดสอบครั้งล่าสุด
  เกณฑ์อนุมัติ: S_level ต้องมากกว่าหรือเท่ากับ 40 คะแนน
  ไม่ผ่าน → fail_reason_code: LEVEL_TOO_WEAK

CONDITION 3 — Price Touch Local S/R
  ตรวจสอบว่าราคาใน 3 แท่งล่าสุด ([-3, -2, -1]) เคยมีการทดสอบแนวราคาหรือไม่:
    - สำหรับ CALL: Low[-k] <= local_support * 1.0002 (อย่างน้อยหนึ่งแท่ง)
    - สำหรับ PUT: High[-k] >= local_resistance * 0.9998 (อย่างน้อยหนึ่งแท่ง)
  ไม่ผ่าน → fail_reason_code: LEVEL_NOT_TOUCHED

CONDITION 4 — RSI(7) Reentry Crossover
  ตรวจสอบความเร็วโมเมนตัมหักกลับเข้าโซนปกติ:
    - สำหรับ CALL: RSI(7)[-2] < 30 และ RSI(7)[-1] >= 30
    - สำหรับ PUT: RSI(7)[-2] > 70 และ RSI(7)[-1] <= 70
  ไม่ผ่าน → fail_reason_code: RSI_REENTRY_FAILED

CONDITION 5 — Broker Feed Validity
  ต้องรับสัญญาณราคาล่าสุดไม่ห่างเกิน 10 วินาที
  ไม่ผ่าน → fail_reason_code: BROKER_FEED_FREEZE

******************************************************************************--
#### 4. ENTRY SCORE LOGIC
******************************************************************************--
Entry Score (สเกล 0–100) คำนวณจากน้ำหนัก 4 ปัจจัย รวม 100% ดังนี้:

Factor 1 — RSI Reentry Momentum (F_rsi_reentry) น้ำหนัก 40%
  ประเมินความเร็วของการหักกลับเข้าสู่แดนปกติของ RSI(7)
  - D_rsi = |RSI(7)[-1] - RSI(7)[-2]|
  - F_rsi_reentry = Min(100, (D_rsi / 10.0) * 100)
  (หมายเหตุ: หาก RSI ดีดข้ามเกณฑ์มากกว่า 10 จุด จะได้คะแนนเต็ม)

Factor 2 — S/R Touch Accuracy (F_sr) น้ำหนัก 30%
  วัดความชิดของจุดต่ำสุด/สูงสุดเทียบกับระดับราคาสำคัญใน 3 แท่งล่าสุด
  - D_sr = Min( |Low[-k] - local_support| สำหรับ k=1,2,3 ) / ATR_M5 (สำหรับ CALL)
  - D_sr = Min( |High[-k] - local_resistance| สำหรับ k=1,2,3 ) / ATR_M5 (สำหรับ PUT)
  - F_sr = Max(0, 100 - (D_sr / 0.1) * 100)

Factor 3 — Close Proximity Factor (F_close) น้ำหนัก 15%
  วัดระยะห่างราคาปิดล่าสุดเทียบกับแนว เพื่อป้องกันราคาไหลทะลุกว้างเกินไป
  - D_close = |Close[-1] - local_SR| / ATR_M5  (local_SR คือ local_support หรือ local_resistance)
  - F_close = Max(0, 100 - (D_close / 0.2) * 100)

Factor 4 — Volumetric Confirmation (F_vol) น้ำหนัก 15%
  วัดความหนาแน่นปริมาณซื้อขายเปรียบเทียบค่าเฉลี่ย
  - R_vol = Volume[-1] / Avg_Volume(20)
  - F_vol = Min(100, Max(0, ((R_vol - 0.5) / 1.5) * 100))

สูตรคะแนนรวมดิบ (Raw Entry Score):
  Raw Entry Score = (0.40 * F_rsi_reentry) + (0.30 * F_sr) + (0.15 * F_close) + (0.15 * F_vol)

การปรับตามวงจรสภาวะตลาด (State Lifecycle Adjustment):
  - Fresh / Active   → ใช้ Raw Entry Score ตรง
  - Late             → Entry Score = Raw Entry Score * 0.80
  - Exhausted        → บล็อกสัญญาณทันที (Block Score = 100)
  - TRANSITIONAL     → Entry Score = Raw Entry Score * 0.70

******************************************************************************--
#### 5. BLOCK SCORE LOGIC
******************************************************************************--
Block Score (สเกล 0–100) ออกแบบมาเพื่อตรวจจับความเสี่ยงระดับสูง

*** SOFT BLOCK FACTORS (สะสมคะแนนเพิ่มความเสี่ยง) ***
  SF-1: ATR ปัจจุบัน > 1.8 * Average ATR(20)
        → +30 คะแนน (เสี่ยงเกิดการแกว่งตัวกว้างจนราคาทะลุแนว)
  SF-2: Volume[-1] > 2.0 * Average Volume(20)
        → +25 คะแนน (ความต้องการซื้อขายหนาแน่นเกินปกติ เสี่ยงเบรคเอาท์)
  SF-3: ราคาปิดล่าสุดปิดห่างจากระดับแนวราคาสำคัญเกิน 0.3 * ATR
        → +20 คะแนน (ราคาย้อนกลับตัวมาได้ยากเนื่องจากปิดลึกเกินไป)

*** HARD BLOCK FACTORS (Block Score = 100 ทันที) ***
  HB-1: Market State เป็น TRENDING_STRONG หรือ BREAKOUT_EMERGING
        → Block Score = 100
  HB-2: ทิศทางไส้เทียนของแท่งเทียนที่ปฏิเสธทิศทางกลับตัวหลักมีขนาดยาวเด่นชัดเจนข่มทิศเป้าหมาย
        (Wick_opposite > Wick_target * 1.5)
        → Block Score = 100
  HB-3: อยู่ในช่วงประกาศข่าวความผันผวนสูง High Impact เศรษฐกิจ (+/- 15 นาที)
        → Block Score = 100
  HB-4: สถานะวงจรสภาวะตลาดเสื่อมถอย (State Lifecycle = Exhausted)
        → Block Score = 100
  HB-5: ไม่มีการตอบสนองราคาจากเซิร์ฟเวอร์โบรกเกอร์เกิน 10 วินาที (Broker Feed Freeze)
        → Block Score = 100

สูตรคำนวณ Block Score สุดท้าย:
  IF มี Hard Block เกิดขึ้นข้อใดข้อหนึ่ง → Block Score = 100
  ELSE → Block Score = Min(100, Sum(คะแนนสะสมของ Soft Block ทั้งหมด))

******************************************************************************--
#### 6. STRATEGY CONFIDENCE
******************************************************************************--
C_strategy คำนวณในรูปแบบค่าต่อเนื่อง (สเกล 0.0–1.0):
  C_strategy = (0.40 * S_rsi_bounce) + (0.40 * S_sr_touch) + (0.20 * S_vol_ratio)

คะแนนย่อย (Sub-scores):
  1. RSI Bounce Score (S_rsi_bounce):
     - S_rsi_bounce = Min(1.0, |RSI(7)[-1] - RSI(7)[-2]| / 8.0)
     (หมายเหตุ: การสปีดตัวของ RSI เกิน 8 จุดสะท้อนแรงขับสูงสุด ได้ 1.0)

  2. S/R Touch Accuracy Score (S_sr_touch):
     - S_sr_touch = Max(0.0, 1.0 - (D_sr / 0.08))

  3. Volume Ratio Score (S_vol_ratio):
     - S_vol_ratio = Min(1.0, Volume[-1] / Avg_Volume(20))

ตัวอย่างการคำนวณ (CALL):
  RSI(7) ย้อนหลัง 2 แท่ง: 27.0 → 32.5 (หักกลับพ้น 30), D_sr = 0.02 * ATR_M5, Volume[-1] = 0.9 * Avg_Volume(20)
  - S_rsi_bounce = Min(1.0, |32.5 - 27.0| / 8.0) = Min(1.0, 5.5 / 8.0) = 0.6875
  - S_sr_touch = Max(0.0, 1.0 - (0.02 / 0.08)) = 0.75
  - S_vol_ratio = Min(1.0, 0.9) = 0.90
  - C_strategy = (0.40 * 0.6875) + (0.40 * 0.75) + (0.20 * 0.90) = 0.275 + 0.30 + 0.18 = 0.755

******************************************************************************--
#### 7. FAIL CONDITIONS
******************************************************************************--
กลยุทธ์จะประเมินผลเป็น NO_SETUP ทันทีในสถานการณ์ต่อไปนี้:
  MARKET_STATE_BLOCKED      : สถานะตลาดขัดต่อทฤษฎีการประเมินสัญญาณ
  LEVEL_TOO_WEAK            : คะแนนความแข็งแรงของพิกัดแนวระดับ S_level < 40
  LEVEL_NOT_TOUCHED         : ไม่มีระดับราคาใดๆ ใน 3 แท่งล่าสุดสัมผัสแนวอ้างอิง
  RSI_REENTRY_FAILED        : RSI(7) ไม่สามารถวิ่งกลับเข้าโซนปกติพ้นเส้น 30 หรือ 70
  BROKER_FEED_FREEZE        : ระบบไม่ได้รับค่าราคาอัปเดตเรียลไทม์เกิน 10 วินาที
  NEWS_BLACKOUT             : ข่าวเศรษฐกิจขัดขวางการประมวลผลในช่วงเวลาที่กำหนด

******************************************************************************--
#### 8. EXPECTED BEHAVIOR
******************************************************************************--
Strong RSI Reentry (สัญญาณคุณภาพสูงสุด):
  ราคาปิดแท่งที่แล้วในจุดต่ำสุดที่แนวรับที่มีคะแนนแข็งแกร่ง (S_level > 70) พร้อม RSI(7) ต่ำกว่า 25
  แท่งเทียนปัจจุบันดีดขึ้นทันทีปิดพ้นระดับ 30 พร้อมปริมาณซื้อขายหนาแน่นปานกลาง
  C_strategy > 0.80, Entry Score > 75
  คาดหวัง: โมเมนตัมพยุงให้ราคาเคลื่อนตัวทิศทางบวกต่อไปอีกอย่างน้อย 1 แท่งเทียน (5 นาที)

Weak RSI Reentry (สัญญาณเสี่ยงปานกลาง):
  RSI(7) พึ่งเลื่อนเข้าขีดสุดและเคลื่อนที่กลับออกนอกกรอบอย่างเชื่องช้า แนวรับในอดีตเคยถูกทดสอบบ่อยครั้ง
  C_strategy 0.50–0.70, Entry Score 60–74
  คาดหวัง: ราคาอาจไซด์เวย์ออกข้างหรือ Retest แนวรับซ้ำก่อนเคลื่อนที่

False RSI Reentry (Breakout Continuation):
  ราคาดิ่งทะลุแนวต้านออกไปอย่างต่อเนื่องโดยไม่มีการย้อนกลับของราคาปิด และ RSI ค้างในแดน Overbought/Oversold เป็นเวลานาน
  ดักจับทาง: เงื่อนไข Hard Block และการประเมิน Market State
  ผลลัพธ์: ระบบขึ้นสถานะ NO_SETUP ทันที

******************************************************************************--
#### 9. AUDIT REQUIREMENTS
******************************************************************************--
บันทึกข้อมูลเพื่อใช้ในการสอบทานลงระบบฐานข้อมูลความปลอดภัย WORM:
  - audit_id              : UUIDv4 หมายเลขรอบบันทึกข้อมูล
  - timestamp             : แสตมป์เวลามาตรฐานสากล UTC
  - symbol                : ชื่อสินทรัพย์
  - market_state          : สภาวะตลาดที่รับคำนวณ
  - candle_ohlcv          : ข้อมูลราคาย้อนหลังแท่ง M5 100 แท่ง
  - rsi7_current          : ค่า RSI(7) ปัจจุบัน
  - rsi7_previous         : ค่า RSI(7) ย้อนหลัง 1 แท่ง
  - local_support         : พิกัดแนวรับที่ใช้อ้างอิง
  - local_resistance      : พิกัดแนวต้านที่ใช้อ้างอิง
  - s_level_final         : คะแนนความแข็งแรงแนวหลังหักค่าเสื่อมถอย
  - f_rsi_reentry         : คะแนนองค์ประกอบการหักกลับ RSI
  - f_sr                  : คะแนนการทดสอบแนวอ้างอิง
  - f_close               : คะแนนความห่างของราคาปิด
  - f_vol                 : คะแนนปริมาณซื้อขาย
  - entry_score           : คะแนนทางสถิติของระบบส่งออเดอร์
  - block_score           : คะแนนวิเคราะห์ขัดขวางออเดอร์
  - c_strategy            : ความน่าจะเป็นในการชนะเชิงระบบ
  - eligible              : ผลความสมบูรณ์สัญญาณ (true/false)
  - action                : คำสั่งดำเนินการ (CALL / PUT / NO_SETUP)
  - fail_reason_code      : รหัสวิเคราะห์ข้อผิดพลาด

******************************************************************************--
#### 10. OUTPUT CONTRACT (FROZEN SCHEMA)
******************************************************************************--
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_RSIReversal_M5_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "rsi_reversal" },
    "eligible":            { "type": "BOOLEAN" },
    "action":              { "type": "STRING", "enum": ["CALL", "PUT", "NO_SETUP"] },
    "entry_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "block_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "strategy_confidence": { "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "direction_confidence":{ "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "expected_state":      { "type": "STRING",
                             "enum": ["SIDEWAY_RANGE","REVERSAL_FORMING",
                                      "DISTRIBUTION","TRANSITIONAL","UNCLEAR"] },
    "fail_reason_code":    { "type": "STRING" },
    "audit_id":            { "type": "STRING",
                             "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[4][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$" },
    "expiry":              { "type": "STRING", "const": "M5" },
    "details": {
      "type": "OBJECT",
      "properties": {
        "level_touched":        { "type": "NUMBER" },
        "pattern_detected":     { "type": "STRING" },
        "calculated_wick_ratio":{ "type": "NUMBER" }
      },
      "required": ["level_touched", "pattern_detected", "calculated_wick_ratio"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}

---

### ?? STRATEGY: Reversal Group C ENGULFING SCALPER

# FINAL SPECIFICATION: ENGULFING MOMENTUM SCALPER (engulfing_scalper)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

******************************************************************************--
#### 1. STRATEGY OVERVIEW
******************************************************************************--
ชื่อกลยุทธ์:
  Engulfing Momentum Scalper
  (Engulfing Pattern with Bollinger Band Edge Penetration & Fast Stochastic)

วัตถุประสงค์:
  ตรวจจับพฤติกรรมแท่งเทียนกลืนกิน (Engulfing Pattern) ณ บริเวณขอบนอกของเส้น Bollinger Bands (10, 1.8)
  ร่วมกับการยืนยันภาวะโมเมนตัมสุดโต่งจาก Fast Stochastic (5, 3, 3) ในกราฟ M5
  กลยุทธ์มุ่งเน้นการเก็งกำไรจังหวะเด้งกลับอย่างรวดเร็ว (Reversal Scalping)
  และส่งสัญญาณ ณ วินาทีเปิดของแท่งเทียนถัดไปทันที
  โดยกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — มีสิทธิ์สร้างสัญญาณหลักด้วยตัวเองเมื่อองค์ประกอบครบถ้วน

ประเภทสัญญาณ:
  Reversal — กลับตัวระยะสั้นภายใน 1-3 แท่ง M5

Market States ที่เหมาะสม:
  SIDEWAY_RANGE    — ตลาดสวิงในกรอบชัดเจน วิ่งชนขอบแล้วกลับตัว     [★★★★★]
  REVERSAL_FORMING — มีสัญญาณเหนื่อยล้าของเทรนด์และจ่อขอบแบนด์      [★★★★★]
  DISTRIBUTION     — การกระจายสินค้าบริเวณขอบแนวต้านสำคัญ          [★★★★★]
  TRANSITIONAL     — ใช้ได้แต่ลดน้ำหนัก Entry Score 30%          [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  TRENDING_STRONG   — ตลาดทำเทรนด์รุนแรง ราคาจะเกาะเส้นแบนด์ลากยาว (Band Riding)
  BREAKOUT_EMERGING — ราคากำลังพุ่งทะลุกรอบเพื่อทำทิศทางใหม่
  ACCUMULATION      — ช่วงสะสมราคา กรอบแคบเกินไป สัญญาณหลอกเยอะ
  TRENDING_WEAK     — เทรนด์อ่อนๆ แต่อาจผลักดันต่อเนื่องจนชนแนว
  LIQUIDITY_VOID    — ขาดสภาพคล่อง ราคาขยับเป็นขั้นบันได
  CHOPPY_UNCERTAIN  — ตลาดสะเปะสะปะ ไม่มีทิศทาง
  UNCLEAR           — สัญญาณตลาดขัดแย้งเชิงโครงสร้าง

******************************************************************************--
#### 2. REQUIRED INPUTS
******************************************************************************--
1. M5 OHLCV Candles (ย้อนหลังอย่างน้อย 20 แท่ง)
   เหตุผล: คำนวณเส้น Bollinger Bands, Fast Stochastic, ATR และระบุแพทเทิร์นแท่งเทียน

2. ATR(14) บน M5
   เหตุผล: ใช้เป็นมาตรวัดสากลในการแปลงค่าความห่างของราคาให้เป็นสัดส่วนผันแปรเทียบเคียงกันได้

3. Bollinger Bands (10, 1.8) บน M5
   - Period             = 10 (หน้าต่างสแกนสั้นเพื่อความไวต่อการตอบสนอง)
   - Standard Deviation = 1.8 (ปรับระดับแบนด์ให้แคบลงเพื่อหาขอบสวิงลึก)
   เหตุผล: ระบุพิกัดขอบบน (Upper BB) และขอบล่าง (Lower BB) เพื่อวัดขอบเขตราคา Overextended

4. Fast Stochastic (5, 3, 3) บน M5
   - %K Period = 5 (ประเมินโมเมนตัมแบบไวพิเศษ)
   - %D Period = 3
   - Smoothing = 3
   เหตุผล: ตรวจวัดระดับโมเมนตัมตึงตัวระยะสั้นพิเศษในโซน Overbought (> 75) หรือ Oversold (< 25)

5. Average Volume (เฉลี่ย 20 แท่ง M5)
   เหตุผล: ป้องกันความเสียหายในกรณีวอลลุ่มหลั่งไหลผิดปกติเพื่อรันเทรนด์ช่วงเบรคเอาท์

6. Real-Time Tick Feed
   เหตุผล: ยืนยันความต่อเนื่องของสายข้อมูลและตรวจสอบอาการค้างของสัญญาณโบรกเกอร์

7. Market State + State Age (จาก Intelligence OS)
   เหตุผล: ตรวจสอบความสอดคล้องของกลยุทธ์กลับตัวกับทิศทางตลาดและรอบชีวิตสภาวะ

8. High Impact News Calendar (+/- 15 นาที)
   เหตุผล: ล็อกระบบไม่ให้เทรดเนื่องจากความหนาแน่นผิดปกติในช่วงข่าว

******************************************************************************--
#### 3. ENTRY CONDITIONS
******************************************************************************--
ขั้นตอนการประเมินเรียงตามลำดับความสำคัญ (หากไม่ผ่านขั้นตอนใดให้หยุดตรวจสอบทันที)

CONDITION 1 — Market State Eligibility
  ประเมินความเข้ากันได้ของสภาวะตลาดหลัก
  ผ่าน: SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION, TRANSITIONAL
  ไม่ผ่าน: หยุดการทำงานทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — Engulfing Pattern Detection
  ตรวจสอบความสัมพันธ์ของโครงสร้างแท่งเทียน M5[-2] และ M5[-1]:
  กำหนดค่าความคลาดเคลื่อน (Tolerance Multiplier) = 1.0002
  
  สำหรับ CALL (Bullish Engulfing):
    2a. แท่งก่อนหน้าเป็นแดง: Close[-2] < Open[-2]
    2b. แท่งปัจจุบันเป็นเขียว: Close[-1] > Open[-1]
    2c. ราคาเปิดปัจจุบันเท่ากับหรือต่ำกว่าราคาปิดก่อนหน้า: Open[-1] <= Close[-2] × 1.0002
    2d. ราคาปิดปัจจุบันเท่ากับหรือสูงกว่าราคาเปิดก่อนหน้า: Close[-1] × 1.0002 >= Open[-2]
  
  สำหรับ PUT (Bearish Engulfing):
    2a. แท่งก่อนหน้าเป็นเขียว: Close[-2] > Open[-2]
    2b. แท่งปัจจุบันเป็นแดง: Close[-1] < Open[-1]
    2c. ราคาเปิดปัจจุบันเท่ากับหรือสูงกว่าราคาปิดก่อนหน้า: Open[-1] × 1.0002 >= Close[-2]
    2d. ราคาปิดปัจจุบันเท่ากับหรือต่ำกว่าราคาเปิดก่อนหน้า: Close[-1] <= Open[-2] × 1.0002
  
  ไม่ผ่านเกณฑ์การกลืนกิน → หยุดประเมินทันที → fail_reason_code: ENGULFING_PATTERN_INVALID

CONDITION 3 — Bollinger Band Edge Touch Validation
  ตรวจสอบราคาปิดของแท่งเทียนกลืนกิน M5[-1] เทียบกับแบนด์
  สำหรับ CALL: ราคาปิดต้องเท่ากับหรืออยู่ต่ำกว่าแบนด์ล่าง: Close[-1] <= LowerBB
  สำหรับ PUT: ราคาปิดต้องเท่ากับหรืออยู่สูงกว่าแบนด์บน: Close[-1] >= UpperBB
  
  ไม่ผ่านเกณฑ์การสัมผัส/ทะลุแบนด์ → หยุดประเมินทันที → fail_reason_code: BOLLINGER_BAND_NOT_TOUCHED

CONDITION 4 — Fast Stochastic Extreme Momentum Validation
  ตรวจสอบค่าความเร็วโมเมนตัม %K ล่าสุด
  สำหรับ CALL: %K[-1] < 25 (ภาวะขายมากเกินไป)
  สำหรับ PUT: %K[-1] > 75 (ภาวะซื้อมากเกินไป)
  
  ไม่ผ่านเกณฑ์โมเมนตัมตึงตัว → หยุดประเมินทันที → fail_reason_code: STOCHASTIC_MOMENTUM_INVALID

CONDITION 5 — Candle Body Size Check
  ขนาดเนื้อเทียนของแท่งตั้งต้น M5[-1] ต้องหนากว่าค่าความผันผวนขั้นต่ำสุด:
    Body Size = |Close[-1] - Open[-1]| >= 0.05 × ATR_M5
  ไม่ผ่านเกณฑ์ → หยุดประเมินทันที → fail_reason_code: DOJI_SETUP_INVALID

CONDITION 6 — Volume Climax Breakout Prevention
  ป้องกันความเสี่ยงกรณีเกิดแท่งกลืนกินวอลลุ่มมหาศาลทะลุออกนอกแบนด์ (ซึ่งมักนำไปสู่การทะลุกรอบต่อ):
  IF Volume[-1] > 2.0 × Avg_Volume
    สำหรับ CALL: หาก (LowerBB - Close[-1]) > 0.5 × ATR_M5 → HARD BLOCK → fail_reason_code: BREAKOUT_VOL_CLIMAX
    สำหรับ PUT: หาก (Close[-1] - UpperBB) > 0.5 × ATR_M5 → HARD BLOCK → fail_reason_code: BREAKOUT_VOL_CLIMAX
  ผ่านเกณฑ์: ดำเนินการตรวจสอบขั้นตอนต่อไป

CONDITION 7 — Broker Feed Validity Check
  ตรวจเช็คความสม่ำเสมอของสายส่งโบรกเกอร์ (ความหน่วงข้อมูลค้างต้องไม่เกิน 10 วินาที)
  ไม่ผ่านเกณฑ์ → หยุดประเมิน → fail_reason_code: BROKER_FEED_FREEZE

******************************************************************************--
#### 4. ENTRY SCORE LOGIC
******************************************************************************--
คะแนนรวมการเข้าเก็งกำไรดิบ (Raw Entry Score) สเกล 0-100 คะแนน คำนวณจากค่าน้ำหนัก 4 ส่วน:

Factor 1 — Engulfing Strength (F_engulf) น้ำหนัก 30%
  วัดแรงกลืนกินทางโครงสร้าง ยิ่งเนื้อเทียนปัจจุบันใหญ่กว่าเนื้อเทียนก่อนหน้า คะแนนยิ่งสูง
    Body_prev = |Close[-2] - Open[-2]|
    Body_curr = |Close[-1] - Open[-1]|
    Ratio = Body_curr / Max(Body_prev, 1e-10)
    F_engulf = Min(100, Max(0, ((Ratio - 1.0) / 0.5) × 50 + 50))
    (หากเนื้อแท่งปัจจุบันใหญ่กว่าแท่งก่อนหน้าตั้งแต่ 1.5 เท่าขึ้นไป จะได้คะแนนเต็ม 100)

Factor 2 — Bollinger Band Penetration (F_band) น้ำหนัก 20%
  วัดระดับความลึกของการปิดราคาออกไปนอกแบนด์
  สำหรับ CALL:
    Dist = (LowerBB - Close[-1]) / ATR_M5
    F_band = Min(100, 50 + (Dist / 0.2) × 50) ยอมรับเฉพาะ Dist >= 0
  สำหรับ PUT:
    Dist = (Close[-1] - UpperBB) / ATR_M5
    F_band = Min(100, 50 + (Dist / 0.2) × 50) ยอมรับเฉพาะ Dist >= 0
    (หากราคาปิดแทงผ่านทะลุแบนด์เกิน 0.2 × ATR_M5 จะได้คะแนนเต็ม 100)

Factor 3 — Fast Stochastic Extremeness (F_stoch) น้ำหนัก 20%
  วัดระดับความสุดโต่งของดัชนีโมเมนตัม Fast Stochastic %K
  สำหรับ CALL:
    F_stoch = Max(0.0, 100.0 × (1.0 - (%K[-1] / 25.0)))
  สำหรับ PUT:
    F_stoch = Max(0.0, 100.0 × ((%K[-1] - 75.0) / 25.0))

Factor 4 — Volume Expansion (F_volume) น้ำหนัก 30%
  วัดระดับการขยายตัวของปริมาณการซื้อขายเมื่อเทียบกับแท่งก่อนหน้า เพื่อยืนยันแรงผลักกลับที่มีคุณภาพ
    V_Ratio = Volume[-1] / Volume[-2]
    F_volume = Min(100, Max(0, ((V_Ratio - 1.0) / 1.0) × 50 + 50))
    (หากปริมาณซื้อขายขยายเพิ่มขึ้นเป็น 2.0 เท่าหรือมากกว่าของแท่งก่อนหน้า จะได้คะแนนเต็ม 100)

สูตรการประเมินคะแนน:
  Raw Entry Score = (0.30 × F_engulf) + (0.20 × F_band) + (0.20 × F_stoch) + (0.30 × F_volume)

การปรับลดคะแนนตามรอบชีวิตสภาวะตลาด (Lifecycle & State Adjustments):
  - Fresh / Active   → ใช้คะแนนดิบตามจริง (Raw Entry Score)
  - Late             → Entry Score = Raw Entry Score × 0.80
  - Exhausted        → ส่งสัญญาณบล็อกคะแนนทันที (Block Score = 100)
  - TRANSITIONAL State  → ปรับลดคะแนนลง 30% (คูณ 0.70) หลังการปรับตามอายุสภาวะ

******************************************************************************--
#### 5. BLOCK SCORE LOGIC
******************************************************************************--
คะแนนบล็อกความเสี่ยง (Block Score) เริ่มต้นจาก 0 และสะสมคะแนนเพิ่มขึ้นตามความเสี่ยงตลาด

*** SOFT BLOCK FACTORS (สะสมคะแนนสูงสุด 100 คะแนน) ***
  SF-1: สภาพตลาดผันผวนสูงฉับพลัน
        ATR_M5 ล่าสุด > 1.5 × ค่าเฉลี่ย ATR 20 แท่งย้อนหลัง
        → บวกเพิ่ม 30 คะแนน
  SF-2: ขนาดแท่งกลืนกินเล็กเกินไปเมื่อเทียบกับสภาพความแกว่งเฉลี่ย
        Body_curr < 0.1 × ATR_M5
        → บวกเพิ่ม 25 คะแนน
  SF-3: ตลาดอยู่ในสภาวะผันผวนด้านกระจายราคา (DISTRIBUTION หรือ TRANSITIONAL)
        → บวกเพิ่ม 20 คะแนน

*** HARD BLOCK FACTORS (Block Score = 100 ทันทีและปฏิเสธสัญญาณโดยเด็ดขาด) ***
  HB-1: สภาวะตลาดเป็นสภาวะต้องห้าม (เช่น TRENDING_STRONG หรือ BREAKOUT_EMERGING)
  HB-2: ปริมาณความผันผวนตึงตัวต่ำเกินขีดจำกัด (ATR_M5 < 0.25 × ค่าเฉลี่ย ATR 20 แท่ง)
  HB-3: ช่วงข่าวนอกโซนปลอดภัย High Impact News ในรอบ +/- 15 นาที
  HB-4: ช่วงอายุตลาดเสื่อมถอยรอบขีดสุด (State Lifecycle = Exhausted)
  HB-5: เกิดแรงดันต้านการกลับตัวสวนแพทเทิร์นอย่างมีนัยสำคัญ (Huge Opposite Wick)
        สำหรับ CALL: ไส้เทียนด้านบนของแท่งกลืนกินยาวเกินครึ่งของตัวเนื้อ: Upper Wick[-1] > 0.5 × Body_curr
        สำหรับ PUT: ไส้เทียนด้านล่างของแท่งกลืนกินยาวเกินครึ่งของตัวเนื้อ: Lower Wick[-1] > 0.5 × Body_curr
  HB-6: เกิดการปิดราคาหลุดทะลุแบนด์รุนแรงพร้อมความหนาแน่นปริมาณซื้อขาย (ตามเกณฑ์ของ Condition 6)

*** สูตรประมวลผลปลายทาง ***
  IF พบเงื่อนไข Hard Block ข้อใดข้อหนึ่ง → Block Score = 100
  ELSE → Block Score = Sum(Soft Block Points) จำกัดค่าสูงสุดที่ 100 คะแนน

******************************************************************************--
#### 6. STRATEGY CONFIDENCE
******************************************************************************--
ระดับความมั่นใจของการวิเคราะห์ด้วยโมเดลแบบค่าต่อเนื่อง (Continuous Model) สเกล 0.0 ถึง 1.0:

  C_strategy = (0.40 × S_engulf) + (0.35 × S_bb) + (0.25 × S_stoch)

เกณฑ์การประเมินคะแนนย่อย (Sub-scores):

  1. S_engulf (Engulfing Dominance Score):
     วัดระดับการเอาชนะความยาวเนื้อเทียนก่อนหน้า
     Ratio = Body_curr / Body_prev
     S_engulf = Min(1.0, Max(0.0, (Ratio - 1.0) / 1.0))
     (หากแท่งปัจจุบันยาวเป็น 2 เท่าขึ้นไปของแท่งเดิม S_engulf = 1.0)

  2. S_bb (BB Edge Extension Score):
     วัดระยะห่าง/ความลึกของการปิดราคาเทียบกับเส้นกรอบแบนด์
     สำหรับ CALL: Dist = LowerBB - Close[-1]
                 S_bb = Min(1.0, Max(0.0, (Dist + 0.05 × ATR_M5) / (0.1 × ATR_M5)))
     สำหรับ PUT: Dist = Close[-1] - UpperBB
                 S_bb = Min(1.0, Max(0.0, (Dist + 0.05 × ATR_M5) / (0.1 × ATR_M5)))

  3. S_stoch (Fast Stochastic Overextended Score):
     สำหรับ CALL: S_stoch = Max(0.0, 1.0 - (%K[-1] / 25.0))
     สำหรับ PUT: S_stoch = Max(0.0, (%K[-1] - 75.0) / 25.0)

******************************************************************************--
#### 7. FAIL CONDITIONS
******************************************************************************--
ระบบจะส่งสัญญาณ NO_SETUP ออกไปทันทีเมื่อขัดตรรกะบังคับข้อใดข้อหนึ่งดังนี้:

  MARKET_STATE_BLOCKED      : สภาวะตลาดห้ามเทรดกลับตัวสวนแนวโน้ม
  ENGULFING_PATTERN_INVALID : โครงสร้างแท่งเทียนไม่เข้าข่ายเกณฑ์แพทเทิร์นกลืนกิน
  BOLLINGER_BAND_NOT_TOUCHED: ราคาปิดไม่ได้ยืนยันตัวตน ณ ขอบแนวสัมผัสแบนด์
  STOCHASTIC_MOMENTUM_INVALID: ค่า Fast Stochastic ปิดนอกเขตเกณฑ์ความตึงตัว
  DOJI_SETUP_INVALID        : แท่งปัจจุบันขาดแรงปะทะหลัก เป็นรูปทรงโดจิไร้น้ำหนัก
  BREAKOUT_VOL_CLIMAX       : แท่งกลืนกินทะลุดึงแบนด์ลึกร่วมกับปริมาณซื้อขายสะสมพุ่งสูง
  BROKER_FEED_FREEZE        : ระบบตรวจสอบพบอาการสายข้อมูลขาดการเคลื่อนไหว
  NEWS_BLACKOUT             : ขัดต่อหลักความปลอดภัยช่วงปล่อยข่าวเศรษฐกิจระดับสูง

******************************************************************************--
#### 8. EXPECTED BEHAVIOR
******************************************************************************--
Strong Engulfing (กลับตัวรุนแรงประสิทธิภาพสูง):
  แท่งเทียนเกิดการขยายตัวกลืนกินแท่งก่อนหน้าอย่างลึกซึ้ง (Ratio > 1.5)
  ปิดราคาแทงทะลุออกไปนอกเส้นแบนด์ล่าง/บนในกรอบสะสมที่กว้างและค่อนข้างนิ่ง พร้อมปริมาณ Volume เพิ่มขึ้นชัดเจน
  Fast Stochastic ปิดในค่าสุดกู่ (< 10 สำหรับ CALL, > 90 สำหรับ PUT)
  C_strategy > 0.80, Entry Score > 75
  คาดหวัง: ราคาจะกลับตัวปิดเป็นบวก/ลบสวนทิศทางใน M5 ถัดไปทันทีอย่างเด็ดขาด

Weak Engulfing (กลับตัวปานกลาง/ผันผวน):
  ขนาดของเนื้อเทียนไม่ได้ต่างกันมาก หรือพิกัดปิดปะทะปะบนเส้นขอบแบนด์แบบหวุดหวิด โดยปริมาณ Volume ทรงตัว
  C_strategy อยู่ในช่วง 0.50–0.79, Entry Score 60–74
  คาดหวัง: ราคาอาจเด้งแบบผันผวนหรือย้อนทดสอบแนวซ้ำก่อนเปลี่ยนทิศทางในกรอบกว้าง

False Engulfing (Breakout):
  เกิดแท่งกลืนกินยาวเหยียดพร้อมปริมาณซื้อขายสะสมล้นพะเนิน ราคาปิดทะลุแบนด์ออกไปไกลเกินเกณฑ์
  ซึ่งสื่อถึงแรงเฉื่อยตามน้ำ (Momentum Breakout) ที่รุนแรงของกลุ่มเทรดเดอร์ในแนวโน้มใหญ่
  ระบบจะสกัดกั้นได้ในด่าน Condition 6 และล็อกการออกสเปกบล็อกสัญญาณทันที (BREAKOUT_VOL_CLIMAX)

******************************************************************************--
#### 9. AUDIT REQUIREMENTS
******************************************************************************--
รายการข้อมูลที่จำเป็นต้องจัดเก็บลง WORM Database ในทุกรอบประเมินสตรีมกลยุทธ์:

  - audit_id        : UUIDv4 อ้างอิงตรวจสอบผลการประเมินประจำรอบ
  - timestamp       : เวลาประเมินระบบในรูปมาตรฐานสากล (UTC)
  - symbol          : ชื่อคู่เงิน
  - market_state    : สภาวะตลาดรวมถึงอายุ State ณ รอบนั้น
  - candle_ohlcv    : ราคา OHLCV ของแท่ง M5[-1] และ M5[-2]
  - atr_m5          : ค่าความผันผวน ATR_M5 ปัจจุบัน
  - upper_bb        : พิกัดค่าเฉลี่ย Bollinger Band บน (10, 1.8)
  - lower_bb        : พิกัดค่าเฉลี่ย Bollinger Band ล่าง (10, 1.8)
  - stoch_k         : ค่า Fast Stochastic %K ล่าสุด
  - stoch_d         : ค่า Fast Stochastic %D ล่าสุด
  - f_engulf        : คะแนนองค์ประกอบ Engulfing Strength
  - f_band          : คะแนนองค์ประกอบ Band Penetration
  - f_stoch         : คะแนนองค์ประกอบ Fast Stochastic Extremeness
  - f_volume        : คะแนนองค์ประกอบ Volume Expansion
  - entry_score_raw : คะแนนประเมินรวมก่อนคิดเงื่อนไขตลาดและอายุ
  - entry_score     : คะแนนประเมินจริงขั้นปลายน้ำ
  - block_score     : คะแนนป้องกันสกัดกั้นความเสี่ยงรวม
  - s_engulf        : ดัชนีความมั่นใจการกลืนกิน
  - s_bb            : ดัชนีความมั่นใจการทะลุแนวแบนด์
  - s_stoch         : ดัชนีความมั่นใจโมเมนตัม Stochastic
  - c_strategy      : ระดับความมั่นใจกลยุทธ์รวม
  - eligible        : ผลตรวจสอบเงื่อนไขความพร้อมใช้งาน (true/false)
  - action          : สัญญาณเปิดเทรด (CALL / PUT / NO_SETUP)
  - fail_reason_code: รหัสข้อมูลระบุขีดจำกัดล้มเหลว (null เมื่อสำเร็จ)

******************************************************************************--
#### 10. OUTPUT CONTRACT (FROZEN SCHEMA)
******************************************************************************--
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_EngulfingScalper_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "engulfing_scalper" },
    "eligible":            { "type": "BOOLEAN" },
    "action":              { "type": "STRING", "enum": ["CALL", "PUT", "NO_SETUP"] },
    "entry_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "block_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "strategy_confidence": { "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "direction_confidence":{ "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "expected_state":      { "type": "STRING",
                             "enum": ["SIDEWAY_RANGE","REVERSAL_FORMING",
                                      "DISTRIBUTION","TRANSITIONAL","UNCLEAR"] },
    "fail_reason_code":    { "type": "STRING" },
    "audit_id":            { "type": "STRING",
                             "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[4][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$" },
    "expiry":              { "type": "STRING", "const": "M5" },
    "details": {
      "type": "OBJECT",
      "properties": {
        "upper_bb": { "type": "NUMBER" },
        "lower_bb": { "type": "NUMBER" },
        "stoch_k":  { "type": "NUMBER" }
      },
      "required": ["upper_bb", "lower_bb", "stoch_k"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}

---

### ?? STRATEGY: Reversal Group C STOCHASTIC CROSSOVER

# FINAL SPECIFICATION: STOCHASTIC CROSSOVER (stochastic_crossover)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

******************************************************************************--
#### 1. STRATEGY OVERVIEW
******************************************************************************--
ชื่อกลยุทธ์:
  Stochastic Crossover
  (Stochastic %K/%D Crossover with Local Support/Resistance Touch)

วัตถุประสงค์:
  ตรวจจับการตัดกันของเส้น Stochastic Oscillator (%K และ %D) ในเขตโซนสุดโต่ง (Overbought/Oversold)
  ร่วมกับการยืนยันการสัมผัสแนวรับ/แนวต้านในระดับท้องถิ่น (Local S/R) บนแท่งเทียน M5 ล่าสุด
  กลยุทธ์มุ่งเน้นการจับจังหวะกลับตัวระยะสั้นเพื่อสร้างสัญญาณ ณ วินาทีเปิดของแท่งเทียนถัดไปทันที
  โดยกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — มีสิทธิ์สร้างสัญญาณหลักด้วยตัวเองเมื่อเงื่อนไขและคะแนนผ่านเกณฑ์ที่กำหนด

ประเภทสัญญาณ:
  Reversal — กลับตัวระยะสั้นภายใน 1-3 แท่ง M5

Market States ที่เหมาะสม:
  SIDEWAY_RANGE    — แนวรับ/ต้านชัดเจน ราคาแกว่งตัวในกรอบ          [★★★★★]
  REVERSAL_FORMING — มีสัญญาณการกลับตัวและโมเมนตัมชะลอตัวลงชัดเจน  [★★★★★]
  DISTRIBUTION     — ราคาแตะขอบบนของกรอบสะสมหนาแน่น           [★★★★★]
  TRANSITIONAL     — ใช้ได้แต่ลดน้ำหนัก Entry Score 30%          [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  TRENDING_STRONG   — ตลาดมีแนวโน้มแข็งแกร่ง สวนทางมีโอกาสขาดทุนสูง
  BREAKOUT_EMERGING — ราคากำลังเบรคทะลุกรอบแนวรับ/แนวต้าน
  ACCUMULATION      — ตลาดบีบอัดตัวรอเลือกทิศทาง ยังไม่มีกรอบแกว่งตัวชัดเจน
  TRENDING_WEAK     — ตลาดยังมีแนวโน้มอ่อนๆ โอกาสกลับตัวไม่แน่นอน
  LIQUIDITY_VOID    — ตลาดขาดสภาพคล่อง ราคาเคลื่อนไหวไม่มีทิศทาง
  CHOPPY_UNCERTAIN  — ราคาผันผวนสะเปะสะปะ ไม่มีโครงสร้างชัดเจน
  UNCLEAR           — สภาวะตลาดมีความขัดแย้งเชิงข้อมูล

******************************************************************************--
#### 2. REQUIRED INPUTS
******************************************************************************--
1. M5 OHLCV Candles (ย้อนหลังอย่างน้อย 30 แท่ง)
   เหตุผล: คำนวณเส้น Stochastic, แนวรับ/แนวต้านระดับท้องถิ่น และ ATR

2. ATR(14) บน M5
   เหตุผล: Normalize ระยะการสัมผัสแนวและค่าความผันผวนเพื่อให้เป็นมาตรฐานเดียวกันในทุกคู่เงิน

3. Local S/R Level (คำนวณจากช่วงแท่งเทียน M5[-13] ถึง M5[-3] ย้อนหลัง)
   - Support Level (แนวรับ)      = ค่าต่ำสุดของราคา Low ในช่วง M5[-13] ถึง M5[-3]
   - Resistance Level (แนวต้าน) = ค่าสูงสุดของราคา High ในช่วง M5[-13] ถึง M5[-3]
   เหตุผล: กำหนดแนวอ้างอิงล่าสุดที่หลีกเลี่ยงผลกระทบของ 3 แท่งเทียนปัจจุบัน (Buffer Zone)

4. Stochastic Oscillator (14, 3, 3) บน M5
   - %K Period  = 14 (Lookback สำหรับหาสูงสุด/ต่ำสุด)
   - %D Period  = 3 (ค่าเฉลี่ย SMA ของ %K)
   - Smoothing = 3
   เหตุผล: วัดแรงส่งโมเมนตัมที่เข้าสู่โซน Overbought (> 80) หรือ Oversold (< 20)

5. Average Volume (เฉลี่ย 20 แท่ง M5)
   เหตุผล: ตรวจสอบสภาวะ Volume Climax เพื่อใช้ในการบล็อกสัญญาณที่เกิดจากการ Breakout จริง

6. Real-Time Tick Feed
   เหตุผล: ตรวจสอบความสม่ำเสมอของสัญญาณโบรกเกอร์ (Broker Feed Validity)

7. Market State + State Age (จาก Intelligence OS)
   เหตุผล: ใช้ตรวจสอบสภาวะตลาดที่เหมาะสมและช่วงอายุของ State เพื่อปรับคะแนน Entry Score

8. High Impact News Calendar (+/- 15 นาที)
   เหตุผล: กำหนดเวลาห้ามส่งสัญญาณเทรดช่วงประกาศข่าวรุนแรง

******************************************************************************--
#### 3. ENTRY CONDITIONS
******************************************************************************--
ขั้นตอนการประเมินเรียงตามลำดับความสำคัญ (หากไม่ผ่านขั้นตอนใดขั้นตอนหนึ่งให้หยุดการทำงานทันที)

CONDITION 1 — Market State Eligibility
  ตรวจจับสภาวะตลาดจากระบบหลัก
  ผ่าน: SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION, TRANSITIONAL
  ไม่ผ่าน: หยุดการประเมินทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — Local S/R Level Touch Validation (วัดระยะโดย ATR)
  คำนวณหาระดับราคาแนวรับ (Support) และแนวต้าน (Resistance) ท้องถิ่น:
    Support = Min(Low[-13] ... Low[-3])
    Resistance = Max(High[-13] ... High[-3])
  กำหนดค่าเผื่อการสัมผัสแนว (Tolerance) = 0.1 × ATR_M5
  
  สำหรับ CALL (กลับตัวขึ้นจากแนวรับ):
    ต้องมีอย่างน้อยหนึ่งแท่งในช่วง M5[-3], M5[-2], M5[-1] ที่ราคาสัมผัสแนวรับ:
    Low[k] <= Support + (0.1 × ATR_M5) สำหรับ k ∈ {-3, -2, -1}
  
  สำหรับ PUT (กลับตัวลงจากแนวต้าน):
    ต้องมีอย่างน้อยหนึ่งแท่งในช่วง M5[-3], M5[-2], M5[-1] ที่ราคาสัมผัสแนวต้าน:
    High[k] >= Resistance - (0.1 × ATR_M5) สำหรับ k ∈ {-3, -2, -1}
    
  ไม่ผ่านเกณฑ์สัมผัส → หยุดการประเมินทันที → fail_reason_code: LEVEL_NOT_TOUCHED

CONDITION 3 — Stochastic Extreme Crossover Validation
  คำนวณหาค่า %K และ %D ของ Stochastic(14, 3, 3) ย้อนหลัง 2 แท่ง:
    %K_t = 100 × (Close_t - LowestLow_14) / Max((HighestHigh_14 - LowestLow_14), 1e-10)
    %D_t = SMA(%K, 3)
  
  สำหรับ CALL:
    3a. เกิดการตัดขึ้น (Bullish Crossover): %K[-2] <= %D[-2] และ %K[-1] > %D[-1]
    3b. สัญญาณเกิดขึ้นในเขต Oversold: %K[-1] < 20 และ %D[-1] < 20
  
  สำหรับ PUT:
    3a. เกิดการตัดลง (Bearish Crossover): %K[-2] >= %D[-2] และ %K[-1] < %D[-1]
    3b. สัญญาณเกิดขึ้นในเขต Overbought: %K[-1] > 80 และ %D[-1] > 80

  ไม่ผ่านเกณฑ์การตัดกันในโซนสุดโต่ง → หยุดประเมิน → fail_reason_code: STOCHASTIC_CROSSOVER_INVALID

CONDITION 4 — Candle Body Size Check
  แท่งเทียนตั้งต้น M5[-1] ต้องมีเนื้อเทียนหนาเพียงพอเพื่อหลีกเลี่ยงช่วงราคาไร้ทิศทาง (Doji):
    Body Size = |Close[-1] - Open[-1]| >= 0.05 × ATR_M5
  ไม่ผ่านเกณฑ์ → หยุดประเมิน → fail_reason_code: DOJI_SETUP_INVALID

CONDITION 5 — Volume Breakout Validation
  ป้องกันความเสี่ยงกรณีเกิดการทะลุผ่านแนวรับ/ต้านอย่างแท้จริงด้วยความเร็วสูง:
  IF Volume[-1] > 1.5 × Avg_Volume
    สำหรับ CALL: หาก Close[-1] < Support → ถือว่าเป็น Breakout ขาลง → fail_reason_code: BREAKOUT_CLOSED_OUTSIDE
    สำหรับ PUT: หาก Close[-1] > Resistance → ถือว่าเป็น Breakout ขาขึ้น → fail_reason_code: BREAKOUT_CLOSED_OUTSIDE
  ผ่านเกณฑ์: ดำเนินการขั้นตอนต่อไป

CONDITION 6 — Broker Feed Validity Check
  ตรวจเช็คข้อมูลราคา Tick ล่าสุด ต้องมีการส่งค่าต่อเนื่องและไม่ค้างเกิน 10 วินาที
  ไม่ผ่านเกณฑ์ → หยุดประเมิน → fail_reason_code: BROKER_FEED_FREEZE

******************************************************************************--
#### 4. ENTRY SCORE LOGIC
******************************************************************************--
คะแนนเข้าเทรดดิ้งดิบ (Raw Entry Score) คำนวณในช่วง 0–100 คะแนน จาก 4 ตัวแปรถ่วงน้ำหนักดังนี้:

Factor 1 — Stochastic Extremeness (F_extreme) น้ำหนัก 30%
  วัดความลึกเชิงโมเมนตัมในโซนสุดโต่ง
  สำหรับ CALL (วัดค่าสูงสุดระหว่าง %K และ %D ยิ่งใกล้ 0 คะแนนยิ่งสูง):
    Stoch_Max = Max(%K[-1], %D[-1])
    F_extreme = Max(0, 100 × (1.0 - (Stoch_Max / 20.0)))
  สำหรับ PUT (วัดค่าต่ำสุดระหว่าง %K และ %D ยิ่งใกล้ 100 คะแนนยิ่งสูง):
    Stoch_Min = Min(%K[-1], %D[-1])
    F_extreme = Max(0, 100 × ((Stoch_Min - 80.0) / 20.0))

Factor 2 — Crossover Separation (F_sep) น้ำหนัก 20%
  วัดระยะห่างระหว่างเส้น %K และ %D หลังจากการตัดกัน เพื่อยืนยันแรงผลักกลับเฉลียบพลัน
    Sep = |%K[-1] - %D[-1]|
    F_sep = Min(100, (Sep / 5.0) × 100)
    (หากระยะห่างตัดกันเกิน 5.0 จะได้คะแนนเต็ม 100)

Factor 3 — Touch Precision (F_touch) น้ำหนัก 20%
  วัดความแม่นยำในการทดสอบระดับราคาของแท่งเทียนภายในกรอบ 3 แท่งเทียนที่ผ่านมา
  สำหรับ CALL (พิจารณาค่าต่ำสุด Low_min = Min(Low[-3], Low[-2], Low[-1])):
    Dist = (Low_min - Support) / ATR_M5
    หาก Dist <= 0 (ราคาแทงผ่านเส้นลงไปแล้วดึงกลับ) → F_touch = 100
    หาก Dist > 0 (ราคาลงมาเกือบแตะ) → F_touch = Max(0, 100 - (Dist / 0.1) × 100)
  สำหรับ PUT (พิจารณาค่าสูงสุด High_max = Max(High[-3], High[-2], High[-1])):
    Dist = (Resistance - High_max) / ATR_M5
    หาก Dist <= 0 (ราคาแทงทะลุเส้นขึ้นไปแล้วดึงกลับ) → F_touch = 100
    หาก Dist > 0 (ราคาขึ้นมาเกือบแตะ) → F_touch = Max(0, 100 - (Dist / 0.1) × 100)

Factor 4 — Range Amplitude Quality (F_location) น้ำหนัก 30%
  ประเมินความกว้างของกรอบ Sideway ท้องถิ่น เพื่อยืนยันพื้นที่ผลกำไรที่เพียงพอและคุณภาพของกรอบสะสมราคา
    Range = Resistance - Support
    R_ratio = Range / ATR_M5
    F_location = Min(100, Max(0, ((R_ratio - 1.0) / 4.0) × 100))
    (หากความกว้างของกรอบตราบเท่า 5 เท่าของ ATR_M5 หรือมากกว่า จะได้คะแนนเต็ม 100)

สูตรการคิดคะแนนรวม:
  Raw Entry Score = (0.30 × F_extreme) + (0.20 × F_sep) + (0.20 × F_touch) + (0.30 × F_location)

การปรับปรุงคะแนนตามสภาวะ State Lifecycle และสภาวะตลาดเฉพาะตัว:
  - Fresh / Active   → ใช้คะแนนดิบตามจริง (Raw Entry Score)
  - Late             → Entry Score = Raw Entry Score × 0.80
  - Exhausted        → จะทำการส่งสัญญาณ Block คะแนนทันที (Block Score = 100)
  - TRANSITIONAL State  → ปรับคะแนนลดลง 30% (คูณ 0.70) หลังการปรับตามอายุสภาวะ

******************************************************************************--
#### 5. BLOCK SCORE LOGIC
******************************************************************************--
คะแนนสะกัดกั้นความเสี่ยง (Block Score) เริ่มต้นที่ 0 และสะสมเพิ่มขึ้นตามระดับสัญญาณเสี่ยงทางสถิติ

*** SOFT BLOCK FACTORS (สะสมคะแนนความเสี่ยงสูงสุด 100 คะแนน) ***
  SF-1: ความผันผวนของตลาดเกินเกณฑ์มาตรฐาน
        ATR_M5 ล่าสุด > 1.5 × ค่าเฉลี่ย ATR 20 แท่งย้อนหลัง
        → บวกสะสมเพิ่ม 30 คะแนน
  SF-2: มุมการตัดเฉียงของ Stochastic อ่อนกำลัง (Slow Crossover)
        |%K[-1] - %K[-2]| < 3.0
        → บวกสะสมเพิ่ม 25 คะแนน
  SF-3: สภาวะตลาดเป็น DISTRIBUTION หรือ TRANSITIONAL
        → บวกสะสมเพิ่ม 20 คะแนน

*** HARD BLOCK FACTORS (Block Score = 100 ทันทีและห้ามเปิดสถานะเด็ดขาด) ***
  HB-1: สภาวะตลาดเป็นสภาวะต้องห้าม (เช่น TRENDING_STRONG หรือ BREAKOUT_EMERGING)
  HB-2: ตลาดอยู่ในภาวะไร้ปริมาณซื้อขายสะสม (ATR_M5 < 0.25 × ค่าเฉลี่ย ATR 20 แท่ง)
  HB-3: ช่วงรอยต่อการออกข่าวเศรษฐกิจ High Impact ในรอบ +/- 15 นาที
  HB-4: ช่วงอายุของตลาดเข้าสู่ระยะเหนื่อยล้าสิ้นสุดรอบ (State Lifecycle = Exhausted)
  HB-5: เกิด Volume Breakout ชัดเจน (Volume[-1] > 1.5 × Avg_Volume และราคาปิดออกนอกขอบ S/R)
  HB-6: เกิดแรงกดดันต้านการกลับตัว (Opposite Wick Dominance)
        สำหรับ CALL: ไส้เทียนด้านบนของแท่ง M5[-1] ยาวกว่าไส้เทียนด้านล่าง (Upper Wick > Lower Wick)
        สำหรับ PUT: ไส้เทียนด้านล่างของแท่ง M5[-1] ยาวกว่าไส้เทียนด้านบน (Lower Wick > Upper Wick)

*** สูตรสุดท้ายในการประเมินคะแนนบล็อก ***
  IF พบเจอเงื่อนไข Hard Block ข้อใดข้อหนึ่ง → Block Score = 100
  ELSE → Block Score = Sum(Soft Block Points) โดนจำกัดเพดานสูงสุดที่ 100 คะแนน

******************************************************************************--
#### 6. STRATEGY CONFIDENCE
******************************************************************************--
คะแนนความมั่นใจของการวิเคราะห์ด้วยสูตรคำนวณค่าต่อเนื่อง (Continuous Confidence Model) ในสเกล 0.0 ถึง 1.0:

  C_strategy = (0.40 × S_stoch) + (0.35 × S_crossover) + (0.25 × S_touch)

เกณฑ์การคิดคะแนนย่อย (Sub-scores):

  1. S_stoch (Stochastic Deep Extreme Score):
     สำหรับ CALL: S_stoch = Max(0.0, 1.0 - (Max(%K[-1], %D[-1]) / 20.0))
     สำหรับ PUT: S_stoch = Max(0.0, 1.0 - ((100.0 - Min(%K[-1], %D[-1])) / 20.0))

  2. S_crossover (Crossover Momentum Velocity Score):
     วัดอัตราเร่งการพุ่งตัดกันระหว่าง %K และ %D ย้อนหลัง 2 แท่ง
     S_crossover = Min(1.0, (|%K[-1] - %D[-1]| + |%K[-2] - %D[-2]|) / 10.0)

  3. S_touch (Level Touch Accuracy Score):
     สำหรับ CALL: S_touch = Max(0.0, 1.0 - (|Low_min - Support| / (0.1 × ATR_M5)))
     สำหรับ PUT: S_touch = Max(0.0, 1.0 - (|High_max - Resistance| / (0.1 × ATR_M5)))
     โดยกำหนดให้ Low_min = Min(Low[-3..-1]) และ High_max = Max(High[-3..-1])

******************************************************************************--
#### 7. FAIL CONDITIONS
******************************************************************************--
ระบบจะส่งสัญญาณ NO_SETUP ออกไปทันทีที่พบเจอเหตุการณ์การทำงานขัดข้องเชิงกฎข้อใดข้อหนึ่งดังนี้:

  MARKET_STATE_BLOCKED        : สภาวะตลาดหลักไม่อยู่ในเงื่อนไขการสร้างผลกำไรกลยุทธ์กลับตัว
  LEVEL_NOT_TOUCHED           : ราคาในช่วง 3 แท่งเทียนล่าสุดไม่สามารถลงมาสัมผัสระดับแนวรับ/ต้านได้ตามเกณฑ์
  STOCHASTIC_CROSSOVER_INVALID: การตัดกันของ Stochastic ไม่อยู่ในโซนความน่าจะเป็นสูง
  DOJI_SETUP_INVALID          : ขนาดเนื้อเทียนของแท่งตั้งต้นสั้นเกินไปจนเกิดความไม่สมดุล
  BREAKOUT_CLOSED_OUTSIDE     : มีการยืนยันการปิดราคาเกินแนวขอบระดับร่วมกับปริมาณซื้อขายสะสมสูง
  BROKER_FEED_FREEZE          : สัญญาณความเร็วข้อมูลโบรกเกอร์ค้างเกินเวลาควบคุมป้องกันความเสี่ยง
  NEWS_BLACKOUT               : ช่วงระงับการเก็งกำไรข่าวนอกเวลาปลอดภัย

******************************************************************************--
#### 8. EXPECTED BEHAVIOR
******************************************************************************--
Strong Reversal (สัญญาณเกรดเอ):
  ราคาทำโครงสร้างชนแนวระดับ S/R ท้องถิ่นพร้อมโมเมนตัมความหนาแน่นสูง และเกิด Stochastic Crossover ตัดหักหัวกลับทันทีในโซนสุดโต่ง
  ความกว้างของช่วงราคาแกว่งตัวกว้างกว่า 3 เท่าของ ATR และเกิดไส้เทียนดึงกลับทันทีใน 3 แท่งล่าสุด
  C_strategy > 0.80, Entry Score > 75
  เป้าหมายคาดหวัง: ราคาเกิดการกลับตัวปิดแท่ง M5 ถัดไปในทิศทางของสัญญาณทันที

Weak Reversal (สัญญาณเกรดรอง):
  ระดับแนวราคาของกรอบแกว่งค่อนข้างแคบ หรือ Stochastic ตัดกันเฉียงราบเรียบ มีระยะห่างที่น้อย
  C_strategy อยู่ในช่วง 0.50–0.79, Entry Score 60–74
  เป้าหมายคาดหวัง: ราคาอาจเด้งสั้นๆ หรือมีการย้อนกลับไปไซด์เวย์สัมผัสแนวอีกรอบก่อนเกิดการกลับตัว

False Reversal (สัญญาณหลอก):
  ราคาผ่านการแตะสะสมแล้วเกิดการปิดออกข้างนอกกรอบด้วยเนื้อแท่งเทียนที่ยาวพร้อมปริมาณซื้อขายล้นระบบ (Volume Climax)
  ซึ่งแสดงถึงการเบรคทะลุแนวระดับจริงเพื่อเปลี่ยนผ่านเข้าสู่แนวโน้มหลัก
  ระบบจะสามารถตรวจจับได้จากขั้นตอน Condition 5 และล็อกสเปกให้ออก NO_SETUP บล็อกสัญญาณทันที

******************************************************************************--
#### 9. AUDIT REQUIREMENTS
******************************************************************************--
ข้อมูลทั้งหมดต่อไปนี้จะต้องมีการบันทึกลงในระบบ WORM Database ทุกครั้งที่เกิดสตรีมประเมินกลยุทธ์:

  - audit_id        : รหัสเฉพาะ UUIDv4 ในแต่ละรอบคำนวณ
  - timestamp       : แสตมป์เวลาระบบในรูปมาตรฐานสากล (UTC)
  - symbol          : ชื่อสินทรัพย์ที่ประเมิน
  - market_state    : สภาวะตลาดรวมถึง State Age ปัจจุบัน
  - candle_ohlcv    : OHLCV ของแท่ง M5[-1]
  - atr_m5          : ค่าความผันผวน ATR_M5 ปัจจุบัน
  - local_support   : ระดับราคาแนวรับท้องถิ่นที่อ้างอิง
  - local_resistance: ระดับราคาแนวต้านท้องถิ่นที่อ้างอิง
  - stoch_k         : ค่า Stochastic %K ล่าสุด
  - stoch_d         : ค่า Stochastic %D ล่าสุด
  - prev_k          : ค่า Stochastic %K แท่งก่อนหน้า
  - prev_d          : ค่า Stochastic %D แท่งก่อนหน้า
  - f_extreme       : คะแนนองค์ประกอบ Stochastic Extremeness
  - f_sep           : คะแนนองค์ประกอบ Crossover Separation
  - f_touch         : คะแนนองค์ประกอบ Touch Precision
  - f_location      : คะแนนองค์ประกอบ Range Amplitude
  - entry_score_raw : คะแนนประเมินรวมก่อนคูณฟิลเตอร์สภาวะ
  - entry_score     : คะแนนประเมินจริงขั้นสุดท้าย
  - block_score     : คะแนนความเสี่ยงการบล็อกสะสมรวม
  - s_stoch         : ดัชนีความมั่นใจ Stochastic Extremeness
  - s_crossover     : ดัชนีความมั่นใจ Crossover Momentum
  - s_touch         : ดัชนีความมั่นใจ Touch Accuracy
  - c_strategy      : ค่ารวมความมั่นใจกลยุทธ์ตามหลักสถิติ
  - eligible        : ผลประเมินการตรวจสอบเบื้องต้น (true/false)
  - action          : สัญญาณเทรดดิ้ง (CALL / PUT / NO_SETUP)
  - fail_reason_code: รหัสอธิบายเหตุผลล้มเหลว (null เมื่อได้รับไฟเขียว)

******************************************************************************--
#### 10. OUTPUT CONTRACT (FROZEN SCHEMA)
******************************************************************************--
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_StochasticCrossover_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "stochastic_crossover" },
    "eligible":            { "type": "BOOLEAN" },
    "action":              { "type": "STRING", "enum": ["CALL", "PUT", "NO_SETUP"] },
    "entry_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "block_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "strategy_confidence": { "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "direction_confidence":{ "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "expected_state":      { "type": "STRING",
                             "enum": ["SIDEWAY_RANGE","REVERSAL_FORMING",
                                      "DISTRIBUTION","TRANSITIONAL","UNCLEAR"] },
    "fail_reason_code":    { "type": "STRING" },
    "audit_id":            { "type": "STRING",
                             "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[4][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$" },
    "expiry":              { "type": "STRING", "const": "M5" },
    "details": {
      "type": "OBJECT",
      "properties": {
        "stoch_k":      { "type": "NUMBER" },
        "stoch_d":      { "type": "NUMBER" },
        "local_level":  { "type": "NUMBER" }
      },
      "required": ["stoch_k", "stoch_d", "local_level"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}

---

### ?? STRATEGY: Trend Group EMA CROSSOVER

# FINAL SPECIFICATION: EMA CROSSOVER (ema_crossover)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

******************************************************************************--
#### 1. STRATEGY OVERVIEW
******************************************************************************--
ชื่อกลยุทธ์:
  EMA Crossover
  (EMA5 / EMA20 Trend-Following Crossover Strategy)

วัตถุประสงค์:
  ตรวจจับการตัดกันของเส้นค่าเฉลี่ยเคลื่อนที่แบบเอ็กซ์โพเนนเชียล (Exponential Moving Average) 
  ระหว่างเส้นระยะสั้น (EMA 5) และเส้นระยะยาว (EMA 20) บนแท่งเทียน M5 ล่าสุด 
  เพื่อระบุจุดเปลี่ยนแนวโน้มช่วงเริ่มต้น (Early Trend Shift) และเปิดสถานะตามทิศทางแนวโน้มใหม่
  โดยส่งสัญญาณ ณ วินาทีเปิดของแท่งถัดไปทันที และกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — มีสิทธิ์สร้างสัญญาณหลักด้วยตัวเองเมื่อการตัดกันเกิดขึ้นอย่างสมบูรณ์
  และได้รับการยืนยันปริมาณการซื้อขายและค่าความผันผวนตามเกณฑ์

ประเภทสัญญาณ:
  Trend-Following — ตามแนวโน้มระยะสั้นถึงกลางภายใน 1-3 แท่ง M5

Market States ที่เหมาะสม:
  TRENDING_STRONG   — แนวโน้มหลักชัดเจนและแข็งแกร่ง             [★★★★★]
  TRENDING_WEAK     — แนวโน้มเริ่มก่อตัวแต่ยังไม่แข็งแรงเต็มที่       [★★★★☆]
  BREAKOUT_EMERGING — ราคาทะลุกรอบสำคัญเพื่อตั้งเทรนด์ใหม่        [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  SIDEWAY_RANGE    — ตลาดไม่มีแนวโน้ม เกิดสัญญาณหลอกบ่อยครั้ง (Whip-saws)
  ACCUMULATION      — ตลาดสะสมพลังเพื่อเลือกทิศทาง ราคาแกว่งแคบ
  DISTRIBUTION     — ราคาแกว่งตัวผันผวนสูงบริเวณยอดคลื่น
  LIQUIDITY_VOID    — ปริมาณการซื้อขายต่ำเกินไป เส้นค่าเฉลี่ยวิ่งทับกัน
  CHOPPY_UNCERTAIN  — ทิศทางตลาดไม่แน่นอน แกว่งตัดไปมาไม่มีทิศทาง
  UNCLEAR           — ข้อมูลขัดแย้ง ไม่ระบุสภาวะตลาดที่แน่นอน

******************************************************************************--
#### 2. REQUIRED INPUTS
******************************************************************************--
1. M5 OHLCV Candles (ย้อนหลัง 100 แท่ง)
   เหตุผล: คำนวณเส้น EMA 5, EMA 20, Volume Profile และ ATR(14)

2. ATR(14) บน M5
   เหตุผล: Normalize ระยะการตัดกันและขนาดแท่งเทียนให้เหมาะสมตามความผันผวนของคู่เงิน

3. EMA 5 และ EMA 20 บน M5
   เหตุผล: ระบุจุดตัดของราคาระหว่างระยะสั้นและระยะกลางเพื่อระบุสัญญาณ Golden/Dead Cross

4. Average Volume (เฉลี่ย 20 แท่ง M5)
   เหตุผล: ตรวจสอบความหนาแน่นของปริมาณการซื้อขายขณะเกิดการตัดกัน (Volume Confirmation)

5. Real-Time Tick Feed (ปัจจุบัน)
   เหตุผล: ป้องกันความล้มเหลวจากการป้อนข้อมูลล่าช้าของโบรกเกอร์ (Broker Feed Freeze)

6. Market State + State Age (จาก Intelligence OS)
   เหตุผล: กลยุทธ์ต้องทำงานเฉพาะในสภาวะที่มีแนวโน้มชัดเจน และจำกัดอายุของสภาวะตลาดเพื่อความปลอดภัย

7. High Impact News Calendar (+/- 15 นาที)
   เหตุผล: ป้องกันความเสียหายจากความผันผวนรุนแรงในช่วงที่ข่าวเศรษฐกิจออก

******************************************************************************--
#### 3. ENTRY CONDITIONS
******************************************************************************--
ลำดับขั้นการประเมิน — ต้องผ่านทุกขั้นตามลำดับ หากขั้นใดล้มเหลวให้หยุดทันที

CONDITION 1 — Market State Eligibility
  ตรวจว่า Market State ปัจจุบันอยู่ใน Suitable States หรือไม่
  ผ่าน: TRENDING_STRONG, TRENDING_WEAK, BREAKOUT_EMERGING
  ไม่ผ่าน: หยุดทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — Crossover Validation (Golden / Dead Cross)
  สำหรับ CALL (Golden Cross):
    - EMA5[-2] <= EMA20[-2] (ก่อนหน้านี้ EMA5 อยู่ใต้หรือเท่ากับ EMA20)
    - EMA5[-1] > EMA20[-1]  (ปัจจุบัน EMA5 ตัดขึ้นเหนือ EMA20 สำเร็จ)
  สำหรับ PUT (Dead Cross):
    - EMA5[-2] >= EMA20[-2] (ก่อนหน้านี้ EMA5 อยู่เหนือหรือเท่ากับ EMA20)
    - EMA5[-1] < EMA20[-1]  (ปัจจุบัน EMA5 ตัดลงใต้ EMA20 สำเร็จ)
  ไม่ผ่าน: หยุดทันที → fail_reason_code: NO_CROSSOVER_DETECTED

CONDITION 3 — Minimum Candle Body Size
  ขนาดเนื้อเทียนของแท่งตัดกันต้องมากกว่า 0.10 × ATR_M5 เพื่อรับประกันว่ามีการเคลื่อนไหวของราคาจริง
  Body Size = |Close[-1] - Open[-1]|
  ไม่ผ่าน: หยุดทันที → fail_reason_code: CANDLE_BODY_TOO_SMALL

CONDITION 4 — Volume Confirmation Check
  ปริมาณซื้อขายในแท่งที่เกิดการตัดกันต้องไม่อยู่ในระดับแห้งตัว (Low Volume)
  Volume[-1] >= 0.50 × Avg_Volume
  ไม่ผ่าน: หยุดทันที → fail_reason_code: INSUFFICIENT_VOLUME

CONDITION 5 — Broker Feed Validity
  ตรวจว่า Tick Feed ไม่หยุดค้างเกิน 10 วินาที
  ไม่ผ่าน: หยุดทันที → fail_reason_code: BROKER_FEED_FREEZE

******************************************************************************--
#### 4. ENTRY SCORE LOGIC
******************************************************************************--
Entry Score (สเกล 0–100) คำนวณจาก 4 ปัจจัยถ่วงน้ำหนัก รวม 100%:

Factor 1 — Crossover Velocity (F_velocity) น้ำหนัก 30%
  วัดอัตราการเร่งหรือมุมของการตัดกันระหว่าง EMA5 และ EMA20
  V_cross = |(EMA5[-1] - EMA20[-1]) - (EMA5[-2] - EMA20[-2])|
  V_norm = V_cross / ATR_M5
  F_velocity = Min(100, (V_norm / 0.15) × 100)
  ตีความ: ค่าการแยกตัวหลังตัดกันลึกถึง 0.15×ATR = คะแนน 100

Factor 2 — Candle Body Momentum (F_body) น้ำหนัก 25%
  วัดแรงส่งจากตัวแท่งเทียนที่นำไปสู่การตัดกัน
  R_body = |Close[-1] - Open[-1]| / ATR_M5
  F_body = Min(100, (R_body / 0.50) × 100)
  ตีความ: ขนาดเนื้อเทียนยาวเท่ากับ 0.5×ATR = คะแนน 100

Factor 3 — Trend Strength (F_trend) น้ำหนัก 25%
  วัดความชันของเส้นค่าเฉลี่ยระยะกลาง (EMA 20) เพื่อประเมินความสม่ำเสมอของแนวโน้มหลัก
  Slope_EMA20 = |EMA20[-1] - EMA20[-2]| / ATR_M5
  F_trend = Min(100, (Slope_EMA20 / 0.05) × 100)
  ตีความ: EMA 20 เคลื่อนที่ชันเกิน 0.05×ATR ต่อแท่ง = คะแนน 100

Factor 4 — Volume Confirmation (F_volume) น้ำหนัก 20%
  ประเมินความหนาแน่นของผู้ร่วมตลาดในแท่งสัญญาณ
  R_vol = Volume[-1] / Avg_Volume
  F_volume = Min(100, (R_vol / 1.5) × 100)
  ตีความ: ปริมาณการซื้อขายมากกว่าหรือเท่ากับ 1.5 เท่าของค่าเฉลี่ย 20 แท่ง = คะแนน 100

สูตรรวม:
  Raw Entry Score = (0.30 × F_velocity) + (0.25 × F_body) + (0.25 × F_trend) + (0.20 × F_volume)

ปรับตาม State Lifecycle:
  Fresh / Active   → ใช้ Raw Entry Score ตรง
  Late             → Entry Score = Raw Entry Score × 0.80
  Exhausted        → Block Score = 100 ทันที (ห้ามเข้า)

ปรับตาม BREAKOUT_EMERGING State:
  เนื่องจากเป็นสภาวะช่วงเริ่มต้นเบรคเอาท์ที่มีความผันผวนสูง ให้ปรับ Entry Score = Raw Entry Score × 0.85

******************************************************************************--
#### 5. BLOCK SCORE LOGIC
******************************************************************************--
Block Score เริ่มที่ 0 สะสมจาก Soft Block และ Hard Block

*** SOFT BLOCK FACTORS (สะสมคะแนนความเสี่ยง) ***

  SF-1: ATR ปัจจุบัน > 1.8 × ATR เฉลี่ย 20 แท่ง
        → +35 คะแนน
        เหตุผล: ความผันผวนสูงเกินปกติ มักเกิดการกระชากกลับของราคาได้ง่าย (Whipsaws)

  SF-2: ขนาดไส้เทียนฝั่งตรงข้าม (Opposite Wick) ยาวเกินไป
        (Upper Wick > 1.5 × Body Size สำหรับ CALL หรือ Lower Wick > 1.5 × Body Size สำหรับ PUT)
        → +30 คะแนน
        เหตุผล: บ่งชี้ถึงแรงต่อต้านของราคาฝั่งตรงข้ามที่เริ่มกดดันสวนทางเข้ามา

  SF-3: Market State เป็น BREAKOUT_EMERGING
        → +20 คะแนน
        เหตุผล: แนวโน้มยังไม่เป็นที่ยอมรับสมบูรณ์ อาจเกิด False Breakout ได้

*** HARD BLOCK FACTORS (Block Score = 100 ทันที) ***

  HB-1: Market State เป็น SIDEWAY_RANGE, ACCUMULATION, DISTRIBUTION หรือ CHOPPY_UNCERTAIN
        → Block Score = 100

  HB-2: ปริมาณการซื้อขายในแท่งสัญญาณต่ำเกินไป (Volume[-1] < 0.40 × Avg_Volume)
        → Block Score = 100

  HB-3: อยู่ในช่วงข่าว High Impact ±15 นาที
        → Block Score = 100

  HB-4: State Lifecycle = Exhausted
        → Block Score = 100

*** สูตร Block Score สุดท้าย ***
  IF มี Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = Sum(Soft Block คะแนนที่ติด), Max = 100

******************************************************************************--
#### 6. STRATEGY CONFIDENCE
******************************************************************************--
C_strategy คำนวณแบบค่าต่อเนื่อง (สเกล 0.0–1.0):

  C_strategy = (0.40 × S_alignment) + (0.35 × S_momentum) + (0.25 × S_volume)

Sub-scores:

  S_alignment (Crossover Separation Score):
    ประเมินระดับระยะแยกหลังจากการตัดกันของสองเส้น EMA เพื่อยืนยันว่าไม่เกิดการเกยกันแคบๆ
    S_alignment = Min(1.0, |EMA5[-1] - EMA20[-1]| / (0.10 × ATR_M5))

  S_momentum (Candle Close Dominance Score):
    ประเมินความแข็งแกร่งของการปิดตัวของแท่งเทียน
    สำหรับ CALL: S_momentum = (Close[-1] - Low[-1]) / (High[-1] - Low[-1])
    สำหรับ PUT:  S_momentum = (High[-1] - Close[-1]) / (High[-1] - Low[-1])

  S_volume (Volume Confirmation Score):
    ประเมินความแข็งแกร่งของปริมาณซื้อขาย ณ แท่งสัญญาณ
    S_volume = Min(1.0, Volume[-1] / (1.20 × Avg_Volume))

******************************************************************************--
#### 7. FAIL CONDITIONS
******************************************************************************--
กลยุทธ์คืนค่า NO_SETUP ทันทีเมื่อเกิดกรณีต่อไปนี้:

  MARKET_STATE_BLOCKED    : Market State ไม่อยู่ใน Suitable States
  NO_CROSSOVER_DETECTED   : ไม่มีสัญญาณการตัดกันเกิดขึ้นระหว่าง EMA5 และ EMA20
  CANDLE_BODY_TOO_SMALL   : ขนาดเนื้อเทียนของแท่งตัดกันต่ำกว่า 0.10 × ATR_M5
  INSUFFICIENT_VOLUME     : ปริมาณการซื้อขายในแท่งตัดกันต่ำกว่า 0.50 × Avg_Volume
  BROKER_FEED_FREEZE      : Tick Feed หยุดค้างเกิน 10 วินาที
  NEWS_BLACKOUT           : อยู่ในช่วงข่าว High Impact ±15 นาที

******************************************************************************--
#### 8. EXPECTED BEHAVIOR
******************************************************************************--
Strong Trend Crossover (สัญญาณคุณภาพสูง):
  การตัดกันเกิดขึ้นพร้อมกันกับแท่งเทียนที่มีเนื้อเทียนขนาดใหญ่ ปิดชิดขอบราคาของทิศทาง
  มีความชันของเส้น EMA 20 ชัดเจน และมีปริมาณการซื้อขายสนับสนุน (Volume[-1] > 1.2 × Avg_Volume)
  C_strategy > 0.80, Entry Score > 75
  คาดหวัง: แนวโน้มใหม่จะรักษาทิศทางเดิมต่อเนื่องไปอย่างน้อย 1-3 แท่ง M5 ถัดไป

Weak Crossover (สัญญาณคุณภาพปานกลาง):
  เกิดการตัดกันของเส้น EMA ด้วยขนาดเนื้อเทียนและปริมาณการซื้อขายปานกลางตามเกณฑ์ขั้นต่ำ
  EMA 20 ยังคงวิ่งแนวราบหรือมีความชันค่อนข้างน้อย
  C_strategy 0.50–0.79, Entry Score 60–74
  คาดหวัง: ราคาอาจวิ่งทดสอบ (Retest) จุดตัดแนวแกนเดิมก่อนที่จะเลือกไปต่อตามทิศทาง

False Crossover (สัญญาณหลอก):
  ราคาเกิดการตัดแกน EMA ชั่วคราวด้วยแท่งเทียน Doji หรือแท่งเนื้อแคบปริมาณการซื้อขายต่ำ
  มักเกิดขึ้นในสภาวะตลาดไซด์เวย์หรือสะสมพลัง ซึ่งระบบจะบล็อกผ่าน Condition 1 และ Condition 3 
  ไม่ส่งสัญญาณ

******************************************************************************--
#### 9. AUDIT REQUIREMENTS
******************************************************************************--
บันทึกข้อมูลต่อไปนี้ลง WORM Database ทุกรอบการประเมิน:

  - audit_id        : UUIDv4 ของรอบนี้
  - timestamp       : แสตมป์เวลาระบบ (UTC)
  - symbol          : ชื่อคู่เงิน
  - market_state    : สภาวะตลาดและ State Age ณ รอบนั้น
  - candle_ohlcv    : OHLCV ของแท่ง M5[-1]
  - atr_m5          : ค่า ATR_M5 ณ รอบนั้น
  - ema5_curr       : ค่า EMA 5 ล่าสุด
  - ema20_curr      : ค่า EMA 20 ล่าสุด
  - ema5_prev       : ค่า EMA 5 ย้อนหลัง 1 แท่ง
  - ema20_prev      : ค่า EMA 20 ย้อนหลัง 1 แท่ง
  - f_velocity      : คะแนน Crossover Velocity Factor
  - f_body          : คะแนน Candle Body Momentum Factor
  - f_trend         : คะแนน Trend Strength Factor
  - f_volume        : คะแนน Volume Confirmation Factor
  - entry_score_raw : คะแนนก่อนปรับ Lifecycle
  - entry_score     : คะแนนหลังปรับ Lifecycle และ State
  - block_score     : คะแนน Block Score รวม
  - s_alignment     : Crossover Separation Score
  - s_momentum      : Candle Close Dominance Score
  - s_volume        : Volume Confirmation Score
  - c_strategy      : คะแนน Strategy Confidence รวม
  - eligible        : true/false
  - action          : CALL / PUT / NO_SETUP
  - fail_reason_code: รหัสล้มเหลว (null ถ้าผ่าน)

******************************************************************************--
#### 10. OUTPUT CONTRACT (FROZEN SCHEMA)
******************************************************************************--
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_EMACrossover_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "ema_crossover" },
    "eligible":            { "type": "BOOLEAN" },
    "action":              { "type": "STRING", "enum": ["CALL", "PUT", "NO_SETUP"] },
    "entry_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "block_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "strategy_confidence": { "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "direction_confidence":{ "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "expected_state":      { "type": "STRING",
                             "enum": ["TRENDING_STRONG","TRENDING_WEAK",
                                      "BREAKOUT_EMERGING","UNCLEAR"] },
    "fail_reason_code":    { "type": "STRING" },
    "audit_id":            { "type": "STRING",
                             "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[4][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$" },
    "expiry":              { "type": "STRING", "const": "M5" },
    "details": {
      "type": "OBJECT",
      "properties": {
        "ema5":           { "type": "NUMBER" },
        "ema20":          { "type": "NUMBER" },
        "crossover_type": { "type": "STRING", "enum": ["GOLDEN_CROSS", "DEAD_CROSS", "NONE"] }
      },
      "required": ["ema5", "ema20", "crossover_type"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}

---

### ?? STRATEGY: Trend Group EMA RIBBON MOMENTUM

# FINAL SPECIFICATION: EMA RIBBON MOMENTUM (ema_ribbon_momentum)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

******************************************************************************--
#### 1. STRATEGY OVERVIEW
******************************************************************************--
ชื่อกลยุทธ์:
  EMA Ribbon Momentum
  (EMA Ribbon Pullback and Bounce Momentum Strategy)

วัตถุประสงค์:
  ตรวจจับสภาวะแนวโน้มที่มีแรงส่งแข็งแรงโดยใช้การเรียงตัวของเส้นค่าเฉลี่ยเคลื่อนที่แบบเอ็กซ์โพเนนเชียล 3 เส้น (EMA 3, EMA 5, EMA 8)
  และรอคอยการดึงตัวกลับชั่วคราว (Pullback) ของราคามาแตะหรือทดสอบระดับเส้นค่าเฉลี่ยแกนกลาง (EMA 5) 
  ก่อนที่ราคาจะดีดตัวกลับ (Bounce/Rejection) ไปตามทิศทางแนวโน้มหลัก
  โดยเสริมความปลอดภัยด้วยตัวกรองดัชนีชี้วัดกำลังตลาดสัมพัทธ์ระยะสั้น RSI(5) เพื่อป้องกันการซื้อขายในช่วงราคาสุดโต่งเกินไป
  และส่งสัญญาณ ณ วินาทีเปิดของแท่งถัดไปทันที โดยกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — มีสิทธิ์สร้างสัญญาณและส่งคำสั่งได้ทันทีที่พฤติกรรมการทดสอบและดีดกลับของราคาเกิดขึ้นสมบูรณ์ 
  และได้รับการยืนยันพารามิเตอร์ตามที่กำหนดไว้ในเงื่อนไขการเปิดสัญญาณ

ประเภทสัญญาณ:
  Trend-Following (Momentum Pullback) — เข้าซื้อเมื่อเกิดการย่อตัวในแนวโน้มเพื่อหาจุดเข้าเปรียบเทียบที่ดีที่สุด

Market States ที่เหมาะสม:
  TRENDING_STRONG   — แนวโน้มมีความชันและการเรียงตัวสมบูรณ์แบบ      [★★★★★]
  TRENDING_WEAK     — แนวโน้มกำลังตั้งตัวและเรียงเส้นเข้าหากัน        [★★★★☆]

Market States ที่ห้ามใช้เด็ดขาด:
  SIDEWAY_RANGE    — ตลาดแกว่งออกข้าง เส้นค่าเฉลี่ยพันกันเป็นเกลียว (No alignment)
  ACCUMULATION      — การสะสมของราคารอบเส้นค่าเฉลี่ย
  DISTRIBUTION     — ราคาผันผวนสูงบริเวณยอดคลื่น เกิดสัญญาณหลอกบ่อย
  LIQUIDITY_VOID    — ขาดปริมาณซื้อขายสะสมอย่างชัดเจน
  CHOPPY_UNCERTAIN  — ตลาดเหวี่ยงตัวอย่างไร้ทิศทาง
  UNCLEAR           — สถานะตลาดไม่ชัดเจนหรือขาดการประมวลผลข้อมูล

******************************************************************************--
#### 2. REQUIRED INPUTS
******************************************************************************--
1. M5 OHLCV Candles (ย้อนหลัง 100 แท่ง)
   เหตุผล: ใช้ประเมินและคำนวณเส้น EMA 3, EMA 5, EMA 8, RSI(5) และค่า ATR(14) ย้อนหลัง

2. ATR(14) บน M5
   เหตุผล: ใช้ในการวัดความกว้างขอบเขตของช่องว่างระหว่างเส้นเฉลี่ยและสเปรดดึงตัวกลับของราคา

3. EMA 3 (Fast), EMA 5 (Mid), และ EMA 8 (Slow) บน M5
   เหตุผล: คำนวณเพื่อใช้เป็นริบบอนความก้าวหน้าและการทดสอบแนวรับ/ต้านเคลื่อนที่ (Dynamic Support/Resistance)

4. RSI(5) บน M5
   เหตุผล: ตัววัดความเร็วโมเมนตัมและควบคุมการตัดสินใจซื้อขายเพื่อป้องกันการไล่ราคาที่จุดปลายทาง (Overbought/Oversold Zone)

5. Average Volume (เฉลี่ย 20 แท่ง M5)
   เหตุผล: ยืนยันปริมาณการซื้อขายในจังหวะการทดสอบและดีดตัวกลับ

6. Real-Time Tick Feed (ปัจจุบัน)
   เหตุผล: ป้องกันปัญหาการค้างของข้อมูลราคาโบรกเกอร์ (Broker Feed Freeze)

7. Market State + State Age (จาก Intelligence OS)
   เหตุผล: คัดกรองการทำงานเฉพาะช่วงเวลาที่ตลาดมีแนวโน้มไหลลื่นต่อเนื่อง

8. High Impact News Calendar (+/- 15 นาที)
   เหตุผล: ป้องกันผลกระทบจากข่าวสำคัญที่มีผลต่อเสถียรภาพริบบอน

******************************************************************************--
#### 3. ENTRY CONDITIONS
******************************************************************************--
ลำดับขั้นการประเมิน — ต้องผ่านทุกขั้นตามลำดับ หากขั้นใดล้มเหลวให้หยุดทันที

CONDITION 1 — Market State Eligibility
  ตรวจว่า Market State ปัจจุบันอยู่ใน Suitable States หรือไม่
  ผ่าน: TRENDING_STRONG, TRENDING_WEAK
  ไม่ผ่าน: หยุดทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — EMA Ribbon Perfect Alignment Check
  สำหรับ CALL (Bullish Ribbon):
    - EMA3[-1] > EMA5[-1] และ EMA5[-1] > EMA8[-1]
  สำหรับ PUT (Bearish Ribbon):
    - EMA3[-1] < EMA5[-1] และ EMA5[-1] < EMA8[-1]
  ไม่ผ่าน: หยุดทันที → fail_reason_code: RIBBON_NOT_ALIGNED

CONDITION 3 — Pullback and Bounce Confirmation
  สำหรับ CALL (Bullish Pullback & Bounce):
    - Pullback: Low[-2] <= EMA5[-2] × 1.0002 (ราคาต่ำสุดของแท่งก่อนหน้าสัมผัสหรือทะลุใต้ EMA 5 เล็กน้อย)
    - Bounce: Close[-1] > EMA5[-1] (ราคาปิดของแท่งล่าสุดยืนยันการเด้งกลับและปิดเหนือเส้น EMA 5 สำเร็จ)
  สำหรับ PUT (Bearish Pullback & Rejection):
    - Pullback: High[-2] >= EMA5[-2] / 1.0002 (ราคาสูงสุดของแท่งก่อนหน้าสัมผัสหรือทะลุเหนือ EMA 5 เล็กน้อย)
    - Bounce: Close[-1] < EMA5[-1] (ราคาปิดของแท่งล่าสุดยืนยันการกดตัวและปิดใต้เส้น EMA 5 สำเร็จ)
  ไม่ผ่าน: หยุดทันที → fail_reason_code: PULLBACK_BOUNCE_INVALID

CONDITION 4 — RSI(5) Momentum Range Filter
  สำหรับ CALL:
    - 40.0 <= RSI5[-1] <= 70.0 (โมเมนตัมขึ้นมั่นคง แต่ไม่สูงเกินไปจนเสี่ยงปรับฐาน)
  สำหรับ PUT:
    - 30.0 <= RSI5[-1] <= 60.0 (โมเมนตัมลงมั่นคง แต่ไม่ต่ำเกินไปจนเสี่ยงดีดกลับ)
  ไม่ผ่าน: หยุดทันที → fail_reason_code: RSI_OUT_OF_BOUNDS

CONDITION 5 — Minimum Candle Body Size
  ขนาดเนื้อเทียนของแท่งยืนยันการเด้งกลับต้องไม่สั้นเกินไปเพื่อให้มั่นใจในแรงผลักดัน
  Body Size = |Close[-1] - Open[-1]|
  เกณฑ์: Body Size > 0.05 × ATR_M5
  ไม่ผ่าน: หยุดทันที → fail_reason_code: DOJI_SETUP_INVALID

CONDITION 6 — Broker Feed Validity
  ตรวจว่า Tick Feed ไม่หยุดค้างเกิน 10 วินาที
  ไม่ผ่าน: หยุดทันที → fail_reason_code: BROKER_FEED_FREEZE

******************************************************************************--
#### 4. ENTRY SCORE LOGIC
******************************************************************************--
Entry Score (สเกล 0–100) คำนวณจาก 4 ปัจจัยถ่วงน้ำหนัก รวม 100%:

Factor 1 — Ribbon Expansion / Spacing (F_spacing) น้ำหนัก 35%
  วัดระยะการแผ่ขยายของริบบอนค่าเฉลี่ยเพื่อยืนยันพละกำลังของแนวโน้ม
  Spacing = |EMA3[-1] - EMA8[-1]| / ATR_M5
  F_spacing = Min(100, (Spacing / 0.15) × 100)
  ตีความ: สเปรดระยะห่างของริบบอนกว้างถึง 0.15×ATR = คะแนน 100

Factor 2 — Pullback Precision (F_pullback) น้ำหนัก 25%
  วัดระดับความแม่นยำในการย่อตัวสัมผัสกับระดับแกนกลาง (EMA 5)
  D_pullback = |Low_or_High[-2] - EMA5[-2]| / ATR_M5
  F_pullback = Max(0, 100 - (D_pullback / 0.10) × 100)
  ตีความ: จุดย่อตัวแตะเส้นเฉลี่ยพิกัดเดียวกันเป๊ะ = คะแนน 100 ห่าง 0.10×ATR = คะแนน 0

Factor 3 — RSI Momentum Score (F_rsi) น้ำหนัก 20%
  ให้คะแนนเชิงน้ำหนักแก่ค่า RSI ในจุดที่มีอัตราเร่งและโมเมนตัมกำลังดีที่สุด (Sweet Spot)
  สำหรับ CALL: Target_RSI = 55.0
    F_rsi = Max(0, 100 - (|RSI5[-1] - 55.0| / 15.0) × 100)
  สำหรับ PUT:  Target_RSI = 45.0
    F_rsi = Max(0, 100 - (|RSI5[-1] - 45.0| / 15.0) × 100)
  ตีความ: ค่า RSI ยิ่งใกล้ค่ากลางเป้าหมายตามเงื่อนไขมากที่สุด = คะแนนเต็ม 100

Factor 4 — Volume Confirmation (F_volume) น้ำหนัก 20%
  วัดการยืนยันปริมาณการซื้อขายในแท่งดีดตัวเพื่อแสดงการสนับสนุนของผู้ซื้อขายหลัก
  R_vol = Volume[-1] / Avg_Volume
  F_volume = Min(100, (R_vol / 1.20) × 100)
  ตีความ: ปริมาณซื้อขายมากกว่า 1.2 เท่าของค่าเฉลี่ยย้อนหลัง = คะแนน 100

สูตรรวม:
  Raw Entry Score = (0.35 × F_spacing) + (0.25 × F_pullback) + (0.20 × F_rsi) + (0.20 × F_volume)

ปรับตาม State Lifecycle:
  Fresh / Active   → ใช้ Raw Entry Score ตรง
  Late             → Entry Score = Raw Entry Score × 0.80
  Exhausted        → Block Score = 100 ทันที (ห้ามเข้า)

******************************************************************************--
#### 5. BLOCK SCORE LOGIC
******************************************************************************--
Block Score เริ่มที่ 0 สะสมจาก Soft Block และ Hard Block

*** SOFT BLOCK FACTORS (สะสมคะแนนความเสี่ยง) ***

  SF-1: ATR ปัจจุบัน > 1.6 × ATR เฉลี่ย 20 แท่ง
        → +30 คะแนน
        เหตุผล: ความผันผวนสัมบูรณ์สูงเกินปกติ ทำให้โครงสร้างริบบอนระยะสั้นบิดพริ้วได้ง่าย

  SF-2: ค่า RSI(5) ปะทะขอบโซนอันตราย (RSI > 67.0 สำหรับ CALL หรือ RSI < 33.0 สำหรับ PUT)
        → +25 คะแนน
        เหตุผล: ตลาดเข้าใกล้ระดับสูงสุดหรือต่ำสุดเกินไป เสี่ยงต่อการพักตัวรอบใหญ่

  SF-3: ปริมาณการซื้อขายในแท่งสัญญาณเหี่ยวแห้งชัดเจน (Volume[-1] < 0.60 × Avg_Volume)
        → +25 คะแนน
        เหตุผล: การดีดตัวบนปริมาณซื้อขายต่ำมีความน่าเชื่อถือทางสถิติน้อย

*** HARD BLOCK FACTORS (Block Score = 100 ทันที) ***

  HB-1: Market State เป็น SIDEWAY_RANGE, ACCUMULATION, DISTRIBUTION หรือ CHOPPY_UNCERTAIN
        → Block Score = 100

  HB-2: เส้นริบบอนเสียรูปทรงหรือมีการไขว้สลับทิศทาง (เช่น EMA3[-1] <= EMA5[-1] ในช่วงขาขึ้น)
        → Block Score = 100

  HB-3: ขนาดไส้เทียนฝั่งตรงข้ามยาวผิดปกติ (Opposite Wick > 1.5 × Body Size)
        → Block Score = 100

  HB-4: อยู่ในช่วงข่าว High Impact ±15 นาที
        → Block Score = 100

  HB-5: State Lifecycle = Exhausted
        → Block Score = 100

*** สูตร Block Score สุดท้าย ***
  IF มี Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = Sum(Soft Block คะแนนที่ติด), Max = 100

******************************************************************************--
#### 6. STRATEGY CONFIDENCE
******************************************************************************--
C_strategy คำนวณแบบค่าต่อเนื่อง (สเกล 0.0–1.0):

  C_strategy = (0.40 × S_spacing) + (0.40 × S_bounce) + (0.20 × S_rsi)

Sub-scores:

  S_spacing (Ribbon Separation Score):
    ประเมินระดับความแยกจากกันของริบบอนเพื่อยืนยันพละกำลังของแนวโน้ม
    S_spacing = Min(1.0, |EMA3[-1] - EMA8[-1]| / (0.10 × ATR_M5))

  S_bounce (Bounce Confirmation Score):
    ประเมินความเด็ดขาดในการดีดตัวกลับชิดขอบราคาของแท่งเทียนปัจจุบัน
    S_bounce = Min(1.0, |Close[-1] - EMA5[-1]| / (0.10 × ATR_M5))

  S_rsi (RSI Confidence Score):
    ประเมินตำแหน่งของ RSI เทียบกับเป้าหมายความมั่นคงทางทิศทาง
    สำหรับ CALL: S_rsi = 1.0 - Min(1.0, |RSI5[-1] - 55.0| / 20.0)
    สำหรับ PUT:  S_rsi = 1.0 - Min(1.0, |RSI5[-1] - 45.0| / 20.0)

******************************************************************************--
#### 7. FAIL CONDITIONS
******************************************************************************--
กลยุทธ์คืนค่า NO_SETUP ทันทีเมื่อเกิดกรณีต่อไปนี้:

  MARKET_STATE_BLOCKED    : Market State ไม่อยู่ใน Suitable States
  RIBBON_NOT_ALIGNED      : เส้นริบบอนเรียงตัวขัดแย้ง ไม่สอดคล้องตามเกณฑ์ขาขึ้น/ขาลง
  PULLBACK_BOUNCE_INVALID : ตรรกะการย่อตัวแตะแกนและการเด้งกลับปิดขอบทิศทางไม่ตรงตามกติกา
  RSI_OUT_OF_BOUNDS       : ค่าดัชนีชี้วัด RSI(5) อยู่นอกพื้นที่ปลอดภัยของทิศทาง
  DOJI_SETUP_INVALID      : เนื้อเทียนของแท่งยืนยันเล็กเกินไป (< 0.05 × ATR_M5)
  BROKER_FEED_FREEZE      : Tick Feed หยุดค้างเกิน 10 วินาที
  NEWS_BLACKOUT           : อยู่ในช่วงข่าว High Impact ±15 นาที

******************************************************************************--
#### 8. EXPECTED BEHAVIOR
******************************************************************************--
Strong Ribbon Trend Continuity (สัญญาณคุณภาพสูง):
  ริบบอนมีการเรียงตัวถ่างออกจากกันกว้างและมีมุมชันขึ้นชัดเจน ราคาดึงย้อนกลับมาสัมผัสระดับ EMA 5 พอดี
  และดีดตัวขึ้นปิดชิดขอบราคาสูงด้วยเนื้อเทียนที่มีปริมาณซื้อขายเด่นชัด
  C_strategy > 0.80, Entry Score > 75
  คาดหวัง: ราคาเคลื่อนที่ตามแนวทิศทางเดิมต่อเนื่องเพื่อสร้างสถานะชนะในระยะเวลา 5 นาที (M5 Expiry)

Mid-Quality Trend Continuity (สัญญาณคุณภาพปานกลาง):
  สัญญาณเกิดขึ้นภายใต้ข้อกำหนดครบถ้วน แต่ความชันริบบอนยังราบหรือช่องว่างระหว่างเส้นไม่ห่างกันเด่นชัด
  C_strategy 0.50–0.79, Entry Score 60–74
  คาดหวัง: ราคาอาจเคลื่อนช้าหรือย่ำรอบแนวริบบอนก่อนดีดตัวขึ้นเล็กน้อย มีความผันผวนสูง

False Pullback (สัญญาณหลอก):
  ราคาเกิดการดึงตัวกลับและทะลุระดับแนวริบบอนทั้งหมดและไม่เกิดการเด้งกลับปิดบนเส้น EMA 5
  กรณีนี้จะล้มเหลวในการทดสอบ Condition 3 หรือถูกจำกัดผ่านขอบเขตตัวบ่งชี้อื่นทันที
  ไม่ส่งสัญญาณ

******************************************************************************--
#### 9. AUDIT REQUIREMENTS
******************************************************************************--
บันทึกข้อมูลต่อไปนี้ลง WORM Database ทุกรอบการประเมิน:

  - audit_id        : UUIDv4 ของรอบนี้
  - timestamp       : แสตมป์เวลาระบบ (UTC)
  - symbol          : ชื่อคู่เงิน
  - market_state    : สภาวะตลาดและ State Age ณ รอบนั้น
  - candle_ohlcv    : OHLCV ของแท่ง M5[-1]
  - atr_m5          : ค่า ATR_M5 ณ รอบนั้น
  - ema3_curr       : ค่า EMA 3 ล่าสุด
  - ema5_curr       : ค่า EMA 5 ล่าสุด
  - ema8_curr       : ค่า EMA 8 ล่าสุด
  - rsi5_curr       : ค่า RSI(5) ล่าสุด
  - close_curr      : ราคาปิดล่าสุด
  - f_spacing       : คะแนน Ribbon Expansion Factor
  - f_pullback      : คะแนน Pullback Precision Factor
  - f_rsi           : คะแนน RSI Momentum Factor
  - f_volume        : คะแนน Volume Confirmation Factor
  - entry_score_raw : คะแนนก่อนปรับ Lifecycle
  - entry_score     : คะแนนหลังปรับ Lifecycle และ State
  - block_score     : คะแนน Block Score รวม
  - s_spacing       : Ribbon Separation Score
  - s_bounce        : Bounce Confirmation Score
  - s_rsi           : RSI Confidence Score
  - c_strategy      : คะแนน Strategy Confidence รวม
  - eligible        : true/false
  - action          : CALL / PUT / NO_SETUP
  - fail_reason_code: รหัสล้มเหลว (null ถ้าผ่าน)

******************************************************************************--
#### 10. OUTPUT CONTRACT (FROZEN SCHEMA)
******************************************************************************--
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_EMARibbonMomentum_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "ema_ribbon_momentum" },
    "eligible":            { "type": "BOOLEAN" },
    "action":              { "type": "STRING", "enum": ["CALL", "PUT", "NO_SETUP"] },
    "entry_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "block_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "strategy_confidence": { "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "direction_confidence":{ "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "expected_state":      { "type": "STRING",
                             "enum": ["TRENDING_STRONG","TRENDING_WEAK","UNCLEAR"] },
    "fail_reason_code":    { "type": "STRING" },
    "audit_id":            { "type": "STRING",
                             "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[4][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$" },
    "expiry":              { "type": "STRING", "const": "M5" },
    "details": {
      "type": "OBJECT",
      "properties": {
        "ema3": { "type": "NUMBER" },
        "ema5": { "type": "NUMBER" },
        "ema8": { "type": "NUMBER" },
        "rsi5": { "type": "NUMBER" }
      },
      "required": ["ema3", "ema5", "ema8", "rsi5"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}

---

### ?? STRATEGY: Trend Group MACD CROSSOVER

# FINAL SPECIFICATION: MACD CROSSOVER (macd_crossover)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

******************************************************************************--
#### 1. STRATEGY OVERVIEW
******************************************************************************--
ชื่อกลยุทธ์:
  MACD Crossover
  (MACD Major Trend Shift Crossover Strategy)

วัตถุประสงค์:
  ตรวจจับการตัดกันระหว่างเส้นสัญญาณ MACD (Moving Average Convergence Divergence) 
  และเส้น Signal Line เพื่อหาจุดเปลี่ยนแนวโน้มหลัก (Major Trend Shift)
  โดยกลยุทธ์จะจำกัดการเทรดเฉพาะกรณีที่เกิดการกลับตัวในฝั่งตรงข้ามของแนวระดับศูนย์ (Zero Line)
  เพื่อเพิ่มแต้มต่อเชิงสถิติ (Golden Cross ต่ำกว่า 0 และ Dead Cross สูงกว่า 0)
  และส่งสัญญาณ ณ วินาทีเปิดของแท่งถัดไปทันที โดยกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — สามารถสร้างสัญญาณส่งคำสั่งด้วยตัวเองตามทฤษฎีการตัดกันของแนวโน้ม 
  โดยไม่ต้องยืนยันจากกลยุทธ์อินดิเคเตอร์อื่น

ประเภทสัญญาณ:
  Trend-Following / Trend-Reversal — ค้นหาจุดเริ่มต้นแนวโน้มใหม่จากการเปลี่ยนรอบของราคาระยะกลาง

Market States ที่เหมาะสม:
  TRENDING_STRONG   — ตลาดเกิดแนวโน้มความชันสูงชัดเจน           [★★★★★]
  TRENDING_WEAK     — แนวโน้มเริ่มชะลอหรือกำลังฟื้นตัวใหม่         [★★★★☆]
  BREAKOUT_EMERGING — ราคาตัดทะลุกรอบเพื่อตั้งเทรนด์ใหม่           [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  SIDEWAY_RANGE    — ตลาดเคลื่อนที่ในกรอบแคบ เส้นตัดสลับกันจนสูญเสียโมเมนตัม
  ACCUMULATION      — การสะสมของราคารอบศูนย์ ไม่มีทิศทาง
  DISTRIBUTION     — ราคาผันผวนสูงบริเวณยอดคลื่น เกิดสัญญาณหลอกบ่อย
  LIQUIDITY_VOID    — ปริมาณการซื้อขายเบาบาง อินดิเคเตอร์แสดงค่าผิดเพี้ยน
  CHOPPY_UNCERTAIN  — ตลาดเหวี่ยงตัวไร้ทิศทาง ไม่เหมาะกับการตามแนวโน้ม
  UNCLEAR           — สถานะตลาดไม่สามารถคำนวณหรือยืนยันได้

******************************************************************************--
#### 2. REQUIRED INPUTS
******************************************************************************--
1. M5 OHLCV Candles (ย้อนหลัง 100 แท่ง)
   เหตุผล: คำนวณอินดิเคเตอร์ MACD (12, 26, 9) และหาค่า ATR(14) ย้อนหลัง

2. ATR(14) บน M5
   เหตุผล: ใช้ประเมินขนาดความกว้างของสัญญาณและการแกว่งตัวของราคาเพื่อตัดความเสี่ยง

3. MACD Line (12, 26) และ Signal Line (9) บน M5
   เหตุผล: ตรวจสอบพิกัดความต่างและการตัดกันของเส้นหลักและเส้นสัญญาณ

4. Average Volume (เฉลี่ย 20 แท่ง M5)
   เหตุผล: ประเมินความหนาแน่นปริมาณการซื้อขายขณะตัดกัน (Volume Confirmation)

5. Real-Time Tick Feed (ปัจจุบัน)
   เหตุผล: ป้องกันความล่าช้าและการหยุดค้างของข้อมูลราคาโบรกเกอร์ (Broker Feed Freeze)

6. Market State + State Age (จาก Intelligence OS)
   เหตุผล: คัดกรองการทำงานให้อยู่ในสภาวะตลาดที่มีทิศทางเอื้ออำนวยเท่านั้น

7. High Impact News Calendar (+/- 15 นาที)
   เหตุผล: Hard Block ช่วงที่มีความเสี่ยงผันผวนรุนแรงจากกระแสข่าวเศรษฐกิจ

******************************************************************************--
#### 3. ENTRY CONDITIONS
******************************************************************************--
ลำดับขั้นการประเมิน — ต้องผ่านทุกขั้นตามลำดับ หากขั้นใดล้มเหลวให้หยุดทันที

CONDITION 1 — Market State Eligibility
  ตรวจว่า Market State ปัจจุบันอยู่ใน Suitable States หรือไม่
  ผ่าน: TRENDING_STRONG, TRENDING_WEAK, BREAKOUT_EMERGING
  ไม่ผ่าน: หยุดทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — MACD Crossover Direction and Zero Line Position
  สำหรับ CALL (Golden Cross Below Zero):
    - MACD[-2] <= Signal[-2] (ก่อนหน้านี้ MACD อยู่ต่ำกว่าหรือเท่ากับ Signal Line)
    - MACD[-1] > Signal[-1]  (ปัจจุบัน MACD ตัดขึ้นเหนือ Signal Line สำเร็จ)
    - MACD[-1] < -0.05 × ATR_M5 (จุดตัดต้องอยู่ใต้แนวระดับศูนย์และห่างเพียงพอเพื่อความปลอดภัย)
  สำหรับ PUT (Dead Cross Above Zero):
    - MACD[-2] >= Signal[-2] (ก่อนหน้านี้ MACD อยู่เหนือหรือเท่ากับ Signal Line)
    - MACD[-1] < Signal[-1]  (ปัจจุบัน MACD ตัดลงใต้ Signal Line สำเร็จ)
    - MACD[-1] > 0.05 × ATR_M5 (จุดตัดต้องอยู่เหนือแนวระดับศูนย์และห่างเพียงพอเพื่อความปลอดภัย)
  ไม่ผ่าน: หยุดทันที → fail_reason_code: MACD_CROSSOVER_INVALID

CONDITION 3 — Minimum Candle Body Size
  ขนาดเนื้อเทียนของแท่งตัดสัญญาณต้องไม่เล็กเป็นลักษณะ Doji หรือไร้แรงกระตุ้น
  Body Size = |Close[-1] - Open[-1]|
  เกณฑ์: Body Size > 0.10 × ATR_M5
  ไม่ผ่าน: หยุดทันที → fail_reason_code: CANDLE_BODY_TOO_SMALL

CONDITION 4 — Volume Confirmation Check
  ปริมาณซื้อขายในแท่งล่าสุดต้องมีความหนาแน่นเพื่อสนับสนุนทิศทางการตัดกัน
  Volume[-1] >= 0.60 × Avg_Volume
  ไม่ผ่าน: หยุดทันที → fail_reason_code: INSUFFICIENT_VOLUME

CONDITION 5 — Broker Feed Validity
  ตรวจว่า Tick Feed ไม่หยุดค้างเกิน 10 วินาที
  ไม่ผ่าน: หยุดทันที → fail_reason_code: BROKER_FEED_FREEZE

******************************************************************************--
#### 4. ENTRY SCORE LOGIC
******************************************************************************--
Entry Score (สเกล 0–100) คำนวณจาก 4 ปัจจัยถ่วงน้ำหนัก รวม 100%:

Factor 1 — MACD Line Distance from Zero (F_distance) น้ำหนัก 30%
  วัดระยะห่างระหว่างจุดตัดของเส้น MACD กับแนวระดับศูนย์ (Zero Line)
  D_macd = |MACD[-1]| / ATR_M5
  F_distance = Min(100, (D_macd / 0.50) × 100)
  ตีความ: จุดตัดยิ่งห่างจากแกนกลาง (0.50×ATR ขึ้นไป) จะให้คะแนนเต็ม 100 เนื่องจากมีช่องว่างให้ราคาวิ่งกลับตัวได้ไกล

Factor 2 — Crossover Angle / Velocity (F_angle) น้ำหนัก 25%
  วัดความแรงหรือความชันของมุมการตัดกันระหว่าง MACD และ Signal
  V_macd = |(MACD[-1] - Signal[-1]) - (MACD[-2] - Signal[-2])| / ATR_M5
  F_angle = Min(100, (V_macd / 0.10) × 100)
  ตีความ: ความชันของมุมตัดที่ชัดเจน (0.10×ATR ขึ้นไป) สะท้อนแรงส่งสูงสุด

Factor 3 — Candle Body Size (F_body) น้ำหนัก 20%
  วัดขนาดเนื้อเทียนของแท่งเทียนที่นำไปสู่การตัดกันของ MACD
  R_body = |Close[-1] - Open[-1]| / ATR_M5
  F_body = Min(100, (R_body / 0.50) × 100)
  ตีความ: เนื้อเทียนยาวเท่ากับ 0.5×ATR = คะแนน 100

Factor 4 — Volume Confirmation (F_volume) น้ำหนัก 25%
  วัดการยืนยันปริมาณการซื้อขายเฉลี่ยในแท่งสัญญาณ
  R_vol = Volume[-1] / Avg_Volume
  F_volume = Min(100, (R_vol / 1.50) × 100)
  ตีความ: Volume สูงกว่า 1.5 เท่าของค่าเฉลี่ย 20 แท่ง = คะแนน 100

สูตรรวม:
  Raw Entry Score = (0.30 × F_distance) + (0.25 × F_angle) + (0.20 × F_body) + (0.25 × F_volume)

ปรับตาม State Lifecycle:
  Fresh / Active   → ใช้ Raw Entry Score ตรง
  Late             → Entry Score = Raw Entry Score × 0.80
  Exhausted        → Block Score = 100 ทันที (ห้ามเข้า)

ปรับตาม BREAKOUT_EMERGING State:
  Entry Score = Raw Entry Score × 0.85

******************************************************************************--
#### 5. BLOCK SCORE LOGIC
******************************************************************************--
Block Score เริ่มที่ 0 สะสมจาก Soft Block และ Hard Block

*** SOFT BLOCK FACTORS (สะสมคะแนนความเสี่ยง) ***

  SF-1: ATR ปัจจุบัน > 1.6 × ATR เฉลี่ย 20 แท่ง
        → +30 คะแนน
        เหตุผล: ความผันผวนภายนอกสูงเกินไป เสี่ยงต่อการกลับตัวกระชากสั้นๆ (Whipsaw)

  SF-2: ปริมาณการซื้อขายในแท่งสัญญาณต่ำกว่าค่าเฉลี่ย (Volume[-1] < 0.80 × Avg_Volume)
        → +25 คะแนน
        เหตุผล: การตัดกันที่ไม่มีปริมาณหนุนอาจนำไปสู่การเคลื่อนที่เฉื่อยและตัดสลับกลับที่เดิม

  SF-3: ระยะจุดตัด MACD เข้าใกล้ศูนย์มากเกินไป (|MACD[-1]| < 0.08 × ATR_M5)
        → +25 คะแนน
        เหตุผล: โซนก้ำกึ่งใกล้ Zero Line มักมีแนวโน้มอ่อนแอและสับสนสูง

*** HARD BLOCK FACTORS (Block Score = 100 ทันที) ***

  HB-1: Market State เป็น SIDEWAY_RANGE, ACCUMULATION, DISTRIBUTION หรือ CHOPPY_UNCERTAIN
        → Block Score = 100

  HB-2: ทิศทางการตัดกันและตำแหน่งของศูนย์ขัดแย้งกัน 
        (เช่น Golden Cross เหนือ 0 หรือ Dead Cross ใต้ 0)
        → Block Score = 100

  HB-3: ขนาดไส้เทียนฝั่งตรงข้ามยาวเกินไป (Opposite Wick > 1.5 × Body Size)
        → Block Score = 100

  HB-4: อยู่ในช่วงข่าว High Impact ±15 นาที
        → Block Score = 100

  HB-5: State Lifecycle = Exhausted
        → Block Score = 100

*** สูตร Block Score สุดท้าย ***
  IF มี Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = Sum(Soft Block คะแนนที่ติด), Max = 100

******************************************************************************--
#### 6. STRATEGY CONFIDENCE
******************************************************************************--
C_strategy คำนวณแบบค่าต่อเนื่อง (สเกล 0.0–1.0):

  C_strategy = (0.40 × S_dist) + (0.40 × S_angle) + (0.20 × S_volume)

Sub-scores:

  S_dist (Zero Line Distance Score):
    ประเมินระดับความอยู่ลึก/สูงของเส้น MACD ในโซนกลับตัวเพื่อรับประกันแต้มต่อที่ดี
    S_dist = Min(1.0, |MACD[-1]| / (0.40 × ATR_M5))

  S_angle (Crossover Angle Score):
    ประเมินความเฉียบและความห่างของทิศทางการตัดกัน
    S_angle = Min(1.0, |MACD[-1] - Signal[-1]| / (0.05 × ATR_M5))

  S_volume (Volume Confirmation Score):
    ประเมินการหนุนของปริมาณการซื้อขายในเชิงความเชื่อมั่น
    S_volume = Min(1.0, Volume[-1] / (1.20 × Avg_Volume))

******************************************************************************--
#### 7. FAIL CONDITIONS
******************************************************************************--
กลยุทธ์คืนค่า NO_SETUP ทันทีเมื่อเกิดกรณีต่อไปนี้:

  MARKET_STATE_BLOCKED    : Market State ไม่อยู่ใน Suitable States
  MACD_CROSSOVER_INVALID  : การตัดกันไม่สมบูรณ์ หรือทิศทาง/ขอบเขตความกว้างขัดแย้งกับ Zero Line
  CANDLE_BODY_TOO_SMALL   : เนื้อเทียนของแท่งสัญญาณเล็กเกินไป (< 0.10 × ATR_M5)
  INSUFFICIENT_VOLUME     : ปริมาณการซื้อขายในแท่งตัดสัญญาณต่ำกว่า 0.60 × Avg_Volume
  BROKER_FEED_FREEZE      : Tick Feed หยุดค้างเกิน 10 วินาที
  NEWS_BLACKOUT           : อยู่ในช่วงข่าว High Impact ±15 นาที

******************************************************************************--
#### 8. EXPECTED BEHAVIOR
******************************************************************************--
Strong Trend Shift Crossover (สัญญาณคุณภาพสูง):
  เกิดการตัดกันระหว่าง MACD และ Signal Line ลึกลงไปใต้ 0 (สำหรับ CALL) หรือเหนือ 0 (สำหรับ PUT)
  พร้อมทิศทางมุมตัดที่กว้างและมีปริมาณการซื้อขายสะสมเข้ามาสูงชัดเจน (Volume[-1] > 1.3 × Avg_Volume)
  C_strategy > 0.80, Entry Score > 75
  คาดหวัง: ราคาจะไหลต่อเนื่องตามทิศทางการกลับตัวส่งผลดีต่อตัวเลือกการปิด M5 Expiry

Weak Crossover (สัญญาณคุณภาพปานกลาง):
  เกิดการตัดกันผ่านเกณฑ์ขั้นต่ำ แต่ตำแหน่งพิกัดอยู่ใกล้ขอบเขตปลอดภัยของศูนย์ 
  หรือความกว้างมุมตัดแคบ ทำให้ราคายังมีโอกาสหน่วงตัว
  C_strategy 0.50–0.79, Entry Score 60–74
  คาดหวัง: ราคามีโอกาสแกว่งตัวทดสอบแนวระดับเดิมชั่วคราวก่อนที่จะเคลื่อนไปต่อ

False Crossover (สัญญาณหลอก):
  เกิดสัญญาณการตัดกันในจุดอับศูนย์ หรือแท่งเทียน Doji แคบๆ ซึ่งจะถูกคัดกรองทิ้งทันทีในระบบคัดกรองเบื้องต้น
  ไม่ส่งสัญญาณ

******************************************************************************--
#### 9. AUDIT REQUIREMENTS
******************************************************************************--
บันทึกข้อมูลต่อไปนี้ลง WORM Database ทุกรอบการประเมิน:

  - audit_id        : UUIDv4 ของรอบนี้
  - timestamp       : แสตมป์เวลาระบบ (UTC)
  - symbol          : ชื่อคู่เงิน
  - market_state    : สภาวะตลาดและ State Age ณ รอบนั้น
  - candle_ohlcv    : OHLCV ของแท่ง M5[-1]
  - atr_m5          : ค่า ATR_M5 ณ รอบนั้น
  - macd_curr       : ค่า MACD Line ล่าสุด
  - signal_curr     : ค่า Signal Line ล่าสุด
  - macd_prev       : ค่า MACD Line ย้อนหลัง 1 แท่ง
  - signal_prev     : ค่า Signal Line ย้อนหลัง 1 แท่ง
  - f_distance      : คะแนน MACD Distance Factor
  - f_angle         : คะแนน Crossover Angle Factor
  - f_body          : คะแนน Candle Body Size Factor
  - f_volume        : คะแนน Volume Confirmation Factor
  - entry_score_raw : คะแนนก่อนปรับ Lifecycle
  - entry_score     : คะแนนหลังปรับ Lifecycle และ State
  - block_score     : คะแนน Block Score รวม
  - s_dist          : Zero Line Distance Score
  - s_angle         : Crossover Angle Score
  - s_volume        : Volume Confirmation Score
  - c_strategy      : คะแนน Strategy Confidence รวม
  - eligible        : true/false
  - action          : CALL / PUT / NO_SETUP
  - fail_reason_code: รหัสล้มเหลว (null ถ้าผ่าน)

******************************************************************************--
#### 10. OUTPUT CONTRACT (FROZEN SCHEMA)
******************************************************************************--
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_MACDCrossover_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "macd_crossover" },
    "eligible":            { "type": "BOOLEAN" },
    "action":              { "type": "STRING", "enum": ["CALL", "PUT", "NO_SETUP"] },
    "entry_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "block_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "strategy_confidence": { "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "direction_confidence":{ "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "expected_state":      { "type": "STRING",
                             "enum": ["TRENDING_STRONG","TRENDING_WEAK",
                                      "BREAKOUT_EMERGING","UNCLEAR"] },
    "fail_reason_code":    { "type": "STRING" },
    "audit_id":            { "type": "STRING",
                             "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[4][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$" },
    "expiry":              { "type": "STRING", "const": "M5" },
    "details": {
      "type": "OBJECT",
      "properties": {
        "macd_line":      { "type": "NUMBER" },
        "signal_line":    { "type": "NUMBER" },
        "macd_histogram": { "type": "NUMBER" }
      },
      "required": ["macd_line", "signal_line", "macd_histogram"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}

---

### ?? STRATEGY: Trend Group TRIPLE CONFLUENCE

# FINAL SPECIFICATION: TRIPLE CONFLUENCE (triple_confluence)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

******************************************************************************--
#### 1. STRATEGY OVERVIEW
******************************************************************************--
ชื่อกลยุทธ์:
  Triple Confluence
  (Trend Sniper EMA, S&R, and Price Action Confluence Strategy)

วัตถุประสงค์:
  ตรวจจับและระบุจุดเข้าซื้อขายในทิศทางเดียวกับแนวโน้มหลัก (Trend-Following) 
  โดยอาศัยความสอดคล้องจาก 3 ปัจจัยหลัก (Triple Confluence):
    1. ทิศทางแนวโน้ม (Trend Check): เปรียบเทียบตำแหน่งและความชันของ EMA 20 และ EMA 50
    2. จุดย่อตัวแตะแนวสำคัญ (Dynamic/Static S&R): การทดสอบเส้นเฉลี่ยเคลื่อนที่หรือแนวรับ/ต้านในอดีต (Local Support/Resistance ย้อนหลัง 10 แท่ง M5)
    3. แท่งเทียนพฤติกรรมราคา (Price Action Patterns): ยืนยันด้วย Hammer, Shooting Star, Bullish Engulfing หรือ Bearish Engulfing
  กลยุทธ์จะส่งสัญญาณ ณ วินาทีเปิดของแท่งถัดไปทันที โดยกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — สัญญาณเปิดออเดอร์จะถูกสร้างเมื่อปัจจัยทั้ง 3 ประสานกันอย่างสมบูรณ์แบบโดยไม่ต้องรอตัวชี้วัดอื่น

ประเภทสัญญาณ:
  Trend-Following / Pullback Reversal — ติดตามเทรนด์หลักของตลาดจากการดีดตัวในระดับราคาสำคัญ

Market States ที่เหมาะสม:
  TRENDING_STRONG   — ตลาดเป็นแนวโน้มชัดเจนและแข็งแกร่ง             [★★★★★]
  TRENDING_WEAK     — แนวโน้มเริ่มชะลอแต่ยังทิศทางเดินหน้าต่อเนื่อง     [★★★★☆]

Market States ที่ห้ามใช้เด็ดขาด:
  SIDEWAY_RANGE    — ราคาแกว่งขอบแนวระดับบ่อยครั้ง จนขาดทิศทางแนวโน้มหลัก
  ACCUMULATION      — ตลาดเข้าสู่สภาวะรอการเบรคตัว ไม่สามารถคำนวณเทรนด์ได้
  DISTRIBUTION     — ตลาดปั่นป่วนตรงจุดสูงสุด
  LIQUIDITY_VOID    — การขาดปริมาณการซื้อขายทำให้เส้นเฉลี่ยวัดทิศทางผิดพลาด
  CHOPPY_UNCERTAIN  — ตลาดสะบัดตัวสับสน ไร้ระเบียบแบบแผน
  UNCLEAR           — ปัญหาข้อมูลส่งเสริมสภาวะตลาดสับสน

******************************************************************************--
#### 2. REQUIRED INPUTS
******************************************************************************--
1. M5 OHLCV Candles (ย้อนหลัง 100 แท่ง)
   เหตุผล: คำนวณค่า EMA 20, EMA 50, ระดับ Local Support/Resistance ย้อนหลัง และค่า ATR(14)

2. ATR(14) บน M5
   เหตุผล: Normalize ระยะการทดสอบแนวรับ/ต้านและขนาดโครงสร้างแท่งเทียนให้มีความเที่ยงตรง

3. EMA 20 และ EMA 50 บน M5
   เหตุผล: ตรวจสอบและระบุแนวโน้มหลักและใช้เป็นจุดแนวรับ/ต้านแบบเคลื่อนที่ (Dynamic S&R)

4. Local S/R Database (คำนวณจาก Swing High/Low ย้อนหลัง 10 แท่งเสร็จสมบูรณ์)
   เหตุผล: หาแนวต้าน (Local Resistance) และแนวรับ (Local Support) ในกรอบการทดสอบล่าสุด

5. Price Action Detector (ตรวจพบบนแท่ง M5[-1] และ [-2])
   เหตุผล: ยืนยันพฤติกรรมแรงซื้อแรงขายสะท้อนกลับ (Hammer / Shooting Star / Engulfing)

6. Average Volume (เฉลี่ย 20 แท่ง M5)
   เหตุผล: ยืนยันความน่าเชื่อถือของการดีดตัวสะท้อนกลับ

7. Real-Time Tick Feed (ปัจจุบัน)
   เหตุผล: ตรวจสอบการค้างของข้อมูลราคาโบรกเกอร์ (Broker Feed Freeze)

8. Market State + State Age (จาก Intelligence OS)
   เหตุผล: จำกัดพื้นที่ปฏิบัติงานเฉพาะในสภาวะที่มีแนวโน้มหนาแน่นเท่านั้น

******************************************************************************--
#### 3. ENTRY CONDITIONS
******************************************************************************--
ลำดับขั้นการประเมิน — ต้องผ่านทุกขั้นตามลำดับ หากขั้นใดล้มเหลวให้หยุดทันที

CONDITION 1 — Market State Eligibility
  ตรวจว่า Market State ปัจจุบันอยู่ใน Suitable States หรือไม่
  ผ่าน: TRENDING_STRONG, TRENDING_WEAK
  ไม่ผ่าน: หยุดทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — Macro Trend Alignment Check
  สำหรับ CALL (Uptrend):
    - EMA20[-1] > EMA50[-1]
  สำหรับ PUT (Downtrend):
    - EMA20[-1] < EMA50[-1]
  ไม่ผ่าน: หยุดทันที → fail_reason_code: TREND_MISALIGNED

CONDITION 3 — Dynamic and Static Support/Resistance Test
  สำหรับ CALL (Dynamic/Static Support Test):
    - ต้องทดสอบ Dynamic EMA: Low[-1] <= EMA20[-1] × 1.0005 หรือ Low[-1] <= EMA50[-1] × 1.0005
    - ต้องทดสอบ Static Support: Low[-1] <= Local_Support × 1.001 (คำนวณจากจุดต่ำสุดของแท่ง [-11] ถึง [-2])
  สำหรับ PUT (Dynamic/Static Resistance Test):
    - ต้องทดสอบ Dynamic EMA: High[-1] >= EMA20[-1] × 0.9995 หรือ High[-1] >= EMA50[-1] × 0.9995
    - ต้องทดสอบ Static Resistance: High[-1] >= Local_Resistance × 0.999 (คำนวณจากจุดสูงสุดของแท่ง [-11] ถึง [-2])
  ไม่ผ่าน: หยุดทันที → fail_reason_code: LEVEL_TEST_FAILED

CONDITION 4 — Price Action Pattern Confirmation
  สำหรับ CALL: ต้องเกิดแท่งกลับตัว Bullish ในแท่งล่าสุด
    - Hammer: (Total_Range > 0) และ (Lower_Wick >= Body × 1.5) และ (Upper_Wick <= Body × 0.5) และ (Body / Total_Range >= 0.1)
    - Bullish Engulfing: (Close[-2] < Open[-2]) และ (Close[-1] > Open[-1]) และ (Open[-1] <= Close[-2] × 1.0002) และ (Close[-1] >= Open[-2] × 0.9998)
  สำหรับ PUT: ต้องเกิดแท่งกลับตัว Bearish ในแท่งล่าสุด
    - Shooting Star: (Total_Range > 0) และ (Upper_Wick >= Body × 1.5) และ (Lower_Wick <= Body × 0.5) และ (Body / Total_Range >= 0.1)
    - Bearish Engulfing: (Close[-2] > Open[-2]) และ (Close[-1] < Open[-1]) และ (Open[-1] >= Close[-2] × 0.9998) และ (Close[-1] <= Open[-2] × 1.0002)
  ไม่ผ่าน: หยุดทันที → fail_reason_code: PRICE_ACTION_INVALID

CONDITION 5 — Broker Feed Validity
  ตรวจว่า Tick Feed ไม่หยุดค้างเกิน 10 วินาที
  ไม่ผ่าน: หยุดทันที → fail_reason_code: BROKER_FEED_FREEZE

******************************************************************************--
#### 4. ENTRY SCORE LOGIC
******************************************************************************--
Entry Score (สเกล 0–100) คำนวณจาก 4 ปัจจัยถ่วงน้ำหนัก รวม 100%:

Factor 1 — EMA Spread & Alignment (F_trend) น้ำหนัก 30%
  วัดแรงส่งและช่องระยะห่างระหว่างแนวโน้มระยะสั้นและระยะกลางเพื่อยืนยันพละกำลังแนวโน้มหลัก
  Spread = |EMA20[-1] - EMA50[-1]| / ATR_M5
  F_trend = Min(100, (Spread / 0.20) × 100)
  ตีความ: ค่าช่องว่างริบบอนกว้างถึง 0.20×ATR = คะแนนเต็ม 100

Factor 2 — S/R Touch Proximity (F_sr) น้ำหนัก 25%
  วัดความแม่นยำในการสัมผัสแนวรับ/ต้านในอดีต (Static Level)
  สำหรับ CALL: D_sr = |Low[-1] - Local_Support| / ATR_M5
  สำหรับ PUT:  D_sr = |High[-1] - Local_Resistance| / ATR_M5
  F_sr = Max(0, 100 - (D_sr / 0.05) × 100)
  ตีความ: จุดย้อนมาสัมผัสระดับแบบชนพอดีเป๊ะ = คะแนน 100 ห่าง 0.05×ATR = คะแนน 0

Factor 3 — Dynamic EMA Touch Proximity (F_ema) น้ำหนัก 25%
  วัดความใกล้ชิดของจุดราคาต่ำสุด/สูงสุดในการทดสอบเส้น EMA 20 หรือ EMA 50
  D_ema = Min(|Low_or_High[-1] - EMA20[-1]|, |Low_or_High[-1] - EMA50[-1]|) / ATR_M5
  F_ema = Max(0, 100 - (D_ema / 0.05) × 100)
  ตีความ: ราคาปะทะเส้นค่าเฉลี่ยระยะใดระยะหนึ่งได้ใกล้เคียงที่สุด = คะแนน 100

Factor 4 — Candle Pattern Quality (F_pattern) น้ำหนัก 20%
  วัดระดับคุณภาพของสัดส่วนพฤติกรรมราคา (Price Action)
  สำหรับรูปแบบ Engulfing: R_eng = Body[-1] / Body[-2]
    F_pattern = Min(100, ((R_eng - 1.0) / 1.0) × 50 + 50)  (หาก R_eng >= 1.0)
  สำหรับรูปแบบ Hammer / Shooting Star: R_wick = Wick_target / Body[-1]
    F_pattern = Min(100, ((R_wick - 1.5) / 1.5) × 50 + 50) (หาก R_wick >= 1.5)
  ตีความ: พฤติกรรมกลืนกินหรือไส้เทียนที่ยาวข่มคู่แข่งอย่างเด็ดขาด = คะแนนเต็ม 100 (เกณฑ์ขั้นต่ำยอมรับที่ 70 คะแนน)

สูตรรวม:
  Raw Entry Score = (0.30 × F_trend) + (0.25 × F_sr) + (0.25 × F_ema) + (0.20 × F_pattern)

ปรับตาม State Lifecycle:
  Fresh / Active   → ใช้ Raw Entry Score ตรง
  Late             → Entry Score = Raw Entry Score × 0.80
  Exhausted        → Block Score = 100 ทันที (ห้ามเข้า)

******************************************************************************--
#### 5. BLOCK SCORE LOGIC
******************************************************************************--
Block Score เริ่มที่ 0 สะสมจาก Soft Block และ Hard Block

*** SOFT BLOCK FACTORS (สะสมคะแนนความเสี่ยง) ***

  SF-1: ATR ปัจจุบัน > 1.7 × ATR เฉลี่ย 20 แท่ง
        → +30 คะแนน
        เหตุผล: ความผันผวนสัมบูรณ์สูงเกินขีดความเชื่อมั่น โครงสร้าง PA อาจชำรุดเสียหาย

  SF-2: ระดับเส้นค่าเฉลี่ย EMA 20 และ EMA 50 กำลังบีบเข้าหากันแคบลง (Spread < 0.05 × ATR_M5)
        → +30 คะแนน
        เหตุผล: บ่งชี้ถึงภาวะแนวโน้มเริ่มหมดกำลังและอาจเข้าสู่สภาวะไซด์เวย์เร็วๆ นี้

  SF-3: ปริมาณการซื้อขายในแท่งกลับตัวน้อยกว่าค่าเฉลี่ย (Volume[-1] < 0.70 × Avg_Volume)
        → +20 คะแนน
        เหตุผล: แรงดีดกลับที่ไม่มีปริมาณหนุนสร้างโอกาส False Pullback ได้ง่าย

*** HARD BLOCK FACTORS (Block Score = 100 ทันที) ***

  HB-1: Market State เป็น SIDEWAY_RANGE, ACCUMULATION, DISTRIBUTION หรือ CHOPPY_UNCERTAIN
        → Block Score = 100

  HB-2: เกิดรูปแบบแท่งเทียนที่ลังเล (Doji/Indecision) หรือเกิดสัญญาณกลับทางขัดแย้งกับเทรนด์
        → Block Score = 100

  HB-3: เส้นค่าเฉลี่ย EMA 20 และ EMA 50 พิ่งเกิดการไขว้สลับทิศทาง (Crossover) ภายใน 3 แท่งล่าสุด
        → Block Score = 100 (สกัดช่วงเริ่มต้นสปริงตัวของเทรนด์ที่ยังไม่เสถียร)

  HB-4: อยู่ในช่วงข่าว High Impact ±15 นาที
        → Block Score = 100

  HB-5: State Lifecycle = Exhausted
        → Block Score = 100

*** สูตร Block Score สุดท้าย ***
  IF มี Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = Sum(Soft Block คะแนนที่ติด), Max = 100

******************************************************************************--
#### 6. STRATEGY CONFIDENCE
******************************************************************************--
C_strategy คำนวณแบบค่าต่อเนื่อง (สเกล 0.0–1.0):

  C_strategy = (0.40 × S_trend) + (0.40 × S_pa) + (0.20 × S_sr)

Sub-scores:

  S_trend (EMA Trend Spread Score):
    ประเมินระดับกำลังการห่างออกจากกันของ EMA 20 และ EMA 50
    S_trend = Min(1.0, |EMA20[-1] - EMA50[-1]| / (0.15 × ATR_M5))

  S_pa (Price Action Quality Score):
    วัดระดับความคมชัดและสัดส่วนที่เปรียบเทียบของรูปแบบพฤติกรรมราคา
    สำหรับ Hammer/Shooting Star: S_pa = Min(1.0, Wick_target / (2.0 × Body[-1]))
    สำหรับ Engulfing:           S_pa = Min(1.0, Body[-1] / (1.50 × Body[-2]))

  S_sr (Static S/R Touch Score):
    วัดความแน่นหนาของการปะทะจุดสัมผัสแนวต้าน/รับแบบราบ
    D_sr = |Low_or_High[-1] - Local_Level| / ATR_M5
    S_sr = 1.0 - Min(1.0, D_sr / 0.03)

******************************************************************************--
#### 7. FAIL CONDITIONS
******************************************************************************--
กลยุทธ์คืนค่า NO_SETUP ทันทีเมื่อเกิดกรณีต่อไปนี้:

  MARKET_STATE_BLOCKED    : Market State ไม่อยู่ใน Suitable States
  TREND_MISALIGNED        : ทิศทางแนวโน้มเส้นเฉลี่ยไม่เอื้ออำนวย
  LEVEL_TEST_FAILED       : จุดราคาสูงสุด/ต่ำสุดไม่ได้สัมผัสกับระดับแนวรับ/ต้านใดๆ ทั้ง dynamic และ static
  PRICE_ACTION_INVALID    : ตรวจไม่พบหรือสัดส่วนของรูปแบบพฤติกรรมราคาที่ตรวจจับผิดปกติจากความจริง
  BROKER_FEED_FREEZE      : Tick Feed หยุดค้างเกิน 10 วินาที
  NEWS_BLACKOUT           : อยู่ในช่วงข่าว High Impact ±15 นาที

******************************************************************************--
#### 8. EXPECTED BEHAVIOR
******************************************************************************--
Strong Triple Confluence (สัญญาณคุณภาพสูง):
  ราคาย่อตัวลงมาทดสอบระดับ Local Support และมี Dynamic EMA 20/50 มาทับซ้อนในระดับเดียวกันพิกัดแคบ
  พร้อมกับฟอร์มตัวเป็นแท่ง Hammer ปิดตัวแข็งแกร่งด้วยปริมาณซื้อขายหนาแน่นกว่าค่าเฉลี่ย
  C_strategy > 0.80, Entry Score > 75
  คาดหวัง: ตลาดจะกลับแรงซื้อคืนรวดเร็วในทิศทางของเทรนด์เพื่อปิดชนะ Expiry 5 นาที

Mid-Quality Confluence (สัญญาณคุณภาพปานกลาง):
  ผ่านเกณฑ์สัญญาณทั้งหมด แต่อาจเกิดเพียงการแตะเฉพาะแนว EMA โดย Local S&R ในอดีตไม่ได้ทับซ้อนกันชัดเจน
  C_strategy 0.50–0.79, Entry Score 60–74
  คาดหวัง: ราคามีโอกาสดึงตัวกลับ Retest แนวเส้นเฉลี่ยซ้ำอีกหนก่อนดีดกลับทิศทางเดิม

False Confluence (สัญญาณหลอก):
  ราคาเกิดการพักตัวทะลุแนวต้าน/รับหรือแนว EMA 50 ทั้งหมดและเกิดรูปแบบพฤติกรรมราคาที่ฝ่าฝืนแนวโน้มหลัก
  ระบบจะสามารถคัดกรองสัญญาณในกลุ่มนี้ออกผ่านทางเงื่อนไข Condition 2 และ 3
  ไม่ส่งสัญญาณ

******************************************************************************--
#### 9. AUDIT REQUIREMENTS
******************************************************************************--
บันทึกข้อมูลต่อไปนี้ลง WORM Database ทุกรอบการประเมิน:

  - audit_id        : UUIDv4 ของรอบนี้
  - timestamp       : แสตมป์เวลาระบบ (UTC)
  - symbol          : ชื่อคู่เงิน
  - market_state    : สภาวะตลาดและ State Age ณ รอบนั้น
  - candle_ohlcv    : OHLCV ของแท่ง M5[-1]
  - atr_m5          : ค่า ATR_M5 ณ รอบนั้น
  - ema20_curr      : ค่า EMA 20 ล่าสุด
  - ema50_curr      : ค่า EMA 50 ล่าสุด
  - local_support   : แนวรับย่อยล่าสุด
  - local_resistance: แนวต้านย่อยล่าสุด
  - pattern_detected: ชื่อรูปแบบพฤติกรรมราคาที่ตรวจพบ
  - f_trend         : คะแนน EMA Spread Factor
  - f_sr            : คะแนน S/R Touch Proximity Factor
  - f_ema           : คะแนน Dynamic EMA Touch Factor
  - f_pattern       : คะแนน Candle Pattern Quality Factor
  - entry_score_raw : คะแนนก่อนปรับ Lifecycle
  - entry_score     : คะแนนหลังปรับ Lifecycle และ State
  - block_score     : คะแนน Block Score รวม
  - s_trend         : EMA Trend Spread Score
  - s_pa            : Price Action Quality Score
  - s_sr            : Static S/R Touch Score
  - c_strategy      : คะแนน Strategy Confidence รวม
  - eligible        : true/false
  - action          : CALL / PUT / NO_SETUP
  - fail_reason_code: รหัสล้มเหลว (null ถ้าผ่าน)

******************************************************************************--
#### 10. OUTPUT CONTRACT (FROZEN SCHEMA)
******************************************************************************--
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_TripleConfluence_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "triple_confluence" },
    "eligible":            { "type": "BOOLEAN" },
    "action":              { "type": "STRING", "enum": ["CALL", "PUT", "NO_SETUP"] },
    "entry_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "block_score":         { "type": "NUMBER", "minimum": 0.0, "maximum": 100.0 },
    "strategy_confidence": { "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "direction_confidence":{ "type": "NUMBER", "minimum": 0.0, "maximum": 1.0 },
    "expected_state":      { "type": "STRING",
                             "enum": ["TRENDING_STRONG","TRENDING_WEAK","UNCLEAR"] },
    "fail_reason_code":    { "type": "STRING" },
    "audit_id":            { "type": "STRING",
                             "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[4][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$" },
    "expiry":              { "type": "STRING", "const": "M5" },
    "details": {
      "type": "OBJECT",
      "properties": {
        "ema20":            { "type": "NUMBER" },
        "ema50":            { "type": "NUMBER" },
        "local_support":    { "type": "NUMBER" },
        "local_resistance": { "type": "NUMBER" },
        "pattern_detected":  { "type": "STRING" }
      },
      "required": ["ema20", "ema50", "local_support", "local_resistance", "pattern_detected"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}

---

## 4. ?? Production Rules & Frozen Output Schema

### ??? PRODUCTION M5 BINARY Baseline
- **Timeframe:** Strict M5 evaluation, signal valid for exactly 1 M5 candle expiry.
- **Zero Repaint:** Signals are processed at the *open* of a new candle.
- **Fail Fast:** Pre-flight and hard blocks instantly terminate evaluation.

### ?? Frozen JSON Schema
`json
{
  "timestamp": "2026-06-07T10:45:00Z",
  "symbol": "EURUSD",
  "strategy_id": "strategy_name",
  "signal_direction": "CALL",
  "confidence_score": 85.5,
  "market_state": "STATE",
  "entry_score": 90,
  "block_score": 10,
  "fail_reason_code": "NONE",
  "audit_id": "REQ-102938"
}
`
