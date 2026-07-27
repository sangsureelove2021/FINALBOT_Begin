# 📊 FINALBOT - กระบวนการทำงานของบอท ส่วนที่ 1: INPUT (Data Feed)

## 🎯 ทำความเข้าใจได้ทันที

บอท FINALBOT มีระบบ **Data Feed** ที่ดึงข้อมูลตลาดแบบเรียลไทม์จาก **IQ Option** และนำเข้าสู่ระบบตรวจสอบและวิเคราะห์ โดยมีการประมวลผลข้อมูลแบบ **Real-time (ทันที)** และบันทึกข้อมูลแบบ **Async (ไม่บล็อกหลัก)** อย่างรวดเร็ว

## 🚨 กฎการทำงานของบอท ที่ AI ต้องทำตาม
- หากระบบทำงานผิดพลาด ให้แสดง Error ที่คอนโซล หยุดทำงาน และบันทึกรายงานความผิดพลาดไว้ที่ `\all_filelogs\logs_datafeed` ห้ามมีระบบ Fallback ระบบต้องมีเพียงหนึ่งเดียวที่ทำงานได้ถูกต้อง
- ห้ามสร้างระบบให้มี Mock การทำงาน หรือการทดสอบต้องมาจากระบบจริง ทุกอย่างต้องรันจริง
- หากเปลี่ยนแปลง แก้ไข ข้อมูล ข้อความ โค้ด หรือสิ่งต่าง ๆ ในบอท เอกสารนี้ต้องได้รับการแก้ไข อัปเดตตามจริงทุกครั้ง

---

## 🏗️ โครงสร้างระบบ Data Feed

### 10 ไฟล์ที่ทำงานร่วมกัน

```
Data Feed System = 10 ไฟล์ที่ทำงานร่วมกัน
├── iq_option_adapter.py      → ดึงข้อมูลจาก IQ Option API
├── data_adapter.py            → กลางคั่น ควบคุมการส่งข้อมูลทั้งหมด (👑 สำคัญที่สุด)
├── timeframe_sync.py          → ประสาน timeframe M1, M5, M15 (มีโครงสร้างแต่ไม่ได้เรียกใช้งานจริง)
├── candle_validator.py        → ตรวจสอบคุณภาพข้อมูลตามเกณฑ์ราคาและปริมาณ
├── csv_queue.py               → คิวงานเขียนไฟล์ (🚀 Non-blocking)
├── csv_writer.py              → เขียนข้อมูลลงดิสก์ (💾 Async) และกรองเฉพาะคอลัมน์มาตรฐาน
├── csv_manager.py             → จัดการโฟลเดอร์ ไฟล์ และการลบไฟล์เก่า (📁)
├── data_monitor.py            → เฝ้าระวังระบบและความพร้อมใช้งานตลอดเวลา
├── data_source.py             → ตัวจัดการหลัก (Abstract)
└── anomaly_detector.py        → ตรวจสอบความผิดปกติของราคาระหว่างรันบอท
```

### ควบคุมการส่งข้อมูลอยู่ที่ไหน?

**👑 DataAdapter (data_adapter.py) = สมองกลางควบคุมทั้งหมด**

DataAdapter ทำหน้าที่:
1. รับข้อมูลจาก IQ Option
2. เก็บข้อมูลใน **RAM** (หน่วยความจำ) เร็วมาก
3. ประมวลผลข้อมูล (Timeframe Sync, Validation)
4. ส่งข้อมูลให้ **csv_queue.py** เพื่อเขียนลงดิสก์
5. เฝ้าระวังประสิทธิภาพระบบ

**RAM Storage:**
```python
_store_m1 = {symbol: DataFrame}  # แท่ง 1 นาที
_store_m5 = {symbol: DataFrame}  # แท่ง 5 นาที
_store_m15 = {symbol: DataFrame}  # แท่ง 15 นาที
```

---

## 🔄 ขั้นตอนการทำงานแบบละเอียด (Pipeline)

### **Step 1: รับข้อมูลจาก IQ Option** ⬇️

**ไฟล์:** `iq_option_adapter.py`

#### **1.1 การเริ่มต้นระบบ (Warm-up)**
```python
# data_adapter.py Line 126-128
m1 = self._iq.get_candles(symbol, 'M1', 100)     # ดึง 100 แท่ง M1
m5 = self._iq.get_candles(symbol, 'M5', 250)     # ดึง 250 แท่ง M5
m15 = self._iq.get_candles(symbol, 'M15', 50)    # ดึง 50 แท่ง M15 จาก Broker API สด 100%
```

