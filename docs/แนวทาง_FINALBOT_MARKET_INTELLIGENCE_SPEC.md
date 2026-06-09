# 🧠 FINALSignal_BOT - Market Intelligence Infrastructure

## PHASE 0: Intelligence Layer (Current Focus)

**Principle:** 
- System must understand market BEFORE strategy executes
- Every module is strategy-agnostic
- Extensible for future AI/ML integration
- No CALL/PUT logic in analysis layer

---

## 📊 TIER 1: CORE ANALYSIS ENGINES

### 1.1 **Trend Intelligence Engine**
**Location:** `core/analysis/trend_intelligence.py`

**Responsibility:**
- Identify trend direction (UP / DOWN / NONE)
- Measure trend strength (WEAK / NORMAL / STRONG)
- Calculate trend slope / momentum
- Detect trend reversals early
- Classify trend type (Impulsive / Corrective / Choppy)

**Outputs:**
```python
TrendState = {
    'direction': 'UP' | 'DOWN' | 'NONE',
    'strength': 0-100,
    'slope': float,
    'momentum': float,
    'type': 'IMPULSIVE' | 'CORRECTIVE' | 'CHOPPY',
    'confidence': 0-100,
    'reversal_risk': 0-100,
    'sustain_probability': 0-100,
}
```

**Uses:**
- EMA (20, 50, 100, 200)
- Higher High / Higher Low
- Lower High / Lower Low
- Slope calculation
- Divergence detection

---

### 1.2 **Strength Intelligence Engine**
**Location:** `core/analysis/strength_intelligence.py`

**Responsibility:**
- Measure directional force (ADX, DI+, DI-)
- Detect momentum strength (RSI, MACD, Momentum)
- Rate of Change analysis
- Identify momentum divergence
- Classify strength regime (Weak / Normal / Strong / Extreme)

**Outputs:**
```python
StrengthState = {
    'adx': 0-100,
    'di_plus': 0-100,
    'di_minus': 0-100,
    'rsi': 0-100,
    'macd': float,
    'momentum_level': 'WEAK' | 'NORMAL' | 'STRONG' | 'EXTREME',
    'roc': float,
    'divergence': 'BULLISH' | 'BEARISH' | 'NONE',
    'strength_score': 0-100,
    'exhaustion_risk': 0-100,
}
```

**Uses:**
- ADX with DI+/DI-
- RSI (14)
- MACD (12, 26, 9)
- Rate of Change
- Momentum oscillator

---

### 1.3 **Volatility Intelligence Engine**
**Location:** `core/analysis/volatility_intelligence.py`

**Responsibility:**
- Measure price dispersion (ATR, BBW, StdDev)
- Classify volatility regime (Low / Normal / High / Extreme)
- Detect volatility spikes
- Calculate volatility percentile (0-100)
- Identify mean reversion / expansion likelihood

**Outputs:**
```python
VolatilityState = {
    'atr': float,
    'atr_percentile': 0-100,
    'bbw': float,
    'stddev': float,
    'regime': 'LOW' | 'NORMAL' | 'HIGH' | 'EXTREME',
    'volatility_score': 0-100,
    'expansion_probability': 0-100,
    'contraction_probability': 0-100,
    'volatility_zscore': float,
    'spike_detected': bool,
}
```

**Uses:**
- ATR (14)
- Bollinger Bands (20, 2)
- Standard Deviation
- Historical volatility percentile

---

### 1.4 **Structure Intelligence Engine**
**Location:** `core/analysis/structure_intelligence.py`

**Responsibility:**
- Identify support/resistance levels
- Detect breaks of structure (BOS)
- Recognize trend continuation/reversal patterns
- Classify price structure (Trending / Ranging / Breakout)
- Identify key zones

**Outputs:**
```python
StructureState = {
    'support_levels': [float, ...],
    'resistance_levels': [float, ...],
    'structure_type': 'TRENDING' | 'RANGING' | 'BREAKOUT',
    'structure_score': 0-100,
    'bos_detected': bool,
    'bos_type': 'BULLISH' | 'BEARISH' | 'NONE',
    'key_zones': {
        'strong_support': float,
        'strong_resistance': float,
        'middle': float,
    },
    'zone_proximity': 'FAR' | 'MEDIUM' | 'NEAR' | 'AT_LEVEL',
    'breakout_probability': 0-100,
    'reversal_probability': 0-100,
}
```

