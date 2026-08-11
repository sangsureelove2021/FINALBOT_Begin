# TASK 3B — ปรับเกณฑ์ Warm-up ทั้ง 3 Timeframe (M1/M5/M15) เป็น 150 แท่ง (แทนที่ TASK 3)

## สถานะ: อนุมัติจาก Boss แล้ว — ลงมือแก้ได้ทันที (เอกสารนี้แทนที่ DS_TASK_3 ทั้งหมด — ถ้ายังไม่ได้ทำ TASK 3 ให้ข้ามไปทำอันนี้แทนเลย)

## ไฟล์ที่ต้องแก้ (ไฟล์เดียวเท่านั้น)
`data_evaluate/orchestration/indicator_store/indicator_store.py`

## ไฟล์ที่ห้ามแตะ
ทุกไฟล์อื่นทั้งหมด รวมถึง `data_feed/` (ห้ามแตะเด็ดขาดตาม AGENTS.md ข้อ 18) และ `core_indicators.py` (ห้ามแตะ)

## บริบท (ตรวจสอบทั้งระบบแล้วตามคำสั่ง Boss)
ตรวจ `core_indicators.py`, `structural_metrics.py`, `base_engine.py` และทุก engine ใน `data_evaluate/` พบว่า:
- **M1, M5, M15 ทั้ง 3 timeframe เรียก `calculate_bb(..., require_100=True)` เหมือนกัน** ต้องการอย่างน้อย 100 แท่งจริง
- เกณฑ์ตรวจปัจจุบัน: M1=100 (พอดีเป๊ะ ไม่มี buffer), M5=250 (ปลอดภัยเกินจำเป็น), M15=100 (พอดีเป๊ะ ไม่มี buffer)
- ไม่มี engine อื่นในระบบที่ต้องการมากกว่า 100 แท่งเลย — 150 แท่งเพียงพอครอบคลุมทั้งระบบ พร้อม buffer 50 แท่ง

## การแก้ไขที่ต้องทำ

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

**(หากทำ TASK 3 ไปแล้ว โค้ดปัจจุบันจะเป็น M15 < 100 แทน — ให้แก้จากสภาพปัจจุบันเป็นเวอร์ชันด้านล่างนี้เหมือนกัน)**

แก้เป็น (ทั้ง 3 timeframe ใช้เกณฑ์เดียวกัน 150 แท่ง):

```python
        # ------------------------------------------------------------
        # 0. Warm-up Candle Lookback Check (Fail-Fast: 150/150/150)
        # NOTE: All 3 timeframes call calculate_bb(require_100=True) which
        # needs a minimum of 100 candles. 150 gives a 50-candle safety
        # margin uniformly across M1/M5/M15 — verified no other engine
        # in data_evaluate requires more than 100 candles.
        # ------------------------------------------------------------
        if df_m1 is None or df_m1.empty or len(df_m1) < 150:
            raise ValueError("FAIL-FAST: Insufficient M1 warm-up candles (minimum 150 required)")
        if df_m5 is None or df_m5.empty or len(df_m5) < 150:
            raise ValueError("FAIL-FAST: Insufficient M5 warm-up candles (minimum 150 required)")
        if df_m15 is None or df_m15.empty or len(df_m15) < 150:
            raise ValueError("FAIL-FAST: Insufficient M15 warm-up candles (minimum 150 required)")
```

## ห้ามแตะส่วนอื่น
- `core_indicators.py` — ห้ามแก้ `calculate_bb()` หรือเปลี่ยน `require_100` เด็ดขาด
- ส่วนอื่นทั้งหมดในไฟล์ `indicator_store.py`
- `runner.py` ที่มีการ `start_stream(sym, 'M1', 100)` / `'M5', 250` / `'M15', 70` — **ไม่ต้องแตะ** เพราะเป็นแค่จำนวนแท่งเริ่มต้นที่ขอตอน subscribe stream ไม่ใช่ตัวตัดสินว่าข้อมูลพอหรือไม่ (CSV จะสะสมต่อไปเรื่อยๆ เอง)

## ขั้นตอนดำเนินการ (บังคับตาม AGENTS.md)
1. แก้เฉพาะจุดที่ระบุ (ตัวเลข M1/M5/M15 ทั้ง 3 → 150 และข้อความ error message ให้ตรงกัน)
2. ห้ามแตะ `data_feed/` หรือ `core_indicators.py`
3. ทดสอบต้องรันผ่าน `runner.py` เท่านั้น
4. รันบน CMD/Terminal แบบเปิดเผยเท่านั้น
5. หลังทดสอบเสร็จต้อง kill process ทันที ห้ามปล่อยบอทรันค้าง

## Success Criteria
- ทั้ง 3 timeframe (M1, M5, M15) ต้องการอย่างน้อย 150 แท่งก่อนเริ่มคำนวณ
- Error message ตรงกับตัวเลขจริง (ไม่มี M5=250 หรือ M15=50/100 หลงเหลือ)
- ไม่มีไฟล์อื่นถูกแก้ไข
- รัน `runner.py` แล้ว error.log ไม่มี `ValueError: Not enough data to calculate bbw_sma_100` อีกเลยหลังข้อมูลสะสมครบ 150 แท่งทุก timeframe
- เมื่อครบ 150 แท่งแล้ว ไฟล์ `.txt` ต้องเริ่มปรากฏใน `data_base/orchestrator/<SYMBOL>/`

## หมายเหตุถึง Boss
M1 สะสมเร็ว (150 นาที ≈ 2.5 ชม.) M15 สะสมช้าสุด (150 x 15 นาที ≈ 37.5 ชม.) — **M15 จะเป็นตัวถ่วงที่ทำให้บอทเริ่ม output ช้าที่สุดในทั้ง 3 timeframe** เป็นผลจากค่า 150 ที่ Boss กำหนด ไม่ใช่บั๊ก
