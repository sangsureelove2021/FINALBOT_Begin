# TASK 1C — นำ trend_strength_score fix กลับมาใหม่ (ที่หายไปตอน Revert)

## สถานะ: อนุมัติจาก Boss แล้ว — ลงมือแก้ได้ทันที

## ไฟล์ที่ต้องแก้ (ไฟล์เดียวเท่านั้น)
`data_evaluate/orchestration/market_classifier/trend_engine.py`

## ไฟล์ที่ห้ามแตะ
ทุกไฟล์อื่นทั้งหมด รวมถึง `data_feed/` (ห้ามแตะเด็ดขาดตาม AGENTS.md ข้อ 18)

## บริบทของปัญหา
TASK 1B สั่งให้คืนค่าเฉพาะฟังก์ชัน `_determine_direction()` กลับเป็นเดิม (สำเร็จแล้ว ยืนยันถูกต้อง — **ห้ามแตะฟังก์ชันนี้อีกในรอบนี้**) แต่การแก้ครั้งนั้นดันไปคืนค่าฟังก์ชัน `_slope_to_strength()` กลับเป็นเวอร์ชันเดิมที่มีบั๊กไปด้วยโดยไม่ได้รับอนุมัติ (ทั้งที่ TASK 1B สั่งชัดว่าห้ามแตะฟังก์ชันนี้) ทำให้บั๊กเดิมของ TASK 1 (`trend_strength_score = 100` ตอน `direction == 'NONE'`) กลับมาอีกครั้ง

งานนี้คือการนำ fix ของ TASK 1 กลับมาใหม่เท่านั้น — **ห้ามแตะ `_determine_direction()` อีกเด็ดขาด เพราะเพิ่งคืนค่าถูกต้องแล้วใน TASK 1B**

## การแก้ไขที่ต้องทำ

หาฟังก์ชันนี้ใน `trend_engine.py` (เวอร์ชันปัจจุบันที่มีบั๊กกลับมา):

```python
def _slope_to_strength(self, slope, thresholds) -> int:
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

แก้เป็น (เพิ่มพารามิเตอร์ `direction` และเช็คก่อนคำนวณ):

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

จากนั้นหาจุดเรียกใช้งานในฟังก์ชัน `_analyze()` (ในไฟล์เดียวกัน):

```python
return {
    'direction': direction,
    'strength': self._slope_to_strength(slope, thresholds),
    ...
}
```

แก้เป็น (ส่ง `direction` เข้าไปด้วย เป็น argument แรก):

```python
return {
    'direction': direction,
    'strength': self._slope_to_strength(direction, slope, thresholds),
    ...
}
```

## ห้ามแตะฟังก์ชันนี้ (ถูกต้องแล้วจาก TASK 1B — เก็บไว้ตามเดิมทุกตัวอักษร ห้ามแก้อีก)

```python
def _determine_direction(self, price, ema20, ema50, ema100, ema200) -> str:
    if price > ema20 > ema50 > ema100:
        return 'UP'
    elif price < ema20 < ema50 < ema100:
        return 'DOWN'
    return 'NONE'
```

## ขั้นตอนดำเนินการ (บังคับตาม AGENTS.md)
1. แก้เฉพาะ 2 จุดที่ระบุใน `_slope_to_strength()` และจุดเรียกใช้เท่านั้น
2. **ห้ามแตะ `_determine_direction()` โดยเด็ดขาด** — เพิ่งถูกต้องแล้วจาก TASK 1B
3. ห้ามแตะฟังก์ชันอื่นใดในไฟล์นี้หรือไฟล์อื่น ห้าม "ปรับปรุง" อะไรเพิ่มเติมนอกเหนือคำสั่งนี้
4. ทดสอบต้องรันผ่าน `runner.py` เท่านั้น (ห้ามเขียน script ทดสอบแยก)
5. รันบน CMD/Terminal แบบเปิดเผยเท่านั้น
6. หลังทดสอบเสร็จต้อง kill process ทันที ห้ามปล่อยบอทรันค้าง

## Success Criteria (ตรวจทั้งไฟล์ ต้องผ่านทั้ง 2 ข้อพร้อมกัน)
1. `_determine_direction()` ต้องเป็น `price > ema20 > ema50 > ema100` (เวอร์ชัน TASK 1B) — **ไม่เปลี่ยนแปลง**
2. `_slope_to_strength()` ต้องรับ `direction` เป็น parameter แรก และคืนค่า 20 ทันทีเมื่อ `direction == 'NONE'`
3. เมื่อ `direction == 'NONE'` → `analysis.trend_strength_score` ในไฟล์ output `.txt` ต้องเป็น 20 เสมอ
4. ไม่มีไฟล์อื่นถูกแก้ไข
5. รัน `runner.py` แล้วไม่มี Exception จาก `trend_engine.py`
