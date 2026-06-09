# FINAL SPECIFICATION: ENGULFING MOMENTUM SCALPER (engulfing_scalper)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

--------------------------------------------------------------------------------
[1] STRATEGY OVERVIEW
--------------------------------------------------------------------------------
ชื่อกลยุทธ์:
  Engulfing Momentum Scalper
  (Engulfing Pattern with Bollinger Band Edge Penetration & Fast Stochastic)

วัตถุประสงค์:
  ตรวจจับพฤติกรรมแท่งเทียนกลืนกิน (Engulfing Pattern) ณ บริเวณขอบนอกของเส้น Bollinger Bands (10, 1.8)
  ร่วมกับการยืนยันภาวะโมเมนตัมสุดโต่งจาก Fast Stochastic (5, 3, 3) ในกราฟ M5
  กลยุทธ์มุ่งเน้นการเก็งกำไรจังหวะเด้งกลับอย่างรวดเร็ว (Reversal Scalping)
  และส่งสัญญาณ ณ วินาทีเปิดของแท่งเทียนถัดไปทันที
  โดยกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — มีสิทธิ์สร้างสัญญาณหลักด้วยตัวเองเมื่อองค์ประกอบครบถ้วน

ประเภทสัญญาณ:
  Reversal — กลับตัวระยะสั้นภายใน 1-3 แท่ง M5

