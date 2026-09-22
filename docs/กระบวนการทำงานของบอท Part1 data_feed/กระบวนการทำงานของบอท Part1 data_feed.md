ได้ครับ 👍 ผมจะเขียน docs ฉบับใหม่ให้ **ตรงกับโค้ดจริง** ใน `data_feed/` ทั้ง 13 ไฟล์ที่คุณส่งมา โดยยึดโครงสร้างเดิมของ docs ไว้ (Executive Summary, Architecture, Rules, File Structure, Lifecycle, CSV Schema, Logging, Testing, Sign-Off)

---

# 📥 FINALBOT - กระบวนการทำงานของบอท ส่วนที่ 1: INPUT (Data Feed System)

## 🎯 ทำความเข้าใจได้ทันที (Executive Summary)

ส่วนงานที่ 1 (**INPUT / Data Feed System**) คือ **"ระบบท่อส่งข้อมูลตลาด"** มีหน้าที่หลักในการเชื่อมต่อกับโบรกเกอร์ (ปัจจุบันคือ IQ Option), ซิงค์เวลาเซิร์ฟเวอร์ให้ตรง, ดึงข้อมูลแท่งเทียน OHLCV แบบ Multi-timeframe (**S30, M1, M5** ในโหมด `strategies_mode` หรือ **M1, M5, M15** ในโหมด `ml_mode`/`ai_mode`), ตรวจสอบความถูกต้อง, เก็บแท่งเทียนที่สมบูรณ์ไว้ใน RAM เพื่อให้อ่านราคาได้ทันทีแบบ Zero Disk I/O และบันทึกไฟล์ `.csv` มาตรฐาน 8 คอลัมน์ลงฮาร์ดดิสก์ผ่านระบบคิวและ Atomic Write

> **📅 เอกสารนี้ปรับปรุงให้ตรงกับโค้ดจริง ณ commit ปัจจุบัน** — ถ้าเอกสารกับโค้ดขัดกัน ให้ยึดโค้ดเป็นหลัก

**ขอบเขตและสัญญาของส่วนงานที่ 1:**

| จุดเริ่มต้น | แกนกลางการประมวลผล | จุดสิ้นสุดการส่งมอบ |
|---|---|---|
| โหลด Config & ซิงค์เวลา | ดึง WebSocket + REST | ไฟล์ 8-Column CSV |
| เชื่อมต่อ Broker API | ตรวจสอบ Data Validation | RAM Cache พร้อมอ่าน |
| โหลดรายชื่อคู่เงิน | ตัดแท่งเทียนที่ยังไม่จบ | Log ตามรอบนาที |
| — | คำนวณ Age & Quality | — |

---

## 🏛️ สถาปัตยกรรมและหลักการออกแบบ (Architecture & Principles)

### 1. Single Source of Truth via CSV

ไฟล์ `.csv` ในโฟลเดอร์ `data_base/output_feed/{symbol}/{symbol}_{timeframe}.csv` คือ **"แหล่งความจริงหนึ่งเดียว"** ของข้อมูลดิบ

ส่วนงานที่ 2 (Data Evaluate) อ่าน OHLCV ผ่านไฟล์ `.csv` นี้เท่านั้น — เป็นการ Decouple ระหว่างระบบรับข้อมูลกับระบบวิเคราะห์

### 2. Zero RAM Transfer ระหว่าง Part

RAM ใช้ได้เต็มที่ **ภายใน Part 1** (cache, queue, lock) แต่ **ห้ามส่ง object ผ่าน RAM ข้าม Part** — ต้องผ่านไฟล์บน SSD เท่านั้น

ภายใน Part 1 แบ่ง RAM เป็น 2 ระดับ:
1. **Raw Store** (`_store_s30`, `_store_m1`, `_store_m5`, `_store_m15`) — เก็บข้อมูลดิบจาก broker รวมแท่งที่กำลังฟอร์ม
2. **Completed Candles** (`_completed_candles`) — เก็บเฉพาะแท่งที่ปิดสมบูรณ์แล้ว 250 แท่ง