**Uses:**
- Pivot points
- Swing highs/lows
- Previous daily/weekly levels
- Fractals
- BOS logic

---

### 1.5 **Multi-Timeframe Context Engine**
**Location:** `core/analysis/mtf_intelligence.py`

**Responsibility:**
- Analyze alignment across timeframes (M1, M5, M15, M60, D1)
- Detect timeframe conflicts
- Classify MTF harmony (Perfect / Good / Mixed / Conflicting)
- Measure timeframe agreement level
- Identify MTF divergence

**Outputs:**
```python
MTFState = {
    'timeframes': {
        'M1': TrendState,
        'M5': TrendState,
        'M15': TrendState,
        'M60': TrendState,
        'D1': TrendState,
    },
    'alignment_score': 0-100,
    'harmony': 'PERFECT' | 'GOOD' | 'MIXED' | 'CONFLICTING',
    'agreement_level': float,
    'direction_consensus': 'STRONG' | 'WEAK' | 'NONE',
    'htf_direction': 'UP' | 'DOWN' | 'NONE',
    'ltf_direction': 'UP' | 'DOWN' | 'NONE',
    'htf_ltf_conflict': bool,
    'confidence_from_mtf': 0-100,
}
```

**Uses:**
- Parallel indicator analysis on multiple timeframes
- Trend alignment scoring

---

## 📊 TIER 2: MARKET STATE CLASSIFICATION

### 2.1 **Market State Classifier**
**Location:** `core/analysis/market_state_classifier.py`

**Responsibility:**
- Synthesize Tier 1 engines into single market state
- Classify market into distinct regimes
- Calculate state confidence
- Detect state transitions

**Market States:**
```
TRENDING_STRONG    - Clear trend + Strong strength + Valid regime
TRENDING_WEAK      - Trend exists but weak strength
SIDEWAY_RANGE      - No trend + Weak strength + Low volatility
BREAKOUT_EMERGING  - High volatility + Breaking S/R + High momentum
REVERSAL_FORMING   - Trend weakening + Divergence signals
ACCUMULATION       - Low volatility + Consolidation
DISTRIBUTION       - High volatility + Range-bound
CHOPPY_UNCERTAIN   - Conflicting signals + High noise
LIQUIDITY_VOID     - Low volume + Sparse trades
UNCLEAR            - Insufficient data or conflicting signals
```

**Outputs:**
```python
MarketState = {
    'state': str,  # one of above
    'state_confidence': 0-100,
    'duration': int,  # candles
    'likelihood_next_state': {
        'TRENDING_STRONG': 0-100,
        'SIDEWAY_RANGE': 0-100,
        'REVERSAL_FORMING': 0-100,
        # ... all states
    },
    'regime_quality': 0-100,
    'composite_score': {
        'trend': 0-100,
        'strength': 0-100,
        'volatility': 0-100,
        'structure': 0-100,
    },
}
```

---

### 2.2 **Regime Quality Scorer**
**Location:** `core/analysis/regime_quality_scorer.py`

**Responsibility:**
- Assess overall market regime quality
- Calculate "tradeable-ness" score
- Identify market noise level
- Measure regime stability

**Outputs:**
```python
RegimeQuality = {
    'overall_score': 0-100,
    'noise_level': 0-100,
    'stability': 0-100,
    'tradeable': bool,
    'quality_factors': {
        'trend_clarity': 0-100,
        'strength_confirmation': 0-100,
        'structure_validity': 0-100,
        'mtf_alignment': 0-100,
    },
    'recommendation': 'TRADE' | 'CAUTIOUS' | 'AVOID',
}
```

---

## 📊 TIER 3: PRICE ACTION INTELLIGENCE

### 3.1 **Candlestick Pattern Analyzer**
**Location:** `core/analysis/candle_pattern_analyzer.py`

**Responsibility:**
- Identify candlestick patterns
- Classify pattern significance
- Measure rejection strength
- Detect reversal/continuation signals

