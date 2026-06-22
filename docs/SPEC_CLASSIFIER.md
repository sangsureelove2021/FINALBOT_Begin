# SPEC: MARKET STATE CLASSIFIER

## ภาพรวม
รับ output จาก Tier 1 ทั้ง 5 engines → จำแนกตลาดเป็น 10 ประเภท

**File:** `core/engines/market_state_classifier.py`  
**Depends on:** trend, strength, volatility, structure, mtf (ทุกตัว)

---

## Input Schema
```python
inputs = {
    'trend': TrendOutput,       # จาก trend_engine
    'strength': StrengthOutput, # จาก strength_engine
    'volatility': VolatilityOutput, # จาก volatility_engine
    'structure': StructureOutput,   # จาก structure_engine
    'mtf': MTFOutput            # จาก mtf_intelligence
}
```

---

## Output Schema
```python
{
    'state': str,               # 1 ใน 10 states ด้านล่าง
    'state_confidence': int,    # 0-100
    'duration': int,            # ประมาณ candles ที่อยู่ใน state นี้
    'stability': int,           # 0-100 (state จะเปลี่ยนเร็วไหม)
    'regime_quality': int,      # 0-100 (คุณภาพรวม)
    'likelihood_next_state': {  # probability ของ state ถัดไป
        'TRENDING_STRONG': int,
        'TRENDING_WEAK': int,
        'SIDEWAY_RANGE': int,
        'BREAKOUT_EMERGING': int,
        'REVERSAL_FORMING': int,
        'ACCUMULATION': int,
        'DISTRIBUTION': int,
        'CHOPPY_UNCERTAIN': int,
        'LIQUIDITY_VOID': int,
        'UNCLEAR': int
    },
    'composite_score': {
        'trend_score': int,     # 0-100
        'strength_score': int,  # 0-100
        'volatility_score': int,# 0-100
        'structure_score': int  # 0-100
    }
}
```

---

## 10 Market States — เงื่อนไขจำแนก

### 1. TRENDING_STRONG
ตลาดเทรนด์ชัดเจน แรง ต่อเนื่อง
```
เงื่อนไข (ต้องผ่านทุกข้อ):
- trend.direction IN ['UP', 'DOWN']
- trend.strength >= 60
- trend.type == 'IMPULSIVE'
- strength.adx >= 25
- strength.momentum_level IN ['STRONG', 'EXTREME']
- mtf.harmony IN ['PERFECT', 'GOOD']
- volatility.regime IN ['NORMAL', 'HIGH']
- structure.structure_type == 'TRENDING'
```

### 2. TRENDING_WEAK
ตลาดเทรนด์อยู่แต่แรงน้อย หรือเริ่มอ่อนแรง
```
เงื่อนไข:
- trend.direction IN ['UP', 'DOWN']
- trend.strength BETWEEN 30-59
- strength.adx BETWEEN 15-24
- strength.momentum_level IN ['WEAK', 'NORMAL']
- mtf.harmony IN ['GOOD', 'MIXED']
- ไม่ผ่านเงื่อนไข TRENDING_STRONG
```

### 3. SIDEWAY_RANGE
ตลาดเคลื่อนที่ในกรอบ S/R ชัดเจน
```
เงื่อนไข:
- trend.direction == 'NONE' หรือ trend.strength < 30
- strength.adx < 20
- structure.structure_type == 'RANGING'
- volatility.regime IN ['LOW', 'NORMAL']
- structure.support_levels มีอย่างน้อย 1 level
- structure.resistance_levels มีอย่างน้อย 1 level
- mtf.harmony IN ['MIXED', 'CONFLICTING']
```

### 4. BREAKOUT_EMERGING
ตลาดกำลังจะ breakout หรือ breakout ใหม่ๆ
```
เงื่อนไข:
- structure.bos_detected == True หรือ structure.breakout_probability >= 65
- volatility.bbw_ratio < 0.6 (compression ก่อน) หรือ regime เพิ่งเปลี่ยนเป็น HIGH
- strength.momentum_level IN ['STRONG', 'EXTREME']
- volatility.expansion_probability >= 60
- trend.type == 'IMPULSIVE' (breakout candle)
```

### 5. REVERSAL_FORMING
ตลาดกำลังกลับทิศ สัญญาณอ่อนแรง
```
เงื่อนไข:
- trend.reversal_risk >= 65
- strength.divergence IN ['BULLISH', 'BEARISH']
- strength.exhaustion_risk >= 60
- structure.reversal_probability >= 55
- trend.sustain_probability < 40
- หรือ structure.choch_detected == True
```

### 6. ACCUMULATION
ตลาดนิ่ง smart money สะสม ก่อน breakout ขาขึ้น
```
เงื่อนไข:
- volatility.regime == 'LOW'
- volatility.atr_percentile < 30
- strength.adx < 20
- trend.direction == 'NONE'
- structure.structure_type == 'RANGING'
- volatility.bbw_ratio < 0.5 (tight compression)
- ราคาอยู่ใกล้ strong_support (zone_proximity IN ['NEAR', 'AT_LEVEL'])
```

