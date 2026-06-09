# FINAL SPECIFICATION: PA SNR STRATEGY (pa_snr)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

--------------------------------------------------------------------------------
[1] STRATEGY OVERVIEW
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[2] REQUIRED INPUTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[3] ENTRY CONDITIONS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[4] ENTRY SCORE LOGIC
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[5] BLOCK SCORE LOGIC
--------------------------------------------------------------------------------
Block Score ของกลยุทธ์ถูกออกแบบไว้ที่ 0 สำหรับทุกกรณีหากผ่านเงื่อนไขบังคับเชิงลบ (Hard Block) ขั้นพื้นฐานเรียบร้อยแล้ว:

--- SOFT BLOCK FACTORS ---
  * ไม่มีตัวแปร Soft Block คะแนนสะสมในเวอร์ชันนี้ (Block Score = 0 เสมอหากผ่าน Hard Block)

--- HARD BLOCK FACTORS ---
  * HB-1: Market State อยู่ในกลุ่มบล็อก (TRENDING_STRONG, BREAKOUT_EMERGING, ACCUMULATION, TRENDING_WEAK, LIQUIDITY_VOID, CHOPPY_UNCERTAIN, UNCLEAR)
          → Block Score = 100
  * HB-2: ความยาวแท่งเทียนล่าสุดเป็นศูนย์ (Candle Height = 0)
          → Block Score = 100
  * HB-3: สถานะรอบตลาด (State Lifecycle) อยู่ในระดับ Exhausted
          → Block Score = 100

--- สูตรคำนวณ Block Score สุดท้าย ---
  IF เกิดเงื่อนไข Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = 0

--------------------------------------------------------------------------------
[6] STRATEGY CONFIDENCE
--------------------------------------------------------------------------------
ความมั่นใจเชิงกลยุทธ์ (C_strategy) มีค่าระหว่าง 0.0 ถึง 1.0 คำนวณจากการแปลงสเกลคะแนนความน่าเชื่อถือของรูปแบบเชิงทฤษฎี:

  C_strategy = Raw Score / 100.0

ตัวอย่างการคำนวณ:
  - หากระบบตรวจพบรูปแบบ Morning Star ณ แนวรับ:
    Raw Score = 92
    C_strategy = 92 / 100.0 = 0.92
    
  - หากระบบตรวจพบรูปแบบ Three White Soldiers ณ แนวรับ:
    Raw Score = 85
    C_strategy = 85 / 100.0 = 0.85

--------------------------------------------------------------------------------
[7] FAIL CONDITIONS
--------------------------------------------------------------------------------
กลยุทธ์จะคืนค่า NO_SETUP ทันทีพร้อมตั้งค่ารหัสล้มเหลว (fail_reason_code) เมื่อพบสถานการณ์ดังต่อไปนี้:

  - MARKET_STATE_BLOCKED      : Market State ไม่ได้อยู่ในเกณฑ์ Suitable States
  - NO_SR_LEVELS_DETECTED     : ไม่พบแนวต้านหรือแนวรับที่ผ่านเกณฑ์การทำ Swing Point ย้อนหลัง 30 แท่ง
  - PRICE_OUTSIDE_SR_PROXIMITY: จุดสูงสุด/ต่ำสุดของแท่งล่าสุด ไม่อยู่ในระยะ Proximity 0.04% ของแนวระดับ
  - NO_PA_PATTERN_DETECTED    : โครงสร้างแท่งเทียนไม่สอดคล้องกับพฤติกรรมราคากลับตัวใดๆ ที่สนับสนุน
  - BROKER_FEED_FREEZE        : การป้อนข้อมูล Tick ค้างเกิน 10 วินาที
  - INSUFFICIENT_DATA         : ข้อมูลแท่งเทียนต่ำกว่าความต้องการขั้นต่ำ (35 แท่ง)
  - ZERO_HEIGHT_CANDLE        : ความยาวแท่งเทียน High - Low มีค่าเท่ากับ 0

--------------------------------------------------------------------------------
[8] EXPECTED BEHAVIOR
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[9] AUDIT REQUIREMENTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[10] OUTPUT CONTRACT (FROZEN SCHEMA)
--------------------------------------------------------------------------------
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
