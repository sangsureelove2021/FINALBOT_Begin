# รายงานตรวจสอบ 3 หลักการคำนวณอินดิเคเตอร์เชิงลึก (Deep Audit Report) — data_evaluate

**วันที่ตรวจสอบ:** 2026-08-11  
**ผู้ตรวจสอบ:** Athena (เอเธน่า) — ตรวจสอบซอร์สโค้ดจริงทุกไฟล์ระดับ Line-by-Line ใน `data_evaluate/`  
**ขอบเขต:** ตรวจสอบตาม 3 หลักการที่ Boss กำหนดครอบคลุมทุกอินดิเคเตอร์ (รวม EMA200, EMA5, EMA10, RSI, MACD, BB, ATR, ADX ฯลฯ)

---

## 📌 สรุปผลการตรวจสอบภาพรวมทั้ง 3 หลักการ

| หลักการ | ผลตรวจสอบ | รายละเอียดสำคัญ |
|---|---|---|
| **1. ข้อมูลราคาจริง** | ✅ **ผ่าน 100%** | ข้อมูลราคาอ่านจาก CSV ที่ตัดแท่งกำลังก่อตัวออกแล้ว (Strict Completed Candle) ไม่มีข้อมูล Mock หรือสุ่ม |
| **2. คำนวณครั้งเดียวต่อรอบ (SSOT)** | ❌ **ไม่ผ่าน (พบ 5 ไฟล์คำนวณซ้ำ)** | พบ 5 ไฟล์ (`conflict_analyzer`, `continuation_analyzer`, `divergence_analyzer`, `persistence_analyzer`, `mtf_engine`) แอบคำนวณ EMA, RSI, MACD เองซ้ำซ้อน ไม่ใช้ค่าจาก SSOT |
| **3. ทุกค่าที่คำนวณต้องถูกใช้** | ❌ **ไม่ผ่าน (พบ Dead Data จำนวนมาก)** | **ema200 ของ M1 และ M15 คำนวณทิ้งเปล่า ไม่ถูกนำไปใช้เลย** (+ ema5, ema10 ทุก TF และฟิลด์อื่นๆ อีกมากกว่า 15 ฟิลด์) |

---

## 🔍 รายละเอียดการตรวจสอบตามหลักการ

### 1. หลักการที่ 1: ระบบต้องคำนวณอินดิเคเตอร์จากข้อมูลราคาที่ถูกต้อง เป็นจริง
**ผลตรวจสอบ: ✅ ผ่าน 100%**

- **Data Pipeline:**
  1. โบรกเกอร์ (IQ Option) → `data_feed/data_adapter.py`
  2. `drop_forming()` ตัดแท่งเทียนที่ยังไม่ปิดออกเสมอ เพื่อรับประกันว่าเป็น Completed Candle 100%
  3. บันทึกลงไฟล์ CSV ใน `data_base/csv/iq_option/<SYMBOL>/`
  4. `orchestrator.py` โหลด CSV ขึ้น RAM
  5. `indicator_store.py` รับ DataFrame ไปคำนวณอินดิเคเตอร์ด้วย Pandas Vectorization
- **การตรวจสอบ:** ไม่พบการสร้างข้อมูล Mock, Random หรือการเดาค่าใดๆ ทุกคำนวณอ้างอิงราคาจริงจาก CSV ดิบ

---

### 2. หลักการที่ 2: ระบบต้องคำนวณอินดิเคเตอร์เพียง 1 ครั้งต่อรอบ (Single Source of Truth - SSOT)
**ผลตรวจสอบ: ❌ ไม่ผ่าน — พบ 5 โมดูลที่แอบคำนวณอินดิเคเตอร์ซ้ำเอง**

แม้อยู่ในโครงสร้าง SSOT ที่ `indicator_store.py` ควรคำนวณให้ทุก Engine ดึงไปใช้ แต่เมื่อตรวจสอบรายบรรทัดพบโมดูลที่แอบคำนวณซ้ำเองดังนี้:

1. **`advanced_tools/conflict_analyzer.py` (บรรทัด 62-63):**
   - แอบคำนวณ `ema20` และ `ema50` ใหม่เองจาก `df['close'].ewm(span=20/50)` แทนที่จะอ่านจาก `payload['m5']['ema20']`
2. **`advanced_tools/continuation_analyzer.py` (บรรทัด 113):**
   - แอบคำนวณ `ema20` ใหม่เองจาก `closes.ewm(span=20)`
3. **`advanced_tools/divergence_analyzer.py` (บรรทัด 76-78):**
   - แอบคำนวณ `ema12` และ `ema26` เพื่อหา MACD Histogram และ RSI ใหม่เองทั้งหมด
4. **`advanced_tools/persistence_analyzer.py` (บรรทัด 78, 142):**
   - แอบคำนวณ `ema20` ใหม่เองถึง 2 จุดจาก `closes`
5. **`market_classifier/mtf_engine.py` (บรรทัด 106-107):**
   - แอบคำนวณ `ema20` และ `ema50` ใหม่เองจาก `df['close']`
6. **ฟังก์ชันซ้ำซ้อน (Logic Duplication):**
   - `context_synthesizer.py` มีฟังก์ชัน `_is_tradeable()` คำนวณซ้ำซ้อนกับ `market_state_classifier.py`

