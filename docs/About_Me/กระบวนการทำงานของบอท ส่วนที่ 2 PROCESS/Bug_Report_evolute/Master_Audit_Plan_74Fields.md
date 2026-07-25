# FINALBOT — Master Audit Plan: 74 Fields Independent Verification

> **วันที่จัดทำ:** 2026-07-23  
> **จัดทำโดย:** Athena (Audit Coordinator)  
> **วัตถุประสงค์:** ไฟล์นี้เป็น "คำสั่งมาตรฐาน" สำหรับ AI ทุกตัวที่จะรับงาน Audit 74 ฟิลด์ เพื่อให้ผลลัพธ์เปรียบเทียบกันได้อย่างยุติธรรม

---

## ส่วนที่ 1 — บริบทและที่มา

ระบบ FINALBOT มีการส่ง payload ข้อมูล **91 บรรทัด** ต่อรอบการวิเคราะห์ แบ่งเป็น:
- **74 ฟิลด์คำนวณจริง** (ที่ต้องตรวจในแผนนี้)
- **17 ฟิลด์ที่เหลือ** (Header, Placeholder รอ AI, Metadata ระบบ)

ก่อนหน้านี้มี AI จำนวน 3 ตัวตรวจสอบแล้ว แต่ผลลัพธ์ขัดแย้งกัน:
- **Ai2** พบ 4 บั๊กวิกฤต (ยืนยันด้วย Payload จริง)
- **Ai3** พบ 4 ฟิลด์ Missing (นอก 74 ฟิลด์)
- **Ai4** รายงาน 100% PASS (ตรวจแบบ High-Level)

**ผลสรุป Consensus:** 66 ฟิลด์ที่ทั้ง 3 AI เห็นตรงกันว่า OK / 8 ฟิลด์ที่มีข้อโต้แย้ง

---

## ส่วนที่ 2 — หลักเกณฑ์การตรวจสอบ 4 ข้อ (บังคับใช้ทุกฟิลด์)

สำหรับทุกฟิลด์ AI ต้องตอบคำถาม 4 ข้อต่อไปนี้ด้วยการอ่านซอร์สโค้ดจริง:

| ข้อ | คำถาม | วิธีตรวจ |
|:---:|:---|:---|
| **1** | **มีโค้ดจริงคำนวณจริงในบอทหรือไม่?** | ระบุชื่อไฟล์ + บรรทัดที่คำนวณค่านี้ |
| **2** | **ใช้ข้อมูลที่เป็นจริงและอัพเดทหรือไม่?** | ดูว่ามีการดึง candle/indicator ล่าสุด หรือใช้ hardcode/default/None |
| **3** | **ใช้วิธีคำนวณแบบสากลหรือไม่?** | เช่น RSI ต้องใช้ Wilder's Smoothing, Pivot ต้องใช้แท่งปิดแล้ว |
| **4** | **ไม่ได้เกิดจากการคำนวณซ้ำหรือไม่?** | ตรวจว่ามีการ recalculate indicator เดิมซ้ำใน Engine อื่นนอกจาก indicator_store.py |

**ผลลัพธ์ต่อฟิลด์:** ให้ตอบเป็น OK / WARN / BUG พร้อมเหตุผลสั้น ๆ
- **OK** = ผ่านทั้ง 4 ข้อ
- **WARN** = ผ่านแต่มีข้อควรระวัง (ไม่กระทบผล output จริง)
- **BUG** = ไม่ผ่านอย่างน้อย 1 ข้อ และมีผลต่อค่าใน payload จริง

---

## ส่วนที่ 3 — คำสั่งสำหรับ AI ที่รับงาน

```
COMMAND TO AI:
คุณคือผู้ตรวจสอบอิสระ (Independent Auditor)

งานของคุณคือตรวจสอบ 74 ฟิลด์ข้างล่างนี้ โดยปฏิบัติตามกฎต่อไปนี้อย่างเคร่งครัด:

1. อ่านซอร์สโค้ดจริงทีละบรรทัด ห้ามอ่านแบบ High-Level
2. ตอบหลักเกณฑ์ 4 ข้อสำหรับทุกฟิลด์
3. ถ้าพบค่า hardcode หรือ None default ให้ระบุว่าเป็น BUG ทันที
4. ถ้า string ที่ฟังก์ชันส่งออกไม่ตรงกับ string ที่ฟังก์ชันปลายทางรับ ให้ระบุเป็น BUG ทันที
5. ถ้าโค้ดซ้อน indent ผิดทำให้ logic ไม่ทำงาน ให้ระบุเป็น BUG ทันที
6. ถ้า indicator ถูกคำนวณจาก Timeframe ผิด (เช่น ATR M5 ใช้กับ Close M1) ให้ระบุเป็น BUG ทันที
7. ห้ามรายงาน OK โดยไม่ได้อ่านโค้ดจริง
8. ระบุชื่อไฟล์และเลขบรรทัดสำหรับทุก BUG ที่พบ

Path โปรเจกต์: E:\BOT_FINALBOT\FINALBOT_Begin\data_evaluate
```

