# คำสั่งปฏิบัติงานสำหรับ ds (DeepSeek Agent): ปรับปรุงระบบตามหลักการ 3 ข้อ (Clean Code & SSOT)

**วัตถุประสงค์:** แก้ไขซอร์สโค้ดใน `data_evaluate/` เพื่อล้างคำนวณขยะ (Dead Data), ขจัดโค้ดคำนวณซ้ำซ้อน (SSOT Violation) และปรับจำนวนแท่งเทียนอุ่นเครื่องให้ถูกต้องตามการใช้งานจริง 100%

---

## 📌 สรุปรายการงานที่ต้องแก้ไข (Task List)

### งานที่ 1: ปรับลดคำนวณ EMA และตัด Dead Data ใน `indicator_store.py` และ `structural_metrics.py`

#### 1.1 ปรับการคำนวณ EMA ใน `indicator_store.py` ให้เหลือเฉพาะค่าที่ถูกใช้งานจริง
- **M5 (`close_m5`):** เปลี่ยนการเรียกใช้เป็น `CoreIndicators.calculate_ema(close_m5, [20, 50, 100, 200], Config.ROUND_DECIMALS)` (ตัด 5, 10 ออก)
- **M1 (`close_m1`):** เปลี่ยนการเรียกใช้เป็น `CoreIndicators.calculate_ema(close_m1, [20], Config.ROUND_DECIMALS)` (ตัด 5, 10, 50, 100, 200 ออก)
- **M15 (`close_m15`):** เปลี่ยนการเรียกใช้เป็น `CoreIndicators.calculate_ema(close_m15, [20], Config.ROUND_DECIMALS)` (ตัด 5, 10, 50, 100, 200 ออก)

#### 1.2 ปรับเกณฑ์ Fail-Fast Warm-up Candles ตอนต้นฟังก์ชัน `calculate_raw_indicators`
- **M5:** ปรับเป็นขั้นต่ำ **200 แท่ง** (ตรงกับความต้องการของ EMA 200)
  ```python
  if df_m5 is None or df_m5.empty or len(df_m5) < 200:
      raise ValueError("FAIL-FAST: Insufficient M5 warm-up candles (minimum 200 required)")
  ```
- **M1:** ปรับเป็นขั้นต่ำ **100 แท่ง** (ตรงกับความต้องการของ Bollinger Bands)
  ```python
  if df_m1 is None or df_m1.empty or len(df_m1) < 100:
      raise ValueError("FAIL-FAST: Insufficient M1 warm-up candles (minimum 100 required)")
  ```
- **M15:** ปรับเป็นขั้นต่ำ **100 แท่ง** (ตรงกับความต้องการของ Bollinger Bands)
  ```python
  if df_m15 is None or df_m15.empty or len(df_m15) < 100:
      raise ValueError("FAIL-FAST: Insufficient M15 warm-up candles (minimum 100 required)")
  ```

#### 1.3 ลบฟิลด์ Dead Data ที่ไม่เคยถูกใช้งานออก
- ใน `indicator_store.py`:
  - ลบ `r2`, `s2`, `support_20`, `resistance_20` ออกจาก `m5`
  - ลบ `slope_20`, `slope_50` ออกจาก `m5`, `m1`, `m15`
  - ลบ `rsi7` ออกจาก `m5`, `m1`, `m15`
- ใน `structural_metrics.py`:
  - ลบ `dx` ออกจากผลลัพธ์ของ `calc_adx()`
  - ลบ `atr_zscore`, `atr_recent_avg`, `atr_past_avg` ออกจากผลลัพธ์ของ `calculate_atr()`

---

### งานที่ 2: ขจัดโค้ดคำนวณซ้ำซ้อนใน 5 โมดูล (บังคับใช้ SSOT จาก `indicator_store`)

แก้ไขโมดูลต่อไปนี้ไม่ให้แอบคำนวณ EMA, RSI หรือ MACD ใหม่เองจาก DataFrame แต่ให้ดึงค่าจาก `payload` หรือ `m5` dictionary ที่ส่งผ่านเข้ามาแทน:

1. **`advanced_tools/conflict_analyzer.py`:**
   - แก้ไข `_ema_direction()` ให้ดึงค่า `ema20`, `ema50` และ `close` จาก `m5` payload แทนการสั่ง `df['close'].ewm(...)`
2. **`advanced_tools/continuation_analyzer.py`:**
   - แก้ไข `_assess_pullback()` ให้ดึงค่า `ema20` จาก `m5` payload แทนการสั่ง `closes.ewm(span=20)`
3. **`advanced_tools/divergence_analyzer.py`:**
   - ยกเลิกการคำนวณ `_calculate_rsi()` และ `_calculate_macd_hist()` ซ้ำ ให้เปลี่ยนมาดึงค่า `rsi14` และ `macd_hist` จาก `m5` payload โดยตรง
4. **`advanced_tools/persistence_analyzer.py`:**
   - แก้ไขจุดที่สั่ง `closes.ewm(span=20)` ให้เปลี่ยนมาดึงค่า `ema20` จาก `m5` payload
5. **`market_classifier/mtf_engine.py`:**
   - แก้ไขจุดที่สั่ง `df['close'].ewm(span=20/50)` ให้รับและใช้ค่า `ema20`, `ema50` จาก `payload`

---

### งานที่ 3: ลบฟังก์ชันตรรกะซ้ำซ้อน
- ใน `context_synthesizer.py`: ลบฟังก์ชัน `_is_tradeable()` ที่ซ้ำซ้อนออก หรือปรับให้อ้างอิงผลลัพธ์จาก `market_state_classifier.py` เพื่อป้องกัน Logic Conflict

---

## ⚠️ ข้อบังคับในการทดสอบและการยืนยันผล (Strict Verification Rules)

1. **ห้ามใช้ `python -m py_compile` หรือสร้างสคริปต์แยกทดสอบ:** การทดสอบต้องทำผ่าน `python runner.py` เท่านั้น (กฎข้อ 13)
2. **เมื่อทดสอบรันเสร็จต้อง Kill Process ทันที:** หลังสั่งรัน `python runner.py` เพื่อยืนยันว่าบอทเชื่อมต่อและคำนวณข้อมูลได้โดยไม่มี KeyError หรือ Crash ให้ทำการยุติการทำงานทันที (กฎข้อ 14)
