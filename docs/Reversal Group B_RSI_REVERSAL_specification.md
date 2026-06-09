# FINAL SPECIFICATION: RSI REVERSAL (rsi_reversal)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

--------------------------------------------------------------------------------
[1] STRATEGY OVERVIEW
--------------------------------------------------------------------------------
ชื่อกลยุทธ์:
  RSI Reversal
  (RSI Oversold/Overbought Reentry Reversal Strategy)

วัตถุประสงค์:
  ตรวจจับสัญญาณกลับตัวแบบยืนยันความเร็ว (Momentum Reentry) บนแท่งเทียน M5 ล่าสุด
  เมื่อค่า RSI(7) วิ่งข้ามเกณฑ์ขีดสุด (น้อยกว่า 30 หรือมากกว่า 70) ในแท่งก่อนหน้า แล้วหักหัวกลับเข้ามาในเกณฑ์ปกติ
  ร่วมกับการยืนยันการสัมผัสแนวราคาที่มีนัยสำคัญในอดีต (Local Support/Resistance)
  ส่งสัญญาณ ณ วินาทีเปิดของแท่งถัดไปทันที โดยกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — สร้างสัญญาณกลับตัวพื้นฐาน (Core Reversal) จากการเปลี่ยนผ่านแนวโน้มระยะสั้นในกรอบแนวรับ/แนวต้านสำคัญ

ประเภทสัญญาณ:
  Reversal — กลับตัวระยะสั้นภายใน 1 แท่ง M5 (5 นาที)

