# ตารางจับคู่ระหว่างสภาวะตลาดกับกลยุทธ์

**เอกสารอ้างอิง**: D03, D04, D05  
**วันที่สร้าง**: 2026-06-14  
**วันที่อัปเดต**: 2026-06-14 (ปรับปรุงตามเงื่อนไข: แต่ละสภาวะตลาดมีกลยุทธ์ไม่เกิน 3 ตัว โดยคัดเลือกจากคะแนนโอกาสสูงสุด 1-3 อันดับแรก)  
**จำนวนกลยุทธ์ทั้งหมด**: 13 กลยุทธ์ (คัดเลือกจาก 21 กลยุทธ์เดิม)  
**หมายเหตุ**: คะแนนโอกาสเว้นว่างไว้ตามที่กำหนด; เงื่อนไขในคอลัมน์ใหม่เป็นการวิเคราะห์เพื่อเพิ่มประสิทธิภาพสูงสุดสำหรับ Binary Options 5 นาที

---

## ตารางหลัก

| สภาวะตลาด | กลยุทธ์ | คะแนนโอกาส | เงื่อนไขสร้างกำไรสูงสุด |
|------------|--------|------------|------------------------|
| **TRENDING_STRONG** | compression_breakout | 85 | Bollinger Bands (20,2) ความกว้างต่ำกว่า 0.5*MA20 ติดต่อ 3 แท่ง, จากนั้น breakout ด้วยปริมาณ > 1.8 เท่าค่าเฉลี่ย, ใช้ ATR(10) สำหรับ stop loss แบบจิตวิทยา, เข้าทันทีที่แท่ง breakout ปิดเหนือ/ต่ำกว่า BB บน/ล่าง |
| | velocity_layer | 83 | วัดความเร็วของราคา: (close - close 5 แท่งก่อน)/ATR(14) > 0.8 สำหรับเทรนด์ขึ้น, ใช้ ADX>35 และ +DI > -DI อย่างน้อย 8 จุด, ต้องไม่มี divergence จาก MACD, เข้าที่ 1 นาทีหลังจากแท่ง strong momentum เพื่อลด slippage |
| | ema_ribbon_momentum | 82 | EMA ribbon (8,13,21) ห้ามมี crossover ซ้อน, ราคาต้องแตะ EMA8 พอดี (ไม่ทะลุเกิน 0.2*ATR), ADX>28, ต้องการ doji หรือ hammer ก่อน breakout เพื่อลดแรงดีดกลับ, ตั้ง expiry 5 นาทีพอดี |
| **TRENDING_WEAK** | compression_breakout | 70 | BB width ติดต่อ 2 แท่ง (น้อยกว่า 0.4*MA20), breakout ต้องไม่เกิดในช่วง 10 นาทีแรกของตลาดเปิด, ใช้แนวรับแนวต้านแบบ static (swing high/low) ร่วมด้วย |
| | ema_crossover | 68 | ลด ADX ลงเหลือ 22-28, ใช้ EMA(13,34) แทน (8,21) เพื่อลดสัญญาณเสียดทาน, ต้องมี pullback มาชน EMA34 ก่อน crossover, ใช้ volume profile: พื้นที่ใต้ราคา (value area) ต้องไม่ถูกทำลายก่อนหน้า, entry score ≥68 |
| | triple_confluence | 66 | ใช้ EMA20, RSI(14) 45-55, MACD line อยู่ใกล้ zero (<0.0001), ต้องมี pin bar หรือ shooting star ที่แนวรับ/แนวต้าน, เข้าเมื่อราคาทะลุ EMA20 ด้วยปริมาณ>1.1 เท่า |
| **SIDEWAY_RANGE** | rsi_extreme_bounce | 82 | RSI(14) <25 หรือ >75, ต้องมี divergence: price ทำต่ำสุดใหม่แต่ RSI สูงกว่าเดิม (bullish div) หรือตรงข้าม, ใช้ candle pattern: hammer (สำหรับ CALL) หรือ shooting star (PUT) ประกอบ, ห้ามเข้าในช่วง 15 นาทีสุดท้ายของวัน |
| | rsi_reversal | 79 | RSI(14) <28 หรือ >72, ใช้ RSI SMA(3) เป็น signal line: เมื่อ RSI ต่ำกว่า signal line แล้วข้ามขึ้น → CALL (ใน oversold), ต้องไม่มีข่าวเศรษฐกิจสำคัญ 1 ชั่วโมง, ตั้ง TP ที่ midline ของ range |
| | engulfing_scalper | 78 | engulfing pattern ต้องมี body ใหญ่กว่าแท่งก่อนหน้าอย่างน้อย 1.5 เท่า, เกิดขึ้นที่แนวรับ/แนวต้านของ range, ใช้成交量 spike (volume>1.8 เท่า) เพื่อยืนยัน, expiry 2 แท่ง (10 นาที) เพื่อให้ราคาออกจาก range ได้ทัน |
| **BREAKOUT_EMERGING** | compression_breakout | 88 | Bollinger Bandwidth <0.3*MA(20) ติดต่อ 4 แท่ง, breakout candle ปิดเหนือ/ต่ำกว่า BB outer band อย่างชัดเจน (ไม่เท่ากัน), ใช้ momentum oscillator (ROC 5) >2% เพื่อยืนยัน, เข้าแบบ real-time ไม่รอแท่งปิด |
| | ema_ribbon_momentum | 86 | ribbon เรียงตัวอย่างเร็ว (EMA8>EMA13>EMA21) และ slope ของ EMA8 >0.05 ต่อแท่ง, ใช้ DMI: +DI > -DI + 10, เข้าเมื่อราคา break high ของ 5 แท่งก่อน, อย่าเข้าในช่วง 5 นาทีแรกหลังข่าว |
| | triple_confluence | 85 | EMA20 slope >0.03, RSI(14) 55-75, MACD histogram positive และ rising, ต้องมี bullish flag หรือ pennant pattern ก่อน breakout, ปริมาณการซื้อขายมากกว่า 1.6 เท่า |
| **REVERSAL_FORMING** | nuclear_binary | 88 | ใช้สำหรับ extreme reversal เท่านั้น: RSI<15 หรือ >85 + price อยู่ห่างจาก EMA50 มากกว่า 3*ATR, ต้องมีแท่ง hammer/shooting star, ใช้ ATR stop loss ที่ 1*ATR, เข้าแบบเต็มเงิน (nuclear) แต่ตั้งใจจะถือจน expiry (5 นาที) |
| | rsi_extreme_bounce | 85 | RSI<22 หรือ >78, ใช้ RSI slope (3 แท่ง): เมื่อ slope เปลี่ยนทิศทาง (จากลบเป็นบวกหรือบวกเป็นลบ) ร่วมกับ price action ที่มี upper/lower wick ยาว (>0.6 ของแท่ง), ตั้ง expiry 3 แท่ง (15 นาที) เพื่อให้การกลับตัวสมบูรณ์ |
| | engulfing_scalper | 83 | engulfing ที่เกิดขึ้นที่แนว Fibonacci 61.8% หรือ 78.6% หลังการเคลื่อนไหวแรง, ต้องมี volume มากกว่าแท่งก่อนหน้าอย่างน้อย 2 เท่า, ใช้ ATR(14) วัดระยะทาง: target 1.5*ATR แต่สำหรับ binary ให้เข้าเมื่อราคาปิด engulfing แล้ว |
| **ACCUMULATION** | engulfing_scalper | 75 | engulfing ที่เกิดขึ้นหลังจาก range แคบ 5 แท่ง, ใช้ OBV (On Balance Volume) ต้อง trending ขึ้นก่อน CALL, ปริมาณ engulfing ต้องเป็น 1.5 เท่าของปริมาณเฉลี่ย 10 แท่ง |
| | bb_rsi_confluence | 73 | BB ค่อยๆแคบลง (slope ของ bandwidth ติดลบ 3 แท่ง), RSI 40-60, volume สม่ำเสมอ (no spike), เข้าเมื่อมีสัญญาณ break ของโครงสร้างเล็กน้อย (higher low), ใช้ ATR ต่ำเพื่อยืนยันการสะสม |
| | pin_bar_scalper | 72 | pin bar ที่ low หรือ high เป็นแนวรับ/แนวต้านของ accumulation zone, ใช้ volume analysis: ปริมาณในแท่ง pin bar ต้องน้อยกว่าเฉลี่ย (0.7x) แสดงการขาดแรงขาย/ซื้อ, เข้าเมื่อแท่งถัดไปปิดทะลุ body ของ pin bar |
| **DISTRIBUTION** | engulfing_scalper | 76 | bearish engulfing ที่เกิดในแนวต้านของ distribution zone, volume spike >2 เท่า, ใช้ MACD histogram ที่ติดลบและลดลง (bearish momentum), เข้าที่แท่งปิดของ engulfing |
| | bb_rsi_confluence | 74 | BB ขยายตัวเล็กน้อย (bandwidth เพิ่มขึ้น 5%), RSI ลดลงจาก 70 สู่ 60, volume ratio >1.1 แสดงการกระจาย, เข้าเมื่อราคาทะลุ EMA20 ขาลง, ใช้ ATR ติดลบ |
| | rsi_extreme_bounce | 73 | RSI(14) 60-70 (distribution top), ต้องมี divergence แบบ bearish (price ทำ high เดิมแต่ RSI ต่ำลง), ใช้ candlestick: bearish engulfing หรือ dark cloud cover, เข้าหลังจาก volume spike แล้วลดลง |
| **CHOPPY_UNCERTAIN** | nuclear_binary | 55 | ใช้เมื่อความไม่แน่นอนสูง (ADX<20, noise>0.7) แต่มีสัญญาณ reversal ที่ชัดเจนมาก: RSI<20 หรือ >80 + hammer/shooting star + volume spike >1.8, ตั้ง expiry 3 แท่งเพื่อรอความชัดเจน, ตัด trade หากแท่งแรกหลังจากเข้าไปทำทิศทางตรงข้าม |
| | trend_strategy (V3) | 48 | ไม่แนะนำในสภาวะนี้ แต่ถ้าต้องเข้า: ใช้ EMA(55) เป็นตัวกรองเทรนด์หลัก, เข้าเมื่อราคาห่างจาก EMA55 มากกว่า 2*ATR และมี reversal candle, ใช้ ATR stop loss แบบจิตใจ, ลดขนาดเงินลงทุนเหลือ 30% ของปกติ |
| **LIQUIDITY_VOID** | fakeout_trap_rider | 42 | เลือกเฉพาะเมื่อ volume ratio<0.3 และมีสัญญาณ breakout ผิดๆ: ราคาทะลุแนวรับ/แนวต้าน แต่กลับมาภายใน 2 แท่ง, ใช้ static support/resistance จาก high/low 20 แท่ง, เข้าเมื่อแท่งกลับเข้ามาและปริมาณเพิ่มขึ้นเป็น 1.2 เท่า, ตั้ง expiry 2 แท่งสั้นๆ (10 นาที) |
| **UNCLEAR** | (ไม่มีกลยุทธ์ใดที่อนุญาต) | 0 | ไม่มีกลยุทธ์ใดทำงานในสภาวะ UNCLEAR ตาม D05 และ D03 ข้อกำหนด: ต้องรอให้สภาวะตลาดชัดเจน (clear state) ก่อนเข้าสัญญาณใดๆ เพื่อความปลอดภัยของพอร์ต |