---

## ส่วนที่ 4 — Checklist 74 ฟิลด์

### สัญลักษณ์ Consensus (จาก 3 AI ก่อนหน้า)
- ✅ CONSENSUS OK = ทั้ง 3 AI เห็นตรงกันว่าผ่าน
- ⚠️ DISPUTED = มี AI อย่างน้อย 1 ตัวพบปัญหา (ต้องตรวจใหม่)

---

### หมวด A: Meta Context (ฟิลด์ 1-14)

| # | ฟิลด์ | หมวด | Consensus | ไฟล์โค้ดหลักที่ต้องอ่าน | ผล AI ใหม่ | หมายเหตุ |
|:---:|:---|:---|:---:|:---|:---:|:---|
| 1 | timestamp | meta | ✅ | orchestrator.py:L137 | | |
| 2 | symbol | meta | ✅ | orchestrator.py:L136 | | |
| 3 | session | meta | ✅ | indicator_store.py:L202-L210 | | ตรวจว่า _derive_session() ใน orchestrator ซ้ำซ้อนหรือไม่ |
| 4 | m1_open | meta | ✅ | indicator_store.py:L214 | | |
| 5 | m1_age | meta | ⚠️ DISPUTED | indicator_store.py:L215 + orchestrator.py (call site) | | **ตรวจว่า orchestrator ส่ง forming_data จริงหรือ None** |
| 6 | m1_quality | meta | ⚠️ DISPUTED | indicator_store.py:L216 + orchestrator.py (call site) | | **ตรวจว่า orchestrator ส่ง forming_data จริงหรือ None** |
| 7 | m5_open | meta | ✅ | indicator_store.py:L217 | | |
| 8 | m5_age | meta | ⚠️ DISPUTED | indicator_store.py:L218 + orchestrator.py (call site) | | **ตรวจว่า orchestrator ส่ง forming_data จริงหรือ None** |
| 9 | m5_quality | meta | ⚠️ DISPUTED | indicator_store.py:L219 + orchestrator.py (call site) | | **ตรวจว่า orchestrator ส่ง forming_data จริงหรือ None** |
| 10 | state | market_context | ✅ | market_state_classifier.py:L40 | | |
| 11 | description | market_context | ✅ | market_state_classifier.py:L619 | | |
| 12 | volatility_regime | market_context | ✅ | volatility_engine.py:L97 | | |
| 13 | news_impact | market_context | ✅ | check_news.py:L110 | | |
| 14 | expected_volatility_% | market_context | ✅ | orchestrator.py:L224 | | **ตรวจว่า ATR และ Close มาจาก Timeframe เดียวกัน** |

---

### หมวด B: Timeframe M1 — Indicators (ฟิลด์ 15-27)

| # | ฟิลด์ | หมวด | Consensus | ไฟล์โค้ดหลักที่ต้องอ่าน | ผล AI ใหม่ | หมายเหตุ |
|:---:|:---|:---|:---:|:---|:---:|:---|
| 15 | last_candle | timeframes.m1 | ✅ | orchestrator.py:L363 | | ตรวจ Doji edge case |
| 16 | ema5 | timeframes.m1 | ✅ | core_indicators.py:L9 | | |
| 17 | ema20 | timeframes.m1 | ✅ | core_indicators.py:L9 | | ตรวจ duplicate calc ใน mtf_engine.py |
| 18 | rsi | timeframes.m1 | ✅ | core_indicators.py:L35 | | Wilder's Smoothing |
| 19 | stoch_k | timeframes.m1 | ✅ | core_indicators.py:L61 | | |
| 20 | stoch_d | timeframes.m1 | ✅ | core_indicators.py:L66 | | |
| 21 | macd | timeframes.m1 | ✅ | core_indicators.py:L46 | | EMA12-26 |
| 22 | macd_signal | timeframes.m1 | ✅ | core_indicators.py:L50 | | Signal 9 |
| 23 | open | timeframes.m1.ohlcv | ✅ | indicator_store.py:L162 | | |
| 24 | high | timeframes.m1.ohlcv | ✅ | indicator_store.py:L163 | | |
| 25 | low | timeframes.m1.ohlcv | ✅ | indicator_store.py:L164 | | |
| 26 | close | timeframes.m1.ohlcv | ✅ | indicator_store.py:L165 | | |
| 27 | volume | timeframes.m1.ohlcv | ✅ | indicator_store.py:L141 | | OTC = 1.0 / NONE_OTC type check |