Market States ที่เหมาะสม:
  SIDEWAY_RANGE    — ตลาดแกว่งตัวในกรอบรับต้านชัดเจน              [★★★★★]
  REVERSAL_FORMING — เกิดรูปแบบกลับตัวหลังจากราคาออกนอกเกณฑ์     [★★★★★]
  DISTRIBUTION     — ราคาอยู่ในเขตบนสะสมและเตรียมเทขาย          [★★★★★]
  TRANSITIONAL     — ใช้ได้แต่ลดน้ำหนัก Entry Score 30%          [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  TRENDING_STRONG   — ตลาดรันเทรนด์ยาวนาน โมเมนตัมหักหัวกลับได้ยากและสเปรดกว้าง
  BREAKOUT_EMERGING — ราคาตัดผ่านระดับอย่างรุนแรงและเกิดการเริ่มเทรนด์ใหม่
  ACCUMULATION      — ตลาดบีบตัวไม่แสดงแนวรับ/ต้านที่ชัดเจน
  TRENDING_WEAK     — สภาวะมีเทรนด์อ่อนๆ แต่ราคาไม่ยอมกลับทิศทาง
  LIQUIDITY_VOID    — การขาดหายของปริมาณซื้อขายทำให้ตัวชี้วัดเพี้ยน
  CHOPPY_UNCERTAIN  — ราคาเปลี่ยนทิศทางอย่างไร้ระเบียบ
  UNCLEAR           — ค่าอินดิเคเตอร์ขัดแย้งเชิงโครงสร้างราคา

--------------------------------------------------------------------------------
[2] REQUIRED INPUTS
--------------------------------------------------------------------------------
1. M5 OHLCV Candles (ย้อนหลัง 100 แท่ง)
   เหตุผล: ใช้คำนวณ RSI(7), แนวรับ/แนวต้าน (Local S/R) และค่า ATR

2. ATR(14) บน M5
   เหตุผล: Normalize ระยะห่างของราคาเทียบกับแนวระดับสำคัญเพื่อวัดพิกัดที่แท้จริง

3. RSI(7) พร้อม Wilder's Smoothing
   เหตุผล: วัดการไหลเข้าออกของแรงซื้อและแรงขาย (Momentum) เพื่อหาจังหวะไหลกลับ (Reentry)

4. Local Support & Resistance (คำนวณจาก Swing Points ช่วงแท่งที่ -13 ถึง -4)
   เหตุผล: ระบุแนวอ้างอิงราคาที่มีประวัติการทดสอบผ่านการยอมรับจากระบบ

5. Average Volume (เฉลี่ย 20 แท่ง M5)
   เหตุผล: ใช้กรองความเสี่ยงในการทะลุผ่าน (Breakout) และยืนยันความแข็งแรงของแท่งยืนยัน

6. Real-Time Tick Feed
   เหตุผล: ตรวจสอบความถูกต้องของค่าราคากับระบบในหน่วยมิลลิวินาที

7. Market State + State Age (จาก Intelligence OS)
   เหตุผล: ใช้ระงับสัญญาณเทรดเมื่อสภาวะตลาดก้าวสู่สถานะมีเทรนด์

8. High Impact News Calendar (+/- 15 นาที)
   เหตุผล: บล็อกการเกิดสัญญาณหลอกในช่วงที่สถิติทางเทคนิคสูญเสียความแม่นยำ

--------------------------------------------------------------------------------
[3] ENTRY CONDITIONS
--------------------------------------------------------------------------------
กระบวนการวิเคราะห์สัญญาณเป็นไปตามขั้นตอนการทดสอบ (Evaluation Pipeline) ดังนี้:

CONDITION 1 — Market State Eligibility
  ตรวจสอบสถานะตลาดปัจจุบันใน Suitable States
  ผ่าน: SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION, TRANSITIONAL
  ไม่ผ่าน: หยุดการทำงานทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — S/R Level Quality Check (S_level Engine)
  คำนวณหาแนวรับ/ต้านในอดีต:
    - local_support = ค่าต่ำสุดของราคา Low ในช่วงแท่งที่ -13 ถึง -4
    - local_resistance = ค่าสูงสุดของราคา High ในช่วงแท่งที่ -13 ถึง -4

  การประเมินคะแนนความแข็งแกร่ง (S_level_base, สูงสุด 100):
    - C_touch (50 คะแนน): จำนวนรอบการสัมผัสแนวราคาอดีต โดยให้รอบละ 25 คะแนน (สูงสุด 50)
    - D_react (30 คะแนน): ขนาดการดีดตัวกลับของราคาหลังทดสอบแนวนั้น (สูงสุด 30)
    - V_profile (20 คะแนน): การทับซ้อนกับโซนที่มีปริมาณซื้อขายสะสมสูงสุดย้อนหลัง 100 แท่ง

  การคิดค่าลดทอนเสื่อมเวลา (Age Decay):
    - S_level = S_level_base * exp(-0.015 * age)
    - age คือจำนวนแท่ง M5 ตั้งแต่การทดสอบครั้งล่าสุด
  เกณฑ์อนุมัติ: S_level ต้องมากกว่าหรือเท่ากับ 40 คะแนน
  ไม่ผ่าน → fail_reason_code: LEVEL_TOO_WEAK

CONDITION 3 — Price Touch Local S/R
  ตรวจสอบว่าราคาใน 3 แท่งล่าสุด ([-3, -2, -1]) เคยมีการทดสอบแนวราคาหรือไม่:
    - สำหรับ CALL: Low[-k] <= local_support * 1.0002 (อย่างน้อยหนึ่งแท่ง)
    - สำหรับ PUT: High[-k] >= local_resistance * 0.9998 (อย่างน้อยหนึ่งแท่ง)
  ไม่ผ่าน → fail_reason_code: LEVEL_NOT_TOUCHED

CONDITION 4 — RSI(7) Reentry Crossover
  ตรวจสอบความเร็วโมเมนตัมหักกลับเข้าโซนปกติ:
    - สำหรับ CALL: RSI(7)[-2] < 30 และ RSI(7)[-1] >= 30
    - สำหรับ PUT: RSI(7)[-2] > 70 และ RSI(7)[-1] <= 70
  ไม่ผ่าน → fail_reason_code: RSI_REENTRY_FAILED

CONDITION 5 — Broker Feed Validity
  ต้องรับสัญญาณราคาล่าสุดไม่ห่างเกิน 10 วินาที
  ไม่ผ่าน → fail_reason_code: BROKER_FEED_FREEZE

--------------------------------------------------------------------------------
[4] ENTRY SCORE LOGIC
--------------------------------------------------------------------------------
Entry Score (สเกล 0–100) คำนวณจากน้ำหนัก 4 ปัจจัย รวม 100% ดังนี้:

Factor 1 — RSI Reentry Momentum (F_rsi_reentry) น้ำหนัก 40%
  ประเมินความเร็วของการหักกลับเข้าสู่แดนปกติของ RSI(7)
  - D_rsi = |RSI(7)[-1] - RSI(7)[-2]|
  - F_rsi_reentry = Min(100, (D_rsi / 10.0) * 100)
  (หมายเหตุ: หาก RSI ดีดข้ามเกณฑ์มากกว่า 10 จุด จะได้คะแนนเต็ม)

Factor 2 — S/R Touch Accuracy (F_sr) น้ำหนัก 30%
  วัดความชิดของจุดต่ำสุด/สูงสุดเทียบกับระดับราคาสำคัญใน 3 แท่งล่าสุด
  - D_sr = Min( |Low[-k] - local_support| สำหรับ k=1,2,3 ) / ATR_M5 (สำหรับ CALL)
  - D_sr = Min( |High[-k] - local_resistance| สำหรับ k=1,2,3 ) / ATR_M5 (สำหรับ PUT)
  - F_sr = Max(0, 100 - (D_sr / 0.1) * 100)

Factor 3 — Close Proximity Factor (F_close) น้ำหนัก 15%
  วัดระยะห่างราคาปิดล่าสุดเทียบกับแนว เพื่อป้องกันราคาไหลทะลุกว้างเกินไป
  - D_close = |Close[-1] - local_SR| / ATR_M5  (local_SR คือ local_support หรือ local_resistance)
  - F_close = Max(0, 100 - (D_close / 0.2) * 100)

Factor 4 — Volumetric Confirmation (F_vol) น้ำหนัก 15%
  วัดความหนาแน่นปริมาณซื้อขายเปรียบเทียบค่าเฉลี่ย
  - R_vol = Volume[-1] / Avg_Volume(20)
  - F_vol = Min(100, Max(0, ((R_vol - 0.5) / 1.5) * 100))

สูตรคะแนนรวมดิบ (Raw Entry Score):
  Raw Entry Score = (0.40 * F_rsi_reentry) + (0.30 * F_sr) + (0.15 * F_close) + (0.15 * F_vol)

การปรับตามวงจรสภาวะตลาด (State Lifecycle Adjustment):
  - Fresh / Active   → ใช้ Raw Entry Score ตรง
  - Late             → Entry Score = Raw Entry Score * 0.80
  - Exhausted        → บล็อกสัญญาณทันที (Block Score = 100)
  - TRANSITIONAL     → Entry Score = Raw Entry Score * 0.70

--------------------------------------------------------------------------------
[5] BLOCK SCORE LOGIC
--------------------------------------------------------------------------------
Block Score (สเกล 0–100) ออกแบบมาเพื่อตรวจจับความเสี่ยงระดับสูง

--- SOFT BLOCK FACTORS (สะสมคะแนนเพิ่มความเสี่ยง) ---
  SF-1: ATR ปัจจุบัน > 1.8 * Average ATR(20)
        → +30 คะแนน (เสี่ยงเกิดการแกว่งตัวกว้างจนราคาทะลุแนว)
  SF-2: Volume[-1] > 2.0 * Average Volume(20)
        → +25 คะแนน (ความต้องการซื้อขายหนาแน่นเกินปกติ เสี่ยงเบรคเอาท์)
  SF-3: ราคาปิดล่าสุดปิดห่างจากระดับแนวราคาสำคัญเกิน 0.3 * ATR
        → +20 คะแนน (ราคาย้อนกลับตัวมาได้ยากเนื่องจากปิดลึกเกินไป)

--- HARD BLOCK FACTORS (Block Score = 100 ทันที) ---
  HB-1: Market State เป็น TRENDING_STRONG หรือ BREAKOUT_EMERGING
        → Block Score = 100
  HB-2: ทิศทางไส้เทียนของแท่งเทียนที่ปฏิเสธทิศทางกลับตัวหลักมีขนาดยาวเด่นชัดเจนข่มทิศเป้าหมาย
        (Wick_opposite > Wick_target * 1.5)
        → Block Score = 100
  HB-3: อยู่ในช่วงประกาศข่าวความผันผวนสูง High Impact เศรษฐกิจ (+/- 15 นาที)
        → Block Score = 100
  HB-4: สถานะวงจรสภาวะตลาดเสื่อมถอย (State Lifecycle = Exhausted)
        → Block Score = 100
  HB-5: ไม่มีการตอบสนองราคาจากเซิร์ฟเวอร์โบรกเกอร์เกิน 10 วินาที (Broker Feed Freeze)
        → Block Score = 100

สูตรคำนวณ Block Score สุดท้าย:
  IF มี Hard Block เกิดขึ้นข้อใดข้อหนึ่ง → Block Score = 100
  ELSE → Block Score = Min(100, Sum(คะแนนสะสมของ Soft Block ทั้งหมด))

--------------------------------------------------------------------------------
[6] STRATEGY CONFIDENCE
--------------------------------------------------------------------------------
C_strategy คำนวณในรูปแบบค่าต่อเนื่อง (สเกล 0.0–1.0):
  C_strategy = (0.40 * S_rsi_bounce) + (0.40 * S_sr_touch) + (0.20 * S_vol_ratio)

คะแนนย่อย (Sub-scores):
  1. RSI Bounce Score (S_rsi_bounce):
     - S_rsi_bounce = Min(1.0, |RSI(7)[-1] - RSI(7)[-2]| / 8.0)
     (หมายเหตุ: การสปีดตัวของ RSI เกิน 8 จุดสะท้อนแรงขับสูงสุด ได้ 1.0)

  2. S/R Touch Accuracy Score (S_sr_touch):
     - S_sr_touch = Max(0.0, 1.0 - (D_sr / 0.08))

  3. Volume Ratio Score (S_vol_ratio):
     - S_vol_ratio = Min(1.0, Volume[-1] / Avg_Volume(20))

ตัวอย่างการคำนวณ (CALL):
  RSI(7) ย้อนหลัง 2 แท่ง: 27.0 → 32.5 (หักกลับพ้น 30), D_sr = 0.02 * ATR_M5, Volume[-1] = 0.9 * Avg_Volume(20)
  - S_rsi_bounce = Min(1.0, |32.5 - 27.0| / 8.0) = Min(1.0, 5.5 / 8.0) = 0.6875
  - S_sr_touch = Max(0.0, 1.0 - (0.02 / 0.08)) = 0.75
  - S_vol_ratio = Min(1.0, 0.9) = 0.90
  - C_strategy = (0.40 * 0.6875) + (0.40 * 0.75) + (0.20 * 0.90) = 0.275 + 0.30 + 0.18 = 0.755

--------------------------------------------------------------------------------
[7] FAIL CONDITIONS
--------------------------------------------------------------------------------
กลยุทธ์จะประเมินผลเป็น NO_SETUP ทันทีในสถานการณ์ต่อไปนี้:
  MARKET_STATE_BLOCKED      : สถานะตลาดขัดต่อทฤษฎีการประเมินสัญญาณ
  LEVEL_TOO_WEAK            : คะแนนความแข็งแรงของพิกัดแนวระดับ S_level < 40
  LEVEL_NOT_TOUCHED         : ไม่มีระดับราคาใดๆ ใน 3 แท่งล่าสุดสัมผัสแนวอ้างอิง
  RSI_REENTRY_FAILED        : RSI(7) ไม่สามารถวิ่งกลับเข้าโซนปกติพ้นเส้น 30 หรือ 70
  BROKER_FEED_FREEZE        : ระบบไม่ได้รับค่าราคาอัปเดตเรียลไทม์เกิน 10 วินาที
  NEWS_BLACKOUT             : ข่าวเศรษฐกิจขัดขวางการประมวลผลในช่วงเวลาที่กำหนด

--------------------------------------------------------------------------------
[8] EXPECTED BEHAVIOR
--------------------------------------------------------------------------------
Strong RSI Reentry (สัญญาณคุณภาพสูงสุด):
  ราคาปิดแท่งที่แล้วในจุดต่ำสุดที่แนวรับที่มีคะแนนแข็งแกร่ง (S_level > 70) พร้อม RSI(7) ต่ำกว่า 25
  แท่งเทียนปัจจุบันดีดขึ้นทันทีปิดพ้นระดับ 30 พร้อมปริมาณซื้อขายหนาแน่นปานกลาง
  C_strategy > 0.80, Entry Score > 75
  คาดหวัง: โมเมนตัมพยุงให้ราคาเคลื่อนตัวทิศทางบวกต่อไปอีกอย่างน้อย 1 แท่งเทียน (5 นาที)

Weak RSI Reentry (สัญญาณเสี่ยงปานกลาง):
  RSI(7) พึ่งเลื่อนเข้าขีดสุดและเคลื่อนที่กลับออกนอกกรอบอย่างเชื่องช้า แนวรับในอดีตเคยถูกทดสอบบ่อยครั้ง
  C_strategy 0.50–0.70, Entry Score 60–74
  คาดหวัง: ราคาอาจไซด์เวย์ออกข้างหรือ Retest แนวรับซ้ำก่อนเคลื่อนที่

False RSI Reentry (Breakout Continuation):
  ราคาดิ่งทะลุแนวต้านออกไปอย่างต่อเนื่องโดยไม่มีการย้อนกลับของราคาปิด และ RSI ค้างในแดน Overbought/Oversold เป็นเวลานาน
  ดักจับทาง: เงื่อนไข Hard Block และการประเมิน Market State
  ผลลัพธ์: ระบบขึ้นสถานะ NO_SETUP ทันที

--------------------------------------------------------------------------------
[9] AUDIT REQUIREMENTS
--------------------------------------------------------------------------------
บันทึกข้อมูลเพื่อใช้ในการสอบทานลงระบบฐานข้อมูลความปลอดภัย WORM:
  - audit_id              : UUIDv4 หมายเลขรอบบันทึกข้อมูล
  - timestamp             : แสตมป์เวลามาตรฐานสากล UTC
  - symbol                : ชื่อสินทรัพย์
  - market_state          : สภาวะตลาดที่รับคำนวณ
  - candle_ohlcv          : ข้อมูลราคาย้อนหลังแท่ง M5 100 แท่ง
  - rsi7_current          : ค่า RSI(7) ปัจจุบัน
  - rsi7_previous         : ค่า RSI(7) ย้อนหลัง 1 แท่ง
  - local_support         : พิกัดแนวรับที่ใช้อ้างอิง
  - local_resistance      : พิกัดแนวต้านที่ใช้อ้างอิง
  - s_level_final         : คะแนนความแข็งแรงแนวหลังหักค่าเสื่อมถอย
  - f_rsi_reentry         : คะแนนองค์ประกอบการหักกลับ RSI
  - f_sr                  : คะแนนการทดสอบแนวอ้างอิง
  - f_close               : คะแนนความห่างของราคาปิด
  - f_vol                 : คะแนนปริมาณซื้อขาย
  - entry_score           : คะแนนทางสถิติของระบบส่งออเดอร์
  - block_score           : คะแนนวิเคราะห์ขัดขวางออเดอร์
  - c_strategy            : ความน่าจะเป็นในการชนะเชิงระบบ
  - eligible              : ผลความสมบูรณ์สัญญาณ (true/false)
  - action                : คำสั่งดำเนินการ (CALL / PUT / NO_SETUP)
  - fail_reason_code      : รหัสวิเคราะห์ข้อผิดพลาด

--------------------------------------------------------------------------------
[10] OUTPUT CONTRACT (FROZEN SCHEMA)
--------------------------------------------------------------------------------
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_RSIReversal_M5_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "rsi_reversal" },
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
