# FINALBOT Part 1 — Data Feed System

## ภาพรวม

FINALBOT แบ่งการทำงานออกเป็น 3 ส่วน:

| ส่วน | หน้าที่ | สถานะ |
|------|---------|--------|
| **Part 1** | ดึงข้อมูลจากโบรกเกอร์ → จัดเรียง → ส่งออก CSV | ✅ พร้อมใช้ |
| Part 2 | รับ CSV จาก Part 1 → วิเคราะห์/ประมวลผล | ⏳ ยังไม่ได้ทำ |
| Part 3 | (กำหนดในอนาคต) | ⏳ ยังไม่ได้ทำ |

เอกสารนี้ครอบคลุมเฉพาะ **Part 1** เท่านั้น

---

## หน้าที่ของ Part 1

```
โบรกเกอร์ (IQ Option)
    ↓ ดึงข้อมูลผ่าน WebSocket / REST API
    ↓ แปลงรูปแบบให้เป็นมาตรฐาน (OHLCV)
    ↓ ตรวจสอบความถูกต้อง
    ↓ เพิ่ม age + quality
    ↓ บันทึกเป็นไฟล์ CSV (8 คอลัมน์)
ไฟล์ CSV พร้อมส่งต่อให้ Part 2
```

**เริ่มต้น:** เชื่อมต่อโบรกเกอร์
**สิ้นสุด:** ส่งออกไฟล์ CSV ไปยัง `data_base/csv/`

---

## โครงสร้างระบบ

```
FINALBOT_Part1/
├── main.py                    # Entry point
├── runner.py                  # ตัวรันหลัก (PureAIRunner)
├── .env                       # Credentials (ไม่ commit)
├── .agents/AGENTS.md          # กฎและสเปกการทำงาน
├── config_setting/            # การตั้งค่าระบบ
│   ├── settings.json          # ตั้งค่าบัญชี, สัญลักษณ์, ขีดจำกัด
│   ├── config_loader.py       # โหลด config
│   └── symbol_mapper.json     # แมปชื่อสัญลักษณ์ระหว่างโบรกเกอร์
├── data_feed/                 # ระบบดึงข้อมูล
│   ├── data_adapter.py        # Coordinator หลัก
│   ├── data_processor.py      # ประมวลผลแท่งเทียน (drop_forming, merge, age/quality)
│   ├── data_validator.py      # ตรวจสอบความถูกต้อง
│   ├── data_cache_store.py    # RAM Cache
│   ├── csv_manager.py         # จัดการไฟล์ CSV
│   ├── csv_queue.py           # Queue การเขียน CSV
│   ├── csv_writer.py          # เขียน CSV (thread-safe)
│   ├── csv_time_sync.py       # ซิงค์เวลา
│   ├── exceptions.py          # Custom exceptions
│   └── bridge_adapter/        # Adapter สำหรับแต่ละโบรกเกอร์
│       ├── abstract_class.py     # Interface มาตรฐาน (IDataSource)
│       ├── broker_factory.py     # โรงงานสร้าง adapter
│       ├── bridge_iq_adapter/    # IQ Option (พร้อมใช้)
│       │   ├── bridge_iq_adapter.py  # Facade
│       │   ├── connection.py         # จัดการการเชื่อมต่อ
│       │   ├── rest_fetcher.py       # ดึงข้อมูลผ่าน REST API
│       │   └── stream_manager.py     # ดึงข้อมูลผ่าน WebSocket
│       ├── bridge_quotex_adapter/# Quotex (skeleton)
│       └── bridge_pocket_adapter/# Pocket Option (skeleton)
├── monitoring/                # ระบบมอนิเตอร์
│   ├── console_dashboard.py   # แดชบอร์ด + ตั้งค่า logging
│   ├── logger.py              # logging utilities
│   ├── error_detector.py      # ตรวจจับ error
│   ├── health_monitor.py      # ตรวจสุขภาพระบบ
│   ├── performance_monitor.py # ตรวจประสิทธิภาพ
│   ├── reporter.py            # รายงาน
│   └── signal_notifier.py     # แจ้งเตือน
├── data_base/                 # ข้อมูลส่งออก
│   ├── csv/iq_option/         # ไฟล์ CSV แยกตามคู่เงิน
│   └── calendar/              # ปฏิทินเศรษฐกิจ
├── logs/                      # ล็อกการทำงาน
│   └── logs_data_feed/
│       ├── all_runtime/       # ล็อกทั้งหมด (runtime.log)
│       ├── errors/            # error.log
│       ├── warnings/          # warning.log
│       ├── system_info/       # info.log
│       └── fallback/          # fallback.log (REST fallback)
└── docs/                      # เอกสาร
    └── README.md              # ไฟล์นี้
```

---

## กระบวนการดึงข้อมูล

### 1. เริ่มต้น (Initialization)
1. โหลด config จาก `settings.json`
2. เชื่อมต่อ IQ Option (ผ่าน `IQConnectionManager`)
3. ซิงค์เวลากับเซิร์ฟเวอร์โบรกเกอร์
4. Warm-up: ดึงข้อมูลย้อนหลัง 250 แท่งเทียนต่อคู่เงิน

### 2. ดึงข้อมูล (Data Fetching)
- **WebSocket** — ดึงข้อมูล real-time (หลัก)
- **REST API** — fallback เมื่อ WebSocket ว่าง (ดึงข้อมูลจริงจากโบรกเกอร์)
- ทุกครั้งที่ใช้ REST fallback → บันทึกลง `fallback.log`

