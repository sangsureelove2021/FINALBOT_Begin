# Market State Classification Blueprint v5.0.0

**Module**: `core/engines/market_state_classifier.py`  
**Class**: `MarketStateClassifier`  
**Tier**: 2 (Core Analysis Layer)  
**Version**: 5.0.0 – Optimized for 5-minute Binary Options  
**Last Updated**: 2026-06-14  
**Lines of Code**: 845  

---

## 1. Overview

The Market State Classifier is the central engine for understanding current market conditions. It ingests OHLCV data and optional precomputed intelligence from Tier 1 engines (Trend, Strength, Volatility, Structure, MTF) and outputs one of **10 distinct market states** along with confidence, quality, tradeability, and stability scores.

### 1.1 Key Optimizations for 5-Minute Trading
- **Reduced indicator periods** – faster response (ADX period = 10, RSI period = 7, EMA spans = 5 & 10).
- **Adaptive thresholds** – ADX threshold changes based on recent volatility (18–28).
- **Momentum divergence detection** – early reversal signals using price/RSI divergence.
- **Volume-confirmed breakouts** – volume surge (>1.5x) boosts breakout probability.
- **State transition smoothing** – requires 3 of last 5 classifications to be the same before changing.
- **Dynamic noise filtering** – weighted efficiency (net move / total weighted move).

---

## 2. Architecture & Dependencies

### 2.1 Class Hierarchy
```
BaseEngine (abstract)
    └── MarketStateClassifier
```

### 2.2 Core Dependencies
- `numpy` – array operations
- `pandas` – rolling calculations, EMAs, ATR, BBW
- `collections.deque` – state history buffer
- `core.engines.base_engine.BaseEngine`

### 2.3 Input Data
- **Primary**: `candles_df` – OHLCV DataFrame with columns: 'open', 'high', 'low', 'close', 'volume'
- **Optional Tier 1 Engine outputs** (passed via `**kwargs`):
  - `trend_data` – from TrendIntelligenceEngine
  - `strength_data` – from StrengthIntelligenceEngine  
  - `volatility_data` – from VolatilityIntelligenceEngine
  - `structure_data` – from StructureIntelligenceEngine
  - `mtf_data` – from MTFIntelligenceEngine

### 2.4 Output Format
```python
{
    'state': str,               # One of 10 market states
    'confidence': int,          # 0-100, raw classification confidence
    'quality_score': int,       # 0-100, tradeability quality (adjusted)
    'tradeable': bool,          # Suitable for strategy entry?
    'stability': int,           # 0-100, market stability
    'description': str,         # Human-readable explanation
    'metrics': dict             # Raw metrics used for classification
}
```

---

## 3. Core Constants & Configuration

| Constant | Value | Description |
|----------|-------|-------------|
| `ENGINE_NAME` | `"market_state_classifier"` | Unique engine identifier |
| `ENGINE_VERSION` | `"5.0.0"` | Version for binary options |
| `TIER` | `2` | Execution order tier |
| `MIN_CANDLES` | `50` | Minimum candles required (reduced from 100) |
| `_max_history` | `5` | State history buffer size for smoothing |
| `VALID_STATES` | List of 10 states | Used for validation |

---

## 4. Mathematical Formulae & Calculation Logic

### 4.1 Trend Metrics (Optimized for 5-min)
- **EMAs**: `EMA5` (25 min) and `EMA10` (50 min) using `ewm(span=5, adjust=False)` and `span=10`.
- **Slope**: `(EMA5 - EMA10) / (EMA10 + 1e-9)`
- **Direction**: Determined by comparing recent highs/lows and EMA crossover.

### 4.2 Strength Metrics (Faster ADX & RSI)
- **ADX period**: `10` (standard Wilder smoothing, but with shorter lookback).
  - Formula: `TR = max(H-L, |H - C_prev|, |L - C_prev|)`
  - Wilder smoothing: `smoothed[i] = (smoothed[i-1]*(per-1) + value[i]) / per`
  - `+DI` = `100 * smoothed_pos_dm / smoothed_tr`
  - `-DI` = `100 * smoothed_neg_dm / smoothed_tr`
  - `DX` = `100 * |+DI - -DI| / (+DI + -DI)`
  - `ADX` = Wilder smooth of `DX` over `period`
- **RSI period**: `7` (standard RSI: average gain / average loss over 7 periods).
- **Momentum Level**: `'STRONG'` if RSI > 65 or < 35, else `'NORMAL'`.
- **Strength Score**: `0-100` based on ADX and RSI extremes.

### 4.3 Volatility Metrics
- **ATR period**: `10`
  - `ATR` = rolling mean of True Range over 10 periods.
  - `atr_percentile` = `(current_atr / avg_atr_last_40) * 100`
