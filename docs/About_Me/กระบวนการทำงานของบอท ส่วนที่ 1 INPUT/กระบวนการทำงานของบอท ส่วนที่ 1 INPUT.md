# 📊 FINALBOT - กระบวนการทำงานของบอท ส่วนที่ 1: INPUT (Data Feed)

## 🎯 ทำความเข้าใจได้ทันที

บอท FINALBOT มีระบบ **Data Feed** ที่ดึงข้อมูลตลาดแบบเรียลไทม์จาก **IQ Option** และนำเข้าสู่ระบบตรวจสอบและวิเคราะห์ โดยมีการประมวลผลข้อมูลแบบ **Real-time (ทันที)** และบันทึกข้อมูลแบบ **Async (ไม่บล็อกหลัก)** ลงดิสก์ และใช้สถาปัตยกรรม **Zero RAM Data Leakage 100%** โดย Part 1 (`data_feed`) ตัดการส่งผ่าน Dictionary หรือ Payload ข้อมูลราคาทาง RAM ข้ามไปหา Part 2 (`data_evaluate`) เด็ดขาด เมธอด `data_adapter.update()` จะคืนค่าเฉพาะสตริง `symbol` เท่านั้น และส่วนงานที่ 2 อ่านไฟล์ CSV จากดิสก์ด้วยตัวเอง

---

## 🚨 กฎการทำงานของบอท ที่ AI ต้องทำตาม (Fail-Fast & Zero Tolerance)
- **ห้ามมีระบบ Fallback โดยเด็ดขาด**: หากระบบทำงานผิดพลาด ให้ระเบิด Error (raise Exception/ValueError/RuntimeError) หยุดทำงานทันทีแบบ Fail-Fast และบันทึกรายงานความผิดพลาดไว้ที่ `\all_filelogs\logs_datafeed` ระบบต้องมีเพียงหนึ่งเดียวที่ทำงานได้ถูกต้อง
- **ห้ามสร้างระบบ Mock**: การทดสอบต้องมาจากระบบจริง รันจริง 100%
- **Zero RAM Data Leakage**: ห้ามส่ง DataFrame หรือ Payload ข้อมูลราคาผ่าน RAM ระหว่าง Part 1 ไปยัง Part 2 เมธอด `update()` คืนค่าเฉพาะสตริง `symbol` เท่านั้น
- **เอกสารตรงตามจริง 100%**: หากเปลี่ยนแปลง แก้ไข โค้ดหรือสถาปัตยกรรม เอกสารนี้ต้องได้รับการอัปเดตตามซอร์สโค้ดจริงทุกครั้ง

---

## 🏗️ โครงสร้างระบบ Data Feed

### 11 ไฟล์ที่ทำงานร่วมกัน

```
Data Feed System = 11 ไฟล์ที่ทำงานร่วมกัน
├── iq_option_adapter.py      → ดึงข้อมูลจาก IQ Option API
├── data_adapter.py            → กลางคั่น ควบคุมการส่งข้อมูลทั้งหมด (👑 สำคัญที่สุด)
├── time_calendar_manager.py   → ศูนย์กลางบริหารจัดการเวลาและข่าวสารเศรษฐกิจประจำวัน (⏰)
├── timeframe_sync.py          → ประสาน timeframe M1, M5, M15 (มีโครงสร้างแต่ไม่ได้เรียกใช้งานจริง)
├── candle_validator.py        → ตรวจสอบคุณภาพข้อมูลตามเกณฑ์ราคาและปริมาณ
├── csv_queue.py               → คิวงานเขียนไฟล์ (🚀 Non-blocking & Fail-Fast เมื่อคิวเกิน 1,000)
├── csv_writer.py              → เขียนข้อมูลลงดิสก์ (💾 Async) กรอง 8 คอลัมน์มาตรฐาน และ Atomic Replace
├── csv_manager.py             → จัดการโฟลเดอร์ ไฟล์ และการลบไฟล์เก่า (📁)
├── data_monitor.py            → เฝ้าระวังระบบและความพร้อมใช้งานตลอดเวลา
├── data_source.py             → ตัวจัดการหลัก (Abstract)
└── anomaly_detector.py        → ตรวจสอบความผิดปกติของราคาระหว่างรันบอท
```

### ควบคุมการส่งข้อมูลอยู่ที่ไหน?

**👑 DataAdapter (data_adapter.py) = สมองกลางควบคุมทั้งหมด**

DataAdapter ทำหน้าที่:
1. รับข้อมูลจาก IQ Option API
2. เก็บข้อมูลแท่งเทียนชั่วคราวใน **RAM Storage Internal** (`_store_m1`, `_store_m5`, `_store_m15`)
3. ประมวลผลข้อมูล (Validation, Anomaly Detection, คำนวณ `age` และ `quality`)
4. ส่งข้อมูลให้ **csv_queue.py** เพื่อเขียนลงดิสก์แบบ Non-blocking
5. **คืนค่าเฉพาะสตริง `symbol`** (ไม่มีการส่ง Payload ราคาทาง RAM ไปยัง Part 2)
6. เฝ้าระวังประสิทธิภาพระบบผ่าน `data_monitor.py`

**RAM Storage (Internal DataAdapter):**
```python
_store_m1 = {symbol: DataFrame}   # แท่ง 1 นาที (100 แท่ง)
_store_m5 = {symbol: DataFrame}   # แท่ง 5 นาที (250 แท่ง)
_store_m15 = {symbol: DataFrame}  # แท่ง 15 นาที (50 แท่ง)
```

