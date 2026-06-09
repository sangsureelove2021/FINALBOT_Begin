# FINAL SPECIFICATION: STOCHASTIC CROSSOVER (stochastic_crossover)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

--------------------------------------------------------------------------------
[1] STRATEGY OVERVIEW
--------------------------------------------------------------------------------
ชื่อกลยุทธ์:
  Stochastic Crossover
  (Stochastic %K/%D Crossover with Local Support/Resistance Touch)

วัตถุประสงค์:
  ตรวจจับการตัดกันของเส้น Stochastic Oscillator (%K และ %D) ในเขตโซนสุดโต่ง (Overbought/Oversold)
  ร่วมกับการยืนยันการสัมผัสแนวรับ/แนวต้านในระดับท้องถิ่น (Local S/R) บนแท่งเทียน M5 ล่าสุด
  กลยุทธ์มุ่งเน้นการจับจังหวะกลับตัวระยะสั้นเพื่อสร้างสัญญาณ ณ วินาทีเปิดของแท่งเทียนถัดไปทันที
  โดยกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — มีสิทธิ์สร้างสัญญาณหลักด้วยตัวเองเมื่อเงื่อนไขและคะแนนผ่านเกณฑ์ที่กำหนด

ประเภทสัญญาณ:
  Reversal — กลับตัวระยะสั้นภายใน 1-3 แท่ง M5

