# SPEC: INDICATOR STORE — ห้องคำนวณและเก็บ Indicator (Single Source of Truth)

## หลักการประมวลผล (SSOT Principle)
เพื่อประสิทธิภาพสูงสุดและหลีกเลี่ยงความซ้ำซ้อนในสถาปัตยกรรม บอทจะใช้หลักการคำนวณแบบรวมศูนย์ (Single Source of Truth):
```
OHLCV Data ➡️ คำนวณครั้งเดียว (IndicatorStore) ➡️ ส่งต่อผลลัพธ์ผ่านไฟล์และ Payload ➡️ ล้างทิ้งเมื่อครบรอบ
```
* **คำนวณรอบเดียว (60 วินาที):** คำนวณค่าดัชนีดิบ (Raw Indicators) ทั้งหมดจากข้อมูลแท่งเทียนที่ผ่านการคลีนแล้วเพียงครั้งเดียวในแต่ละรอบของการทำงาน
* **ไม่มีการคำนวณซ้ำ:** ห้ามให้โมดูลย่อยใดๆ (Engines/Classifier) คำนวณดัชนีทางเทคนิคด้วยตัวเอง

---

## สถาปัตยกรรมระบบเก็บข้อมูล (File Layout)
ระบบจะทำการแยกการวิเคราะห์คำนวณออกเป็น 3 ไฟล์หลักเพื่อความเป็นระเบียบและง่ายต่อการดูแลรักษา:

1. **`basic_indicators.py`**  
   ทำหน้าที่คิดคำนวณอินดิเคเตอร์ทางเทคนิคทั่วไปตามมาตรฐานสากล (EMA, Bollinger Bands, RSI, MACD, Stochastic, ATR, ADX) โดยใช้ระบบ Pandas Vectorization
2. **`structural_indicators.py`**  
   ทำหน้าที่ประมวลผลดัชนีสถิติเชิงโครงสร้างที่ออกแบบมาสำหรับบอทนี้โดยเฉพาะ (Linear Regression Slope, Volume Ratio, Box Squeeze, Pivot Points, Rate of Change)
3. **`indicator_store.py`**  
   ทำหน้าที่เป็น Orchestrator สำหรับ Layer 1 ในการดึงเอาข้อมูลจากทั้งสองไฟล์ย่อยข้างต้นมารวมกัน จัดระบบล็อก (Thread Lock) เพื่อความปลอดภัย และเป็น Instance Singleton ให้โมดูลอื่นดึงข้อมูลไปใช้

---

## ดัชนีทางเทคนิคที่คำนวณเก็บไว้ (Layer 1: Raw Indicators)

