# SPEC: TIMEFRAME USAGE — M1, M5, M15

## หลักการใช้ TF
```
M15 → บอกทิศทางใหญ่ (Bias)
M5  → บอกสภาวะตลาดและสัญญาณ (Signal)
M1  → บอก Timing เข้าเทรด (Entry)
```

---

## M15 — Higher Timeframe Bias

### หน้าที่
- กำหนดทิศทางหลักของตลาด
- ห้ามเทรดสวนทาง M15
- ใช้เป็น Filter เท่านั้น ไม่ใช่ Signal

### สิ่งที่คำนวณ
```
EMA20, EMA50          → ทิศทางเทรนด์หลัก
Support, Resistance   → โซน S/R สำคัญ
Market_Bias           → BULLISH / BEARISH / NEUTRAL
Structure             → TRENDING / RANGING / BREAKOUT
```

### Logic
```
EMA20 > EMA50 → Bias = BULLISH  → รับสัญญาณ CALL เท่านั้น
EMA20 < EMA50 → Bias = BEARISH  → รับสัญญาณ PUT เท่านั้น
EMA20 ≈ EMA50 → Bias = NEUTRAL  → ระวัง / ลด size
```

### ส่งให้
```
→ IndicatorStore['m15']['bias']
→ ใช้ใน: Market State Classifier, AUTO_BOT filter, AI_BOT JSON
```

---

## M5 — Signal Timeframe

### หน้าที่
- กำหนดสภาวะตลาด (Market State)
- สร้างสัญญาณเทรดหลัก
- คำนวณ indicator หลักทั้งหมด

### สิ่งที่คำนวณ
```
EMA5, EMA10, EMA20, EMA50      → เทรนด์ M5
BB_Upper, BB_Lower, BB_Width   → volatility / compression
RSI7, RSI14                    → momentum / overbought / oversold
MACD, MACD_Signal, MACD_Hist   → momentum direction
Stoch_K, Stoch_D               → timing reversal
ATR14                          → ความผันผวน / position size
Support, Resistance            → โซน S/R M5
Pivot, R1, R2, S1, S2          → target / SL zone
Price Action (ทุกค่า)          → pattern / candle behavior
Market_State                   → สภาวะตลาดรวม
```

### Market State จาก M5
```
UPTREND       → EMA5>EMA10>EMA20>EMA50, RSI>50, MACD>0
DOWNTREND     → EMA5<EMA10<EMA20<EMA50, RSI<50, MACD<0
SIDEWAY       → EMA entangled, RSI 40-60, ATR ต่ำ
BREAKOUT      → BB_Width แคบแล้วขยาย, ATR พุ่ง, BOS detected
REVERSAL      → RSI divergence, MACD cross, pattern reversal
UNCLEAR       → สัญญาณขัดแย้ง → NO_SIGNAL
```

### ส่งให้
```
→ IndicatorStore['m5'][ทุกค่า]
→ ใช้ใน: Market State Classifier, AUTO_BOT signal, AI_BOT JSON
```

---

## M1 — Entry Timing Timeframe

### หน้าที่
- ยืนยันจังหวะเข้าเทรด
- กรอง false signal จาก M5
- ห้ามใช้หา Market State

### สิ่งที่คำนวณ
```
EMA5, EMA20            → momentum ระยะสั้น
RSI14                  → overbought/oversold ระยะสั้น
MACD, MACD_Signal      → momentum cross
Stoch_K, Stoch_D       → timing entry
BB_Upper, BB_Lower     → squeeze / expansion
ATR14                  → ความผันผวนระยะสั้น
Support, Resistance    → โซน M1
Last_Candle            → BULLISH / BEARISH
```

### Entry Confirmation Logic
```
สัญญาณ M5 = CALL และ:
  M1 RSI14 < 60        → ยังไม่ overbought
  M1 MACD > Signal     → momentum ขึ้น
  M1 Last_Candle = BULLISH → แท่งล่าสุดยืนยัน
  M15 Bias = BULLISH   → ทิศทางใหญ่ตรงกัน
→ ENTRY CONFIRMED

สัญญาณ M5 = PUT และ:
  M1 RSI14 > 40        → ยังไม่ oversold
  M1 MACD < Signal     → momentum ลง
  M1 Last_Candle = BEARISH → แท่งล่าสุดยืนยัน
  M15 Bias = BEARISH   → ทิศทางใหญ่ตรงกัน
→ ENTRY CONFIRMED

ถ้าไม่ครบ → NO_SIGNAL
```