### 3. Thread-Safe Asynchronous I/O

การดึงข้อมูลและแสดงผลต้องไม่ถูกบล็อกด้วย Disk I/O — การเขียน CSV จึงแยกไปที่ `CSVQueue` (Daemon Thread) ร่วมกับ `CSVWriter` ที่ใช้ **Per-File RLock** และ **Atomic Write** ผ่าน `.tmp` + `os.replace`

### 4. Staggered Timing ตามไทม์เฟรม

แต่ละไทม์เฟรมมี "เวลาปิด" ไม่พร้อมกัน จึงต้องรอให้ปิดก่อนดึง:
- **S30** → รอถึง `:00.800`
- **M1** → รอถึง `:01.500`
- **M5** → รอถึง `:02.000` (เฉพาะเมื่อ block เปลี่ยน)
- **M15** → รอถึง `:02.500` (เฉพาะเมื่อ block เปลี่ยน และไม่ skip)

---

## 🚨 กฎเหล็ก Fail-Fast และมาตรฐาน Zero Tolerance

ระบบ Data Feed ยึดถือกฎวินัย AI ตามเอกสาร **`agent.md`** (ไม่มี S) ซึ่งมีทั้งหมด **27 ข้อ** — สรุปข้อที่เกี่ยวข้องกับ Part 1:

1. **Zero Retries สำหรับ Network I/O** — `retry_attempts` และ `retry_delay` ใน config ต้องเป็น 0 (โค้ดตรวจสอบและ raise ถ้าไม่ใช่ 0)
2. **No Mock Data** — ห้ามประมาณการราคา ห้ามใช้แท่งเก่าสวมรอย
3. **Fail-Fast Data Gap** — พบ gap เกินเกณฑ์ → `DataGapError` ทันที
4. **Immutability of Part 1 & 2** — `data_feed/` และ `data_evaluate/` ห้ามแก้
5. **Single Daily News Calendar** — ปฏิทินข่าวเก็บ 1 ไฟล์/วัน
6. **No Silent Failures** — ต้อง `logger.exception()` ไม่ใช่ `except: pass`
7. **Background Process Rule** — ห้ามรันค้างเบื้องหลัง

**เกณฑ์ Gap Detection ที่ใช้จริง:**

| ไทม์เฟรม | Gap Threshold |
|---|---|
| S30 | 150 วินาที |
| M1 | 300 วินาที |
| M5 | 1500 วินาที |
| M15 | 4500 วินาที |

---

## 📂 โครงสร้างไฟล์ในระบบ Data Feed (ของจริง)

```
data_feed/                              [Part 1 — Data Feed]
├── data_adapter.py                     Commander ประสานงานทั้งหมด
├── data_processor.py                   drop_forming, merge_candles, add_age_and_quality, process_candle_refresh
├── data_validator.py                   ตรวจสอบความถูกต้อง + continuity + overlap
├── data_cache_store.py                 RAMCacheStore (S30/M1/M5/M15 + completed)
├── csv_manager.py                      จัดการ path (Singleton)
├── csv_queue.py                        คิวเขียนแบบ async (Singleton)
├── csv_writer.py                       เขียนไฟล์แบบ atomic + listener (Singleton)
├── csv_time_sync.py                    TimeSyncManager (Singleton)
└── bridge_adapter/                     [Bridge Adapter]
    ├── abstract_class.py               Interface IDataSource (ABC)
    ├── broker_factory.py               สร้าง broker + DataAdapter
    ├── bridge_iq_adapter/              [IQ Option — ใช้งานจริง]
    │   ├── bridge_iq_adapter.py        Facade
    │   ├── connection.py               Connection Manager
    │   ├── rest_fetcher.py             REST Fetcher
    │   └── stream_manager.py           WebSocket Stream
    ├── bridge_quotex_adapter/          [Quotex — stub]
    └── bridge_pocket_adapter/          [Pocket Option — stub]
```

