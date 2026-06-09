BOT_FINALBOT — The Art of Saying NO

เปลี่ยนเป็นไฟล์ ที่ทำหน้าที่เป็น "คัมภีร์หลัก" ที่กำหนดกฎเกณฑ์ ทิศทาง และปรัชญาของระบบ  The Art of Saying NO

**Status:** Architecture Approved (With Minor Fixes)  
**Version:** 2.1-final  
**Date:** May 19, 2026  
**Owner:** Boss  
**Purpose:** Institutional-grade Trading Intelligence OS

---

## 📁 Project Tree (Complete - 151 Files)

```
BOT_FINALBOT/
│
├── 📄 main.py                          ← Entry point (orchestrator only)
├── 📄 __init__.py                      ← Package marker
├── 📄 requirements.txt                 ← Dependencies
├── 📄 README.md                        ← Documentation
│
├── 📁 config/                          ← Configuration (IMMUTABLE at runtime)
│   ├── settings.json                   ← System config
│   ├── symbols.txt                     ← Trading pairs
│   └── thresholds.json                 ← Decision thresholds
│
├── 📁 core/                            ← Core Intelligence OS (LAYER 1)
│   ├── 📄 __init__.py
│   │
│   ├── 📁 interfaces/                  ← Contracts (INPUT/OUTPUT SHAPES)
│   │   ├── 📄 __init__.py
│   │   ├── 📄 engine_interface.py      ← Engine contract
│   │   ├── 📄 context_interface.py     ← Context contract
│   │   └── 📄 strategy_interface.py    ← Strategy contract
│   │
│   ├── 📁 models/                      ← Data Schemas (TYPE SAFETY)
│   │   ├── 📄 __init__.py
│   │   ├── 📄 candle.py                ← Candle model (OHLCV)
│   │   ├── 📄 market_context.py        ← MarketContext model (immutable snapshot)
│   │   ├── 📄 score.py                 ← Score model (entry/block/confidence)
│   │   ├── 📄 signal.py                ← Signal model (CALL/PUT/NO_SIGNAL)
│   │   └── 📄 engine_output.py         ← Generic engine output
│   │
│   ├── 📁 data/                        ← Data Layer (INPUT)
│   │   ├── 📄 __init__.py
│   │   ├── 📄 data_source.py           ← Abstract data source interface
│   │   ├── 📄 iq_option_adapter.py     ← IQ Option API adapter
│   │   └── 📄 dummy_data.py            ← Synthetic data generator
│   │
│   ├── 📁 engines/                     ← Intelligence Engines (FLAT - NO TIER FOLDERS)
│   │   │                               ← Future: can refactor to behavior/, synthesis/, utilities/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 RESPONSIBILITY_MATRIX.md ← ⭐ CRITICAL: Engine boundary document
│   │   ├── 📄 base_engine.py           ← Abstract engine base
│   │   │
│   │   ├── 📄 trend_engine.py          ← TIER 1: Detect direction + slope
│   │   ├── 📄 structure_engine.py      ← TIER 1: Detect HH/HL/LH/LL + BOS/CHOCH
│   │   ├── 📄 strength_engine.py       ← TIER 1: ADX + RSI + MACD + momentum
│   │   ├── 📄 volatility_engine.py     ← TIER 1: ATR + BBW + regime
│   │   ├── 📄 liquidity_engine.py      ← TIER 1: Stop hunt + sweep zones
│   │   │
│   │   ├── 📄 market_state_classifier.py ← TIER 2: Classify market state (10 types)
│   │   ├── 📄 regime_quality_scorer.py   ← TIER 2: Rate regime quality
│   │   │
│   │   ├── 📄 candle_pattern_analyzer.py ← TIER 3: Candle patterns (engulfing, hammer, etc)
│   │   ├── 📄 price_action_handler.py    ← TIER 3: Candle momentum + rejection
│   │   │
│   │   ├── 📄 trap_detector.py         ← TIER 4: Trap + fakeout probability
│   │   ├── 📄 noise_detector.py        ← TIER 4: Noise level + signal quality
│   │   ├── 📄 divergence_analyzer.py   ← TIER 4: Bullish/bearish divergence
│   │   ├── 📄 anomaly_detector.py      ← TIER 4: Statistical anomalies
│   │   │
│   │   ├── 📄 transition_analyzer.py   ← TIER 5: State transition probability
│   │   ├── 📄 conflict_analyzer.py     ← TIER 5: Signal conflicts
│   │   ├── 📄 efficiency_analyzer.py   ← TIER 5: Move quality + efficiency ratio
│   │   ├── 📄 persistence_analyzer.py  ← TIER 5: Trend fatigue + sustain prob
│   │   ├── 📄 continuation_analyzer.py ← TIER 5: Continuation vs reversal prob
│   │   ├── 📄 market_pressure_analyzer.py ← TIER 5: Smart money pressure (NOT orderflow)
│   │   ├── 📄 behavior_analyzer.py     ← TIER 5: Combined behavior intelligence
│   │   │
│   │   ├── 📄 context_synthesizer.py   ← TIER 6: Merge all engines → MarketContext
│   │   ├── 📄 context_probability_inference.py ← TIER 6: Infer probability from current context
│   │   │
│   │   ├── 📄 signal_quality_scorer.py ← TIER 7: Overall signal confidence
│   │   ├── 📄 confidence_framework.py  ← TIER 7: Confidence aggregation
│   │   │
│   │   ├── 📄 analytical_utils.py      ← TIER 8: Shared math utilities
│   │   ├── 📄 explainability_engine.py ← TIER 8: Reasoning reports
│   │   └── 📄 performance_tracker.py   ← TIER 8: Accuracy tracking
│   │
│   ├── 📁 scoring/                     ← Scoring Layer (DECISION LOGIC)
│   │   ├── 📄 __init__.py
│   │   ├── 📄 entry_scorer.py          ← Score: Entry viability (0-100)
│   │   ├── 📄 block_scorer.py          ← Score: Block risk (0-100)
│   │   ├── 📄 confidence_scorer.py     ← Score: Overall confidence (0-100)
│   │   └── 📄 score_aggregator.py      ← Merge & normalize all scores
│   │
│   ├── 📁 orchestration/               ← Pipeline Orchestration (WIRES ONLY)
│   │   ├── 📄 __init__.py
│   │   ├── 📄 pipeline.py              ← Main orchestrator (no logic, wires only)
│   │   ├── 📄 context_builder.py       ← Assemble MarketContext (immutable)
│   │   └── 📄 execution_gate.py        ← ⭐ FINAL AUTHORITY (default: NO_SIGNAL)
│   │
│   └── 📁 exceptions/                  ← Error Handling
│       ├── 📄 __init__.py
│       ├── 📄 engine_exceptions.py     ← Engine errors
│       ├── 📄 context_exceptions.py    ← Context errors
│       └── 📄 validation_exceptions.py ← Validation errors
│
├── 📁 strategy/                        ← Strategy Layer (LAYER 2 - PLUGIN ONLY)
│   ├── 📄 __init__.py
│   ├── 📄 base_strategy.py             ← Strategy abstract interface (read-only context)
│   ├── 📄 strategy_registry.py         ← Strategy loader
│   │
│   ├── 📁 v1_compression_breakout/     ← V1 Strategy
│   │   ├── 📄 __init__.py
│   │   ├── 📄 strategy.py              ← V1 logic (5M Volatility Compression Breakout)
│   │   ├── 📄 entry_rules.py           ← Entry conditions
│   │   ├── 📄 block_rules.py           ← Block conditions
│   │   └── 📄 config.json              ← V1 parameters
│   │
│   └── 📁 v2_reversal/                 ← V2 Strategy (Future)
│       └── 📄 __init__.py
│
├── 📁 execution/                       ← Execution Layer (LAYER 3 - SIGNAL ONLY INPUT)
│   ├── 📄 __init__.py
│   ├── 📄 broker_adapter.py            ← Abstract broker interface
│   ├── 📄 iq_option_executor.py        ← IQ Option orders (receives Signal only)
│   ├── 📄 order_manager.py             ← Order tracking
│   └── 📄 position_sizer.py            ← Risk management (from Signal)
│
├── 📁 monitoring/                      ← Monitoring & Logging (LAYER 4 - OUTPUT)
│   ├── 📄 __init__.py
│   ├── 📄 logger.py                    ← Logging system
│   ├── 📄 performance_monitor.py       ← Track accuracy metrics
│   ├── 📄 signal_notifier.py           ← Alerts (Telegram, email)
│   └── 📄 reporter.py                  ← Daily/weekly reports
│
├── 📁 tests/                           ← Testing Suite
│   ├── 📄 __init__.py
│   │
│   ├── 📁 unit/                        ← Unit tests (organized by component)
│   │   ├── 📄 __init__.py
│   │   ├── 📁 test_engines/            ← Test each engine independently
│   │   │   ├── test_trend_engine.py
│   │   │   ├── test_structure_engine.py
│   │   │   ├── test_strength_engine.py
│   │   │   ├── ... (1 per engine = 30 files)
│   │   │
│   │   ├── 📁 test_models/             ← Test schema validation
│   │   │   ├── test_candle_model.py
│   │   │   ├── test_market_context_model.py
│   │   │   ├── test_score_model.py
│   │   │   ├── test_signal_model.py
│   │   │   └── test_engine_output_model.py
│   │   │
│   │   ├── 📁 test_scoring/            ← Test scoring logic
│   │   │   ├── test_entry_scorer.py
│   │   │   ├── test_block_scorer.py
│   │   │   └── test_score_aggregator.py
│   │   │
│   │   └── 📁 test_orchestration/      ← Test pipeline
│   │       ├── test_pipeline.py
│   │       └── test_execution_gate.py
│   │
│   ├── 📁 integration/                 ← Integration tests
│   │   ├── 📄 __init__.py
│   │   ├── 📄 test_end_to_end.py       ← Full pipeline (data → signal)
│   │   ├── 📄 test_strategy.py         ← Strategy + pipeline
│   │   └── 📄 test_execution.py        ← Order execution flow
│   │
│   ├── 📁 backtest/                    ← Backtesting
│   │   ├── 📄 __init__.py
│   │   ├── 📄 backtest_engine.py       ← Replay candles
│   │   ├── 📄 metrics.py               ← Win rate, profit, sharpe, etc
│   │   └── 📄 report.py                ← Backtest report generator
│   │
│   └── 📁 fixtures/                    ← Test data & samples
│       ├── 📄 __init__.py
│       ├── 📄 sample_candles.py        ← Dummy candle data
│       └── 📄 sample_context.py        ← Sample MarketContext objects
│
├── 📁 utils/                           ← Utilities
│   ├── 📄 __init__.py
│   ├── 📄 time_utils.py                ← Time handling (UTC, Bangkok tz)
│   ├── 📄 math_utils.py                ← Math functions (slope, normalize, etc)
│   └── 📄 validators.py                ← Data validation
│
└── 📁 docs/                            ← Documentation
    ├── 📄 ARCHITECTURE.md              ← Architecture overview
    ├── 📄 ENGINE_RESPONSIBILITY.md     ← Full responsibility matrix
    ├── 📄 API_REFERENCE.md             ← Engine APIs
    ├── 📄 DATA_MODELS.md               ← Schema definitions
    └── 📄 DEPLOYMENT.md                ← Deployment guide
```