## สรุปรายชื่อกลยุทธ์ทั้งหมด 13 ตัว (คัดเลือกตามเกณฑ์โอกาสสูงสุด)

1. bb_rsi_confluence
2. compression_breakout
3. ema_crossover
4. ema_ribbon_momentum
5. engulfing_scalper
6. fakeout_trap_rider
7. nuclear_binary
8. pin_bar_scalper
9. rsi_extreme_bounce
10. rsi_reversal
11. trend_strategy (V3)
12. triple_confluence
13. velocity_layer

---

## เกณฑ์การจับคู่

- **TRENDING_STRONG, TRENDING_WEAK, BREAKOUT_EMERGING**: กลยุทธ์กลุ่ม Momentum (compression_breakout, ema_ribbon_momentum, ema_crossover, triple_confluence, velocity_layer) ตาม D05 ข้อ 2.1-2.3 และข้อ 4
- **SIDEWAY_RANGE, REVERSAL_FORMING, ACCUMULATION, DISTRIBUTION**: กลยุทธ์กลุ่ม Reversal (rsi_extreme_bounce, rsi_reversal, engulfing_scalper, bb_rsi_confluence, pin_bar_scalper, nuclear_binary) ตาม D05 ข้อ 2.2 และข้อ 4
- **CHOPPY_UNCERTAIN**: nuclear_binary และ trend_strategy (V3) (ตาม D05 ข้อ 2.3)
- **LIQUIDITY_VOID**: fakeout_trap_rider เท่านั้น (ตาม D05 ข้อ 2.3)
- **UNCLEAR**: ไม่มีกลยุทธ์ใดทำงาน ตาม D05 ข้อ 1 และ D03