---

## 🛡️ กลไก Fail-Fast (Strict Zero Fallback)

ระบบ FINALBOT บังคับใช้เกณฑ์ **Fail-Fast** อย่างเคร่งครัดในทุกจุด หากเกิดเงื่อนไขที่ผิดปกติจะหยุดการทำงานทันทีโดยไม่มี Silent Fallback หรือ Retry ซ้ำแบบสุ่มเสี่ยง:

### 1. `config_loader.get_symbols()`
หากไม่มีคีย์ `symbols` หรือคีย์เป็นค่าว่างใน `settings.json` ระบบจะระเบิด `ValueError` สั่งหยุดบอททันที (ไม่มี Default Symbol Fallback):
```python
# config_setting/config_loader.py
def get_symbols() -> list[str]:
    symbols = load_settings(reload=True).get("symbols")
    if not symbols or not isinstance(symbols, list):
        raise ValueError("FAIL-FAST: Missing or empty 'symbols' array in config_setting/settings.json")
    return list(symbols)
```

### 2. `TimeCalendarManager.ensure_calendar_news()` (News Auto-Update Startup)
หากการตรวจสอบหรือการดาวน์โหลดตารางข่าวเศรษฐกิจประจำวันด้วย `calendar_news.py` เกิดความผิดพลาด ระบบจะบันทึก Full Stack Trace และระเบิด `RuntimeError` หยุดการรันบอททันที:
```python
# data_feed/time_calendar_manager.py
try:
    ...
    subprocess.run([sys.executable, script_path], check=True, timeout=60)
except Exception as e:
    logger.exception("Failed to check or run calendar_news.py at startup")
    raise RuntimeError(f"FAIL-FAST: Failed to execute calendar_news.py: {e}") from e
```

### 3. `TimeCalendarManager.sync_server_time()` (Server Time Sync)
หากการยิงขอเวลาเซิร์ฟเวอร์โบรกเกอร์ล้มเหลว หรือ `api` เป็น None ระบบจะบันทึก Exception และระเบิด `RuntimeError` สั่งหยุดบอททันที (ไม่มี Fallback `time_offset = 0.0`):
```python
# data_feed/time_calendar_manager.py
try:
    server_time = self.data_adapter.api.get_server_timestamp()
    if server_time is None:
        raise ValueError("get_server_timestamp returned None")
    local_time = int(time.time())
    self.time_offset = server_time - local_time
except Exception as e:
    logger.exception("Failed to get server time offset")
    raise RuntimeError("FAIL-FAST: Failed to get server time offset from broker") from e
```

### 4. `csv_queue.py` Queue Overflow Check
หากคิวงานเขียน CSV สะสมเกิน `max_queue_size` (1,000 รายการ) ระบบจะระเบิด `RuntimeError` สั่งหยุดการทำงานทันที (ไม่มี Silent Drop Write):
```python
# data_feed/csv_queue.py
def enqueue_write(self, df: pd.DataFrame, file_path: str) -> None:
    if df is not None and not df.empty:
        if self._queue.qsize() >= self.max_queue_size:
            raise RuntimeError(f"FAIL-FAST: CSVQueue size exceeded max limit ({self.max_queue_size}) - write blocked for {file_path}")
        
        self._queue.put((df.copy(), file_path))
```

### 5. `candle_validator.py` & `anomaly_detector.py` Data Quality Check
หากพบแท่งเทียนขาดคอลัมน์สำคัญ, มีค่า NaN ในราคา, ปริมาณ Volume = 0 สำหรับคู่อัตราแลกเปลี่ยนปกติ (Non-OTC), หรือราคาหลุดกรอบปกติ/กระโดดผิดปกติ ระบบจะระเบิด `ValueError` สั่งหยุดการประมวลผลแท่งเทียนทันที:
```python
# data_feed/candle_validator.py
if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")
if df[["open", "close", "high", "low"]].isnull().any().any():
    raise ValueError(f"NaN values found in prices")
```

### 6. `runner.py` CSV Read Fail-Fast
หากการอ่านไฟล์ CSV ของคู่เงินใดในดิสก์ล้มเหลว ระบบจะบันทึก Exception และระเบิด `RuntimeError` หยุดทันที:
```python
# runner.py
except Exception as e:
    logger.exception(f"Failed to read latest price from CSV for {symbol}")
    raise RuntimeError(f"FAIL-FAST: Failed to read latest price from CSV for {symbol}") from e
```

---

## 📋 กลไก Centralized System Logging & Full Stack Trace Recording

ระบบ Data Feed และ Runner ทั้งหมดถูกเชื่อมต่อผ่าน `setup_logging()` จาก `monitoring/console_dashboard.py` โดยมีกลไกเฝ้าระวังความล้มเหลวดังนี้:

1. **ตำแหน่งจัดเก็บไฟล์ Log**:
   ระบบจะบันทึก Log ลงดิสก์อัตโนมัติตามรูปแบบชื่อไฟล์:
   `all_filelogs/system_logs/bot_YYYYMMDD_HHMMSS.log` (รูปแบบเวลา UTC / Local)