---

## 🔄 Data Flow (5 Layers - Strict Unidirectional)

```
┌────────────────────────────────────────────────────────────┐
│ LAYER 0: DATA INPUT                                        │
│ └─ Raw OHLCV from IQ Option or dummy data                 │
│    └─ Type: Candle objects                                │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ LAYER 1: INTELLIGENCE OS (core/engines/ + core/scoring/)  │
│                                                            │
│ ✅ Can: Analyze market independently                      │
│ ❌ Cannot: Know about strategy or execution               │
│ ❌ Cannot: Modify context at runtime                      │
│ ❌ Cannot: Send signals                                   │
│                                                            │
│ Process:                                                   │
│ ├─ Step 1: 30 engines analyze in parallel                │
│ │          ├─ TIER 1: Trend, Structure, Strength, etc   │
│ │          ├─ TIER 2-4: Classification + Detection       │
│ │          └─ TIER 5-8: Behavior + Synthesis + Quality  │
│ │          └─ Output: Individual engine results           │
│ │                                                          │
│ ├─ Step 2: Context Synthesizer merges all                │
│ │          └─ Output: MarketContext (immutable snapshot) │
│ │                                                          │
│ └─ Step 3: Scoring layers compute decisions              │
│            ├─ Entry Score (0-100)                         │
│            ├─ Block Score (0-100)                         │
│            └─ Confidence Score (0-100)                    │
│            └─ Output: MarketContext + Scores              │
│                                                            │
└────────────────────┬─────────────────────────────────────┘
                     │ (MarketContext - frozen/immutable)
                     ▼
┌────────────────────────────────────────────────────────────┐
│ LAYER 2: STRATEGY (strategy/ folder - PLUGIN ONLY)        │
│                                                            │
│ ✅ Can: Read MarketContext (read-only)                    │
│ ✅ Can: Propose entry/block signals                       │
│ ❌ Cannot: Analyze indicators directly                    │
│ ❌ Cannot: Access raw candle data                         │
│ ❌ Cannot: Send signals                                   │
│ ❌ Cannot: Modify MarketContext                           │
│                                                            │
│ Output: Strategy recommendation (entry/block scores)      │
│                                                            │
└────────────────────┬─────────────────────────────────────┘
                     │ (Strategy output)
                     ▼
┌────────────────────────────────────────────────────────────┐
│ LAYER 3: EXECUTION GATE (core/orchestration/execution_gate) │
│                                                            │
│ ⭐ FINAL AUTHORITY (ONLY SIGNAL EMITTER)                 │
│ 🚫 DEFAULT: NO_SIGNAL (philosophy: "Art of saying NO")   │
│                                                            │
│ Checks (ALL must pass):                                   │
│ ├─ Entry Score ≥ 70? ✓                                   │
│ ├─ Block Score < 40? ✓                                   │
│ ├─ Confidence ≥ 40? ✓                                    │
│ ├─ Market quality valid? ✓                               │
│ ├─ Cooldown OK? ✓                                        │
│ ├─ Max trades today OK? ✓                                │
│ └─ If ALL pass → emit Signal (CALL/PUT)                  │
│ └─ Else → NO_SIGNAL (default)                            │
│                                                            │
│ Output: Signal object (CALL | PUT | NO_SIGNAL)           │
│                                                            │
└────────────────────┬─────────────────────────────────────┘
                     │ (Signal object only)
                     ▼
┌────────────────────────────────────────────────────────────┐
│ LAYER 4: EXECUTION (execution/ folder)                    │
│                                                            │
│ ✅ Can: Receive Signal object                             │
│ ✅ Can: Size positions, calculate SL/TP                  │
│ ✅ Can: Submit orders                                     │
│ ❌ Cannot: Import core/engines directly                   │
│ ❌ Cannot: Parse MarketContext                            │
│ ❌ Cannot: Modify Signal                                  │
│                                                            │
│ ├─ Position Sizing                                        │
│ ├─ Stop Loss Calculation                                  │
│ ├─ Take Profit Calculation                                │
│ ├─ Order Submission (IQ Option API)                       │
│ └─ Order Tracking                                         │
│                                                            │
└────────────────────┬─────────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────────────┐
│ LAYER 5: MONITORING (monitoring/ folder)                  │
│                                                            │
│ ✅ Can: Log everything                                    │
│ ✅ Can: Track performance                                 │
│ ✅ Can: Send notifications                                │
│ ❌ Cannot: Modify any layer above                         │
│                                                            │
│ ├─ Logging                                                │
│ ├─ Notifications (Telegram, email)                        │
│ ├─ Performance Tracking                                   │
│ └─ Daily Reports                                          │
│                                                            │
└────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════
KEY PRINCIPLE: DATA FLOWS DOWNWARD ONLY ✅
NO BACKWARD FLOW ALLOWED
═══════════════════════════════════════════════════════════════
```