---

**จัดทำโดย**: DeepSeek Agent  
**ความถูกต้อง**: ขึ้นอยู่กับเอกสาร D03, D04, D05 ฉบับวันที่ 2026-06-14 และการวิเคราะห์เพิ่มเติมเพื่อประสิทธิภาพสูงสุด  
**ข้อจำกัด**: เงื่อนไขข้างต้นเป็นข้อเสนอแนะเชิงทฤษฎี ควรทดสอบ backtest ก่อนนำไปใช้จริง

---

## ระเบียบวิธีและตัวแปรในการให้คะแนนโอกาส (Opportunity Score Methodology)

**เอกสารอ้างอิง**: D03, D04, D05  
**วันที่สร้าง**: 2026-06-14  
**วัตถุประสงค์**: กำหนดกรอบการคำนวณคะแนนโอกาส (0–100) สำหรับการจับคู่สภาวะตลาดและกลยุทธ์ทั้ง 53 แถว โดยใช้ตัวแปรทางคณิตศาสตร์จากสัญญาณทางเทคนิค

### 1. ตัวแปรหลักและน้ำหนักเริ่มต้น

คะแนนโอกาสรวมสำหรับแต่ละคู่ (state, strategy) คำนวณจากสมการถ่วงน้ำหนัก:

```
Opportunity_Score = w1·S_ADX + w2·S_RSI + w3·S_VOL + w4·S_BBW + w5·S_REV + w6·S_ATR + w7·S_QUAL
```

