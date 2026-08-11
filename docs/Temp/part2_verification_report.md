# รายงานตรวจสอบการทำงานจริง — data_evaluate (ส่วนงานที่ 2)

**วันที่ตรวจสอบ:** 2026-08-09
**ผู้ตรวจสอบ:** Joy (Claude) — อ่านซอร์สโค้ดจริงทุกไฟล์ที่อยู่ใน live execution path
**ไฟล์ตัวอย่างที่ใช้ตรวจสอบ:** `data_base/orchestrator/EURUSD-OTC/EURUSDOTC0809180601.txt`
**ขอบเขต:** ตรวจเฉพาะ `data_evaluate/` (ส่วนงานที่ 2) — ไม่แตะ/ไม่แก้โค้ด ตรวจอย่างเดียว

---

## 1. บทสรุปสำหรับ Boss

**คำตอบตรงประเด็น: บอทคำนวณจริง ไม่มีข้อมูลเท็จ (fake/hardcoded) ในค่าตัวเลขที่แสดง**

ทุกฟิลด์ในไฟล์ `.txt` ที่ AI จะอ่าน (ยกเว้น 4 ฟิลด์ decision_layer ที่ Boss ระบุไว้ว่ารอ AI ใส่เอง) สืบย้อนกลับไปหาสูตรคำนวณจริงได้ทั้งหมด — ไม่มีจุดไหนใน path ที่บอทรันจริงที่เป็นค่า mock/placeholder/สุ่ม

อย่างไรก็ตาม พบ **3 จุดที่เป็นจุดอ่อนเชิงตรรกะ (logic gap)** ที่ควรทราบไว้ — ไม่ใช่ข้อมูลเท็จ แต่เป็นการออกแบบที่อาจทำให้ตีความผิดได้ และพบว่า **มีไฟล์โค้ดจำนวนมากใน `data_evaluate/` ที่ไม่ได้ถูกเรียกใช้งานจริงเลย** (โค้ดที่ตกค้างมาจากบอทตัวอื่นที่ Boss คัดลอกมา) รายละเอียดในหัวข้อ 4 และ 5

---

## 2. Data Flow ที่ยืนยันแล้วว่าทำงานจริง

```
runner.py
  └─> orchestrator.process_cycle(symbol)
        └─> _load_csv_to_ram(symbol)              # อ่าน CSV จริงจาก data_base/csv/iq_option/
        └─> store.calculate_all()                  # indicator_store.py — Layer 1: คำนวณ EMA/RSI/MACD/ATR/ADX ฯลฯ จาก OHLCV จริง
        └─> advanced_tools.analyze_all()            # 9 analyzer ทำงานกับ M5 DataFrame จริง
        └─> 5 Tier-1 engines (parallel)              # trend/strength/volatility/structure/mtf
        └─> market_state_classifier.analyze()        # จำแนก market state จาก engine outputs จริง
        └─> 9 supplementary engines                  # liquidity/noise/trap/probability/explainability/ฯลฯ
        └─> _format_payload() -> _save_txt_payload() # เขียนไฟล์ .txt
```

ทุก engine อ่าน `candles_dict['M1'/'M5'/'M15']` ซึ่งเป็น DataFrame ที่โหลดจาก CSV จริงของ Part 1 — ไม่มีจุดไหน inject ข้อมูลปลอมหรือ mock แทน

---

## 3. ตารางยืนยันที่มาของข้อมูล (Field-by-Field)

### meta (9 ฟิลด์) — จาก `indicator_store.py`
| ฟิลด์ | สูตร/แหล่งที่มา |
|---|---|
| timestamp, symbol | ส่งต่อจาก orchestrator |
| session | คำนวณจาก UTC hour ปัจจุบัน (ASIAN/LONDON/NEW YORK) |
| m1_open/age/quality, m5_open/age/quality | จาก timestamp แท่งเทียนล่าสุดจริง เทียบเวลาปัจจุบัน (age = now - candle_timestamp) |

### market_context (5 ฟิลด์)
| ฟิลด์ | แหล่งที่มา |
|---|---|
| state, description | `market_state_classifier.py` — ระบบให้คะแนนถ่วงน้ำหนัก 10 สภาวะตลาด (ADX, trend_strength, alignment, noise ฯลฯ) |
| volatility_regime | `volatility_engine.py` — จัดกลุ่มจาก **atr_percentile** (อันดับเปอร์เซ็นไทล์ของ ATR ปัจจุบันเทียบประวัติ) |
| news_impact | `economic_news_calendar.py` — ดึงข่าวจริงจาก Forex Factory (web scraping) หรือ `NONE_OTC` ถ้าเป็นคู่ OTC |
| expected_volatility_% | orchestrator.py: `(atr14 / close_price) * 100` — ATR เป็น % ของราคาจริง |