---

## 🔐 Strict Separation of Concerns

### **Layer Responsibilities (LOCKED)**

| Layer | Can Do | Cannot Do |
|-------|--------|-----------|
| **Intelligence (L1)** | Analyze market, compute scores | Know strategy, execute, modify context |
| **Strategy (L2)** | Read context, propose entry/block | Analyze indicators, send signals |
| **Execution Gate (L3)** | Apply rules, emit Signal | Modify strategy, analyze market |
| **Execution (L4)** | Size positions, submit orders | Import engines, parse context |
| **Monitoring (L5)** | Log, track, notify | Modify any layer above |

---

## 📊 Engine Responsibility Matrix (30 Engines)

### **TIER 1: Foundation (5 engines)**

| # | Engine | Input | Output | Purpose | Cannot Do |
|---|--------|-------|--------|---------|-----------|
| 1 | trend_engine | Candles M1-M60 | direction, slope, strength, confidence | Detect UP/DOWN/NONE + slope | Forecast reversal, classify state |
| 2 | structure_engine | Candles M15 | support, resistance, HH, HL, LH, LL, BOS | Detect price levels + BOS | Trap detection, fakeout rating |
| 3 | strength_engine | Candles M5 | ADX, RSI, MACD, momentum, divergence | Measure momentum indicators | Volatility analysis, noise detection |
| 4 | volatility_engine | Candles M5 | ATR, BBW, regime, spike, percentile | Measure ATR/volatility only | Noise filtering, signal quality |
| 5 | liquidity_engine | Candles + Structure | zones, sweeps, hunts, quality | Detect liquidity phenomena | Trap probability, fakeout rating |

