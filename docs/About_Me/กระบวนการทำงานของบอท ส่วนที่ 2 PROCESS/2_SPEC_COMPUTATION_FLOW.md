# SPEC: COMPUTATION FLOW — คำนวณครั้งเดียว ส่งออกแบบไร้ RAM ระหว่างโมดูล

## หลักการแบ่งส่วนงาน (Decoupled Architecture)
บอทแบ่งการทำงานออกเป็นส่วนงานย่อยอย่างเด็ดขาดตามกฎและเส้นทางข้อมูล (Data Flow) โดยไม่มีการส่งข้อมูลสดผ่านแรม (RAM) ข้ามส่วนงานเพื่อความเสถียรและทนทานของระบบ

1. **ส่วนงานแรก (Data Feed):** ทำหน้าที่ดึงข้อมูลราคา Real-time บันทึกเป็นไฟล์ `.csv` ลงใน `data_base/csv/iq_option/[symbol]/[date]/`
2. **ส่วนงานที่สอง (Analysis / Orchestrator):** ทำหน้าที่อ่านไฟล์ `.csv` นำมาคำนวณประมวลผลเชิงคณิตศาสตร์และวิเคราะห์แนวโน้มตลาด เขียนบันทึกเป็นไฟล์ `.txt` (โครงสร้าง YAML 77 ฟิลด์) ลงใน `all_filelogs/logs_orchestrator/`
3. **ส่วนงานที่สาม (Execution / AI Analysis):** ดึงข้อมูลสำเร็จรูปจากไฟล์ `.txt` ไปใช้งานหรือส่งต่อให้ AI วิเคราะห์ส่งคำสั่งเทรดต่อ

---

## ภาพรวมสถาปัตยกรรมกระบวนการ (1 รอบ = 60 วินาที)

```
[ส่วนงานแรก: Data Feed]
ดึงราคาจาก IQ Option WebSocket
      ↓
บันทึกดิบลง CSV (data_base/csv/iq_option/...)
      ↓
======================= สิ้นสุดส่วนงานแรก =======================
      ↓
[ส่วนงานที่สอง: Analysis / Orchestrator]
โหลดข้อมูลจาก CSV (ลบข้อมูลเวลาซ้ำซ้อน / Duplicate Timestamp)
      ↓
ประสานเวลาแท่งเทียน (Timeframe Synchronization)
      ↓
ประมวลผลคำนวณทางเทคนิค (Indicator Store) + เครื่องมือชั้นสูง (Advanced Tools)
      ↓
ส่งวิเคราะห์ Tier-1 Engines ทั้ง 5 ชุดแบบขนาน (Parallel Processing)
      ↓
วิเคราะห์จำแนกสถานะตลาด (Market State Classifier) และจัดระดับความเสี่ยง
      ↓
บันทึกแบบจำลองข้อมูลรวม 74 ฟิลด์ (ความยาว 91 บรรทัด) ลงไฟล์ .txt
  → บันทึกที่: all_filelogs/logs_orchestrator/[symbol]/[filename].txt
  → 4 ฟิลด์สุดท้ายกำหนดค่าเป็น "รอการวิเคราะห์จาก AI"
      ↓
======================= สิ้นสุดส่วนงานที่สอง =======================
```

---

## รูปแบบโครงสร้างข้อมูลส่งออก (SSOT Payload .txt Schema)

ไฟล์วิเคราะห์ที่บันทึกสำเร็จจะมีโครงสร้างข้อมูลแบบ YAML จำนวน 74 ฟิลด์ (ความยาว 91 บรรทัด) ดังตัวอย่างด้านล่างนี้:

