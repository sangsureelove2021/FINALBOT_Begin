# FINAL SPECIFICATION: EMA RIBBON MOMENTUM (ema_ribbon_momentum)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

--------------------------------------------------------------------------------
[1] STRATEGY OVERVIEW
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[2] REQUIRED INPUTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[3] ENTRY CONDITIONS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[4] ENTRY SCORE LOGIC
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[5] BLOCK SCORE LOGIC
--------------------------------------------------------------------------------
Block Score เริ่มที่ 0 สะสมจาก Soft Block และ Hard Block

--- SOFT BLOCK FACTORS (สะสมคะแนนความเสี่ยง) ---

  SF-1: ATR ปัจจุบัน > 1.6 × ATR เฉลี่ย 20 แท่ง
        → +30 คะแนน
        เหตุผล: ความผันผวนสัมบูรณ์สูงเกินปกติ ทำให้โครงสร้างริบบอนระยะสั้นบิดพริ้วได้ง่าย

  SF-2: ค่า RSI(5) ปะทะขอบโซนอันตราย (RSI > 67.0 สำหรับ CALL หรือ RSI < 33.0 สำหรับ PUT)
        → +25 คะแนน
        เหตุผล: ตลาดเข้าใกล้ระดับสูงสุดหรือต่ำสุดเกินไป เสี่ยงต่อการพักตัวรอบใหญ่

  SF-3: ปริมาณการซื้อขายในแท่งสัญญาณเหี่ยวแห้งชัดเจน (Volume[-1] < 0.60 × Avg_Volume)
        → +25 คะแนน
        เหตุผล: การดีดตัวบนปริมาณซื้อขายต่ำมีความน่าเชื่อถือทางสถิติน้อย

--- HARD BLOCK FACTORS (Block Score = 100 ทันที) ---

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

--- สูตร Block Score สุดท้าย ---
  IF มี Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = Sum(Soft Block คะแนนที่ติด), Max = 100

--------------------------------------------------------------------------------
[6] STRATEGY CONFIDENCE
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[7] FAIL CONDITIONS
--------------------------------------------------------------------------------
กลยุทธ์คืนค่า NO_SETUP ทันทีเมื่อเกิดกรณีต่อไปนี้:

  MARKET_STATE_BLOCKED    : Market State ไม่อยู่ใน Suitable States
  RIBBON_NOT_ALIGNED      : เส้นริบบอนเรียงตัวขัดแย้ง ไม่สอดคล้องตามเกณฑ์ขาขึ้น/ขาลง
  PULLBACK_BOUNCE_INVALID : ตรรกะการย่อตัวแตะแกนและการเด้งกลับปิดขอบทิศทางไม่ตรงตามกติกา
  RSI_OUT_OF_BOUNDS       : ค่าดัชนีชี้วัด RSI(5) อยู่นอกพื้นที่ปลอดภัยของทิศทาง
  DOJI_SETUP_INVALID      : เนื้อเทียนของแท่งยืนยันเล็กเกินไป (< 0.05 × ATR_M5)
  BROKER_FEED_FREEZE      : Tick Feed หยุดค้างเกิน 10 วินาที
  NEWS_BLACKOUT           : อยู่ในช่วงข่าว High Impact ±15 นาที

--------------------------------------------------------------------------------
[8] EXPECTED BEHAVIOR
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[9] AUDIT REQUIREMENTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[10] OUTPUT CONTRACT (FROZEN SCHEMA)
--------------------------------------------------------------------------------
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
