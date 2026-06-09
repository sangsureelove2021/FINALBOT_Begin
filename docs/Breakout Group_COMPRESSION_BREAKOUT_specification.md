# FINAL SPECIFICATION: COMPRESSION BREAKOUT (compression_breakout)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

--------------------------------------------------------------------------------
[1] STRATEGY OVERVIEW
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[2] REQUIRED INPUTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[3] ENTRY CONDITIONS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[4] ENTRY SCORE LOGIC
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[5] BLOCK SCORE LOGIC
--------------------------------------------------------------------------------
Block Score เริ่มต้นที่ 0 คะแนน และจะสะสมจาก Soft Block และ Hard Block ดังต่อไปนี้:

--- SOFT BLOCK FACTORS (สะสมคะแนนเพิ่มความเสี่ยงสูงสุด 100 คะแนน) ---
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

--- HARD BLOCK FACTORS (เมื่อเงื่อนไขตรง จะปรับ Block Score = 100 ทันทีและปฏิเสธคำสั่งซื้อ) ---
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

--- สูตรคำนวณ Block Score ท้ายสุด ---
  IF มีการตรวจพบเงื่อนไข Hard Block ข้อใดข้อหนึ่ง → Block Score = 100
  ELSE → Block Score = Sum(Soft Block คะแนนที่ติดทั้งหมด) โดยมีค่าสูงสุดจำกัดที่ 100 คะแนน

--------------------------------------------------------------------------------
[6] STRATEGY CONFIDENCE
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[7] FAIL CONDITIONS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[8] EXPECTED BEHAVIOR
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[9] AUDIT REQUIREMENTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[10] OUTPUT CONTRACT (FROZEN SCHEMA)
--------------------------------------------------------------------------------
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