2. **การบันทึก Full Stack Trace 100% (No Error Hiding)**:
   เมื่อเกิดความผิดพลาดใดๆ ในชั้น Data Feed หรือ Runner ระบบจะใช้ `logger.exception(...)` หรือ `traceback.print_exc()` เสมอ ซึ่งจะทำการ Write ข้อมูลรายละเอียดของ Error และ Stack Trace บรรทัดต่อบรรทัดลงในไฟล์ `bot_YYYYMMDD_HHMMSS.log` ก่อนระเบิด Exception เพื่อสั่งหยุดบอท (Fail-Fast)
3. **การทำงานร่วมกับ Thread Safety**:
   `console_dashboard.py` มีการใช้ `SafeStreamWrapper` และ `_PRINT_LOCK` เพื่อป้องกันความล้มเหลวจากการเขียนข้อความออกหน้าจอ คอนโซล และรับประกันว่าทุก Log Message และ Error Exception จะถูก flush ลงไฟล์ `bot_YYYYMMDD_HHMMSS.log` อย่างสมบูรณ์แบบเสมอ

---

## 🔒 กลไก Zero RAM Data Leakage (100% Disk-Based Transfer)

เพื่อป้องกันปัญหา Data Leakage และ Memory Bloat ข้าม Module ระหว่าง Part 1 (Data Feed) และ Part 2 (Data Evaluate):

1. **Part 1 ตัดการส่ง DataPayload ข้าม RAM**:
   เมธอด `DataAdapter.update(symbol, broker_epoch)` จะคืนค่าเฉพาะสตริงชื่อคู่เงิน `symbol` เท่านั้น:
   ```python
   # data_feed/data_adapter.py
   def update(self, symbol: str, broker_epoch: float) -> str:
       ...
       # Return only symbol string on successful write queuing
       return symbol
   ```

2. **Part 2 อ่านข้อมูลจากดิสก์ (CSV) เท่านั้น**:
   ใน `runner.py` และ `Orchestrator` จะบังคับอ่านข้อมูลราคาจากไฟล์ CSV บนดิสก์ผ่าน `read_csv_safe()` เท่านั้น:
   ```python
   # runner.py
   prices_dict[sym] = self._get_latest_price_from_csv(sym)
   self.orchestrator.process_cycle(sym)  # Orchestrator อ่าน CSV จากดิสก์ด้วยตัวเอง
   ```

---

## 📁 โครงสร้างไฟล์ CSV 8 คอลัมน์มาตรฐาน

ไฟล์ CSV ที่ถูกจัดเก็บบนดิสก์จะได้รับการจัดระเบียบให้มี **8 คอลัมน์มาตรฐาน** อย่างเคร่งครัด:

### รายชื่อคอลัมน์มาตรฐาน (Standard CSV Columns)
```csv
timestamp, open, high, low, close, volume, age, quality
```

| คอลัมน์ | ประเภทข้อมูล | คำอธิบาย |
|---------|-------------|----------|
| `timestamp` | String (Index) | เวลาเริ่มต้นแท่งเทียน รูปแบบ `%Y-%m-%d %H:%M:%S` |
| `open` | Float (6 decimals) | ราคาเปิดแท่งเทียน |
| `high` | Float (6 decimals) | ราคาสูงสุดแท่งเทียน |
| `low` | Float (6 decimals) | ราคาต่ำสุดแท่งเทียน |
| `close` | Float (6 decimals) | ราคาปิดแท่งเทียน |
| `volume` | Float/Int (6 decimals) | ปริมาณการซื้อขาย |
| `age` | Integer | อายุความล่าช้า คิดเป็น **มิลลิวินาที (ms)** จากเวลาปิดแท่งเทียนจริง |
| `quality` | String | สถานะประเมินความสดใหม่ของข้อมูล (`FRESH` หรือ `STALE`) |

### การคำนวณ `age` และ `quality`

การคำนวณถูกประมวลผลผ่าน `DataAdapter._add_age_and_quality()` ก่อนส่งเขียนดิสก์:

1. **สูตรการคำนวณเวลาปิดแท่งเทียนจริง ($T_{close}$)**:
   $$T_{close} = T_{start} + \text{tf\_seconds}$$
   *(โดย $\text{tf\_seconds}$: M1 = 60, M5 = 300, M15 = 900)*

2. **สูตรการคำนวณอายุความล่าช้า ($\text{age\_ms}$)**:
   $$\text{age\_ms} = \max\left(0, (T_{now} - T_{close}) \times 1000\right)$$

3. **เกณฑ์การประเมินสถานะ `quality`**:
   $$\text{threshold\_ms} = 2 \times \text{tf\_seconds} \times 1000$$
   - หาก $\text{age\_ms} \le \text{threshold\_ms} \implies \text{quality} = \text{'FRESH'}$
   - หาก $\text{age\_ms} > \text{threshold\_ms} \implies \text{quality} = \text{'STALE'}$

   *ตัวอย่าง Threshold*:
   - **M1**: Threshold = $2 \times 60 \times 1000 = 120,000 \text{ ms}$ (2 นาที)
   - **M5**: Threshold = $2 \times 300 \times 1000 = 600,000 \text{ ms}$ (10 นาที)
   - **M15**: Threshold = $2 \times 900 \times 1000 = 1,800,000 \text{ ms}$ (30 นาที)

