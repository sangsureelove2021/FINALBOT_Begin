# SPEC: INDICATOR STORE — ห้องคำนวณและเก็บ Indicator

## หลักการ
```
คำนวณครั้งเดียว → เก็บใน IndicatorStore → ทุกคนมาดึงเอา → หมดรอบลบทิ้ง
```

---

## IndicatorStore คืออะไร
- คือ dict ที่เก็บค่า indicator ทุกตัวของทุก pair
- คำนวณ 1 ครั้งต่อรอบ (60s)
- ทุก module ดึงค่าจากที่นี่ที่เดียว
- ห้ามคำนวณ indicator ซ้ำในที่อื่น
- หมดรอบ → ล้างทิ้ง → คำนวณใหม่รอบหน้า

---

## Indicator ทั้งหมดในบอท

### TF M5
| Indicator | ค่าที่คำนวณ | ใช้ใน |
|-----------|------------|-------|
| EMA | EMA5, EMA10, EMA20, EMA50 | สภาวะตลาด, กลยุทธ์, AI |
| Bollinger Bands | BB_Upper, BB_Lower, BB_Width | สภาวะตลาด, กลยุทธ์, AI |
| RSI | RSI7, RSI14 | สภาวะตลาด, กลยุทธ์, AI |
| MACD | MACD, MACD_Signal, MACD_Hist | สภาวะตลาด, กลยุทธ์, AI |
| Stochastic | Stoch_K, Stoch_D | กลยุทธ์, AI |
| ATR | ATR14 | สภาวะตลาด, กลยุทธ์, AI |
| Pivot | Pivot, R1, R2, S1, S2 | กลยุทธ์, AI |
| S/R | Support, Resistance | สภาวะตลาด, กลยุทธ์, AI |

### TF M1
| Indicator | ค่าที่คำนวณ | ใช้ใน |
|-----------|------------|-------|
| EMA | EMA5, EMA10, EMA20, EMA50 | กลยุทธ์, AI |
| Bollinger Bands | BB_Upper, BB_Lower | กลยุทธ์, AI |
| RSI | RSI7, RSI14 | กลยุทธ์, AI |
| MACD | MACD, MACD_Signal | กลยุทธ์, AI |
| Stochastic | Stoch_K, Stoch_D | กลยุทธ์, AI |
| ATR | ATR14 | กลยุทธ์, AI |
| S/R | Support, Resistance | กลยุทธ์, AI |

### Price Action (คำนวณจาก M5 candles)
| ค่า | ใช้ใน |
|-----|-------|
| Pattern | สภาวะตลาด, กลยุทธ์, AI |
| Last_Candle | กลยุทธ์, AI |
| Body_Strength | กลยุทธ์, AI |
| Rejection_Zone | กลยุทธ์, AI |
| Wick_Dominance | กลยุทธ์, AI |
| Momentum_Bias | สภาวะตลาด, กลยุทธ์, AI |
| Move_Quality | กลยุทธ์, AI |
| Trap_Alert | กลยุทธ์, AI |
| SR_Interaction | กลยุทธ์, AI |

### Market State (คำนวณจาก indicator ข้างบน)
| ค่า | ใช้ใน |
|-----|-------|
| Market_State | กลยุทธ์, AI |
| Session | กลยุทธ์, AI |

---

## สิ่งที่แต่ละโหมดต้องการ

### AUTO_BOT โหมด (Rule-based Strategy)
```
ต้องการจาก IndicatorStore:
M5: EMA5, EMA10, EMA20, EMA50
    BB_Upper, BB_Lower, BB_Width
    RSI7, RSI14
    MACD, MACD_Signal, MACD_Hist
    Stoch_K, Stoch_D
    ATR14, Support, Resistance
    Pivot, R1, S1

M1: EMA5, EMA20
    RSI14
    MACD, MACD_Signal
    Support, Resistance

Price Action: Pattern, Momentum_Bias, Trap_Alert, SR_Interaction

Market State: Market_State
```

### AI_BOT โหมด (ส่ง JSON ให้ AI)
```
ต้องการจาก IndicatorStore:
ทุกค่าเดียวกับ AUTO_BOT +
M5: Stoch_K, Stoch_D, Pivot, R1, R2, S1, S2
M1: Stoch_K, Stoch_D, BB_Upper, BB_Lower, ATR14
Price Action: ทุกค่า
Market State: Market_State, Session
```