### 1. กรอบเวลา M5 (TF M5 Indicators)
| Indicator | แหล่งคำนวณ | รายการดัชนีและค่าการตั้งค่าหลัก |
|-----------|------------|---------------------------------|
| **EMA** | `BasicIndicators` | `ema5`, `ema10`, `ema20`, `ema50`, `ema100`, `ema200` |
| **Trend Bias** | `BasicIndicators` | `bias` ('BULLISH' เมื่อ Close > EMA20, 'BEARISH' เมื่อ Close <= EMA20) |
| **Bollinger Bands** | `BasicIndicators` | `bb_upper`, `bb_lower`, `bb_width`, `bbw_sma_100` (ค่า BB: 20, 2) |
| **RSI** | `BasicIndicators` | `rsi7`, `rsi14` (RSI ดั้งเดิมแบบ Wilder's Smoothing) |
| **MACD** | `BasicIndicators` | `macd`, `macd_signal`, `macd_hist` (ค่ามาตรฐาน: 12, 26, 9) |
| **Stochastic** | `BasicIndicators` | `stoch_k`, `stoch_d` (ค่ามาตรฐาน: 14, 3, 3) |
| **ATR** | `BasicIndicators` | `atr14`, `atr_percentile`, `atr_zscore`, `atr_recent_avg`, `atr_past_avg` |
| **ADX / DMI** | `BasicIndicators` | `adx`, `di_plus`, `di_minus`, `dx` (ADX 14) |
| **Rate of Change** | `StructuralIndicators` | `roc` (Rate of Change เทียบย้อนหลัง 10 แท่งเทียน) |
| **Volume Analysis** | `StructuralIndicators` | `volume`, `volume_ma20`, `volume_ratio` (ลิมิตสูงสุด 10.0), `volume_spike` (> 2.0) |
| **Slope Analysis** | `StructuralIndicators` | `slope_10`, `slope_20`, `slope_50` (คำนวณด้วย Linear Regression) |
| **Pivot Points** | `StructuralIndicators` | `pivot`, `r1`, `r2`, `s1`, `s2` <br>• **วิธีคำนวณ:** ใช้แท่งเทียน M5 ที่ปิดสมบูรณ์เท่านั้น (ไม่ใช่แท่งก่อนตัว) <br>• **สูตร:** Pivot = (High + Low + Close) / 3 ของแท่งที่ปิดสมบูรณ์ <br>• **การเลือกแท่ง:** เมื่อมีหลายแท่ง M5 ใช้แท่งที่สองจากท้าย (iloc[-2]) เป็นแท่งเทียนที่ปิดสมบูรณ์ <br>• **กรณีพิเศษ:** เมื่อมีแค่ 1 แท่งใช้ iloc[-1] แท่งเทียนเป็นแท่งที่ปิดสมบูรณ์ |
| **Box Metrics** | `StructuralIndicators` | `box_duration` (จำนวนแท่งที่ไซด์เวย์), `box_tightness` (ความแคบเทียบกับ ATR) |

### 2. กรอบเวลา M1 (TF M1 Indicators)
| Indicator | แหล่งคำนวณ | รายการดัชนีและค่าการตั้งค่าหลัก |
|-----------|------------|---------------------------------|
| **EMA** | `BasicIndicators` | `ema5`, `ema10`, `ema20`, `ema50` |
| **RSI** | `BasicIndicators` | `rsi7`, `rsi14` |
| **MACD** | `BasicIndicators` | `macd`, `macd_signal` |
| **Stochastic** | `BasicIndicators` | `stoch_k`, `stoch_d` |
| **ATR** | `BasicIndicators` | `atr14` |
| **Bollinger Bands** | `BasicIndicators` | `bb_upper`, `bb_lower` |
| **Pivot Points** | `StructuralIndicators` | `pivot`, `r1`, `s1` |
| **Volume Analysis** | `StructuralIndicators` | `volume`, `volume_ratio` |

### 3. กรอบเวลา M15 (TF M15 Indicators)
* **Trend Bias (`bias`):** 'BULLISH' หรือ 'BEARISH' ประเมินจากความสัมพันธ์ระหว่างราคาปิดกับเส้น EMA20 ของแท่ง M15
* **Fail-Fast Safety Check:** หากแท่ง M15 ล่าสุดมีอายุข้อมูลเกิน 40 นาที (`m15_age_ms > 2400000`) ระบบจะเกิด Error หยุดการทำงานทันทีเพื่อป้องกันสัญญาณเก่าล้าสมัยทำงานผิดพลาด

---

## โครงสร้างข้อมูล Metadata ความสมบูรณ์ของแท่งเทียน (Forming & Age Data)
ในแต่ละรอบการสร้าง Payload จะเก็บความสมบูรณ์ของข้อมูลไว้ในส่วนหัว (`meta`) เสมอ:
* **Session Classification:** จำแนกตามเวลาสากล UTC:
  - `00:00 - 07:00 UTC` ➡️ **SYDNEY/TOKYO**
  - `07:00 - 12:00 UTC` ➡️ **LONDON_OPEN**
  - `12:00 - 16:00 UTC` ➡️ **NY/LONDON_OVERLAP**
  - `16:00 - 21:00 UTC` ➡️ **NY_AFTERNOON**
  - `21:00 - 24:00 UTC` ➡️ **SYDNEY_OPEN**
* **Candle Age & Quality:**
  - `m1_open` / `m5_open`: ราคาเปิดของแท่งเทียนกำลังก่อตัว
  - `m1_age` / `m5_age`: เวลาอายุแท่งเทียนที่รอข้อมูล
  - `m1_quality` / `m5_quality`: สถานะความสดใหม่ของข้อมูล (เช่น `MEDIUM`, `STALE`)

---

## กฎเหล็กความปลอดภัย (Security Constraints)
1. **ห้ามมีค่า NaN หรือ Null:** หากฟังก์ชันคำนวณ Linear Regression หรือการป้อนค่าดัชนีใดๆ ประสบปัญหาข้อมูลขาดช่วงจนเกิดค่า `NaN` หรือหารด้วยศูนย์ (`ZeroDivisionError`) ระบบจะต้องยกเลิกกระบวนการทำงานทันที (Fail-Fast)
2. **ขีดจำกัด Volume Ratio:** ค่าอัตราส่วนความแรงปริมาณซื้อขาย (`volume_ratio`) จะถูกคำนวณและจำกัดเพดานความแรงไว้ที่ระดับสูงสุดไม่เกิน `10.0` เท่า เพื่อป้องกันค่ากระโดดผิดธรรมชาติส่งผลเสียหายต่อระบบวิเคราะห์ในขั้นตอนถัดไป
3. **การเข้าถึงแบบ Read-Only:** เมื่อผ่านการคำนวณจาก `IndicatorStore` ในขั้นตอนการจัดเตรียม Payload เรียบร้อยแล้ว ข้อมูลจะถือเป็นข้อมูลถาวรที่ไม่สามารถแก้ไขค่าระหว่างทางได้ (Immutability) เพื่อความเสถียรของลอจิกการเทรด