**Patterns:**
```
Reversal Patterns:
- Bullish Engulfing
- Bearish Engulfing
- Hammer
- Inverse Hammer
- Bullish Star
- Bearish Star
- Morning Star
- Evening Star

Continuation Patterns:
- Bullish Harami
- Bearish Harami
- Three White Soldiers
- Three Black Crows

Rejection Patterns:
- Bullish Rejection Candle
- Bearish Rejection Candle
- Doji
- Spinning Top
```

**Outputs:**
```python
CandlePattern = {
    'pattern_type': str,
    'classification': 'REVERSAL' | 'CONTINUATION' | 'NEUTRAL',
    'significance': 0-100,
    'reliability': 0-100,
    'location_quality': 0-100,
    'body_size': 'LARGE' | 'MEDIUM' | 'SMALL',
    'wick_length': 'LONG' | 'MEDIUM' | 'SMALL',
    'color': 'BULLISH' | 'BEARISH',
}
```

---

### 3.2 **Price Action Behavior Engine**
**Location:** `core/analysis/price_action_engine.py`

**Responsibility:**
- Analyze recent price behavior
- Detect impulse vs. corrective moves
- Measure momentum through candles
- Identify pullback zones
- Detect entry/exit zones

**Outputs:**
```python
PriceAction = {
    'recent_behavior': 'IMPULSIVE' | 'CORRECTIVE' | 'CHOPPY',
    'candle_momentum': float,
    'pullback_zone': {
        'start': float,
        'end': float,
        'quality': 0-100,
    },
    'entry_zone': {
        'price': float,
        'confidence': 0-100,
    },
    'rejection_strength': 0-100,
    'follow_through_likelihood': 0-100,
}
```

---

## 📊 TIER 4: SPECIAL INTELLIGENCE SYSTEMS

### 4.1 **Trap & Fakeout Detection Engine**
**Location:** `core/analysis/trap_fakeout_detector.py`

**Responsibility:**
- Detect fake breakouts
- Identify wick traps
- Recognize failed reversal signals
- Measure trap probability

**Indicators:**
- Break of structure without confirmation
- High wick rejection
- Momentum divergence at breakout
- Volume analysis on fakeout
- MTF conflict on breakout

**Outputs:**
```python
TrapDetection = {
    'trap_probability': 0-100,
    'fakeout_probability': 0-100,
    'breakout_quality': 0-100,
    'risk_level': 'LOW' | 'MEDIUM' | 'HIGH',
    'trap_type': 'WICK_TRAP' | 'BOS_FAKEOUT' | 'REVERSAL_TRAP' | 'NONE',
}
```

---

### 4.2 **Noise Detection & Filtering Engine**
**Location:** `core/analysis/noise_detector.py`

**Responsibility:**
- Measure market noise level
- Detect random vs. meaningful moves
- Filter out false signals
- Identify high-noise periods

**Outputs:**
```python
NoiseAnalysis = {
    'noise_level': 0-100,
    'signal_quality': 0-100,
    'whipsaw_risk': 0-100,
    'false_signal_probability': 0-100,
    'recommendation': 'TRUST_SIGNALS' | 'CAUTIOUS' | 'IGNORE',
}
```

---

### 4.3 **Liquidity Intelligence Engine**
**Location:** `core/analysis/liquidity_intelligence.py`

**Responsibility:**
- Analyze volume patterns
- Detect liquidity voids
- Measure spread quality (bid-ask)
- Identify slippage risk
- Volume profile analysis

**Outputs:**
```python
LiquidityState = {
    'volume': float,
    'volume_profile': dict,
    'liquidity_quality': 0-100,
    'spread_estimate': float,
    'slippage_risk': 0-100,
    'volume_confirmation': bool,
    'volume_divergence': bool,
}
```

---

### 4.4 **Divergence Intelligence Engine**
**Location:** `core/analysis/divergence_intelligence.py`

**Responsibility:**
- Detect bullish/bearish divergence
- Measure divergence strength
- Identify divergence zones
- Classify divergence type (Price/Momentum/Volume)

**Outputs:**
```python
Divergence = {
    'bullish_divergence': bool,
    'bearish_divergence': bool,
    'divergence_strength': 0-100,
    'divergence_type': 'PRICE' | 'MOMENTUM' | 'VOLUME' | 'NONE',
    'reversal_probability': 0-100,
    'zone_quality': 0-100,
}
```

---

## 📊 TIER 5: CONTEXT & PROBABILITY GENERATORS