---

## โครงสร้าง IndicatorStore

```python
IndicatorStore = {
    'EURUSD-OTC': {
        'expires_at': datetime,   # หมดอายุเมื่อไหร่
        'm5': {
            'ema5': 1.10550,
            'ema10': 1.10565,
            'ema20': 1.10580,
            'ema50': 1.10620,
            'bb_upper': 1.10650,
            'bb_lower': 1.10510,
            'bb_width': 0.00140,
            'rsi7': 32.5,
            'rsi14': 41.2,
            'macd': -0.00015,
            'macd_signal': -0.00010,
            'macd_hist': -0.00005,
            'stoch_k': 22.4,
            'stoch_d': 35.1,
            'atr14': 0.00080,
            'support': 1.10520,
            'resistance': 1.10680,
            'pivot': 1.10600,
            'r1': 1.10640,
            'r2': 1.10720,
            's1': 1.10560,
            's2': 1.10480,
        },
        'm1': {
            'ema5': 1.10530,
            'ema10': 1.10545,
            'ema20': 1.10555,
            'ema50': 1.10570,
            'bb_upper': 1.10580,
            'bb_lower': 1.10510,
            'rsi7': 45.6,
            'rsi14': 42.1,
            'macd': -0.00005,
            'macd_signal': -0.00008,
            'stoch_k': 55.2,
            'stoch_d': 45.8,
            'atr14': 0.00030,
            'support': 1.10520,
            'resistance': 1.10680,
        },
        'price_action': {
            'pattern': 'BEARISH_ENGULFING',
            'last_candle': 'BEARISH',
            'body_strength': 'STRONG',
            'rejection_zone': 'NEAR_SUPPORT',
            'wick_dominance': 'LOW_WICK',
            'momentum_bias': 'BEARISH',
            'move_quality': 'CLEAN_TRENDING',
            'trap_alert': 'NONE',
            'sr_interaction': 'BREAKING_BELOW_SUPPORT',
        },
        'market_state': 'DOWNTREND',
        'session': 'asian',
        'current_price': 1.10540,
        'timestamp': '2026-06-21T05:55:00+00:00',
    },
    'GBPUSD-OTC': { ... },
    'USDJPY-OTC': { ... },
    'AUDUSD-OTC': { ... },
    'NZDUSD-OTC': { ... },
}
```

---

## Flow การทำงาน 1 รอบ

```
START
  ↓
[1] ดึง Candles M1+M5 ทุก pair (parallel)
  ↓
[2] คำนวณ Indicators ทุกตัว ทุก pair (parallel)
    → เก็บใน IndicatorStore ทันที
  ↓
[3] คำนวณ Price Action + Market State
    → อ่านจาก IndicatorStore
    → เขียนลง IndicatorStore
  ↓
[4] IndicatorStore พร้อมใช้งาน
  ↓
    ┌─────────────────────┐
    ↓                     ↓
[AUTO_BOT]           [AI_BOT]
ดึงค่าจาก Store     สร้าง JSON จาก Store
→ Rule logic        → ส่งให้ AI
→ Signal            → Signal
    ↓                     ↓
    └─────────────────────┘
  ↓
[5] execution_gate → CALL / PUT / NO_SIGNAL
  ↓
[6] หมดรอบ → ล้าง IndicatorStore
END
```

---

## กฎ (ห้ามละเมิด)

```
✅ คำนวณ indicator ใน STEP 2 เท่านั้น
✅ ทุก module ดึงค่าจาก IndicatorStore เท่านั้น
✅ AUTO_BOT และ AI_BOT ใช้ค่าเดียวกันจาก Store
✅ หมดรอบต้องล้าง Store ทุกครั้ง
✅ IndicatorStore เป็น read-only หลัง STEP 3

❌ ห้าม module ใดคำนวณ EMA/RSI/ATR เอง
❌ ห้าม AI_BOT ดึง candle เอง
❌ ห้าม AUTO_BOT คำนวณ indicator ซ้ำ
❌ ห้ามใช้ค่าจาก Store ที่หมดอายุแล้ว
```
