# รายงานการ Audit ทั้ง 74 ฟิลด์คำนวณจริง — FINALBOT

> **วันที่ตรวจสอบ:** 2026-07-21  
> **Payload อ้างอิง:** EURGBP_OTC_20260721011305.txt  
> **ตรวจสอบโดย:** Athena Audit Team (3 Subagents)  
> **โปรเจกต์:** E:\BOT_FINALBOT\FINALBOT_Begin\data_evaluate

---

## หลักเกณฑ์การตรวจสอบ 4 ข้อ

| ข้อ | หลักเกณฑ์ |
| :---: | :--- |
| 1 | ค่าฟิลด์นั้น มีโค้ดจริง ที่คำนวณจริงในบอท (ระบุไฟล์และบรรทัด) |
| 2 | ค่าฟิลด์นั้น ใช้ข้อมูลที่เป็นจริงและอัพเดท (Live vs Hardcode/Cached) |
| 3 | ค่าฟิลด์นั้น ใช้วิธีคำนวณแบบสากล |
| 4 | ค่าฟิลด์นั้น ไม่ได้เกิดจากการคำนวณซ้ำ (SSOT) |

สัญลักษณ์: OK=ผ่าน / WARN=ข้อควรระวัง / FAIL=ไม่ผ่าน / BUG=จุดพังวิกฤต

---

## สถาปัตยกรรม SSOT Flow

```
indicator_store.py (Layer 1 - SSOT)
    basic_payload
advanced_tools_manager.py (Price Action)
    advanced_payload
TrendEngine / StrengthEngine / VolatilityEngine / StructureEngine / MTFEngine (Tier-1)
    engine results
MarketStateClassifier (Tier-2)
    final_payload
orchestrator.py -> _format_payload() -> 74 fields -> TXT/CSV/JSON
```

---

## หมวด 1: Meta Context (ฟิลด์ 1-14)

| # | ฟิลด์ | ตำแหน่งโค้ด | 1 | 2 | 3 | 4 | สรุปสถานะ |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|
| 1 | timestamp | orchestrator.py:L137 | OK | WARN | WARN | OK | WARN: ใช้เวลาเครื่อง OS ไม่ใช่เวลาแท่งเทียน M1 |
| 2 | symbol | orchestrator.py:L136 | OK | OK | OK | OK | PASS |
| 3 | session | indicator_store.py:L202 / orchestrator.py:L417 | OK | WARN | FAIL | FAIL | WARN: มีโค้ด 2 ชุดขัดแย้ง + Dead Code + ละเลย DST |
| 4 | m1_open | indicator_store.py:L214 | OK | OK | OK | OK | PASS |
| 5 | m1_age | indicator_store.py:L215 | BUG | FAIL | FAIL | OK | **BUG-03: Hardcoded 0 ตลอดเวลา** |
| 6 | m1_quality | indicator_store.py:L216 | BUG | FAIL | FAIL | OK | **BUG-03: Hardcoded STALE ตลอดเวลา** |
| 7 | m5_open | indicator_store.py:L217 | OK | OK | OK | OK | PASS |
| 8 | m5_age | indicator_store.py:L218 | BUG | FAIL | FAIL | OK | **BUG-03: Hardcoded 0 ตลอดเวลา** |
| 9 | m5_quality | indicator_store.py:L219 | BUG | FAIL | FAIL | OK | **BUG-03: Hardcoded STALE ตลอดเวลา** |
| 10 | state | market_state_classifier.py:L40 | OK | OK | OK | OK | PASS (10 Market Regimes) |
| 11 | description | market_state_classifier.py:L619 | OK | OK | OK | OK | PASS |
| 12 | volatility_regime | volatility_engine.py:L97 | OK | OK | OK | OK | PASS (ATR Percentile) |
| 13 | news_impact | check_news.py:L110 | OK | OK | OK | OK | PASS (OTC=NONE_OTC) |
| 14 | expected_volatility_% | orchestrator.py:L224 | OK | WARN | FAIL | OK | **BUG-08: ATR M5 หาร Close M1 ผิด Timeframe** |

---

## หมวด 2: Timeframe M1 Indicators & OHLCV (ฟิลด์ 15-27)

