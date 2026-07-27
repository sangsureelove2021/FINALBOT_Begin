# 📋 รายงานการสแกนโค้ดสแกนทีละฟิลด์ครบ 74 ฟิลด์ (74-Field Code Trace Report of Orchestrator)

เอกสารนี้ระบุการเชื่อมโยงซอร์สโค้ดใน `data_evaluate/orchestrator.py` สำหรับฟิลด์ส่งออกทั้ง 74 ฟิลด์ (ความยาว 91 บรรทัด .txt) อย่างละเอียดทุกบรรทัด

---

## 📊 ตารางสแกนไล่ตรวจโค้ดทีละฟิลด์ (Line-by-Line Code Trace Table)

| # | ชื่อฟิลด์ใน TXT Output | บรรทัด TXT | บรรทัดโค้ด `orchestrator.py` | ฟังก์ชัน / โมดูลต้นทางที่คำนวณค่า |
| :---: | --- | :---: | :---: | --- |
| 1 | `ID` | L1 | L947 | `prompt_id` (ISO Compact Timestamp `[SYMBOL][MMDDHHMMSS]`) |
| 2 | `meta.timestamp` | L3 | L949, L525 | `p.get('timestamp')` (เวลามาตรฐาน ISO-8601 UTC Sync Clock) |
| 3 | `meta.symbol` | L4 | L950, L526 | `_req(p, 'symbol')` จากโครงสร้าง payload หลัก |
| 4 | `meta.session` | L5 | L951, L527 | `_derive_session()` คำนวณช่วงเวลาตลาดโลก (`NEW YORK`, `LONDON`, ฯลฯ) |
| 5 | `meta.m1_open` | L6 | L952, L528 | `_req(meta, 'm1_open')` ดึงราคาเปิด M1 ล่าสุดจาก Broker Stream |
| 6 | `meta.m1_age` | L7 | L953, L529 | `_req(meta, 'm1_age')` คำนวณอายุแท่งเทียน M1 (วินาที) |
| 7 | `meta.m1_quality` | L8 | L954, L530 | `_req(meta, 'm1_quality')` ตรวจสอบความสดใหม่ข้อมูล (`FRESH`) |
| 8 | `meta.m5_open` | L9 | L955, L531 | `_req(meta, 'm5_open')` ดึงราคาเปิด M5 ล่าสุดจาก Broker Stream |
| 9 | `meta.m5_age` | L10 | L956, L532 | `_req(meta, 'm5_age')` คำนวณอายุแท่งเทียน M5 (วินาที) |
| 10 | `meta.m5_quality` | L11 | L957, L533 | `_req(meta, 'm5_quality')` ตรวจสอบความสดใหม่ข้อมูล (`FRESH`) |
| 11 | `market_context.state` | L13 | L959, L434 | `_req(mc, 'state')` จาก `market_state_classifier.py` (1 ใน 10 สภาวะ) |
| 12 | `market_context.description` | L14 | L960, L435 | `_req(mc, 'description')` คำอธิบายสภาวะจาก `MarketStateClassifier` |
| 13 | `market_context.volatility_regime` | L15 | L961, L436 | `_req(p, 'analysis', 'volatility_regime')` จาก `VolatilityEngine` |
| 14 | `market_context.news_impact` | L16 | L962, L437 | `check_news.py` หรือบังคับเป็น `'NONE_OTC'` สำหรับ OTC |
| 15 | `market_context.expected_volatility_%` | L17 | L963, L438 | คำนวณสูตร `round((atr / close_price) * 100, 3)` ในบรรทัดที่ 320 |
| 16 | `timeframes.m1.last_candle` | L20 | L966, L461 | เช็คเงื่อนไข `BULLISH` หากราคาปิด M1 > ราคาเปิด M1 (มิฉะนั้น `BEARISH`) |
| 17 | `timeframes.m1.ema5` | L21 | L967, L462 | `_req(m1, 'ema5')` คำนวณค่าเฉลี่ยเคลื่อนที่ EMA 5 ใน `indicator_store.py` |
| 18 | `timeframes.m1.ema20` | L22 | L968, L463 | `_req(m1, 'ema20')` คำนวณค่าเฉลี่ยเคลื่อนที่ EMA 20 ใน `IndicatorStore` |
| 19 | `timeframes.m1.rsi` | L23 | L969, L464 | `_req(m1, 'rsi14')` คำนวณดัชนีกำลัง RSI 14 M1 ใน `IndicatorStore` |
| 20 | `timeframes.m1.stoch_k` | L24 | L970, L465 | `_req(m1, 'stoch_k')` คำนวณ Stochastic %K (14,3,3) ใน `IndicatorStore` |
| 21 | `timeframes.m1.stoch_d` | L25 | L971, L466 | `_req(m1, 'stoch_d')` คำนวณ Stochastic %D (14,3,3) ใน `IndicatorStore` |
| 22 | `timeframes.m1.macd` | L26 | L972, L467 | `_req(m1, 'macd')` คำนวณเส้น MACD Line (12,26,9) ใน `IndicatorStore` |
| 23 | `timeframes.m1.macd_signal` | L27 | L973, L468 | `_req(m1, 'macd_signal')` คำนวณ MACD Signal Line ใน `IndicatorStore` |
| 24 | `timeframes.m1.ohclv.open` | L29 | L975, L536 | `_req(m1, 'open')` ราคาเปิดแท่งเทียน M1 ล่าสุดจาก `candles_dict` |
| 25 | `timeframes.m1.ohclv.high` | L30 | L976, L536 | `_req(m1, 'high')` ราคาสูงสุดแท่งเทียน M1 ล่าสุดจาก `candles_dict` |
| 26 | `timeframes.m1.ohclv.low` | L31 | L977, L536 | `_req(m1, 'low')` ราคาต่ำสุดแท่งเทียน M1 ล่าสุดจาก `candles_dict` |
| 27 | `timeframes.m1.ohclv.close` | L32 | L978, L536 | `_req(m1, 'close')` ราคาปิดแท่งเทียน M1 ล่าสุดจาก `candles_dict` |
| 28 | `timeframes.m1.ohclv.volume` | L33 | L979, L536 | `'NONE_OTC'` สำหรับ OTC หรือ `_req(m1, 'volume')` สำหรับคู่ปกติ |
| 29 | `timeframes.m5.bias` | L35 | L981, L441 | `_req(m5, 'bias')` ดึงทิศทางเทรนด์ M5 จาก `TrendEngine` |
| 30 | `timeframes.m5.ema5` | L36 | L982, L442 | `_req(m5, 'ema5')` คำนวณค่าเฉลี่ยเคลื่อนที่ EMA 5 M5 ใน `IndicatorStore` |
| 31 | `timeframes.m5.ema10` | L37 | L983, L443 | `_req(m5, 'ema10')` คำนวณค่าเฉลี่ยเคลื่อนที่ EMA 10 M5 ใน `IndicatorStore` |
| 32 | `timeframes.m5.ema20` | L38 | L984, L444 | `_req(m5, 'ema20')` คำนวณค่าเฉลี่ยเคลื่อนที่ EMA 20 M5 ใน `IndicatorStore` |
| 33 | `timeframes.m5.ema50` | L39 | L985, L445 | `_req(m5, 'ema50')` คำนวณค่าเฉลี่ยเคลื่อนที่ EMA 50 M5 ใน `IndicatorStore` |
| 44 | `timeframes.m5.bb_upper` | L40 | L986, L446 | `_req(m5, 'bb_upper')` คำนวณกรอบบน Bollinger Band M5 ใน `IndicatorStore` |
| 35 | `timeframes.m5.bb_lower` | L41 | L987, L447 | `_req(m5, 'bb_lower')` คำนวณกรอบล่าง Bollinger Band M5 ใน `IndicatorStore` |
| 36 | `timeframes.m5.bb_width` | L42 | L988, L448 | `_req(m5, 'bb_width')` คำนวณความกว้างกรอบ BB M5 ใน `IndicatorStore` |
| 37 | `timeframes.m5.rsi` | L43 | L989, L449 | `_req(m5, 'rsi14')` คำนวณดัชนีกำลัง RSI 14 M5 ใน `IndicatorStore` |
| 38 | `timeframes.m5.stoch_k` | L44 | L990, L450 | `_req(m5, 'stoch_k')` คำนวณ Stochastic %K M5 ใน `IndicatorStore` |
| 39 | `timeframes.m5.stoch_d` | L45 | L991, L451 | `_req(m5, 'stoch_d')` คำนวณ Stochastic %D M5 ใน `IndicatorStore` |
| 40 | `timeframes.m5.macd` | L46 | L992, L452 | `_req(m5, 'macd')` คำนวณเส้น MACD Line M5 ใน `IndicatorStore` |
| 41 | `timeframes.m5.macd_signal` | L47 | L993, L453 | `_req(m5, 'macd_signal')` คำนวณ MACD Signal Line M5 ใน `IndicatorStore` |
| 42 | `timeframes.m5.adx` | L48 | L994, L454 | `_req(m5, 'adx')` คำนวณดัชนีวัดกำลังเทรนด์ ADX 14 M5 ใน `IndicatorStore` |
| 43 | `timeframes.m5.atr` | L49 | L995, L455 | `_req(m5, 'atr14')` คำนวณระยะแกว่ง ATR 14 M5 ใน `IndicatorStore` |
| 44 | `timeframes.m5.support` | L50 | L996, L456 | `_req(m5, 'support')` คำนวณแนวรับล่าสุดจาก Fractal Low ใน `IndicatorStore` |
| 45 | `timeframes.m5.resistance` | L51 | L997, L457 | `_req(m5, 'resistance')` คำนวณแนวต้านล่าสุดจาก Fractal High ใน `IndicatorStore` |
| 46 | `timeframes.m5.pivot` | L52 | L998, L458 | `_req(m5, 'pivot')` คำนวณจุดกึ่งกลาง Pivot Point (H+L+C)/3 ใน `IndicatorStore` |
| 47 | `timeframes.m5.ohclv.open` | L54 | L1000, L537 | `_req(m5, 'open')` ราคาเปิดแท่งเทียน M5 ล่าสุดจาก `candles_dict` |
| 48 | `timeframes.m5.ohclv.high` | L55 | L1001, L537 | `_req(m5, 'high')` ราคาสูงสุดแท่งเทียน M5 ล่าสุดจาก `candles_dict` |
| 49 | `timeframes.m5.ohclv.low` | L56 | L1002, L537 | `_req(m5, 'low')` ราคาต่ำสุดแท่งเทียน M5 ล่าสุดจาก `candles_dict` |
| 50 | `timeframes.m5.ohclv.close` | L57 | L1003, L537 | `_req(m5, 'close')` ราคาปิดแท่งเทียน M5 ล่าสุดจาก `candles_dict` |
| 51 | `timeframes.m5.ohclv.volume` | L58 | L1004, L537 | `'NONE_OTC'` สำหรับ OTC หรือ `_req(m5, 'volume')` สำหรับคู่ปกติ |
| 52 | `timeframes.m15.bias` | L60 | L1006, L471 | `_req(p, 'm15', 'bias')` ดึงทิศทางเทรนด์ไทม์เฟรมใหญ่ M15 จาก `MtfEngine` |
| 53 | `price_action.pattern` | L62 | L1008, L474 | `_req(pa, 'pattern')` ตรวจจับรูปแบบแท่งเทียนใน `advanced_tools.py` |
| 54 | `price_action.last_candle_bias` | L63 | L1009, L475 | `_req(pa, 'last_candle_bias')` วิเคราะห์ฝั่งความได้เปรียบตัวแท่งใน `AdvancedTools` |
| 55 | `price_action.body_strength` | L64 | L1010, L476 | `_req(pa, 'body_strength')` คำนวณความแข็งแกร่งตัวแท่งใน `AdvancedTools` |
| 56 | `price_action.wick_dominance` | L65 | L1011, L477 | `_req(pa, 'wick_dominance')` คำนวณอัตราส่วนไส้เทียนบน/ล่างใน `AdvancedTools` |
| 57 | `price_action.momentum_bias` | L66 | L1012, L478 | `_req(pa, 'momentum_bias')` ประเมินโมเมนตัมพฤติกรรมราคาใน `AdvancedTools` |
| 58 | `price_action.move_quality` | L67 | L1013, L479 | `_req(pa, 'move_quality')` ประเมินความราบเรียบ/ความผันผวนการวิ่งใน `AdvancedTools` |
| 59 | `price_action.trap_alert` | L68 | L1014, L480 | `_req(pa, 'trap_alert')` ตรวจจับกับดักราคา (`BULL_TRAP`/`BEAR_TRAP`) ใน `TrapDetector` |
| 60 | `price_action.sr_interaction` | L69 | L1015, L481 | `_req(pa, 'sr_interaction')` เช็คการปะทะแนวรับต้านใน `AdvancedTools` |
| 61 | `volume.tick_volume` | L71 | L1017, L482 | `1.0` สำหรับ OTC หรือ `_req(m5, 'volume')` สำหรับคู่ปกติ |
| 62 | `volume.volume_momentum` | L72 | L1018, L483 | `'NO_VOLUME_DATA'` สำหรับ OTC หรือ `_req(pa, 'volume_momentum')` สำหรับคู่ปกติ |
| 63 | `volume.volume_vs_average` | L73 | L1019, L484 | `1.0` สำหรับ OTC หรือ `_req(m5, 'volume_ratio')` สำหรับคู่ปกติ |
| 64 | `analysis.trend_direction` | L75 | L1021, L487 | `_req(eng, 'trend', 'direction')` ดึงทิศทางเทรนด์หลักจาก `TrendEngine` |
| 65 | `analysis.trend_type` | L76 | L1022, L489 | `_req(eng, 'trend', 'type')` จำแนกประเภทเทรนด์ (`IMPULSIVE`/`CHOPPY`) จาก `TrendEngine` |
| 66 | `analysis.trend_strength_score` | L77 | L1023, L488 | `_req(eng, 'trend', 'strength')` คะแนนกำลังเทรนด์ (0-100) จาก `TrendEngine` |
| 67 | `analysis.mtf_alignment_%` | L78 | L1024, L499 | `_req(eng, 'mtf', 'alignment_score')` % ความสอดคล้อง MTF จาก `MtfEngine` |
| 68 | `analysis.compression_quality_%` | L79 | L1025, L495 | `_req(eng, 'volatility', 'compression_quality')` % คุณภาพการบีบตัวจาก `VolatilityEngine` |
| 69 | `analysis.exhaustion_risk_%` | L80 | L1026, L492 | `_req(eng, 'strength', 'exhaustion_risk')` % ความเสี่ยงหมดแรงจาก `StrengthEngine` |
| 70 | `analysis.bos_detected` | L81 | L1027, L498 | `_req(eng, 'structure', 'bos_detected')` ตรวจจับการ Break of Structure จาก `StructureEngine` |
| 71 | `decision_layer.tradeable` | L83 | L1029, L503 | `_req(dl, 'tradeable')` ประเมินเกณฑ์อนุมัติเทรนด์จาก `MarketStateClassifier` |
| 72 | `decision_layer.stability_score` | L84 | L1030, L504 | `_req(dl, 'stability_score')` คะแนนความเสถียรระบบจาก `MarketStateClassifier` |
| 73 | `decision_layer.quality_score` | L85 | L1031, L505 | `_req(dl, 'quality_score')` คะแนนคุณภาพสัญญาณรวมจาก `MarketStateClassifier` |
| 74 | `decision_layer.risk_level` | L86 | L1032, L506 | `_req(dl, 'risk_level')` ประเมินระดับความเสี่ยง (`LOW`/`MEDIUM`/`HIGH`) จาก `MarketStateClassifier` |
