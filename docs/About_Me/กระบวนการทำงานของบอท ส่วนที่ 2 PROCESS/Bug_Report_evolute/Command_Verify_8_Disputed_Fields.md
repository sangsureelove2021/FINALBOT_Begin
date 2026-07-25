# คำสั่ง: ตรวจสอบ 8 Disputed Fields — FINALBOT Independent Verification

> **วันที่จัดทำ:** 2026-07-23  
> **จัดทำโดย:** Athena (Audit Coordinator)  
> **วัตถุประสงค์:** AI ที่รับคำสั่งนี้ต้องตรวจสอบ **เฉพาะ 8 ฟิลด์** ที่ 3 AI ก่อนหน้าให้ผลลัพธ์ขัดแย้งกัน โดยต้องอ่านซอร์สโค้ดจริงทีละบรรทัดเท่านั้น

---

## กฎเหล็กก่อนเริ่ม (บังคับ)

1. **อ่านโค้ดจริงทีละบรรทัด** — ห้ามสรุปจาก logic ทั่วไปโดยไม่อ่านโค้ด
2. **ต้องระบุ file + line number** ทุกครั้งที่สรุปผล
3. **ตอบ BUG เท่านั้น** หาก: มีค่า hardcode, มี None default, มี string ไม่ตรงกัน, มี indent ผิด
4. **ตอบ OK เท่านั้น** หาก: อ่านโค้ดจริงแล้วไม่พบปัญหา — ห้ามตอบ OK โดยไม่ได้อ่าน
5. **ห้ามแก้ไขโค้ดใดๆ** งานนี้คืองานอ่านและรายงานเท่านั้น

Project Path: `E:\BOT_FINALBOT\FINALBOT_Begin\data_evaluate`

---

## FIELD 5 & 6 & 8 & 9: m1_age / m1_quality / m5_age / m5_quality

### ข้อโต้แย้ง
- **Ai2 (Payload Verified):** พบ BUG — ค่าเป็น `0` และ `STALE` ทุกรอบ เพราะ orchestrator ไม่ส่ง `forming_data` จริง
- **Ai3 & Ai4:** รายงาน PASS — `indicator_store.py:L215-L219` รับ `forming_data` มาใช้ถูกต้อง

### คำถามที่ต้องตอบ (ต้องอ่านโค้ดจริง)

**ขั้นตอน 1:** เปิดไฟล์ `orchestrator.py` แล้วค้นหาบรรทัดที่เรียก `store.calculate_all(...)` หรือ `calculate_all(...)` หรือชื่อฟังก์ชันที่คล้ายกัน

**คำถาม:**
- A. `orchestrator.py` เรียก `calculate_all()` ด้วย argument กี่ตัว?
- B. มีการส่ง `forming_data` (หรือชื่อตัวแปรที่คล้ายกัน) เป็น argument หรือไม่?
- C. ถ้าส่ง — ค่านั้นมาจากไหน? มีการคำนวณจริงหรือเป็น `None`?

**ขั้นตอน 2:** เปิดไฟล์ `indicator_store.py` แล้วดูที่ฟังก์ชัน `calculate_all()`

**คำถาม:**
- D. parameter `forming_data` มี default value เป็นอะไร? (`= None`? หรืออื่น?)
- E. มี `if forming_data is None:` block อยู่ไหม? ถ้ามี ค่า default ที่ใส่ใน m1_age, m1_quality, m5_age, m5_quality คืออะไร?

**คำตอบที่คาดหวัง:**
- ถ้า orchestrator ส่ง `forming_data=None` หรือไม่ส่งเลย และ store มี default = STALE/0 → **BUG CONFIRMED**
- ถ้า orchestrator ส่ง `forming_data` ที่คำนวณจริง → **OK**

### Template รายงานผล (กรอกหลังอ่านโค้ด)

```
Field 5 (m1_age):
- orchestrator.py call site: [file:line]
- forming_data ที่ส่งไป: [ค่า/None/ไม่ส่ง]
- indicator_store.py default block: [มี/ไม่มี]
- ผลลัพธ์: OK / BUG
- เหตุผล: [อธิบาย]

Field 6 (m1_quality): [เหมือนกัน]
Field 8 (m5_age): [เหมือนกัน]
Field 9 (m5_quality): [เหมือนกัน]
```

---

## FIELD 43 & 44: support / resistance (M5)