---

### หมวด C: Timeframe M5 — Indicators (ฟิลด์ 28-50)

| # | ฟิลด์ | หมวด | Consensus | ไฟล์โค้ดหลักที่ต้องอ่าน | ผล AI ใหม่ | หมายเหตุ |
|:---:|:---|:---|:---:|:---|:---:|:---|
| 28 | bias | timeframes.m5 | ✅ | indicator_store.py:L73 | | |
| 29 | ema5 | timeframes.m5 | ✅ | core_indicators.py:L9 | | |
| 30 | ema10 | timeframes.m5 | ✅ | core_indicators.py:L9 | | |
| 31 | ema20 | timeframes.m5 | ✅ | core_indicators.py:L9 | | |
| 32 | ema50 | timeframes.m5 | ✅ | core_indicators.py:L9 | | |
| 33 | bb_upper | timeframes.m5 | ✅ | core_indicators.py:L14 | | min_periods |
| 34 | bb_lower | timeframes.m5 | ✅ | core_indicators.py:L18 | | min_periods |
| 35 | bb_width | timeframes.m5 | ✅ | core_indicators.py:L26 | | ตรวจ ValueError หากข้อมูลน้อยกว่า 100 แท่ง |
| 36 | rsi | timeframes.m5 | ✅ | core_indicators.py:L35 | | Wilder's Smoothing |
| 37 | stoch_k | timeframes.m5 | ✅ | core_indicators.py:L61 | | |
| 38 | stoch_d | timeframes.m5 | ✅ | core_indicators.py:L66 | | |
| 39 | macd | timeframes.m5 | ✅ | core_indicators.py:L46 | | |
| 40 | macd_signal | timeframes.m5 | ✅ | core_indicators.py:L50 | | |
| 41 | adx | timeframes.m5 | ✅ | structural_metrics.py:L43 | | ADX14 Wilder's |
| 42 | atr | timeframes.m5 | ✅ | structural_metrics.py:L6 | | ATR14 |
| 43 | support | timeframes.m5 | ⚠️ DISPUTED | price_action_handler.py:L149 + advanced_tools_manager.py:L63 | | **ตรวจ fallback: m5_basic['support'] มีคีย์นี้จริงใน store หรือไม่** |
| 44 | resistance | timeframes.m5 | ⚠️ DISPUTED | price_action_handler.py:L149 + advanced_tools_manager.py:L63 | | **ตรวจ fallback: m5_basic['resistance'] มีคีย์นี้จริงใน store หรือไม่** |
| 45 | pivot | timeframes.m5 | ✅ | indicator_store.py:L116 | | **ตรวจว่าใช้ iloc[-1] (กำลังเดิน) หรือ iloc[-2] (ปิดแล้ว)** |
| 46 | open | timeframes.m5.ohlcv | ✅ | indicator_store.py:L128 | | |
| 47 | high | timeframes.m5.ohlcv | ✅ | indicator_store.py:L129 | | |
| 48 | low | timeframes.m5.ohlcv | ✅ | indicator_store.py:L130 | | |
| 49 | close | timeframes.m5.ohlcv | ✅ | indicator_store.py:L131 | | |
| 50 | volume | timeframes.m5.ohlcv | ✅ | structural_metrics.py:L86 | | |

---

### หมวด D: Timeframe M15 (ฟิลด์ 51)

| # | ฟิลด์ | หมวด | Consensus | ไฟล์โค้ดหลักที่ต้องอ่าน | ผล AI ใหม่ | หมายเหตุ |
|:---:|:---|:---|:---:|:---|:---:|:---|
| 51 | bias | timeframes.m15 | ✅ | indicator_store.py:L170 | | Fail-Fast age check |