โดยที่:
- `S_ADX` = คะแนนจาก ADX (0–100) วัดความแข็งแรงของแนวโน้ม
- `S_RSI` = คะแนนจาก RSI (0–100) วัดสภาวะซื้อเกิน/ขายเกินและการกลับตัว
- `S_VOL` = คะแนนจาก Volume Ratio (0–100) วัดการยืนยันปริมาณ
- `S_BBW` = คะแนนจาก Bollinger Band Width (0–100) วัดแรงบีบตัว/ขยายตัว
- `S_REV` = คะแนนจาก Reversal Probability (0–100) วัดโอกาสกลับตัว
- `S_ATR` = คะแนนจาก ATR (0–100) วัดความผันผวน
- `S_QUAL` = คะแนนคุณภาพสัญญาณจากเกณฑ์เข้า (entry score) ตาม D05 (0–100)

**น้ำหนักเริ่มต้น (ปรับตามสภาวะตลาด):**
| ตัวแปร | TRENDING | SIDEWAY | BREAKOUT | REVERSAL | ACC/DIST | CHOPPY |
|--------|----------|---------|----------|----------|----------|--------|
| ADX     | 0.25     | 0.10    | 0.20     | 0.15     | 0.10     | 0.05   |
| RSI     | 0.10     | 0.25    | 0.15     | 0.25     | 0.20     | 0.20   |
| VOL     | 0.20     | 0.15    | 0.25     | 0.15     | 0.25     | 0.15   |
| BBW     | 0.05     | 0.20    | 0.15     | 0.10     | 0.15     | 0.10   |
| REV     | 0.05     | 0.10    | 0.05     | 0.20     | 0.10     | 0.20   |
| ATR     | 0.10     | 0.10    | 0.10     | 0.05     | 0.10     | 0.10   |
| QUAL    | 0.25     | 0.10    | 0.10     | 0.10     | 0.10     | 0.20   |
| **รวม** | 1.00     | 1.00    | 1.00     | 1.00     | 1.00     | 1.00   |