### ข้อโต้แย้ง
- **Ai2 (Payload Verified):** พบ BUG — `advanced_tools_manager.py` มี fallback ดึง `m5_basic['support']` และ `m5_basic['resistance']` ที่ไม่มีคีย์นี้ใน `indicator_store.py` → KeyError crash risk
- **Ai3 & Ai4:** รายงาน PASS — `indicator_store.py:L119-L120` คำนวณ support/resistance ไว้แล้ว

### คำถามที่ต้องตอบ (ต้องอ่านโค้ดจริง)

**ขั้นตอน 1:** เปิดไฟล์ `advanced_tools_manager.py` แล้วค้นหา `support` และ `resistance`

**คำถาม:**
- A. มี `else:` หรือ fallback block ที่ดึง `m5_basic['support']` หรือ `m5_basic['resistance']` ไหม?
- B. ถ้ามี — อยู่ที่บรรทัดไหน?

**ขั้นตอน 2:** เปิดไฟล์ `indicator_store.py` แล้วค้นหาว่า `m5` dict มีคีย์ `'support'` และ `'resistance'` จริงหรือไม่

**คำถาม:**
- C. `indicator_store.py` ใส่คีย์ `'support'` ใน m5 dict ตรงๆ หรือไม่? (ไม่ใช่ 's1')
- D. `indicator_store.py` ใส่คีย์ `'resistance'` ใน m5 dict ตรงๆ หรือไม่? (ไม่ใช่ 'r1')

**คำตอบที่คาดหวัง:**
- ถ้า advanced_tools_manager มี fallback ดึง `m5_basic['support']` แต่ indicator_store ไม่มีคีย์นี้ → **BUG CONFIRMED (KeyError)**
- ถ้า indicator_store มีคีย์ `'support'` จริง → **OK**

### Template รายงานผล (กรอกหลังอ่านโค้ด)

```
Field 43 (support M5):
- advanced_tools_manager.py fallback: [มี/ไม่มี] ที่ [file:line]
- indicator_store.py key 'support': [มี/ไม่มี]
- ผลลัพธ์: OK / BUG
- เหตุผล: [อธิบาย]

Field 44 (resistance M5): [เหมือนกัน]
```

---

## FIELD 58: trap_alert

### ข้อโต้แย้ง
- **Ai2 (Payload Verified):** พบ BUG — `trap_detector.py` คืนค่า `'BULL_TRAP'` (ตัวใหญ่) แต่ `advanced_tools_manager.py` เช็คด้วย `'bull'` (ตัวเล็ก) → ไม่มีทางตรงกัน → `trap_alert` เป็น `'TRUE'` ทุกครั้ง
- **Ai3 & Ai4:** รายงาน PASS หรือไม่ได้ตรวจละเอียด

### หลักฐานจาก Payload จริง (Log: EURGBPOTC0721011305)
```
trap_alert: 'TRUE'    ← ควรเป็นชนิด trap เช่น BULL_TRAP ไม่ใช่แค่ TRUE
```

### คำถามที่ต้องตอบ (ต้องอ่านโค้ดจริง)

**ขั้นตอน 1:** เปิดไฟล์ `trap_detector.py` แล้วค้นหาค่าที่ return

**คำถาม:**
- A. `trap_detector.py` return ค่า `trap_type` เป็นอะไรบ้าง? (ระบุทุกค่าที่เป็นไปได้)
- B. ตัวใหญ่หรือตัวเล็ก?

**ขั้นตอน 2:** เปิดไฟล์ `advanced_tools_manager.py` แล้วค้นหา `trap_alert`

**คำถาม:**
- C. มีการเช็ค `trap_type` ด้วยค่าอะไรบ้าง? ตัวใหญ่หรือตัวเล็ก?
- D. ถ้า trap_type ไม่ match → `trap_alert` ถูก set เป็นอะไร?

**คำตอบที่คาดหวัง:**
- ถ้า trap_detector คืน `'BULL_TRAP'` แต่ manager เช็ค `'bull'` → ไม่ match → trap_alert = 'TRUE' → **BUG CONFIRMED**
- ถ้า string ตรงกัน → **OK**

### Template รายงานผล (กรอกหลังอ่านโค้ด)