**หมายเหตุ:** `news_calendar.py` **ไม่ได้อยู่ใน `data_feed/`** — อยู่ที่ `data_evaluate/<mode>/news_calendar.py` (ของ Part 2)

**ไฟล์ที่เกี่ยวข้อง (นอก `data_feed/`):**
- `runner.py` — Main Controller
- `main.py` — Entry point
- `config_setting/config_loader.py` — Config getter
- `config_setting/settings.json` — Config หลัก
- `config_setting/symbols.json` — รายชื่อคู่เงิน (อ่านโดย `get_symbols()` / `get_symbols_with_payouts()`)

---

## 📋 รายละเอียดแต่ละไฟล์ใน `data_feed/`

| # | ไฟล์ | หน้าที่ |
|---|---|---|
| 1 | `data_adapter.py` | `DataAdapter` — Commander ประสานงาน Broker, Validator, Cache, Processor, CSV Queue มี `init_symbol()`, `update()`, `ingest_cycle()`, `warmup_all_symbols()` |
| 2 | `data_processor.py` | ฟังก์ชัน: `drop_forming()`, `merge_candles()`, `add_age_and_quality()`, `process_candle_refresh()` |
| 3 | `data_validator.py` | `DataValidator` — ตรวจ NaN, ค่าลบ, high<low, open/close นอกช่วง, volume ติดลบ, continuity, overlap, `ensure_utc_datetime_index()` |
| 4 | `data_cache_store.py` | `RAMCacheStore` — เก็บ `_store_s30/m1/m5/m15`, `_completed_candles`, `_last_block_*` มี `check_warmup()`, `get_latest_close()` |
| 5 | `csv_manager.py` | `CSVManager` (Singleton) — `get_file_path()`, `cleanup_old_files()`, ป้องกัน path traversal |
| 6 | `csv_queue.py` | `CSVQueue` (Singleton) — `enqueue_write()`, `flush()`, worker thread + circuit breaker |
| 7 | `csv_writer.py` | `CSVWriter` (Singleton) — `write()`, `read()`, listener pattern, per-file RLock, atomic write |
| 8 | `csv_time_sync.py` | `TimeSyncManager` (Singleton) — `sync_server_time()`, `start_time_sync_thread()`, `get_broker_epoch()` |
| 9 | `bridge_adapter/abstract_class.py` | `IDataSource` (ABC) — interface มาตรฐาน |
| 10 | `bridge_adapter/broker_factory.py` | `BrokerFactory.create_raw_broker()` และ `create_broker()` |
| 11 | `bridge_iq_adapter/bridge_iq_adapter.py` | `IQOptionAdapter` — Facade |
| 12 | `bridge_iq_adapter/connection.py` | `IQConnectionManager` — login, balance, server time |
| 13 | `bridge_iq_adapter/rest_fetcher.py` | `IQRestFetcher` — ดึงแท่งเทียนผ่าน REST + global lock |
| 14 | `bridge_iq_adapter/stream_manager.py` | `IQStreamManager` — WebSocket stream + micro-polling |
| 15 | `bridge_quotex_adapter/` | Stub (ยังไม่ทำงาน) |
| 16 | `bridge_pocket_adapter/` | Stub (ยังไม่ทำงาน) |

---

## 🔄 วงจรการทำงาน (End-to-End Lifecycle)

### Phase 1: Startup & Initialization

1. `runner.py` โหลด `settings.json` ผ่าน `load_settings(reload=True)`
2. สร้าง single-instance lock ที่ `logs/runner.lock`
3. ตัดสินโหมดจาก CLI (`--mode strategies/ai/ml`) หรือ `active_mode` ใน settings
4. `BrokerFactory.create_broker()` สร้าง:
   - `IQOptionAdapter` (หรือ broker อื่นตาม `active_broker`)
   - `TimeSyncManager` → เรียก `sync_server_time()` ครั้งแรก + เริ่ม daemon thread
   - `DataAdapter` → สร้าง `RAMCacheStore`, `DataValidator`, `CSVManager`, `CSVQueue`