| # | ฟิลด์ | ตำแหน่งโค้ด | 1 | 2 | 3 | 4 | สรุปสถานะ |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|
| 15 | last_candle M1 | orchestrator.py:L363 | OK | OK | WARN | OK | WARN: Doji (close==open) ถูกรวบเป็น BEARISH |
| 16 | ema5 M1 | core_indicators.py:L9 | OK | OK | OK | OK | PASS |
| 17 | ema20 M1 | core_indicators.py:L9 | OK | OK | OK | WARN | WARN: คำนวณซ้ำใน mtf_engine.py:L95 |
| 18 | rsi M1 | core_indicators.py:L35 | OK | OK | OK | OK | PASS (Wilder RSI14) |
| 19 | stoch_k M1 | core_indicators.py:L61 | OK | OK | OK | OK | PASS (14,3,3) |
| 20 | stoch_d M1 | core_indicators.py:L66 | OK | OK | OK | OK | PASS (14,3,3) |
| 21 | macd M1 | core_indicators.py:L46 | OK | OK | OK | OK | PASS (EMA12-26) |
| 22 | macd_signal M1 | core_indicators.py:L50 | OK | OK | OK | OK | PASS (Signal 9) |
| 23 | open M1 OHLCV | indicator_store.py:L162 | OK | OK | OK | OK | PASS |
| 24 | high M1 OHLCV | indicator_store.py:L163 | OK | OK | OK | OK | PASS |
| 25 | low M1 OHLCV | indicator_store.py:L164 | OK | OK | OK | OK | PASS |
| 26 | close M1 OHLCV | indicator_store.py:L165 | OK | OK | OK | OK | PASS |
| 27 | volume M1 OHLCV | indicator_store.py:L141 | OK | OK | OK | WARN | WARN: OTC float 1.0 vs string NONE_OTC Type Mismatch |

---

## หมวด 3: Timeframe M5 Indicators & OHLCV (ฟิลด์ 28-50)

| # | ฟิลด์ | ตำแหน่งโค้ด | 1 | 2 | 3 | 4 | สรุปสถานะ |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|
| 28 | bias M5 | indicator_store.py:L73 | OK | OK | OK | OK | WARN: Binary ขาด Buffer Zone |
| 29 | ema5 M5 | core_indicators.py:L9 | OK | OK | OK | OK | PASS |
| 30 | ema10 M5 | core_indicators.py:L9 | OK | OK | OK | OK | PASS |
| 31 | ema20 M5 | core_indicators.py:L9 | OK | OK | OK | OK | PASS |
| 32 | ema50 M5 | core_indicators.py:L9 | OK | OK | OK | OK | PASS |
| 33 | bb_upper M5 | core_indicators.py:L14 | OK | OK | OK | OK | WARN: min_periods=1 Band แคบผิดใน 19 แท่งแรก |
| 34 | bb_lower M5 | core_indicators.py:L18 | OK | OK | OK | OK | WARN: เช่นเดียวกับ bb_upper |
| 35 | bb_width M5 | core_indicators.py:L26 | OK | OK | WARN | OK | **BUG: ValueError หากข้อมูลน้อยกว่า 100 แท่ง** |
| 36 | rsi M5 | core_indicators.py:L35 | OK | OK | OK | OK | PASS (Wilder RSI14) |
| 37 | stoch_k M5 | core_indicators.py:L61 | OK | OK | OK | OK | PASS |
| 38 | stoch_d M5 | core_indicators.py:L66 | OK | OK | OK | OK | PASS |
| 39 | macd M5 | core_indicators.py:L46 | OK | OK | OK | OK | PASS |
| 40 | macd_signal M5 | core_indicators.py:L50 | OK | OK | OK | OK | PASS |
| 41 | adx M5 | structural_metrics.py:L43 | OK | OK | OK | OK | PASS (ADX14 Wilder) |
| 42 | atr M5 | structural_metrics.py:L6 | OK | OK | OK | OK | PASS (ATR14) |
| 43 | support M5 | price_action_handler.py:L149 | BUG | OK | OK | OK | **BUG-04: KeyError Crash เมื่อ fractal<=0** |
| 44 | resistance M5 | price_action_handler.py:L149 | BUG | OK | OK | OK | **BUG-04: KeyError Crash เมื่อ fractal<=0** |
| 45 | pivot M5 | indicator_store.py:L116 | OK | WARN | FAIL | OK | WARN: ใช้แท่งปัจจุบัน ผิดหลักสากล |
| 46 | open M5 OHLCV | indicator_store.py:L128 | OK | OK | OK | OK | PASS |
| 47 | high M5 OHLCV | indicator_store.py:L129 | OK | OK | OK | OK | PASS |
| 48 | low M5 OHLCV | indicator_store.py:L130 | OK | OK | OK | OK | PASS |
| 49 | close M5 OHLCV | indicator_store.py:L131 | OK | OK | OK | OK | PASS |
| 50 | volume M5 OHLCV | structural_metrics.py:L86 | OK | OK | OK | OK | PASS (OTC=1.0) |