```
Field 58 (trap_alert):
- trap_detector.py return values: [ระบุทุกค่า]
- advanced_tools_manager.py check values: [ระบุทุกค่า]
- Match หรือไม่: [YES/NO]
- trap_alert เมื่อ trap_detected=True แต่ไม่ match: [ค่าที่ได้]
- ผลลัพธ์: OK / BUG
- เหตุผล: [อธิบาย]
```

---

## FIELD 59: sr_interaction

### ข้อโต้แย้ง
- **Ai2 (Payload Verified):** พบ BUG — โค้ดคำนวณ `sr_interaction` ถูก indent ซ้อนอยู่ภายใน `elif resistance` branch → `TESTING_PIVOT` และ `TESTING_SUPPORT` เป็น Dead Code 100%
- **Ai3 & Ai4:** รายงาน PASS หรือไม่ได้ตรวจ indent จริง

### หลักฐานจาก Payload จริง (Log: EURGBPOTC0721011305)
```
close M1  = 0.863785
pivot M5  = 0.863915
ห่างกัน  = 0.000130
threshold = ATR × 0.5 = 0.000676 × 0.5 = 0.000338
เงื่อนไข: 0.000130 ≤ 0.000338 → ควรได้ TESTING_PIVOT
ผลจริง:  sr_interaction = NONE  ← ผิด
```

### คำถามที่ต้องตอบ (ต้องอ่านโค้ดจริง)

**ขั้นตอน 1:** เปิดไฟล์ `advanced_tools_manager.py` แล้วค้นหา `sr_interaction`

**คำถาม:**
- A. โค้ดที่ set `sr_interaction = "TESTING_PIVOT"` อยู่ที่บรรทัดไหน?
- B. โค้ดนั้นอยู่ภายใน if/elif block อะไร? (ดู indentation จริง)
- C. โค้ดที่ set `rejection_zone = "AT_PIVOT"` อยู่ที่บรรทัดไหน?
- D. โค้ดที่ set `rejection_zone = "AT_RESISTANCE"` อยู่ที่บรรทัดไหน?

**คำถามชี้ขาด:**
- E. `sr_interaction = "TESTING_PIVOT"` อยู่ภายใน `elif abs(close_price - resistance) <= threshold:` หรือเปล่า?
- F. ถ้า close อยู่ใกล้ pivot (AT_PIVOT) → sr_interaction จะถูก set ได้ไหม?

**คำตอบที่คาดหวัง:**
- ถ้า TESTING_PIVOT อยู่ใน elif resistance block → ราคาอยู่ใกล้ pivot ไม่มีทางได้ TESTING_PIVOT → **BUG CONFIRMED**
- ถ้า sr_interaction อยู่นอก if/elif block (อิสระ) → **OK**

### Template รายงานผล (กรอกหลังอ่านโค้ด)

```
Field 59 (sr_interaction):
- บรรทัดที่ set sr_interaction = TESTING_PIVOT: [file:line]
- บล็อกที่ครอบอยู่: [ชื่อ if/elif branch]
- TESTING_PIVOT เป็น Dead Code: [YES/NO]
- Payload verification: close=0.863785, pivot=0.863915, ห่าง=0.00013 < threshold=0.000338
  ผลที่ได้จริง: [TESTING_PIVOT / NONE / อื่น]
- ผลลัพธ์: OK / BUG
- เหตุผล: [อธิบาย]
```

---

## Template รายงานสรุปรวม (ส่งกลับเมื่อตรวจครบ)

```markdown
## Verification Result — 8 Disputed Fields
**AI:** [ชื่อ AI]
**วันที่:** [วันที่]

| # | Field | สถานะ | หลักฐาน (file:line) | สรุป |
|:---:|:---|:---:|:---|:---|
| 5 | m1_age | OK/BUG | | |
| 6 | m1_quality | OK/BUG | | |
| 8 | m5_age | OK/BUG | | |
| 9 | m5_quality | OK/BUG | | |
| 43 | support M5 | OK/BUG | | |
| 44 | resistance M5 | OK/BUG | | |
| 58 | trap_alert | OK/BUG | | |
| 59 | sr_interaction | OK/BUG | | |

**สรุป:** BUG X/8 | OK Y/8
**คำแนะนำ:** [ลำดับการแก้ไข]
```

---

*จัดทำโดย Athena — FINALBOT Audit Coordinator*  
*2026-07-23 | อ้างอิง: Ai2 (Payload Verified) vs Ai3/Ai4*
