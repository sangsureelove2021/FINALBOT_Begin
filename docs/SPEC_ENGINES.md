# SPEC: TIER 1 ENGINES (Input → Output)

## ภาพรวม
5 engines ทำงาน parallel จาก OHLCV candle data
Output รวมกันส่งต่อให้ Market State Classifier

---

## 1. trend_engine.py
**Input:** Candles M1, M5, M15, M60  
**Indicators:** EMA20, EMA50, EMA100, EMA200, HH/HL/LH/LL, Linear Regression Slope

**Output:**
```python
{
    'direction': 'UP' | 'DOWN' | 'NONE',
    'strength': int,          # 0-100
    'slope': float,           # linear regression slope
    'momentum': float,
    'type': 'IMPULSIVE' | 'CORRECTIVE' | 'CHOPPY',
    'confidence': int,        # 0-100
    'reversal_risk': int,     # 0-100
    'sustain_probability': int  # 0-100
}
```

**Logic สำคัญ:**
- UP: price > EMA20 > EMA50 > EMA100 (fan up)
- DOWN: price < EMA20 < EMA50 < EMA100 (fan down)
- NONE: EMAs entangled หรือ conflicting
- IMPULSIVE: body ใหญ่, slope ชัน, efficiency สูง
- CORRECTIVE: pullback, zig-zag, slope อ่อน
- CHOPPY: ไม่มีทิศ, noise สูง

---

## 2. strength_engine.py
**Input:** Candles M5  
**Indicators:** ADX(14), DI+(14), DI-(14), RSI(14), MACD(12,26,9), ROC(10)

**Output:**
```python
{
    'adx': float,             # 0-100
    'di_plus': float,         # 0-100
    'di_minus': float,        # 0-100
    'rsi': float,             # 0-100
    'macd': float,
    'macd_signal': float,
    'macd_hist': float,
    'momentum_level': 'WEAK' | 'NORMAL' | 'STRONG' | 'EXTREME',
    'roc': float,
    'divergence': 'BULLISH' | 'BEARISH' | 'NONE',
    'strength_score': int,    # 0-100 (composite)
    'exhaustion_risk': int    # 0-100
}
```

**Logic สำคัญ:**
- ADX < 20 → WEAK
- ADX 20-25 → NORMAL
- ADX 25-40 → STRONG
- ADX > 40 → EXTREME
- exhaustion_risk สูงเมื่อ RSI > 75 หรือ < 25 + MACD diverge

---

## 3. volatility_engine.py
**Input:** Candles M5  
**Indicators:** ATR(14), Bollinger Bands(20,2), StdDev(20), Historical ATR percentile

**Output:**
```python
{
    'atr': float,
    'atr_percentile': int,    # 0-100 vs 100-candle history
    'bbw': float,             # Bollinger Band Width
    'bbw_ratio': float,       # current BBW / avg BBW (50 candles)
    'stddev': float,
    'regime': 'LOW' | 'NORMAL' | 'HIGH' | 'EXTREME',
    'volatility_score': int,  # 0-100
    'expansion_probability': int,   # 0-100
    'contraction_probability': int, # 0-100
    'volatility_zscore': float,
    'spike_detected': bool
}
```

**Logic สำคัญ:**
- regime LOW: atr_percentile < 25
- regime NORMAL: 25-75
- regime HIGH: 75-90
- regime EXTREME: > 90
- spike_detected: ATR > 2x avg ATR (14 candles)
- bbw_ratio < 0.5 → compression สูง (breakout risk)

---

## 4. structure_engine.py
**Input:** Candles M15  
**Indicators:** Swing High/Low, Pivot Points, Fractals, BOS logic

**Output:**
```python
{
    'support_levels': [float, ...],   # ระดับแนวรับ (max 3)
    'resistance_levels': [float, ...], # ระดับแนวต้าน (max 3)
    'structure_type': 'TRENDING' | 'RANGING' | 'BREAKOUT',
    'structure_score': int,   # 0-100
    'bos_detected': bool,     # Break of Structure
    'bos_type': 'BULLISH' | 'BEARISH' | 'NONE',
    'choch_detected': bool,   # Change of Character
    'key_zones': {
        'strong_support': float,
        'strong_resistance': float,
        'middle': float
    },
    'zone_proximity': 'FAR' | 'MEDIUM' | 'NEAR' | 'AT_LEVEL',
    'breakout_probability': int,  # 0-100
    'reversal_probability': int   # 0-100
}
```

**Logic สำคัญ:**
- BOS: price breaks last swing high (bullish) หรือ swing low (bearish)
- CHOCH: สัญญาณเปลี่ยน bias (HH→LH หรือ LL→HL)
- RANGING: price bounces between clear S/R
- NEAR: price ภายใน 0.2% ของ level

---

## 5. mtf_intelligence.py
**Input:** Candles M1, M5, M15, M60, D1 (ส่ง trend_engine ให้แต่ละ TF)  
**Indicators:** ใช้ผล trend_engine ซ้ำในแต่ละ TF

**Output:**
```python
{
    'timeframes': {
        'M1':  {'direction': str, 'strength': int, 'confidence': int},
        'M5':  {'direction': str, 'strength': int, 'confidence': int},
        'M15': {'direction': str, 'strength': int, 'confidence': int},
        'M60': {'direction': str, 'strength': int, 'confidence': int},
        'D1':  {'direction': str, 'strength': int, 'confidence': int},
    },
    'alignment_score': int,   # 0-100 (กี่ TF เห็นตรงกัน)
    'harmony': 'PERFECT' | 'GOOD' | 'MIXED' | 'CONFLICTING',
    'direction_consensus': 'STRONG_UP' | 'STRONG_DOWN' | 'WEAK_UP' | 'WEAK_DOWN' | 'NONE',
    'htf_direction': 'UP' | 'DOWN' | 'NONE',   # M60+D1
    'ltf_direction': 'UP' | 'DOWN' | 'NONE',   # M1+M5
    'htf_ltf_conflict': bool,
    'confidence_from_mtf': int  # 0-100
}
```

**Logic สำคัญ:**
- alignment_score: (TF ที่เห็นด้วย / 5) × 100
- PERFECT: 5/5 TF ตรงกัน
- GOOD: 4/5
- MIXED: 3/5
- CONFLICTING: ≤ 2/5
- htf_direction ใช้ M60+D1 majority vote
- htf_ltf_conflict = True เมื่อ htf ≠ ltf direction

---

## Data Contract
Engine ทั้งหมดรับ DataFrame format:
```python
# columns: open, high, low, close, volume
# index: datetime (UTC)
# ต้องมีขั้นต่ำ 200 candles
candles_df: pd.DataFrame
```

ทุก engine ต้อง handle error และ return neutral state:
```python
def _neutral_state(self) -> dict:
    # return safe default ไม่ crash pipeline
```