---

## หมวด 4: Timeframe M15 (ฟิลด์ 51)

| # | ฟิลด์ | ตำแหน่งโค้ด | 1 | 2 | 3 | 4 | สรุปสถานะ |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|
| 51 | bias M15 | indicator_store.py:L170 | OK | OK | OK | OK | PASS (Fail-Fast อายุข้อมูล) |

---

## หมวด 5: Price Action (ฟิลด์ 52-59)

| # | ฟิลด์ | ตำแหน่งโค้ด | 1 | 2 | 3 | 4 | สรุปสถานะ |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|
| 52 | pattern | candle_pattern_analyzer.py:L33 / advanced_tools_manager.py:L114 | OK | OK | OK | OK | WARN: ดึงเฉพาะ pattern แรก |
| 53 | last_candle_bias | candle_pattern_analyzer.py:L59 / advanced_tools_manager.py:L115 | OK | OK | OK | WARN | WARN: Doji ถูกรวบเป็น BEARISH |
| 54 | body_strength | price_action_handler.py:L60 / advanced_tools_manager.py:L117 | OK | OK | WARN | OK | WARN: Threshold 0.1% Hardcoded |
| 55 | wick_dominance | price_action_handler.py:L72 / advanced_tools_manager.py:L119 | OK | OK | OK | OK | **BUG-05: HIGH_WICK vs HIGH_LOWER_WICK String Mismatch** |
| 56 | momentum_bias | price_action_handler.py:L134 | OK | OK | OK | OK | WARN: Multiplier 1.5 Hardcoded |
| 57 | move_quality | price_action_handler.py:L102 / advanced_tools_manager.py:L121 | OK | OK | OK | OK | **BUG-06: CLEAN_TRENDING ถูกตัดเป็น CLEAN** |
| 58 | trap_alert | trap_detector.py:L27 / advanced_tools_manager.py:L106 | OK | OK | OK | OK | **BUG-01: BULL_TRAP vs bull Case Mismatch -> TRUE เสมอ** |
| 59 | sr_interaction | advanced_tools_manager.py:L93-L99 | OK | OK | OK | OK | **BUG-02: Indentation Bug TESTING_PIVOT Dead Code 100%** |

---

## หมวด 6: Volume (ฟิลด์ 60-62)

| # | ฟิลด์ | ตำแหน่งโค้ด | 1 | 2 | 3 | 4 | สรุปสถานะ |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|
| 60 | tick_volume | orchestrator.py:L384 | OK | OK | OK | OK | PASS (OTC=1.0) |
| 61 | volume_momentum | price_action_handler.py:L176 | OK | OK | OK | OK | PASS |
| 62 | volume_vs_average | orchestrator.py:L386 | OK | OK | OK | OK | PASS (OTC=1.0) |

---

## หมวด 7: Analysis Engine (ฟิลด์ 63-69)

| # | ฟิลด์ | ตำแหน่งโค้ด | 1 | 2 | 3 | 4 | สรุปสถานะ |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|
| 63 | trend_direction | trend_engine.py:L84 | OK | OK | OK | OK | WARN: เงื่อนไขเข้มงวด Pullback -> NONE |
| 64 | trend_type | trend_engine.py:L130 | OK | OK | OK | OK | WARN: price<5.0 แยก Forex/Crypto อาจผิด |
| 65 | trend_strength_score | trend_engine.py:L195 | OK | OK | WARN | OK | WARN: Step-wise ไม่ Continuous |
| 66 | mtf_alignment_% | mtf_engine.py:L43 | OK | OK | OK | OK | WARN: ส่งออก Integer ไม่ใช่ Decimal |
| 67 | compression_quality_% | volatility_engine.py:L78 | OK | OK | OK | OK | PASS |
| 68 | exhaustion_risk_% | strength_engine.py:L96 | OK | OK | OK | OK | PASS |
| 69 | bos_detected | structure_engine.py:L77-L82 | OK | OK | OK | OK | **BUG-07: False ตลอดเวลา Cascade จาก BUG-02** |

