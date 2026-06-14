# FINALBOT — Strategy Specification (Pre-Intelligence Era)

**Status:** Historical reference — กลยุทธ์ก่อนการอัปเกรดเป็น Intelligence OS
**Source:** `FINALSignal_BOT_M5_Strategy_Full.xlsx`
**Era:** SIGNAL_BOT V.1_Plus → FINALSignal_BOT (initial design)

---

## 1. ภาพรวม (Overview)

ในยุคก่อนการเพิ่มเครื่องมือ Intelligence ระบบถูกออกแบบโดยมี **กลยุทธ์เป็นแกนหลัก** ของการตัดสินใจ
ใช้ **Weighted Signal Engine** เป็นกรรมการรวมคะแนน และ **Context Filter System** เป็นตัวกรองสัญญาณ

**โครงสร้างวิวัฒนาการ:**
```
12 กลยุทธ์ (3 หมวดหลัก) → 8 กลยุทธ์สุดท้าย → CALL/PUT
```

---

## 2. กลยุทธ์ทั้ง 12 (Complete Strategy Catalog)

### หมวดที่ 1: Trend-Based Strategies

| # | ชื่อกลยุทธ์ | สภาพตลาด | อินดิเคเตอร์หลัก |
|---|---|---|---|
| 1 | **Trend-Follow Strategy** | Uptrend / Downtrend ชัดเจน | EMA20, EMA50, ADX, RSI |
| 7 | **Trend-Follow (EMA+RSI/MACD) 2025** | Trend ระยะสั้น-กลาง | EMA50, RSI(14), MACD |
| 6 | **Multi-TF Confirmation Strategy** | TF Alignment | RSI(14), EMA20, EMA50 |

**Entry Logic (Strategy 1):**
- EMA20 ตัด EMA50 → CALL
- EMA20 ต่ำกว่า EMA50 → PUT
- RSI > 50 (ขาขึ้น) / RSI < 50 (ขาลง)
- ADX > 25 ยืนยันเทรนด์

---

### หมวดที่ 2: Reversal / Range Strategies

| # | ชื่อกลยุทธ์ | สภาพตลาด | อินดิเคเตอร์หลัก |
|---|---|---|---|
| 2 | **RSI Reversal Strategy** | Sideway / พักตัว | RSI(14), Bollinger Bands(20), MACD |
| 4 | **S/R Bounce Strategy** | Range (กรอบ) | EMA50, ATR, S/R Zone |
| 5 | **Momentum Divergence** | ใกล้กลับตัว | MACD Histogram, RSI Divergence |
| 8 | **Price Action Reversal** | กลับตัวจาก S/R | Engulfing, Hammer, Doji |
| 10 | **Indicator Combo (RSI+CCI+PSAR)** | Sideway / Reversal | RSI(14), CCI(14), PSAR |

**Entry Logic (Strategy 2):**
- RSI > 70 + ราคาทะลุ BB Upper → PUT
- RSI < 30 + ราคาทะลุ BB Lower → CALL
- MACD Histogram เริ่มกลับทิศ

---

### หมวดที่ 3: Breakout / High-Volatility Strategies

| # | ชื่อกลยุทธ์ | สภาพตลาด | อินดิเคเตอร์หลัก |
|---|---|---|---|
| 3 | **Breakout Confirmation Strategy** | Volatile สูง | Bollinger Bands, ATR, Volume Spike |
| 9 | **S/R Breakout** | ทะลุ Zone สำคัญ | S/R Zones, MACD, RSI |

**Entry Logic (Strategy 3):**
- ราคาเบรก High + Volume > 1.5x → CALL
- ราคาเบรก Low + Volume > 1.5x → PUT
- ATR เพิ่มขึ้น > 20% จากค่าเฉลี่ย 14 แท่ง

---

### หมวดพิเศษ: กลยุทธ์ทำเงินสูง (High-Profit)

| # | ชื่อกลยุทธ์ | สภาพตลาด | อินดิเคเตอร์หลัก |
|---|---|---|---|
| 11 | **Price Action + SR** ⭐ | Trend + กลับตัว SR | Pattern + SR + RSI |
| 12 | **Indicator Combo** ⭐ | นิ่ง / เด้งระยะสั้น | RSI, CCI, PSAR, Volume |

**Entry Logic (Strategy 11):**
- สัญญาณกลับตัวที่ SR Zone + RSI < 40 หรือ > 60
- ยืนยันด้วยแท่งเทียนกลับตัว
- ATR ต่ำ → รอแท่งยืนยัน

---

## 3. หัวใจระบบ: Weighted Signal Engine

**สูตรการคำนวณ:**
```
Final_Confidence = Σ(Indicator_Score × Weight) / Σ(Weight)
```

**กฎตัดสินใจ:**
- Confidence > 75% (Threshold) → ส่งสัญญาณ CALL หรือ PUT
- Confidence ≤ 75% → NO SIGNAL

**คุณสมบัติ:**
- รวมคะแนนจากอินดิเคเตอร์หลายตัว (EMA, RSI, ATR, Volume, ...)
- น้ำหนัก (Weight) เก็บใน `ai_weights.json`
- AI Layer สามารถปรับน้ำหนักได้อัตโนมัติ

---

## 4. ตัวกรองชั้นที่สอง: Context Filter System

**Config:** `config/context_rules.json`

