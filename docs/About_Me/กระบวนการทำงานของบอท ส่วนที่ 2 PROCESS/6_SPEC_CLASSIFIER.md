# SPEC: MARKET STATE CLASSIFIER

## ภาพรวม
รับ output จาก Tier 1 ทั้ง 5 engines (trend, strength, volatility, structure, mtf) → จำแนกตลาดเป็น 10 ประเภทหลักโดยใช้ระบบถ่วงน้ำหนักคะแนน (Weighted Scoring System) เพื่อให้เหมาะกับการเทรด Binary Options แบบ 5 นาที

**File:** `data_evaluate/orchestration/market_classifier/market_state_classifier.py`  
**Depends on:** trend, strength, volatility, structure, mtf (ทุกตัว)

---

## Input Schema
ส่งข้อมูลผ่าน kwargs และ payload โดยตรง:
```python
payload = {
    'm5': dict,                 # ข้อมูล indicator พื้นฐาน M5
    'price_action': dict,       # ข้อมูล Price Action
    'ohlcv': dict               # ข้อมูลราคา OHLCV ล่าสุด
}

kwargs = {
    'trend_data': dict,         # จาก trend_engine
    'strength_data': dict,      # จาก strength_engine
    'volatility_data': dict,    # จาก volatility_engine
    'structure_data': dict,     # จาก structure_engine
    'mtf_data': dict,           # จาก mtf_engine
    'symbol': str               # ชื่อคู่เงิน (เช่น EURUSD, EURGBP-OTC)
}
```

---

## Output Schema
```python
{
    'state': str,               # 1 ใน 10 states ด้านล่าง
    'confidence': int,          # ระดับความเชื่อมั่น 0-100
    'quality_score': int,       # คะแนนคุณภาพของตลาด 0-100
    'tradeable': bool,          # ตลาดอยู่ในสภาวะที่น่าเทรดหรือไม่ (True/False)
    'stability': int,           # คะแนนความเสถียรของสภาวะตลาด 0-100
    'description': str,         # คำอธิบายภาษาอังกฤษเชิงแนะนำกลยุทธ์
    'breakout_prob': float,     # ความน่าจะเป็นในการเกิด Breakout
    'reversal_prob': float,     # ความน่าจะเป็นในการเกิด Reversal
    'risk_level': str,          # ระดับความเสี่ยง ('LOW' | 'MEDIUM' | 'HIGH')
    'suggested_action': str,    # แนะนำการปฏิบัติงาน ('PREPARE_TO_TRADE' | 'WAIT')
    'suggested_expiry': int,    # เวลาหมดอายุที่แนะนำ (ค่าเริ่มต้น 5 นาที)
    'metrics': dict             # ค่าน้ำหนักทางคณิตศาสตร์ทั้งหมดที่ใช้ประมวลผล
}
```

---

## 10 Market States — การคำนวณคะแนนดิบ (Weighted Scores)

ระบบจะคำนวณคะแนนดิบ (Raw Score) ของทั้ง 10 สถานะขึ้นมาพร้อมกัน จากนั้นปรับจูนด้วยตัวแปรเสริม (Boosts & Penalties) และเลือกสถานะที่ได้คะแนนสูงสุด

### 1. TRENDING_STRONG
คะแนนดิบเริ่มต้นจาก ADX (35%), Trend Strength (30%), MTF Alignment (20%) และ 1 - Noise Level (15%)
```
เงื่อนไข & การปรับแต่ง:
- เพิ่มคะแนน (+10): หากทิศทางแนวโน้มไม่ใช่ 'NONE'
- เพิ่มคะแนน (+10): หากโครงสร้างตลาดเป็น 'TRENDING' หรือ 'BREAKOUT'
- เพิ่มคะแนน (+5): หากพบการเกิด BOS (Breakout of Structure)
- เพิ่มคะแนน (+10): หาก MTF Alignment >= 70%
- หักคะแนน (-20): หากระดับ Noise > 0.6
- หักคะแนน (-20): หากระดับ Exhaustion Risk > 70%
- หักคะแนน (-15): หากทิศทางกรอบเวลาหลักกับย่อยขัดแย้งกัน (htf_ltf_conflict)
```

### 2. TRENDING_WEAK
คะแนนดิบเริ่มต้นจาก ADX (30%), Trend Strength (25%), 1 - Noise Level (25%) และ MTF Alignment (20%)
```
เงื่อนไข & การปรับแต่ง:
- เพิ่มคะแนน (+10): หากทิศทางแนวโน้มไม่ใช่ 'NONE'
- เพิ่มคะแนน (+5): หากโครงสร้างตลาดเป็น 'TRENDING' หรือ 'CORRECTIVE'
- หักคะแนน (-25): หากระดับ Exhaustion Risk > 70%
- หักคะแนน (-10): หากทิศทางกรอบเวลาหลักกับย่อยขัดแย้งกัน (htf_ltf_conflict)
- หักคะแนน (-15): หากระดับ Noise > 0.5
```

