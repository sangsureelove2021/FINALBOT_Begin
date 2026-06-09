# FINAL SPECIFICATION: RSI EXTREME BOUNCE (rsi_extreme_bounce)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

--------------------------------------------------------------------------------
[1] STRATEGY OVERVIEW
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[2] REQUIRED INPUTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[3] ENTRY CONDITIONS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[4] ENTRY SCORE LOGIC
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[5] BLOCK SCORE LOGIC
--------------------------------------------------------------------------------
Block Score (สเกล 0–100) ดำเนินการบล็อกออเดอร์ความเสี่ยงสูง

--- SOFT BLOCK FACTORS (สะสมคะแนนเพิ่มความเสี่ยง) ---
  SF-1: ATR ปัจจุบัน > 1.8 * Average ATR(20)
        → +30 คะแนน (ตลาดกำลังขยายความผันผวนสูงเกินไป เสี่ยงเกิดกระชากราคา)
  SF-2: สัญญาณ Stochastic %K และ %D มีทิศทางสวนทางกันในจังหวะเด้ง
        (เช่น สำหรับ CALL: %K[-1] < %D[-1] หรือ สำหรับ PUT: %K[-1] > %D[-1])
        → +25 คะแนน (ความเฉื่อยของโมเมนตัมขัดแย้งกับการกลับตัวเรียลไทม์)
  SF-3: Market State อยู่ในกลุ่ม TRANSITIONAL
        → +15 คะแนน

--- HARD BLOCK FACTORS (Block Score = 100 ทันที) ---
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

--------------------------------------------------------------------------------
[6] STRATEGY CONFIDENCE
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[7] FAIL CONDITIONS
--------------------------------------------------------------------------------
ระบบจะส่งผลลัพธ์เป็น NO_SETUP ทันทีในสภาวะดังนี้:
  MARKET_STATE_BLOCKED      : สภาวะตลาดไม่เหมาะสมในการเล่นกลับตัวสั้น
  RSI_EXTREME_BOUNCE_NOT_MET: สัญญาณ RSI(3) ไม่กระโดดออกจากโซนสุดขีดอย่างถูกต้อง
  STOCHASTIC_CONFIRMATION_FAILED: Stochastic %K อยู่ในเกณฑ์เร่งตัวเกินไป
  BB_PREV_CLOSE_NOT_PENETRATED: ราคาปิดแท่งก่อนหน้าไม่สัมผัส/ปิดทะลุขอบนอกของ Bollinger Band ล่าสุด
  BROKER_FEED_FREEZE        : การสื่อสารราคากับโบรกเกอร์ค้างเกิน 10 วินาที
  NEWS_BLACKOUT             : อยู่ในช่วงระยะเตือนข่าวระดับสูง +/- 15 นาที

--------------------------------------------------------------------------------
[8] EXPECTED BEHAVIOR
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[9] AUDIT REQUIREMENTS
--------------------------------------------------------------------------------
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

--------------------------------------------------------------------------------
[10] OUTPUT CONTRACT (FROZEN SCHEMA)
--------------------------------------------------------------------------------
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
