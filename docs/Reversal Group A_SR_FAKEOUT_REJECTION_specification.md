# FINAL SPECIFICATION: SR FAKEOUT REJECTION (sr_fakeout_rejection)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

--------------------------------------------------------------------------------
[1] STRATEGY OVERVIEW
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[2] REQUIRED INPUTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[3] ENTRY CONDITIONS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[4] ENTRY SCORE LOGIC
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[5] BLOCK SCORE LOGIC
--------------------------------------------------------------------------------
Block Score ของกลยุทธ์ถูกกำหนดไว้ที่ 0 สำหรับกรณีทั่วไปที่ผ่านเงื่อนไขการบล็อกระดับ Hard Block:

--- SOFT BLOCK FACTORS ---
  * ไม่มีตัวแปร Soft Block คะแนนสะสมในเวอร์ชันนี้ (Block Score = 0 เสมอหากผ่าน Hard Block)

--- HARD BLOCK FACTORS ---
  * HB-1: Market State อยู่ในกลุ่มบล็อก (TRENDING_STRONG, BREAKOUT_EMERGING, ACCUMULATION, TRENDING_WEAK, LIQUIDITY_VOID, CHOPPY_UNCERTAIN, UNCLEAR)
          → Block Score = 100
  * HB-2: ความยาวแท่งเทียนปัจจุบันมีค่าเป็นศูนย์ (Candle Height = 0)
          → Block Score = 100
  * HB-3: สถานะรอบตลาด (State Lifecycle) อยู่ในระดับ Exhausted
          → Block Score = 100

--- สูตรคำนวณ Block Score สุดท้าย ---
  IF เกิดเงื่อนไข Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = 0

--------------------------------------------------------------------------------
[6] STRATEGY CONFIDENCE
--------------------------------------------------------------------------------
ความมั่นใจเชิงกลยุทธ์ (C_strategy) มีค่าระหว่าง 0.0 ถึง 1.0 คำนวณจากการแปลงสเกลคะแนนความน่าเชื่อถือของการดึงกลับเชิงทิศทาง:

  C_strategy = Raw Score / 100.0

ตัวอย่างการคำนวณ:
  - เกิดสัญญาณ SPRING และปิดด้วยแท่งสีเขียว:
    Raw Score = 90
    C_strategy = 90 / 100.0 = 0.90
    
  - เกิดสัญญาณ SPRING แต่ปิดด้วยแท่งสีแดง:
    Raw Score = 80
    C_strategy = 80 / 100.0 = 0.80

--------------------------------------------------------------------------------
[7] FAIL CONDITIONS
--------------------------------------------------------------------------------
กลยุทธ์จะคืนค่า NO_SETUP ทันทีพร้อมตั้งค่ารหัสล้มเหลว (fail_reason_code) เมื่อพบสถานการณ์ดังต่อไปนี้:

  - MARKET_STATE_BLOCKED      : Market State ไม่ได้อยู่ในเกณฑ์ Suitable States
  - NO_SR_LEVELS_DETECTED     : ไม่พบแนวต้านหรือแนวรับที่ผ่านเกณฑ์ Swing Point ย้อนหลัง 40 แท่ง
  - FAKEOUT_PATTERN_NOT_MATCHED: โครงสร้างแท่งเทียนขัดแย้งกับตรรกะเบรคทะลุหลอก หรือสัดส่วนไส้เทียนไม่ได้ตามกำหนด
  - BROKER_FEED_FREEZE        : การป้อนข้อมูล Tick ค้างเกิน 10 วินาที
  - INSUFFICIENT_DATA         : ข้อมูลแท่งเทียนต่ำกว่าความต้องการขั้นต่ำ (45 แท่ง)
  - ZERO_HEIGHT_CANDLE        : ความสูงแท่งเทียนเป็น 0 (High = Low)

--------------------------------------------------------------------------------
[8] EXPECTED BEHAVIOR
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[9] AUDIT REQUIREMENTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[10] OUTPUT CONTRACT (FROZEN SCHEMA)
--------------------------------------------------------------------------------
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