### 5.1 **Market Context Generator**
**Location:** `core/analysis/market_context_generator.py`

**Responsibility:**
- Synthesize all intelligence into unified context
- Generate actionable market understanding
- Provide strategy-agnostic recommendations
- Calculate overall tradeable probability

**Outputs:**
```python
MarketContext = {
    'state': MarketState,
    'trend': TrendState,
    'strength': StrengthState,
    'volatility': VolatilityState,
    'structure': StructureState,
    'mtf': MTFState,
    'price_action': PriceAction,
    'candle_pattern': CandlePattern,
    'trap_risk': TrapDetection,
    'noise': NoiseAnalysis,
    'liquidity': LiquidityState,
    'divergence': Divergence,
    
    # Synthesized insights
    'overall_tradeable_score': 0-100,
    'bias': 'BULLISH' | 'BEARISH' | 'NEUTRAL',
    'key_insight': str,
    'risk_factors': [str],
    'opportunity_factors': [str],
    'next_expected_move': {
        'direction': 'UP' | 'DOWN',
        'probability': 0-100,
        'target': float,
        'risk': float,
    },
}
```

---

### 5.2 **Move Probability Estimator**
**Location:** `core/analysis/move_probability_estimator.py`

**Responsibility:**
- Estimate probability of next move
- Calculate expected move size
- Measure move confidence
- Project price targets

**Outputs:**
```python
MoveProbability = {
    'upside_probability': 0-100,
    'downside_probability': 0-100,
    'expected_move_size': float,
    'upside_target': float,
    'downside_target': float,
    'confidence': 0-100,
    'timeframe_to_move': int,  # candles
}
```

---

## 📊 TIER 6: QUALITY & CONFIDENCE FRAMEWORK

### 6.1 **Signal Quality Scorer**
**Location:** `core/analysis/signal_quality_scorer.py`

**Responsibility:**
- Rate quality of any potential signal
- Measure signal reliability
- Quantify signal confidence
- Identify high-quality vs. low-quality setups

**Scoring Factors:**
```
- Trend alignment
- Strength confirmation
- Structure validity
- MTF agreement
- Pattern quality
- Price action clarity
- Trap probability (inverse)
- Noise level (inverse)
- Liquidity quality
```

**Outputs:**
```python
SignalQuality = {
    'overall_score': 0-100,
    'individual_scores': {
        'trend_alignment': 0-100,
        'strength_confirmation': 0-100,
        'structure_validity': 0-100,
        'mtf_agreement': 0-100,
        'pattern_quality': 0-100,
        'price_action_clarity': 0-100,
        'trap_risk': 0-100,  # inverse (lower = better)
        'noise_level': 0-100,  # inverse
        'liquidity': 0-100,
    },
    'quality_tier': 'PREMIUM' | 'GOOD' | 'ACCEPTABLE' | 'POOR',
    'reliability_estimate': 0-100,
}
```

---

### 6.2 **Confidence & Reliability Framework**
**Location:** `core/analysis/confidence_framework.py`

**Responsibility:**
- Rate confidence in all analyses
- Measure reliability of classifications
- Provide confidence intervals
- Track confidence degradation over time

**Outputs:**
```python
ConfidenceMetrics = {
    'analysis_confidence': 0-100,
    'state_confidence': 0-100,
    'direction_confidence': 0-100,
    'strength_confidence': 0-100,
    'volatility_confidence': 0-100,
    'structure_confidence': 0-100,
    'mtf_confidence': 0-100,
    
    'confidence_factors': {
        'data_quality': 0-100,
        'indicator_agreement': 0-100,
        'historical_pattern_match': 0-100,
        'regime_stability': 0-100,
    },
    
    'degradation': float,  # 0-1, increases with time
}
```

---

## 📊 TIER 7: MARKET BEHAVIOR INTELLIGENCE (NEW - PHASE 0)

### 7.1 **State Transition Intelligence Engine**
**Location:** `core/analysis/transition_intelligence.py`

**Responsibility:**
- Detect market state transitions early
- Measure probability of state change
- Identify pre-transition signals
- Calculate transition stability
- Predict next likely state