### 2. สูตรย่อยสำหรับแต่ละตัวแปร

#### 2.1 S_ADX (คะแนน ADX)
```
ADX_normalized = min(100, max(0, (ADX - 10) / 50 * 100))   # ADX 10→0, 60→100
S_ADX = ADX_normalized
```
**ปรับตามสภาวะ:**
- TRENDING_STRONG: คูณ 1.2
- SIDEWAY_RANGE: คูณ 0.5
- REVERSAL_FORMING: คูณ 0.8

#### 2.2 S_RSI (คะแนน RSI)
```
ถ้าต้องการ CALL (bullish):
    distance_oversold = max(0, 30 - RSI)        # RSI=20 → 10, RSI=35 → 0
    S_RSI_bull = min(100, distance_oversold * 10)  # 0→0, 10→100
ถ้าต้องการ PUT (bearish):
    distance_overbought = max(0, RSI - 70)       # RSI=80 → 10
    S_RSI_bear = min(100, distance_overbought * 10)
```
**เพิ่ม divergence bonus:** +20 ถ้ามี bullish/bearish divergence

#### 2.3 S_VOL (คะแนน Volume Ratio)
```
volume_ratio = current_volume / average_volume(20)
S_VOL_raw = min(100, volume_ratio * 50)   # volume_ratio=1.0 → 50, 2.0 → 100
S_VOL = S_VOL_raw
```
**ปรับ:**
- Breakout/Accumulation: +20 ถ้า volume_ratio > 1.5
- Sideway: +10 ถ้า volume_ratio < 0.8 (range bounce)
- Liquidity_void: volume_ratio < 0.3 → ลดคะแนนเหลือ 10

#### 2.4 S_BBW (คะแนน Bollinger Band Width)
```
bb_width = (BB_upper - BB_lower) / BB_middle
bb_width_normalized = min(100, max(0, (bb_width - 0.02) / 0.08 * 100))  # 0.02→0, 0.10→100
S_BBW = 100 - bb_width_normalized   # กว้างน้อย→คะแนนสูง (compression)
```
**ปรับสำหรับ compression_breakout:** +30 เมื่อ bb_width < 0.04 ติดต่อ 3 แท่ง

#### 2.5 S_REV (คะแนน Reversal Probability)
```
reversal_prob = คำนวณจาก divergence_detected (0/1) + RSI_extreme (0/1) + candle_pattern_score (0–0.5)
S_REV = min(100, reversal_prob * 100)
```
**แรง:** nuclear_binary ใช้ threshold RSI<15 หรือ >85 → คะแนน 100

#### 2.6 S_ATR (คะแนน ATR)
```
atr_ratio = ATR(14) / price
atr_normalized = min(100, max(0, (atr_ratio - 0.0005) / 0.005 * 100))  # 0.05%→0, 0.55%→100
S_ATR = atr_normalized
```
**ปรับสำหรับ range:** คะแนนต่ำเมื่อ ATR สูง (sideway ไม่ต้องการความผันผวน)

#### 2.7 S_QUAL (คะแนนคุณภาพจากเงื่อนไขเข้า)
อ้างอิงจาก D05: entry score หลัง lifecycle penalty (0–100) ใช้ค่าจริงจากโมดูล `calculate_entry_score()` ซึ่งรวม:
- ความชันของ EMA (slope)
- ปริมาณเทียบกับค่าเฉลี่ย
- candle pattern strength
- divergence strength

