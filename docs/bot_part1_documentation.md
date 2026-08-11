# เอกสารสรุปการทำงานของระบบ (FINALBOT - ส่วนงานที่ 1: Data Feed System) ฉบับสมบูรณ์

เอกสารฉบับนี้อธิบายโครงสร้างและการทำงานของบอทอย่างเจาะลึก โดยครอบคลุม **ทุกไฟล์** ในโปรเจกต์ `FINALBOT_Part1` และเจาะจงลงรายละเอียดกลไก **วิธีการดึงข้อมูลและจัดการไทม์เฟรม M1 (1 นาที)** แบบ Step-by-Step เพื่อให้เข้าใจสถาปัตยกรรมและนำไปตรวจสอบได้โดยง่าย

---

## 1. ภาพรวมของระบบ (System Overview)
ระบบ `FINALBOT_Part1` เป็นหัวใจหลักในการดึงและประมวลผลข้อมูลตลาดแบบสด (Data Ingestion & Feed) ทำหน้าที่เชื่อมต่อโบรกเกอร์เพื่อรับข้อมูล OHLCV ตรวจสอบคุณภาพ ปรับแต่งเวลา (Time Synchronization) และบันทึกลงหน่วยความจำหลัก (RAM) เพื่อให้การดึงราคาแบบวินาทีเป็นไปอย่างรวดเร็ว พร้อมกับการส่งข้อมูลไปเขียนลงดิสก์ (CSV) เป็นพื้นหลัง (Background queue)

---

## 2. โครงสร้างและการทำงานของทุกไฟล์ในโปรเจกต์ (File Directory Breakdown)

### 2.1 ไฟล์หลัก (Root Files)
- **`main.py`**: จุดเริ่มต้น (Entry Point) ทำการกำหนดค่าตัวแปรสิ่งแวดล้อม ตั้งค่า Logger และเรียกให้ `PureAIRunner` เริ่มต้นกระบวนการ Live Mode
- **`runner.py`**: หัวใจหลักของระบบ (Main Controller) ควบคุมวงจรทำงานหลัก (Run Cycle) โหลดการตั้งค่าทั้งหมด ซิงค์เวลา และยิงคำสั่งดึงข้อมูล M1, M5, M15 แบบคู่ขนาน (Multi-threading) ตลอดจนการนับถอยหลังรอขอบเวลา (Countdown to exact minute boundary)
- **`.env`, `.env.example`, `.gitignore`**: ไฟล์ตั้งค่า Environment ตัวอย่าง และการละเว้นไฟล์ไม่ให้ส่งขึ้น Git

### 2.2 โฟลเดอร์ `config_setting/` (ระบบจัดการตั้งค่า)
- **`config_loader.py`**: ตัวโหลดค่าตั้งค่าเป็น Single Source of Truth ดึงข้อมูลจากไฟล์ JSON และส่งให้ระบบอื่นๆ นำไปใช้ (ป้องกันการตั้งค่ากระจัดกระจาย)
- **`settings.json`**: ไฟล์ Config หลัก (กำหนดรหัสผ่านโบรกเกอร์, สินทรัพย์, เงื่อนไขบัญชี และความถี่ของการดึง)
- **`symbol_mapper.json`**: คลังข้อมูลอ้างอิงชื่อคู่เงิน (Symbol) ที่อาจแตกต่างกันระหว่างระบบภายในและโบรกเกอร์

### 2.3 โฟลเดอร์ `data_feed/` (ระบบดึงข้อมูลและจัดการฐานข้อมูล)
- **`data_adapter.py`**: (Coordinator) ศูนย์กลางคอยสั่งการดึงข้อมูลจาก Broker, ส่งต่อให้ Validator ตรวจสอบ, อัปเดต RAM Cache และโยนใส่คิว CSV
- **`csv_manager.py`**: ตัวจัดการพาธและชื่อไฟล์ (เช่น วางแผนโครงสร้างโฟลเดอร์ `data_base/csv/iq_option/EURUSD_M1.csv`)
- **`csv_queue.py`**: ระบบคิว (Queue) รองรับ DataFrames เพื่อรอเขียนลงดิสก์ ช่วยกระจายคิวโดยไม่ทำให้เกิด Thread Blocking
- **`csv_writer.py`**: Worker Thread พิเศษที่รับคิวจาก `csv_queue.py` มาเขียนเป็นไฟล์ CSV 
- **`csv_time_sync.py`** (`TimeSyncManager`): โมดูลวัดความต่างของเวลา (Offset) ระหว่างเซิร์ฟเวอร์กับเวลาท้องถิ่น ช่วยให้ระบบยิง API ดึงข้อมูลได้ตรงจังหวะเวลาจริงมากที่สุด
- **`data_processor.py`**: แหล่งรวมลอจิกการคำนวณแท่งเทียน เช่น `process_candle_refresh()`, ฟังก์ชันตัดแท่งที่ยังไม่จบ (drop forming) และฟังก์ชันเติมข้อมูลอายุกับคุณภาพ
- **`data_validator.py`**: ตรวจสอบมาตรฐานข้อมูล บังคับโครงสร้าง 8 คอลัมน์, จัด Timezone เป็น UTC และป้องกันข้อมูล Overlap 
- **`data_cache_store.py`**: ระบบหน่วยความจำ (RAM Cache) เก็บแท่งเทียนสมบูรณ์พร้อมราคาล่าสุด ลดภาระ Disk I/O จนเป็นศูนย์เมื่อระบบทำงานแบบสด
- **`exceptions.py`**: คลาส Error ที่เจาะจงกับ Data Feed เช่น `DataGapError`