**State Transitions to Track:**
```
TRENDING → REVERSAL
TRENDING → SIDEWAY
SIDEWAY → BREAKOUT
BREAKOUT → TRENDING
CHOPPY → CONSOLIDATION
CONSOLIDATION → BREAKOUT
```

**Outputs:**
```python
TransitionState = {
    'current_state': str,
    'stability': 0-100,  # How stable is current state?
    'transition_risk': 0-100,  # Risk of state change
    'next_likely_state': str,
    'next_state_probability': 0-100,
    'transition_candles_remaining': int,  # Est. candles until transition
    'early_transition_signals': [str],
    'transition_type': 'GRADUAL' | 'ABRUPT' | 'FAILED',
    'time_to_transition': {
        'optimistic': int,  # earliest
        'realistic': int,   # most likely
        'pessimistic': int, # latest
    },
}
```

**Detects:**
- Strength degradation
- Structure breakdown
- Volatility spike/contraction
- MTF divergence appearance
- Candle pattern warnings

---

### 7.2 **Conflict Analysis Engine**
**Location:** `core/analysis/conflict_intelligence.py`

**Responsibility:**
- Detect signals that contradict each other
- Measure conflict severity
- Identify which signals are wrong
- Quantify market uncertainty
- Classify conflict type

**Types of Conflicts:**
```
TREND vs STRENGTH conflict
TREND vs STRUCTURE conflict
MTF conflict (higher TF vs lower TF)
VOLATILITY vs MOMENTUM conflict
VOLUME vs PRICE conflict
DIVERGENCE conflicts
```

**Outputs:**
```python
ConflictAnalysis = {
    'conflict_detected': bool,
    'conflict_severity': 0-100,
    'conflict_type': str,
    'conflicting_signals': [
        {'signal': str, 'direction': 'BULLISH|BEARISH'},
        ...
    ],
    'resolution_probability': {
        'bullish_win': 0-100,
        'bearish_win': 0-100,
        'consolidation': 0-100,
    },
    'uncertainty_level': 0-100,
    'market_indecision_strength': 0-100,
    'likely_resolution_candles': int,
    'resolution_scenario': str,
}
```

**Measures:**
- How many signals agree vs. disagree
- Strength of disagreement
- Which side is "stronger"
- Time until conflict resolves

---

### 7.3 **Market Efficiency Analysis Engine**
**Location:** `core/analysis/efficiency_intelligence.py`

**Responsibility:**
- Measure how efficiently market is moving
- Detect inefficient price moves (opportunities)
- Identify noise vs. signal
- Calculate move "quality"
- Detect mean reversion setups

**Concepts:**
- Efficiency Ratio (directional move vs total move)
- Candle Quality (body size vs total range)
- Compression Level (pre-breakout tightness)
- Range Position (where price sits in recent range)

**Outputs:**
```python
EfficiencyMetrics = {
    'efficiency_ratio': 0-1,  # 1 = perfect trending, 0 = complete noise
    'move_quality': 0-100,    # How clean is the move?
    'signal_to_noise': 0-1,   # What % is real move vs noise?
    
    'candle_quality': {
        'body_to_range_ratio': 0-1,
        'wick_quality': 0-100,
        'candle_conviction': 0-100,
    },
    
    'compression': {
        'atr_ratio': float,  # Current vs historical
        'bbw_ratio': float,  # Current vs historical
        'compression_level': 'EXTREME' | 'HIGH' | 'NORMAL' | 'LOW',
        'breakout_imminent': bool,
    },
    
    'range_position': {
        'position_in_range': 0-100,  # 0 = bottom, 100 = top
        'proximity_to_extremes': {
            'to_high': 0-100,
            'to_low': 0-100,
        },
        'breakout_direction_bias': 'UP' | 'DOWN' | 'NEUTRAL',
    },
    
    'mean_reversion_probability': 0-100,
    'continuation_probability': 0-100,
    'breakout_probability': 0-100,
}
```

---

### 7.4 **Behavioral Persistence Layer**
**Location:** `core/analysis/persistence_intelligence.py`

**Responsibility:**
- Measure how likely behavior is to continue
- Detect pattern persistence
- Identify behavior fatigue
- Calculate momentum persistence
- Forecast behavior change likelihood

**Behaviors to Track:**
```
Trend persistence
Momentum persistence
Volatility persistence
Range-bound persistence
Rejection persistence
Pullback persistence
```