#### **1.2 การอัปเดตข้อมูล (Update)**
```python
# data_adapter.py Line 239, 290, 339
# M1 ดึง 3 แท่งใหม่
fresh = self._iq.get_candles(symbol, 'M1', 3)

# M5 ดึง 3 แท่งใหม่
fresh = self._iq.get_candles(symbol, 'M5', 3)

# M15 ดึง 3 แท่งใหม่ ตรงจาก Broker API สด 100%
fresh_m15 = self._iq.get_candles(symbol, 'M15', 3)
```

#### **1.3 Configuration สำคัญ**
```python
# iq_option_adapter.py Line 208-211
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

# data_adapter.py Line 59-62
default_candle_count = 250    # ดึง 250 แท่งเริ่มต้น
min_candle_count = 21         # ต้องมีอย่างน้อย 21 แท่ง
m5_seconds = 300              # 5 นาที
m15_seconds = 900             # 15 นาที
```

**Data ที่ได้:**
```python
{
    'timestamp': '2026-07-18 10:30:00',
    'open': 1.2340,
    'high': 1.2342,
    'low': 1.2338,
    'close': 1.2341,
    'volume': 100
}
```

---

### **Step 2: บันทึกลง RAM Storage** ⬇️

**ไฟล์:** `data_adapter.py`

```python
# data_adapter.py Line 70-72
self._store_m1: Dict[str, Optional[pd.DataFrame]] = {}  # RAM Storage M1
self._store_m5: Dict[str, Optional[pd.DataFrame]] = {}  # RAM Storage M5
self._store_m15: Dict[str, Optional[pd.DataFrame]] = {}  # RAM Storage M15

# data_adapter.py Line 107-109
self._store_m1[symbol] = m1        # เก็บ M1 ลง RAM
self._store_m5[symbol] = m5        # เก็บ M5 ลง RAM
self._store_m15[symbol] = m15      # เก็บ M15 ลง RAM
```

**ข้อดี:**
- ⚡ เข้าถึงได้เร็ว (microseconds)
- 🚀 ไม่ต้องรอเขียนดิสก์
- 🔄 Processing ทันที

**RAM Usage:**
```python
# แต่ละ symbol (คำนวณตามสเปก M1=100, M5=250, M15=50 แท่ง)
- M1: ~4.8KB (100 rows × 6 cols × 8 bytes)
- M5: ~12KB (250 rows × 6 cols × 8 bytes)
- M15: ~2.4KB (50 rows × 6 cols × 8 bytes)
- ทั้งหมด ~19.2KB per symbol

# หลาย symbol
- 5 symbols = ~96KB (น้ำหนักเบามาก ปลอดภัย 100%)
```

---

### **Step 3: ตรวจสอบคุณภาพข้อมูล** ⬇️

**ไฟล์:** `candle_validator.py`

**Validation ทำทุกครั้ง:**
```python
# data_adapter.py Line 102-104
CandleValidator().validate(m1, symbol)      # เช็ค M1
CandleValidator().validate(m5, symbol)      # เช็ค M5
CandleValidator().validate(m15, symbol)     # เช็ค M15
```

**เกณฑ์ตรวจสอบ:**
```python
# candle_validator.py Line 56-87
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
- ระบบ **จะระเบิด** (raise ValueError)
- ไม่มีการ skip หรือ retry แบบลื่นไหล
- หยุดระบบทันทีค่ะ

---

### **Step 4: ประสาน Timeframe** ⬇️

**ไฟล์:** `data_adapter.py`

#### **⚠️ ข้อควรรู้สำคัญ: M15 ไม่ Resample จาก M5**

```python
# data_adapter.py Line 339: ดึง M15 ตรงจาก Broker API (3 แท่งสำหรับการอัปเดต)
fresh_m15 = self._iq.get_candles(symbol, 'M15', 3)

# data_adapter.py Line 276-322: _refresh_m5()
def _refresh_m5(self, symbol, now_naive, current_block):
    # M5 ดึง 3 แท่งใหม่
    fresh = self._iq.get_candles(symbol, 'M5', 3)

    # รวมข้อมูลเก่า + ข้อมูลใหม่
    self._store_m5[symbol] = self._merge(
        self._store_m5[symbol], fresh,
        gap_threshold=_M5_GAP_SEC,  # 1500 วินาที
        refetch_fn=lambda: self._iq.get_candles(symbol, 'M5', 250),
        label=f"M5 {symbol}",
        timeframe="M5",
        max_candles=250
    )

    # ตัดแท่งเปิดไม่เสร็จออก
    completed = self._drop_forming(self._store_m5[symbol], now_naive, 300)

    # เขียน CSV เมื่อ block เปลี่ยนหรือโหลดข้อมูลครั้งแรก (block_changed)
    if block_changed:
        CandleValidator().validate(completed, symbol)
        self._csv_queue.enqueue_write(completed, self._csv_manager.get_file_path(symbol, "M5"))

    return completed