---

## หมวด 8: Decision Layer (ฟิลด์ 70-74)

| # | ฟิลด์ | ตำแหน่งโค้ด | 1 | 2 | 3 | 4 | สรุปสถานะ |
|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|
| 70 | tradeable | market_state_classifier.py:L107 | OK | OK | OK | OK | PASS |
| 71 | stability_score | market_state_classifier.py:L108 | OK | OK | OK | OK | PASS |
| 72 | quality_score | market_state_classifier.py:L106 | OK | OK | OK | OK | WARN: ได้รับผลจาก Bug ฟิลด์ 55 และ 57 |
| 73 | risk_level | market_state_classifier.py:L111 | OK | OK | OK | OK | WARN: ขึ้นกับ move_quality ที่ String Mismatch |
| 74 | confidence_score | orchestrator.py:L264 | OK | OK | N/A | OK | PASS: Placeholder รอ AI |

---

## Critical Bugs เรียงลำดับความสำคัญ

### Priority 1 — แก้ทันที

#### BUG-01: trap_alert Case Mismatch (Field 58)
- **File:** advanced_tools_manager.py:L106-L108
- **Symptom:** trap_alert คืนค่า TRUE ทุกครั้ง ไม่บอกชนิด Trap
- **Evidence Payload:** trap_alert: TRUE
- **Cause:** trap_detector.py คืน BULL_TRAP (ตัวใหญ่) แต่ manager เช็ค bull (ตัวเล็ก)
- **Fix:**

```python
# Before:
if trap_type == 'bear':
    trap_alert = "BEAR_TRAP"
elif trap_type == 'bull':
    trap_alert = "BULL_TRAP"
else:
    trap_alert = "TRUE"

# After:
if trap_type in ('BULL_TRAP', 'BEAR_TRAP', 'STOP_HUNT', 'REJECTION'):
    trap_alert = trap_type
else:
    trap_alert = "NONE"
```

#### BUG-02: sr_interaction Indentation Bug (Field 59)
- **File:** advanced_tools_manager.py:L93-L99
- **Symptom:** sr_interaction เป็น NONE เสมอ ยกเว้นราคาอยู่ที่ Resistance
- **Evidence Payload:** close=0.863785, pivot=0.863915, ห่าง=0.00013 < threshold=0.000338 ควรได้ TESTING_PIVOT แต่ได้ NONE
- **Cause:** Block sr_interaction ซ้อนอยู่ใน elif resistance ทำให้ TESTING_PIVOT/TESTING_SUPPORT เป็น Dead Code 100%
- **Fix:** ย้าย block sr_interaction ออกมาเป็นอิสระ ให้ทำงานทุกกรณี (AT_PIVOT / AT_SUPPORT / AT_RESISTANCE)

#### BUG-03: m1/m5 age/quality Hardcoded (Fields 5,6,8,9)
- **File:** orchestrator.py -> indicator_store.py:L212-L220
- **Symptom:** ค่า 0 และ STALE ทุกรอบ
- **Evidence Payload:** m1_age: 0, m1_quality: STALE, m5_age: 0, m5_quality: STALE
- **Cause:** orchestrator.py เรียก calculate_all โดยไม่ส่ง forming_data
- **Fix:** ส่ง forming_data จาก data_adapter.py / timeframe_sync.py เข้า calculate_all()

### Priority 2 — Crash Risk

#### BUG-04: support/resistance KeyError Crash (Fields 43,44)
- **File:** advanced_tools_manager.py:L63-L64
- **Symptom:** บอทพัง KeyError เมื่อ fractal <= 0
- **Cause:** Fallback ดึง m5_basic['support'] / m5_basic['resistance'] ที่ไม่มีคีย์นี้ใน indicator_store.py
- **Fix:** เพิ่มคีย์ support/resistance ใน indicator_store.py ใช้ S1/R1 จาก Pivot เป็น fallback

