# FINAL SPECIFICATION: BB RSI CONFLUENCE (bb_rsi_confluence)
PRODUCTION M5 BINARY — ยึด PTGF-M5 Blueprint เป็น Frozen Baseline

--------------------------------------------------------------------------------
[1] STRATEGY OVERVIEW
--------------------------------------------------------------------------------
ชื่อกลยุทธ์:
  Bollinger Bands + RSI Confluence
  (Bollinger Bands and RSI Confluence Extreme Reversal Strategy)

วัตถุประสงค์:
  ตรวจจับจุดกลับตัวรุนแรง (Extreme Reversal) บนแท่งเทียน M5 ล่าสุด
  เมื่อราคาปิดทะลุขอบนอกของ Bollinger Bands ร่วมกับตัวบ่งชี้ RSI(7) ที่อยู่ในสภาวะ Overbought/Oversold
  และยืนยันด้วยการสัมผัสพิกัดแนวรับ/แนวต้านในอดีต (Local Support/Resistance)
  ส่งสัญญาณ ณ วินาทีเปิดของแท่งถัดไปทันที โดยกำหนด Expiry ที่ปิดแท่ง M5 ถัดไป (5 นาที)

บทบาทในระบบ:
  Leading Strategy — มีสิทธิ์สร้างสัญญาณหลักด้วยตัวเองจากการเกิด Confluence เชิงโครงสร้างราคาและ Momentum

ประเภทสัญญาณ:
  Reversal — กลับตัวระยะสั้นภายใน 1 แท่ง M5 (5 นาที)

Market States ที่เหมาะสม:
  SIDEWAY_RANGE    — แนวรับ/ต้านชัดเจน ราคาเด้งในกรอบและแบนด์       [★★★★★]
  REVERSAL_FORMING — เกิดการปฏิเสธราคาบริเวณขอบแบนด์ชัดเจน      [★★★★★]
  DISTRIBUTION     — ราคาแตะขอบบนของกรอบสะสมเตรียมกลับตัว       [★★★★★]
  TRANSITIONAL     — ใช้ได้แต่ลดน้ำหนัก Entry Score 30%          [★★★☆☆]

Market States ที่ห้ามใช้เด็ดขาด:
  TRENDING_STRONG   — ราคาวิ่งเกาะขอบแบนด์เหนียวแน่น (Band Walking) โอกาสแพ้สูงมาก
  BREAKOUT_EMERGING — ราคากำลังฉีกแบนด์ทะลุแนวต้าน/รับแบบรุนแรง
  ACCUMULATION      — ตลาดกำลังบีบตัวแคบ (Squeeze) เพื่อรอระเบิดทิศทาง
  TRENDING_WEAK     — แนวโน้มอ่อนแรงแต่ยังไหลไปตามทิศทางแบนด์
  LIQUIDITY_VOID    — ปริมาณซื้อขายต่ำเกินไป แบนด์แคบและราคาไม่มีนัยสำคัญ
  CHOPPY_UNCERTAIN  — ตลาดผันผวนสับสนในกรอบแคบเกินไป
  UNCLEAR           — สภาวะตลาดคลุมเครือ

--------------------------------------------------------------------------------
[2] REQUIRED INPUTS
--------------------------------------------------------------------------------
1. M5 OHLCV Candles (ย้อนหลัง 100 แท่ง)
   เหตุผล: ใช้คำนวณ Bollinger Bands, RSI(7), พิกัดแนวรับ/ต้านท้องถิ่น (Local S/R) และ ATR

2. ATR(14) บน M5
   เหตุผล: Normalize ระยะการคำนวณและเกณฑ์การยอมรับค่าเผื่อให้ไม่ขึ้นกับคู่เงิน

3. Bollinger Bands ( window, std_dev )
   เหตุผล: กำหนดขอบเขตความผันผวนทางสถิติของราคาในรอบเวลาที่กำหนด (14 หรือ 20)

4. RSI(7) พร้อม Wilder's Smoothing
   เหตุผล: วัดแรงขับเคลื่อน (Momentum) ในระยะสั้นเพื่อหาจุด Overbought/Oversold

