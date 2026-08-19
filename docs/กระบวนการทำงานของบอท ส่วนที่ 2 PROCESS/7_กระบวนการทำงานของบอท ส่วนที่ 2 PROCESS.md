# 🧠 FINALBOT - กระบวนการทำงานของบอท ส่วนที่ 2: PROCESS (Data Evaluate)

## 🎯 ทำความเข้าใจได้ทันที
ส่วนงานที่ 2 (PROCESS) คือ **"สมองกลวิเคราะห์ข้อมูลและมิติพฤติกรรมตลาด"** ที่ตั้งอยู่ในโฟลเดอร์ `data_evaluate/` มีหน้าที่รับข้อมูลแท่งเทียน (M1, M5, M15) จาก RAM ผ่าน `runner.py` มาคำนวณผ่านอินดิเคเตอร์, 10 เครื่องมือวิเคราะห์พฤติกรรมขั้นสูง (Advanced Tools) และระบบ Tier 1-6 Engines เพื่อสร้างเป็น **"แพ็กเกจข้อมูล Prompt Payload ความยาว 100 บรรทัด (.txt)"** สำหรับส่งต่อให้ AI (ส่วนที่ 3) นำไปตัดสินใจ โดยส่วนงานที่ 2 จะทำหน้าที่ "วิเคราะห์และรายงานผล" เท่านั้น จะไม่มีการตัดสินใจยิงออร์เดอร์ใดๆ ทั้งสิ้น

---

## 🏗️ โครงสร้างหลักของโปรเจกต์และขอบเขตส่วนงาน

**โครงสร้างหลักของโปรเจกต์:**
- `runner.py` คือผู้ควบคุมทิศทางและจับจังหวะเวลารายวินาที
- `config_setting/` คือโฟลเดอร์สำหรับเก็บไฟล์การตั้งค่าทั้งหมด
- `data_feed/` คือระบบดึงและตรวจสอบข้อมูล OHLCV (ส่วนที่ 1)
- `data_evaluate/` คือระบบสมองกลประมวลผลข้อมูลและพฤติกรรม (ส่วนที่ 2)
- `data_base/orchestrator/` คือคลังเก็บไฟล์ผลลัพธ์ Prompt Payload 100 บรรทัด

---

## 🚨 กฎการทำงานและกติกาข้อบังคับ (Strict Rules)

1. **ดึงข้อมูลจากแหล่งเดียว (Single Source of Truth):**
   - การคำนวณอินดิเคเตอร์พื้นฐานทำที่ `indicator_store.py` ครั้งเดียว แล้วส่งต่อให้โมดูลอื่นใช้งานร่วมกัน ไม่มีการคำนวณซ้ำซ้อน

2. **กฎการแตกหัก (Fail-Fast Policy & No Silent Failures):**
   - หากเจอข้อผิดพลาดของข้อมูลหรือคำนวณไม่ได้ ระบบต้องหยุดและแจ้งข้อผิดพลาดทันที ห้ามกลืน Error ด้วย `try-except` ว่างเด็ดขาด

3. **ห้ามมี Mock เด็ดขาด (No Mocks & Real Implementation):**
   - ทุกค่าต้องคำนวณจากคณิตศาสตร์และแท่งเทียนจริง ห้ามใช้ข้อมูลจำลองหรือค่าสุ่มหลอกระบบ

4. **ไม่ใช่ผู้ตัดสินใจขั้นสุดท้าย (Analysis Only):**
   - หน้าที่ของส่วนงานที่ 2 สิ้นสุดเมื่อสร้างเอกสาร Prompt Payload 100 บรรทัดสำเร็จ โดยในหมวด `decision_layer:` จะคงสถานะเป็น "รอการวิเคราะห์จาก AI"

---

## 🏗️ แผนผังสถาปัตยกรรมการประมวลผล 8 ขั้นตอน

