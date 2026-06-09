# FINAL SPECIFICATION: MACD CROSSOVER (macd_crossover)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

--------------------------------------------------------------------------------
[1] STRATEGY OVERVIEW
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[2] REQUIRED INPUTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[3] ENTRY CONDITIONS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[4] ENTRY SCORE LOGIC
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[5] BLOCK SCORE LOGIC
--------------------------------------------------------------------------------
Block Score เริ่มที่ 0 สะสมจาก Soft Block และ Hard Block

--- SOFT BLOCK FACTORS (สะสมคะแนนความเสี่ยง) ---

  SF-1: ATR ปัจจุบัน > 1.6 × ATR เฉลี่ย 20 แท่ง
        → +30 คะแนน
        เหตุผล: ความผันผวนภายนอกสูงเกินไป เสี่ยงต่อการกลับตัวกระชากสั้นๆ (Whipsaw)

  SF-2: ปริมาณการซื้อขายในแท่งสัญญาณต่ำกว่าค่าเฉลี่ย (Volume[-1] < 0.80 × Avg_Volume)
        → +25 คะแนน
        เหตุผล: การตัดกันที่ไม่มีปริมาณหนุนอาจนำไปสู่การเคลื่อนที่เฉื่อยและตัดสลับกลับที่เดิม

  SF-3: ระยะจุดตัด MACD เข้าใกล้ศูนย์มากเกินไป (|MACD[-1]| < 0.08 × ATR_M5)
        → +25 คะแนน
        เหตุผล: โซนก้ำกึ่งใกล้ Zero Line มักมีแนวโน้มอ่อนแอและสับสนสูง

--- HARD BLOCK FACTORS (Block Score = 100 ทันที) ---

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

--- สูตร Block Score สุดท้าย ---
  IF มี Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = Sum(Soft Block คะแนนที่ติด), Max = 100

--------------------------------------------------------------------------------
[6] STRATEGY CONFIDENCE
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[7] FAIL CONDITIONS
--------------------------------------------------------------------------------
กลยุทธ์คืนค่า NO_SETUP ทันทีเมื่อเกิดกรณีต่อไปนี้:

  MARKET_STATE_BLOCKED    : Market State ไม่อยู่ใน Suitable States
  MACD_CROSSOVER_INVALID  : การตัดกันไม่สมบูรณ์ หรือทิศทาง/ขอบเขตความกว้างขัดแย้งกับ Zero Line
  CANDLE_BODY_TOO_SMALL   : เนื้อเทียนของแท่งสัญญาณเล็กเกินไป (< 0.10 × ATR_M5)
  INSUFFICIENT_VOLUME     : ปริมาณการซื้อขายในแท่งตัดสัญญาณต่ำกว่า 0.60 × Avg_Volume
  BROKER_FEED_FREEZE      : Tick Feed หยุดค้างเกิน 10 วินาที
  NEWS_BLACKOUT           : อยู่ในช่วงข่าว High Impact ±15 นาที

--------------------------------------------------------------------------------
[8] EXPECTED BEHAVIOR
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[10] OUTPUT CONTRACT (FROZEN SCHEMA)
--------------------------------------------------------------------------------
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
