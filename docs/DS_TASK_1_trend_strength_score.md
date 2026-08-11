# TASK 1/7 — แก้ไข trend_strength_score ไม่ผูกกับ trend_direction

## สถานะ: อนุมัติจาก Boss แล้ว — ลงมือแก้ได้ทันที

## ไฟล์ที่ต้องแก้ (ไฟล์เดียวเท่านั้น)
`data_evaluate/orchestration/market_classifier/trend_engine.py`

## ไฟล์ที่ห้ามแตะ
ทุกไฟล์อื่นทั้งหมด รวมถึง `data_feed/` (ห้ามแตะเด็ดขาดตาม AGENTS.md ข้อ 18)

## ปัญหา (ยืนยันจากการตรวจโค้ดจริงแล้ว)
ฟังก์ชัน `_slope_to_strength()` คำนวณ `trend_strength_score` จากค่าสัมบูรณ์ของ slope เพียงอย่างเดียว โดยไม่ตรวจสอบ `direction` เลย ทำให้เมื่อ `direction == 'NONE'` (EMA ไม่เรียงลำดับ) แต่ราคาแกว่งแรงในช่วงสั้น (slope สูง) จะได้ `trend_strength_score = 100` ซึ่งขัดแย้งกับความหมายจริง (ไม่มีเทรนด์) และส่งผลกระทบไปถึงคะแนนจำแนกสภาวะตลาดใน `market_state_classifier.py` (TRENDING_STRONG, TRENDING_WEAK, ACCUMULATION, DISTRIBUTION)

## จุดสังเกต: ไฟล์นี้มี pattern การจัดการ direction=='NONE' อยู่แล้วในฟังก์ชันอื่นในไฟล์เดียวกัน ให้ใช้ pattern เดียวกัน:
- `_score_confidence()`: `if direction == 'NONE': return 20`
- `_calculate_reversal_risk()`: `if direction == 'NONE': return 50`
- `_calculate_sustain_probability()`: `if direction == 'NONE': return 30`

## การแก้ไขที่ต้องทำ

หาฟังก์ชันนี้ใน `trend_engine.py`:

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
def _slope_to_strength(self, slope, thresholds, direction: str = None) -> int:
    if direction == 'NONE':
        return 20  # ไม่มีทิศทางเทรนด์ที่ชัดเจน = ไม่ควรได้คะแนนความแข็งแรงสูง (ตาม pattern เดียวกับ _score_confidence/_calculate_sustain_probability ในไฟล์นี้)
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

แก้เป็น (ส่ง `direction` เข้าไปด้วย):

```python
return {
    'direction': direction,
    'strength': self._slope_to_strength(slope, thresholds, direction=direction),
    ...
}
```

## ขั้นตอนดำเนินการ (บังคับตาม AGENTS.md)
1. แก้เฉพาะ 2 จุดข้างต้นในไฟล์เดียว ห้ามแตะโค้ดส่วนอื่น
2. ห้าม silent fallback ใดๆ เพิ่มเติมนอกเหนือจากที่ระบุ (Fail-Fast ตามเดิม)
3. ทดสอบต้องรันผ่าน `runner.py` เท่านั้น (ห้ามเขียน script ทดสอบแยก)
4. รันบน CMD/Terminal แบบเปิดเผยเท่านั้น
5. หลังทดสอบเสร็จต้อง kill process ทันที ห้ามปล่อยบอทรันค้าง

## Success Criteria
- เมื่อ `direction == 'NONE'` → `trend_strength` (ในไฟล์ output `.txt` ที่ `analysis.trend_strength_score`) ต้องได้ค่า 20 เสมอ ไม่ใช่ 100
- เมื่อ `direction` เป็น 'UP' หรือ 'DOWN' → พฤติกรรมเดิมทุกอย่างเหมือนเดิมไม่เปลี่ยนแปลง (คำนวณจาก slope ตามปกติ)
- ไม่มีไฟล์อื่นถูกแก้ไข
- รัน `runner.py` แล้วไม่มี Exception จาก `trend_engine.py`