5. Local Support & Resistance (คำนวณจาก Swing High/Low ย้อนหลังช่วง 10 แท่งก่อนหน้า)
   เหตุผล: ตรวจจับแนวราคาที่มีนัยสำคัญซึ่งอยู่นอกเขตสัญญาณ 3 แท่งล่าสุด

6. Average Volume (เฉลี่ย 20 แท่ง M5)
   เหตุผล: ตรวจสอบปริมาณซื้อขายประกอบเพื่อกรองการเบรคเอาท์ปลอม

7. Real-Time Tick Feed
   เหตุผล: ตรวจสอบสถานะการเชื่อมต่อและความสมบูรณ์ของราคา ณ วินาทีเปิดออเดอร์

8. Market State + State Age (จาก Intelligence OS)
   เหตุผล: ตรวจสอบสภาวะตลาดตามมาตรฐานความปลอดภัยเพื่อบล็อกสภาวะเทรนด์

9. High Impact News Calendar (+/- 15 นาที)
   เหตุผล: หลีกเลี่ยงความผันผวนที่สูญเสียความแม่นยำทางสถิติในช่วงข่าวสำคัญ

--------------------------------------------------------------------------------
[3] ENTRY CONDITIONS
--------------------------------------------------------------------------------
การประเมินสัญญาณต้องดำเนินการตามลำดับขั้นตอน (Evaluation Pipeline) หากไม่ผ่านขั้นตอนใดให้หยุดการทำงานทันที

CONDITION 1 — Market State Eligibility
  ตรวจเช็คว่า Market State ปัจจุบันอยู่ในสภาวะที่เหมาะสมหรือไม่
  ผ่าน: SIDEWAY_RANGE, REVERSAL_FORMING, DISTRIBUTION, TRANSITIONAL
  ไม่ผ่าน: หยุดการทำงานทันที → fail_reason_code: MARKET_STATE_BLOCKED

CONDITION 2 — S/R Level Quality Check (S_level Engine)
  คำนวณระดับแนวรับและแนวต้านในอดีต (Local Support & Resistance):
    - local_support = ค่าต่ำสุดของราคา Low ในช่วงแท่งที่ -13 ถึง -4 ( low_prices.iloc[-13:-3].min() )
    - local_resistance = ค่าสูงสุดของราคา High ในช่วงแท่งที่ -13 ถึง -4 ( high_prices.iloc[-13:-3].max() )

  การคำนวณความแข็งแกร่งแนวราคา (S_level_base, สูงสุด 100):
    - C_touch (50 คะแนน): จำนวนครั้งที่ราคาสัมผัสระดับภายในค่าเผื่อ ±0.1*ATR โดยให้สัมผัสละ 25 คะแนน (สูงสุด 50)
    - D_react (30 คะแนน): ระยะการดีดกลับเฉลี่ยหลังสัมผัสแนวเมื่อเทียบกับ ATR (สูงสุด 30)
    - V_profile (20 คะแนน): การทับซ้อนกับโซนปริมาณซื้อขายหนาแน่นย้อนหลัง 100 แท่ง (+20 คะแนน)

  คำนวณการลดทอนคะแนนตามเวลา (Age Decay):
    - S_level = S_level_base * exp(-0.015 * age)
    - age คือจำนวนแท่ง M5 ที่ห่างจากจุดที่เกิดแนวสัมผัสล่าสุด
  เกณฑ์การอนุมัติ: S_level ต้องไม่ต่ำกว่า 40 คะแนน
  ไม่ผ่าน → fail_reason_code: LEVEL_TOO_WEAK

CONDITION 3 — Price Touch Local Levels (การสัมผัสแนวราคาใน 3 แท่งล่าสุด)
  สำหรับ CALL (กลับตัวขึ้น):
    - ต้องมีอย่างน้อยหนึ่งแท่งในช่วง 3 แท่งล่าสุด ([-3, -2, -1]) ที่ Low[-k] <= local_support * 1.0002
  สำหรับ PUT (กลับตัวลง):
    - ต้องมีอย่างน้อยหนึ่งแท่งในช่วง 3 แท่งล่าสุด ([-3, -2, -1]) ที่ High[-k] >= local_resistance * 0.9998
  ไม่ผ่าน → fail_reason_code: LEVEL_NOT_TOUCHED