### **TIER 2: Classification (2 engines)**

| # | Engine | Input | Output | Purpose | Cannot Do |
|---|--------|-------|--------|---------|-----------|
| 6 | market_state_classifier | All T1 | state (10 types), confidence | Classify market state (TRENDING, RANGING, etc) | Forecast transitions, rate quality |
| 7 | regime_quality_scorer | All T1 | regime_quality (0-100), tradeable | Rate overall market quality | Classify state, detect conflicts |

### **TIER 3: Price Action (2 engines)**

| # | Engine | Input | Output | Purpose | Cannot Do |
|---|--------|-------|--------|---------|-----------|
| 8 | candle_pattern_analyzer | Candles M5 | pattern, type, reliability | Identify candle patterns | Analyze momentum, rate quality |
| 9 | price_action_handler | Candles M5 | momentum, rejection, entry_zone | Analyze candle behavior | Pattern recognition, quality scoring |

### **TIER 4: Detection (4 engines)**

| # | Engine | Input | Output | Purpose | Cannot Do |
|---|--------|-------|--------|---------|-----------|
| 10 | trap_detector | Structure + Liquidity | trap_prob, fakeout_prob (0-100) | Rate trap quality (uses S/L input) | Detect structure, analyze signals |
| 11 | noise_detector | Volatility + Price Action | noise_level, signal_quality (0-100) | Detect noise (uses volatility input) | Analyze volatility, analyze candles |
| 12 | divergence_analyzer | Strength + Candles | bullish_div, bearish_div, strength | Detect divergence patterns | Measure indicators, rate quality |
| 13 | anomaly_detector | All inputs | anomaly, severity, rarity_score | Detect statistical anomalies | Classify state, rate signals |