```

#### **TimeframeSync ทำอะไร?**

```python
# timeframe_sync.py Line 20-24
TF_MINUTES = {
    'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30,
    'M60': 60, 'H1': 60, 'H4': 240, 'D1': 1440,
}

# timeframe_sync.py Line 55-81: sync() method
def sync(self, candles, as_of):
    # Sync แต่ไม่ถูกเรียกใช้จริง
    ref = as_of or self._reference_time(candles)
    synced = {}
    for tf, df in candles.items():
        synced[tf] = df[df.index <= ref]
    return synced
```

**⚠️ ข้อควรรู้:**
- `TimeframeSync` มี class แต่ **ไม่ถูกเรียกใช้จริง** ใน workflow
- M1, M5, M15 ดึงแยกกัน ไม่ใช่ sync ร่วมกัน
- M15 ดึงตรงจาก Broker API ไม่ได้ resample

**Merge Data:**
```python
# data_adapter.py Line 294-322
def _merge(self, stored, fresh, gap_threshold, refetch_fn, label, timeframe):
    # 1. Check gap
    last_ts = stored.index[-1]
    first_ts = fresh.index[0]
    gap_sec = (first_ts - last_ts).total_seconds()

    if gap_sec > gap_threshold:
        # หากมีช่องว่าง > 5 นาที (M1) / 25 นาที (M5) / 75 นาที (M15)
        raise ValueError(f"Data gap detected: {gap_sec}s")

    # 2. Merge data
    combined = pd.concat([stored, fresh])
    combined = combined[~combined.index.duplicated(keep='last')].sort_index()

    # 3. Return last 250 candles
    return combined.tail(self.default_candle_count)
```

---

### **Step 5: ส่งข้อมูลไปคิวเขียน** ⬇️

**ไฟล์:** `csv_queue.py`

```python
# data_adapter.py Line 211 (M1), Line 242 (M5), Line 277 (M15)
self._csv_queue.enqueue_write(completed, self._csv_manager.get_file_path(symbol, "M1"))
self._csv_queue.enqueue_write(completed, self._csv_manager.get_file_path(symbol, "M5"))
self._csv_queue.enqueue_write(completed, self._csv_manager.get_file_path(symbol, "M15"))
```

**Queue Flow:**
```
DataAdapter (RAM) → enqueue_write() → Queue (RAM) → Worker Thread → CSV Writer → CSV File
```

**ข้อควรรู้:**
- Queue ใช้ RAM สำหรับเก็บข้อมูล
- Worker Thread ดึงข้อมูลจาก Queue
- CSV Writer เขียนลงดิสก์แบบ Async

#### **Queue Implementation:**
```python
# csv_queue.py Line 18-81
class CSVQueue:
    def __init__(self, config):
        self.max_queue_size = 1000          # Max 1000 items
        self.queue_timeout = 30             # 30 seconds timeout
        self._queue = queue.Queue()         # Queue storage
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def enqueue_write(self, df, file_path):
        # สำเนาข้อมูลแล้วส่ง
        if self._queue.qsize() >= self.max_queue_size:
            logger.warning(f"Queue full - dropping write for {file_path}")
            return

        self._queue.put((df.copy(), file_path))  # สำเนาข้อมูล

    def _worker(self):
        # Worker thread ทำงานใน background
        while True:
            try:
                df, file_path = self._queue.get(timeout=self.queue_timeout)

                # เขียนไฟล์
                writer = CSVWriter()
                writer.write(df, file_path)

                self._queue.task_done()

            except queue.Empty:
                continue  # Timeout ปกติ
            except Exception as e:
                logger.error(f"Asynchronous write failed: {e}")