CONDITION 4 — Bollinger Bands Penetration
  สำหรับ CALL:
    - Close[-1] <= Lower Band[-1] (ราคาปิดทะลุหรือสัมผัสขอบล่าง Bollinger Band)
  สำหรับ PUT:
    - Close[-1] >= Upper Band[-1] (ราคาปิดทะลุหรือสัมผัสขอบบน Bollinger Band)
  ไม่ผ่าน → fail_reason_code: BB_PENETRATION_INVALID

CONDITION 5 — RSI Extreme Oversold/Overbought
  สำหรับ CALL:
    - RSI(7)[-1] < config['rsi_oversold'] (เช่น ต่ำกว่า 30 หรือ 35 ตามเงื่อนไขคู่เงิน)
  สำหรับ PUT:
    - RSI(7)[-1] > config['rsi_overbought'] (เช่น สูงกว่า 70 หรือ 65 ตามเงื่อนไขคู่เงิน)
  ไม่ผ่าน → fail_reason_code: RSI_NOT_EXTREME

CONDITION 6 — Broker Feed Validity
  ตรวจสอบอัตราการส่งข้อมูลราคาของโบรกเกอร์ (Tick Update Rate) ต้องมีการขยับราคาภายใน 10 วินาทีล่าสุด
  ไม่ผ่าน → fail_reason_code: BROKER_FEED_FREEZE

--------------------------------------------------------------------------------
[4] ENTRY SCORE LOGIC
--------------------------------------------------------------------------------
Entry Score (สเกล 0–100) คำนวณจากค่าน้ำหนัก 4 ปัจจัย รวม 100% ดังนี้:

Factor 1 — RSI Deviation Factor (F_rsi) น้ำหนัก 30%
  วัดความลึกของ RSI(7) ที่เกินเกณฑ์ขีดสุดเข้าไป
  สำหรับ CALL:
    - R_rsi = rsi_oversold_threshold - RSI(7)[-1]
    - IF RSI(7)[-1] >= rsi_oversold_threshold → F_rsi = 0
    - IF RSI(7)[-1] < rsi_oversold_threshold → F_rsi = Min(100, (R_rsi / rsi_oversold_threshold) * 100 * 3.0)
  สำหรับ PUT:
    - R_rsi = RSI(7)[-1] - rsi_overbought_threshold
    - IF RSI(7)[-1] <= rsi_overbought_threshold → F_rsi = 0
    - IF RSI(7)[-1] > rsi_overbought_threshold → F_rsi = Min(100, (R_rsi / (100 - rsi_overbought_threshold)) * 100 * 3.0)

Factor 2 — Bollinger Bands Penetration Factor (F_bb) น้ำหนัก 30%
  วัดระยะของราคาปิดที่เบี่ยงเบนทะลุขอบนอกของ Bollinger Band normalized ด้วย ATR
  - D_pen = |Close[-1] - BB_Band[-1]| / ATR_M5  (BB_Band คือ Lower Band สำหรับ CALL และ Upper Band สำหรับ PUT)
  - F_bb = Min(100, (D_pen / 0.3) * 100)
  (หมายเหตุ: หากราคาปิดทะลุขอบแบนด์ไป 0.3 เท่าของ ATR จะได้คะแนนเต็ม)

Factor 3 — Level Contact Precision Factor (F_sr) น้ำหนัก 20%
  วัดความแม่นยำในการทดสอบแนวรับ/ต้านใน 3 แท่งล่าสุด
  - D_sr = Min( |Low[-k] - local_support| สำหรับ k=1,2,3 ) / ATR_M5 (สำหรับ CALL)
  - D_sr = Min( |High[-k] - local_resistance| สำหรับ k=1,2,3 ) / ATR_M5 (สำหรับ PUT)
  - F_sr = Max(0, 100 - (D_sr / 0.1) * 100)
  (หมายเหตุ: ยิ่งราคาดิ่งไปสัมผัสใกล้แนวมากที่สุด คะแนนส่วนนี้ยิ่งเข้าใกล้ 100)