**Outputs:**
```python
PersistenceMetrics = {
    'trend_persistence': {
        'continues_probability': 0-100,
        'reverses_probability': 0-100,
        'consolidates_probability': 0-100,
        'persistence_strength': 0-100,
        'persistence_candles_remaining': int,
    },
    
    'momentum_persistence': {
        'continues': 0-100,
        'fades': 0-100,
        'exhaustion_risk': 0-100,
    },
    
    'volatility_persistence': {
        'high_vol_continues': 0-100,
        'low_vol_continues': 0-100,
        'regime_change_probability': 0-100,
    },
    
    'pattern_persistence': {
        'current_pattern': str,
        'pattern_holds_probability': 0-100,
        'pattern_breaks_probability': 0-100,
        'most_likely_outcome': str,
    },
    
    'fatigue_analysis': {
        'trend_fatigue': 0-100,
        'buyer_fatigue': 0-100,
        'seller_fatigue': 0-100,
        'exhaustion_imminent': bool,
    },
}
```

**Uses:**
- Candle count in current state
- Strength degradation over time
- Pattern lifespan analysis
- Historical similar patterns
- Momentum divergence

---

### 7.5 **Probabilistic Continuation/Failure Engine**
**Location:** `core/analysis/continuation_failure_analyzer.py`

**Responsibility:**
- Estimate probability of move continuing vs failing
- Identify turn points early
- Measure move sustainability
- Project likely outcome

**Outputs:**
```python
ContinuationFailureAnalysis = {
    'continuation': {
        'probability': 0-100,
        'expected_distance': float,
        'timeframe': int,  # candles
        'confidence': 0-100,
    },
    
    'failure': {
        'probability': 0-100,
        'reversal_probability': 0-100,
        'consolidation_probability': 0-100,
        'timeframe': int,
        'confidence': 0-100,
    },
    
    'turn_point_analysis': {
        'next_likely_turn': float,  # price level
        'distance_to_turn': float,
        'candles_to_turn': int,
        'turn_probability': 0-100,
    },
    
    'sustainability': {
        'move_sustainable': bool,
        'sustainability_score': 0-100,
        'risk_factors': [str],
        'strength_factors': [str],
    },
    
    'scenario_analysis': {
        'bull_scenario': {
            'probability': 0-100,
            'target': float,
            'invalidation': float,
        },
        'bear_scenario': {
            'probability': 0-100,
            'target': float,
            'invalidation': float,
        },
        'sideways_scenario': {
            'probability': 0-100,
            'upper_bound': float,
            'lower_bound': float,
        },
    },
}
```

---

### 7.6 **OrderFlow Intelligence Approximation**
**Location:** `core/analysis/orderflow_approximation.py`

**Responsibility:**
- Approximate order flow behavior (without direct orderflow data)
- Detect accumulation/distribution
- Measure buying vs selling pressure
- Identify smart money moves

**Approximation Methods:**
- Volume analysis
- Candle body vs wick analysis
- Close position in candle
- Breakout quality
- Support/Resistance behavior

**Outputs:**
```python
OrderflowApproximation = {
    'buying_pressure': 0-100,
    'selling_pressure': 0-100,
    'pressure_balance': float,  # -1 = all selling, +1 = all buying
    
    'accumulation': {
        'detected': bool,
        'strength': 0-100,
        'phase': 'EARLY' | 'ACTIVE' | 'LATE',
    },
    
    'distribution': {
        'detected': bool,
        'strength': 0-100,
        'phase': 'EARLY' | 'ACTIVE' | 'LATE',
    },
    
    'smart_money_behavior': {
        'detected': bool,
        'direction': 'UP' | 'DOWN' | 'NONE',
        'strength': 0-100,
        'accumulation_zone': (float, float),
    },
    
    'retail_vs_institutional': {
        'retail_dominated': bool,
        'institutional_dominated': bool,
        'conflict_level': 0-100,
    },
}
```

---

### 7.7 **Statistical Anomaly Detection**
**Location:** `core/analysis/anomaly_detector.py`

**Responsibility:**
- Detect statistical outliers in market behavior
- Identify unusual price/volume combinations
- Flag improbable moves
- Calculate move rarity

