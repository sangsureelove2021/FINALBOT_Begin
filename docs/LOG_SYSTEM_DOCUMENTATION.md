# เอกสารสถาปัตยกรรมและการบันทึก Log ของระบบ FINALBOT (LOG SYSTEM DOCUMENTATION)

> **ศูนย์รวม Log หลัก (Single Source of Truth - SSOT):** `E:\BOT_FINALBOT\FINALBOT_Begin\all_filelogs\`  
> **สถานะการย้ายข้อมูล (Consolidation Status):** คัดลอก/ย้าย Log ทั้งหมดจาก `logs/system_logs` เข้าสู่ `all_filelogs/system_logs` เรียบร้อยแล้ว 100%

---

## 1. โครงสร้างสถาปัตยกรรมระบบ Log (Overall Log Architecture)

ระบบ FINALBOT ออกแบบโดยใช้หลักการ **Decoupled Architecture (สถาปัตยกรรมแบบแยกส่วน)** และ **RAM-less Data Flow (การส่งผ่านข้อมูลผ่านไฟล์ดิสก์โดยไม่ผ่าน RAM ข้ามโมดูล)** เพื่อสร้างความเสถียรสูงสุด ป้องกันข้อมูลสูญหายเมื่อระบบหยุดทำงานชั่วคราว (Crash Resilience) และรองรับการตรวจสอบย้อนหลัง (Auditability) ได้ 100%

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               1. DATA FEED STAGE                                       │
│  IQ Option WebSocket ──> CSV Raw Ingestion ──> data_base/csv/iq_option/[symbol]/        │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                     (File I/O Only)
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                            2. ANALYSIS & ORCHESTRATOR STAGE                            │
│  orchestrator.py ──> Indicator Store & 5 Parallel Engines ──> Market State Classifier  │
│  └─> Export Core Analysis (63+/74 Fields TXT) ──> all_filelogs/logs_orchestrator/      │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                     (File I/O Only)
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              3. AI & STRATEGY EXECUTION                                │
│  AI / Strategy Engine ──> Read TXT Payload ──> Decision & Trade Order Execution         │
│  ├─> AI Execution Logs ───────> all_filelogs/logs_ai/                                  │
│  ├─> Strategy Logs ───────────> all_filelogs/logs_strategy/                            │
│  └─> Trade Orders Log (JSONL) ─> all_filelogs/orders/orders.jsonl                      │
└────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               4. SYSTEM MONITORING & AUDIT                             │
│  ├─> Runtime & Errors ────────> all_filelogs/system_logs/                              │
│  ├─> Anomaly & Zero Volume ───> all_filelogs/anomaly_logs/                             │
│  ├─> Economic News ───────────> all_filelogs/calendar_logs/                            │
│  └─> Signal & Performance ────> all_filelogs/signal_tracker/                           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### หลักการสำคัญ 4 ประการของระบบ Log:
1. **Single Source of Truth (SSOT):** โฟลเดอร์ `all_filelogs/` เป็นศูนย์กลางการเก็บ Log เพียงแห่งเดียวของทั้งระบบ
2. **Fail-Fast & No Silent Failures:** เมื่อเกิดข้อผิดพลาดในการประมวลผลหรือบันทึก Log ระบบจะทำการบันทึก Stack Trace เต็มรูปแบบ (`logger.exception`) และแจ้งหยุดทันที ห้ามหมกเม็ด Error หรือซ่อนด้วย `except Exception: pass`
3. **Immutability & Deduplication:** ข้อมูลในไฟล์ Log จะถูกกำจัดแถวเวลาซ้ำซ้อน (`df[~df.index.duplicated(keep='last')]`) และรับประกันความถูกต้องของลำดับเวลา
4. **OTC Compatibility Standard:** สำหรับคู่เงิน OTC ข้อมูลวอลุ่มที่ไม่สะท้อนตลาดจริงจะถูกปรับเป็นค่ามาตรฐาน Neutral (`NONE_OTC` หรือ `volume=1.0`) เพื่อป้องกัน AI/Strategy เกิดการหลงทิศทางจากสัญญาณเท็จ

---

## 2. รายละเอียดโฟลเดอร์ทั้ง 14 โฟลเดอร์ใน `all_filelogs/`

| ลำดับ | ชื่อโฟลเดอร์ (Directory Name) | คำอธิบายและหน้าที่การทำงาน (Description & Function) | รูปแบบไฟล์ (File Format) |
| :---: | :--- | :--- | :---: |
| 1 | `all_process` | เก็บบันทึกไฟล์ประมวลผลข้อมูลราคาและอินดิเคเตอร์รวมทุก Timeframe ในรูปแบบ CSV สำหรับการวิเคราะห์เชิงลึกย้อนหลัง | `.csv` |
| 2 | `anomaly_logs` | เก็บบันทึกรายการความผิดปกติของข้อมูลตลาด เช่น การตรวจพบ Volume เป็นศูนย์ (`zero_volume`), สัญญาณราคาขาดหาย หรือการกระโดดของราคาที่ผิดปกติ | `.csv` / `.log` |
| 3 | `archive` | โฟลเดอร์สำหรับจัดเก็บสำรอง (Archive) ไฟล์ Log และสคริปต์ประมวลผลรุ่นเก่าเพื่อความสะอาดของระบบหลัก | หลากหลาย |
| 4 | `calendar_logs` | เก็บบันทึกข้อมูลปฏิทินข่าวสารทางเศรษฐกิจ (Economic Calendar Events) และระดับผลกระทบของข่าวในแต่ละวัน | `.json` |
| 5 | `json_process` | เก็บบันทึก Payload การวิเคราะห์สภาวะตลาดสมบูรณ์ในรูปแบบโครงสร้าง JSON | `.json` |
| 6 | `logs_ai` | เก็บบันทึกประวัติการส่งวิเคราะห์ ข้อความ Prompt คำตอบจากโมเดล AI (เช่น DeepSeek / Gemini) และบันทึกความจำ AI Memory | `.txt` / `.json` |
| 7 | `logs_datafeed` | เก็บบันทึกสถานะการรับส่งข้อมูล Real-time การเชื่อมต่อ WebSocket กับ Broker และข้อผิดพลาดระดับวิกฤตของ Data Feed | `.log` |
| 8 | `logs_orchestrator` | **ศูนย์รวมไฟล์วิเคราะห์หลัก (SSOT Output):** เก็บบันทึกผลการวิเคราะห์ 63+ / 74 ฟิลด์ของ Orchestrator รายรอบการคำนวณ | `.txt` (YAML format) |
| 9 | `logs_strategy` | เก็บบันทึกการเงื่อนไขประเมินของกลยุทธ์การเทรด (Strategy Rules) ทั้งเงื่อนไขการเข้า (Entry) และออก (Exit) ออเดอร์ | `.log` / `.txt` |
| 10 | `Machine Learning` | เก็บบันทึก Feature Store, ชุดข้อมูลการฝึกฝนโมเดล (Training Data) และผลคะแนนการทำนายของโมเดล Machine Learning | `.csv` / `.pkl` / `.json` |
| 11 | `market_snapshots` | เก็บบันทึกภาพถ่ายสภาวะตลาด (Snapshot) ณ ช่วงเวลาสำคัญเพื่อใช้เปรียบเทียบโครงสร้างราคาและพฤติกรรมกราฟ | `.json` / `.csv` |
| 12 | `orders` | เก็บบันทึกประวัติการส่งคำสั่งเทรด (Trade Orders Executed), สถานะออเดอร์ (Win/Loss), ราคาเปิด-ปิด และกำไรขาดทุน | `.jsonl` / `.csv` |
| 13 | `signal_tracker` | เก็บบันทึกการติดตามประสิทธิภาพของสัญญาณเทรด (Signal Performance Tracker) การเรียนรู้และปรับปรุงน้ำหนักสัญญาณ | `.py` / `.json` |
| 14 | `system_logs` | **ศูนย์รวม Log การทำงานระบบหลัก:** คัดลอก/ย้ายจาก `logs/system_logs` มารวมที่นี่ 100% บันทึก Console Output, Exception Traceback และเหตุการณ์ระบบทั้งหมด (`bot_YYYYMMDD_HHMMSS.log`) | `.log` |

---

## 3. รายละเอียดฟิลด์วิเคราะห์ 63+ / 74 ฟิลด์ของ `logs_orchestrator`

ไฟล์วิเคราะห์ใน `all_filelogs/logs_orchestrator/` จะใช้ชื่อไฟล์ในรูปแบบ `[PROMPT_ID].txt` (ตัวอย่าง: `EURUSD0724125805.txt`) โดยโครงสร้างภายในประกอบด้วยฟิลด์วิเคราะห์หลัก **65 ฟิลด์ (Core Analysis)** และฟิลด์เสริมรวม **74 ฟิลด์ (Total System Fields)** แบ่งตามหมวดหมู่ดังนี้:

### โครงสร้างชื่อไฟล์และ Header
* **PROMPT_ID:** รหัสอ้างอิงรอบการคำนวณ สร้างจาก `[SYMBOL][MMDDHHMMSS]` (เช่น `EURUSD0724125805`)

---

### รายละเอียดฟิลด์ทั้ง 7 หมวดหมู่หลัก (Core Analysis - 65 ฟิลด์)

#### หมวดที่ 1: Market Context & State (สภาวะและบริบทตลาด - 5 ฟิลด์)
1. `state`: สภาวะตลาดปัจจุบัน (เช่น `SIDEWAY_RANGE`, `BULLISH_TREND`, `BEARISH_BREAKOUT`)
2. `description`: คำอธิบายสภาวะตลาดและคำแนะนำกลยุทธ์เบื้องต้น
3. `volatility_regime`: โหมดความผันผวนของตลาด (`LOW`, `NORMAL`, `HIGH`, `EXTREME`)
4. `news_impact`: ระดับผลกระทบจากข่าวเศรษฐกิจ (`NONE`, `LOW`, `MEDIUM`, `HIGH`, `NONE_OTC`)
5. `expected_volatility_%`: เปอร์เซ็นต์ความผันผวนที่คาดการณ์ คำนวณจาก `(ATR / Close) * 100`

#### หมวดที่ 2: M5 Indicators (ตัวชี้วัดทางเทคนิค Timeframe 5 นาที - 18 ฟิลด์)
6. `m5_bias`: ทิศทางแนวโน้มภาพรวม M5 (`BULLISH`, `BEARISH`, `NEUTRAL`)
7. `m5_ema5`: ค่าเส้นเฉลี่ยเคลื่อนที่ Exponential 5 งวด M5
8. `m5_ema10`: ค่าเส้นเฉลี่ยเคลื่อนที่ Exponential 10 งวด M5
9. `m5_ema20`: ค่าเส้นเฉลี่ยเคลื่อนที่ Exponential 20 งวด M5
10. `m5_ema50`: ค่าเส้นเฉลี่ยเคลื่อนที่ Exponential 50 งวด M5
11. `m5_bb_upper`: กรอบบน Bollinger Bands M5
12. `m5_bb_lower`: กรอบล่าง Bollinger Bands M5
13. `m5_bb_width`: ความกว้างของกรอบ Bollinger Bands M5
14. `m5_rsi`: ค่า Relative Strength Index (14) M5
15. `m5_stoch_k`: ค่า Stochastic Oscillator %K M5
16. `m5_stoch_d`: ค่า Stochastic Oscillator %D M5
17. `m5_macd`: ค่า MACD Line M5
18. `m5_macd_signal`: ค่า MACD Signal Line M5
19. `m5_adx`: ค่า Average Directional Index (ความแรงแนวโน้ม) M5
20. `m5_atr`: ค่า Average True Range (ความผันผวน) M5
21. `m5_support`: แนวรับสำคัญ M5
22. `m5_resistance`: แนวต้านสำคัญ M5
23. `m5_pivot`: จุดกลับตัว Pivot Point M5

#### หมวดที่ 3: M1 Indicators (ตัวชี้วัดทางเทคนิค Timeframe 1 นาที - 8 ฟิลด์)
24. `m1_last_candle`: สถานะแท่งเทียนล่าสุด M1 (`BULLISH`, `BEARISH`)
25. `m1_ema5`: ค่าเส้นเฉลี่ยเคลื่อนที่ EMA 5 M1
26. `m1_ema20`: ค่าเส้นเฉลี่ยเคลื่อนที่ EMA 20 M1
27. `m1_rsi`: ค่า RSI (14) M1
28. `m1_stoch_k`: ค่า Stochastic %K M1
29. `m1_stoch_d`: ค่า Stochastic %D M1
30. `m1_macd`: ค่า MACD Line M1
31. `m1_macd_signal`: ค่า MACD Signal Line M1

#### หมวดที่ 4: M15 Indicators (ตัวชี้วัดทางเทคนิค Timeframe 15 นาที - 1 ฟิลด์)
32. `m15_bias`: ทิศทางแนวโน้มภาพรวมกรอบเวลาใหญ่ M15 (`BULLISH`, `BEARISH`, `NEUTRAL`)

#### หมวดที่ 5: Advanced Tools - Price Action & Volume (เครื่องมือวิเคราะห์ขั้นสูง - 11 ฟิลด์)
33. `pa_pattern`: รูปแบบแท่งเทียน Price Action (เช่น `PINBAR`, `ENGULFING`, `NONE`)
34. `pa_last_candle_bias`: แรงแท่งเทียนล่าสุด (`BULLISH`, `BEARISH`)
35. `pa_body_strength`: ความแข็งแกร่งของเนื้อเทียน (`STRONG`, `MEDIUM`, `WEAK`)
36. `pa_wick_dominance`: ลักษณะไส้เทียนเด่น (`HIGH_WICK`, `LOW_WICK`, `BALANCED`)
37. `pa_momentum_bias`: ทิศทางแรงโมเมนตัมราคา (`BULLISH`, `BEARISH`, `NEUTRAL`)
38. `pa_move_quality`: คุณภาพการเคลื่อนที่ของราคา (`SMOOTH`, `CHAOTIC`, `RANGING`)
39. `pa_trap_alert`: สัญญาณเตือนกับดักราคา (`BULL_TRAP`, `BEAR_TRAP`, `NONE`)
40. `pa_sr_interaction`: การปฏิสัมพันธ์กับแนวรับแนวต้าน (`TESTING_SUPPORT`, `TESTING_PIVOT`, `NONE`)
41. `vol_tick_volume`: ปริมาณการซื้อขาย Tick Volume M5 (`1.0` สำหรับ OTC)
42. `vol_momentum`: โมเมนตัมของวอลุ่ม (`HIGH_MOMENTUM`, `NORMAL`, `NO_VOLUME_DATA`)
43. `vol_vs_average`: อัตราส่วนวอลุ่มเทียบค่าเฉลี่ย (`Volume Ratio`)

#### หมวดที่ 6: Tier-1 Engine Analysis (ผลประมวลผล 5 Engine ขนาน - 14 ฟิลด์)
44. `eng_trend_direction`: ทิศทางจาก Trend Engine (`UP`, `DOWN`, `NONE`)
45. `eng_trend_strength`: คะแนนความแข็งแรงแนวโน้ม (0-100)
46. `eng_trend_type`: ประเภทแนวโน้ม (`STRONG_TREND`, `CHOPPY`, `REVERSAL`)
47. `eng_strength_momentum_bias`: ทิศทางจาก Strength Engine (`STRONG`, `WEAK`, `NEUTRAL`)
48. `eng_strength_momentum_strength`: คะแนนโมเมนตัมจาก Strength Engine
49. `eng_strength_exhaustion_risk`: คะแนนความเสี่ยงราคาหมดแรง (Exhaustion Risk %)
50. `eng_volatility_regime`: โหมดความผันผวนจาก Volatility Engine
51. `eng_volatility_compression_detected`: การตรวจพบการบีบตัวของราคา (Squeeze/Compression True/False)
52. `eng_volatility_compression_quality`: คะแนนคุณภาพการบีบตัวของราคา (%)
53. `eng_volatility_score`: คะแนนความผันผวนรวม (0-100)
54. `eng_structure_type`: โครงสร้างราคาจาก Structure Engine (`TRENDING`, `RANGING`, `BREAKOUT`)
55. `eng_structure_bos_detected`: การตรวจพบการทะลุโครงสร้าง (Break of Structure - True/False)
56. `eng_mtf_alignment_score`: คะแนนความสอดคล้องของหลาย Timeframe (MTF Alignment Score %)
57. `eng_mtf_htf_direction`: ทิศทางหลักจาก Timeframe ใหญ่ (`UP`, `DOWN`, `NEUTRAL`)

#### หมวดที่ 7: Decision Layer (ชั้นการตัดสินใจและข้อแนะนำ - 8 ฟิลด์)
58. `dl_tradeable`: สถานะความเหมาะสมในการเทรด (`True` / `False`)
59. `dl_stability_score`: คะแนนความเสถียรของสภาวะตลาด (0-100)
60. `dl_quality_score`: คะแนนคุณภาพสัญญาณรวม (0-100)
61. `dl_risk_level`: ระดับความเสี่ยง (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
62. `dl_confidence_score`: คะแนนความมั่นใจในการส่งคำสั่ง
63. `dl_suggested_expiry_minutes`: เวลาหมดอายุออเดอร์ที่แนะนำ (เช่น 5, 10, 15 นาที)
64. `dl_suggested_action`: การกระทำที่แนะนำ (`CALL`, `PUT`, `WAIT`, `PREPARE_TO_TRADE`)
65. `dl_final_reason_th`: สรุปเหตุผลการตัดสินใจภาษาไทย

---

### หมวดที่ 8: Meta & Supplementary Data (ข้อมูลกำกับระบบ - 9 ฟิลด์เสริม)
66. `timestamp`: เวลาประมวลผลระดับ ISO-8601 (เช่น `2026-07-24T12:58:05`)
67. `symbol`: สัญลักษณ์คู่เงิน (เช่น `EURUSD`, `EURGBP-OTC`)
68. `session`: ช่วงเวลาการเทรดของโลก (`SYDNEY/TOKYO`, `LONDON_OPEN`, `NY/LONDON_OVERLAP`, `NY_AFTERNOON`)
69. `m1_open`: ราคาเปิดแท่งเทียน M1
70. `m1_age`: อายุของข้อมูล M1 (มิลลิวินาที)
71. `m1_quality`: คุณภาพข้อมูล M1 (`FRESH`, `MEDIUM`, `STALE`)
72. `m5_open`: ราคาเปิดแท่งเทียน M5
73. `m5_age`: อายุของข้อมูล M5 (มิลลิวินาที)
74. `m5_quality`: คุณภาพข้อมูล M5 (`FRESH`, `MEDIUM`, `STALE`)

---

## 4. ความเชื่อมโยงของระบบรันและการบันทึก Log ของ FINALBOT

```
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                      กระบวนการทำงานในแต่ละรอบ (60-Second Live Cycle)                   │
 └────────────────────────────────────────────────────────────────────────────────────────┘
                                           │
  1. main_live.py / Orchestrator เริ่มต้นรอบประมวลผล
     ├─> บันทึก System Log ลงใน all_filelogs/system_logs/bot_YYYYMMDD_HHMMSS.log
     └─> ตรวจสอบความพร้อมของข้อมูลดิบใน data_base/csv/iq_option/
                                           │
                                           ▼
  2. Orchestrator อ่านไฟล์ CSV (M1, M5, M15) 
     ├─> ตรวจสอบและลบ Duplicate Timestamps ด้วย df[~df.index.duplicated(keep='last')]
     ├─> คำนวณ Basic Indicators (Indicator Store)
     ├─> คำนวณ Advanced Tools (Price Action & Volume)
     ├─> เรียกใช้ 5 Engines แบบขนาน (ThreadPoolExecutor max_workers=5)
     └─> จำแนกสภาวะตลาดผ่าน MarketStateClassifier
                                           │
                                           ▼
  3. บันทึกผลการวิเคราะห์ลง Log
     ├─> สร้าง SSOT Payload TXT (65 ฟิลด์หลัก + 9 ฟิลด์เสริม) 
     │   ลงใน all_filelogs/logs_orchestrator/[PROMPT_ID].txt
     └─> หากพบ Anomaly (เช่น Volume=0 บน Non-OTC) 
         บันทึกลงใน all_filelogs/anomaly_logs/
                                           │
                                           ▼
  4. การส่งต่อเข้าสู่ Execution / AI Layer
     ├─> AI หรือ Strategy Engine ดึงไฟล์ TXT จาก all_filelogs/logs_orchestrator/
     ├─> ทำการตัดสินใจเทรด บันทึกประวัติลง all_filelogs/logs_ai/ และ all_filelogs/logs_strategy/
     └─> เมื่อส่งคำสั่งสำเร็จ บันทึกรายการลง all_filelogs/orders/orders.jsonl
```

### สรุปกฎระเบียบการบันทึก Log ของระบบ:
* **การรวมศูนย์ Log (Log Centralization):** ห้ามสร้างไฟล์ Log นอกโฟลเดอร์ `all_filelogs/` เป็นอันขาด ทุกโมดูลต้องเขียนไฟล์ลงในย่อยโฟลเดอร์ของ `all_filelogs/` เท่านั้น
* **ความโปร่งใสของ Log (Traceability):** ทุกไฟล์ Log ที่สร้างขึ้นสามารถย้อนกลับไปยัง `PROMPT_ID` และ `timestamp` ได้อย่างเที่ยงตรง
* **การปฏิบัติตามวินัย AI (AI Discipline):** เลขาเอเธน่าและผู้ช่วยทุกตัวยึดถือความเป็นมืออาชีพ ปฏิบัติตามคำสั่งบอสอย่างเคร่งครัด อัปเดตและควบคุม Log ทั้งหมดให้พร้อมใช้งาน 100%