Factor 4 — Volumetric Confirmation Factor (F_vol) น้ำหนัก 20%
  ประเมินความมั่นคงผ่านปริมาณซื้อขายเปรียบเทียบกับค่าเฉลี่ย
  - R_vol = Volume[-1] / Avg_Volume(20)
  - F_vol = Min(100, Max(0, ((R_vol - 0.5) / 1.5) * 100))

สูตรคำนวณคะแนนดิบ (Raw Entry Score):
  Raw Entry Score = (0.30 * F_rsi) + (0.30 * F_bb) + (0.20 * F_sr) + (0.20 * F_vol)

การปรับตามวงจรอายุของสภาวะตลาด (State Lifecycle Adjustment):
  - Fresh / Active   → ใช้ Raw Entry Score ตรง
  - Late             → Entry Score = Raw Entry Score * 0.80
  - Exhausted        → บล็อกสัญญาณทันที (Block Score = 100)
  - TRANSITIONAL     → ปรับลดคะแนนลงโดยคุณตัวคูณพิเศษ: Entry Score = Raw Entry Score * 0.70

--------------------------------------------------------------------------------
[5] BLOCK SCORE LOGIC
--------------------------------------------------------------------------------
Block Score (สเกล 0–100) ใช้สำหรับสะกัดกั้นสัญญาณที่มีความเสี่ยงสูง

--- SOFT BLOCK FACTORS (สะสมคะแนนเพิ่มความเสี่ยง) ---
  SF-1: ATR ปัจจุบัน > 1.8 * Average ATR(20)
        → +35 คะแนน (สภาวะความผันผวนที่สูงเกินกว่าโครงสร้างเชิงสถิติทั่วไป)
  SF-2: Close[-1] ปิดห่างจาก Local Level มากกว่า 0.3 * ATR_M5
        → +25 คะแนน (ราคาไม่สามารถประคองตัวอยู่ใกล้แนวระดับสำคัญได้)
  SF-3: Market State เป็น TRANSITIONAL หรือ DISTRIBUTION
        → +20 คะแนน (ความไม่แน่นอนในการสลับรูปแบบสภาวะตลาด)

--- HARD BLOCK FACTORS (Block Score = 100 ทันที) ---
  HB-1: Market State เป็น TRENDING_STRONG หรือ BREAKOUT_EMERGING
        → Block Score = 100
  HB-2: ปริมาณซื้อขายเกินขีดสุดโดยปิดทะลุขอบนอกและเปิดห่างด้วยช่องว่างสเปรด (Gap)
        (Volume[-1] > 2.0 * Avg_Volume(20) และ Close[-1] ทะลุนอก Bollinger Band เกิน 0.5*ATR)
        → Block Score = 100
  HB-3: มีแท่งเทียนก่อนหน้าเกิดทิศทางตรงกันข้ามที่มีไส้เทียนยาวเด่นชัดเจนข่มทิศทางเป้าหมาย
        (Wick_opposite > Wick_target * 1.5)
        → Block Score = 100
  HB-4: ช่วงเวลามีข่าวรุนแรง High Impact News (ในกรอบ +/- 15 นาที)
        → Block Score = 100
  HB-5: วงจรสภาวะตลาดเสื่อมสภาพ (State Lifecycle = Exhausted)
        → Block Score = 100
  HB-6: ไม่มีการอัปเดตราคาจากฟีดเกินกว่า 10 วินาที (Broker Feed Freeze)
        → Block Score = 100

สูตร Block Score สุดท้าย:
  IF มี Hard Block ใดๆ เกิดขึ้น → Block Score = 100
  ELSE → Block Score = Min(100, Sum(คะแนนของ Soft Block ที่พบ))

--------------------------------------------------------------------------------
[6] STRATEGY CONFIDENCE
--------------------------------------------------------------------------------
C_strategy คำนวณในรูปของค่าต่อเนื่องทางคณิตศาสตร์ (สเกล 0.0–1.0):
  C_strategy = (0.40 * S_rsi) + (0.40 * S_bb) + (0.20 * S_sr)

