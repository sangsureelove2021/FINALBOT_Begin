# FINALBOT Architecture: 24 Execution Gates & Quality Filters
**คู่มือสถาปัตยกรรมโครงสร้าง 24 ด่านการตรวจสอบ คัดกรอง และออกออเดอร์ของระบบ FINALBOT**

---

## 🗺️ ภาพรวมสถาปัตยกรรม (High-Level Architecture)

```
[PART 1: Data Ingest & Health] ────▶ [PART 2: Technical & Context] ────▶ [PART 3: AI & Execution Gate]
  • ด่าน 1-3: เวลาและวงรอบ               • ด่าน 10-13: อินดิเคเตอร์ & กับดัก      • ด่าน 16-20: AI & System Prompt
  • ด่าน 4-9: การเชื่อมต่อ & ข้อมูล      • ด่าน 14-15: Decision & Prompt 100 บรรทัด • ด่าน 21-24: Gate ชี้ขาด & ยิงออเดอร์
```

---

## 📋 รายละเอียด 24 ด่านการออกออเดอร์เชิงลึก (Line-by-Line Breakdown)

### 🕒 หมวดที่ 1: ด่านเวลาและวงรอบการทำงานหลัก (Master Runner & Session) — 3 ด่าน

#### ด่านที่ 1: ช่วงเวลาทำการเทรด (Trading Hours Gate)
* **ไฟล์:** [`config_setting/settings.json`](file:///e:/FINALBOT_Begin/config_setting/settings.json)
* **โค้ด:** `"trading_hours": "01.00-23.00"`
* **รายละเอียด:** ตรวจสอบเวลาปัจจุบันตามเขตเวลาไทย (Asia/Bangkok) หากอยู่นอกเวลาที่กำหนด บอทจะปฏิเสธการประมวลผลและไม่ยิงออเดอร์

#### ด่านที่ 2: วินาทีปิดแท่งเทียนสมบูรณ์ (Minute-Boundary Trigger)
* **ไฟล์:** [`runner.py`](file:///e:/FINALBOT_Begin/runner.py)
* **โค้ด:** `target_time = now.replace(second=1, microsecond=500000)`
* **รายละเอียด:** บังคับให้เริ่มการวิเคราะห์เฉพาะ ณ วินาทีที่ `:01.500` เท่านั้น เพื่อให้แน่ใจว่าแท่งเทียน M1 ปิดสมบูรณ์ 100%

#### ด่านที่ 3: โหมดการทำงานของบอท (Trading Mode Gate)
* **ไฟล์:** [`data_trade/executor_manager.py`](file:///e:/FINALBOT_Begin/data_trade/executor_manager.py)
* **โค้ด:** `if self.trading_mode == "AI SIGNAL_BOT": should_execute_order = False`
* **รายละเอียด:** คัดกรองระหว่างโหมด `AI AUTO_BOT` (ยิงคำสั่งซื้อขายจริง) กับ `AI SIGNAL_BOT` (แสดงการวิเคราะห์และสัญญาณบนหน้าจอเท่านั้น)

---

### 📥 หมวดที่ 2: Part 1 - ด่านคุณภาพข้อมูลและโบรกเกอร์ (Data Feed & Broker) — 6 ด่าน

#### ด่านที่ 4: การเชื่อมต่อโบรกเกอร์ (Broker Connection Gate)
* **ไฟล์:** [`runner.py`](file:///e:/FINALBOT_Begin/runner.py) & [`data_trade/execution_gate/broker_executor.py`](file:///e:/FINALBOT_Begin/data_trade/execution_gate/broker_executor.py)
* **โค้ด:** `self.data_adapter.ensure_connected()`
* **รายละเอียด:** ตรวจสอบสถานะ Socket และการเชื่อมต่อโบรกเกอร์ก่อนประมวลผล หากหลุดจะ Reconnect ทันที

#### ด่านที่ 5: ทะเบียนรหัสสินทรัพย์ (Dynamic Asset ID Gate)
* **ไฟล์:** [`runner.py`](file:///e:/FINALBOT_Begin/runner.py)
* **โค้ด:** `OP_code.ACTIVES[name] = int(aid)`
* **รายละเอียด:** ลงทะเบียนคู่เงินและสินทรัพย์ทั้งหมด 631 รายการเข้าสู่แคชโบรกเกอร์ ป้องกัน Error `Asset not found on consts`

#### ด่านที่ 6: ความครบถ้วนของแท่งเทียน (Warm-up 250 Candles Gate)
* **ไฟล์:** [`data_evaluate/orchestrator.py`](file:///e:/FINALBOT_Begin/data_evaluate/orchestrator.py)
* **โค้ด:** `min_required_candles = {'M1': 250, 'M5': 250, 'M15': 250}`
* **รายละเอียด:** ตรวจสอบว่ามีข้อมูลแท่งเทียนย้อนหลังครบ 250 แท่งในทุก Timeframe (M1/M5/M15) หากไม่ครบจะ Fail-Fast ทันที

#### ด่านที่ 7: ความสดใหม่ของแท่งเทียน (Candle Freshness Gate)
* **ไฟล์:** [`data_feed/data_validator.py`](file:///e:/FINALBOT_Begin/data_feed/data_validator.py)
* **โค้ด:** `quality == 'FRESH'` (`age <= timeframe_seconds * 2 * 1000`)
* **รายละเอียด:** จัดกลุ่มคุณภาพข้อมูลเป็น `FRESH` และปฏิเสธข้อมูลเก่าค้าง (`STALE`)

#### ด่านที่ 8: ความสมเหตุสมผลของราคา (Price Sanity & FX Range Gate)
* **ไฟล์:** [`data_feed/bridge_adapter/bridge_iq_adapter/rest_fetcher.py`](file:///e:/FINALBOT_Begin/data_feed/bridge_adapter/bridge_iq_adapter/rest_fetcher.py)
* **โค้ด:** `0.3 <= median_close <= 10.0` (และ `50.0 <= price <= 300.0` สำหรับ JPY)
* **รายละเอียด:** ตรวจสอบราคาเฉลี่ย ป้องกันฟีดราคาผิดปกติจากโบรกเกอร์

#### ด่านที่ 9: ตัวกรองข่าวเศรษฐกิจรุนแรง (News Impact Filter)
* **ไฟล์:** [`data_evaluate/news_calendar.py`](file:///e:/FINALBOT_Begin/data_evaluate/news_calendar.py)
* **โค้ด:** `check_news_impact(symbol)`
* **รายละเอียด:** ดึงปฏิทินเศรษฐกิจเพื่อตรวจจับข่าว High Impact (สำหรับสินทรัพย์จริง ส่วน OTC รายงาน `NONE_OTC`)

---

### 🧠 หมวดที่ 3: Part 2 - ด่านประเมินเทคนิคอลและสร้าง Prompt 100 บรรทัด (Data Evaluate) — 6 ด่าน

#### ด่านที่ 10: การสอดคล้องของหลาย Timeframe (MTF Alignment Gate)
* **ไฟล์:** [`data_evaluate/orchestrator.py`](file:///e:/FINALBOT_Begin/data_evaluate/orchestrator.py)
* **โค้ด:** `mtf_alignment_%` และ `mtf_conflict_score`
* **รายละเอียด:** คำนวณความสอดคล้องของทิศทางแนวโน้มระหว่าง M1, M5 และ M15

#### ด่านที่ 11: การตรวจจับความผันผวนผิดปกติ (Volatility Regime Gate)
* **ไฟล์:** [`data_evaluate/orchestrator.py`](file:///e:/FINALBOT_Begin/data_evaluate/orchestrator.py)
* **โค้ด:** `volatility_regime` และ `expected_volatility_%`
* **รายละเอียด:** ตรวจสอบสภาวะตลาด (Normal, Compression, Extreme Volatility)

#### ด่านที่ 12: การดักจับกับดักราคา (Trap & Fakeout Detection Gate)
* **ไฟล์:** [`data_evaluate/orchestrator.py`](file:///e:/FINALBOT_Begin/data_evaluate/orchestrator.py)
* **โค้ด:** `m5_pa_trap_alert` (BULL_TRAP / BEAR_TRAP / NONE)
* **รายละเอียด:** วิเคราะห์ไส้เทียนและพฤติกรรมราคาเพื่อแจ้งเตือนกับดักราคาให้ AI ทราบ

#### ด่านที่ 13: การยืนยันสัญญาณ Divergence (Divergence Analyzer Gate)
* **ไฟล์:** [`data_evaluate/orchestration/advanced_tools/divergence_analyzer.py`](file:///e:/FINALBOT_Begin/data_evaluate/orchestration/advanced_tools/divergence_analyzer.py)
* **โค้ด:** `m5_pa_divergence_alert` และ `m5_pa_divergence_strength`
* **รายละเอียด:** ตรวจสอบความขัดแย้งของราคากับ RSI และ MACD เพื่อหาจุดกลับตัว

#### ด่านที่ 14: ด่านสังเคราะห์ความพร้อมตลาด (Decision Layer Gate)
* **ไฟล์:** [`data_evaluate/orchestrator.py`](file:///e:/FINALBOT_Begin/data_evaluate/orchestrator.py)
* **โค้ด:** `dl_tradeable`, `dl_stability_score`, `dl_quality_score`, `dl_risk_level`
* **รายละเอียด:** สรุปคุณภาพและความพร้อมของตลาดในเชิงสถิติ

#### ด่านที่ 15: มาตรฐานไฟล์ Prompt 100 บรรทัดเป๊ะ (100-Line Prompt Contract)
* **ไฟล์:** [`data_evaluate/orchestrator.py`](file:///e:/FINALBOT_Begin/data_evaluate/orchestrator.py)
* **โค้ด:** `_format_payload()` บังคับโครงสร้าง 96 ฟิลด์ตลาด + 4 ฟิลด์ AI
* **รายละเอียด:** ส่งออกไฟล์ `.txt` ที่มีขนาดคงที่ 100 บรรทัดพอดีเข้าสู่ Part 3

---

### 🚀 หมวดที่ 4: Part 3 - ด่านการตัดสินใจ AI และการยิงออเดอร์ (Data Trade & Execution) — 9 ด่าน

#### ด่านที่ 16: การควบคุมความเสี่ยงและการเงิน (Pre-Trade Money Manager Gate)
* **ไฟล์:** [`data_trade/execution_gate/money_manager.py`](file:///e:/FINALBOT_Begin/data_trade/execution_gate/money_manager.py)
* **โค้ด:** `can_trade, risk_reason = self.money_manager.can_trade()`
* **รายละเอียด:** ตรวจสอบขีดจำกัดขาดทุนรายวัน (Daily Loss) และล็อกขนาดไม้คงที่ (Fixed Stake 35 THB)

#### ด่านที่ 17: ด่านเชื่อมต่อสมองกล AI (AI Dispatch & Resilient Fallback Gate)
* **ไฟล์:** [`data_trade/ai_analysis/gemini_bridge.py`](file:///e:/FINALBOT_Begin/data_trade/ai_analysis/gemini_bridge.py)
* **โค้ด:** `send_prompt()` พร้อมระบบสลับ Candidate Models อัตโนมัติ
* **รายละเอียด:** ส่ง Prompt วิเคราะห์และรับผลลัพธ์ JSON จาก Gemini API

#### ด่านที่ 18: การคัดกรองคำสั่งซื้อขาย (Action Resolution Gate)
* **ไฟล์:** [`data_trade/ai_analysis/system_prompt.py`](file:///e:/FINALBOT_Begin/data_trade/ai_analysis/system_prompt.py)
* **โค้ด:** คัดกรองผลลัพธ์ให้อยู่ใน 3 สถานะเท่านั้น: **`CALL` | `PUT` | `WAIT`**
* **รายละเอียด:** ป้องกันคำสั่งนอกเหนือมาตรฐานและแปลงค่าสัญญาณให้อยู่ในรูปแบบที่ถูกต้อง

#### ด่านที่ 19: การจำกัดอายุสัญญา (Expiry Duration Gate)
* **ไฟล์:** [`data_trade/ai_analysis/system_prompt.py`](file:///e:/FINALBOT_Begin/data_trade/ai_analysis/system_prompt.py)
* **โค้ด:** `norm_expiry = max(1, min(5, norm_expiry))`
* **รายละเอียด:** บังคับให้อายุสัญญาการเทรดต้องอยู่ระหว่าง **1 - 5 นาที** เท่านั้น

#### ด่านที่ 20: การปรับเกณฑ์คะแนนความมั่นใจ (Confidence Score Bounding Gate)
* **ไฟล์:** [`data_trade/ai_analysis/system_prompt.py`](file:///e:/FINALBOT_Begin/data_trade/ai_analysis/system_prompt.py)
* **โค้ด:** `norm_confidence = max(0.0, min(100.0, norm_confidence))`
* **รายละเอียด:** ล็อกคะแนนความมั่นใจให้อยู่ในช่วง 0.0 - 100.0%

#### ด่านที่ 21: ด่านชี้ขาดการเข้าเทรด (The Ultimate Execution Gate) 👑
* **ไฟล์:** [`data_trade/execution_gate/gate_controller.py`](file:///e:/FINALBOT_Begin/data_trade/execution_gate/gate_controller.py)
* **โค้ด:**
  ```python
  if action in ("CALL", "PUT") and confidence_score >= 60.0:
      return {"approved": True, ...}  # ➡️ อนุมัติยิงออเดอร์ทันที 100%
  ```
* **รายละเอียด:** **ด่านหัวใจหลักชี้ขาด** หากคะแนน >= 60% และเป็น CALL/PUT อนุมัติเทรดทันที หากคะแนน < 60% หรือเป็น WAIT จะปฏิเสธการเทรด

#### ด่านที่ 22: การส่งคำสั่งออเดอร์เส้นทางหลัก (Binary/Turbo Execution Route)
* **ไฟล์:** [`data_trade/execution_gate/broker_executor.py`](file:///e:/FINALBOT_Begin/data_trade/execution_gate/broker_executor.py)
* **โค้ด:** `api.buy(stake, symbol, act_param, expiry_minutes)`
* **รายละเอียด:** ส่งคำสั่ง Binary Option เข้าโบรกเกอร์ IQ Option ทันที

#### ด่านที่ 23: การส่งคำสั่งเส้นทางสำรอง (Digital Options V2 Fallback Route)
* **ไฟล์:** [`data_trade/execution_gate/broker_executor.py`](file:///e:/FINALBOT_Begin/data_trade/execution_gate/broker_executor.py)
* **โค้ด:** `api.buy_digital_spot(clean_sym, stake, action, duration)`
* **รายละเอียด:** หากเส้นทาง Binary Option ปิดทำการหรือถูกระงับ จะสลับไปยิง Digital Option โดยอัตโนมัติ

#### ด่านที่ 24: การติดตามผลและบันทึกสถิติ (Order Settlement & Tracking Gate)
* **ไฟล์:** [`data_trade/execution_gate/order_tracker.py`](file:///e:/FINALBOT_Begin/data_trade/execution_gate/order_tracker.py)
* **โค้ด:** `track_order()` ➡️ ตรวจผล WIN/LOSE เมื่อหมดเวลา และบันทึกลง `trades_history.csv`
* **รายละเอียด:** ติดตามสถานะออเดอร์แบบ Asynchronous และอัปเดตยอด PnL พอร์ตแบบอัตโนมัติ

---

## 📊 ตารางสรุป 24 ด่าน (Summary Matrix)

| ด่านที่ | ชื่อด่าน | ส่วนงาน (Layer) | ไฟล์ที่เกี่ยวข้อง | ผลลัพธ์เมื่อผ่านเกณฑ์ |
| :---: | :--- | :---: | :--- | :--- |
| **1** | Trading Hours Gate | Main Runner | [`settings.json`](file:///e:/FINALBOT_Begin/config_setting/settings.json) | อนุญาตให้ระบบเริ่มทำงาน |
| **2** | Minute-Boundary Trigger | Main Runner | [`runner.py`](file:///e:/FINALBOT_Begin/runner.py) | ปล่อยสัญญาณ ณ วินาที `:01.500` |
| **3** | Trading Mode Gate | Main Runner | [`executor_manager.py`](file:///e:/FINALBOT_Begin/data_trade/executor_manager.py) | ตัดสินใจระหว่าง Signal vs Auto |
| **4** | Broker Connection Gate | Part 1 | [`runner.py`](file:///e:/FINALBOT_Begin/runner.py) | ยืนยันสถานะ Socket โบรกเกอร์ |
| **5** | Dynamic Asset ID Gate | Part 1 | [`runner.py`](file:///e:/FINALBOT_Begin/runner.py) | ลงทะเบียน Active ID 631 สินทรัพย์ |
| **6** | Warm-up 250 Candles Gate | Part 1 / 2 | [`orchestrator.py`](file:///e:/FINALBOT_Begin/data_evaluate/orchestrator.py) | ยืนยันแท่งเทียนครบ 250 แท่ง |
| **7** | Candle Freshness Gate | Part 1 | [`data_validator.py`](file:///e:/FINALBOT_Begin/data_feed/data_validator.py) | ข้อมูลต้องเป็นสถานะ FRESH |
| **8** | Price Sanity & FX Range Gate | Part 1 | [`rest_fetcher.py`](file:///e:/FINALBOT_Begin/data_feed/bridge_adapter/bridge_iq_adapter/rest_fetcher.py) | ยืนยันราคาไม่หลุดช่วงทศนิยม |
| **9** | News Impact Filter | Part 1 / 2 | [`news_calendar.py`](file:///e:/FINALBOT_Begin/data_evaluate/news_calendar.py) | รายงานความเสี่ยงข่าวแรง |
| **10** | MTF Alignment Gate | Part 2 | [`orchestrator.py`](file:///e:/FINALBOT_Begin/data_evaluate/orchestrator.py) | ตรวจสอบแนวโน้ม M1, M5, M15 |
| **11** | Volatility Regime Gate | Part 2 | [`orchestrator.py`](file:///e:/FINALBOT_Begin/data_evaluate/orchestrator.py) | ระบุสภาวะความผันผวนตลาด |
| **12** | Trap & Fakeout Detection Gate | Part 2 | [`orchestrator.py`](file:///e:/FINALBOT_Begin/data_evaluate/orchestrator.py) | ตรวจจับกับดักราคา Bull/Bear |
| **13** | Divergence Analyzer Gate | Part 2 | [`divergence_analyzer.py`](file:///e:/FINALBOT_Begin/data_evaluate/orchestration/advanced_tools/divergence_analyzer.py) | ยืนยันสัญญาณกลับตัว RSI/MACD |
| **14** | Decision Layer Gate | Part 2 | [`orchestrator.py`](file:///e:/FINALBOT_Begin/data_evaluate/orchestrator.py) | สังเคราะห์ความพร้อมตลาด 4 มิติ |
| **15** | 100-Line Prompt Contract | Part 2 | [`orchestrator.py`](file:///e:/FINALBOT_Begin/data_evaluate/orchestrator.py) | ส่งออกไฟล์ .txt ขนาด 100 บรรทัด |
| **16** | Pre-Trade Money Manager Gate | Part 3 | [`money_manager.py`](file:///e:/FINALBOT_Begin/data_trade/execution_gate/money_manager.py) | ตรวจสอบความปลอดภัยของเงินทุน |
| **17** | AI Dispatch & Fallback Gate | Part 3 | [`gemini_bridge.py`](file:///e:/FINALBOT_Begin/data_trade/ai_analysis/gemini_bridge.py) | ยิงวิเคราะห์และรับผลลัพธ์ JSON |
| **18** | Action Resolution Gate | Part 3 | [`system_prompt.py`](file:///e:/FINALBOT_Begin/data_trade/ai_analysis/system_prompt.py) | จัดกลุ่ม Action: CALL / PUT / WAIT |
| **19** | Expiry Duration Gate | Part 3 | [`system_prompt.py`](file:///e:/FINALBOT_Begin/data_trade/ai_analysis/system_prompt.py) | ล็อกอายุสัญญา 1 - 5 นาที |
| **20** | Confidence Score Bounding Gate | Part 3 | [`system_prompt.py`](file:///e:/FINALBOT_Begin/data_trade/ai_analysis/system_prompt.py) | ล็อกคะแนนความมั่นใจ 0 - 100% |
| **21** | The Ultimate Execution Gate | Part 3 | [`gate_controller.py`](file:///e:/FINALBOT_Begin/data_trade/execution_gate/gate_controller.py) | **อนุมัติยิงออเดอร์ (คะแนน >= 60%)** |
| **22** | Binary/Turbo Execution Route | Part 3 | [`broker_executor.py`](file:///e:/FINALBOT_Begin/data_trade/execution_gate/broker_executor.py) | ยิงออเดอร์ Binary เข้า IQ Option |
| **23** | Digital Options V2 Fallback | Part 3 | [`broker_executor.py`](file:///e:/FINALBOT_Begin/data_trade/execution_gate/broker_executor.py) | ยิงออเดอร์ Digital สำรอง |
| **24** | Order Settlement & Tracking Gate | Part 3 | [`order_tracker.py`](file:///e:/FINALBOT_Begin/data_trade/execution_gate/order_tracker.py) | ติดตามผลออเดอร์และบันทึกสถิติ |

---
*เอกสารนี้จัดทำและรวบรวมโดย เอเธน่า (Athena AI Secretary) สำหรับระบบ FINALBOT*
