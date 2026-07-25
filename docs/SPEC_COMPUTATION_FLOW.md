# SPEC: COMPUTATION FLOW — คำนวณครั้งเดียว ใช้ได้ทั้ง AI และ Strategy

## หลักการ
คำนวณ indicator **ครั้งเดียวต่อ 1 รอบต่อ 1 pair**
ผลลัพธ์เก็บเป็น JSON snapshot แชร์ให้ทั้ง AI path และ Strategy path

---

## ภาพรวม (1 รอบ = 60s)

```
[STEP 1] ดึง Candles (ครั้งเดียว)
              ↓
[STEP 2] คำนวณ Indicators (ครั้งเดียวต่อ pair)
              ↓
[STEP 3] สร้าง Market Payload JSON (1 ชุดต่อ pair)
              ↓
         ┌────────────┐
         ↓            ↓
    [AI PATH]   [STRATEGY PATH]
    ส่ง JSON    อ่าน JSON เดียวกัน
    → DeepSeek  → Rule-based logic
         ↓            ↓
         └────────────┘
              ↓
    [STEP 4] รวม Signal → execution_gate
              ↓
         CALL / PUT / NO_SIGNAL
```

---

## STEP 1: ดึง Candles
**คำนวณกี่ครั้ง:** 1 ครั้งต่อ pair ต่อรอบ

```python
# ดึงพร้อมกัน parallel ทุก pair
candles = {
    'EURUSD-OTC': {
        'M1': DataFrame(200 candles),
        'M5': DataFrame(200 candles),
    },
    'GBPUSD-OTC': { ... },
    ...
}
```

---

## STEP 2: คำนวณ Indicators
**คำนวณกี่ครั้ง:** 1 ครั้งต่อ pair (ไม่ซ้ำ ไม่คำนวณใหม่ใน engine)

### สิ่งที่คำนวณ (ต่อ pair):

**TF M5:**
```
EMA5, EMA10, EMA20, EMA50
BB Upper, BB Lower, BB Width
RSI7, RSI14
MACD, MACD Signal, MACD Histogram
Stoch K, Stoch D
ATR14
Pivot, R1, R2, S1, S2
Support, Resistance
```

**TF M1:**
```
EMA5, EMA10, EMA20, EMA50
BB Upper, BB Lower
RSI7, RSI14
MACD, MACD Signal
Stoch K, Stoch D
ATR14
Support, Resistance
```

**Price Action (จาก M5 candles ล่าสุด):**
```
pattern (BULLISH_ENGULFING, BEARISH_ENGULFING, DOJI, ...)
last_candle (BULLISH/BEARISH)
body_strength (STRONG/MEDIUM/WEAK)
rejection_zone
wick_dominance
momentum_bias
move_quality
trap_alert
sr_interaction
```

**Market State (จาก indicators ที่คำนวณแล้ว):**
```
UPTREND / DOWNTREND / SIDEWAY / BREAKOUT / REVERSAL / UNCLEAR
```

---

## STEP 3: สร้าง Market Payload JSON
**สร้างกี่ครั้ง:** 1 ครั้งต่อ pair — ใช้ร่วมกันทั้ง AI และ Strategy

```json
{
  "timestamp": "2026-06-21T05:55:00+00:00",
  "symbol": "EURUSD-OTC",
  "current_price": 1.10540,
  "session": "asian",
  "timeframe": "m5",
  "market_state": "DOWNTREND",
  "m5": {
    "ema5": 1.10550,
    "ema10": 1.10565,
    "ema20": 1.10580,
    "ema50": 1.10620,
    "bb_upper": 1.10650,
    "bb_lower": 1.10510,
    "rsi7": 32.5,
    "rsi14": 41.2,
    "macd": -0.00015,
    "macd_signal": -0.00010,
    "stoch_k": 22.4,
    "stoch_d": 35.1,
    "support": 1.10520,
    "resistance": 1.10680,
    "pivot": 1.10600,
    "r1": 1.10640,
    "s1": 1.10560,
    "atr": 0.00080
  },
  "m1": {
    "ema5": 1.10530,
    "ema10": 1.10545,
    "ema20": 1.10555,
    "ema50": 1.10570,
    "bb_upper": 1.10580,
    "bb_lower": 1.10510,
    "rsi7": 45.6,
    "rsi14": 42.1,
    "macd": -0.00005,
    "macd_signal": -0.00008,
    "stoch_k": 55.2,
    "stoch_d": 45.8,
    "support": 1.10520,
    "resistance": 1.10680,
    "pivot": 1.10600,
    "r1": 1.10640,
    "s1": 1.10560,
    "atr": 0.00030
  },
  "price_action": {
    "pattern": "BEARISH_ENGULFING",
    "last_candle": "BEARISH",
    "body_strength": "STRONG",
    "rejection_zone": "NEAR_SUPPORT",
    "wick_dominance": "LOW_WICK",
    "momentum_bias": "BEARISH",
    "move_quality": "CLEAN_TRENDING",
    "trap_alert": "NONE",
    "sr_interaction": "BREAKING_BELOW_SUPPORT"
  },
  "triggered_signals": [],
  "signal_count": 0
}
```

---

## STEP 4: แยก Path (ใช้ JSON เดียวกัน)

### AI PATH
```python
# ส่ง payload JSON ให้ AI โดยตรง
prompt = build_prompt(payload)
response = ai_client.ask(prompt)
signal = parse_signal(response)  # CALL / PUT / NO_TRADE
```

### STRATEGY PATH
```python
# อ่านค่าจาก payload โดยตรง ไม่คำนวณใหม่
def analyze(payload):
    rsi = payload['m5']['rsi14']
    macd = payload['m5']['macd']
    market_state = payload['market_state']
    pattern = payload['price_action']['pattern']
    # → rule-based logic → CALL / PUT / NO_SIGNAL
```

---

## กฎสำคัญ (ห้ามละเมิด)

```
✅ คำนวณ indicator 1 ครั้งต่อ pair ต่อรอบ
✅ JSON payload สร้าง 1 ชุดต่อ pair
✅ AI และ Strategy อ่าน JSON ชุดเดียวกัน
✅ ไม่มี engine ใดคำนวณ indicator เอง
✅ ไม่มีการคำนวณซ้ำในขั้นตอนใดๆ

❌ ห้าม AI หรือ Strategy ดึง candle เอง
❌ ห้ามคำนวณ EMA/RSI/ATR ซ้ำในหลายที่
❌ ห้าม modify payload หลังสร้างแล้ว (immutable)
```

---

## สรุป: คำนวณกี่ครั้ง

| ขั้นตอน | จำนวนครั้ง |
|---------|-----------|
| ดึง Candles | 1 ครั้ง/pair/รอบ |
| คำนวณ Indicators | 1 ครั้ง/pair/รอบ |
| สร้าง JSON Payload | 1 ครั้ง/pair/รอบ |
| AI อ่าน Payload | 1 ครั้ง/pair/รอบ |
| Strategy อ่าน Payload | 1 ครั้ง/pair/รอบ |
| **รวมทั้งหมด (5 pairs)** | **5 ครั้ง/รอบ** |