คะแนนย่อย (Sub-scores):
  1. RSI Extent Score (S_rsi):
     - สำหรับ CALL: S_rsi = Min(1.0, (rsi_oversold_threshold - RSI(7)[-1]) / 10.0)
     - สำหรับ PUT: S_rsi = Min(1.0, (RSI(7)[-1] - rsi_overbought_threshold) / 10.0)
     (หมายเหตุ: หาก RSI ลึกเข้าไปในแนวเขตเกินกว่าเกณฑ์ 10 จุดขึ้นไป จะได้คะแนนเต็ม 1.0)

  2. Bollinger Band Penetration Score (S_bb):
     - S_bb = Min(1.0, |Close[-1] - BB_Band[-1]| / (0.20 * ATR_M5))
     (หมายเหตุ: ยิ่งราคาปิดทะลุแบนด์ออกไปมากกว่า 0.2 เท่าของ ATR จะได้คะแนนเต็ม 1.0)

  3. Level Contact Score (S_sr):
     - S_sr = Max(0.0, 1.0 - (D_sr / 0.08))
     (หมายเหตุ: ระยะห่างที่สัมผัสแนวต่ำกว่า 0.08 * ATR_M5 จะสะท้อนคะแนนความแม่นยำสูงขึ้น)

ตัวอย่างการคำนวณ (CALL สำหรับ EURUSD):
  RSI(7) ปัจจุบัน = 28.0 (เกณฑ์คือ 35), Close = 1.08500, Lower BB = 1.08510, ATR = 0.00100, local_support = 1.08495, Low[-1] = 1.08496
  - S_rsi = Min(1.0, (35.0 - 28.0) / 10.0) = 0.70
  - S_bb = Min(1.0, |1.08500 - 1.08510| / (0.20 * 0.00100)) = Min(1.0, 0.00010 / 0.00020) = 0.50
  - D_sr = |1.08496 - 1.08495| / 0.00100 = 0.01
  - S_sr = Max(0.0, 1.0 - (0.01 / 0.08)) = 0.875
  - C_strategy = (0.40 * 0.70) + (0.40 * 0.50) + (0.20 * 0.875) = 0.28 + 0.20 + 0.175 = 0.655

--------------------------------------------------------------------------------
[7] FAIL CONDITIONS
--------------------------------------------------------------------------------
กลยุทธ์จะกำหนดให้สัญญาณเป็น NO_SETUP ทันทีเมื่อเกิดประเด็นต่อไปนี้:
  MARKET_STATE_BLOCKED      : สภาวะตลาดไม่อยู่ในกลุ่มที่อนุญาต
  LEVEL_TOO_WEAK            : คะแนนความแข็งแกร่งของแนวราคาสะสม S_level < 40
  LEVEL_NOT_TOUCHED         : ไม่มีราคาใน 3 แท่งล่าสุดสัมผัสแนวราคา
  BB_PENETRATION_INVALID    : ราคาปิดไม่แตะหรือทะลุขอบนอกของแบนด์ตามทิศทาง
  RSI_NOT_EXTREME           : RSI(7) ไม่ผ่านเงื่อนไขขอบเขตการกลับตัวขั้นต่ำ
  BROKER_FEED_FREEZE        : การหน่วงค้างหรือขาดหาย of สัญญาณราคามากกว่า 10 วินาที
  NEWS_BLACKOUT             : อยู่ในรัศมีช่วงเวลาเผยแพร่ข่าวเศรษฐกิจระดับสูง +/- 15 นาที

--------------------------------------------------------------------------------
[8] EXPECTED BEHAVIOR
--------------------------------------------------------------------------------
Strong Confluence (สัญญาณกลับตัวคุณภาพสูง):
  ราคาปิดทะลุผ่านขอบของ Bollinger Band ชัดเจนและสัมผัสแนวรับ/แนวต้านที่แข็งแกร่ง (S_level > 70) 
  โดย RSI(7) เข้าลึกในโซนวิกฤต (เช่น <20 สำหรับ CALL หรือ >80 สำหรับ PUT)
  ค่า C_strategy > 0.80, Entry Score > 75
  คาดหวัง: ราคาดีดตัวกลับเข้ามาในแบนด์และปิดทิศทางตรงกันข้ามในแท่งถัดไปอย่างรวดเร็ว

