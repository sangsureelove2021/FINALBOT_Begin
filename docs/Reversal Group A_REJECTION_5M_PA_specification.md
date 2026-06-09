# FINAL SPECIFICATION: REJECTION 5M PA (rejection_5m_pa)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

--------------------------------------------------------------------------------
[1] STRATEGY OVERVIEW
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[2] REQUIRED INPUTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[3] ENTRY CONDITIONS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[4] ENTRY SCORE LOGIC
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[5] BLOCK SCORE LOGIC
--------------------------------------------------------------------------------
Block Score เริ่มที่ 0 สะสมจาก Soft Block และ Hard Block

--- SOFT BLOCK FACTORS (สะสมคะแนนความเสี่ยง) ---

  SF-1: ATR ปัจจุบัน > 1.5 × ATR เฉลี่ย 20 แท่ง
        → +30 คะแนน
        เหตุผล: ตลาดผันผวนสูง Rejection อาจเป็น Noise

  SF-2: Close[-1] ห่างจากแนวระดับ > 0.3 × ATR_M5
        → +25 คะแนน
        เหตุผล: ปิดห่างแนวมาก ราคากลับมาสัมผัสได้ยาก

  SF-3: Market State เป็น DISTRIBUTION หรือ ACCUMULATION
        → +20 คะแนน
        เหตุผล: สภาวะเสี่ยง False Rejection สูง

--- HARD BLOCK FACTORS (Block Score = 100 ทันที) ---

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

--- สูตร Block Score สุดท้าย ---
  IF มี Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = Sum(Soft Block คะแนนที่ติด), Max = 100

--------------------------------------------------------------------------------
[6] STRATEGY CONFIDENCE
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[7] FAIL CONDITIONS
--------------------------------------------------------------------------------
กลยุทธ์คืนค่า NO_SETUP ทันทีเมื่อเกิดกรณีต่อไปนี้:

  MARKET_STATE_BLOCKED   : Market State ไม่อยู่ใน Suitable States
  LEVEL_TOO_WEAK         : S_level < 40 หลังคำนวณ Age Decay
  DOJI_SETUP_INVALID     : Body Size < 0.05 × ATR_M5
  CANDLE_STRUCTURE_INVALID: เงื่อนไขโครงสร้างแท่งเทียนไม่ผ่าน (Condition 4)
  BREAKOUT_CLOSED_OUTSIDE : Volume สูง + ปิดทะลุออกนอกแนวระดับ
  BROKER_FEED_FREEZE     : Tick Feed หยุดค้างเกิน 10 วินาที
  NEWS_BLACKOUT          : อยู่ในช่วงข่าว High Impact ±15 นาที

--------------------------------------------------------------------------------
[8] EXPECTED BEHAVIOR
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[10] OUTPUT CONTRACT (FROZEN SCHEMA)
--------------------------------------------------------------------------------
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
