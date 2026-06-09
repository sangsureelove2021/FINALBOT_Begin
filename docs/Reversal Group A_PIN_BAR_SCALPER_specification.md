# FINAL SPECIFICATION: PIN BAR SCALPER (pin_bar_scalper)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

--------------------------------------------------------------------------------
[1] STRATEGY OVERVIEW
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[2] REQUIRED INPUTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[3] ENTRY CONDITIONS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[4] ENTRY SCORE LOGIC
--------------------------------------------------------------------------------
ในเวอร์ชันพิมพ์เขียวพื้นฐาน (Baseline Specs) คะแนนการเทรดจะถูกกำหนดคงที่หากผ่านทุกข้อกำหนดของเงื่อนไขการเปิดสัญญาณ:

  - Raw Score = 88 (คะแนนความเสถียรรูปทรง Pin Bar ร่วมกับ RSI)

การปรับคะแนนตามช่วงเวลาและสภาวะตลาด (State & Lifecycle Adjustments):
  - Fresh / Active State Lifecycle → Entry Score = Raw Score
  - Late State Lifecycle           → Entry Score = Raw Score * 0.80
  - Exhausted State Lifecycle      → Entry Score = 0 (และบล็อกการเข้าเทรด)
  - TRANSITIONAL Market State      → Entry Score = Entry Score * 0.70

--------------------------------------------------------------------------------
[5] BLOCK SCORE LOGIC
--------------------------------------------------------------------------------
Block Score ของกลยุทธ์ถูกออกแบบไว้ที่ 0 สำหรับทุกกรณีที่ผ่านเงื่อนไขการกรองเบื้องต้น:

--- SOFT BLOCK FACTORS ---
  * ไม่มีตัวแปร Soft Block คะแนนสะสมในเวอร์ชันนี้ (Block Score = 0 เสมอหากผ่าน Hard Block)

--- HARD BLOCK FACTORS ---
  * HB-1: Market State อยู่ในกลุ่มบล็อก (TRENDING_STRONG, BREAKOUT_EMERGING, ACCUMULATION, TRENDING_WEAK, LIQUIDITY_VOID, CHOPPY_UNCERTAIN, UNCLEAR)
          → Block Score = 100
  * HB-2: ความสูงแท่งเทียนต่ำกว่าหรือเท่ากับศูนย์ (Candle Height <= 0)
          → Block Score = 100
  * HB-3: สถานะรอบตลาด (State Lifecycle) อยู่ในระดับ Exhausted
          → Block Score = 100

--- สูตรคำนวณ Block Score สุดท้าย ---
  IF เกิดเงื่อนไข Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = 0

--------------------------------------------------------------------------------
[6] STRATEGY CONFIDENCE
--------------------------------------------------------------------------------
ความมั่นใจเชิงกลยุทธ์ (C_strategy) มีค่าคงที่ระหว่าง 0.0 ถึง 1.0 ตามระบบคะแนนดิบที่แปลงสเกล:

  C_strategy = Raw Score / 100.0 = 0.88

ตัวอย่างการคำนวณ:
  - สัญญาณเทรดเกิดขึ้นสมบูรณ์ผ่านเงื่อนไข Pin Bar + RSI + S/R Proximity:
    C_strategy = 0.88
    direction_confidence = 0.88

--------------------------------------------------------------------------------
[7] FAIL CONDITIONS
--------------------------------------------------------------------------------
กลยุทธ์จะคืนค่า NO_SETUP ทันทีพร้อมตั้งค่ารหัสล้มเหลว (fail_reason_code) เมื่อพบสถานการณ์ดังต่อไปนี้:

  - MARKET_STATE_BLOCKED      : Market State ไม่ได้อยู่ในเกณฑ์ Suitable States
  - DOJI_CANDLE_INVALID       : แท่งเทียนมีสัดส่วนเนื้อเทียนน้อยเกินไป (น้อยกว่า 5% ของความสูงรวม)
  - NO_PIN_BAR_PATTERN        : โครงสร้างแท่งเทียนไม่ผ่านเกณฑ์การทำรูปทรง Pin Bar ที่ระบุ
  - RSI_NOT_EXTREME           : ค่าดัชนี RSI(3) ไม่ถึงขีดสุดขอบ (20 สำหรับ CALL / 80 สำหรับ PUT)
  - OUTSIDE_LOCAL_SR_PROXIMITY: ขอบราคาต่ำสุด/สูงสุดอยู่ห่างแนวรับ/ต้านในระยะ 8 แท่ง เกินกว่า 0.05%
  - BROKER_FEED_FREEZE        : การป้อนข้อมูล Tick ค้างเกิน 10 วินาที
  - INSUFFICIENT_DATA         : ข้อมูลแท่งเทียนต่ำกว่าความต้องการขั้นต่ำ (20 แท่ง)
  - ZERO_HEIGHT_CANDLE        : ความยาวแท่งเทียนล่าสุดมีค่าเท่ากับ 0

--------------------------------------------------------------------------------
[8] EXPECTED BEHAVIOR
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[9] AUDIT REQUIREMENTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[10] OUTPUT CONTRACT (FROZEN SCHEMA)
--------------------------------------------------------------------------------
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
