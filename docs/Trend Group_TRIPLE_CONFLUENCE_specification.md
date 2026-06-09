# FINAL SPECIFICATION: TRIPLE CONFLUENCE (triple_confluence)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

--------------------------------------------------------------------------------
[1] STRATEGY OVERVIEW
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[2] REQUIRED INPUTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[3] ENTRY CONDITIONS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[4] ENTRY SCORE LOGIC
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[5] BLOCK SCORE LOGIC
--------------------------------------------------------------------------------
Block Score เริ่มที่ 0 สะสมจาก Soft Block และ Hard Block

--- SOFT BLOCK FACTORS (สะสมคะแนนความเสี่ยง) ---

  SF-1: ATR ปัจจุบัน > 1.7 × ATR เฉลี่ย 20 แท่ง
        → +30 คะแนน
        เหตุผล: ความผันผวนสัมบูรณ์สูงเกินขีดความเชื่อมั่น โครงสร้าง PA อาจชำรุดเสียหาย

  SF-2: ระดับเส้นค่าเฉลี่ย EMA 20 และ EMA 50 กำลังบีบเข้าหากันแคบลง (Spread < 0.05 × ATR_M5)
        → +30 คะแนน
        เหตุผล: บ่งชี้ถึงภาวะแนวโน้มเริ่มหมดกำลังและอาจเข้าสู่สภาวะไซด์เวย์เร็วๆ นี้

  SF-3: ปริมาณการซื้อขายในแท่งกลับตัวน้อยกว่าค่าเฉลี่ย (Volume[-1] < 0.70 × Avg_Volume)
        → +20 คะแนน
        เหตุผล: แรงดีดกลับที่ไม่มีปริมาณหนุนสร้างโอกาส False Pullback ได้ง่าย

--- HARD BLOCK FACTORS (Block Score = 100 ทันที) ---

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

--- สูตร Block Score สุดท้าย ---
  IF มี Hard Block ใดๆ → Block Score = 100
  ELSE → Block Score = Sum(Soft Block คะแนนที่ติด), Max = 100

--------------------------------------------------------------------------------
[6] STRATEGY CONFIDENCE
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[7] FAIL CONDITIONS
--------------------------------------------------------------------------------
กลยุทธ์คืนค่า NO_SETUP ทันทีเมื่อเกิดกรณีต่อไปนี้:

  MARKET_STATE_BLOCKED    : Market State ไม่อยู่ใน Suitable States
  TREND_MISALIGNED        : ทิศทางแนวโน้มเส้นเฉลี่ยไม่เอื้ออำนวย
  LEVEL_TEST_FAILED       : จุดราคาสูงสุด/ต่ำสุดไม่ได้สัมผัสกับระดับแนวรับ/ต้านใดๆ ทั้ง dynamic และ static
  PRICE_ACTION_INVALID    : ตรวจไม่พบหรือสัดส่วนของรูปแบบพฤติกรรมราคาที่ตรวจจับผิดปกติจากความจริง
  BROKER_FEED_FREEZE      : Tick Feed หยุดค้างเกิน 10 วินาที
  NEWS_BLACKOUT           : อยู่ในช่วงข่าว High Impact ±15 นาที

--------------------------------------------------------------------------------
[8] EXPECTED BEHAVIOR
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[10] OUTPUT CONTRACT (FROZEN SCHEMA)
--------------------------------------------------------------------------------
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