5. ถ้า `symbol_mode == "bot"` → `symbols_selection.run_selector()` คัดคู่เงิน → เขียน `config_setting/symbols.json`
6. `get_symbols_with_payouts()` อ่านรายชื่อคู่เงิน + payout
7. แสดง Time Sync offset
8. ดึง balance ผ่าน `data_feed.get_balance()` — ถ้าดึงไม่ได้ **raise ทันที**
9. โหลด orchestrator ของโหมด (Part 2)
10. Pre-warm สมอง (ML/Chronos หรือ AI/Gemini หรือ log เฉยๆ สำหรับ strategies)
11. สร้าง `DecisionManager` (Part 3) และ `ExecutorManager` (Part 4)
12. `warmup_all_symbols()` — ดึงข้อมูลย้อนหลัง

### Phase 2: Historical Warm-Up

`warmup_all_symbols(symbols)`:
1. ใช้ `ThreadPoolExecutor` (สูงสุด 20 workers) ดึงข้อมูลทุกคู่เงินพร้อมกัน
2. แต่ละคู่เรียก `init_symbol()`:
   - ดึง 255 แท่งสำหรับ **S30, M1, M5** (โหมด strategies) หรือ **M1, M5, M15** (โหมด ml/ai)
   - `validator.validate()` แต่ละ TF
   - เก็บลง `_store_*` และตั้ง `_last_block_*`
   - `drop_forming()` → เหลือ 250 แท่งที่ปิดสมบูรณ์
   - `add_age_and_quality()` → เพิ่มคอลัมน์ age (ms) และ quality (FRESH/STALE)
   - เก็บลง `_completed_candles`
   - `csv_queue.enqueue_write()` ส่งเข้า queue
3. หลัง warmup เสร็จ → `csv_queue.flush()` รอเขียนเสร็จ
4. เก็บ `ready_symbols` — ถ้าไม่มีคู่ไหนผ่านเลย **raise**

### Phase 3: Countdown to Boundary

`runner.py` คำนวณเวลาถึง `:01.500` ของนาทีถัดไป (เขตเวลา Asia/Bangkok, UTC+7 — hardcode ในโค้ด) แล้ว sleep รอ จากนั้นเข้าสู่ main loop

### Phase 4: Live Cycle (ทุก 1 นาที)

`runner.run_cycle()` ทำงานที่ `:01.500` ของทุกนาที:

1. `ensure_connected()` — ถ้าหลุด raise ทันที
2. `data_feed.ingest_cycle(symbols)`:
   - `ThreadPoolExecutor` (สูงสุด 20 workers) เรียก `update()` ต่อคู่เงิน
   - `update()` ทำ staggered timing:
     - S30: `_wait_staggered_timing(0.8)`
     - M1: `_wait_staggered_timing(1.5)`
     - M5: `_wait_staggered_timing(2.0)` ถ้า block เปลี่ยน
     - M15: `_wait_staggered_timing(2.5)` ถ้า block เปลี่ยน และไม่ skip
   - แต่ละ TF ผ่าน `process_candle_refresh()`:
     - ถ้า store ว่าง → fetch ข้อมูลเต็ม
     - ถ้า block เปลี่ยน → fetch 2 แท่งใหม่ แล้ว `merge_candles()` (ตรวจ continuity + overlap)
     - ตรวจ gap → ถ้าเกิน threshold raise `DataGapError`
     - `drop_forming()` + `add_age_and_quality()`
   - เก็บ completed candles ลง RAM
   - `enqueue_write()` ถ้า block changed
   - `csv_queue.flush()` รอเขียนเสร็จ
   - `ConsoleUI.show_prices_and_balance()`
3. `orchestrator.evaluate_cycle()` — Part 2
4. `decision_manager.process_latest()` — Part 3
5. `executor_manager.process_decision_files()` — Part 4
6. sleep ถึง `:01.500` ของนาทีถัดไป

### Phase 5: Background Time Resync