### Priority 3 — Data Accuracy

#### BUG-05: wick_dominance String Mismatch (Field 55)
- **File:** advanced_tools_manager.py:L119 / market_state_classifier.py:L184
- **Cause:** Manager คืน HIGH_WICK แต่ Classifier รอรับ HIGH_LOWER_WICK
- **Effect:** Classifier ได้ fallback 0.3 เสมอ

#### BUG-06: move_quality String Truncation (Field 57)
- **File:** advanced_tools_manager.py:L121 / structure_engine.py:L73
- **Cause:** Manager ตัด CLEAN_TRENDING เป็น CLEAN แต่ structure_engine เช็ค CLEAN_TRENDING

#### BUG-07: bos_detected Cascade (Field 69)
- **Note:** แก้ BUG-02 แล้วฟิลด์นี้จะหายเองค่ะ

### Priority 4 — Financial Math

#### BUG-08: expected_volatility_% Cross-Timeframe (Field 14)
- **File:** orchestrator.py:L219-L224
- **Cause:** ATR M5 หาร Close M1 ผิด Timeframe

#### BUG-09: pivot Forming Candle (Field 45)
- **File:** indicator_store.py:L116
- **Cause:** ใช้ df_m5.iloc[-1] (กำลังเดิน) แทน df_m5.iloc[-2] (ปิดแล้ว)

### Priority 5 — Housekeeping

#### BUG-10: session Dead Code (Field 3)
- **File:** orchestrator.py:L417-L425
- **Cause:** _derive_session() เป็น Dead Code เพราะ indicator_store คำนวณก่อนเสมอ

---

## สถิติสรุป

| หมวด | จำนวนฟิลด์ | ผ่าน 100% | มีข้อควรระวัง | บั๊กวิกฤต |
|:---|:---:|:---:|:---:|:---:|
| Meta Context (1-14) | 14 | 5 | 5 | 4 |
| M1 Indicators & OHLCV (15-27) | 13 | 10 | 2 | 1 |
| M5 Indicators & OHLCV (28-50) | 23 | 15 | 5 | 3 |
| M15 (51) | 1 | 1 | 0 | 0 |
| Price Action (52-59) | 8 | 1 | 3 | 4 |
| Volume (60-62) | 3 | 3 | 0 | 0 |
| Analysis Engine (63-69) | 7 | 3 | 3 | 1 |
| Decision Layer (70-74) | 5 | 3 | 2 | 0 |
| **รวม** | **74** | **41 (55.4%)** | **20 (27.0%)** | **13 (17.6%)** |

---

## แผนแก้ไขเรียงตาม Priority

| ลำดับ | บั๊ก | ไฟล์หลัก | ความซับซ้อน | ผลกระทบ |
|:---:|:---|:---|:---:|:---:|
| 1 | trap_alert string mismatch | advanced_tools_manager.py:L106 | ต่ำ | สูง |
| 2 | sr_interaction indentation | advanced_tools_manager.py:L93 | กลาง | สูง |
| 3 | m1/m5 age/quality hardcode | orchestrator.py -> indicator_store.py | สูง | สูง |
| 4 | support/resistance KeyError | advanced_tools_manager.py:L63 | ต่ำ | กลาง |
| 5 | wick_dominance string | advanced_tools_manager.py:L119 | ต่ำ | กลาง |
| 6 | move_quality truncation | advanced_tools_manager.py:L121 | ต่ำ | กลาง |
| 7 | bos_detected cascade | แก้ BUG-02 แล้วหายเอง | - | กลาง |
| 8 | expected_volatility_% cross-TF | orchestrator.py:L224 | ต่ำ | กลาง |
| 9 | pivot forming candle | indicator_store.py:L116 | ต่ำ | ต่ำ |
| 10 | session dead code | orchestrator.py:L417 | ต่ำ | ต่ำ |

---

*รายงานจัดทำโดย Athena Audit Team — FINALBOT Project*  
*วันที่: 2026-07-21 | อ้างอิง: EURGBP_OTC_20260721011305.txt*