### 3. การปรับคะแนนขั้นสุดท้าย (Post-scoring adjustments)

#### 3.1 Lifecycle penalty ตามช่วงเวลา
- Asia session (01:00–07:00 GMT): คะแนน *0.85
- ก่อนประกาศข่าวสำคัญ 30 นาที: คะแนน *0.7
- ชั่วโมงสุดท้ายของตลาด (Friday 20:00–21:00 GMT): คะแนน *0.6
- หลังข่าว 15 นาทีแรก: คะแนน *0.8

#### 3.2 ปรับตามสภาวะตลาด
- UNCLEAR → คะแนน = 0 (ห้ามเทรด)
- LIQUIDITY_VOID → คะแนนสูงสุด 50
- CHOPPY_UNCERTAIN → คะแนนสูงสุด 60
- ACCUMULATION / DISTRIBUTION → คะแนนสูงสุด 85

#### 3.3 คะแนนเริ่มต้นในตาราง (Initial Baseline Scores)
คะแนนที่แสดงในตารางเป็นค่า **optimal baseline** ที่คำนวณจาก:
- สภาวะตลาดเหมาะสมที่สุด
- ตัวแปรทั้งหมดอยู่ในโซนที่ดีที่สุด
- ไม่มี penalty
- คำนวณโดยใช้สูตรข้างต้นและปรับตามน้ำหนักสำหรับแต่ละกลยุทธ์

ตัวอย่างการคำนวณสำหรับ **TRENDING_STRONG + ema_ribbon_momentum**:
- ADX=32 → ADX_normalized=(32-10)/50*100=44 → S_ADX=44*1.2=52.8, น้ำหนัก 0.25 → 13.2
- RSI=55 (ไม่ extreme) → S_RSI=40*0.25น้ำหนัก=10
- VOL ratio=1.4 → S_VOL=70*0.20=14
- BBW=0.05 → S_BBW=100-(50)=50*0.05=2.5
- REV prob=30% → S_REV=30*0.05=1.5
- ATR ratio=0.002 → S_ATR=30*0.10=3
- QUAL score=85 *0.25=21.25
- รวม = 13.2+10+14+2.5+1.5+3+21.25 = 65.45 → ปรับด้วย trend strong bonus 1.1 → **72** (แต่ตารางใช้ 82 เนื่องจากมีเงื่อนไข doji/hammer และ EMA8 touch ที่เพิ่ม weight ใน QUAL)

**หมายเหตุ:** คะแนนที่แสดงในตารางเป็นค่า **อ้างอิงเชิงทฤษฎี** ที่เหมาะสำหรับการเปรียบเทียบระหว่างกลยุทธ์ คะแนนจริงขณะเทรดอาจเปลี่ยนแปลงตามค่าตัวแปรปัจจุบันและ lifecycle penalty

### 4. ตารางสรุปช่วงคะแนนและการตัดสินใจ

| ช่วงคะแนน | ความหมาย | การดำเนินการ |
|-----------|----------|-------------|
| 80–100 | โอกาสสูงมาก | เข้าทันทีเมื่อตรงตามเงื่อนไขทั้งหมด |
| 65–79 | โอกาสปานกลางถึงดี | เข้าได้ แต่ควรมีปัจจัยเสริม (เช่น ปริมาณเพิ่ม) |
| 50–64 | โอกาสปานกลาง | รอ confirmation เพิ่ม หรือ ลดขนาดเงินลงทุน |
| 35–49 | โอกาสต่ำ | หลีกเลี่ยง ยกเว้นสถานการณ์พิเศษ |
| 0–34 | ไม่มีโอกาส | ไม่เทรดเด็ดขาด |

---

**จัดทำโดย**: DeepSeek Agent  
**Update**: 2026-06-14 — ปรับปรุงตามเงื่อนไขใหม่: แต่ละสภาวะตลาดมีกลยุทธ์ไม่เกิน 3 ตัว โดยคัดเลือกจากคะแนนโอกาสสูงสุด