---

### หมวด E: Price Action (ฟิลด์ 52-59)

| # | ฟิลด์ | หมวด | Consensus | ไฟล์โค้ดหลักที่ต้องอ่าน | ผล AI ใหม่ | หมายเหตุ |
|:---:|:---|:---|:---:|:---|:---:|:---|
| 52 | pattern | price_action | ✅ | candle_pattern_analyzer.py:L33 / advanced_tools_manager.py:L114 | | ตรวจ multi-pattern case |
| 53 | last_candle_bias | price_action | ✅ | candle_pattern_analyzer.py:L59 / advanced_tools_manager.py:L115 | | Doji edge case |
| 54 | body_strength | price_action | ✅ | price_action_handler.py:L60 / advanced_tools_manager.py:L117 | | Threshold hardcoded |
| 55 | wick_dominance | price_action | ✅ | price_action_handler.py:L72 / advanced_tools_manager.py:L119 / market_state_classifier.py:L184 | | **ตรวจ string: ฝั่งส่งออก vs ฝั่งรับ ต้องตรงกัน** |
| 56 | momentum_bias | price_action | ✅ | price_action_handler.py:L134 | | |
| 57 | move_quality | price_action | ✅ | price_action_handler.py:L102 / advanced_tools_manager.py:L121 / structure_engine.py:L73 | | **ตรวจ string: ฝั่งส่งออก vs ฝั่งรับ ต้องตรงกัน** |
| 58 | trap_alert | price_action | ⚠️ DISPUTED | trap_detector.py:L27 / advanced_tools_manager.py:L106-L108 | | **ตรวจ case: trap_detector ส่ง BULL_TRAP แต่ manager เช็ค 'bull' (ตัวเล็ก) หรือไม่** |
| 59 | sr_interaction | price_action | ⚠️ DISPUTED | advanced_tools_manager.py:L93-L99 | | **ตรวจ indent: บล็อก sr_interaction อยู่นอก/ใน elif resistance?** |

---

### หมวด F: Volume (ฟิลด์ 60-62)

| # | ฟิลด์ | หมวด | Consensus | ไฟล์โค้ดหลักที่ต้องอ่าน | ผล AI ใหม่ | หมายเหตุ |
|:---:|:---|:---|:---:|:---|:---:|:---|
| 60 | tick_volume | volume | ✅ | orchestrator.py:L384 | | |
| 61 | volume_momentum | volume | ✅ | price_action_handler.py:L176 | | |
| 62 | volume_vs_average | volume | ✅ | orchestrator.py:L386 | | |

---

### หมวด G: Analysis Engine (ฟิลด์ 63-69)

| # | ฟิลด์ | หมวด | Consensus | ไฟล์โค้ดหลักที่ต้องอ่าน | ผล AI ใหม่ | หมายเหตุ |
|:---:|:---|:---|:---:|:---|:---:|:---|
| 63 | trend_direction | analysis | ✅ | trend_engine.py:L84 | | |
| 64 | trend_type | analysis | ✅ | trend_engine.py:L130 | | ตรวจ price<5.0 logic |
| 65 | trend_strength_score | analysis | ✅ | trend_engine.py:L195 | | Step-wise vs Continuous |
| 66 | mtf_alignment_% | analysis | ✅ | mtf_engine.py:L43 | | |
| 67 | compression_quality_% | analysis | ✅ | volatility_engine.py:L78 | | |
| 68 | exhaustion_risk_% | analysis | ✅ | strength_engine.py:L96 | | |
| 69 | bos_detected | analysis | ✅ | structure_engine.py:L77-L82 | | **ตรวจว่า logic พึ่งค่า sr_interaction หรือไม่** |

---

### หมวด H: Decision Layer (ฟิลด์ 70-74)

| # | ฟิลด์ | หมวด | Consensus | ไฟล์โค้ดหลักที่ต้องอ่าน | ผล AI ใหม่ | หมายเหตุ |
|:---:|:---|:---|:---:|:---|:---:|:---|
| 70 | tradeable | decision_layer | ✅ | market_state_classifier.py:L107 | | |
| 71 | stability_score | decision_layer | ✅ | market_state_classifier.py:L108 | | |
| 72 | quality_score | decision_layer | ✅ | market_state_classifier.py:L106 | | ตรวจผลกระทบจาก wick_dominance / move_quality |
| 73 | risk_level | decision_layer | ✅ | market_state_classifier.py:L111 | | |
| 74 | confidence_score | decision_layer | ✅ | orchestrator.py:L264 | | Placeholder by Design — รอ AI |