`TimeSyncDaemonThread` รันตลอด — คำนวณ sleep ให้ตื่นที่ `:30.000` ของทุกนาที แล้วเรียก `sync_server_time()` อัปเดต `time_offset`

---

## 📊 CSV Schema 8 คอลัมน์

ไฟล์ CSV ทุกไฟล์ใน `data_base/output_feed/{symbol}/{symbol}_{timeframe}.csv` มี 8 คอลัมน์:

| # | คอลัมน์ | ชนิด | ตัวอย่าง | หมายเหตุ |
|---|---|---|---|---|
| 1 | `timestamp` | ISO 8601 UTC | `2026-09-20 01:59:00+00:00` | ต้องมี `+00:00` เสมอ |
| 2 | `open` | float (6 ตำแหน่ง) | `1.16210` | |
| 3 | `high` | float (6 ตำแหน่ง) | `1.16225` | ≥ low |
| 4 | `low` | float (6 ตำแหน่ง) | `1.16195` | ≤ high |
| 5 | `close` | float (6 ตำแหน่ง) | `1.16218` | |
| 6 | `volume` | int64 | `1523` | ห้ามติดลบ |
| 7 | `age` | int64 (ms) | `1500` | `(broker_epoch - candle_ts) * 1000` |
| 8 | `quality` | str | `FRESH` / `STALE` | FRESH ถ้า age ≤ tf_seconds × 2 × 1000 |

**จำนวนแถว:** 250 แถว + header (บังคับด้วย `tail(250)`)

**การเขียน:**
1. อ่านไฟล์เดิม (ถ้ามี)
2. Merge + dedup ตาม timestamp + sort
3. `tail(250)`
4. Format คอลัมน์
5. เขียนลง `{file_path}.{thread_id}.tmp`
6. `os.replace(tmp, file_path)` — atomic
7. Retry `PermissionError` 5 ครั้ง × 50ms (Windows file handle defense)
8. เรียก listeners

---

## 🖥️ Logging

- ใช้ `monitoring/console_dashboard.py` เป็นตัวจัดการ
- Log หลักอยู่ที่ `logs/logs_data_feed/`
- การ log ใน `run_cycle` มี:
  - `[DataFeedRunner] Cycle start: symbols=N`
  - `[DataFeedRunner] Ingest complete: X.XXXs; timeframe_blocks={...}`
  - `[DataFeedRunner] Evaluation/decision/trade complete: X.XXXs/X.XXXs; cycle_total=X.XXXs`
- `ConsoleUI` แสดงข้อความภาษาไทย (เช่น "กำลังเชื่อมต่อโบรกเกอร์", "ตรวจพบรายการสินทรัพย์")

---

## 🧪 การทดสอบ

1. รันผ่าน `python runner.py` เท่านั้น — ห้ามใช้ script แยก
2. ทดสอบใน foreground terminal — ห้ามรันค้างเบื้องหลัง
3. ทดสอบแล้ว kill process ทันที
4. ตรวจสอบผลลัพธ์ 2 ชั้น:
   - **Tier 1:** ดู log และ console output
   - **Tier 2:** เปิดไฟล์ CSV จริงใน `data_base/output_feed/` ดูว่า 8 คอลัมน์, 250 แถว, เรียงเวลา, quality ถูกต้อง

---

## 📌 สรุปความพร้อมส่งมอบ

Part 1 (Data Feed System) ออกแบบให้:
- **Thread-safe** ด้วย Singleton + RLock + Atomic Write
- **Time-synced** ด้วย TimeSyncManager resync ทุก :30
- **Fail-Fast** ด้วย Zero Tolerance (ไม่ retry network, ตรวจ gap, ตรวจ continuity)
- **Zero RAM Transfer** ระหว่าง Part — ส่งต่อผ่านไฟล์ `.csv` 8 คอลัมน์ 250 แถว
- **Multi-timeframe** S30/M1/M5 (strategies) หรือ M1/M5/M15 (ml/ai)
- **Staggered timing** ตามไทม์เฟรม

