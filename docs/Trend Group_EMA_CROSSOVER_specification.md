# FINAL SPECIFICATION: EMA CROSSOVER (ema_crossover)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

--------------------------------------------------------------------------------
[1] STRATEGY OVERVIEW
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[2] REQUIRED INPUTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[3] ENTRY CONDITIONS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[4] ENTRY SCORE LOGIC
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[5] BLOCK SCORE LOGIC
--------------------------------------------------------------------------------
Block Score เริ่มที่ 0 สะสมจาก Soft Block และ Hard Block

--- SOFT BLOCK FACTORS (สะสมคะแนนความเสี่ยง) ---

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

--- HARD BLOCK FACTORS (Block Score = 100 ทันที) ---

  HB-1: Market State เป็น SIDEWAY_RANGE, ACCUMULATION, DISTRIBUTION หรือ CHOPPY_UNCERTAIN
        → Block Score = 100

  HB-2: ปริมาณการซื้อขายในแท่งสัญญาณต่ำเกินไป (Volume[-1] < 0.40 × Avg_Volume)
        → Block Score = 100

  HB-3: อยู่ในช่วงข่าว High Impact ±15 นาที
        → Block Score = 100

  HB-4: State Lifecycle = Exhausted
        → Block Score = 100

--- สูตร Block Score สุดท้าย ---
  IF มี Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = Sum(Soft Block คะแนนที่ติด), Max = 100

--------------------------------------------------------------------------------
[6] STRATEGY CONFIDENCE
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[7] FAIL CONDITIONS
--------------------------------------------------------------------------------
กลยุทธ์คืนค่า NO_SETUP ทันทีเมื่อเกิดกรณีต่อไปนี้:

  MARKET_STATE_BLOCKED    : Market State ไม่อยู่ใน Suitable States
  NO_CROSSOVER_DETECTED   : ไม่มีสัญญาณการตัดกันเกิดขึ้นระหว่าง EMA5 และ EMA20
  CANDLE_BODY_TOO_SMALL   : ขนาดเนื้อเทียนของแท่งตัดกันต่ำกว่า 0.10 × ATR_M5
  INSUFFICIENT_VOLUME     : ปริมาณการซื้อขายในแท่งตัดกันต่ำกว่า 0.50 × Avg_Volume
  BROKER_FEED_FREEZE      : Tick Feed หยุดค้างเกิน 10 วินาที
  NEWS_BLACKOUT           : อยู่ในช่วงข่าว High Impact ±15 นาที

--------------------------------------------------------------------------------
[8] EXPECTED BEHAVIOR
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[10] OUTPUT CONTRACT (FROZEN SCHEMA)
--------------------------------------------------------------------------------
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