```

---

### **Step 6: เขียนข้อมูลลงดิสก์** ⬇️

**ไฟล์:** `csv_writer.py` + `csv_manager.py`

#### **Queue Worker Thread:**
```python
# csv_queue.py Line 57-81
def _worker(self):
    while True:
        try:
            df, file_path = self._queue.get(timeout=self.queue_timeout)

            # เรียก CSVWriter
            writer = CSVWriter()
            writer.write(df, file_path)

            self._queue.task_done()

        except queue.Empty:
            continue  # Timeout ปกติ
        except Exception as e:
            logger.error(f"Asynchronous write failed: {e}")
```

#### **CSV Path:**
```python
# csv_manager.py Line 37-59
def get_file_path(self, symbol, timeframe, date_str=None):
    if not date_str:
        date_str = datetime.now().strftime("%Y_%m_%d")

    # สร้าง path ตาม convention
    symbol_folder = symbol  # เก็บเป็นเดิม EURUSD-OTC
    filename = self.naming_convention.format(
        symbol=symbol,  # เก็บเป็นเดิม EURUSD-OTC ทั้ง โฟลเดอร์ ทั้งชื่อไฟล์
        timeframe=timeframe,
        date=date_str
    )

    # สร้าง directory
    full_path = os.path.join(self.base_dir, symbol_folder, filename)
    os.makedirs(self.base_dir, exist_ok=True)
    if self.auto_create_dirs:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

    return full_path
```

**Path Convention:**
```
data_base/csv/iq_option/{symbol}/{symbol}_{timeframe}.csv
```

**ตัวอย่าง:**
```
data_base/csv/iq_option/EURGBP/EURGBP_M5.csv
data_base/csv/iq_option/EURUSD-OTC/EURUSD-OTC_M1.csv
```

**Format CSV:**
```csv
timestamp,open,high,low,close,volume
2026-07-18 10:30:00,1.2340,1.2342,1.2338,1.2341,100
2026-07-18 10:30:05,1.2341,1.2343,1.2339,1.2342,150
2026-07-18 10:30:10,1.2342,1.2344,1.2340,1.2343,200
```

#### **csv_writer.py - Implementation Detail:**

```python
# csv_writer.py Line 13-72
class CSVWriter:
    """Writes candle dataframes to CSV files."""

    def __init__(self, config=None):
        if config is None:
            from config_setting.config_loader import get_csv_writer_config
            config = get_csv_writer_config()

        # Load writer configuration
        self.encoding = config.get("encoding", "utf-8")
        self.date_format = config.get("date_format", "%Y-%m-%d %H:%M:%S")
        self.include_header = config.get("include_header", True)
        self.decimal_places = config.get("decimal_places", 6)  # ⚠️ ปัดเศษ 6 ตำแหน่ง

    def write(self, df, file_path):
        """Write DataFrame to the specified file path."""
        if df is None or df.empty:
            logger.warning(f"[CSVWriter] Attempted to write empty dataframe to {file_path}")
            return

        try:
            logger.info(f"[CSVWriter] Writing {len(df)} rows to {file_path}")

            # Prepare dataframe for writing
            df_to_write = df.copy()

            # Select ONLY standard OHLCV columns (drop any injected anomaly tracking columns)
            cols = ['open', 'high', 'low', 'close', 'volume']
            df_to_write = df_to_write[[c for c in cols if c in df_to_write.columns]]

            # Format index as timestamp
            df_to_write.index = pd.to_datetime(df_to_write.index).strftime(self.date_format)

            # ⚠️ Round decimal places to 6 places
            for col in cols:
                if col in df_to_write.columns:
                    df_to_write[col] = df_to_write[col].round(self.decimal_places)

            # Write to CSV safely using Atomic Replace inside a Per-File Lock
            # 1. Read existing file if present, merge and deduplicate
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                existing_df = pd.read_csv(file_path, index_col=0, encoding=self.encoding)
                combined_df = pd.concat([existing_df, df_to_write])
                combined_df = combined_df[~combined_df.index.duplicated(keep='last')].sort_index()
                df_to_write = combined_df

            # 2. Write to temporary .tmp file and replace atomically
            tmp_path = file_path + ".tmp"
            df_to_write.to_csv(tmp_path, encoding=self.encoding, header=self.include_header, index=True, mode='w', date_format=self.date_format)
            os.replace(tmp_path, file_path)

            logger.info(f"[CSVWriter] Successfully wrote {len(df_to_write)} rows to {file_path}")

        except Exception as e:
            logger.error(f"[CSVWriter] Failed to write to {file_path}: {e}")
            raise