---

## ส่วนที่ 5 — สรุป Consensus จาก 3 AI ก่อนหน้า

| สถานะ | จำนวนฟิลด์ | รายการฟิลด์ |
|:---|:---:|:---|
| ✅ **Consensus OK** (ทั้ง 3 AI เห็นตรงกัน) | **66** | ฟิลด์ 1-4, 7, 10-16, 16-42, 45-57, 60-74 |
| ⚠️ **Disputed** (มี AI อย่างน้อย 1 ตัวพบปัญหา) | **8** | ฟิลด์ 5, 6, 8, 9, 43, 44, 58, 59 |
| **รวม** | **74** | |

### 8 ฟิลด์ Disputed — รายละเอียด

| # | ฟิลด์ | ปัญหาที่พบ | ตรวจซ้ำ? |
|:---:|:---|:---|:---:|
| 5 | m1_age | orchestrator ไม่ส่ง forming_data → ค่าเป็น 0 ตลอด | YES |
| 6 | m1_quality | orchestrator ไม่ส่ง forming_data → ค่าเป็น STALE ตลอด | YES |
| 8 | m5_age | orchestrator ไม่ส่ง forming_data → ค่าเป็น 0 ตลอด | YES |
| 9 | m5_quality | orchestrator ไม่ส่ง forming_data → ค่าเป็น STALE ตลอด | YES |
| 43 | support M5 | Fallback ดึง m5_basic['support'] ที่อาจไม่มีคีย์ใน store → KeyError | YES |
| 44 | resistance M5 | Fallback ดึง m5_basic['resistance'] ที่อาจไม่มีคีย์ใน store → KeyError | YES |
| 58 | trap_alert | trap_detector คืน 'BULL_TRAP' แต่ manager เช็ค 'bull' → ได้ TRUE เสมอ | YES |
| 59 | sr_interaction | Block sr_interaction ซ้อนอยู่ใน elif resistance → TESTING_PIVOT Dead Code | YES |

---

## ส่วนที่ 6 — Template ผลลัพธ์ที่ต้องส่งกลับ

AI ที่รับงานต้องส่งผลในรูปแบบนี้:

```markdown
## Audit Result — [ชื่อ AI] — [วันที่]

| # | ฟิลด์ | ข้อ1 | ข้อ2 | ข้อ3 | ข้อ4 | สรุป | หลักฐาน (ไฟล์:บรรทัด) |
|:---:|:---|:---:|:---:|:---:|:---:|:---|:---|
| 1 | timestamp | OK | OK | OK | OK | OK | orchestrator.py:L137 |
...
| 5 | m1_age | BUG | FAIL | - | - | BUG | orchestrator.py:L??? — ไม่ส่ง forming_data |
...

## สรุป
- PASS: X/74 ฟิลด์
- WARN: X/74 ฟิลด์  
- BUG: X/74 ฟิลด์
```

---

## ส่วนที่ 7 — Payload อ้างอิงสำหรับยืนยันตัวเลข

Log ID: `EURGBPOTC0721011305`  
File: `E:\BOT_FINALBOT\FINALBOT_Begin\docs\Basic\EURGBP_OTC_20260721011305.txt`

ตัวเลขสำคัญสำหรับยืนยัน BUG:
- close M1 = 0.863785, pivot M5 = 0.863915
- ห่าง = 0.00013, threshold = ATR×0.5 = 0.000338
- **ถ้า sr_interaction ไม่ใช่ TESTING_PIVOT แสดงว่า BUG 59 ยังอยู่**
- **ถ้า trap_alert = 'TRUE' แทนที่จะเป็นชนิด trap แสดงว่า BUG 58 ยังอยู่**
- **ถ้า m1_age = 0 และ m1_quality = STALE ทุกรอบ แสดงว่า BUG 5,6,8,9 ยังอยู่**

---

*จัดทำโดย Athena — FINALBOT Audit Coordinator*  
*2026-07-23 | อ้างอิงรายงาน: Ai2, Ai3, Ai4 ใน Bug_Report_evolute/*
