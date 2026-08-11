# TASK 1B — คืนค่า _determine_direction() กลับเป็นเดิม (Revert Unauthorized Change)

## สถานะ: อนุมัติจาก Boss แล้ว — ลงมือแก้ได้ทันที

## ไฟล์ที่ต้องแก้ (ไฟล์เดียวเท่านั้น)
`data_evaluate/orchestration/market_classifier/trend_engine.py`

## ไฟล์ที่ห้ามแตะ
ทุกไฟล์อื่นทั้งหมด รวมถึง `data_feed/` (ห้ามแตะเด็ดขาดตาม AGENTS.md ข้อ 18)

## บริบทของปัญหา
ใน TASK 1 (trend_strength_score) มีการอนุมัติให้แก้เฉพาะฟังก์ชัน `_slope_to_strength()` เท่านั้น (ซึ่งแก้ถูกต้องแล้ว ยืนยันแล้ว — ส่วนนี้ไม่ต้องแตะ) แต่พบว่ามีการแก้ฟังก์ชัน `_determine_direction()` เพิ่มเติมโดยไม่ได้รับอนุมัติ ซึ่งเปลี่ยนตรรกะหลักของการหาทิศทางเทรนด์ทั้งระบบ (จาก "ต้องเรียง EMA ครบ 4 เงื่อนไข" เป็น "โหวตเสียงข้างมาก 3 ใน 4") — Boss สั่งให้คืนค่ากลับเป็นเดิม

## การแก้ไขที่ต้องทำ — คืนค่ากลับเป็นเดิม

หาฟังก์ชันนี้ใน `trend_engine.py` (เวอร์ชันปัจจุบันที่ถูกแก้โดยไม่ได้รับอนุมัติ):

```python
def _determine_direction(self, price, ema20, ema50, ema100, ema200) -> str:
    # Check majority alignment
    up_count = sum([
        price > ema20,
        ema20 > ema50,
        ema50 > ema100,
        ema100 > ema200
    ])
    
    down_count = sum([
        price < ema20,
        ema20 < ema50,
        ema50 < ema100,
        ema100 < ema200
    ])
    
    if up_count >= 3:
        return 'UP'
    elif down_count >= 3:
        return 'DOWN'
    elif up_count == 2 and down_count == 2:
        # Mixed signals - check price vs ema20 as tiebreaker
        return 'UP' if price > ema20 else 'DOWN'
    return 'NONE'
```

**คืนค่ากลับเป็นโค้ดเดิมนี้ (เวอร์ชันก่อนถูกแก้โดยไม่ได้รับอนุมัติ):**

```python
def _determine_direction(self, price, ema20, ema50, ema100, ema200) -> str:
    if price > ema20 > ema50 > ema100:
        return 'UP'
    elif price < ema20 < ema50 < ema100:
        return 'DOWN'
    return 'NONE'
```

## ห้ามแตะฟังก์ชันนี้ (แก้ถูกต้องแล้วจาก TASK 1 — เก็บไว้ตามเดิมทุกตัวอักษร)

```python
def _slope_to_strength(self, direction, slope, thresholds) -> int:
    if direction == 'NONE':
        return 20
        
    abs_slope = abs(slope)
    if abs_slope > thresholds['strength_100']:
        return 100
    elif abs_slope > thresholds['strength_80']:
        return 80
    elif abs_slope > thresholds['strength_60']:
        return 60
    elif abs_slope > thresholds['strength_40']:
        return 40
    return 20
```

และจุดเรียกใช้ใน `_analyze()` ที่ส่ง `direction` เข้าไปแล้ว — เก็บไว้ตามเดิมเช่นกัน:
```python
'strength': self._slope_to_strength(direction, slope, thresholds),
```

## ขั้นตอนดำเนินการ (บังคับตาม AGENTS.md)
1. แก้เฉพาะ `_determine_direction()` ให้กลับเป็นโค้ดเดิมที่ระบุไว้ข้างต้นเท่านั้น
2. ห้ามแตะ `_slope_to_strength()` หรือฟังก์ชันอื่นใดในไฟล์นี้หรือไฟล์อื่น
3. ห้ามเพิ่ม logic ใหม่ ห้าม "ปรับปรุง" อะไรเพิ่มเติมนอกเหนือคำสั่งนี้โดยเด็ดขาด — งานนี้คือการคืนค่ากลับเป็นเดิม (revert) เท่านั้น ไม่ใช่การพัฒนาต่อ
4. ทดสอบต้องรันผ่าน `runner.py` เท่านั้น (ห้ามเขียน script ทดสอบแยก)
5. รันบน CMD/Terminal แบบเปิดเผยเท่านั้น
6. หลังทดสอบเสร็จต้อง kill process ทันที ห้ามปล่อยบอทรันค้าง

## Success Criteria
- `_determine_direction()` ต้องตรงกับโค้ดเดิมที่ระบุไว้ข้างต้นทุกตัวอักษร (ใช้ `price > ema20 > ema50 > ema100` เท่านั้น ไม่มี majority vote)
- `_slope_to_strength()` และจุดเรียกใช้ยังคงเหมือนเดิม (ไม่เปลี่ยนแปลงจาก TASK 1)
- ไม่มีไฟล์อื่นถูกแก้ไข
- รัน `runner.py` แล้วไม่มี Exception จาก `trend_engine.py`
- เมื่อ `direction == 'NONE'` → `analysis.trend_strength_score` ในไฟล์ output `.txt` ต้องเป็น 20 เสมอ (ยืนยันผลจาก TASK 1 ยังคงอยู่)