- **Bollinger Band Width (BBW) period**: `14`
  - `BBW` = `(Upper_Band - Lower_Band) / Middle_Band`
  - Upper = MA14 + 2*StdDev14, Lower = MA14 - 2*StdDev14
- **Volatility Regime**:
  - `EXTREME` if `atr_percentile > 150`
  - `HIGH` if `> 110`
  - `NORMAL` if `> 80`
  - `LOW` otherwise

### 4.4 Noise Level (Weighted Efficiency)
```python
total_move_weighted = sum(|close[i] - close[i-1]| * weight[i])
weight[i] = min(1.0, (i - n + lookback) / lookback)  # recent candles get higher weight
net_move = abs(close[-1] - close[-n])
efficiency = net_move / (total_move_weighted + 1e-9)
noise = max(0, min(1, 1 - efficiency))

# Adjust noise downward if last candle body is large
if candle_body_ratio > 0.3:
    noise = max(0, noise - 0.15)
```

### 4.5 Volume Metrics
- **Volume Ratio**: `current_volume / average_volume_last_20`
- **Volume Surge**: `volume_ratio > 1.5`

### 4.6 Wick Pattern Detection (Accumulation/Distribution)
For each of last 15 candles:
- **Lower wick ratio** (bullish candle): `(open - low) / (high - low)`
- **Upper wick ratio** (bullish candle): `(high - close) / (high - low)`
- Count if lower ratio > 0.4 → accumulation signal
- Count if upper ratio > 0.5 → distribution signal
- Final ratios: `lower_wick_count / 15`, `upper_wick_count / 15`

### 4.7 Volatility Compression Detection
- **BBW trend**: recent BBW decreased by >15% over last 7 candles
- **Low BBW**: `bbw < 0.06`
- **Low ATR**: `atr_percentile < 75`
- **Range narrowing**: `(max_high_5 - min_low_5) / close[-1] < 0.005`
- Returns `True` if any of: `(bbw_trend and low_bbw)` OR `(low_bbw and low_atr)` OR `range_narrowing`

### 4.8 Momentum Divergence (Simplified)
- **Bullish divergence**: `RSI < 35` AND `close[-1] > min(close[-5:])`
- **Bearish divergence**: `RSI > 65` AND `close[-1] < max(close[-5:])`
- Returns `True` if either condition met.

### 4.9 Breakout & Reversal Probabilities

**Breakout Probability (0-100)**:
- Base: 30
- +30 if `bbw < 0.05`
- +15 if `0.05 <= bbw < 0.08`
- +15 if `atr_percentile < 70`
- +10 if `adx > 22`
- +15 if `price_range_5 < 0.003` (very tight range)

**Reversal Probability (0-100)**:
- Base: 30
- +20 if momentum loss: `abs(close[-1]-close[-4]) < 0.5 * abs(close[-3]-close[-6])`
- +15 if price near recent high/low and RSI extreme (approximated)
- +15 if reversal pattern detected (2-bar reversal logic)
- Capt at 100.

---

## 5. State Classification Logic

### 5.1 Decision Tree Order (Priority from highest to lowest)

#### 1. **LIQUIDITY_VOID**
- **Conditions**:
  - `volume_ratio < 0.2` OR
  - (`adx < 10` AND `volume_ratio < 0.5`)
- **Confidence**: 85
- **Tradeable**: No
- **Description**: Extremely low volume / dead market.

#### 2. **CHOPPY_UNCERTAIN**
- **Conditions**:
  - `noise_level > 0.65` AND `adx < adaptive_adx_threshold`
- **Confidence**: 80
- **Tradeable**: No
- **Quality Score Base**: 25
- **Description**: Chaotic movement, high noise, avoid trading.

#### 3. **TRENDING_STRONG**
- **Conditions**:
  - `adx > adaptive_adx_threshold + 10`
  - `trend_strength > 55`
  - `noise_level < 0.55`
- **Confidence**: `min(90, adx + trend_strength/2)`
- **Tradeable**: Yes (requires quality >= 60)
- **Quality Score Base**: 85
- **Description**: Strong directional move with high momentum.

#### 4. **TRENDING_WEAK**
- **Conditions**:
  - `adx > adaptive_adx_threshold - 5`
  - `trend_direction != 'NONE'`
  - `trend_strength < 55`
- **Confidence**: 65
- **Tradeable**: Conditional (quality >= 65)
- **Quality Score Base**: 65
- **Description**: Directional bias but low conviction.

#### 5. **BREAKOUT_EMERGING**
- **Conditions** (any of):
  - `compression_detected` AND `breakout_prob > 45`
  - (`bbw < 0.06` AND `volatility_regime == 'LOW'` AND `breakout_prob > 35`)
  - `volume_surge` AND `breakout_prob > 40`