**กฎหลัก:**
| สภาพตลาด | การกระทำ |
|---|---|
| Sideway | ยกเลิกสัญญาณเทรนด์ |
| Volatility สูง | ลด Confidence 20% |
| TF Alignment ไม่ตรง | รอสัญญาณใหม่ |
| Trend / Range / Volatile | คัดกรองกลยุทธ์ที่เข้ากับ context |

**บทบาท:** กรอง false signal ก่อนส่งออก

---

## 5. โครงสร้างการตัดสินใจ (Decision Flow)

```
Candle Data (MT4)
        │
        ▼
Indicator Engine (คำนวณ EMA, RSI, ATR, MACD, ...)
        │
        ▼
Strategy Layer (12 กลยุทธ์ทำงาน Parallel)
        │
        ▼ (แต่ละกลยุทธ์ส่ง Score)
Weighted Signal Engine
        │
        ▼
Context Filter System (กรองตามสภาพตลาด)
        │
        ▼
Final Confidence > 75%?
        │
   ┌────┴────┐
  YES        NO
   │          │
   ▼          ▼
CALL/PUT   NO SIGNAL
```

---

## 6. อินดิเคเตอร์ที่ใช้ทั้งหมด (Indicator Inventory)

**Trend / Momentum:**
- EMA20, EMA50
- MACD (12,26,9) + Histogram
- ADX
- PSAR (Parabolic SAR)

**Oscillator:**
- RSI(14)
- CCI(14)

**Volatility / Range:**
- Bollinger Bands(20, 2)
- ATR(14)

**Volume:**
- Volume Spike (>1.5x average)

**Price Action / Pattern:**
- Engulfing
- Hammer
- Doji
- Support / Resistance Zones
- Pivot Points

**Multi-Timeframe:**
- TF Alignment (5M ↔ 15M)
- Cross-TF Confirmation

---

## 7. เปรียบเทียบ: Pre-Intelligence vs Post-Intelligence

| มิติ | ก่อน (12 กลยุทธ์) | หลัง (Intelligence OS) |
|---|---|---|
| **แกนตัดสินใจ** | กลยุทธ์เป็นใหญ่ | Market State เป็นใหญ่ |
| **กลยุทธ์** | 12 ตัว ทำงานพร้อมกัน | 5 templates ตาม Market State |
| **Confidence** | จาก Indicator Score | จาก Market Behavior (29 engines) |
| **Filter** | Context Rules JSON | Trap/Noise/Anomaly Detectors |
| **อำนาจตัดสินขั้นสุดท้าย** | Weighted Engine + Filter | `signal_veto.py` (single gate) |
| **โครงสร้าง** | 80 ไฟล์ / 15 โฟลเดอร์ | 8 Tiers / 29 modules |
| **Layer Separation** | บางส่วนซ้อนกัน | แยกขาด (Intelligence ≠ Strategy ≠ Decision) |
| **V1 Focus** | ทุกกลยุทธ์ทำงานพร้อมกัน | เฉพาะ 5M Compression Breakout |
| **ปรัชญา** | "ยืนยันแล้วเทรด" | "The Art of Saying NO" |

---

## 8. จุดอ่อนของระบบ Pre-Intelligence (Why Refactor)

1. **Strategy Overlap** — กลยุทธ์หลายตัวคำนวณ market type ซ้ำ
2. **Weighted Engine ทำหน้าที่เกินขอบเขต** — ทั้งคำนวณและตัดสินใจในที่เดียว
3. **Filter Layer ชนกับ Strategy** — Strategy บอกเข้า แต่ Filter บอกไม่เข้า
4. **ไม่มีตัวกลางควบคุม** — สัญญาณซ้อนหลายคู่ได้พร้อมกัน
5. **Debug ยาก** — เหตุผลของการ Reject/Approve กระจัดกระจาย
6. **AI Layer มีอำนาจตัดสินใจ** — ไม่ใช่ที่ปรึกษาอย่างเดียว

---

## 9. กลยุทธ์ที่ "รอด" สู่ยุค Intelligence

จาก 12 กลยุทธ์ — มีบางตัวที่ถูกพัฒนาต่อใน Intelligence OS:

| Pre-Intelligence | → | Post-Intelligence Template |
|---|---|---|
| #1 Trend-Follow | → | EMA Pullback Continuation |
| #3 Breakout Confirmation | → | **5M Compression Breakout** ⭐ V1 |
| #9 S/R Breakout | → | Break & Continuation |
| #2 RSI Reversal + #4 S/R Bounce | → | Range Reversal |
| #5 Momentum Divergence + #8 Price Action | → | Exhaustion Reversal |

**V1 ที่เลือก:** Strategy #3 (Breakout Confirmation) ถูกพัฒนาต่อเป็น **5M Volatility Compression Breakout** พร้อม 4 enhancements

---

## 10. สรุป

```
╔══════════════════════════════════════════════════╗
║ PRE-INTELLIGENCE ERA                             ║
║ ─────────────────                                ║
║ Strategies        : 12 (consolidated to 8)       ║
║ Decision Core     : Weighted Signal Engine       ║
║ Threshold         : Confidence > 75%             ║
║ Filter            : Context Rules JSON           ║
║ Authority         : Distributed                  ║
║ Structure         : 80 files / 15 folders        ║
║ Philosophy        : "Confirm → Trade"            ║
║                                                  ║
║ Status: ⚠️ Superseded by Intelligence OS         ║
║ Reason: Logic overlap + authority distribution   ║
╚══════════════════════════════════════════════════╝
```

---

**END OF PRE-INTELLIGENCE STRATEGY DOCUMENT**
*Historical reference — preserved for design lineage*