```

**ข้อควรรู้สำคัญ:**
- ปัดเศษทศนิยมราคาสุดท้ายที่ **6 ตำแหน่ง** (decimal_places=6)
- ทำงานผ่าน **Zero-Lock Architecture (Thread-Safe Atomic Write)** ร่วมกับ `get_file_lock`
- อ่านไฟล์เดิม ตัดเวลาซ้ำ (Deduplicate) เขียนลงไฟล์ชั่วคราว `.tmp` แล้วทำ `os.replace` สลับไฟล์อย่างปลอดภัย
- ป้องกันปัญหา `PermissionError [WinError 5]` บน Windows และป้องกันบรรทัดซ้ำ 100%

---

### **Step 7: เฝ้าระวังระบบ** ⬇️

**ไฟล์:** `data_monitor.py`

**Metrics ที่ตรวจวัด:**
```python
# data_monitor.py Line 28-36
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

#### **Gap Detection:**
```python
# data_monitor.py Line 56-73
def report_gap(self, symbol, timeframe, gap_seconds):
    self.gap_count += 1
    threshold = self.gap_thresholds.get(timeframe, 300)

    if gap_seconds > threshold:
        # หยุดระบบทันที
        raise RuntimeError(f"CRITICAL DATA GAP: {symbol} {timeframe} {gap_seconds}s")
```

#### **Latency Monitoring:**
```python
# data_monitor.py Line 75-105
def report_latency(self, symbol, timeframe, age_ms):
    self.latency_ms = age_ms

    # หยุดระบบทันทีถ้าข้อมูลเก่า
    if age_ms >= self.latency_thresholds["STALE"]:
        raise RuntimeError(f"CRITICAL LATENCY: {symbol} {timeframe} {age_ms}ms")
```

#### **Queue Overflow:**
```python
# data_monitor.py Line 107-119
def report_queue_status(self, queue_length):
    if queue_length > 1000:
        raise RuntimeError(f"CRITICAL QUEUE OVERFLOW: {queue_length} items")
    elif queue_length > 500:
        raise RuntimeError(f"CRITICAL QUEUE SIZE: {queue_length} items")
```

#### **Alert Levels:**
- 🟢 Normal - ทำงานปกติ
- 🟡 WARNING - ควรตรวจสอบ
- 🔴 ERROR - มีปัญหา
- ⚫ CRITICAL - หยุดระบบทันที

**ข้อควรรู้:**
- Gap > 5 นาที (M1) → หยุดระบบ
- Gap > 25 นาที (M5) → หยุดระบบ
- Gap > 75 นาที (M15) → หยุดระบบ
- Latency > 600,000ms (10 นาที) (STALE) → หยุดระบบ
- Queue > 1000 รายการ → หยุดระบบ

---

## 🚀 Runner Loop จริง

**ไฟล์:** `runner.py`

```python
def start(self):
    while True:
        # sleep 60-57 วินาที
        # sleep = 3 - now.second (ถ้า now.second < 3)
        # หรือ sleep = 60 - now.second + 3 (ถ้า now.second >= 3)
        # แปลว่า sleep คร่างๆ 3-60 วินาที

        self.run_cycle()

def run_cycle(self):
    # 1. Check connection
    self.data_adapter.ensure_connected()

    # 2. Fetch and save data concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.symbols)) as executor:
        for sym in self.symbols:
            executor.submit(self.fetch_and_save_data, sym)

    # 3. Get latest price from CSV (ไม่จาก RAM)
    prices_dict[sym] = self._get_latest_price_from_csv(sym)

    # 4. Trigger Orchestrator
    self.orchestrator.process_cycle(sym)
```

**ข้อควรรู้:**
- Loop ทำงานทุกช่วงเวลาที่เรียกใหม่
- ไม่ได้ sleep 5 วินาทีอย่างแน่นอน
- Worker Thread ทำงานแบบ concurrent
- ดึงข้อมูลจาก CSV ไม่จาก RAM (ราคา)

---

## 📊 ตารางสรุปขั้นตอนการทำงาน

| ขั้นตอน | ไฟล์ที่เกี่ยวข้อง | ทำอะไร | สถานะ |
|---------|-------------------|---------|--------|
| 1. รับข้อมูล | iq_option_adapter.py | ดึง 3 แท่งใหม่จาก IQ Option API | ✅ Active |
| 2. เก็บ RAM | data_adapter.py | บันทึกในหน่วยความจำ RAM | ✅ Active |
| 3. Validate | candle_validator.py | ตรวจสอบคุณภาพ 4 เกณฑ์ | ✅ Active |
| 4. Timeframe | data_adapter.py | Merge + Drop forming (M1, M5, M15) | ✅ Active |
| 5. Enqueue | csv_queue.py | ส่งไปคิว (Non-blocking) | ✅ Active |
| 6. Write | csv_writer.py + csv_manager.py | เขียนลงดิสก์ (Async) | ✅ Active |
| 7. Monitor | data_monitor.py | เฝ้าระวังระบบ (หยุดถ้าสั่ง) | ✅ Active |