Weak Confluence (สัญญาณกลับตัวคุณภาพต่ำ):
  ราคาเกือบไม่พ้นขอบแบนด์หรือขอบแบนด์ค่อนข้างแคบ แนวรับ/แนวต้านมีอายุนานเกินไป (S_level 40-55)
  ค่า C_strategy 0.50–0.70, Entry Score 60–74
  คาดหวัง: ราคาอาจเคลื่อนตัวออกด้านข้าง (Sideway) หรือเบรกเอาท์ผ่านแนวได้ง่าย

False Confluence (Breakout / Trend Start):
  ราคามีลักษณะการวิ่งไล่ราคาแบบ Momentum สูง ดึงขอบแบนด์ให้ฉีกขยายตัวกว้างขึ้นและราคาปิดนอกแบนด์ต่อเนื่อง
  ระบบจะสามารถดักจับสภาวะนี้ได้ทางโครงสร้างเทรนด์และการบล็อก Volume ใน Condition 1 & 5
  ผลลัพธ์: สัญญาณถูกบล็อกทันที (fail_reason_code: MARKET_STATE_BLOCKED)

--------------------------------------------------------------------------------
[9] AUDIT REQUIREMENTS
--------------------------------------------------------------------------------
บันทึกข้อมูลและประทับเวลาลงใน WORM Database ทุกครั้งที่มีการประเมินสัญญาณ:
  - audit_id              : UUIDv4 อ้างอิงสิทธิ์เฉพาะของรอบสัญญาณ
  - timestamp             : วันที่และเวลาประเมินผลในรูปแบบมาตรฐาน UTC
  - symbol                : ชื่อคู่เงินเป้าหมาย
  - market_state          : สภาวะตลาดและอายุของสภาวะตลาด
  - candle_ohlcv          : ข้อมูลราคาทั้งหมดของแท่ง M5 ย้อนหลัง 100 แท่ง
  - atr_m5                : ค่า ATR ของรอบเวลานั้น
  - local_support         : พิกัดแนวรับที่ใช้อ้างอิง
  - local_resistance      : พิกัดแนวต้านที่ใช้อ้างอิง
  - s_level_final         : คะแนนระดับความแข็งแกร่งของแนวราคาหลังคิดค่าเสื่อมถอย
  - rsi_value             : ค่าดัชนี RSI(7) ล่าสุด
  - upper_band            : พิกัดขอบบน Bollinger Band
  - lower_band            : พิกัดขอบล่าง Bollinger Band
  - f_rsi                 : คะแนนจากปัจจัย RSI
  - f_bb                  : คะแนนจากปัจจัย Bollinger Bands
  - f_sr                  : คะแนนจากปัจจัยแนวรับ/แนวต้าน
  - f_vol                 : คะแนนจากปริมาณซื้อขายสะสม
  - entry_score           : คะแนนเข้าซื้อขายสุดท้ายที่ผ่านตัวคูณสภาวะแล้ว
  - block_score           : คะแนนการบล็อกรวม
  - c_strategy            : ความมั่นใจสุดท้ายของกลยุทธ์ (Strategy Confidence)
  - eligible              : ผลความเหมาะสมของสัญญาณ (true/false)
  - action                : ทิศทางการส่งคำสั่ง (CALL / PUT / NO_SETUP)
  - fail_reason_code      : รหัสที่ล้มเหลวในการส่งสัญญาณ

--------------------------------------------------------------------------------
[10] OUTPUT CONTRACT (FROZEN SCHEMA)
--------------------------------------------------------------------------------
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StrategyOutputContract_BBRSIConfluence_M5_R3",
  "type": "OBJECT",
  "properties": {
    "strategy_name":       { "type": "STRING", "const": "bb_rsi_confluence" },
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