Market States ที่เหมาะสม:
  SIDEWAY_RANGE    — แนวรับ/ต้านชัดเจน ราคาแกว่งตัวในกรอบ          [★★★★★]
  REVERSAL_FORMING — มีสัญญาณการกลับตัวและโมเมนตัมชะลอตัวลงชัดเจน  [★★★★★]
  DISTRIBUTION     — ราคาแตะขอบบนของกรอบสะสมหนาแน่น           [★★★★★]
  TRANSITIONAL     — ใช้ได้แต่ลดน้ำหนัก Entry Score 30%          [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  TRENDING_STRONG   — ตลาดมีแนวโน้มแข็งแกร่ง สวนทางมีโอกาสขาดทุนสูง
  BREAKOUT_EMERGING — ราคากำลังเบรคทะลุกรอบแนวรับ/แนวต้าน
  ACCUMULATION      — ตลาดบีบอัดตัวรอเลือกทิศทาง ยังไม่มีกรอบแกว่งตัวชัดเจน
  TRENDING_WEAK     — ตลาดยังมีแนวโน้มอ่อนๆ โอกาสกลับตัวไม่แน่นอน
  LIQUIDITY_VOID    — ตลาดขาดสภาพคล่อง ราคาเคลื่อนไหวไม่มีทิศทาง
  CHOPPY_UNCERTAIN  — ราคาผันผวนสะเปะสะปะ ไม่มีโครงสร้างชัดเจน
  UNCLEAR           — สภาวะตลาดมีความขัดแย้งเชิงข้อมูล

--------------------------------------------------------------------------------
[2] REQUIRED INPUTS
--------------------------------------------------------------------------------
1. M5 OHLCV Candles (ย้อนหลังอย่างน้อย 30 แท่ง)
   เหตุผล: คำนวณเส้น Stochastic, แนวรับ/แนวต้านระดับท้องถิ่น และ ATR

2. ATR(14) บน M5
   เหตุผล: Normalize ระยะการสัมผัสแนวและค่าความผันผวนเพื่อให้เป็นมาตรฐานเดียวกันในทุกคู่เงิน

3. Local S/R Level (คำนวณจากช่วงแท่งเทียน M5[-13] ถึง M5[-3] ย้อนหลัง)
   - Support Level (แนวรับ)      = ค่าต่ำสุดของราคา Low ในช่วง M5[-13] ถึง M5[-3]
   - Resistance Level (แนวต้าน) = ค่าสูงสุดของราคา High ในช่วง M5[-13] ถึง M5[-3]
   เหตุผล: กำหนดแนวอ้างอิงล่าสุดที่หลีกเลี่ยงผลกระทบของ 3 แท่งเทียนปัจจุบัน (Buffer Zone)

4. Stochastic Oscillator (14, 3, 3) บน M5
   - %K Period  = 14 (Lookback สำหรับหาสูงสุด/ต่ำสุด)
   - %D Period  = 3 (ค่าเฉลี่ย SMA ของ %K)
   - Smoothing = 3
   เหตุผล: วัดแรงส่งโมเมนตัมที่เข้าสู่โซน Overbought (> 80) หรือ Oversold (< 20)

5. Average Volume (เฉลี่ย 20 แท่ง M5)
   เหตุผล: ตรวจสอบสภาวะ Volume Climax เพื่อใช้ในการบล็อกสัญญาณที่เกิดจากการ Breakout จริง

6. Real-Time Tick Feed
   เหตุผล: ตรวจสอบความสม่ำเสมอของสัญญาณโบรกเกอร์ (Broker Feed Validity)

7. Market State + State Age (จาก Intelligence OS)
   เหตุผล: ใช้ตรวจสอบสภาวะตลาดที่เหมาะสมและช่วงอายุของ State เพื่อปรับคะแนน Entry Score

8. High Impact News Calendar (+/- 15 นาที)
   เหตุผล: กำหนดเวลาห้ามส่งสัญญาณเทรดช่วงประกาศข่าวรุนแรง

--------------------------------------------------------------------------------
[3] ENTRY CONDITIONS
--------------------------------------------------------------------------------
ขั้นตอนการประเมินเรียงตามลำดับความสำคัญ (หากไม่ผ่านขั้นตอนใดขั้นตอนหนึ่งให้หยุดการทำงานทันที)

CONDITION 1 — Market State Eligibility
  ตรวจจับสภาวะตลาดจากระบบหลัก
  ผ่าน: SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION, TRANSITIONAL
  ไม่ผ่าน: หยุดการประเมินทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — Local S/R Level Touch Validation (วัดระยะโดย ATR)
  คำนวณหาระดับราคาแนวรับ (Support) และแนวต้าน (Resistance) ท้องถิ่น:
    Support = Min(Low[-13] ... Low[-3])
    Resistance = Max(High[-13] ... High[-3])
  กำหนดค่าเผื่อการสัมผัสแนว (Tolerance) = 0.1 × ATR_M5
  
  สำหรับ CALL (กลับตัวขึ้นจากแนวรับ):
    ต้องมีอย่างน้อยหนึ่งแท่งในช่วง M5[-3], M5[-2], M5[-1] ที่ราคาสัมผัสแนวรับ:
    Low[k] <= Support + (0.1 × ATR_M5) สำหรับ k ∈ {-3, -2, -1}
  
  สำหรับ PUT (กลับตัวลงจากแนวต้าน):
    ต้องมีอย่างน้อยหนึ่งแท่งในช่วง M5[-3], M5[-2], M5[-1] ที่ราคาสัมผัสแนวต้าน:
    High[k] >= Resistance - (0.1 × ATR_M5) สำหรับ k ∈ {-3, -2, -1}
    
  ไม่ผ่านเกณฑ์สัมผัส → หยุดการประเมินทันที → fail_reason_code: LEVEL_NOT_TOUCHED

CONDITION 3 — Stochastic Extreme Crossover Validation
  คำนวณหาค่า %K และ %D ของ Stochastic(14, 3, 3) ย้อนหลัง 2 แท่ง:
    %K_t = 100 × (Close_t - LowestLow_14) / Max((HighestHigh_14 - LowestLow_14), 1e-10)
    %D_t = SMA(%K, 3)
  
  สำหรับ CALL:
    3a. เกิดการตัดขึ้น (Bullish Crossover): %K[-2] <= %D[-2] และ %K[-1] > %D[-1]
    3b. สัญญาณเกิดขึ้นในเขต Oversold: %K[-1] < 20 และ %D[-1] < 20
  
  สำหรับ PUT:
    3a. เกิดการตัดลง (Bearish Crossover): %K[-2] >= %D[-2] และ %K[-1] < %D[-1]
    3b. สัญญาณเกิดขึ้นในเขต Overbought: %K[-1] > 80 และ %D[-1] > 80

  ไม่ผ่านเกณฑ์การตัดกันในโซนสุดโต่ง → หยุดประเมิน → fail_reason_code: STOCHASTIC_CROSSOVER_INVALID

CONDITION 4 — Candle Body Size Check
  แท่งเทียนตั้งต้น M5[-1] ต้องมีเนื้อเทียนหนาเพียงพอเพื่อหลีกเลี่ยงช่วงราคาไร้ทิศทาง (Doji):
    Body Size = |Close[-1] - Open[-1]| >= 0.05 × ATR_M5
  ไม่ผ่านเกณฑ์ → หยุดประเมิน → fail_reason_code: DOJI_SETUP_INVALID

CONDITION 5 — Volume Breakout Validation
  ป้องกันความเสี่ยงกรณีเกิดการทะลุผ่านแนวรับ/ต้านอย่างแท้จริงด้วยความเร็วสูง:
  IF Volume[-1] > 1.5 × Avg_Volume
    สำหรับ CALL: หาก Close[-1] < Support → ถือว่าเป็น Breakout ขาลง → fail_reason_code: BREAKOUT_CLOSED_OUTSIDE
    สำหรับ PUT: หาก Close[-1] > Resistance → ถือว่าเป็น Breakout ขาขึ้น → fail_reason_code: BREAKOUT_CLOSED_OUTSIDE
  ผ่านเกณฑ์: ดำเนินการขั้นตอนต่อไป

CONDITION 6 — Broker Feed Validity Check
  ตรวจเช็คข้อมูลราคา Tick ล่าสุด ต้องมีการส่งค่าต่อเนื่องและไม่ค้างเกิน 10 วินาที
  ไม่ผ่านเกณฑ์ → หยุดประเมิน → fail_reason_code: BROKER_FEED_FREEZE

--------------------------------------------------------------------------------
[4] ENTRY SCORE LOGIC
--------------------------------------------------------------------------------
คะแนนเข้าเทรดดิ้งดิบ (Raw Entry Score) คำนวณในช่วง 0–100 คะแนน จาก 4 ตัวแปรถ่วงน้ำหนักดังนี้:

Factor 1 — Stochastic Extremeness (F_extreme) น้ำหนัก 30%
  วัดความลึกเชิงโมเมนตัมในโซนสุดโต่ง
  สำหรับ CALL (วัดค่าสูงสุดระหว่าง %K และ %D ยิ่งใกล้ 0 คะแนนยิ่งสูง):
    Stoch_Max = Max(%K[-1], %D[-1])
    F_extreme = Max(0, 100 × (1.0 - (Stoch_Max / 20.0)))
  สำหรับ PUT (วัดค่าต่ำสุดระหว่าง %K และ %D ยิ่งใกล้ 100 คะแนนยิ่งสูง):
    Stoch_Min = Min(%K[-1], %D[-1])
    F_extreme = Max(0, 100 × ((Stoch_Min - 80.0) / 20.0))

Factor 2 — Crossover Separation (F_sep) น้ำหนัก 20%
  วัดระยะห่างระหว่างเส้น %K และ %D หลังจากการตัดกัน เพื่อยืนยันแรงผลักกลับเฉลียบพลัน
    Sep = |%K[-1] - %D[-1]|
    F_sep = Min(100, (Sep / 5.0) × 100)
    (หากระยะห่างตัดกันเกิน 5.0 จะได้คะแนนเต็ม 100)

Factor 3 — Touch Precision (F_touch) น้ำหนัก 20%
  วัดความแม่นยำในการทดสอบระดับราคาของแท่งเทียนภายในกรอบ 3 แท่งเทียนที่ผ่านมา
  สำหรับ CALL (พิจารณาค่าต่ำสุด Low_min = Min(Low[-3], Low[-2], Low[-1])):
    Dist = (Low_min - Support) / ATR_M5
    หาก Dist <= 0 (ราคาแทงผ่านเส้นลงไปแล้วดึงกลับ) → F_touch = 100
    หาก Dist > 0 (ราคาลงมาเกือบแตะ) → F_touch = Max(0, 100 - (Dist / 0.1) × 100)
  สำหรับ PUT (พิจารณาค่าสูงสุด High_max = Max(High[-3], High[-2], High[-1])):
    Dist = (Resistance - High_max) / ATR_M5
    หาก Dist <= 0 (ราคาแทงทะลุเส้นขึ้นไปแล้วดึงกลับ) → F_touch = 100
    หาก Dist > 0 (ราคาขึ้นมาเกือบแตะ) → F_touch = Max(0, 100 - (Dist / 0.1) × 100)

Factor 4 — Range Amplitude Quality (F_location) น้ำหนัก 30%
  ประเมินความกว้างของกรอบ Sideway ท้องถิ่น เพื่อยืนยันพื้นที่ผลกำไรที่เพียงพอและคุณภาพของกรอบสะสมราคา
    Range = Resistance - Support
    R_ratio = Range / ATR_M5
    F_location = Min(100, Max(0, ((R_ratio - 1.0) / 4.0) × 100))
    (หากความกว้างของกรอบตราบเท่า 5 เท่าของ ATR_M5 หรือมากกว่า จะได้คะแนนเต็ม 100)

สูตรการคิดคะแนนรวม:
  Raw Entry Score = (0.30 × F_extreme) + (0.20 × F_sep) + (0.20 × F_touch) + (0.30 × F_location)

การปรับปรุงคะแนนตามสภาวะ State Lifecycle และสภาวะตลาดเฉพาะตัว:
  - Fresh / Active   → ใช้คะแนนดิบตามจริง (Raw Entry Score)
  - Late             → Entry Score = Raw Entry Score × 0.80
  - Exhausted        → จะทำการส่งสัญญาณ Block คะแนนทันที (Block Score = 100)
  - TRANSITIONAL State  → ปรับคะแนนลดลง 30% (คูณ 0.70) หลังการปรับตามอายุสภาวะ

--------------------------------------------------------------------------------
[5] BLOCK SCORE LOGIC
--------------------------------------------------------------------------------
คะแนนสะกัดกั้นความเสี่ยง (Block Score) เริ่มต้นที่ 0 และสะสมเพิ่มขึ้นตามระดับสัญญาณเสี่ยงทางสถิติ

--- SOFT BLOCK FACTORS (สะสมคะแนนความเสี่ยงสูงสุด 100 คะแนน) ---
  SF-1: ความผันผวนของตลาดเกินเกณฑ์มาตรฐาน
        ATR_M5 ล่าสุด > 1.5 × ค่าเฉลี่ย ATR 20 แท่งย้อนหลัง
        → บวกสะสมเพิ่ม 30 คะแนน
  SF-2: มุมการตัดเฉียงของ Stochastic อ่อนกำลัง (Slow Crossover)
        |%K[-1] - %K[-2]| < 3.0
        → บวกสะสมเพิ่ม 25 คะแนน
  SF-3: สภาวะตลาดเป็น DISTRIBUTION หรือ TRANSITIONAL
        → บวกสะสมเพิ่ม 20 คะแนน

--- HARD BLOCK FACTORS (Block Score = 100 ทันทีและห้ามเปิดสถานะเด็ดขาด) ---
  HB-1: สภาวะตลาดเป็นสภาวะต้องห้าม (เช่น TRENDING_STRONG หรือ BREAKOUT_EMERGING)
  HB-2: ตลาดอยู่ในภาวะไร้ปริมาณซื้อขายสะสม (ATR_M5 < 0.25 × ค่าเฉลี่ย ATR 20 แท่ง)
  HB-3: ช่วงรอยต่อการออกข่าวเศรษฐกิจ High Impact ในรอบ +/- 15 นาที
  HB-4: ช่วงอายุของตลาดเข้าสู่ระยะเหนื่อยล้าสิ้นสุดรอบ (State Lifecycle = Exhausted)
  HB-5: เกิด Volume Breakout ชัดเจน (Volume[-1] > 1.5 × Avg_Volume และราคาปิดออกนอกขอบ S/R)
  HB-6: เกิดแรงกดดันต้านการกลับตัว (Opposite Wick Dominance)
        สำหรับ CALL: ไส้เทียนด้านบนของแท่ง M5[-1] ยาวกว่าไส้เทียนด้านล่าง (Upper Wick > Lower Wick)
        สำหรับ PUT: ไส้เทียนด้านล่างของแท่ง M5[-1] ยาวกว่าไส้เทียนด้านบน (Lower Wick > Upper Wick)

--- สูตรสุดท้ายในการประเมินคะแนนบล็อก ---
  IF พบเจอเงื่อนไข Hard Block ข้อใดข้อหนึ่ง → Block Score = 100
  ELSE → Block Score = Sum(Soft Block Points) โดนจำกัดเพดานสูงสุดที่ 100 คะแนน

--------------------------------------------------------------------------------
[6] STRATEGY CONFIDENCE
--------------------------------------------------------------------------------
คะแนนความมั่นใจของการวิเคราะห์ด้วยสูตรคำนวณค่าต่อเนื่อง (Continuous Confidence Model) ในสเกล 0.0 ถึง 1.0:

  C_strategy = (0.40 × S_stoch) + (0.35 × S_crossover) + (0.25 × S_touch)

เกณฑ์การคิดคะแนนย่อย (Sub-scores):

  1. S_stoch (Stochastic Deep Extreme Score):
     สำหรับ CALL: S_stoch = Max(0.0, 1.0 - (Max(%K[-1], %D[-1]) / 20.0))
     สำหรับ PUT: S_stoch = Max(0.0, 1.0 - ((100.0 - Min(%K[-1], %D[-1])) / 20.0))

  2. S_crossover (Crossover Momentum Velocity Score):
     วัดอัตราเร่งการพุ่งตัดกันระหว่าง %K และ %D ย้อนหลัง 2 แท่ง
     S_crossover = Min(1.0, (|%K[-1] - %D[-1]| + |%K[-2] - %D[-2]|) / 10.0)

  3. S_touch (Level Touch Accuracy Score):
     สำหรับ CALL: S_touch = Max(0.0, 1.0 - (|Low_min - Support| / (0.1 × ATR_M5)))
     สำหรับ PUT: S_touch = Max(0.0, 1.0 - (|High_max - Resistance| / (0.1 × ATR_M5)))
     โดยกำหนดให้ Low_min = Min(Low[-3..-1]) และ High_max = Max(High[-3..-1])

--------------------------------------------------------------------------------
[7] FAIL CONDITIONS
--------------------------------------------------------------------------------
ระบบจะส่งสัญญาณ NO_SETUP ออกไปทันทีที่พบเจอเหตุการณ์การทำงานขัดข้องเชิงกฎข้อใดข้อหนึ่งดังนี้:

  MARKET_STATE_BLOCKED        : สภาวะตลาดหลักไม่อยู่ในเงื่อนไขการสร้างผลกำไรกลยุทธ์กลับตัว
  LEVEL_NOT_TOUCHED           : ราคาในช่วง 3 แท่งเทียนล่าสุดไม่สามารถลงมาสัมผัสระดับแนวรับ/ต้านได้ตามเกณฑ์
  STOCHASTIC_CROSSOVER_INVALID: การตัดกันของ Stochastic ไม่อยู่ในโซนความน่าจะเป็นสูง
  DOJI_SETUP_INVALID          : ขนาดเนื้อเทียนของแท่งตั้งต้นสั้นเกินไปจนเกิดความไม่สมดุล
  BREAKOUT_CLOSED_OUTSIDE     : มีการยืนยันการปิดราคาเกินแนวขอบระดับร่วมกับปริมาณซื้อขายสะสมสูง
  BROKER_FEED_FREEZE          : สัญญาณความเร็วข้อมูลโบรกเกอร์ค้างเกินเวลาควบคุมป้องกันความเสี่ยง
  NEWS_BLACKOUT               : ช่วงระงับการเก็งกำไรข่าวนอกเวลาปลอดภัย

--------------------------------------------------------------------------------
[8] EXPECTED BEHAVIOR
--------------------------------------------------------------------------------
Strong Reversal (สัญญาณเกรดเอ):
  ราคาทำโครงสร้างชนแนวระดับ S/R ท้องถิ่นพร้อมโมเมนตัมความหนาแน่นสูง และเกิด Stochastic Crossover ตัดหักหัวกลับทันทีในโซนสุดโต่ง
  ความกว้างของช่วงราคาแกว่งตัวกว้างกว่า 3 เท่าของ ATR และเกิดไส้เทียนดึงกลับทันทีใน 3 แท่งล่าสุด
  C_strategy > 0.80, Entry Score > 75
  เป้าหมายคาดหวัง: ราคาเกิดการกลับตัวปิดแท่ง M5 ถัดไปในทิศทางของสัญญาณทันที

Weak Reversal (สัญญาณเกรดรอง):
  ระดับแนวราคาของกรอบแกว่งค่อนข้างแคบ หรือ Stochastic ตัดกันเฉียงราบเรียบ มีระยะห่างที่น้อย
  C_strategy อยู่ในช่วง 0.50–0.79, Entry Score 60–74
  เป้าหมายคาดหวัง: ราคาอาจเด้งสั้นๆ หรือมีการย้อนกลับไปไซด์เวย์สัมผัสแนวอีกรอบก่อนเกิดการกลับตัว

False Reversal (สัญญาณหลอก):
  ราคาผ่านการแตะสะสมแล้วเกิดการปิดออกข้างนอกกรอบด้วยเนื้อแท่งเทียนที่ยาวพร้อมปริมาณซื้อขายล้นระบบ (Volume Climax)
  ซึ่งแสดงถึงการเบรคทะลุแนวระดับจริงเพื่อเปลี่ยนผ่านเข้าสู่แนวโน้มหลัก
  ระบบจะสามารถตรวจจับได้จากขั้นตอน Condition 5 และล็อกสเปกให้ออก NO_SETUP บล็อกสัญญาณทันที

--------------------------------------------------------------------------------
[9] AUDIT REQUIREMENTS
--------------------------------------------------------------------------------
ข้อมูลทั้งหมดต่อไปนี้จะต้องมีการบันทึกลงในระบบ WORM Database ทุกครั้งที่เกิดสตรีมประเมินกลยุทธ์:

  - audit_id        : รหัสเฉพาะ UUIDv4 ในแต่ละรอบคำนวณ
  - timestamp       : แสตมป์เวลาระบบในรูปมาตรฐานสากล (UTC)
  - symbol          : ชื่อสินทรัพย์ที่ประเมิน
  - market_state    : สภาวะตลาดรวมถึง State Age ปัจจุบัน
  - candle_ohlcv    : OHLCV ของแท่ง M5[-1]
  - atr_m5          : ค่าความผันผวน ATR_M5 ปัจจุบัน
  - local_support   : ระดับราคาแนวรับท้องถิ่นที่อ้างอิง
  - local_resistance: ระดับราคาแนวต้านท้องถิ่นที่อ้างอิง
  - stoch_k         : ค่า Stochastic %K ล่าสุด
  - stoch_d         : ค่า Stochastic %D ล่าสุด
  - prev_k          : ค่า Stochastic %K แท่งก่อนหน้า
  - prev_d          : ค่า Stochastic %D แท่งก่อนหน้า
  - f_extreme       : คะแนนองค์ประกอบ Stochastic Extremeness
  - f_sep           : คะแนนองค์ประกอบ Crossover Separation
  - f_touch         : คะแนนองค์ประกอบ Touch Precision
  - f_location      : คะแนนองค์ประกอบ Range Amplitude
  - entry_score_raw : คะแนนประเมินรวมก่อนคูณฟิลเตอร์สภาวะ
  - entry_score     : คะแนนประเมินจริงขั้นสุดท้าย
  - block_score     : คะแนนความเสี่ยงการบล็อกสะสมรวม
  - s_stoch         : ดัชนีความมั่นใจ Stochastic Extremeness
  - s_crossover     : ดัชนีความมั่นใจ Crossover Momentum
  - s_touch         : ดัชนีความมั่นใจ Touch Accuracy
  - c_strategy      : ค่ารวมความมั่นใจกลยุทธ์ตามหลักสถิติ
  - eligible        : ผลประเมินการตรวจสอบเบื้องต้น (true/false)
  - action          : สัญญาณเทรดดิ้ง (CALL / PUT / NO_SETUP)
  - fail_reason_code: รหัสอธิบายเหตุผลล้มเหลว (null เมื่อได้รับไฟเขียว)

--------------------------------------------------------------------------------
[10] OUTPUT CONTRACT (FROZEN SCHEMA)
--------------------------------------------------------------------------------
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_StochasticCrossover_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "stochastic_crossover" },
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
        "stoch_k":      { "type": "NUMBER" },
        "stoch_d":      { "type": "NUMBER" },
        "local_level":  { "type": "NUMBER" }
      },
      "required": ["stoch_k", "stoch_d", "local_level"]
    }
  },
  "required": [
    "strategy_name", "eligible", "action", "entry_score", "block_score",
    "strategy_confidence", "direction_confidence", "expected_state",
    "fail_reason_code", "audit_id", "expiry", "details"
  ]
}