### 3. ประมวลผล (Processing)
1. ตรวจสอบข้อมูล (validate) — type, NaN, price range
2. ตัดแท่งเทียนที่ยังไม่ปิด (drop_forming)
3. รวมข้อมูลเก่า + ใหม่ (merge) ตรวจสอบช่องว่าง (gap)
4. คำนวณ age (มิลลิวินาที) และ quality (FRESH/STALE)

### 4. ส่งออก (Output)
- เขียนลง RAM Cache (อ่านเร็ว ไม่ต้องอ่านดิสก์)
- เขียนลงไฟล์ CSV ผ่าน Queue (thread-safe)
- ไฟล์ CSV เก็บที่ `data_base/csv/iq_option/<SYMBOL>/`

---

## โบรกเกอร์ที่รองรับ

| โบรกเกอร์ | สถานะ | ประเภท |
|-----------|--------|--------|
| IQ Option | ✅ พร้อมใช้ | Binary Options (OTC) |
| Quotex | ⏳ Skeleton | Binary Options |
| Pocket Option | ⏳ Skeleton | Binary Options |

## สินทรัพย์ปัจจุบัน

- EURUSD-OTC
- EURGBP-OTC
- GBPUSD-OTC
- GBPJPY-OTC

**อนาคต:** Crypto, Forex, หุ้น

## Timeframe ที่รองรับ

- M1 (1 นาที)
- M5 (5 นาที)
- M15 (15 นาที)

---

## มาตรฐานข้อมูล CSV (Output)

ไฟล์ CSV ที่ส่งออกมี 8 คอลัมน์:

| คอลัมน์ | ประเภท | คำอธิบาย |
|---------|--------|----------|
| timestamp | datetime (UTC) | เวลาเริ่มแท่งเทียน (ISO 8601) |
| open | float | ราคาเปิด |
| high | float | ราคาสูงสุด |
| low | float | ราคาต่ำสุด |
| close | float | ราคาปิด |
| volume | int64 | ปริมาณการซื้อขาย |
| age | int64 | อายุแท่งเทียน (มิลลิวินาที) |
| quality | string | FRESH หรือ STALE |

**quality:**
- `FRESH` — age <= timeframe_seconds × 2 × 1000 ms
- `STALE` — age > timeframe_seconds × 2 × 1000 ms

### ตัวอย่างไฟล์ CSV
```
timestamp,open,high,low,close,volume,age,quality
2026-08-08 22:14:00+00:00,1.142245,1.142535,1.142015,1.142205,0,185688,STALE
2026-08-08 22:15:00+00:00,1.142265,1.143035,1.142245,1.142935,0,125688,STALE
2026-08-08 22:16:00+00:00,1.142945,1.143765,1.142805,1.143545,0,65688,FRESH
```

### ตำแหน่งไฟล์ CSV
```
data_base/csv/iq_option/
├── EURUSD-OTC/
│   ├── EURUSD-OTC_M1.csv
│   ├── EURUSD-OTC_M5.csv
│   └── EURUSD-OTC_M15.csv
├── EURGBP-OTC/
│   ├── EURGBP-OTC_M1.csv
│   ├── EURGBP-OTC_M5.csv
│   └── EURGBP-OTC_M15.csv
├── GBPUSD-OTC/
│   └── ...
└── GBPJPY-OTC/
    └── ...
```

---

## วิธีรัน

```bash
# ใช้ Python 3.12
cd E:\BOT_FINALBOT\FINALBOT_Part1
python runner.py
```

**ข้อกำหนด:**
- ต้องติดตั้ง: iqoptionapi, pandas, numpy
- ต้องมี .env พร้อม credentials
- รันบน CMD/Terminal แบบเปิดเผยเท่านั้น

## การตั้งค่า

แก้ไข `config_setting/settings.json`:
- `account` — บัญชี IQ Option
- `symbols` — รายการสัญลักษณ์ที่ต้องการดึง
- `active_broker` — เลือกโบรกเกอร์
- `data_feed` — ตั้งค่า CSV manager, queue, writer

---

## ล็อกไฟล์

| ไฟล์ | เนื้อหา |
|------|--------|
| `logs/logs_data_feed/all_runtime/runtime.log` | ล็อกทั้งหมด รวม SEC_TRACK (รายวินาที) |
| `logs/logs_data_feed/errors/error.log` | ERROR + CRITICAL |
| `logs/logs_data_feed/warnings/warning.log` | WARNING |
| `logs/logs_data_feed/system_info/info.log` | INFO |
| `logs/logs_data_feed/fallback/fallback.log` | บันทึกทุกครั้งที่ใช้ REST แทน WebSocket |

---

## กฎการทำงาน

ดูรายละเอียดใน `.agents/AGENTS.md`

- Think twice, act once — คิดก่อนทำ ไม่แน่ใจถาม
- Simplicity first — ทำให้ง่ายก่อน
- Surgical changes — แก้เฉพาะจุด
- งานต้อง verify ได้ — ต้องมี test
- No Silent Failures — ห้ามกลืน error
- Fail-Fast — ห้าม fallback ยกเว้นข้อมูลจริงจากโบรกเกอร์
- ทดสอบผ่าน runner.py เท่านั้น