```python
# data_feed/data_adapter.py - การคำนวณ age และ quality
@staticmethod
def _add_age_and_quality(df: pd.DataFrame, now_naive: datetime, tf_seconds: int) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    df_copy = df.copy()
    now_epoch = now_naive.replace(tzinfo=timezone.utc).timestamp() if now_naive.tzinfo is None else now_naive.timestamp()

    dt_index = pd.to_datetime(df_copy.index, utc=True)
    start_epochs = np.array([ts.timestamp() for ts in dt_index])

    close_epochs = start_epochs + tf_seconds
    age_ms_array = np.maximum(0, ((now_epoch - close_epochs) * 1000)).astype(int)

    threshold_ms = tf_seconds * 2 * 1000
    quality_array = np.where(age_ms_array <= threshold_ms, 'FRESH', 'STALE')

    df_copy['age'] = age_ms_array
    df_copy['quality'] = quality_array
    return df_copy
```

### ตัวอย่างเนื้อหาไฟล์ CSV จริง
```csv
timestamp,open,high,low,close,volume,age,quality
2026-07-28 14:20:00,1.085210,1.085430,1.085150,1.085380,142,21500,FRESH
2026-07-28 14:21:00,1.085380,1.085500,1.085300,1.085450,158,1500,FRESH
```

---

## 🔄 ขั้นตอนการทำงานแบบละเอียด (Pipeline)

### **Step 0: ตรวจสอบและดาวน์โหลดข่าวเศรษฐกิจประจำวันอัตโนมัติ (News Auto-Update on Startup)** ⬇️

**ไฟล์:** `TimeCalendarManager` (`data_feed/time_calendar_manager.py`) + `runner.py` + `calendar_news.py`

#### **0.1 การตรวจสอบและดาวน์โหลดตารางข่าวประจำวัน**
- **การทริกเกอร์:** เมื่อเปิดรันบอทครั้งแรกของวัน (`PureAIRunner.__init__()` ใน `runner.py`) ระบบจะเรียกใช้งาน `TimeCalendarManager` (`data_feed/time_calendar_manager.py`) ซึ่งจะบริหารจัดการและเรียกเมธอด `ensure_calendar_news()` ทันทีเพื่อเตรียมความพร้อมข้อมูลข่าวสารก่อนเริ่มกระบวนการ Data Feed
- **การเช็กไฟล์ข่าว:** `TimeCalendarManager` จะเข้าไปเช็กการมีอยู่ของไฟล์ข่าวประจำวันที่ตำแหน่ง:
  `all_filelogs/calendar_logs/calendar_YYYY-MM-DD.json`
- **การดาวน์โหลดอัตโนมัติ:**
  - หากพบว่า **ยังไม่มีไฟล์ข่าวประจำวันนี้** ระบบจะรันสคริปต์ `calendar_news.py` อัตโนมัติทันทีผ่าน `subprocess.run()` เพื่อดึงตารางข่าวเศรษฐกิจประจำวันจากแหล่งข้อมูลข่าวสารมาจัดเก็บลงไฟล์ `calendar_YYYY-MM-DD.json` ไว้ใช้ประเมินความเสี่ยงข่าวนอกตลาด (News Risk Assessment)
  - หากพบว่า **มีไฟล์ข่าวประจำวันนี้แล้ว** ระบบจะข้ามขั้นตอนการดาวน์โหลดและโหลดไฟล์ที่มีอยู่ขึ้นมาใช้งานทันที

---

### **Step 1: รับข้อมูลจาก IQ Option** ⬇️

**ไฟล์:** `iq_option_adapter.py`

#### **1.1 การเริ่มต้นระบบ (Warm-up)**
```python
# data_adapter.py Line 126-128
m1 = self._iq.get_candles(symbol, 'M1', 100)     # ดึง 100 แท่ง M1
m5 = self._iq.get_candles(symbol, 'M5', 250)     # ดึง 250 แท่ง M5
m15 = self._iq.get_candles(symbol, 'M15', 50)    # ดึง 50 แท่ง M15 จาก Broker API สด 100%
```

#### **1.2 การอัปเดตข้อมูลสดแยกตาม Timeframe (Update Cycle Logic)**
การดึงข้อมูลสดและการอัปเดตไฟล์ CSV จะแยกตามรอบเวลา (Timeframe) เพื่อลดภาระการสื่อสารกับโบรกเกอร์ (Broker API Overhead):

- **M1 (1 นาที):** ยิงดึงข้อมูลสด 3 แท่งใหม่ (`get_candles(symbol, 'M1', 3)`) และอัปเดตไฟล์ `M1.csv` **ทุกๆ 1 นาที**
- **M5 (5 นาที):** ยิงดึงข้อมูลสด 3 แท่งใหม่ (`get_candles(symbol, 'M5', 3)`) และอัปเดตไฟล์ `M5.csv` **เฉพาะเมื่อมีการเปลี่ยนบล็อกนาที (`current_block_m5 != _last_block_m5`)**
- **M15 (15 นาที):** ยิงดึงข้อมูลสด 3 แท่งใหม่ (`get_candles(symbol, 'M15', 3)`) และอัปเดตไฟล์ `M15.csv` **เฉพาะเมื่อมีการเปลี่ยนบล็อกนาที (`current_block_m15 != _last_block_m15`)**

#### **1.3 Configuration สำคัญ**
```python
# iq_option_adapter.py
_TF_SECONDS = {
    'M1': 60,      # 1 นาที
    'M5': 300,     # 5 นาที
    'M15': 900,    # 15 นาที
    'M30': 1800,   # 30 นาที
    'M60': 3600,   # 60 นาที
    'H1': 3600,    # 1 ชั่วโมง
    'H4': 14400,   # 4 ชั่วโมง
    'D1': 86400,   # 1 วัน
}

# data_adapter.py
default_candle_count = 250    # ดึง 250 แท่งเริ่มต้น
min_candle_count = 21         # ต้องมีอย่างน้อย 21 แท่ง
m5_seconds = 300              # 5 นาที
m15_seconds = 900             # 15 นาที
```