### **TIER 5: Behavior (7 engines)**

| # | Engine | Input | Output | Purpose | Cannot Do |
|---|--------|-------|--------|---------|-----------|
| 14 | transition_analyzer | Market State | next_state_prob, type | Forecast state changes | Classify state, detect conflicts |
| 15 | conflict_analyzer | All engines | severity, type, resolution_prob | Detect conflicting signals | Forecast transitions, rate quality |
| 16 | efficiency_analyzer | Price Action + Volatility | ratio, quality, compression_level | Rate move efficiency | Analyze price action, analyze volatility |
| 17 | persistence_analyzer | Trend + Strength | persistence_prob, fatigue, candles_remaining | Forecast trend fatigue | Detect trend, measure momentum |
| 18 | continuation_analyzer | All behavioral | continuation_prob, reversal_prob, turn_points | Forecast continuation vs reversal | Forecast transitions, detect state |
| 19 | market_pressure_analyzer | Price Action + Volume | buying_pressure, selling_pressure, accum | Approximate smart money pressure (NO true orderflow - OTC) | Detect patterns, analyze candles |
| 20 | behavior_analyzer | All T5 | combined_score, risk_indicators | Synthesize behavior insights | Forecast individual behaviors |

### **TIER 6: Synthesis (2 engines) ⭐ GATEWAY**