พร้อมส่งมอบให้ Part 2 (Data Evaluate) อ่านต่อ

---

## ⚠️ หมายเหตุสถาปัตยกรรม: จุดที่ตั้งใจออกแบบ

### 1. Skeleton ของ Quotex/Pocket Adapter
เป็น **Intentional Skeleton** ตาม Factory Pattern รองรับ Multi-Broker ในอนาคต — ปัจจุบันใช้ IQ Option เท่านั้น

### 2. Retry `PermissionError` ใน CSVWriter
ไม่ขัดกับ Zero Tolerance เพราะ **Zero Tolerance บังคับใช้กับ Network I/O** เท่านั้น — Retry ใน CSVWriter เป็น **OS-Level File Lock Defense** บน Windows (Windows Defender/Anti-Virus อ่านไฟล์ `.tmp` ขณะ `os.replace`)

### 3. Staggered Timing ตามไทม์เฟรม
S30 `:00.800`, M1 `:01.500`, M5 `:02.000`, M15 `:02.500` — เลือกจากพฤติกรรมจริงของเซิร์ฟเวอร์โบรกเกอร์ ที่ใช้เวลาประมาณ 500–1000ms หลังสิ้นสุดแท่งในการประมวลผล

### 4. Warm-up 255 → 250 แท่ง
255 แท่งเพื่อ buffer สำหรับ `drop_forming()` ตัดแท่งที่กำลังฟอร์มทิ้ง → เหลือ 250 แท่งที่ปิดสมบูรณ์พอดี

### 5. Per-File RLock + Atomic Write
ป้องกัน race condition ระหว่าง Part 1 เขียนกับ Part 2 อ่าน — ทั้งสองใช้ `get_file_lock(file_path)` และ `read_csv_safe()` ที่ใช้ lock เดียวกัน

---

**จบเอกสาร**

---

## 📌 สรุปสิ่งที่ผมแก้จาก docs เดิม

| # | จุดที่แก้ |
|---|---|
| 1 | Path CSV → `data_base/output_feed/{symbol}/` (ไม่มี `{active_broker}`) |
| 2 | Timeframe → S30/M1/M5 (strategies) หรือ M1/M5/M15 (ml/ai) |
| 3 | จำนวน Payload → ลบ "74 ฟิลด์" ออก |
| 4 | ลบ `fetch_and_save_data()` และ `[SEC_TRACK]` ที่ไม่มีจริง |
| 5 | Phase 4 → ทำงานทุก 1 นาทีที่ `:01.500` (ไม่ใช่ทุกวินาที) |
| 6 | เพิ่ม staggered timing (S30 :00.800, M1 :01.500, M5 :02.000, M15 :02.500) |
| 7 | จำนวนไฟล์ → 16 ไฟล์ใน `data_feed/` + bridge_adapter |
| 8 | `AGENTS.md` → `agent.md` (ไม่มี S) |
| 9 | กฎ → 27 ข้อ |
| 10 | `news_calendar.py` → ระบุว่าอยู่นอก `data_feed/` |
| 11 | ปฏิทินข่าว → ลบ path `data_base/calendar/` ออก |
| 12 | `symbol_mapper.json` → ลบออก (ไม่ได้อ้าง) |
| 13 | Interface `IDataSource` → ไม่พูดว่าครบ (มีแค่ที่ประกาศ) |
| 14 | Log → ปรับให้ตรงกับที่ `runner.py` เขียนจริง |
| 15 | Testing → ปรับให้สอดคล้อง |
| 16 | เพิ่ม S30 gap threshold (150s) |

---

**หมายเหตุ:** ผมยึด **โค้ดจริง** เป็นหลักตามที่คุณกำหนด และคงโครงสร้างเดิมของ docs ไว้ (Executive Summary → Architecture → Rules → File Structure → Lifecycle → CSV Schema → Logging → Testing → Sign-Off → Design Rationale)

ถ้าต้องการให้ปรับจุดไหนเพิ่ม บอกได้เลยครับ 🙂