#### **1.4 ระบบซิงค์เวลาเซิร์ฟเวอร์แบบ Real-time (Server Time Sync & Fail-Fast)**
- **การบริหารจัดการแบบรวมศูนย์:** การซิงค์เวลาและการคำนวณ `time_offset` ถูกบริหารจัดการผ่าน `TimeCalendarManager` (`data_feed/time_calendar_manager.py`) เป็นศูนย์กลาง
- **Daemon Thread (`TimeSyncThread`):** `TimeCalendarManager.start_time_sync_thread()` จะเริ่มเปิด Daemon Thread เบื้องหลังเพื่อซิงค์เวลาผ่าน `sync_server_time()` และคำนวณ `self.time_offset = server_time - local_time` ใหม่โดยอัตโนมัติใน **ทุกๆ วินาทีที่ 30** (`:30`) ของทุกนาที
- **Fail-Fast การซิงค์เวลา:** หากไม่สามารถขอเวลาเซิร์ฟเวอร์จากโบรกเกอร์ได้เมื่อเริ่มรันบอท `TimeCalendarManager.sync_server_time()` จะระเบิด `RuntimeError("FAIL-FAST: Failed to get server time offset from broker")` หยุดทำงานทันที (ไม่มี Fallback `time_offset = 0.0`)
- **Dynamic Broker Epoch:** ในขั้นตอนการอัปเดตข้อมูล `fetch_and_save_data()` จะดึง `broker_epoch` ผ่าน `self.time_calendar_mgr.get_broker_epoch()` (หรือคำนวณ `time.time() + self.time_calendar_mgr.time_offset`) ส่งไปยัง `DataAdapter.update()` เพื่อให้การคำนวณช่วงเวลาและการแบ่งบล็อก M5/M15 ตรงกับเวลาเซิร์ฟเวอร์โบรกเกอร์ 100%

---

### **Step 2: บันทึกลง RAM Storage (Internal DataAdapter)** ⬇️

**ไฟล์:** `data_adapter.py`

```python
# data_adapter.py
self._store_m1: Dict[str, Optional[pd.DataFrame]] = {}   # RAM Storage M1 Internal
self._store_m5: Dict[str, Optional[pd.DataFrame]] = {}   # RAM Storage M5 Internal
self._store_m15: Dict[str, Optional[pd.DataFrame]] = {}  # RAM Storage M15 Internal

self._store_m1[symbol] = m1        # เก็บ M1 ลง RAM ชั่วคราวภายใน DataAdapter
self._store_m5[symbol] = m5        # เก็บ M5 ลง RAM ชั่วคราวภายใน DataAdapter
self._store_m15[symbol] = m15      # เก็บ M15 ลง RAM ชั่วคราวภายใน DataAdapter
```

**ข้อดี:**
- ⚡ เข้าถึงได้เร็วในกระบวนการ internal processing (microseconds)
- 🚀 แยกขาด ไม่แชร์ RAM ไปยัง Part 2 (Zero RAM Data Leakage 100%)

---

### **Step 3: ตรวจสอบคุณภาพข้อมูล (Validation & Anomaly Detection)** ⬇️

**ไฟล์:** `candle_validator.py` + `anomaly_detector.py`

**Validation ทำทุกครั้ง:**
```python
# data_adapter.py
CandleValidator().validate(m1, symbol)      # เช็ค M1
CandleValidator().validate(m5, symbol)      # เช็ค M5
CandleValidator().validate(m15, symbol)     # เช็ค M15
```

**เกณฑ์ตรวจสอบ (CandleValidator):**
```python
# candle_validator.py
# 1. Check required columns (open, close, high, low, volume)
missing_cols = self.required_columns - set(df.columns)
if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")

# 2. Check for NaNs in price
if df[["open", "close", "high", "low"]].isnull().any().any():
    raise ValueError(f"NaN values found in prices")

# 3. Check volume (OTC ไม่ต้องตรวจ)
is_otc = "OTC" in symbol.upper()
if not is_otc and df["volume"].sum() == 0:
    raise ValueError(f"Volume is all zeros for non-OTC symbol")

# 4. Sanity check: price range
median_close = float(df["close"].median())
is_jpy = "JPY" in symbol.upper()
if is_otc:
    min_val, max_val = 0.3, 10.0
elif is_jpy:
    min_val, max_val = 50.0, 300.0
else:
    min_val, max_val = 0.3, 10.0

if not (min_val <= median_close <= max_val):
    raise ValueError(f"{symbol} median {median_close} out of range [{min_val}, {max_val}]")
```

**หากข้อมูลไม่ดี:**
- ระบบ **จะระเบิด** (raise ValueError / RuntimeError) หยุดระบบทันทีตามหลัก Fail-Fast

---

### **Step 4: ประสาน Timeframe & Merge Data** ⬇️

**ไฟล์:** `data_adapter.py`

#### **⚠️ ข้อควรรู้สำคัญ: M15 ไม่ Resample จาก M5**

```python
# data_adapter.py: ดึง M15 ตรงจาก Broker API (3 แท่งสำหรับการอัปเดต)
fresh_m15 = self._iq.get_candles(symbol, 'M15', 3)
```