### 2.4 โฟลเดอร์ `data_feed/bridge_adapter/` (ตัวเชื่อมต่อโบรกเกอร์)
- **`abstract_class.py`**: สัญญาข้อตกลง (Interface: `IDataSource`) สำหรับบังคับให้ทุก Broker ที่สร้างขึ้นต้องมีเมธอดมาตรฐาน (เช่น `get_candles`)
- **`broker_factory.py`**: โรงงาน (Factory) สร้าง Object ตัวเชื่อมต่อของแต่ละโบรกเกอร์ตามที่กำหนดใน Config
- **โฟลเดอร์ `bridge_iq_adapter/`, `bridge_pocket_adapter/`, `bridge_quotex_adapter/`**: การสร้างโค้ดเชื่อมต่อกับ API หรือ WebSocket ของโบรกเกอร์ค่ายนั้น ๆ (ระบบหลักใช้ IQ Option)

### 2.5 โฟลเดอร์ `monitoring/` (ระบบติดตามการทำงาน)
- **`console_dashboard.py`**: จัดการพิมพ์ผลลัพธ์ลงบนหน้าต่าง Command Line/Terminal รายงานสถานะราคา, วินาที, Latency, และยอดเงินบัญชี
- **`logger.py`, `error_detector.py`, `health_monitor.py`, `performance_monitor.py`, `reporter.py`, `signal_notifier.py`**: ตัวช่วยวิเคราะห์ประสิทธิภาพ ทรัพยากรเครื่อง บันทึกข้อผิดพลาด (Traceback) และคอยเตือนหากมีจังหวะเวลาแฝง (Latency) ผิดปกติ
- **`advanced_dashboard/`**: เครื่องมือส่วนเสริมสำหรับ UI ขั้นสูงอื่น ๆ 

### 2.6 โฟลเดอร์ `data_evaluate/` (ระบบประเมินผล - ส่วนประกอบหลักของ Part 2-3)
แม้จะเป็นโมดูลของพาร์ทการประเมิน แต่ได้มีการเตรียมไฟล์ไว้ดังนี้:
- **`orchestrator.py`**: หัวเรือใหญ่ในการสั่งรัน Pipeline แจกจ่ายงานและประเมินผลข้อมูล
- **`economic_news_calendar.py`**: ประมวลผลและดาวน์โหลดข้อมูลปฏิทินข่าว
- **`exceptions.py`**: Exception พิเศษฝั่ง Evaluate
- **`models/`**: กลุ่มโดเมนออบเจกต์ (Data classes) เช่น `candle.py`, `market_context.py`, `engine_output.py`, `score.py`, `signal.py`
- **`orchestration/`**: ห้องเครื่องหลัก (Pipelines) ในการวิเคราะห์ แบ่งเป็น `pipeline.py`, `base_engine.py`, `context_builder.py`, `context_synthesizer.py`, `explainability_engine.py`, `liquidity_engine.py`, `noise_detector.py`, `probability_estimator.py`, `signal_throttle.py`, `trap_detector.py`, `engine_registry.py`, `engine_setup.py` และมีระบบเครื่องมือย่อยใน `advanced_tools`, `indicator_store`, `market_classifier`, `scoring`
- **`interfaces/`**: รวม Interface ของฝั่ง Evaluate (`context_interface.py`, `engine_interface.py`, `strategy_interface.py`) และโฟลเดอร์ `exceptions`
- **`regime_output/`**: โฟลเดอร์ที่เก็บเอาต์พุตของการวิเคราะห์ตลาดเป็นช่วงเวลา (เช่น `EURUSD_M5_regime.csv`)

### 2.7 โฟลเดอร์ `data_base/` (ฐานข้อมูลดิบ)
- **`calendar/`**: จุดเก็บปฏิทินข่าวเศรษฐกิจ
- **`csv/`**: ศูนย์รวมปลายทางของแท่งเทียนที่สมบูรณ์แล้ว แยกเก็บตามโบรกเกอร์และคู่เงิน (เช่น `iq_option/EURUSD_M1.csv`)

---

## 3. เจาะลึกกลไกการดึงข้อมูลและจัดการไทม์เฟรม M1 (The M1 Fetching Pipeline)

ข้อมูลแท่งเทียนราย 1 นาที (M1) เป็นความถี่สูงที่สุดในระบบ การจัดการกับข้อมูล M1 จะทำงานผ่านหลายไฟล์ผสานกัน ดังลำดับต่อไปนี้:

### Step 1: การเตรียมจังหวะ (Sync & Countdown) - `runner.py`
- **Time Offset Sync:** `csv_time_sync.py` จะเทียบเวลาเครื่องเซิร์ฟเวอร์กับเวลาท้องถิ่นเพื่อหาค่าหน่วงเวลา
- **Countdown to Exact Boundary:** `runner.py` จะเรียก `_countdown_to_first_candle()` รอจนถึงขอบนาทีเป๊ะ ๆ (เวลาวินาทีเข้าสู่ `:01.500` ของนาทีใหม่) เพื่อให้มั่นใจว่าแท่งเทียน M1 ของนาทีที่แล้วได้รับการสั่ง **ปิดแท่ง (Close)** จากเซิร์ฟเวอร์โดยสมบูรณ์

### Step 2: สั่งดึงข้อมูลคู่ขนาน (Concurrent Fetching) - `runner.py` สั่ง `data_adapter.py`
- `runner.py` ใช้ `ThreadPoolExecutor` ส่งคำสั่ง `update()` ไปยังทุกคู่เงินพร้อมๆ กัน 
- ใน `data_adapter.py` (เมธอด `update()`) จะเช็ค Current Block ของ M1 โดยเอา Epoch เซิร์ฟเวอร์หาร 60 วินาที 
- หากบล็อกเปลี่ยนไป (ขึ้นนาทีใหม่) ระบบจะกระตุ้น `process_candle_refresh()` จาก `data_processor.py` ให้ทำงาน 

### Step 3: ประมวลผลและหั่นส่วนเกิน (Refresh & Drop Forming) - `data_processor.py`
- ระบบสั่ง API โบรกเกอร์ (ผ่าน `abstract_class.py` ไปยัง `bridge_iq_adapter`) ขอดึงแท่งเทียน M1 จำนวน 110 แท่งล่าสุด (100 แท่งจริง + 10 แท่งเผื่อสำรอง)
- **Merge & Continuity Check:** นำข้อมูล 110 แท่งใหม่มาเช็ค Gap เทียบกับชุดที่อยู่ใน RAM หาก Gap ขาดหายเกินกำหนดตามกฎ 300 วินาที (_M1_GAP_SEC) ระบบจะทริกเกอร์ `DataGapError` 
- **Drop Forming:** ฟังก์ชัน `drop_forming()` จะรับเวลา Epoch ปัจจุบันมาหักล้าง ถ้าแท่งสุดท้ายเวลายังไม่ถึง 60 วินาทีตามอายุของมัน แปลว่า **"ยังฟอร์มตัวไม่เสร็จ"** ระบบจะตัดทิ้ง (Drop) ทันที
- **Add Quality Metadata:** ฟังก์ชัน `add_age_and_quality()` จะคำนวณระยะเวลา (เป็น ms) เทียบอายุของแท่งเทียน หากพบว่ามีอายุไม่เกินขอบเขตที่ตั้งไว้ แท่งเทียนนั้นจะได้รับสถานะ **`FRESH`** ไม่เช่นนั้นจะเป็น **`STALE`**

### Step 4: ตรวจสอบขั้นสุดท้าย (Validation) - `data_validator.py`
- ตัว Validator จะบังคับดัดแปลงคอลัมน์ให้อยู่ในโหมดโครงสร้าง 8 คอลัมน์มาตรฐาน (Timestamp, Open, High, Low, Close, Volume, Age, Quality) และปรับค่าเวลาให้อยู่ในรูปแบบ UTC เสมอ 

### Step 5: จัดเก็บและบันทึกลงดิสก์ (RAM to Disk) - `data_adapter.py` สู่ `csv_queue.py`
- ข้อมูล M1 ที่ตรวจสอบเสร็จและได้รับการอนุมัติ จะถูกเซฟอัปเดตลงตัวแปรในหน่วยความจำ (`RAMCacheStore` ภายใน `data_adapter.py`) 
- ในขณะเดียวกัน ข้อมูลก้อนนั้นจะถูกสำเนาส่งให้ `CSVQueue` 
- `csv_writer.py` ซึ่งทำงานแบบ Background จะดึงคิวไปทยอยเขียนทับลงไฟล์ที่ `data_base/csv/iq_option/EURUSD_M1.csv` 
- ท้ายสุดในแต่ละวินาที `runner.py` จะเรียก `get_latest_close()` ไปอ่านค่าปิดล่าสุดจาก RAM เพื่อโชว์ราคาที่หน้าจออย่างรวดเร็ว ปราศจากหน่วงรั้งของการอ่านเขียนฮาร์ดดิสก์ (Zero Disk I/O on Reading)

---

> [!IMPORTANT]
> **ระบบ M1 ทั้งหมดผูกติดกับกฎ Fail-Fast:** ระหว่างกระบวนการนี้ ไม่ว่าจะเป็นการโหลดไฟล์ `.json`, การเชื่อมต่อ API ขาด, หรือเจอช่องโหว่ข้อมูลแบบ Overlap/Gap ระบบจะยุติสคริปต์ (Sys Exit) พ่นแจ้งเตือน Error บนหน้าจอทันที เพื่อป้องกันข้อมูลปนเปื้อน (Silent Failure is completely prohibited)