```mermaid
flowchart TD
    A[runner.py @ :01.500s] -->|Send candles_dict in RAM| B[orchestrator.py]
    
    subgraph Step 1: SSOT Basic Indicators
    B --> C[indicator_store.py]
    C -->|EMA, BB, RSI, Stoch, MACD, ADX, ATR, Pivot| D[basic_payload]
    end
    
    subgraph Step 2: 10 Advanced Behavioral Tools
    D --> E[advanced_tools_manager.py]
    E --> E1[PriceActionHandler]
    E --> E2[CandlePatternAnalyzer]
    E --> E3[TrapDetector]
    E --> E4[BehaviorAnalyzer]
    E --> E5[ConflictAnalyzer]
    E --> E6[ContinuationAnalyzer]
    E --> E7[DivergenceAnalyzer]
    E --> E8[EfficiencyAnalyzer]
    E --> E9[PersistenceAnalyzer]
    E --> E10[TransitionAnalyzer]
    end
    
    subgraph Step 3: Tier 1 Core Engines
    E --> F{Parallel Core Engines}
    F --> F1[TrendEngine]
    F --> F2[StrengthEngine]
    F --> F3[VolatilityEngine]
    F --> F4[StructureEngine]
    F --> F5[MTFEngine]
    end
    
    subgraph Step 4: Tier 2 Market State Classification
    F1 & F2 & F3 & F4 & F5 --> G[MarketStateClassifier]
    end
    
    subgraph Step 5: Tier 3-5 Supplementary Engines
    G --> H{Parallel Supplementary}
    H --> H1[MarketStructureEngine]
    H --> H2[MarketPressureAnalyzer]
    H --> H3[NoiseDetector]
    H --> H4[LiquidityEngine]
    end
    
    subgraph Step 6: Tier 6 Synthesis & Probability
    H1 & H2 & H3 & H4 --> I[MarketContext Linkage]
    I --> I1[ContextSynthesizer]
    I --> I2[ProbabilityEstimator]
    I --> I3[ExplainabilityEngine]
    I --> I4[SignalThrottle]
    end
    
    subgraph Step 7: Output Prompt Formatting
    I1 & I2 & I3 & I4 --> J[Format 100-Line Prompt]
    J --> K[data_base/orchestrator/SYMBOL/SYMBOL_TIMESTAMP.txt]
    end
```

---

## 📄 โครงสร้างไฟล์ Prompt Payload 100 บรรทัด (Standard Format)

ไฟล์ผลลัพธ์ที่สร้างขึ้นจะถูกบันทึกที่ `data_base/orchestrator/{SYMBOL}/{SYMBOL}{TIMESTAMP}.txt` โดยมีโครงสร้างมาตรฐาน 100 บรรทัด แบ่งออกเป็น 7 หมวดหมู่หลัก:

1. **`meta:`** (ข้อมูลจำเพาะสินทรัพย์, เวลา, คุณภาพแท่งเทียน `m1_quality`, `m5_quality` ที่เป็น `FRESH` หรือ `STALE`)
2. **`market_context:`** (สภาวะตลาด 10 รูปแบบ, ระดับความผันผวน, ผลกระทบข่าวเศรษฐกิจ)
3. **`timeframes:`** (ข้อมูลอินดิเคเตอร์และราคาเปิด/ปิดของ M1, M5, M15 พร้อมคำนำหน้าระบุ Timeframe ชัดเจน เช่น `m1_ema5`, `m5_rsi`, `m15_bias`)
4. **`price_action:`** (แพทเทิร์นและจิตวิทยาแท่งเทียน M5 พร้อม Prefix `m5_pa_` เช่น `m5_pa_divergence_alert`, `m5_pa_hesitation_score`, `m5_pa_path_efficiency`)
5. **`volume:`** (ปริมาณซื้อขาย M5 พร้อม Prefix `m5_` เช่น `m5_tick_volume`, `m5_volume_momentum`, `m5_volume_vs_average`)
6. **`analysis:`** (ทิศทางเทรนด์ M5, MTF Alignment, ความเสี่ยงเปลี่ยนสภาวะ เช่น `m5_trend_direction`, `mtf_alignment_%`, `m5_trend_continuation_%`)
7. **`decision_layer:`** (ระดับความเสี่ยง, คะแนนเสถียรภาพ `dl_tradeable`, `dl_stability_score` และ 4 ฟิลด์สุดท้ายรอรับการวิเคราะห์จาก AI `ai_confidence_score`, `ai_suggested_expiry_minutes`, `ai_suggested_action`, `ai_final_reason_th`)

---

## 🛡️ นโยบายการจัดเก็บและทดสอบ (Retention & System Verification)
- **นโยบายการจัดเก็บไฟล์ (Auto Retention Policy):** เพื่อป้องกันพื้นที่จัดเก็บข้อมูลบวม ระบบจะรักษาไฟล์ Prompt Payload ไว้ไม่เกิน **30 ไฟล์ล่าสุดต่อคู่เงิน** โดยระบบจะทำการลบไฟล์ที่เก่าที่สุดทิ้งโดยอัตโนมัติทุกครั้งที่มีการบันทึกรอบใหม่
- **การทดสอบความถูกต้อง:** รันสดผ่าน `runner.py` เท่านั้น
- **ความเร็วในการประมวลผล:** ทำงานเสร็จสิ้นภายใน 0.2-0.5 วินาทีต่อ 4 คู่เงิน
- **ความสมบูรณ์:** ผ่านการทดสอบระดับบรรทัด ไร้จุดคำนวณซ้ำซ้อน และพร้อมส่งต่อให้ Part 3 ใช้งาน 100%