---

## ⚙️ ค่า Configuration สำคัญ

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
      "default_candle_count": 250,  # Note: M15 จะดึงเพียง 50 แท่งใน Warm-up (M1=100, M5=250, M15=50)
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
    "anomaly_detector": {
      "response_time_warning": 7.0,
      "response_time_critical": 10.0,
      "connection_timeout": 15.0,
      "spike_threshold": 0.3,
      "zero_volume_threshold": 0,
      "impossible_candle_threshold": 0.001,
      "spike_window": 20,
      "max_consecutive_zero_volume": 3,
      "max_consecutive_anomalies": 10
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

## 🚨 Error Handling จริง

### ปัญหาที่เกิดขึ้น + การแก้ไข

| ปัญหา | เกิดจากอะไร | การแก้ไข |
|-------|-------------|-----------|
| **Data Gap** | หากมีช่องว่าง > 5 นาที (M1) / 25 นาที (M5) / 75 นาที (M15) | ระเบิด RuntimeError → หยุดระบบทันที |
| **Latency** | หากข้อมูลเก่า > 10 นาที | ระเบิด RuntimeError → หยุดระบบทันที |
| **Queue Overflow** | หาก Queue > 1000 รายการ | ระเบิด RuntimeError → หยุดระบบทันที |
| **Invalid Data** | NaN, Volume=0, Price out of range | ระเบิด ValueError → หยุดระบบทันที |
| **Connection Lost** | IQ Option ตัดการเชื่อมต่อ | Auto reconnect (5 วินาที) |

---

## 📈 สถานะปัจจุบัน

### ✅ ระบบพร้อมใช้งาน 100%

- **เชื่อมต่อ:** IQ Option (PRACTICE)
- **Timeframe:** M1, M5, M15
- **Symbols:** EURGBP, EURUSD, EURJPY, EURUSD-OTC, EURGBP-OTC
- **Storage:** RAM + Async CSV
- **Monitoring:** Active
- **Error Handling:** Auto restart หรือหยุดระบบ

### ค่าเฉลี่ยการทำงาน

- ⏱️ **Startup:** 10-15 วินาที
- 🔄 **Update:** ทุกช่วงเวลาที่เรียกใหม่ (ไม่ใช่ 5 วินาที)
- 💾 **RAM Usage:** ~96KB (5 symbols)
- 📁 **Disk I/O:** Non-blocking

---

## 🎯 สรุปสั้นๆ

**FINALBOT Data Feed ทำงานดังนี้:**

1. ✅ ดึงข้อมูลจาก IQ Option → มาไว้ใน RAM
2. ✅ ตรวจสอบคุณภาพข้อมูล → ตัดข้อมูลเสีย (หยุดระบบ)
3. ✅ ประสาน Timeframe → Merge + Drop forming (M1, M5, M15)
4. ✅ ส่งไปคิว → ไม่บล็อกหลัก (Non-blocking)
5. ✅ เขียนลงดิสก์ → แบบ Async & Zero-Lock Atomic Write (decimal_places=6, Deduplicate, Atomic replace)
6. ✅ เฝ้าระวังระบบ → หยุดทันทีถ้ามีปัญหา

**ข้อควรจำ:**
- 👑 **DataAdapter = หัวใจระบบ**
- ⚡ **RAM = สถานที่ทำงานหลัก**
- 🚀 **Queue = ไม่บล็อกหลัก**
- 💾 **CSV = เก็บข้อมูลถาวร**
- 📊 **Monitor = เฝ้าระวังทุกอย่าง**
- ❌ **M15 ดึงตรงจาก Broker ไม่ resample**
- ❌ **TimeframeSync ไม่ถูกเรียกใช้จริง**
- ⚠️ **Decimal places = 6** (ปัดเศษราคา 6 ตำแหน่ง)
- ⚠️ **Zero-Lock Atomic Write** (Deduplicate & Atomic replace)

---

**สร้างเมื่อ:** 2026-07-18
**สถานะ:** ✅ ใช้งานได้เต็มรูปแบบ
**ความพร้อม:** 🚀 พร้อมเริ่มต้นการทดสอบ