#### **TimeframeSync สถานะปัจจุบัน:**
- `TimeframeSync` มี class ในไฟล์ `timeframe_sync.py` แต่ **ไม่ได้ถูกเรียกใช้จริง** ใน Data Pipeline หลัก
- M1, M5, M15 ดึงแยกกันและ merge แยกกันอย่างเป็นอิสระ

**Merge Data Logic:**
```python
# data_adapter.py
def _merge(self, stored, fresh, gap_threshold, refetch_fn, label, timeframe, max_candles=250):
    last_ts = stored.index[-1]
    first_ts = fresh.index[0]
    gap_sec = (first_ts - last_ts).total_seconds()

    if gap_sec > gap_threshold:
        # หากมีช่องว่าง > 5 นาที (M1) / 25 นาที (M5) / 75 นาที (M15)
        self._data_monitor.report_gap(label.split()[1], timeframe, gap_sec)
        full = refetch_fn()
        if full is not None and not full.empty:
            return full
        raise ValueError("Refetch failed after gap detection")

    combined = pd.concat([stored, fresh])
    combined = combined[~combined.index.duplicated(keep='last')].sort_index()
    return combined.tail(max_candles)
```

---

### **Step 5: ส่งข้อมูลไปคิวเขียน (Non-blocking & Fail-Fast Queue)** ⬇️

**ไฟล์:** `csv_queue.py`

```python
# data_adapter.py
self._csv_queue.enqueue_write(completed, self._csv_manager.get_file_path(symbol, "M1"))
self._csv_queue.enqueue_write(completed, self._csv_manager.get_file_path(symbol, "M5"))
self._csv_queue.enqueue_write(completed, self._csv_manager.get_file_path(symbol, "M15"))
```

**Queue Flow:**
```
DataAdapter (Internal RAM) → enqueue_write() → Queue (RAM) → Worker Thread → CSVWriter → CSV File
```

#### **Queue Implementation & Fail-Fast Check:**
```python
# csv_queue.py
class CSVQueue:
    def __init__(self, config=None):
        self.max_queue_size = config.get("max_queue_size", 1000)
        self.queue_timeout = config.get("queue_timeout", 30)
        self._queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def enqueue_write(self, df: pd.DataFrame, file_path: str) -> None:
        if df is not None and not df.empty:
            # Check queue size — Fail-Fast if full (No Silent Drop Write)
            if self._queue.qsize() >= self.max_queue_size:
                raise RuntimeError(f"FAIL-FAST: CSVQueue size exceeded max limit ({self.max_queue_size}) - write blocked for {file_path}")
            
            self._queue.put((df.copy(), file_path))
```

---

### **Step 6: เขียนข้อมูลลงดิสก์ (8 คอลัมน์มาตรฐาน & Atomic Replace)** ⬇️

**ไฟล์:** `csv_writer.py` + `csv_manager.py`

#### **Path Convention:**
```
data_base/csv/iq_option/{symbol}/{symbol}_{timeframe}.csv
```

**ตัวอย่าง:**
```
data_base/csv/iq_option/EURGBP/EURGBP_M5.csv
data_base/csv/iq_option/EURUSD-OTC/EURUSD-OTC_M1.csv
```

#### **csv_writer.py - Implementation Detail:**

```python
# csv_writer.py
class CSVWriter:
    def __init__(self, config=None):
        if config is None:
            from config_setting.config_loader import get_csv_writer_config
            config = get_csv_writer_config()

        self.encoding = config.get("encoding", "utf-8")
        self.date_format = config.get("date_format", "%Y-%m-%d %H:%M:%S")
        self.include_header = config.get("include_header", True)
        self.decimal_places = config.get("decimal_places", 6)

    def write(self, df: pd.DataFrame, file_path: str) -> None:
        if df is None or df.empty:
            raise ValueError(f"Cannot write empty dataframe to {file_path}")
            
        file_lock = get_file_lock(file_path)
        with file_lock:
            try:
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)

                df_to_write = df.copy()
                
                # Select ONLY standard 8 columns (open, high, low, close, volume, age, quality) + timestamp (index)
                cols = ['open', 'high', 'low', 'close', 'volume', 'age', 'quality']
                df_to_write = df_to_write[[c for c in cols if c in df_to_write.columns]]
                
                df_to_write.index = pd.to_datetime(df_to_write.index).strftime(self.date_format)
                
                # Round decimal places for numeric OHLCV columns to 6 places
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df_to_write.columns:
                        df_to_write[col] = df_to_write[col].round(self.decimal_places)
                
                # Read existing file if present, merge and deduplicate
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    existing_df = pd.read_csv(file_path, index_col=0, encoding=self.encoding)
                    existing_cols = [c for c in cols if c in existing_df.columns]
                    existing_df = existing_df[existing_cols]
                    
                    combined_df = pd.concat([existing_df, df_to_write])
                    combined_df = combined_df[~combined_df.index.duplicated(keep='last')].sort_index()
                    df_to_write = combined_df

                # Write to temporary file and replace atomically
                tmp_path = f"{file_path}.{threading.get_ident()}.tmp"
                df_to_write.to_csv(
                    path_or_buf=tmp_path,
                    encoding=self.encoding,
                    header=self.include_header,
                    index=True,
                    mode='w',
                    date_format=self.date_format
                )
                
                # Atomic Replace with Retry Backoff for Windows file locks
                max_retries = 5
                backoff_sec = 0.1
                for attempt in range(1, max_retries + 1):
                    try:
                        os.replace(tmp_path, file_path)
                        break
                    except Exception as e:
                        if attempt < max_retries:
                            time.sleep(backoff_sec)
                            backoff_sec *= 2
                        else:
                            if os.path.exists(tmp_path):
                                os.remove(tmp_path)
                            raise
            except Exception as e:
                logger.error(f"[CSVWriter] Failed to write to {file_path}: {e}")
                raise
```