### 7. DISTRIBUTION
ตลาดนิ่ง smart money ปล่อยของ ก่อน breakout ขาลง
```
เงื่อนไข:
- เหมือน ACCUMULATION แต่:
- ราคาอยู่ใกล้ strong_resistance (zone_proximity IN ['NEAR', 'AT_LEVEL'])
- trend.direction == 'NONE' หรือ 'DOWN' อ่อนๆ
```

### 8. CHOPPY_UNCERTAIN
ตลาด noise สูง สัญญาณขัดแย้ง
```
เงื่อนไข (ข้อใดข้อหนึ่ง):
- mtf.harmony == 'CONFLICTING'
- trend.type == 'CHOPPY' และ strength.adx < 15
- volatility.spike_detected == True และ trend.direction == 'NONE'
- composite_score ทุกตัว < 40 (ไม่มีตัวใดชัดเจน)
```

### 9. LIQUIDITY_VOID
ตลาดบางเกินไป spread สูง หรือ candle ผิดปกติ
```
เงื่อนไข:
- volatility.atr < threshold_minimum (ต่ำผิดปกติ)
- candle body ขนาดเล็กมาก ติดต่อกัน > 10 candles
- หรือเป็นช่วง weekend/holiday gap
- ใช้เป็น safety filter
```

### 10. UNCLEAR
ข้อมูลไม่พอ หรือสัญญาณขัดแย้งรุนแรง → default NO_SIGNAL
```
เงื่อนไข (ข้อใดข้อหนึ่ง):
- engine ใดๆ return error หรือ confidence < 30
- ไม่ผ่านเงื่อนไขของ state ใดเลย
- state_confidence < 40 หลัง scoring
- mtf.harmony == 'CONFLICTING' และ trend ไม่ชัด
```

---

## Classification Logic (Priority Order)

```python
def classify(self, inputs) -> dict:
    # ลำดับความสำคัญในการตรวจสอบ
    
    # 1. Safety checks ก่อน
    if self._is_unclear(inputs):
        return state('UNCLEAR')
    
    if self._is_liquidity_void(inputs):
        return state('LIQUIDITY_VOID')
    
    if self._is_choppy(inputs):
        return state('CHOPPY_UNCERTAIN')
    
    # 2. Active states
    if self._is_breakout_emerging(inputs):
        return state('BREAKOUT_EMERGING')
    
    if self._is_reversal_forming(inputs):
        return state('REVERSAL_FORMING')
    
    if self._is_trending_strong(inputs):
        return state('TRENDING_STRONG')
    
    if self._is_trending_weak(inputs):
        return state('TRENDING_WEAK')
    
    # 3. Range states
    if self._is_distribution(inputs):
        return state('DISTRIBUTION')
    
    if self._is_accumulation(inputs):
        return state('ACCUMULATION')
    
    if self._is_sideway_range(inputs):
        return state('SIDEWAY_RANGE')
    
    # 4. Default
    return state('UNCLEAR')
```

---

## Composite Score Calculation

```python
# ใช้คำนวณ state_confidence
trend_score    = (trend.strength × 0.3) + (trend.confidence × 0.7)
strength_score = (strength.adx / 100 × 50) + (strength.strength_score × 0.5)
volatility_score = volatility.volatility_score
structure_score  = structure.structure_score

# weighted composite
composite = (
    trend_score    × 0.35 +
    strength_score × 0.30 +
    volatility_score × 0.20 +
    structure_score  × 0.15
)

state_confidence = int(composite × mtf_multiplier)
# mtf_multiplier: PERFECT=1.0, GOOD=0.9, MIXED=0.75, CONFLICTING=0.5
```

---

## Regime Quality Scorer (คู่กัน)

**File:** `core/engines/regime_quality_scorer.py`

```python
# Output
{
    'overall_score': int,     # 0-100
    'noise_level': int,       # 0-100 (สูง = noise เยอะ)
    'stability': int,         # 0-100
    'tradeable': bool,
    'recommendation': 'TRADE' | 'CAUTIOUS' | 'AVOID'
}

# Logic
if overall_score >= 65: recommendation = 'TRADE'
elif overall_score >= 45: recommendation = 'CAUTIOUS'
else: recommendation = 'AVOID'

# tradeable = True เฉพาะเมื่อ
# state NOT IN ['UNCLEAR', 'CHOPPY_UNCERTAIN', 'LIQUIDITY_VOID']
# AND overall_score >= 50
```

---

## Strategy Mapping (ต่อจาก Classifier)

| State | Strategy ที่ activate |
|-------|----------------------|
| TRENDING_STRONG | EMA Pullback Continuation |
| TRENDING_WEAK | EMA Pullback (conservative) |
| BREAKOUT_EMERGING | **5M Compression Breakout** ⭐ V1 |
| SIDEWAY_RANGE | Range Reversal |
| REVERSAL_FORMING | Exhaustion Reversal |
| ACCUMULATION | รอ BREAKOUT_EMERGING |
| DISTRIBUTION | รอ BREAKOUT_EMERGING |
| CHOPPY_UNCERTAIN | NO_SIGNAL |
| LIQUIDITY_VOID | NO_SIGNAL |
| UNCLEAR | NO_SIGNAL |