```yaml
ID: EURGBP0707144601
meta:
  timestamp: '2026-07-07T14:46:01.441458'
  symbol: EURGBP
  session: ASIAN
  m1_open: 0.853985
  m1_age: 60383
  m1_quality: MEDIUM
  m5_open: 0.85432
  m5_age: 2160383
  m5_quality: STALE
market_context:
  state: SIDEWAY_RANGE
  description: Price ranging between clear levels. Suitable for mean-reversion strategies.
  volatility_regime: HIGH
  news_impact: LOW
  expected_volatility_%: 0.014
timeframes:
  m1:
    last_candle: BULLISH
    ema5: 0.853972
    ema20: 0.854052
    rsi: 37.32
    stoch_k: 11.94
    stoch_d: 14.23
    macd: -6.6e-05
    macd_signal: -5.7e-05
    ohclv:
      open: 0.853985
      high: 0.85398
      low: 0.85396
      close: 0.853965
      volume: 49
  m5:
    bias: BEARISH
    ema5: 0.854027
    ema10: 0.854082
    ema20: 0.854123
    ema50: 0.854159
    bb_upper: 0.854357
    bb_lower: 0.853948
    bb_width: 0.00041
    rsi: 38.98
    stoch_k: 12.95
    stoch_d: 13.32
    macd: -3.9e-05
    macd_signal: -1.2e-05
    adx: 14.25
    atr: 0.000116
    support: 0.854045
    resistance: 0.85444
    pivot: 0.85397
    ohclv:
      open: 0.85396
      high: 0.85398
      low: 0.85396
      close: 0.85397
      volume: 60
  m15:
    bias: BEARISH
price_action:
  pattern: NONE
  last_candle_bias: BULLISH
  body_strength: WEAK
  wick_dominance: HIGH_WICK
  momentum_bias: NEUTRAL
  move_quality: CHAOTIC
  trap_alert: 'TRUE'
  sr_interaction: TESTING_PIVOT
volume:
  tick_volume: 60
  volume_momentum: LOW_MOMENTUM
  volume_vs_average: 0.075
analysis:
  trend_direction: DOWN
  trend_type: CORRECTIVE
  trend_strength_score: 60
  mtf_alignment_%: 100
  compression_quality_%: 5.63
  exhaustion_risk_%: 30
  bos_detected: false
decision_layer:
  tradeable: true
  stability_score: 100
  quality_score: 40
  risk_level: MEDIUM
  confidence_score: รอการวิเคราะห์จาก AI
  suggested_expiry_minutes: รอการวิเคราะห์จาก AI
  suggested_action: รอการวิเคราะห์จาก AI
  final_reason_th: รอการวิเคราะห์จาก AI
```

---

## กฎเหล็กควบคุมการประมวลผล (Computation Constraints)

1. **Strict Explicit Consent (ห้ามทำงานโดยไม่ได้รับคำสั่ง):** ระบบและผู้ช่วย AI จะไม่มีสิทธิ์เข้าแก้ไขโค้ดหรือดำเนินการใดๆ ที่ผู้ใช้ไม่ได้มีคำสั่งระบุเจาะจงโดยตรงเป็นลายลักษณ์อักษร
2. **ห้ามส่งผ่านข้อมูลผ่านแรมข้ามส่วนงาน:** ส่วนงานที่สองจะต้องเข้าดึงราคาผ่านการโหลดไฟล์จากโฟลเดอร์ `data_base/csv/iq_option/` เท่านั้น ห้ามเขียนโค้ดเชื่อมโยงแรมแบบ Real-time ดึงราคาโดยตรงจาก `data_feed`
3. **การลบ Duplicate Timestamp:** ต้องกำจัดแถวเวลาที่ซ้ำซ้อนใน CSV ดิบออกด้วยวิธี `df[~df.index.duplicated(keep='last')]` ก่อนนำไปป้อนเข้าคำนวณทางสถิติทุกครั้ง
4. **ความสมบูรณ์และถูกต้องของข้อมูล:** ตรวจสอบความถูกต้องและปริมาณแท่งเทียนที่ป้อน (Defensive Programming) หากข้อมูลไม่ครบถ้วนพอต่อการประมวลผล ต้องปฏิเสธการทำรายการทันที (Fail-Fast)