**Detects:**
```
Unusual volume spikes
Unusual price moves (larger than expected)
Unusual candle formations
Unusual pattern breakdowns
Unusual volatility spikes
```

**Outputs:**
```python
AnomalyDetection = {
    'anomaly_detected': bool,
    'anomaly_type': str,
    'severity': 0-100,  # How unusual is this?
    'rarity_score': 0-100,  # 100 = very rare
    'move_percentile': 0-100,  # Where does this rank historically?
    
    'anomaly_interpretation': {
        'is_bullish': bool | None,
        'is_bearish': bool | None,
        'is_neutral': bool,
        'likely_cause': str,
    },
    
    'continuation_probability_given_anomaly': 0-100,
    'failure_probability_given_anomaly': 0-100,
    'reversal_probability_given_anomaly': 0-100,
}
```

---

## 📊 TIER 8: UTILITIES & HELPERS

### 8.1 **Analytical Utilities**
**Location:** `core/utils/analytical_utils.py`

**Reusable functions:**
- Trend slope calculation
- Moving average alignment
- Indicator normalization
- Probability calculation
- Weighted scoring
- Confidence aggregation
- Efficiency Ratio calculation
- Candle Quality scoring
- Persistence calculation

---

### 8.2 **Debugging & Explainability**
**Location:** `core/utils/debug_explainer.py`

**Responsibility:**
- Explain every intelligence output
- Provide reasoning for classifications
- Generate analytical reports
- Track decision flow for auditing
- Show how each behavior score was calculated

**Outputs:**
```python
ExplainabilityReport = {
    'timestamp': datetime,
    'market_state': str,
    'reasoning': str,  # Human-readable explanation
    'supporting_factors': [str],
    'contradicting_factors': [str],
    'confidence_justification': str,
    'alternative_interpretations': [str],
    'behavior_analysis': {
        'transition_signals': [str],
        'conflict_sources': [str],
        'efficiency_assessment': str,
        'persistence_forecast': str,
        'continuation_probability_logic': str,
    },
}
```

---

### 8.3 **Performance Analytics**
**Location:** `core/utils/performance_analytics.py`

**Responsibility:**
- Track accuracy of intelligence outputs
- Measure predictive power
- Calculate win rate per signal type
- Analyze effectiveness over time
- Compare predicted vs actual outcomes

---

## 🔄 DATA FLOW ARCHITECTURE

```
DATA LAYER
    ↓
[Input: OHLCV Candles]
    ↓
================== TIER 1: CORE ENGINES ==================
├── Trend Intelligence Engine
├── Strength Intelligence Engine
├── Volatility Intelligence Engine
├── Structure Intelligence Engine
└── Multi-Timeframe Intelligence Engine
    ↓
================== TIER 2: STATE CLASSIFICATION ==================
├── Market State Classifier
└── Regime Quality Scorer
    ↓
================== TIER 3: PRICE ACTION ==================
├── Candlestick Pattern Analyzer
└── Price Action Behavior Engine
    ↓
================== TIER 4: SPECIAL SYSTEMS ==================
├── Trap & Fakeout Detector
├── Noise Detection Engine
├── Liquidity Intelligence Engine
└── Divergence Intelligence Engine
    ↓
================== TIER 5: CONTEXT GENERATION ==================
├── Market Context Generator
└── Move Probability Estimator
    ↓
================== TIER 6: QUALITY ASSESSMENT ==================
├── Signal Quality Scorer
└── Confidence & Reliability Framework
    ↓
[OUTPUT: Rich Market Intelligence]
    ↓
STRATEGY LAYER (Future)
    ↓
SCORING LAYER (Future)
    ↓
DECISION LAYER (Future)
```

---

## 🎯 KEY PRINCIPLES

1. **Strategy-Agnostic**: Every module works independently of strategy
2. **Reusable**: All engines available for any future strategy
3. **Extensible**: Easy to add new intelligence sources
4. **Explainable**: Every output can be justified
5. **Confidence-Rated**: All outputs include confidence/reliability
6. **Non-Prescriptive**: No CALL/PUT logic anywhere
7. **Probability-Based**: Everything in terms of probability
8. **Future-Proof**: Ready for AI/ML enhancement

---

## 📋 IMPLEMENTATION ORDER - PHASE 0 FOCUS