**ข้อควรรู้สำคัญ:**
- คัดกรองและบันทึก **8 คอลัมน์มาตรฐาน** (`timestamp, open, high, low, close, volume, age, quality`)
- ปัดเศษทศนิยมราคาสุดท้ายที่ **6 ตำแหน่ง** (decimal_places=6)
- ทำงานผ่าน **Zero-Lock Architecture (Thread-Safe Atomic Write)** ร่วมกับ `get_file_lock`
- อ่านไฟล์เดิม ตัดเวลาซ้ำ (Deduplicate) เขียนลงไฟล์ชั่วคราว `.tmp` แล้วทำ `os.replace` สลับไฟล์อย่างปลอดภัย
- ป้องกันปัญหา `PermissionError [WinError 5]` บน Windows 100%

---

### **Step 7: เฝ้าระวังระบบ (Data Monitor & Health Check)** ⬇️

**ไฟล์:** `data_monitor.py`

**Metrics ที่ตรวจวัด:**
```python
# data_monitor.py
self.gap_thresholds = {
    "M1": 300,      # 5 นาที
    "M5": 1500,     # 25 นาที
    "M15": 4500     # 75 นาที
}

self.latency_thresholds = {
    "HIGH": 360000,      # 6 นาที
    "MEDIUM": 480000,    # 8 นาที
    "LOW": 600000,       # 10 นาที
    "STALE": 600000      # 10 นาที
}
```

#### **Fail-Fast Trigger Cases:**
- Gap > 5 นาที (M1) / 25 นาที (M5) / 75 นาที (M15) → ระเบิด RuntimeError หยุดระบบทันที
- Latency > 600,000ms (10 นาที) (STALE) → ระเบิด RuntimeError หยุดระบบทันที
- Queue > 1,000 รายการ → ระเบิด RuntimeError หยุดระบบทันที

---

## 🚀 Runner Loop จริง (PureAIRunner)

**ไฟล์:** `runner.py`

```python
def run_cycle(self):
    # 1. Ensure connection is active
    self.data_adapter.ensure_connected()

    # 2. Fetch and save data concurrently (writes CSV only)
    cycle_broker_epoch = time.time() + self.time_offset
    sym_futures = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.symbols)) as executor:
        for sym in self.symbols:
            sym_futures[sym] = executor.submit(self.fetch_and_save_data, sym, cycle_broker_epoch)
        concurrent.futures.wait(sym_futures.values())

    prices_dict = {}
    for sym in self.symbols:
        result_val = sym_futures[sym].result()
        if not result_val:
            continue

        if not self._check_warmup_data(sym):
            continue

        # 3. บังคับดึงข้อมูล OHLCV (ราคา) จากโฟลเดอร์เท่านั้น ห้ามส่งทาง RAM
        prices_dict[sym] = self._get_latest_price_from_csv(sym)

        # 4. Trigger Orchestrator without passing any data via RAM
        self.orchestrator.process_cycle(sym)
```

**ข้อควรรู้:**
- Loop ทำงานตรงตามวินาทีแรกของนาทีถัดไป (`sleep_sec = (1 - now.second) % 60`)
- `DataAdapter.update()` คืนค่าเฉพาะ `symbol: str`
- Part 2 ดึงราคาและข้อมูล OHLCV จาก CSV บนดิสก์ผ่าน `_get_latest_price_from_csv()` 100%

---

## 📊 ตารางสรุปขั้นตอนการทำงาน

| ขั้นตอน | ไฟล์ที่เกี่ยวข้อง | ทำอะไร | สถานะ / เกณฑ์ Fail-Fast |
|---------|-------------------|---------|--------------------------|
| 0. ข่าวเศรษฐกิจ | TimeCalendarManager (data_feed/time_calendar_manager.py) | เช็ก `calendar_YYYY-MM-DD.json` หากยังไม่มี จะรัน `calendar_news.py` อัตโนมัติ | ✅ Active |
| 1. รับข้อมูล & Sync เวลา | iq_option_adapter.py / TimeCalendarManager | ดึง 3 แท่งใหม่จาก IQ Option API และซิงค์เวลาโบรกเกอร์ผ่าน TimeCalendarManager | ✅ Fail-Fast หากขอเวลาไม่สำเร็จ |
| 2. เก็บ RAM Internal | data_adapter.py | บันทึกในหน่วยความจำ RAM ชั่วคราวภายใน DataAdapter เท่านั้น | ✅ Active (Zero RAM Leakage) |
| 3. Validate & Detect | candle_validator.py / anomaly_detector.py | ตรวจสอบคุณภาพและหาความผิดปกติของข้อมูล | ✅ Fail-Fast หากพบข้อมูลเสีย |
| 4. Timeframe & Merge | data_adapter.py | Merge + Drop forming (M1, M5, M15) | ✅ Active (M15 ไม่ resample) |
| 5. Enqueue Write | csv_queue.py | ส่งไปคิวเขียน CSV แบบ Non-blocking | ✅ Fail-Fast หากคิวเกิน 1,000 |
| 6. Write CSV | csv_writer.py + csv_manager.py | เขียน 8 คอลัมน์ลงดิสก์ (Async & Atomic replace) | ✅ Active (decimal_places=6) |
| 7. Monitor | data_monitor.py | เฝ้าระวังระบบ latency/gap/queue | ✅ Fail-Fast เมื่อเกินเกณฑ์ |

