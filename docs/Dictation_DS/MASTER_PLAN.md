# แผนแม่บทการปรับโครงสร้างบอท (Master Architecture Alignment Plan)

## 1. โครงสร้างบอทแบบ Tree (Target Architecture)
อ้างอิงจากเอกสารจำเพาะทั้ง 5 ฉบับ โครงสร้างโฟลเดอร์และไฟล์สำคัญที่ต้องมี/ปรับปรุง มีดังนี้:

`	ext
BOT_FINALBOT/
├── main.py                     # Entry point เริ่มระบบ
├── runner.py                   # Main Loop 
├── config/
│   └── settings.json           # เก็บ Trading Mode, Account Type, AI Mode
├── docs/
│   ├── SPEC_CLASSIFIER.md
│   ├── SPEC_COMPUTATION_FLOW.md
│   ├── SPEC_ENGINES.md
│   ├── SPEC_INDICATOR_STORE.md
│   ├── SPEC_TIMEFRAME_USAGE.md
│   ├── MASTER_PLAN.md          # แผนฉบับนี้
│   └── Report.md               # รายงานการประเมินแผน
├── core/
│   ├── indicator_store.py      # [สร้างใหม่] ศูนย์กลางคำนวณ TA ครั้งเดียว
│   ├── orchestrator.py         # [สร้างใหม่] ตัวคุมคิวส่งข้อมูลและ Feedback loop
│   ├── config_loader.py
│   ├── execution_gate.py       # [สร้างใหม่/กู้คืน] จุดรวม Signal ตัดสินใจก่อนยิงออเดอร์
│   ├── ai_analysis/
│   │   └── deepseek_agent_bridge.py # AI PATH
│   ├── strategy/
│   │   └── auto_bot_strategy.py     # [สร้างใหม่/ปรับปรุง] STRATEGY PATH (Rule-based)
│   ├── engines/
│   │   ├── base_engine.py
│   │   ├── trend_engine.py     # [ต้องแก้] เปลี่ยนไปดึงค่าจาก IndicatorStore
│   │   ├── strength_engine.py  # [ต้องแก้] เปลี่ยนไปดึงค่าจาก IndicatorStore
│   │   ├── volatility_engine.py# [ต้องแก้] เปลี่ยนไปดึงค่าจาก IndicatorStore
│   │   ├── structure_engine.py # [ต้องแก้] เปลี่ยนไปดึงค่าจาก IndicatorStore
│   │   ├── mtf_intelligence.py # [ต้องแก้] เปลี่ยนไปดึงค่าจาก IndicatorStore
│   │   ├── market_state_classifier.py # [ต้องแก้]
│   │   └── regime_quality_scorer.py   # [เพิ่ม] ชั่งน้ำหนักความน่าเทรด
│   └── logging/
│       └── trade_logger.py     # [ต้องแก้] ลบการคำนวณ TA ทั้งหมดออก เป็นแค่ตัวจด Log
└── execution/
    └── iq_option_executor.py   # ตัวยิงออเดอร์จริง/เดโม่
`

## 2. ปัญหาที่พบในปัจจุบัน (Current Flaws vs 5 SPECs)
1. **ละเมิด SPEC_COMPUTATION_FLOW.md:** ปัจจุบัน Engines คำนวณ TA เอง และยังขาดระบบสร้าง Market Payload JSON (Immutable) แบบตายตัวที่ส่งให้ทั้ง AI และ Strategy ใช้ร่วมกัน
2. **ละเมิด SPEC_INDICATOR_STORE.md:** ยังไม่มี IndicatorStore ทำให้ไม่มีศูนย์กลางในการเก็บค่า Indicator รวมถึงขาดระบบ Feedback Loop ที่เขียน Market State กลับเข้า Store
3. **ละเมิดขอบเขตหน้าที่ (Trade Logger Overstepping):** trade_logger ดันคำนวณ Indicator เอง
4. **ละเมิด SPEC_TIMEFRAME_USAGE.md:** ปัจจุบันดึงแต่ M5 ขาดการดึง M1, M15, M60, D1 แบบครบวงจร และไม่มีระบบ M15(Bias) -> M5(Signal) -> M1(Confirmation)
5. **ละเมิด SPEC_CLASSIFIER.md:** ขาดระบบ Regime Quality Scorer 
6. **ขาด Execution Gate & Strategy Path:** ปัจจุบันโฟกัสแค่ AI แต่ Spec สั่งให้มีทั้ง AI Path และ Strategy Path ทำงานคู่ขนานกันแล้วไปจบที่ execution_gate