| # | Engine | Input | Output | Purpose | Cannot Do |
|---|--------|-------|--------|---------|-----------|
| 21 | context_synthesizer | All engines (T1-5) | MarketContext (frozen) | MERGE all engines → immutable context | Add new fields, modify at runtime |
| 22 | context_probability_inference | MarketContext | upside_prob, downside_prob, targets | **INFER** probability from CURRENT context (NOT forecast future) | Forecast future moves, add indicators |

### **TIER 7: Quality (2 engines)**

| # | Engine | Input | Output | Purpose | Cannot Do |
|---|--------|-------|--------|---------|-----------|
| 23 | signal_quality_scorer | MarketContext | quality (PREMIUM/GOOD/ACCEPTABLE/POOR) | Rate overall signal quality | Classify state, aggregate confidence |
| 24 | confidence_framework | All outputs | analysis_confidence (0-100), factors | Aggregate confidence from all engines | Rate individual engines, forecast |

### **TIER 8: Utilities (3 engines)**

| # | Engine | Input | Output | Purpose | Cannot Do |
|---|--------|-------|--------|---------|-----------|
| 25 | analytical_utils | Any numeric data | slopes, normalized, calculations | Provide shared math utilities | Implement domain logic |
| 26 | explainability_engine | All decisions | reasoning_report, factor_breakdown | Generate decision explanations | Make decisions, modify reasoning |
| 27 | performance_tracker | Historical signals | accuracy, win_rate, profit_metrics | Track performance metrics | Make trading decisions |

### **TIER 6+ (continued)**

| # | Engine | Input | Output | Purpose | Cannot Do |
|---|--------|-------|--------|---------|-----------|
| 28 | (Reserved for future T6) | | | (Future enhancement) | |
| 29 | (Reserved for future T7) | | | (Future enhancement) | |
| 30 | (Reserved for future T8) | | | (Future enhancement) | |

---

## 🔒 Critical Rules (LOCKED IN)

✅ **Rule 1:** No tier folder nesting → All engines flat in `core/engines/`  
✅ **Rule 2:** Engine responsibility frozen → See RESPONSIBILITY_MATRIX.md  
✅ **Rule 3:** No backward data flow → Unidirectional only (downward)  
✅ **Rule 4:** Single MarketContext → One immutable snapshot per cycle  
✅ **Rule 5:** signal_gate is ONLY emitter → No other module sends CALL/PUT  
✅ **Rule 6:** execution_gate default = NO_SIGNAL → Philosophy: "Art of saying NO"  
✅ **Rule 7:** MarketContext is frozen → Engine CANNOT modify at runtime  
✅ **Rule 8:** Strategy is plugin-only → Read context, no raw data access  
✅ **Rule 9:** Execution receives Signal only → NEVER import core/engines  
✅ **Rule 10:** Every output has confidence → 0-100 score always (never NaN)  
✅ **Rule 11:** No circular dependencies → Dependency graph is DAG  
✅ **Rule 12:** Interface contracts → Every engine has input/output spec  
✅ **Rule 13:** Explainability required → Every decision has reasoning  
✅ **Rule 14:** market_pressure_analyzer ≠ orderflow → OTC has no true orderflow  
✅ **Rule 15:** context_probability_inference ≠ forecast → INFER from current only  

---

## 📋 Data Model Schemas (IMMUTABLE)

### **Candle Model**
```python
@dataclass(frozen=True)
class Candle:
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime
    timeframe: str  # M1, M5, M15, M60, D1
```

### **MarketContext (IMMUTABLE SNAPSHOT)**
```python
@dataclass(frozen=True)
class MarketContext:
    # TIER 1 outputs
    trend: TrendOutput
    structure: StructureOutput
    strength: StrengthOutput
    volatility: VolatilityOutput
    liquidity: LiquidityOutput
    
    # TIER 2 outputs
    market_state: MarketStateOutput
    regime_quality: RegimeQualityOutput
    
    # TIER 3-4 outputs
    candle_pattern: CandlePatternOutput
    price_action: PriceActionOutput
    trap_analysis: TrapAnalysisOutput
    noise_analysis: NoiseAnalysisOutput
    divergence: DivergenceOutput
    anomaly: AnomalyOutput
    
    # TIER 5 outputs
    behavior: BehaviorOutput
    
    # TIER 6 outputs
    probability: ProbabilityOutput
    
    # TIER 7 outputs
    quality: QualityOutput
    
    # Metadata
    timestamp: datetime
    pair: str
    confidence: int  # 0-100
```