**Phase 0 Core (Stabilize Analytical Core):**

1. **TIER 1: Core Engines** (5 modules)
   - Trend Intelligence
   - Strength Intelligence
   - Volatility Intelligence
   - Structure Intelligence
   - Multi-Timeframe Intelligence

2. **TIER 2: State Classification** (2 modules)
   - Market State Classifier
   - Regime Quality Scorer

3. **TIER 3: Price Action** (2 modules)
   - Candlestick Pattern Analyzer
   - Price Action Behavior Engine

4. **TIER 4: Detection Systems** (4 modules)
   - Trap & Fakeout Detector
   - Noise Detection Engine
   - Liquidity Intelligence Engine
   - Divergence Intelligence Engine

5. **TIER 5: Market Behavior Intelligence** (7 modules - NEW PRIORITY)
   - State Transition Intelligence ⭐
   - Conflict Analysis Engine ⭐
   - Market Efficiency Analysis ⭐
   - Behavioral Persistence Layer ⭐
   - Probabilistic Continuation/Failure Engine ⭐
   - OrderFlow Intelligence Approximation ⭐
   - Statistical Anomaly Detection ⭐

6. **TIER 6: Context Generation** (2 modules)
   - Market Context Generator
   - Move Probability Estimator

7. **TIER 7: Quality Assessment** (2 modules)
   - Signal Quality Scorer
   - Confidence & Reliability Framework

8. **TIER 8: Utilities** (3 modules)
   - Analytical Utilities
   - Debugging & Explainability
   - Performance Analytics

**Total Phase 0: 29 modules**

**What comes AFTER Phase 0 (Phase 1-3):**
- Strategy Layer (using intelligence from Phase 0)
- Scoring Layer
- Decision Layer
- Execution Layer
- AI Integration Layer

---

## 📊 SUCCESS METRICS - PHASE 0

By end of Phase 0, system must understand:

**Market Understanding (10+ dimensions):**
- ✅ Direction (Trend Intelligence)
- ✅ Strength (Strength Intelligence)
- ✅ Volatility (Volatility Intelligence)
- ✅ Structure (Structure Intelligence)
- ✅ Multi-Timeframe Alignment (MTF Intelligence)
- ✅ Overall State (Market State Classifier)
- ✅ Price Action Patterns (Candlestick Analyzer)
- ✅ Risk Factors (Trap/Fakeout Detector, Noise Detector)
- ✅ Liquidity Quality (Liquidity Intelligence)
- ✅ Signal Conflicts (Divergence Intelligence)

**Behavioral Understanding (NEW - Market Behavior Layer):**
- ✅ What state transition is coming (Transition Intelligence)
- ✅ What signals contradict (Conflict Analysis)
- ✅ How efficiently market is moving (Efficiency Analysis)
- ✅ How long behavior will persist (Persistence Intelligence)
- ✅ Probability move continues vs fails (Continuation/Failure Analysis)
- ✅ What order flow approximation says (OrderFlow Intelligence)
- ✅ What is statistically unusual (Anomaly Detection)

**Context & Quality:**
- ✅ Unified market context (Market Context Generator)
- ✅ Next move probability (Move Probability Estimator)
- ✅ Signal quality rating (Signal Quality Scorer)
- ✅ Confidence in all outputs (Confidence Framework)

**Explainability:**
- ✅ Every output can be justified (Debugging & Explainability)
- ✅ Human-readable reasoning available
- ✅ Decision flow traceable for auditing

**Key Requirements Met:**
- ✅ Zero CALL/PUT logic in analysis layer
- ✅ Strategy-agnostic (works for any strategy)
- ✅ Extensible (easy to add more intelligence)
- ✅ Confidence-rated (all outputs with reliability)
- ✅ Probability-based thinking
- ✅ Institutional-grade observation capability
- ✅ AI-ready architecture
- ✅ Behavioral understanding, not just indicator-based

**System Ready To:**
- ✅ Feed rich context to Strategy Layer
- ✅ Support AI/ML training with high-quality data
- ✅ Identify market behavior patterns
- ✅ Forecast market state transitions
- ✅ Detect conflicts and ambiguities
- ✅ Rate quality of any potential signal
- ✅ Explain every decision made

---

**This is the Intelligence OS. Strategy is just one consumer of it.**