- **Confidence**: `min(85, breakout_prob + 20 + (15 if volume_surge else 0))`
- **Tradeable**: Yes (quality >= 55)
- **Quality Score Base**: 80
- **Description**: Volatility expanding after compression, potential explosive move.

#### 6. **REVERSAL_FORMING**
- **Conditions** (any of):
  - `reversal_prob > 50` AND `adx < 45`
  - (`rsi_extreme_bull` OR `rsi_extreme_bear`) AND `trend_strength < 45`
  - `divergence_detected` AND `adx < 40`
- **Confidence**: `min(80, reversal_prob + (15 if divergence_detected else 0))`
- **Tradeable**: Conditional (quality >= 65)
- **Quality Score Base**: 60
- **Description**: Early signs of trend change, wait for confirmation.
- **Note**: Uses fixed ADX thresholds (45,40) rather than adaptive for faster reversal detection in 5-min trading.

#### 7. **ACCUMULATION**
- **Conditions** (all must be true):
  - `volume_ratio > 1.1`
  - `trend_direction == 'UP'`
  - `trend_strength < 55`
  - `35 < rsi < 65`
  - `wick_lower_ratio > 0.45`
- **Confidence**: `min(95, max(50, 50 + min(30, (volume_ratio-1.1)*30) + min(20, wick_lower_ratio*25)))`
- **Tradeable**: Yes (quality >= 55)
- **Quality Score Base**: 75
- **Description**: Smart money accumulating, bullish bias.

#### 8. **DISTRIBUTION**
- **Conditions** (all must be true):
  - `volume_ratio > 1.1`
  - `trend_direction == 'DOWN'`
  - `trend_strength < 55`
  - `35 < rsi < 65`
  - `wick_upper_ratio > 0.45`
- **Confidence**: `min(95, max(50, 50 + min(30, (volume_ratio-1.1)*30) + min(20, wick_upper_ratio*25)))`
- **Tradeable**: Yes (quality >= 55)
- **Quality Score Base**: 75
- **Description**: Smart money distributing, bearish bias.

#### 9. **SIDEWAY_RANGE**
- **Conditions** (all must be true):
  - `adx < adaptive_adx_threshold + 5`
  - `structure_type == 'RANGING'`
  - `volatility_regime in ['LOW', 'NORMAL']`
  - `breakout_prob < 45`
- **Confidence**: 70
- **Tradeable**: Conditional (quality >= 65)
- **Quality Score Base**: 70
- **Description**: Price oscillating between clear levels, mean reversion favored.

#### 10. **UNCLEAR** (default fallback)
- **Confidence**: 50
- **Tradeable**: No
- **Quality Score Base**: 40
- **Description**: Mixed signals or insufficient data.

### 5.2 Adaptive ADX Threshold
```python
def _get_adaptive_adx_threshold(atr_percentile):
    if atr_percentile < 60:   return 18  # low volatility – lower threshold
    if atr_percentile > 140:  return 28  # high volatility – higher threshold
    return 22  # normal
```

---

## 6. Quality Score Calculation

Base scores per state (from `_calculate_quality_score`):

| State | Base Score |
|-------|------------|
| TRENDING_STRONG | 85 |
| TRENDING_WEAK | 65 |
| SIDEWAY_RANGE | 70 |
| BREAKOUT_EMERGING | 80 |
| REVERSAL_FORMING | 60 |
| ACCUMULATION | 75 |
| DISTRIBUTION | 75 |
| CHOPPY_UNCERTAIN | 25 |
| LIQUIDITY_VOID | 10 |
| UNCLEAR | 40 |

**Adjustments**:
- `noise_level > 0.6` → `-20`
- `adx > 35` → `+8`
- `adx > 25` → `+3` (only the higher applies)
- `volume_ratio > 1.4` → `+10`
- `alignment_score > 65` → `+10`
- `divergence_detected` AND state in (TRENDING_STRONG, TRENDING_WEAK) → `-15`

Final quality clamped to `[0, 100]`.

---

## 7. Tradeability Rules

| State Category | States | Requirements |
|----------------|--------|--------------|
| **Always tradeable** (if quality OK) | TRENDING_STRONG, BREAKOUT_EMERGING, ACCUMULATION, DISTRIBUTION | TRENDING_STRONG requires quality ≥60; others ≥55 |
| **Conditional** | TRENDING_WEAK, SIDEWAY_RANGE, REVERSAL_FORMING | quality ≥65 |
| **Never tradeable** | CHOPPY_UNCERTAIN, LIQUIDITY_VOID, UNCLEAR | (no exceptions) |

---

## 8. Stability Score Calculation

Stability starts at 50 and is adjusted:

| Factor | Condition | Change |
|--------|-----------|--------|
| Noise | < 0.3 | +25 |
| Noise | < 0.5 | +10 |
| Noise | > 0.7 | -25 |
| Trend | direction != 'NONE' AND strength > 50 | +15 |
| Volatility | 70 ≤ atr_percentile ≤ 130 | +10 |
| Volatility | > 150 | -20 |
| Volatility | < 40 | -15 |
| Volume | 0.7 < ratio < 1.5 | +10 |
| Volume | ratio > 2.0 OR ratio < 0.3 | -15 |
| MTF alignment | alignment_score > 65 | +15 |
| MTF alignment | alignment_score < 35 | -10 |

Final stability clamped to `[0, 100]`.

---

## 9. State Transition Smoothing

- History buffer size: 5
- After each classification, the engine checks the last 5 states.
- If any state appears **≥3 times** in the buffer, that state is returned (overrides current classification).
- Otherwise, the current raw classification is returned.

**Purpose**: Prevent rapid state flipping in noisy or transitional market conditions.

---

## 10. Helper Function Reference

| Method | Description |
|--------|-------------|
| `analyze(candles_df, **kwargs)` | Main entry point |
| `_compute_metrics(...)` | Aggregates all precomputed/calculated metrics |
| `_classify_state(metrics)` | Decision tree for state selection |
| `_smooth_state(state, confidence)` | Applies transition smoothing |
| `_calculate_quality_score(state, metrics)` | Computes tradeability quality |
| `_is_tradeable(state, quality, metrics)` | Boolean tradeability decision |
| `_compute_stability(metrics)` | Market stability score |
| `_describe_state(state, metrics)` | Human-readable description |
| `_calc_trend_metrics_optimized(df)` | EMA5/10, slope, direction |
| `_calc_strength_metrics_optimized(df)` | ADX10, RSI7 |
| `_calc_volatility_metrics(df)` | ATR percentile, BBW, regime |
| `_calc_noise_level_optimized(df)` | Weighted efficiency noise |
| `_calc_volume_ratio(df)` | Volume surge detection |
| `_detect_wick_pattern_optimized(df)` | Accumulation/distribution wicks |
| `_detect_volatility_compression_optimized(df, bbw, atr_percentile)` | Range/BBW compression |
| `_compute_dynamic_probabilities_optimized(df, adx, bbw, atr_percentile, regime)` | Breakout & reversal probs |
| `_detect_momentum_divergence(df, rsi)` | Simplified divergence |
| `_get_adaptive_adx_threshold(close, atr_percentile)` | Volatility-adjusted ADX threshold |

---

## 11. Example Usage

```python
from core.engines.market_state_classifier import MarketStateClassifier
import pandas as pd

classifier = MarketStateClassifier()

# Load OHLCV data
df = pd.read_csv('eurusd_5min.csv')

# Optionally pass precomputed Tier 1 data
result = classifier.analyze(
    candles_df=df,
    trend_data=trend_output,
    strength_data=strength_output,
    volatility_data=vol_output,
    structure_data=struct_output,
    mtf_data=mtf_output
)

print(f"Market State: {result['state']}")
print(f"Confidence: {result['confidence']}%")
print(f"Tradeable: {result['tradeable']}")
print(f"Quality: {result['quality_score']}/100")
print(f"Description: {result['description']}")
```

---

## 12. Version History

| Version | Date | Changes |
|---------|------|---------|
| 5.0.0 | 2026-06-14 | Optimized for 5-min binary options: reduced periods (ADX10, RSI7, ATR10, BBW14), adaptive ADX thresholds, divergence detection, volume surge, faster EMAs (5/10), reduced MIN_CANDLES to 50, state smoothing (3/5 rule) |
| (earlier) | – | Original version for longer timeframes |

---

## 13. Notes & Caveats

- The engine assumes `candles_df` is sorted in **ascending time order** (oldest first).
- Missing or insufficient candles (less than 50) will return `UNCLEAR` state with confidence 0.
- Precomputed Tier 1 data **significantly improves accuracy** – always pass if available.
- Divergence detection is **simplified** and relies on RSI + price extremes; a more sophisticated divergence engine may be added in future versions.
- The engine does **not** perform any trading decisions – it only classifies market regimes.
- For backtesting, the `_state_history` should be reset between independent runs (by creating a new instance).

---

## 14. Future Enhancements (Planned)

- [ ] Full RSI series divergence detection (not just endpoint approximation).
- [ ] Machine learning confidence calibration (output probabilities instead of raw scores).
- [ ] Micro-structure states for tick data (if needed).
- [ ] Integration with order flow / footprint data for accumulation/distribution.

---

**Document prepared by**: DeepSeek Agent  
**Purpose**: Official blueprint for market state classification calculations.  
**Maintainer**: Core Trading Engine Team