### 3. SIDEWAY_RANGE
คะแนนดิบเริ่มต้นจาก 1 - ADX (35%), โครงสร้างเป็น 'RANGING' (25%), 1 - Noise Level (20%) และ Volatility Regime ในช่วง Low หรือ Normal (20%)
```
เงื่อนไข & การปรับแต่ง:
- เพิ่มคะแนน (+15): หาก ADX < 18
- เพิ่มคะแนน (+10): หากระดับ Noise < 0.3
- หักคะแนน (-20): หากพบ BOS
- หักคะแนน (-15): หาก breakout_probability > 50%
```

### 4. BREAKOUT_EMERGING
คะแนนดิบเริ่มต้นจาก ระดับบีบตัวของ Bollinger Bands (30%), Volatility Percentile ต่ำ (20%), Breakout Probability (25%) และ BOS Detected (15%)
```
เงื่อนไข & การปรับแต่ง:
- ปัจจัยปริมาณซื้อขาย (Volume Factor): บวกคะแนนตามสัดส่วน Volume Ratio สูงสุดไม่เกิน +10 คะแนน (สำหรับคู่เงิน OTC จะได้เต็ม +10 ทันที)
- เพิ่มคะแนน (+15): หาก bbw < 0.04 (บีบอัดตัวรุนแรง)
- เพิ่มคะแนน (+10): หาก ATR Percentile < 30
- เพิ่มคะแนน (+10): หากไม่ใช่ OTC และ Volume Ratio > 1.5
- หักคะแนน (-15): หากระดับ Noise > 0.5
- หักคะแนน (-20): หากทิศทางกรอบเวลาขัดแย้งกัน
```

### 5. REVERSAL_FORMING
คะแนนดิบเริ่มต้นจาก Reversal Probability (35%), ADX ต่ำ (25%), พบ Divergence (20%) และ 1 - Noise Level (20%)
```
เงื่อนไข & การปรับแต่ง:
- เพิ่มคะแนน (+15): หาก RSI อยู่ในเขตตึงตัวสุดขั้ว (< 30 หรือ > 70)
- เพิ่มคะแนน (+10): หากโครงสร้างเป็นแบบปรับฐาน 'CORRECTIVE'
- หักคะแนน (-15): หากระดับ Noise > 0.5
- หักคะแนน (-10): หากทิศทางกรอบเวลาขัดแย้งกัน
```

### 6. ACCUMULATION (การสะสมกำลังขาขึ้น)
คะแนนดิบเริ่มต้นจาก สัดส่วนไส้เทียนด้านล่างยาว (35%), ปัจจัย Volume (สูงสุด 25%), Trend Strength ต่ำ (20%) และ โครงสร้างเป็น Ranging หรือ Corrective (20%)
```
เงื่อนไข & การปรับแต่ง:
- เพิ่มคะแนน (+15): หากไม่ใช่ OTC และ Volume Ratio > 1.2
- เพิ่มคะแนน (+10): หากสัดส่วนไส้เทียนล่างยาวมาก (wick_lower_ratio > 0.5)
- หักคะแนน (-15): หากพบ BOS
- หักคะแนน (-10): หากตรวจเจอ Divergence
```

### 7. DISTRIBUTION (การกระจายสินค้าขาลง)
คะแนนดิบเริ่มต้นจาก สัดส่วนไส้เทียนด้านบนยาว (35%), ปัจจัย Volume (สูงสุด 25%), Trend Strength ต่ำ (20%) และ โครงสร้างเป็น Ranging หรือ Corrective (20%)
```
เงื่อนไข & การปรับแต่ง:
- เพิ่มคะแนน (+15): หากไม่ใช่ OTC และ Volume Ratio > 1.2
- เพิ่มคะแนน (+10): หากสัดส่วนไส้เทียนบนยาวมาก (wick_upper_ratio > 0.5)
- หักคะแนน (-15): หากพบ BOS
- หักคะแนน (-10): หากตรวจเจอ Divergence
```

### 8. CHOPPY_UNCERTAIN (ตลาดสับสนไร้แนวโน้ม)
คะแนนดิบเริ่มต้นจาก ระดับ Noise Level (60%), ADX ต่ำ (20%) และ โครงสร้างตลาดแบบ CHOPPY (20%)
```
เงื่อนไข & การหักล้าง:
- หักคะแนน (-20): หาก Trend Strength ยังชัดเจน (> 40)
- หักคะแนน (-15): หาก MTF Alignment Score สูง (> 50)
```