## 3. แผนการปรับปรุงแก้ไข (Action Plan)

### เฟส 1: ติดตั้งศูนย์กลางข้อมูล (Indicator Store) & ดึงกราฟให้ครบ
- ให้ Runner ดึงข้อมูล M1, M5, M15, M60, D1 มาให้ครบถ้วน
- สร้าง core/indicator_store.py รับกราฟมาคำนวณ TA ทุกตัวครั้งเดียว แล้วเก็บใส่ dict

### เฟส 2: ล้างบางการคำนวณซ้ำซ้อน (Clean Up)
- ลบการคำนวณ TA จาก 	rade_logger.py 
- ลบสูตร TA ออกจาก Tier 1 Engines ให้เปลี่ยนไปอ่านค่าจาก IndicatorStore แทน 

### เฟส 3: Orchestration & Feedback Loop (หัวใจหลัก)
- สร้าง core/orchestrator.py:
  1. ดึงค่าจาก Store ป้อน Tier 1 Engines 
  2. รวบยอดส่ง Tier 2 (Classifier และ Regime Quality Scorer)
  3. **Feedback Loop:** นำ Market_State และ Price_Action ที่ได้ เขียนกลับทับลงใน IndicatorStore
  4. สร้าง Market Payload JSON 1 ชุดจาก Store

### เฟส 4: แยก Path & กฎการเข้าเทรด (Execution & Confirmation)
- สร้าง execution_gate.py
- นำ JSON Payload โยนไป 2 ทาง:
  - **AI PATH:** deepseek_agent_bridge.py
  - **STRATEGY PATH:** uto_bot_strategy.py
- บังคับใช้กฎ **TIMEFRAME CONFIRMATION**: (M15 Bias -> M5 Signal -> M1 Confirmation) ก่อนที่จะให้ execution_gate อนุมัติยิง (CALL/PUT/NO_SIGNAL)

### เฟส 5: ล้างข้อมูล (Cleanup)
- หมดรอบ (60s) สั่งเคลียร์ IndicatorStore เพื่อรอรอบถัดไป 

## 4. กฎเหล็กสถาปัตยกรรม (Architecture Core Logic - สรุปความเข้าใจจากบอส)
เพื่อให้ AI ตัวต่อไปเข้าใจการทำงานของบอทอย่างทะลุปรุโปร่ง ให้มองเป็น **"โรงงาน 3 แผนก"**:
1. **แผนกที่ 1: ฝ่ายหาวัตถุดิบ (IndicatorStore)**
   - ทำหน้าที่ "คำนวณตัวเลขทางคณิตศาสตร์" อย่างเดียว (EMA, RSI, MACD, BB, ATR, ADX, ROC, Stoch, S/R, Pivot)
   - ไม่มีการวิเคราะห์ใดๆ ทั้งสิ้น ใช้เฉพาะ 3 Timeframe คือ M1, M5, M15 (ไม่ใช้ M60, D1)
2. **แผนกที่ 2: ฝ่ายวิเคราะห์เฉพาะทาง (5 Tier 1 Engines)**
   - ดึงข้อมูลตัวเลขจากแผนกที่ 1 มาแปลเป็น "ภาษาคน"
   - เช่น ตัวเลข BB กว้าง 0.001 -> เครื่องยนต์แปลเป็นคำว่า "LOW (บีบตัวแน่น)"
3. **แผนกที่ 3: ฝ่ายแยกสภาวะตลาด (Market State Classifier)**
   - ไม่มองตัวเลขดิบ แต่รออ่านรายงานภาษาคนจากแผนกที่ 2
   - นำรายงานทั้ง 5 มาผูกเงื่อนไข (IF/ELSE) เพื่อเคาะออกมาเป็นสภาวะตลาด 1 สภาวะ (จาก 10 สภาวะ)

**ผู้บังคับการ (Orchestrator):** 
คือตัวละครใน Phase 3 ที่จะทำหน้าที่เป็นคนเดินเอกสาร สั่ง Store ให้คำนวณ ส่งข้อมูลให้ Engines ส่งต่อให้ Classifier และส่งผลลัพธ์กลับไปอัปเดตที่ Store (Feedback Loop)
