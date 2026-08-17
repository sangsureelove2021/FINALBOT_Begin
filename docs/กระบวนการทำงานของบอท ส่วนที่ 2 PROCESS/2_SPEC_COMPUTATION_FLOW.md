# SPEC: COMPUTATION FLOW — สถาปัตยกรรมประมวลผลข้อมูลผ่าน RAM 100%

## 🚀 หลักการประมวลผล (RAM-First Architecture)
ระบบใช้สถาปัตยกรรม **RAM 100% In-Memory Data Passing** เพื่อให้การประมวลผล 4 สินทรัพย์เสร็จสิ้นภายในเวลาเพียง < 0.5 วินาที:

1. **ส่วนงานแรก (Data Feed / DataAdapter):** ดึงข้อมูลราคา Real-time ผ่าน WebSocket/REST เก็บไว้ใน RAM (`RAMCacheStore` / `_completed_candles`) และบันทึกไฟล์ CSV ลงดิสก์แบบ Asynchronous Background
2. **ส่วนงานที่สอง (Analysis / Orchestrator):** รับ `candles_dict` (M1, M5, M15) จาก RAM โดยตรงผ่าน `runner.py` ที่วินาที `:01.500` เข้าประมวลผลผ่าน:
   - `IndicatorStore` (SSOT Raw Indicators)
   - `AdvancedToolsManager` (10 เครื่องมือวิเคราะห์พฤติกรรมราคาและมิติทางจิตวิทยา)
   - `Tier 1 Parallel Engines` (Trend, Strength, Volatility, Structure, MTF)
   - `MarketStateClassifier` (จัดกลุ่มสภาวะตลาด 10 รูปแบบ)
   - `Tier 3-5 Supplementary Engines` (MarketStructure, Orderflow, Noise, Liquidity)
   - `Tier 6 Synthesis Engines` (ContextSynthesizer, ProbabilityEstimator, ExplainabilityEngine, SignalThrottle)
3. **ส่งออกผลลัพธ์ (Prompt Payload):** บันทึกไฟล์ข้อมูลมาตรฐาน **100 บรรทัด (.txt)** ไปยัง `data_base/orchestrator/<SYMBOL>/<PROMPT_ID>.txt` เพื่อส่งต่อให้ AI ในส่วนที่ 3 นำไปตัดสินใจ

---

## ⚡ แผนผังกระบวนการทำงาน (1 รอบ = 60 วินาที)

```text
[ส่วนงานที่ 1: Data Feed & RAM Cache]
ดึงราคาจาก IQ Option WebSocket Stream
      ↓
อัปเดตและเก็บแท่งเทียนสมบูรณ์ใน RAM (_completed_candles 250 แท่ง)
      ↓
======================= สิ้นสุดส่วนงานที่ 1 =======================
      ↓
[ส่วนงานที่ 2: Data Evaluate / Orchestration (RAM 100%)]
runner.py ดึง candles_dict จาก RAM ส่งตรงให้ orchestrator.process_cycle() ที่วินาที :01.500
      ↓
1. คำนวณอินดิเคเตอร์พื้นฐาน (IndicatorStore) แบบรวมศูนย์ (SSOT)
      ↓
2. วิเคราะห์พฤติกรรมตลาด 7 มิติผ่าน 10 Advanced Tools
      ↓
3. รัน Tier 1 Core Engines ทั้ง 5 ชุดแบบ Parallel (ThreadPoolExecutor)
      ↓
4. จำแนก 10 สภาวะตลาด (MarketStateClassifier)
      ↓
5. รัน Tier 3-5 Supplementary Engines แบบ Parallel
      ↓
6. เชื่อมโยงข้อมูลจริงเข้าสู่ Tier 6 Context Synthesizer & Probability Estimator
      ↓
7. บันทึกไฟล์ Prompt Payload มาตรฐาน 100 บรรทัด (.txt)
   → บันทึกที่: data_base/orchestrator/<SYMBOL>/<PROMPT_ID>.txt
   → หมวด decision_layer: กำหนดค่าเป็น "รอการวิเคราะห์จาก AI"
      ↓
======================= สิ้นสุดส่วนงานที่ 2 =======================
```

---

## 📄 โครงสร้างไฟล์ Prompt Payload มาตรฐาน 100 บรรทัด (Standard Format)