### 9. LIQUIDITY_VOID (ตลาดสภาพคล่องต่ำผิดปกติ)
คำนวณเฉพาะคู่เงินปกติ (ไม่ใช่คู่เงิน OTC)
```
เงื่อนไข:
- คะแนนดิบเริ่มต้นอิงจากความผกผันของปริมาณการซื้อขาย (50%) และ ADX ต่ำเฉื่อยชา (50%)
- หากเป็นคู่เงิน OTC สถานะนี้จะถูกเซตคะแนนเป็น 0 เสมอ
```

### 10. UNCLEAR
หากคะแนนสะสมของทุกสถานะต่ำกว่า 40 คะแนน หรือเกิดข้อผิดพลาดในการประมวลผลข้อมูล ระบบจะเลือกใช้สถานะ 'UNCLEAR' เป็นค่ามาตรฐานความปลอดภัยในการเลี่ยงเทรด

---

## Classification Logic & State Smoothing
เพื่อให้ระบบไม่เปลี่ยนสถานะไปมารวดเร็วเกินไป (Rapid Flipping) จนส่งผลต่อระบบส่งสัญญาณเทรด ระบบใช้หลักการดังนี้:

1. **State history:** ระบบจะเก็บประวัติสถานะย้อนหลังไว้สูงสุด 5 แท่ง (`_state_history`)
2. **Buffer Margin สำหรับ Liquidity Void:** หากระบบตัดสินใจเลือก `LIQUIDITY_VOID` แต่แท่งก่อนหน้าไม่ใช่ จะต้องมีคะแนนนำสถานะอันดับสองมากกว่าหรือเท่ากับ 15 คะแนนเท่านั้นเพื่อบังคับเปลี่ยน หากไม่ถึงจะยกเลิกและปรับไปใช้สถานะอันดับสองทดแทน
3. **State Smoothing logic:** หากคะแนนความเชื่อมั่น (Confidence) ต่ำกว่า 60 และสถานะใหม่ขัดแย้งกับประวัติส่วนใหญ่ใน 3 แท่งก่อนหน้า ระบบจะดึงสถานะเดิมมาคงสภาพไว้ชั่วคราวเพื่อรอการยืนยันในแท่งถัดไป

---

## Composite Score & Metrics Scoring
การคำนวณหาคะแนนคุณภาพของตลาด (`quality_score` 0-100) คำนวณแบบถ่วงน้ำหนักจากคะแนนที่ประมวลผลได้:
- **Trend Score (35%)**: `(trend_strength × 0.3) + (trend_confidence × 0.7)`
- **Strength Score (30%)**: `(adx / 100 × 50) + (strength_score × 0.5)`
- **Volatility Score (20%)**: `volatility_score`
- **Structure Score (15%)**: `structure_score`

ค่ารวมทั้งหมดจะถูกนำไปปรับค่าความสั่นไหวกับค่า MTF Multiplier (`alignment_score` สูงช่วยเพิ่มความคุ้มค่า และหักคะแนนหากตลาดมีความขัดแย้งในกรอบเวลารุ่นพี่)

---

## Strategy Mapping
ตารางจับคู่สถานะและระดับสิทธิ์การเทรด (Tradeability flag):

| State | Tradeable (สิทธิ์การเข้าเทรด) | Action แนะนำ |
|-------|------------------------------|--------------|
| TRENDING_STRONG | **True** (หาก quality_score >= 50) | `PREPARE_TO_TRADE` |
| TRENDING_WEAK | **True** (หาก quality_score >= 55) | `WAIT` |
| BREAKOUT_EMERGING | **True** (หาก quality_score >= 50) | `PREPARE_TO_TRADE` |
| SIDEWAY_RANGE | **True** (หาก quality_score >= 50) | `WAIT` |
| REVERSAL_FORMING | **False** (เสี่ยงกลับตัวเฉียบพลัน) | `WAIT` |
| ACCUMULATION | **False** (สภาวะรอการสะสมแรง) | `WAIT` |
| DISTRIBUTION | **False** (สภาวะรอการสะสมแรง) | `WAIT` |
| CHOPPY_UNCERTAIN | **False** (หลีกเลี่ยงการเทรด) | `WAIT` |
| LIQUIDITY_VOID | **False** (หลีกเลี่ยงการเทรด) | `WAIT` |
| UNCLEAR | **False** (หลีกเลี่ยงการเทรด) | `WAIT` |