### ส่งให้
```
→ IndicatorStore['m1'][ทุกค่า]
→ ใช้ใน: Entry confirmation, AUTO_BOT filter, AI_BOT JSON
```

---

## สรุปการทำงานร่วมกัน

```
M15 Bias (ทิศทางใหญ่)
    ↓
    Filter → ถ้าสวนทาง M15 → NO_SIGNAL ทันที
    ↓
M5 Signal (สภาวะตลาด + สัญญาณ)
    ↓
    ถ้า Market_State = UNCLEAR → NO_SIGNAL
    ถ้ามีสัญญาณ → ส่งต่อ
    ↓
M1 Entry Confirmation (จังหวะเข้า)
    ↓
    ยืนยันครบ → CALL / PUT
    ไม่ครบ    → NO_SIGNAL
```

---

## IndicatorStore Structure (3 TF)

```python
IndicatorStore['EURUSD-OTC'] = {
    'm15': {
        'ema20': float,
        'ema50': float,
        'support': float,
        'resistance': float,
        'bias': 'BULLISH' | 'BEARISH' | 'NEUTRAL',
        'structure': 'TRENDING' | 'RANGING' | 'BREAKOUT',
    },
    'm5': {
        'ema5': float, 'ema10': float, 'ema20': float, 'ema50': float,
        'bb_upper': float, 'bb_lower': float, 'bb_width': float,
        'rsi7': float, 'rsi14': float,
        'macd': float, 'macd_signal': float, 'macd_hist': float,
        'stoch_k': float, 'stoch_d': float,
        'atr14': float,
        'support': float, 'resistance': float,
        'pivot': float, 'r1': float, 'r2': float, 's1': float, 's2': float,
        'price_action': {
            'pattern': str,
            'last_candle': str,
            'body_strength': str,
            'rejection_zone': str,
            'wick_dominance': str,
            'momentum_bias': str,
            'move_quality': str,
            'trap_alert': str,
            'sr_interaction': str,
        },
        'market_state': str,
    },
    'm1': {
        'ema5': float, 'ema20': float,
        'rsi14': float,
        'macd': float, 'macd_signal': float,
        'stoch_k': float, 'stoch_d': float,
        'bb_upper': float, 'bb_lower': float,
        'atr14': float,
        'support': float, 'resistance': float,
        'last_candle': 'BULLISH' | 'BEARISH',
    },
    'current_price': float,
    'session': str,
    'timestamp': str,
    'expires_at': datetime,
}
```

---

## กฎ TF (ห้ามละเมิด)

```
✅ M15 = Bias filter เท่านั้น
✅ M5  = Signal หลัก + Market State
✅ M1  = Entry confirmation เท่านั้น
✅ ต้องผ่านทั้ง 3 TF จึง CALL/PUT ได้

❌ ห้ามหา Market State จาก M1
❌ ห้ามเทรดสวนทาง M15 Bias
❌ ห้ามใช้ M1 เป็น Signal หลัก
❌ ห้ามข้าม M1 confirmation
```

---

## AI System Prompt Rules (บังคับใส่ทุกครั้งที่ส่ง AI)

```
=== TIMEFRAME RULES (MUST FOLLOW) ===

M15 = Higher Timeframe Bias (ทิศทางใหญ่)
M5  = Signal Timeframe (สัญญาณหลัก)
M1  = Entry Confirmation (ยืนยัน timing)

กฎที่ต้องปฏิบัติ:
1. ดู M15 bias ก่อนเสมอ
   - M15 bias = BULLISH → รับแค่ CALL
   - M15 bias = BEARISH → รับแค่ PUT
   - M15 bias = NEUTRAL → NO_TRADE

2. ดู M5 market_state
   - UNCLEAR → NO_TRADE ทันที
   - ต้องสอดคล้องกับ M15 bias

3. ยืนยัน M1 ก่อนตัดสินใจ
   - M1 last_candle ต้องตรงทิศทาง
   - M1 momentum ต้องยืนยัน

4. ถ้าไม่ผ่านครบทั้ง 3 TF → NO_TRADE เท่านั้น

ห้าม:
- CALL ถ้า M15 bias = BEARISH
- PUT ถ้า M15 bias = BULLISH
- ข้าม M1 confirmation
- ใช้ M1 เป็นสัญญาณหลัก

ตอบได้แค่: CALL / PUT / NO_TRADE
=== END RULES ===
```