```yaml
ID: GBPUSDOTC0817145201
meta:
  timestamp: '2026-08-17T14:52:01.852518'
  symbol: GBPUSD-OTC
  session: LONDON_OPEN
  m1_open: 1.335315
  m1_age: 60850
  m1_quality: FRESH
  m5_open: 1.336115
  m5_age: 420850
  m5_quality: FRESH
market_context:
  state: DISTRIBUTION
  description: Smart money distribution. Bearish bias, look for breakdown.
  volatility_regime: HIGH
  news_impact: NONE_OTC
  expected_volatility_%: 0.088
timeframes:
  m1:
    m1_last_candle: BULLISH
    m1_ema5: 1.335428
    m1_ema20: 1.335819
    m1_rsi: 44.29
    m1_stoch_k: 21.24
    m1_stoch_d: 17.07
    m1_macd: -0.000236
    m1_macd_signal: -0.000155
    ohlcv:
      open: 1.335315
      high: 1.335525
      low: 1.335185
      close: 1.335465
      volume: NONE_OTC
  m5:
    m5_bias: BEARISH
    m5_ema5: 1.33566
    m5_ema10: 1.335983
    m5_ema20: 1.336204
    m5_ema50: 1.335529
    m5_bb_upper: 1.339216
    m5_bb_lower: 1.334383
    m5_bb_width: 0.004833
    m5_rsi: 42.85
    m5_stoch_k: 11.41
    m5_stoch_d: 17.28
    m5_macd: -0.000092
    m5_macd_signal: 0.000159
    m5_adx: 15.05
    m5_atr: 0.001177
    m5_support: 1.334402
    m5_resistance: 1.335862
    m5_pivot: 1.335358
    ohlcv:
      open: 1.336115
      high: 1.336315
      low: 1.334855
      close: 1.334905
      volume: NONE_OTC
  m15:
    m15_bias: BULLISH
price_action:
  m5_pa_pattern: BEARISH_ENGULFING
  m5_pa_last_candle_bias: BEARISH
  m5_pa_body_strength: WEAK
  m5_pa_wick_dominance: LOW_WICK
  m5_pa_momentum_bias: NEUTRAL
  m5_pa_move_quality: CHAOTIC
  m5_pa_trap_alert: NONE
  m5_pa_sr_interaction: TESTING_PIVOT
  m5_pa_divergence_alert: BEARISH
  m5_pa_divergence_strength: 50
  m5_pa_market_behavior: NEUTRAL
  m5_pa_hesitation_score: 20
  m5_pa_path_efficiency: POOR
volume:
  m5_tick_volume: 1.0
  m5_volume_momentum: NO_VOLUME_DATA
  m5_volume_vs_average: 1.0
analysis:
  m5_trend_direction: NONE
  m5_trend_type: CHOPPY
  m5_trend_strength_score: 20
  mtf_alignment_%: 33
  m5_compression_quality_%: 40.47
  m5_exhaustion_risk_%: 30
  m5_bos_detected: false
  mtf_conflict_score: 0
  m5_trend_continuation_%: 82
  m5_transition_risk: MEDIUM
  m5_persistence_score: 63
decision_layer:
  dl_tradeable: true
  dl_stability_score: 33
  dl_quality_score: 33
  dl_risk_level: MEDIUM
  ai_confidence_score: รอการวิเคราะห์จาก AI
  ai_suggested_expiry_minutes: รอการวิเคราะห์จาก AI
  ai_suggested_action: รอการวิเคราะห์จาก AI
  ai_final_reason_th: รอการวิเคราะห์จาก AI
```

---

## 🛡️ กฎเหล็กควบคุมการประมวลผล (Computation Constraints)

1. **Single Source of Truth (SSOT):** ไม่มีการคำนวณอินดิเคเตอร์ซ้ำซ้อน ทุกโมดูลดึงค่าจาก Payload หลัก
2. **Fail-Fast Policy:** หากข้อมูลไม่ครบถ้วน (น้อยกว่า 50 แท่ง) หรือคำนวณไม่ได้ ระบบจะหยุดทำงานทันที ไม่มีการหมกเม็ด Error
3. **Immutability of Data:** ห้ามดัดแปลงตัวแปรต้นฉบับ ส่งผลลัพธ์ผ่านตัวแปรใหม่เสมอ
4. **Analysis Only:** ส่วนงานที่ 2 สิ้นสุดเมื่อสร้างไฟล์ Prompt 100 บรรทัดสำเร็จ โดยไม่มีการส่งคำสั่งเทรดเอง