### timeframes.m1 / m5 / m15 (39 ฟิลด์) — จาก `core_indicators.py` + `structural_metrics.py`
EMA (`ewm().mean()`), RSI (Wilder's smoothing), MACD (12/26/9 EMA), Stochastic (14,3,3), ATR (Wilder's), ADX/DI (Wilder's), Bollinger Bands (SMA±2σ), Pivot/S1/R1 (สูตร floor pivot มาตรฐานจากแท่งที่ปิดสมบูรณ์) — **ทุกสูตรเป็นสูตรมาตรฐานอุตสาหกรรม ไม่มีการ hardcode ค่า**

### price_action (8 ฟิลด์) — จาก `advanced_tools_manager.py` + `price_action_handler.py` + `candle_pattern_analyzer.py`
| ฟิลด์ | แหล่งที่มา |
|---|---|
| pattern | `candle_pattern_analyzer.py` — ตรวจ 7 รูปแบบแท่งเทียนจริง (Engulfing, Hammer, Doji, Morning/Evening Star ฯลฯ) ด้วยเงื่อนไข OHLC จริง |
| last_candle_bias | **คำนวณจาก M5 DataFrame**: close M5 > open M5 → BULLISH |
| body_strength, wick_dominance, momentum_bias, move_quality | `price_action_handler.py` — คำนวณจาก body/wick ratio, momentum dominance จริง |
| trap_alert | `trap_detector.py` — ตรวจ false breakout / stop hunt / rejection wick จาก OHLC จริง |
| sr_interaction | คำนวณจาก fractal support/resistance (`_fractal_support_resistance`) เทียบราคาปิดปัจจุบัน |

### volume (3 ฟิลด์)
สำหรับคู่ OTC: บังคับเป็น 1.0/`NO_VOLUME_DATA` เพราะ OTC ไม่มีข้อมูล volume จริง (เป็นการ mark ชัดเจน ไม่ใช่การปลอมข้อมูล) — สำหรับคู่ปกติ คำนวณจาก volume จริงเทียบ MA20

### analysis (7 ฟิลด์) — จาก 5 Tier-1 engines
| ฟิลด์ | แหล่งที่มา |
|---|---|
| trend_direction | `trend_engine.py`: เทียบ price/EMA20/EMA50/EMA100 ต้องเรียงลำดับสมบูรณ์ถึงจะได้ UP/DOWN ไม่งั้น NONE |
| trend_strength_score | `trend_engine.py`: คำนวณจาก **ความชันของ slope (regression 10 แท่ง)** — ดู "จุดที่ 1" ในหัวข้อ 4 |
| mtf_alignment_% | `mtf_engine.py`: % ของ timeframe (M1/M5/M15) ที่ทิศทาง EMA ตรงกัน |
| compression_quality_% | `volatility_engine.py`: จาก bb_width เทียบ bbw_sma_100 |
| exhaustion_risk_% | `strength_engine.py`: จาก ADX/RSI สุดขั้ว + MACD divergence |
| bos_detected | `structure_engine.py`: True เมื่อราคาทะลุ support/resistance จริง |

### decision_layer (8 ฟิลด์)
4 ฟิลด์แรก (`tradeable`, `stability_score`, `quality_score`, `risk_level`) คำนวณจริงจาก `market_state_classifier.py` — 4 ฟิลด์หลัง (`confidence_score`, `suggested_expiry_minutes`, `suggested_action`, `final_reason_th`) เป็น placeholder ข้อความคงที่ "รอการวิเคราะห์จาก AI" ตามที่ Boss ระบุไว้ว่า AI จะเป็นผู้ใส่เอง — **ยืนยันว่าไม่มีการคำนวณหลอกในฟิลด์เหล่านี้ เป็นการเว้นว่างไว้จริง**

---

## 4. จุดที่เป็นตรรกะอ่อน (ไม่ใช่ข้อมูลเท็จ แต่ควรทราบ)

### จุดที่ 1 — `trend_strength_score` ไม่ผูกกับ `trend_direction`
`trend_engine.py` → `_slope_to_strength()` คำนวณคะแนนความแข็งแรงจาก **ค่าสัมบูรณ์ของ slope เพียงอย่างเดียว** โดยไม่เช็คว่า `direction` เป็น NONE หรือไม่ ผลคือ: ตลาดที่ไม่มีทิศทางชัดเจน (EMA ไม่เรียงลำดับ → direction=NONE) แต่ราคาแกว่งแรงในช่วงสั้น (slope สูง) จะได้ `trend_strength_score = 100` ทั้งที่ direction เป็น NONE — เป็นค่าที่คำนวณจริง ไม่ใช่ bug คำนวณผิดสูตร แต่เป็นช่องโหว่เชิงตรรกะที่อาจทำให้ AI ตีความผิดว่า "เทรนด์แข็งแรง" ทั้งที่จริงคือ "ราคาแกว่งแรงแบบไม่มีทิศทาง"

### จุดที่ 2 — Pivot กับ Support/Resistance คนละสูตร คนละที่มา
`m5_pivot` มาจาก `indicator_store.py` (สูตร floor pivot จากแท่งที่ปิดสมบูรณ์แท่งเดียว) ส่วน `m5_support`/`m5_resistance` ที่แสดงจริงถูก **เขียนทับ** ใน `advanced_tools_manager.py` ด้วยค่า fractal support/resistance จาก `price_action_handler.py` (หา fractal high/low จาก 20+ แท่งย้อนหลัง) — สองค่านี้ไม่ได้คำนวณจากฐานเดียวกัน จึงเป็นไปได้ที่ pivot จะอยู่นอกกรอบ support-resistance (ไม่ใช่บั๊ก แต่เป็นการผสมสองระเบียบวิธีที่ต่างกัน)

### จุดที่ 3 — ชื่อฟิลด์ `last_candle` ซ้ำกันแต่คนละ timeframe
`timeframes.m1.last_candle` คำนวณจากแท่ง **M1**, ส่วน `price_action.last_candle_bias` คำนวณจากแท่ง **M5** (ผ่าน `candle_pattern_analyzer.py` ที่รับ `df_m5`) — ทั้งสองค่าถูกต้องตามข้อมูลจริงของ timeframe ตัวเอง แต่ชื่อฟิลด์ไม่ได้ระบุ timeframe ไว้ อาจทำให้ผู้อ่าน (คนหรือ AI) เข้าใจผิดว่าเป็นค่าเดียวกันแล้วดู "ขัดแย้งกัน"

---

## 5. โค้ดที่ไม่ได้ถูกใช้งานจริง (Dead Code)

ตรวจสอบ `orchestrator.py` แล้วยืนยันว่า **ไม่ได้ import หรือเรียกใช้** ไฟล์ต่อไปนี้เลยแม้แต่ครั้งเดียวในระหว่าง cycle การทำงานจริง:

- `pipeline.py` (คลาส `Pipeline`)
- `context_builder.py` (คลาส `ContextBuilder`) — คนละตัวกับ `context_synthesizer.py` ที่ถูกใช้จริง
- `engine_registry.py`, `engine_setup.py`
- `scoring/` ทั้งโฟลเดอร์ (`confidence_scorer.py`, `entry_scorer.py`, `block_scorer.py`, `score_aggregator.py`, `score_normalizer.py`, `signal_quality_scorer.py`, `confidence_framework.py`)
- `models/signal.py`, `models/score.py`
- `interfaces/strategy_interface.py`

ไฟล์เหล่านี้เป็นโครงสร้างของระบบ "Strategy + Signal + Execution Gate" ที่ซับซ้อนกว่า ซึ่งน่าจะติดมาจากการคัดลอกทั้งโฟลเดอร์จากบอทตัวอื่น (`FINALBOT_Ai V.1`) ตามที่ Boss แจ้งไว้ — **ไม่ส่งผลกระทบต่อความถูกต้องของข้อมูลในไฟล์ .txt ที่ AI อ่าน เพราะไม่ได้อยู่ใน execution path** แต่ทำให้โค้ดเบสใหญ่เกินจำเป็นและอาจสร้างความสับสนเวลาแก้ไขในอนาคต (แนะนำให้ปรึกษา Boss ก่อนว่าจะเก็บไว้หรือลบทิ้ง — หนูไม่มีสิทธิ์ตัดสินใจหรือแก้ไขเอง)

---

## 6. สรุปคำตอบคำถามที่ Boss เคยถามไว้ (พร้อมหลักฐานโค้ด)

| คำถามเดิม | คำตอบ |
|---|---|
| last_candle ขัดแย้งกัน (BEARISH vs BULLISH) | ไม่ใช่บั๊ก — คนละ timeframe (M1 vs M5) ดูหัวข้อ 4 จุดที่ 3 |
| trend_direction=NONE แต่ strength=100 | เป็นช่องโหว่เชิงตรรกะจริง (คำนวณถูกสูตร แต่ตรรกะไม่ผูกกัน) ดูหัวข้อ 4 จุดที่ 1 |
| pivot ต่ำกว่า support | ไม่ใช่บั๊ก — คนละสูตร คนละที่มา ดูหัวข้อ 4 จุดที่ 2 |
| volatility_regime=HIGH แต่ expected_volatility_%=0.134 ดูต่ำ | ไม่ใช่บั๊ก — regime มาจาก**อันดับเปอร์เซ็นไทล์เทียบประวัติของตัวเอง** ส่วน expected_volatility_% เป็น**ค่าสัมบูรณ์ (ATR/price)** ซึ่งของ forex จะเป็นเลขน้อยตามธรรมชาติอยู่แล้ว คนละสเกลกัน |

---

## 7. ข้อสรุปสุดท้าย

**บอทส่วนงานที่ 2 คำนวณข้อมูลจริงจากราคาตลาดจริง 100% ไม่มีข้อมูลเท็จ ไม่มีค่า hardcode/สุ่มปลอมแอบแฝงอยู่ในฟิลด์ที่ AI จะใช้ตัดสินใจ** สิ่งที่ควรติดตามต่อคือ 3 จุดตรรกะอ่อนในหัวข้อ 4 (แนะนำให้พิจารณาว่าจะให้ทีมแก้ไขหรือไม่) และการตัดสินใจเรื่อง dead code ในหัวข้อ 5

*รายงานนี้จัดทำจากการอ่านซอร์สโค้ดจริงทุกไฟล์ใน execution path เท่านั้น ไม่มีการอนุมานหรือคาดเดา*
