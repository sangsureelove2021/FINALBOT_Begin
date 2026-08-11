# TASK 3 — แก้เกณฑ์ M15 Warm-up ให้ตรงกับที่ Bollinger Band ต้องการจริง (100 แท่ง)

## สถานะ: อนุมัติจาก Boss แล้ว — ลงมือแก้ได้ทันที

## ไฟล์ที่ต้องแก้ (ไฟล์เดียวเท่านั้น)
`data_evaluate/orchestration/indicator_store/indicator_store.py`

## ไฟล์ที่ห้ามแตะ
ทุกไฟล์อื่นทั้งหมด รวมถึง `data_feed/` (ห้ามแตะเด็ดขาดตาม AGENTS.md ข้อ 18) และ `core_indicators.py` (ห้ามแตะ — ดูเหตุผลด้านล่าง)

## ปัญหา (ยืนยันจาก error.log จริง — เกิดขึ้นทุกนาที ทุกคู่เงิน)
```
ValueError: Not enough data to calculate bbw_sma_100
  File "indicator_store.py", line 270, in calculate_raw_indicators
    m15.update(CoreIndicators.calculate_bb(close_m15, 20, Config.ROUND_DECIMALS, require_100=True))
  File "core_indicators.py", line 29, in calculate_bb
    raise ValueError("Not enough data to calculate bbw_sma_100")
```

**สาเหตุ:** เกณฑ์ตรวจ warm-up ของ M15 ที่ต้นฟังก์ชัน `calculate_raw_indicators()` กำหนดไว้แค่ 50 แท่ง แต่การคำนวณ Bollinger Band ของ M15 (บรรทัด 270) เรียกด้วย `require_100=True` ซึ่งต้องการข้อมูลอย่างน้อย **100 แท่ง** จริงๆ ทำให้ระบบผ่านด่านตรวจ warm-up ไปได้ทั้งที่ข้อมูลไม่พอ แล้วไปพังตอนคำนวณจริง — เป็นแบบนี้ทุกรอบ ทุกคู่เงิน จนกว่า M15 จะสะสมครบ 100 แท่ง (ต้องใช้เวลาประมาณ 25 ชั่วโมงนับจากเริ่มเก็บข้อมูลใหม่)

**ผลกระทบ:** `data_base/orchestrator/` ว่างเปล่า ไม่มีไฟล์ output เลยแม้แต่คู่เดียว ตราบใดที่ M15 ยังไม่ครบ 100 แท่ง

## การแก้ไขที่ต้องทำ — แก้เกณฑ์ตรวจ warm-up ให้ตรงกับความจริง

หาโค้ดนี้ใน `indicator_store.py` (ส่วน Warm-up Check ต้นฟังก์ชัน `calculate_raw_indicators`):

```python
        # ------------------------------------------------------------
        # 0. Warm-up Candle Lookback Check (Fail-Fast: 100/250/50)
        # ------------------------------------------------------------
        if df_m1 is None or df_m1.empty or len(df_m1) < 100:
            raise ValueError("FAIL-FAST: Insufficient M1 warm-up candles (minimum 100 required)")
        if df_m5 is None or df_m5.empty or len(df_m5) < 250:
            raise ValueError("FAIL-FAST: Insufficient M5 warm-up candles (minimum 250 required)")
        if df_m15 is None or df_m15.empty or len(df_m15) < 50:
            raise ValueError("FAIL-FAST: Insufficient M15 warm-up candles (minimum 50 required)")
```

แก้เป็น (เปลี่ยนเกณฑ์ M15 จาก 50 เป็น 100 ให้ตรงกับที่ `calculate_bb(..., require_100=True)` ต้องการจริง):

```python
        # ------------------------------------------------------------
        # 0. Warm-up Candle Lookback Check (Fail-Fast: 100/250/100)
        # NOTE: M15 requires 100 candles (not 50) because calculate_bb()
        # below is called with require_100=True for bbw_sma_100.
        # ------------------------------------------------------------
        if df_m1 is None or df_m1.empty or len(df_m1) < 100:
            raise ValueError("FAIL-FAST: Insufficient M1 warm-up candles (minimum 100 required)")
        if df_m5 is None or df_m5.empty or len(df_m5) < 250:
            raise ValueError("FAIL-FAST: Insufficient M5 warm-up candles (minimum 250 required)")
        if df_m15 is None or df_m15.empty or len(df_m15) < 100:
            raise ValueError("FAIL-FAST: Insufficient M15 warm-up candles (minimum 100 required)")
```

## ห้ามแตะส่วนอื่น
- `core_indicators.py` — ห้ามแก้ `calculate_bb()` หรือลด `require_100` เป็น `False` เด็ดขาด เพราะจะเปลี่ยนความแม่นยำของ `bbw_sma_100` (ใช้ในคำนวณ `compression_quality_%`) — งานนี้คือแก้ให้ **เกณฑ์ตรวจสอบตรงกับความจริง** ไม่ใช่ลดมาตรฐานการคำนวณ
- ส่วนอื่นทั้งหมดในไฟล์ `indicator_store.py`

## ขั้นตอนดำเนินการ (บังคับตาม AGENTS.md)
1. แก้เฉพาะจุดที่ระบุ (ตัวเลข 50 → 100 และข้อความ error message ให้ตรงกัน)
2. ห้ามแตะ `data_feed/` หรือ `core_indicators.py`
3. ทดสอบต้องรันผ่าน `runner.py` เท่านั้น
4. รันบน CMD/Terminal แบบเปิดเผยเท่านั้น
5. หลังทดสอบเสร็จต้อง kill process ทันที ห้ามปล่อยบอทรันค้าง

## Success Criteria
- เมื่อ M15 มีข้อมูลน้อยกว่า 100 แท่ง → error message ต้องบอกชัดเจนว่า "minimum 100 required" (ไม่ใช่ 50) และระบบไม่ไป error ที่ `bbw_sma_100` อีกต่อไป (fail เร็วขึ้น ด้วยข้อความที่ตรงความจริง)
- เมื่อ M15 สะสมครบ 100 แท่งแล้ว (ประมาณ 25 ชม. หลัง CSV เริ่มเก็บใหม่) → Part 2 ต้องรันผ่านได้ปกติ ไม่มี `ValueError: Not enough data to calculate bbw_sma_100` อีก และเริ่มมีไฟล์ `.txt` ปรากฏใน `data_base/orchestrator/<SYMBOL>/`
- ไม่มีไฟล์อื่นถูกแก้ไข
- รัน `runner.py` แล้ว log error.log ไม่มี error `bbw_sma_100` เกิดขึ้นอีกหลัง M15 ครบ 100 แท่ง

## หมายเหตุถึง Boss
แก้จุดนี้แล้ว **บอทจะยังไม่มี output ทันที** เพราะ M15 ต้องสะสมให้ครบ 100 แท่งก่อน (ของ EURUSD-OTC ตอนนี้มี 69 แท่ง ต้องรออีกประมาณ 31 แท่ง x 15 นาที ≈ 7-8 ชั่วโมง) — เป็นเรื่องปกติของข้อมูลที่ยังสะสมไม่ครบ ไม่ใช่บั๊กใหม่ที่เกิดจากการแก้ครั้งนี้