Market States ที่เหมาะสม:
  SIDEWAY_RANGE    — ตลาดสวิงในกรอบชัดเจน วิ่งชนขอบแล้วกลับตัว     [★★★★★]
  REVERSAL_FORMING — มีสัญญาณเหนื่อยล้าของเทรนด์และจ่อขอบแบนด์      [★★★★★]
  DISTRIBUTION     — การกระจายสินค้าบริเวณขอบแนวต้านสำคัญ          [★★★★★]
  TRANSITIONAL     — ใช้ได้แต่ลดน้ำหนัก Entry Score 30%          [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  TRENDING_STRONG   — ตลาดทำเทรนด์รุนแรง ราคาจะเกาะเส้นแบนด์ลากยาว (Band Riding)
  BREAKOUT_EMERGING — ราคากำลังพุ่งทะลุกรอบเพื่อทำทิศทางใหม่
  ACCUMULATION      — ช่วงสะสมราคา กรอบแคบเกินไป สัญญาณหลอกเยอะ
  TRENDING_WEAK     — เทรนด์อ่อนๆ แต่อาจผลักดันต่อเนื่องจนชนแนว
  LIQUIDITY_VOID    — ขาดสภาพคล่อง ราคาขยับเป็นขั้นบันได
  CHOPPY_UNCERTAIN  — ตลาดสะเปะสะปะ ไม่มีทิศทาง
  UNCLEAR           — สัญญาณตลาดขัดแย้งเชิงโครงสร้าง

--------------------------------------------------------------------------------
[2] REQUIRED INPUTS
--------------------------------------------------------------------------------
1. M5 OHLCV Candles (ย้อนหลังอย่างน้อย 20 แท่ง)
   เหตุผล: คำนวณเส้น Bollinger Bands, Fast Stochastic, ATR และระบุแพทเทิร์นแท่งเทียน

2. ATR(14) บน M5
   เหตุผล: ใช้เป็นมาตรวัดสากลในการแปลงค่าความห่างของราคาให้เป็นสัดส่วนผันแปรเทียบเคียงกันได้

3. Bollinger Bands (10, 1.8) บน M5
   - Period             = 10 (หน้าต่างสแกนสั้นเพื่อความไวต่อการตอบสนอง)
   - Standard Deviation = 1.8 (ปรับระดับแบนด์ให้แคบลงเพื่อหาขอบสวิงลึก)
   เหตุผล: ระบุพิกัดขอบบน (Upper BB) และขอบล่าง (Lower BB) เพื่อวัดขอบเขตราคา Overextended

4. Fast Stochastic (5, 3, 3) บน M5
   - %K Period = 5 (ประเมินโมเมนตัมแบบไวพิเศษ)
   - %D Period = 3
   - Smoothing = 3
   เหตุผล: ตรวจวัดระดับโมเมนตัมตึงตัวระยะสั้นพิเศษในโซน Overbought (> 75) หรือ Oversold (< 25)

5. Average Volume (เฉลี่ย 20 แท่ง M5)
   เหตุผล: ป้องกันความเสียหายในกรณีวอลลุ่มหลั่งไหลผิดปกติเพื่อรันเทรนด์ช่วงเบรคเอาท์

6. Real-Time Tick Feed
   เหตุผล: ยืนยันความต่อเนื่องของสายข้อมูลและตรวจสอบอาการค้างของสัญญาณโบรกเกอร์

7. Market State + State Age (จาก Intelligence OS)
   เหตุผล: ตรวจสอบความสอดคล้องของกลยุทธ์กลับตัวกับทิศทางตลาดและรอบชีวิตสภาวะ

8. High Impact News Calendar (+/- 15 นาที)
   เหตุผล: ล็อกระบบไม่ให้เทรดเนื่องจากความหนาแน่นผิดปกติในช่วงข่าว

--------------------------------------------------------------------------------
[3] ENTRY CONDITIONS
--------------------------------------------------------------------------------
ขั้นตอนการประเมินเรียงตามลำดับความสำคัญ (หากไม่ผ่านขั้นตอนใดให้หยุดตรวจสอบทันที)

CONDITION 1 — Market State Eligibility
  ประเมินความเข้ากันได้ของสภาวะตลาดหลัก
  ผ่าน: SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION, TRANSITIONAL
  ไม่ผ่าน: หยุดการทำงานทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — Engulfing Pattern Detection
  ตรวจสอบความสัมพันธ์ของโครงสร้างแท่งเทียน M5[-2] และ M5[-1]:
  กำหนดค่าความคลาดเคลื่อน (Tolerance Multiplier) = 1.0002
  
  สำหรับ CALL (Bullish Engulfing):
    2a. แท่งก่อนหน้าเป็นแดง: Close[-2] < Open[-2]
    2b. แท่งปัจจุบันเป็นเขียว: Close[-1] > Open[-1]
    2c. ราคาเปิดปัจจุบันเท่ากับหรือต่ำกว่าราคาปิดก่อนหน้า: Open[-1] <= Close[-2] × 1.0002
    2d. ราคาปิดปัจจุบันเท่ากับหรือสูงกว่าราคาเปิดก่อนหน้า: Close[-1] × 1.0002 >= Open[-2]
  
  สำหรับ PUT (Bearish Engulfing):
    2a. แท่งก่อนหน้าเป็นเขียว: Close[-2] > Open[-2]
    2b. แท่งปัจจุบันเป็นแดง: Close[-1] < Open[-1]
    2c. ราคาเปิดปัจจุบันเท่ากับหรือสูงกว่าราคาปิดก่อนหน้า: Open[-1] × 1.0002 >= Close[-2]
    2d. ราคาปิดปัจจุบันเท่ากับหรือต่ำกว่าราคาเปิดก่อนหน้า: Close[-1] <= Open[-2] × 1.0002
  
  ไม่ผ่านเกณฑ์การกลืนกิน → หยุดประเมินทันที → fail_reason_code: ENGULFING_PATTERN_INVALID

CONDITION 3 — Bollinger Band Edge Touch Validation
  ตรวจสอบราคาปิดของแท่งเทียนกลืนกิน M5[-1] เทียบกับแบนด์
  สำหรับ CALL: ราคาปิดต้องเท่ากับหรืออยู่ต่ำกว่าแบนด์ล่าง: Close[-1] <= LowerBB
  สำหรับ PUT: ราคาปิดต้องเท่ากับหรืออยู่สูงกว่าแบนด์บน: Close[-1] >= UpperBB
  
  ไม่ผ่านเกณฑ์การสัมผัส/ทะลุแบนด์ → หยุดประเมินทันที → fail_reason_code: BOLLINGER_BAND_NOT_TOUCHED

CONDITION 4 — Fast Stochastic Extreme Momentum Validation
  ตรวจสอบค่าความเร็วโมเมนตัม %K ล่าสุด
  สำหรับ CALL: %K[-1] < 25 (ภาวะขายมากเกินไป)
  สำหรับ PUT: %K[-1] > 75 (ภาวะซื้อมากเกินไป)
  
  ไม่ผ่านเกณฑ์โมเมนตัมตึงตัว → หยุดประเมินทันที → fail_reason_code: STOCHASTIC_MOMENTUM_INVALID

CONDITION 5 — Candle Body Size Check
  ขนาดเนื้อเทียนของแท่งตั้งต้น M5[-1] ต้องหนากว่าค่าความผันผวนขั้นต่ำสุด:
    Body Size = |Close[-1] - Open[-1]| >= 0.05 × ATR_M5
  ไม่ผ่านเกณฑ์ → หยุดประเมินทันที → fail_reason_code: DOJI_SETUP_INVALID

CONDITION 6 — Volume Climax Breakout Prevention
  ป้องกันความเสี่ยงกรณีเกิดแท่งกลืนกินวอลลุ่มมหาศาลทะลุออกนอกแบนด์ (ซึ่งมักนำไปสู่การทะลุกรอบต่อ):
  IF Volume[-1] > 2.0 × Avg_Volume
    สำหรับ CALL: หาก (LowerBB - Close[-1]) > 0.5 × ATR_M5 → HARD BLOCK → fail_reason_code: BREAKOUT_VOL_CLIMAX
    สำหรับ PUT: หาก (Close[-1] - UpperBB) > 0.5 × ATR_M5 → HARD BLOCK → fail_reason_code: BREAKOUT_VOL_CLIMAX
  ผ่านเกณฑ์: ดำเนินการตรวจสอบขั้นตอนต่อไป

CONDITION 7 — Broker Feed Validity Check
  ตรวจเช็คความสม่ำเสมอของสายส่งโบรกเกอร์ (ความหน่วงข้อมูลค้างต้องไม่เกิน 10 วินาที)
  ไม่ผ่านเกณฑ์ → หยุดประเมิน → fail_reason_code: BROKER_FEED_FREEZE

--------------------------------------------------------------------------------
[4] ENTRY SCORE LOGIC
--------------------------------------------------------------------------------
คะแนนรวมการเข้าเก็งกำไรดิบ (Raw Entry Score) สเกล 0-100 คะแนน คำนวณจากค่าน้ำหนัก 4 ส่วน:

Factor 1 — Engulfing Strength (F_engulf) น้ำหนัก 30%
  วัดแรงกลืนกินทางโครงสร้าง ยิ่งเนื้อเทียนปัจจุบันใหญ่กว่าเนื้อเทียนก่อนหน้า คะแนนยิ่งสูง
    Body_prev = |Close[-2] - Open[-2]|
    Body_curr = |Close[-1] - Open[-1]|
    Ratio = Body_curr / Max(Body_prev, 1e-10)
    F_engulf = Min(100, Max(0, ((Ratio - 1.0) / 0.5) × 50 + 50))
    (หากเนื้อแท่งปัจจุบันใหญ่กว่าแท่งก่อนหน้าตั้งแต่ 1.5 เท่าขึ้นไป จะได้คะแนนเต็ม 100)

Factor 2 — Bollinger Band Penetration (F_band) น้ำหนัก 20%
  วัดระดับความลึกของการปิดราคาออกไปนอกแบนด์
  สำหรับ CALL:
    Dist = (LowerBB - Close[-1]) / ATR_M5
    F_band = Min(100, 50 + (Dist / 0.2) × 50) ยอมรับเฉพาะ Dist >= 0
  สำหรับ PUT:
    Dist = (Close[-1] - UpperBB) / ATR_M5
    F_band = Min(100, 50 + (Dist / 0.2) × 50) ยอมรับเฉพาะ Dist >= 0
    (หากราคาปิดแทงผ่านทะลุแบนด์เกิน 0.2 × ATR_M5 จะได้คะแนนเต็ม 100)

Factor 3 — Fast Stochastic Extremeness (F_stoch) น้ำหนัก 20%
  วัดระดับความสุดโต่งของดัชนีโมเมนตัม Fast Stochastic %K
  สำหรับ CALL:
    F_stoch = Max(0.0, 100.0 × (1.0 - (%K[-1] / 25.0)))
  สำหรับ PUT:
    F_stoch = Max(0.0, 100.0 × ((%K[-1] - 75.0) / 25.0))

Factor 4 — Volume Expansion (F_volume) น้ำหนัก 30%
  วัดระดับการขยายตัวของปริมาณการซื้อขายเมื่อเทียบกับแท่งก่อนหน้า เพื่อยืนยันแรงผลักกลับที่มีคุณภาพ
    V_Ratio = Volume[-1] / Volume[-2]
    F_volume = Min(100, Max(0, ((V_Ratio - 1.0) / 1.0) × 50 + 50))
    (หากปริมาณซื้อขายขยายเพิ่มขึ้นเป็น 2.0 เท่าหรือมากกว่าของแท่งก่อนหน้า จะได้คะแนนเต็ม 100)

สูตรการประเมินคะแนน:
  Raw Entry Score = (0.30 × F_engulf) + (0.20 × F_band) + (0.20 × F_stoch) + (0.30 × F_volume)

การปรับลดคะแนนตามรอบชีวิตสภาวะตลาด (Lifecycle & State Adjustments):
  - Fresh / Active   → ใช้คะแนนดิบตามจริง (Raw Entry Score)
  - Late             → Entry Score = Raw Entry Score × 0.80
  - Exhausted        → ส่งสัญญาณบล็อกคะแนนทันที (Block Score = 100)
  - TRANSITIONAL State  → ปรับลดคะแนนลง 30% (คูณ 0.70) หลังการปรับตามอายุสภาวะ

--------------------------------------------------------------------------------
[5] BLOCK SCORE LOGIC
--------------------------------------------------------------------------------
คะแนนบล็อกความเสี่ยง (Block Score) เริ่มต้นจาก 0 และสะสมคะแนนเพิ่มขึ้นตามความเสี่ยงตลาด

--- SOFT BLOCK FACTORS (สะสมคะแนนสูงสุด 100 คะแนน) ---
  SF-1: สภาพตลาดผันผวนสูงฉับพลัน
        ATR_M5 ล่าสุด > 1.5 × ค่าเฉลี่ย ATR 20 แท่งย้อนหลัง
        → บวกเพิ่ม 30 คะแนน
  SF-2: ขนาดแท่งกลืนกินเล็กเกินไปเมื่อเทียบกับสภาพความแกว่งเฉลี่ย
        Body_curr < 0.1 × ATR_M5
        → บวกเพิ่ม 25 คะแนน
  SF-3: ตลาดอยู่ในสภาวะผันผวนด้านกระจายราคา (DISTRIBUTION หรือ TRANSITIONAL)
        → บวกเพิ่ม 20 คะแนน

--- HARD BLOCK FACTORS (Block Score = 100 ทันทีและปฏิเสธสัญญาณโดยเด็ดขาด) ---
  HB-1: สภาวะตลาดเป็นสภาวะต้องห้าม (เช่น TRENDING_STRONG หรือ BREAKOUT_EMERGING)
  HB-2: ปริมาณความผันผวนตึงตัวต่ำเกินขีดจำกัด (ATR_M5 < 0.25 × ค่าเฉลี่ย ATR 20 แท่ง)
  HB-3: ช่วงข่าวนอกโซนปลอดภัย High Impact News ในรอบ +/- 15 นาที
  HB-4: ช่วงอายุตลาดเสื่อมถอยรอบขีดสุด (State Lifecycle = Exhausted)
  HB-5: เกิดแรงดันต้านการกลับตัวสวนแพทเทิร์นอย่างมีนัยสำคัญ (Huge Opposite Wick)
        สำหรับ CALL: ไส้เทียนด้านบนของแท่งกลืนกินยาวเกินครึ่งของตัวเนื้อ: Upper Wick[-1] > 0.5 × Body_curr
        สำหรับ PUT: ไส้เทียนด้านล่างของแท่งกลืนกินยาวเกินครึ่งของตัวเนื้อ: Lower Wick[-1] > 0.5 × Body_curr
  HB-6: เกิดการปิดราคาหลุดทะลุแบนด์รุนแรงพร้อมความหนาแน่นปริมาณซื้อขาย (ตามเกณฑ์ของ Condition 6)

--- สูตรประมวลผลปลายทาง ---
  IF พบเงื่อนไข Hard Block ข้อใดข้อหนึ่ง → Block Score = 100
  ELSE → Block Score = Sum(Soft Block Points) จำกัดค่าสูงสุดที่ 100 คะแนน

--------------------------------------------------------------------------------
[6] STRATEGY CONFIDENCE
--------------------------------------------------------------------------------
ระดับความมั่นใจของการวิเคราะห์ด้วยโมเดลแบบค่าต่อเนื่อง (Continuous Model) สเกล 0.0 ถึง 1.0:

  C_strategy = (0.40 × S_engulf) + (0.35 × S_bb) + (0.25 × S_stoch)

เกณฑ์การประเมินคะแนนย่อย (Sub-scores):

  1. S_engulf (Engulfing Dominance Score):
     วัดระดับการเอาชนะความยาวเนื้อเทียนก่อนหน้า
     Ratio = Body_curr / Body_prev
     S_engulf = Min(1.0, Max(0.0, (Ratio - 1.0) / 1.0))
     (หากแท่งปัจจุบันยาวเป็น 2 เท่าขึ้นไปของแท่งเดิม S_engulf = 1.0)

  2. S_bb (BB Edge Extension Score):
     วัดระยะห่าง/ความลึกของการปิดราคาเทียบกับเส้นกรอบแบนด์
     สำหรับ CALL: Dist = LowerBB - Close[-1]
                 S_bb = Min(1.0, Max(0.0, (Dist + 0.05 × ATR_M5) / (0.1 × ATR_M5)))
     สำหรับ PUT: Dist = Close[-1] - UpperBB
                 S_bb = Min(1.0, Max(0.0, (Dist + 0.05 × ATR_M5) / (0.1 × ATR_M5)))

  3. S_stoch (Fast Stochastic Overextended Score):
     สำหรับ CALL: S_stoch = Max(0.0, 1.0 - (%K[-1] / 25.0))
     สำหรับ PUT: S_stoch = Max(0.0, (%K[-1] - 75.0) / 25.0)

--------------------------------------------------------------------------------
[7] FAIL CONDITIONS
--------------------------------------------------------------------------------
ระบบจะส่งสัญญาณ NO_SETUP ออกไปทันทีเมื่อขัดตรรกะบังคับข้อใดข้อหนึ่งดังนี้:

  MARKET_STATE_BLOCKED      : สภาวะตลาดห้ามเทรดกลับตัวสวนแนวโน้ม
  ENGULFING_PATTERN_INVALID : โครงสร้างแท่งเทียนไม่เข้าข่ายเกณฑ์แพทเทิร์นกลืนกิน
  BOLLINGER_BAND_NOT_TOUCHED: ราคาปิดไม่ได้ยืนยันตัวตน ณ ขอบแนวสัมผัสแบนด์
  STOCHASTIC_MOMENTUM_INVALID: ค่า Fast Stochastic ปิดนอกเขตเกณฑ์ความตึงตัว
  DOJI_SETUP_INVALID        : แท่งปัจจุบันขาดแรงปะทะหลัก เป็นรูปทรงโดจิไร้น้ำหนัก
  BREAKOUT_VOL_CLIMAX       : แท่งกลืนกินทะลุดึงแบนด์ลึกร่วมกับปริมาณซื้อขายสะสมพุ่งสูง
  BROKER_FEED_FREEZE        : ระบบตรวจสอบพบอาการสายข้อมูลขาดการเคลื่อนไหว
  NEWS_BLACKOUT             : ขัดต่อหลักความปลอดภัยช่วงปล่อยข่าวเศรษฐกิจระดับสูง

--------------------------------------------------------------------------------
[8] EXPECTED BEHAVIOR
--------------------------------------------------------------------------------
Strong Engulfing (กลับตัวรุนแรงประสิทธิภาพสูง):
  แท่งเทียนเกิดการขยายตัวกลืนกินแท่งก่อนหน้าอย่างลึกซึ้ง (Ratio > 1.5)
  ปิดราคาแทงทะลุออกไปนอกเส้นแบนด์ล่าง/บนในกรอบสะสมที่กว้างและค่อนข้างนิ่ง พร้อมปริมาณ Volume เพิ่มขึ้นชัดเจน
  Fast Stochastic ปิดในค่าสุดกู่ (< 10 สำหรับ CALL, > 90 สำหรับ PUT)
  C_strategy > 0.80, Entry Score > 75
  คาดหวัง: ราคาจะกลับตัวปิดเป็นบวก/ลบสวนทิศทางใน M5 ถัดไปทันทีอย่างเด็ดขาด

Weak Engulfing (กลับตัวปานกลาง/ผันผวน):
  ขนาดของเนื้อเทียนไม่ได้ต่างกันมาก หรือพิกัดปิดปะทะปะบนเส้นขอบแบนด์แบบหวุดหวิด โดยปริมาณ Volume ทรงตัว
  C_strategy อยู่ในช่วง 0.50–0.79, Entry Score 60–74
  คาดหวัง: ราคาอาจเด้งแบบผันผวนหรือย้อนทดสอบแนวซ้ำก่อนเปลี่ยนทิศทางในกรอบกว้าง

False Engulfing (Breakout):
  เกิดแท่งกลืนกินยาวเหยียดพร้อมปริมาณซื้อขายสะสมล้นพะเนิน ราคาปิดทะลุแบนด์ออกไปไกลเกินเกณฑ์
  ซึ่งสื่อถึงแรงเฉื่อยตามน้ำ (Momentum Breakout) ที่รุนแรงของกลุ่มเทรดเดอร์ในแนวโน้มใหญ่
  ระบบจะสกัดกั้นได้ในด่าน Condition 6 และล็อกการออกสเปกบล็อกสัญญาณทันที (BREAKOUT_VOL_CLIMAX)

--------------------------------------------------------------------------------
[9] AUDIT REQUIREMENTS
--------------------------------------------------------------------------------
รายการข้อมูลที่จำเป็นต้องจัดเก็บลง WORM Database ในทุกรอบประเมินสตรีมกลยุทธ์:

  - audit_id        : UUIDv4 อ้างอิงตรวจสอบผลการประเมินประจำรอบ
  - timestamp       : เวลาประเมินระบบในรูปมาตรฐานสากล (UTC)
  - symbol          : ชื่อคู่เงิน
  - market_state    : สภาวะตลาดรวมถึงอายุ State ณ รอบนั้น
  - candle_ohlcv    : ราคา OHLCV ของแท่ง M5[-1] และ M5[-2]
  - atr_m5          : ค่าความผันผวน ATR_M5 ปัจจุบัน
  - upper_bb        : พิกัดค่าเฉลี่ย Bollinger Band บน (10, 1.8)
  - lower_bb        : พิกัดค่าเฉลี่ย Bollinger Band ล่าง (10, 1.8)
  - stoch_k         : ค่า Fast Stochastic %K ล่าสุด
  - stoch_d         : ค่า Fast Stochastic %D ล่าสุด
  - f_engulf        : คะแนนองค์ประกอบ Engulfing Strength
  - f_band          : คะแนนองค์ประกอบ Band Penetration
  - f_stoch         : คะแนนองค์ประกอบ Fast Stochastic Extremeness
  - f_volume        : คะแนนองค์ประกอบ Volume Expansion
  - entry_score_raw : คะแนนประเมินรวมก่อนคิดเงื่อนไขตลาดและอายุ
  - entry_score     : คะแนนประเมินจริงขั้นปลายน้ำ
  - block_score     : คะแนนป้องกันสกัดกั้นความเสี่ยงรวม
  - s_engulf        : ดัชนีความมั่นใจการกลืนกิน
  - s_bb            : ดัชนีความมั่นใจการทะลุแนวแบนด์
  - s_stoch         : ดัชนีความมั่นใจโมเมนตัม Stochastic
  - c_strategy      : ระดับความมั่นใจกลยุทธ์รวม
  - eligible        : ผลตรวจสอบเงื่อนไขความพร้อมใช้งาน (true/false)
  - action          : สัญญาณเปิดเทรด (CALL / PUT / NO_SETUP)
  - fail_reason_code: รหัสข้อมูลระบุขีดจำกัดล้มเหลว (null เมื่อสำเร็จ)

--------------------------------------------------------------------------------
[10] OUTPUT CONTRACT (FROZEN SCHEMA)
--------------------------------------------------------------------------------
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_EngulfingScalper_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "engulfing_scalper" },
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
        "upper_bb": { "type": "NUMBER" },
        "lower_bb": { "type": "NUMBER" },
        "stoch_k":  { "type": "NUMBER" }
      },
      "required": ["upper_bb", "lower_bb", "stoch_k"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}
