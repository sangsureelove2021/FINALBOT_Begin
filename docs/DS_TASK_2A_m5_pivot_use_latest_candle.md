# TASK 2A — แก้ M5 Pivot ให้ใช้ iloc[-1] แทน iloc[-2]

## สถานะ: อนุมัติจาก Boss แล้ว — ลงมือแก้ได้ทันที

## ไฟล์ที่ต้องแก้ (ไฟล์เดียวเท่านั้น)
`data_evaluate/orchestration/indicator_store/indicator_store.py`

## ไฟล์ที่ห้ามแตะ
ทุกไฟล์อื่นทั้งหมด รวมถึง `data_feed/` (ห้ามแตะเด็ดขาดตาม AGENTS.md ข้อ 18)

## บริบทของปัญหา (ยืนยันแล้วจากซอร์สโค้ดจริง)
`data_feed/data_adapter.py` เรียก `drop_forming()` กับข้อมูลทุก timeframe (M1, M5, M15) **ก่อน**เขียนลง CSV เสมอ (ทั้งใน `init_symbol()` และ `update()`) แปลว่าไฟล์ CSV **ไม่มีแท่งที่ยังไม่ปิดหลงเหลืออยู่เลย** — แถวสุดท้าย (`iloc[-1]`) ของทุก timeframe คือแท่งที่ปิดสมบูรณ์แล้วเสมอ (ยืนยันโดย Boss และตรวจสอบโค้ดตรงกัน)

แต่ `indicator_store.py` ส่วนคำนวณ pivot ของ M5 ยังคงถอยไปใช้ `iloc[-2]` โดยมีคอมเมนต์เข้าใจผิดว่าต้อง "หนี" แท่งที่กำลังวิ่ง ทั้งที่ไม่มีแท่งแบบนั้นอยู่ในข้อมูลแล้ว ทำให้ M5 pivot คำนวณจากข้อมูลเก่ากว่าที่ควร 1 แท่ง (5 นาที) โดยไม่จำเป็น — เป็นจุดเดียวในทั้งระบบที่มีปัญหานี้ (ตรวจสอบทั้ง `data_evaluate/` แล้วไม่พบจุดอื่น)

## การแก้ไขที่ต้องทำ

หาโค้ดนี้ใน `indicator_store.py` (ส่วน M5 Indicators, ก่อนคำนวณ pivot):

```python
        # ================================================================
        # FLOOR PIVOT POINTS (UNIFIED METHODOLOGY)
        # All pivot and S/R levels come from the same Floor Pivot calculation
        # This ensures consistency between pivot and support/resistance
        # ================================================================
        # Use completed candle only (per SPEC) - avoid using forming candle
        if len(df_m5) < 1:
            raise ValueError("FAIL-FAST: Insufficient M5 candles for Pivot Point calculation (minimum 1 required)")
        
        # Use the last completed candle (iloc[-1] is forming, iloc[-2] is completed)
        # If only 1 candle exists, use it as completed
        if len(df_m5) == 1:
            completed_high = high_m5.iloc[-1]
            completed_low = low_m5.iloc[-1]
            completed_close = close_m5.iloc[-1]
        else:
            completed_high = high_m5.iloc[-2]
            completed_low = low_m5.iloc[-2]
            completed_close = close_m5.iloc[-2]
```

แก้เป็น (ใช้ `iloc[-1]` เสมอ เพราะ CSV ไม่มีแท่งที่ยังไม่ปิดอยู่แล้ว):

```python
        # ================================================================
        # FLOOR PIVOT POINTS (UNIFIED METHODOLOGY)
        # All pivot and S/R levels come from the same Floor Pivot calculation
        # This ensures consistency between pivot and support/resistance
        # ================================================================
        # NOTE: data_feed already drops the still-forming candle via drop_forming()
        # before writing to CSV/RAM (see data_adapter.py init_symbol/update).
        # Therefore iloc[-1] is ALWAYS the latest completed candle — no need to step back.
        if len(df_m5) < 1:
            raise ValueError("FAIL-FAST: Insufficient M5 candles for Pivot Point calculation (minimum 1 required)")
        
        completed_high = high_m5.iloc[-1]
        completed_low = low_m5.iloc[-1]
        completed_close = close_m5.iloc[-1]
```

## ห้ามแตะส่วนอื่นในไฟล์นี้
- การคำนวณ `pivot`, `r1`, `r2`, `s1`, `s2`, `support`, `resistance` ที่อยู่**ถัดจาก**ส่วนนี้ — สูตรเหมือนเดิมทุกตัวอักษร (ใช้ `pivot`, `completed_high`, `completed_low` ตัวแปรเดิม ไม่ต้องเปลี่ยน)
- M1 pivot และ M15 pivot — ใช้ `iloc[-1]` อยู่แล้วถูกต้อง ไม่ต้องแตะ
- ฟังก์ชันอื่นทั้งหมดในไฟล์

## ขั้นตอนดำเนินการ (บังคับตาม AGENTS.md)
1. แก้เฉพาะจุดที่ระบุข้างต้นเท่านั้น (เปลี่ยนจาก `iloc[-2]`/เงื่อนไข if-else เป็น `iloc[-1]` ตรงๆ)
2. ห้ามแตะ `data_feed/` โดยเด็ดขาด
3. ห้ามแตะไฟล์อื่นใดนอกจาก `indicator_store.py`
4. ทดสอบต้องรันผ่าน `runner.py` เท่านั้น
5. รันบน CMD/Terminal แบบเปิดเผยเท่านั้น
6. หลังทดสอบเสร็จต้อง kill process ทันที ห้ามปล่อยบอทรันค้าง

## Success Criteria
- M5 pivot คำนวณจาก `iloc[-1]` (แท่งล่าสุดที่ปิดสมบูรณ์) ไม่ใช่ `iloc[-2]` อีกต่อไป
- `m5_pivot` ในไฟล์ output `.txt` ควรมีค่าสดขึ้น (อัปเดตทุกแท่งใหม่ ไม่ล่าช้า 1 แท่งเหมือนก่อนแก้)
- M1 pivot, M15 pivot ไม่เปลี่ยนแปลง
- support (s1), resistance (r1) ยังคงคำนวณถูกต้องจาก pivot ตัวใหม่
- ไม่มีไฟล์อื่นถูกแก้ไข
- รัน `runner.py` แล้วไม่มี Exception จาก `indicator_store.py`