### **Score Model**
```python
@dataclass(frozen=True)
class Score:
    value: int  # 0-100
    confidence: int  # 0-100
    factors: Dict[str, float]  # breakdown
    timestamp: datetime
```

### **Signal Model (FINAL OUTPUT)**
```python
@dataclass(frozen=True)
class Signal:
    action: str  # CALL | PUT | NO_SIGNAL (default)
    pair: str
    entry_score: Score
    block_score: Score
    confidence: Score
    reasoning: str  # explainability
    timestamp: datetime
    sl_price: float  # (optional)
    tp_price: float  # (optional)
```

---

## 📊 File Count Summary

| Component | Count | Detail |
|-----------|-------|--------|
| **core/** | 61 | 30 engines + interfaces + models + data + scoring + orchestration |
| **strategy/** | 10 | Base + V1 + V2 placeholder + registry |
| **execution/** | 5 | Adapter + executor + order manager + position sizer |
| **monitoring/** | 5 | Logger + monitor + notifier + reporter |
| **tests/** | 54 | Unit (42) + integration (4) + backtest (4) + fixtures (3) + init (1) |
| **utils/** | 4 | Time + math + validators + init |
| **docs/** | 5 | Architecture + responsibility + API + models + deployment |
| **config/** | 3 | settings.json + symbols.txt + thresholds.json |
| **root/** | 4 | main.py + __init__.py + requirements.txt + README.md |
| **TOTAL** | **151** | Complete system |

---

## 🚀 Implementation Roadmap (10 Phases)

### **Phase 0: Setup (1-2 days)**
- Create folder structure
- Create __init__.py files
- Create core/interfaces/ (contracts)

### **Phase 1: Models (2-3 days)**
- Create core/models/ (all schemas)
- Implement Candle, MarketContext, Score, Signal
- Add validation

### **Phase 2: Base Classes (1 day)**
- Implement base_engine.py
- Implement data_source.py
- Create engine skeletons (empty)

### **Phase 3: TIER 1 - Foundation (5-7 days)**
- trend_engine.py (logic)
- structure_engine.py (logic)
- strength_engine.py (logic)
- volatility_engine.py (logic)
- liquidity_engine.py (logic)
- Unit tests (5 files)

### **Phase 4: TIER 2-4 (7-10 days)**
- Implement 8 engines (T2-4)
- Unit tests (8 files)

### **Phase 5: TIER 5 (10-14 days) ⭐ MOST COMPLEX**
- Implement 7 behavior engines
- Unit tests (7 files)
- RESPONSIBILITY_MATRIX.md

### **Phase 6: TIER 6-8 + Orchestration (7-10 days)**
- Implement context_synthesizer (GATEWAY)
- Implement probability_inference
- Implement scoring layers
- Implement pipeline + execution_gate
- Unit tests (8 files)

### **Phase 7: Data Layer (3-4 days)**
- Implement data_source, IQ Option adapter, dummy_data
- Integration tests

### **Phase 8: Strategy (5-7 days)**
- base_strategy, strategy_registry
- V1 compression breakout strategy
- Entry/block rules
- Integration tests

### **Phase 9: Execution + Monitoring (5-7 days)**
- broker_adapter, executor, order_manager, position_sizer
- logger, performance_monitor, notifier, reporter
- Integration tests

### **Phase 10: Testing + Documentation (5-7 days)**
- Backtest framework
- Full E2E testing
- Complete documentation
- Performance optimization

---

## ✅ Key Changes from v2.0 to v2.1

| Change | Detail |
|--------|--------|
| ✏️ Rename | orderflow_analyzer → market_pressure_analyzer |
| ✏️ Clarify | probability_estimator → context_probability_inference |
| ✏️ Critical | execution_gate default = NO_SIGNAL (not CALL/PUT) |
| ✏️ Enforce | MarketContext frozen (immutable) |
| ✏️ Add | RESPONSIBILITY_MATRIX.md document |
| ✏️ Structure | tests/unit/ → folder-based organization |
| ✏️ Isolate | execution/ receives Signal only (never imports core) |
| ✏️ Document | 30 engine responsibilities + boundaries |
| ✏️ Defer | engines/ refactoring to future phases |

---

## 🎬 GO/NO-GO STATUS

```
═══════════════════════════════════════════════════════════
✅ ARCHITECTURE v2.1 APPROVED - READY FOR IMPLEMENTATION
═══════════════════════════════════════════════════════════

Status: READY TO CODE
Next: Phase 0 Setup

Boss: Ready to build? 🚀
```

---

**Project:** BOT_FINALBOT  
**Version:** 2.1-final (Architecture)  
**Owner:** Boss  
**Build:** Joy (Claude)  
**Date:** May 19, 2026  
**Total Files:** 151  
**Total Engines:** 30  
**Total Layers:** 5  
**Timeline:** 8-10 weeks to MVP

---

## 🗡️ บทบัญญัติการปฏิบัติตามวินัย Buso (มีผลใช้งานจริง 100%)

ระบบได้รับการพัฒนาและแก้ไขรอยต่อ (System Refactoring) จนกระทั่งมีความ **"แตกฉาน"** ตรงตามหลักการของคัมภีร์ทั้งหมดเรียบร้อยแล้ว ดังนี้:

### 1. **สัจธรรม "ตลาดต้องมาก่อนกลยุทธ์" (Market-First Execution)**
- **การป้อนข้อมูลข้ามสมองกล:** ปรับปรุง `ContextBuilder` ให้ส่งต่อผลวิเคราะห์ระดับสูงของ Tier 1 (ทิศทาง, ความแรงเทรนด์, ความผันผวน, แนวรับแนวต้าน) เข้าไปประมวลผลต่อใน Tier 2 (`MarketStateClassifier`) โดยสมบูรณ์ เพื่อลดจุดบอดในการจำแนกประเภทตลาด
- **การบังคับเงื่อนไขตามสภาวะตลาด:** ปรับปรุงระบบคัดกรองสัญญาณในกลยุทธ์ `CompressionBreakoutStrategy` ในฟังก์ชัน `is_eligible` ให้ทำหน้าที่เช็กสภาวะตลาดจริงก่อนเข้าเทรด หากสภาพตลาด ณ แท่งปัจจุบันไม่อยู่ในกลุ่มสภาวะสะสมพลังและการระเบิดกรอบ (`BREAKOUT_EMERGING` หรือ `ACCUMULATION`) **ระบบจะปฏิเสธการเทรดโดยสิ้นเชิง (The Art of Saying NO)**

### 2. **การทำงานแบบรันสดเท่านั้น (No Mock Bypasses)**
- **ปิดระบบจำลอง (use_mock = False):** ล็อกค่าการทำงานของ Adapter และ Executor ให้รันเชื่อมโยงข้อมูลจริงจากโบรกเกอร์ (Real WebSocket & REST API) เท่านั้น โดยตัดการจำลองข้อมูล/คำสั่งซื้อขายหลอกออก 100% เพื่อหลีกเลี่ยงความสับสนและป้องกันเงินทุนจริง
- **การส่งสัญญาณใน Python Console:** บอทรองรับโหมด `SIGNALBOT` (แสดงสัญญาณกล่อง ASCII สวยงามทางคอนโซลเท่านั้นโดยไม่กดส่งไม้จริงทั้งเงินจริงและเดโม่) และพร้อมสลับเป็น `AUTOBOT` (ยิงออเดอร์ตรงไปยังพอร์ต PRACTICE/REAL ของโบรกเกอร์) ได้ทันทีเมื่อกำหนดค่าผ่าน `settings.json` โดยไม่ไปแตะต้องระบบการเข้ารหัสบัญชีเดิมเพื่อคงความปลอดภัยสูงสุดไว้

**วันสิ้นสุดภารกิจ:** 28 พฤษภาคม 2026  
**ผู้เย็บรอยต่อสุดท้าย:** Antigravity (Gemini)  
**สถานะคัมภีร์:** ผ่านการตรวจสอบและรันจริงผ่านระบบสำเร็จลุล่วง 100% 🏆👔