---

### 3. หลักการที่ 3: ทุกการคำนวณอินดิเคเตอร์ ต้องถูกนำไปใช้งานจริง
**ผลตรวจสอบ: ❌ ไม่ผ่าน — พบการคำนวณขยะ (Dead Data) เป็นจำนวนมาก**

#### 🎯 ผลการตรวจเจาะลึก EMA (รวม EMA200):
| Timeframe | อินดิเคเตอร์ | สถานะการใช้งานจริง | โค้ดที่ใช้งาน |
|---|---|---|---|
| **M5** | `ema5`, `ema10` | ❌ **Dead Data (คำนวณทิ้ง)** | ไม่พบการเรียกใช้งานในระบบ |
| **M5** | `ema20`, `ema50`, `ema100`, `ema200` | ✅ **ใช้งานจริง** | `trend_engine.py` (บรรทัด 91-94) และ `market_state_classifier.py` |
| **M1** | `ema20` | ✅ **ใช้งานจริง** | `indicator_store.py` (คำนวณ bias) |
| **M1** | `ema5`, `ema10`, `ema50`, `ema100`, `ema200` | ❌ **Dead Data (คำนวณทิ้ง)** | **ไม่พบการเรียกใช้งานเลยแม้แต่จุดเดียว!** |
| **M15** | `ema20` | ✅ **ใช้งานจริง** | `indicator_store.py` (คำนวณ bias) |
| **M15** | `ema5`, `ema10`, `ema50`, `ema100`, `ema200` | ❌ **Dead Data (คำนวณทิ้ง)** | **`m15['ema200']` ไม่ถูกเรียกใช้เลยแม้แต่จุดเดียว!** |

> ⚠️ **ประเด็นสำคัญเรื่อง EMA200:**
> การที่ `indicator_store.py` สั่งคำนวณ `CoreIndicators.calculate_ema(close_m15, [5, 10, 20, 50, 100, 200])` ส่งผลให้ M1 และ M15 ต้องแบกการคำนวณ `ema200` ไปด้วย ทั้งๆ ที่มีแค่ M5 เท่านั้นที่นำ `ema200` ไปใช้ใน `trend_engine.py` 
> นี่คือสาเหตุหลักที่ทำให้บอทต้องร้องขอแท่งเทียนอุ่นเครื่องมหาศาลโดยไม่จำเป็น!

#### 🔴 รายการ Dead Data อินดิเคเตอร์อื่นๆ ที่คำนวณทิ้งเปล่า:
| ฟิลด์ | Timeframe | ไฟล์ที่คำนวณ | ผลกระทบ |
|---|---|---|---|
| `dx` | M1, M5, M15 | `structural_metrics.py: calc_adx()` | คำนวณทิ้ง ไม่เคยถูกอ่าน |
| `r2`, `s2` | M5 | `indicator_store.py` | คำนวณ Floor Pivot R2/S2 ทิ้งเปล่า |
| `support_20`, `resistance_20` | M5 | `indicator_store.py` | คำนวณทิ้งเปล่า |
| `slope_20`, `slope_50` | M1, M5, M15 | `structural_metrics.py: calc_slope()` | คำนวณทิ้ง ใช้แค่ `slope_10` |
| `atr_zscore`, `atr_recent_avg`, `atr_past_avg` | M1, M5, M15 | `structural_metrics.py: calculate_atr()` | คำนวณทิ้ง ใช้แค่ `atr14` |
| `rsi7` | M1, M5, M15 | `core_indicators.py` | คำนวณทิ้ง ระบบใช้แค่ `rsi14` |
| `volume_ma20`, `volume_spike` | M1, M5, M15 | `structural_metrics.py` | คำนวณทิ้ง ไม่เคยถูกอ่าน |

---

## 🛠️ แผนการปรับปรุงแก้ไข (Implementation Plan Suggestions)

1. **ปรับลด EMA ของ M1 และ M15 ให้เหลือเฉพาะที่ใช้จริง:**
   - **M5:** คำนวณ `[20, 50, 100, 200]` (ลบ 5, 10 ออก)
   - **M1:** คำนวณ `[20]` เท่านั้น (ลบ 5, 10, 50, 100, 200 ออก)
   - **M15:** คำนวณ `[20]` เท่านั้น (ลบ 5, 10, 50, 100, 200 ออก)
   *ผลลัพธ์:* ลดแท่งเทียนอุ่นเครื่องของ M1 และ M15 ลงได้อย่างมหาศาล และลดภาระ CPU

2. **แก้ไข 5 โมดูลที่คำนวณซ้ำ ให้หันมารับค่าจาก SSOT (`indicator_store`):**
   - แก้ไข `conflict_analyzer`, `continuation_analyzer`, `divergence_analyzer`, `persistence_analyzer`, `mtf_engine` ให้ดึงค่า EMA/RSI/MACD จาก `payload` โดยตรง

3. **ลบฟิลด์ขยะ (Dead Data) ออกจาก `indicator_store.py` และ `structural_metrics.py`:**
   - ตัดการคำนวณ `dx`, `r2`, `s2`, `support_20`, `resistance_20`, `slope_20`, `slope_50`, `atr_zscore`, `rsi7`, `volume_ma20` ออกทั้งหมด
