# 🎯 FINALBOT - กระบวนการทำงานของบอท ส่วนที่ 3: OUTPUT (AI Decision & Execution)

## 📌 ภาพรวมสถาปัตยกรรมส่วนที่ 3 (Overview)
ส่วนงานที่ 3 (**OUTPUT / AI Decision & Execution System**) คือ **"ระบบสมองกลตัดสินใจขั้นสุดท้ายและการบริหารจัดการออเดอร์"** มีหน้าที่รับไฟล์ Prompt Payload มาตรฐาน 100 บรรทัด (.txt) จากส่วนงานที่ 2 (PROCESS) เพื่อส่งให้ AI วิเคราะห์ตัดสินใจเลือกทิศทาง (CALL / PUT), กำหนดเวลาหมดอายุ (Expiry 1-5 นาที), และส่งคำสั่งเข้าสู่ระบบยิงออเดอร์ตามกฎการบริหารความเสี่ยงและเงินทุน (Money Management)

---

## 🏗️ โครงสร้างขอบเขตงานส่วนที่ 3 (Planned Workflow)

```mermaid
flowchart TD
    A[data_base/orchestrator/*.txt] -->|Read 100-Line Prompt| B[AI Prompt Manager]
    B -->|Send to AI Model| C[DeepSeek / Gemini AI]
    C -->|Return Decision JSON| D[AI Response Parser & Validator]
    
    subgraph Decision_Verification [ตรวจสอบความปลอดภัย]
    D --> E{Check Signal & Filters}
    E -->|Approved| F[Money Management & Position Sizing]
    E -->|Rejected / WAIT| G[Log & Standby]
    end
    
    subgraph Trade_Execution [การยิงออเดอร์]
    F --> H[Broker Execution Engine]
    H -->|Send Order| I[Broker API: IQ Option]
    I --> J[Order State Tracker & Result Logger]
    end
```

---

## 📋 หน้าที่หลักของโมดูลในส่วนที่ 3 (Planned Modules)

1. **AI Prompt Dispatcher & Interface:**
   - อ่านไฟล์ Prompt `.txt` ล่าสุดของแต่ละคู่เงินจาก `data_base/orchestrator/<SYMBOL>/`
   - แนบ **System Prompt (คู่มือกำกับตัวแปร 100 ฟิลด์ & กฎการเทรด)** ประกบคู่กับไฟล์ Prompt สด
   - จัดส่งให้โมเดล AI (DeepSeek / Gemini API) ประมวลผลแบบ Real-time ภายในกรอบเวลา < 2 วินาที

2. **Decision Parser & Signal Validator:**
   - ถอดรหัสผลการตัดสินใจของ AI ในรูปแบบมาตรฐาน JSON:
     ```json
     {
       "symbol": "EURUSD",
       "action": "CALL",
       "expiry_minutes": 5,
       "confidence_score": 85,
       "reason_th": "เกิด Reversal Breakout บนแนวรับ M5 ร่วมกับ RSI M1 เริ่มฟื้นตัว"
     }
     ```
   - ตรวจสอบความถูกต้องและขจัดสัญญาณขัดแย้งตามเงื่อนไขความปลอดภัย (Safety Circuit Breaker)

3. **Money Management & Position Sizing:**
   - คำนวณขนาดเงินลงทุนต่อไม้ (Fixed Amount / Compound / Martingale / Fractional Sizing)
   - ควบคุมขีดจำกัดความเสี่ยงรายวัน (Daily Drawdown / Profit Target / Max Loss Streak)

4. **Trade Execution & Order Management:**
   - ส่งคำสั่งเทรดไปยังโบรกเกอร์ (IQ Option) แบบเสี้ยววินาทีผ่าน Broker Bridge
   - ติดตามผลลัพธ์การเทรดเมื่อหมดเวลาสัญญา (Win / Loss / PnL / Payout) และบันทึกลงในระบบ Memory Manager และ Performance Report

---

## ⏳ สถานะและความพร้อม (Readiness Status)
- **สถานะ:** ⏳ เตรียมพร้อมเริ่มพัฒนาในขั้นตอนถัดไป (Pending Development)
- **ความพร้อมของระบบรองรับ:** ข้อมูลจาก Part 1 (Data Feed) และ Part 2 (Data Evaluate) เสร็จสมบูรณ์ 100% พร้อมเชื่อมต่อทันที ไร้ข้อติดค้างใดๆ ค่ะ 🚀