---

## ⚙️ ค่า Configuration สำคัญ (`settings.json` & `datafeed_config.json`)

### ไฟล์: `datafeed_config.json`

```json
{
  "data_feed": {
    "iq_option_adapter": {
      "account_type": "PRACTICE",
      "timeout_sec": 8,
      "max_workers": 10,
      "connection_retries": 0
    },
    "data_adapter": {
      "default_candle_count": 250,
      "min_candle_count": 21,
      "m5_seconds": 300,
      "m15_seconds": 900,
      "enable_cache": true,
      "cache_size": 1000
    },
    "csv_queue": {
      "max_workers": 1,
      "queue_timeout": 30,
      "max_queue_size": 1000
    },
    "csv_writer": {
      "encoding": "utf-8",
      "decimal_places": 6,
      "include_header": true,
      "date_format": "%Y-%m-%d %H:%M:%S"
    },
    "csv_manager": {
      "base_dir": "data_base/csv/iq_option",
      "naming_convention": "{symbol}_{timeframe}.csv",
      "auto_create_dirs": true,
      "file_permissions": "rw-r--r--"
    },
    "data_monitor": {
      "gap_thresholds": {
        "M1": 300,
        "M5": 1500,
        "M15": 4500
      },
      "latency_thresholds": {
        "HIGH": 360000,
        "MEDIUM": 480000,
        "LOW": 600000,
        "STALE": 600000
      },
      "error_threshold": 10
    }
  }
}
```

---

## 🚨 Error Handling & Fail-Fast Summary

| ปัญหา | เกิดจากอะไร | การตอบสนองตามเกณฑ์ Fail-Fast |
|-------|-------------|----------------------------------|
| **Missing Symbols Key** | คีย์ `symbols` ไม่มีใน `settings.json` | ระเบิด `ValueError` → หยุดระบบทันที (ไม่มี Fallback) |
| **Server Time Sync Failed** | ยิงขอเวลาเซิร์ฟเวอร์จากโบรกเกอร์ล้มเหลว | ระเบิด `RuntimeError` → หยุดระบบทันที (ไม่มี Fallback `time_offset=0`) |
| **Queue Overflow** | คิวงานเขียนไฟล์ > 1,000 รายการ | ระเบิด `RuntimeError` → หยุดระบบทันที (ไม่มี Silent Drop Write) |
| **Data Gap** | มีช่องว่าง > 5 นาที (M1) / 25 นาที (M5) / 75 นาที (M15) | ระเบิด `RuntimeError` → หยุดระบบทันที |
| **Latency Stale** | ข้อมูลช้าเกิน 10 นาที (age > 600,000ms) | ระเบิด `RuntimeError` → หยุดระบบทันที |
| **Invalid Data** | พบ NaN, Volume=0 (Non-OTC), Price out of range | ระเบิด `ValueError` → หยุดระบบทันที |

---

## 🎯 สรุปสั้นๆ

**FINALBOT Data Feed ทำงานดังนี้:**

0. ✅ **ข่าวเศรษฐกิจ**: ตรวจสอบและดาวน์โหลดข่าวเศรษฐกิจประจำวันอัตโนมัติผ่าน `TimeCalendarManager` (`data_feed/time_calendar_manager.py`) เมื่อเริ่มรันบอท
1. ✅ **Fail-Fast Settings & Time**: ตรวจเช็ก `symbols` และขอเวลาโบรกเกอร์ผ่าน `TimeCalendarManager` หากพลาดสั่งระเบิดหยุดบอททันที
2. ✅ **ดึงข้อมูล IQ Option**: ดึง 3 แท่งใหม่ เข้าสู่ RAM Storage ชั่วคราวภายใน `DataAdapter`
3. ✅ **Validate & Age/Quality**: ตรวจสอบคุณภาพข้อมูล และคำนวณ 8 คอลัมน์มาตรฐาน (`age` ms, `quality` FRESH/STALE)
4. ✅ **Zero RAM Data Leakage**: `DataAdapter.update()` คืนค่าเฉพาะสตริง `symbol` ตัดการส่งข้อมูลราคาข้าม RAM ไป Part 2 100%
5. ✅ **Non-blocking CSV Queue**: ส่งงานเขียนลงดิสก์ หากคิวสะสมเกิน 1,000 รายการสั่ง Fail-Fast หยุดระบบทันที
6. ✅ **Atomic CSV Writer**: เขียนไฟล์ลงดิสก์ 8 คอลัมน์มาตรฐาน ทศนิยม 6 ตำแหน่ง ด้วย Atomic Replace และ Per-File Thread Lock
7. ✅ **Disk Read Part 2**: Part 2 (`data_evaluate`) อ่านข้อมูลราคาจากไฟล์ CSV บนดิสก์ด้วยตัวเอง

---

**สร้างเมื่อ:** 2026-07-18  
**อัปเดตล่าสุด:** 2026-07-28  
**สถานะ:** ✅ ใช้งานได้เต็มรูปแบบ (ตรงตามซอร์สโค้ดจริง 100%)  
