# FINALSignal_BOT — Continuation Guide for Phase 0

**Status:** Architecture Approved | Pre-Coding | Phase 0 Ready
**Date Created:** May 18, 2026
**For:** Chat Continuation — New Session Context

---

## 1. Executive Summary

### Current Status
```
Architecture       ✅ Approved (8 Tiers, 29 Modules)
Blueprint          ✅ Complete (100% specification)
Code               ❌ Not started (0 lines)
Integration        ❌ Not started
Backtest           ❌ Not started

Next Step: Phase 0 — Tier 1 Coding (5 core engines)
Timeline: ~2-3 weeks to Phase 1
Goal: Teach bot to read market (Intelligence OS foundation)
```

### What's Ready Now
- ✅ Full architecture designed
- ✅ All decisions made
- ✅ Integration points defined
- ✅ V1 strategy locked in
- ✅ Config specifications finalized

### What's NOT Ready Yet
- ❌ 29 modules not coded
- ❌ MarketContext object not built
- ❌ Strategy logic not implemented
- ❌ signal_veto gate not created
- ❌ IQ Option adapter not connected

---

## 2. Core Philosophy — FINALBOT Principles

### The 4 Laws (ศรัทธาของระบบ)

```
Law 1: "ตลาดเป็นคนเลือกกลยุทธ์"
       Market State → determines which strategy activates
       NOT: Strategy decides what market looks like

Law 2: "กลยุทธ์เป็นคนเสนอคะแนน"
       Strategy outputs Entry Score + Block Score
       NOT: Strategy outputs CALL/PUT directly

Law 3: "คะแนนไม่ใช่คำสั่งเทรด"
       Scores are advisory only (0-100)
       NOT: Score > threshold = automatic trade

Law 4: "และสุดท้าย 'กฎของระบบ' มีอำนาจสูงสุด"
       signal_veto.py = final decision gate (only authority)
       Checks: Cooldown, Daily Cap, Market Quality, Confidence
```

### Architecture Philosophy
- **Single Responsibility** — Each layer owns one decision
- **No Overlap** — No layer duplicates another's computation
- **No Circular Logic** — Data flows downward only
- **Centralized Authority** — signal_veto is ONLY signal emitter
- **Explainability** — Every decision comes with reasoning

---

## 3. Architecture Overview — 8 Tiers / 29 Modules

### Layer Structure

```
┌─────────────────────────────────────────────────────┐
│ L0: DATA LAYER (IQ Option API)                      │
│     Raw OHLCV data from broker                      │
├─────────────────────────────────────────────────────┤
│ L1: INTELLIGENCE OS (8 Tiers, 29 Modules)           │
│   ├─ T1 Foundation (5)     → Observe market         │
│   ├─ T2 Classification (2) → State + Quality        │
│   ├─ T3 Price Action (2)   → Candle behavior        │
│   ├─ T4 Detection (4)      → Risk filters           │
│   ├─ T5 Behavior (7) ⭐    → Market cognition       │
│   ├─ T6 Context (2) ⭐     → Synthesis gateway      │
│   ├─ T7 Quality (2)        → Confidence             │
│   └─ T8 Utilities (3)      → Shared infra           │
├─────────────────────────────────────────────────────┤
│ L2: STRATEGY LAYER (5 templates, V1 = 1 active)    │
│     Read-only access to MarketContext               │
├─────────────────────────────────────────────────────┤
│ L3: RISK & DECISION (signal_veto = final gate)     │
│     Size, SL, TP, approval checks                   │
├─────────────────────────────────────────────────────┤
│ L4: EXECUTION & OUTPUT (IQ Option API orders)       │
│     Send signals, logging, notifications            │
└─────────────────────────────────────────────────────┘

Data Flow: STRICTLY DOWNWARD
No layer writes backward
```

### Tier 1 — Foundation (PHASE 0 START)

| Module | Purpose | Output |
|---|---|---|
| **trend_intelligence.py** | Detect direction & slope | direction, strength, type, confidence |
| **strength_intelligence.py** | Measure momentum | adx, rsi, macd, momentum_level |
| **volatility_intelligence.py** | Measure ATR/BBW regime | regime, percentile, spike_detected |
| **structure_intelligence.py** | Find S/R & BOS | support, resistance, bos_detected |
| **mtf_intelligence.py** | Cross-TF alignment | harmony, htf_direction, conflicts |

**Tier 1 Output → MarketContext (shared data object)**

---

## 4. V1 Strategy — 5M Volatility Compression Breakout

### Strategic Profile
```
Activation: Market State = BREAKOUT_EMERGING
TriggerType: Volatility compression → breakout expansion
EntrySignal: BreakoutQuality ≥ 70%
BlockSignal: TrapProbability > 40% OR Noise > 50%
Timeframe: M5 (5-minute candles)
Expiry: M5 bar (fixed, ~5 minutes)
RiskProfile: Conservative (wait for full setup)
```

### 14 Core Requirements

```
1. ATR Compression Detection           ✅ (Volatility Intel)
2. Volatility Contraction Analysis     ✅ (Volatility Intel)
3. Compression Box Structure           ⚠️ (Needs Box Duration Tracker)
4. Breakout Quality Scoring            ✅ (95% ready)
5. Breakout Participation              ✅ (90% ready)
6. Fake Breakout Filtering             ✅ (Trap Detector)
7. Momentum Expansion Confirmation     ✅ (Strength Intel)
8. Candle Efficiency Analysis          ✅ (Efficiency Intel)
9. Noise Filtering                     ✅ (Noise Detector)
10. Market Quality Validation          ✅ (Regime Scorer)
11. HTF Bias Confirmation              ✅ (MTF Intel)
12. Continuation Probability           ✅ (Continuation Analyzer)
13. Liquidity Trap Rejection           ✅ (Trap Detector)
14. Context-aware Entry Filtering      ⚠️ (Needs Retest Analyzer)

Coverage: 95% → Need 4 enhancements for 100%
```

### 4 Enhancements (Post Phase 0)

```
1. Box Duration Tracker
   Effort: 1-2 days | Difficulty: 1/10
   Adds to: Tier 2 (Market State Classifier)
   
2. Compression Pattern Classifier
   Effort: 2-3 days | Difficulty: 3/10
   Adds to: Tier 5 (new engine)
   
3. Retest Analyzer
   Effort: 3-4 days | Difficulty: 4/10
   Adds to: Tier 5 (new engine)
   
4. Expansion Persistence Module
   Effort: 3-4 days | Difficulty: 4/10
   Adds to: Tier 5 (new engine)

Total: 14-17 days additional work
```

### Entry Logic (Simple)

```
IF MarketContext.compression_exhaustion > 75%
   AND MarketContext.breakout_quality > 70%
   AND MarketContext.trap_probability < 40%
   AND MarketContext.noise_level < 50%
   THEN
     Entry_Score = weighted(compression, breakout, trap_rejection)
     IF Entry_Score > 70 THEN → send to signal_veto
```

### Block Logic

```
Block if ANY:
├─ Trap probability dominant
├─ Regime quality below threshold
├─ Market confidence < 40%
├─ Market state = UNCLEAR
├─ Conflict severity high
└─ Liquidity trap detected
```

---

## 5. IQ Option Mechanics & Configuration

### Product Types

**Digital Option** (V1 Choice)
```
Payout: 82% base
        85-86% during high volatility (14:00 LT)
Expiry: M5 bar (fixed at bar close)
Entry:  Immediate upon signal
Exit:   Automatic at bar expiry (5 min from bar start)
```

**Binary Option** (Optional, future)
```
Payout: [Boss to specify]
Expiry: Flexible (1 min to 1 hour+)
Entry:  Immediate upon signal
Exit:   Can close early or wait expiry
```

### M5 Expiry Structure

```
Bar 1: 05:00 - 05:05
Bar 2: 05:05 - 05:10
Bar 3: 05:10 - 05:15
...etc

Entry at 05:03 → Closes at 05:05 (end of current bar)
Entry at 05:06 → Closes at 05:10 (end of next bar)
= FIXED to bar boundary (no flexibility)
```

### Configuration (config.json)

```json
{
  "iq_option": {
    "email": "your_email@gmail.com",
    "password": "your_password",
    "account_type": "PRACTICE"  // PRACTICE or REAL
  },
  "trading": {
    "product_type": "DIGITAL_OPTION",
    "default_expiry": "M5",
    "default_amount": 30,
    "max_trades_per_day": 2,
    "cooldown_minutes": 20
  },
  "symbols": [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "NZDUSD"
  ],
  "market_hours": {
    "start": "17:00",
    "end": "23:00",
    "timezone": "LT"  // Local Time
  }
}
```

### Runtime Flexibility

```
Can Change During Bot Execution:
├─ Product Type    (DIGITAL ↔ BINARY)
├─ Expiry          (M5 ↔ M15 ↔ M60)
├─ Amount          (30 ↔ 50 ↔ 100 THB)
├─ Market Hours    (extend/restrict)
└─ Symbol Whitelist (add/remove pairs)

Cannot Change:
├─ API credentials (restart needed)
└─ Account type    (PRACTICE ↔ REAL)
```

---

## 6. Phase 0 Task — Tier 1 Implementation

### What Needs to Be Done

**Write 5 Python modules:**

```
core/intelligence/tier_1/
├─ trend_intelligence.py
├─ strength_intelligence.py
├─ volatility_intelligence.py
├─ structure_intelligence.py
└─ mtf_intelligence.py
```

### Each Module Structure

```python
# Example: trend_intelligence.py

class TrendIntelligence:
    def __init__(self, config):
        self.config = config
        self.ema_periods = [20, 50, 100, 200]
    
    def analyze(self, candles_df):
        """
        Input: DataFrame with OHLCV data
        Output: Dict with trend analysis
        """
        return {
            'direction': 'UP|DOWN|NONE',
            'strength': 0-100,
            'slope': float,
            'type': 'IMPULSIVE|CORRECTIVE|CHOPPY',
            'confidence': 0-100,
            'reversal_risk': 0-100,
            'sustain_probability': 0-100,
        }
```

### Output Format (MarketContext)

```python
MarketContext = {
    'trend': { ... },                 # From T1
    'strength': { ... },              # From T1
    'volatility': { ... },            # From T1
    'structure': { ... },             # From T1
    'mtf': { ... },                   # From T1
    
    # Later (T2-7):
    'market_state': { ... },
    'behavior': { ... },
    'recommendation': { ... },
    # ...
}
```

### Dependencies (Tier 1 Only)

```
No Tier 1 module depends on another Tier 1 module
├─ All read raw candle data
├─ All write to MarketContext independently
├─ Can run in parallel
└─ No blocking dependencies
```

### Integration Points

```
Input:  IQ Option Adapter
        └─ fetch_ohlcv(symbol, timeframe, lookback)
        
Process: Tier 1 Analysis (5 modules parallel)

Output: MarketContext object
        └─ passed to Tier 2 (Classification)
```

### Success Criteria

```
✅ All 5 T1 modules written
✅ Each module outputs correct schema
✅ MarketContext fully populated from T1
✅ No crashes with real IQ Option data
✅ Cycle time < 15 seconds for 5 pairs
✅ Confidence scores reasonable (0-100)
```

---

## 7. Code Skeleton Template

### Tier 1 Module Template

```python
# core/intelligence/tier_1/trend_intelligence.py

from dataclasses import dataclass
from typing import Dict, Any
import numpy as np
import pandas as pd

@dataclass
class TrendOutput:
    direction: str              # 'UP', 'DOWN', 'NONE'
    strength: int              # 0-100
    slope: float
    type: str                  # 'IMPULSIVE', 'CORRECTIVE', 'CHOPPY'
    confidence: int            # 0-100
    reversal_risk: int         # 0-100
    sustain_probability: int   # 0-100

class TrendIntelligence:
    """Tier 1: Detect market direction and slope"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ema_periods = [20, 50, 100, 200]
    
    def analyze(self, candles_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze price direction
        
        Input:
            candles_df: DataFrame with columns [open, high, low, close, volume]
            Index: datetime
        
        Output:
            Dict with trend analysis
        """
        try:
            # Step 1: Calculate EMAs
            ema20 = candles_df['close'].ewm(span=20).mean()
            ema50 = candles_df['close'].ewm(span=50).mean()
            ema100 = candles_df['close'].ewm(span=100).mean()
            ema200 = candles_df['close'].ewm(span=200).mean()
            
            # Step 2: Determine direction
            price_latest = candles_df['close'].iloc[-1]
            direction = self._determine_direction(
                price_latest, ema20.iloc[-1], ema50.iloc[-1], 
                ema100.iloc[-1], ema200.iloc[-1]
            )
            
            # Step 3: Calculate slope
            slope = self._calculate_slope(candles_df['close'].tail(10))
            
            # Step 4: Determine type (IMPULSIVE vs CORRECTIVE)
            candle_type = self._analyze_candle_type(candles_df)
            
            # Step 5: Confidence scoring
            confidence = self._score_confidence(
                direction, slope, ema20.iloc[-1], ema50.iloc[-1]
            )
            
            return {
                'direction': direction,
                'strength': self._calculate_strength(slope),
                'slope': float(slope),
                'type': candle_type,
                'confidence': confidence,
                'reversal_risk': self._calculate_reversal_risk(candles_df),
                'sustain_probability': self._calculate_sustain_prob(candles_df),
            }
        except Exception as e:
            # Log error, return neutral state
            print(f"❌ TrendIntelligence error: {e}")
            return self._neutral_state()
    
    def _determine_direction(self, price, ema20, ema50, ema100, ema200) -> str:
        """Determine UP, DOWN, or NONE"""
        if price > ema20 > ema50 and ema50 > ema100:
            return 'UP'
        elif price < ema20 < ema50 and ema50 < ema100:
            return 'DOWN'
        else:
            return 'NONE'
    
    def _calculate_slope(self, prices) -> float:
        """Linear regression slope"""
        x = np.arange(len(prices))
        y = prices.values
        slope = np.polyfit(x, y, 1)[0]
        return slope
    
    def _analyze_candle_type(self, df) -> str:
        """Return IMPULSIVE, CORRECTIVE, or CHOPPY"""
        # Implementation here
        return 'IMPULSIVE'  # placeholder
    
    def _score_confidence(self, direction, slope, ema20, ema50) -> int:
        """0-100 confidence score"""
        # Implementation here
        return 75  # placeholder
    
    def _calculate_strength(self, slope) -> int:
        """Convert slope to 0-100"""
        return min(100, max(0, int(abs(slope) * 100)))
    
    def _calculate_reversal_risk(self, df) -> int:
        """0-100 risk of reversal"""
        # Implementation here
        return 25  # placeholder
    
    def _calculate_sustain_prob(self, df) -> int:
        """0-100 probability trend sustains"""
        # Implementation here
        return 75  # placeholder
    
    def _neutral_state(self) -> Dict[str, Any]:
        """Return neutral/safe state on error"""
        return {
            'direction': 'NONE',
            'strength': 0,
            'slope': 0.0,
            'type': 'CHOPPY',
            'confidence': 0,
            'reversal_risk': 50,
            'sustain_probability': 50,
        }
```

### Integration with Adapter

```python
# core/broker/iq_option_adapter.py

class IQOptionAdapter:
    """Bridge between IQ Option API and bot"""
    
    def fetch_ohlcv(self, symbol: str, timeframe: str, 
                    lookback: int) -> pd.DataFrame:
        """
        Fetch candlestick data from IQ Option
        
        Args:
            symbol: 'EURUSD', 'GBPUSD', etc.
            timeframe: 'M1', 'M5', 'M15', 'M60', 'D1'
            lookback: number of candles to fetch
        
        Returns:
            DataFrame with columns [open, high, low, close, volume]
            Index: datetime (UTC)
        """
        # Implementation: call IQ Option API
        # Return formatted DataFrame
        pass

# core/intelligence/market_context_builder.py

class MarketContextBuilder:
    """Assemble MarketContext from Tier 1 outputs"""
    
    def __init__(self, tier1_engines: Dict[str, Any]):
        self.tier1 = tier1_engines
    
    def build(self, symbol: str, candles: Dict[str, pd.DataFrame]) -> Dict:
        """
        Build MarketContext from Tier 1 analysis
        
        Args:
            symbol: trading pair
            candles: dict of {timeframe: DataFrame}
        
        Returns:
            MarketContext object (dict)
        """
        context = {
            'symbol': symbol,
            'timestamp': pd.Timestamp.now(),
            'trend': self.tier1['trend'].analyze(candles['M5']),
            'strength': self.tier1['strength'].analyze(candles['M1']),
            'volatility': self.tier1['volatility'].analyze(candles['M5']),
            'structure': self.tier1['structure'].analyze(candles['M15']),
            'mtf': self.tier1['mtf'].analyze(candles),  # all TF
        }
        return context
```

---

## 8. Key Decisions Made (Locked In)

```
✅ Data Source
   Decision: IQ Option API
   Reason: Real-time, no MT4 file dependency
   
✅ Product Type (V1)
   Decision: Digital Option
   Reason: Higher payout (82-86%)
   
✅ Expiry (V1)
   Decision: M5 (fixed bar)
   Reason: Matches 5M Compression Breakout strategy
   
✅ Default Trade Amount
   Decision: 30 THB per trade
   Reason: 2,000 THB capital, max 2 trades/day
   
✅ Concurrent Pairs
   Decision: 5 pairs (EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD)
   Reason: Diversification without bloat
   
✅ Parallel Execution
   Decision: 1 Thread per pair
   Reason: No data contention, independent analysis
   
✅ Architecture Pattern
   Decision: 8 Tiers, 29 Modules, Single MarketContext
   Reason: Separation of concerns, no decision overlap
   
✅ Signal Authority
   Decision: signal_veto.py ONLY
   Reason: Prevent CALL/PUT from strategy or other layers
   
✅ V1 Strategy
   Decision: 5M Volatility Compression Breakout
   Reason: Clear setup, testable, fits architecture
```

---

## 9. Questions for Next Chat (To Be Decided)

### Q1: Tier 1 Implementation Approach
```
Option A: Extract logic from old bot (v5_FULL)
          + Faster
          - May not fit new architecture perfectly

Option B: Write Tier 1 from scratch
          + Clean, fits architecture
          - Slower (1-2 weeks)

Option C: Hybrid (reference old logic, rewrite)
          + Balanced
          - Need careful mapping

→ Boss decision needed
```

### Q2: Timeframe Strategy (Multiple Pairs)
```
Question: Should Tier 1 analyze all timeframes
          for each pair, or just M5?

Current: Each module gets M1, M5, M15, M60, D1

Optimized: Each module gets only needed TF
           (trend: M5, MTF: M1-D1, etc.)

→ Boss confirmation needed
```

### Q3: Error Handling & Fallback
```
Question: If IQ Option API is slow/fails,
          how should bot behave?

Options:
A. Skip trade cycle, retry next minute
B. Use cached data from previous minute
C. Send alert, wait manual confirmation
D. Other?

→ Boss preference needed
```

### Q4: Monitoring & Logging
```
Question: What level of logging during Phase 0?

Minimal:  Only CALL/PUT signals
Standard: + each Tier 1 engine output
Verbose:  + every calculation step
Debug:    + all intermediate values

→ Boss preference needed (impacts performance)
```

---

## 10. Next Steps (Phase 0 Roadmap)

### Immediate (This Chat)
```
1. Confirm implementation approach (Q1)
2. Start coding Tier 1 modules
3. Write unit tests for each module
4. Integrate with MarketContext builder
```

### Week 1 (T1 Complete)
```
5. Test T1 with real IQ Option data
6. Validate output schema and ranges
7. Performance tune (target <15s per cycle)
8. Document each module
```

### Week 2 (T2-T4)
```
9. Code Tier 2 (Classification)
10. Code Tier 3 (Price Action)
11. Code Tier 4 (Detection)
12. Integrate into unified flow
```

### Week 3 (T5-T8)
```
13. Code Tier 5 (Behavior) ⭐ MOST COMPLEX
14. Code Tier 6 (Context)
15. Code Tier 7 (Quality)
16. Code Tier 8 (Utilities)
17. Full integration test
```

### Week 4-6 (Phases 1-5)
```
Phase 0.5: V1 Enhancements (4 modules)
Phase 1: Strategy Framework (5 templates, V1 = 1 active)
Phase 2: Risk Layer + signal_veto
Phase 3: Execution + IQ Option integration
Phase 4: Config system
Phase 5: Backtest + optimization
```

---

## 11. File Organization (Expected)

```
FINALSignal_BOT/
├─ config/
│  ├─ config.json              # Trading parameters
│  ├─ symbols.txt              # List of pairs
│  └─ context_rules.json       # Filter rules (future)
│
├─ core/
│  ├─ broker/
│  │  ├─ iq_option_adapter.py  # IQ Option API wrapper
│  │  └─ websocket_handler.py  # Real-time data
│  │
│  ├─ intelligence/
│  │  ├─ tier_1/
│  │  │  ├─ trend_intelligence.py
│  │  │  ├─ strength_intelligence.py
│  │  │  ├─ volatility_intelligence.py
│  │  │  ├─ structure_intelligence.py
│  │  │  └─ mtf_intelligence.py
│  │  │
│  │  ├─ tier_2/ (later)
│  │  ├─ tier_3/ (later)
│  │  └─ ... (other tiers)
│  │
│  ├─ market_context.py        # MarketContext object
│  ├─ strategy_framework.py    # 5 templates
│  ├─ signal_veto.py           # FINAL decision gate
│  └─ execution_engine.py      # Send orders
│
├─ utils/
│  ├─ math_tools.py            # Calculations
│  ├─ time_tools.py            # Timestamps
│  └─ logging_tools.py         # Log management
│
├─ tests/
│  ├─ test_tier1.py
│  ├─ test_integration.py
│  └─ backtest/ (future)
│
├─ logs/
│  ├─ signals.csv              # All CALL/PUT
│  ├─ errors.log               # Errors
│  └─ performance.csv          # Metrics
│
├─ docs/
│  ├─ ARCHITECTURE.md
│  ├─ STRATEGY_V1.md
│  └─ API_REFERENCE.md
│
├─ main.py                      # Entry point
└─ requirements.txt
```

---

## 12. Critical Reminders

```
🔴 HARD RULES (Cannot Break)

1. signal_veto.py = ONLY signal emitter
   → No other module sends CALL/PUT
   
2. MarketContext = Single Source of Truth
   → Only one MarketContext per cycle
   → All modules read from it, none write during strategy/veto
   
3. Layer separation is STRICT
   → Intelligence doesn't know about Strategy
   → Strategy doesn't know about Risk
   → Risk doesn't know about Execution
   
4. No backwards data flow
   → Data flows: L0 → L1 → L2 → L3 → L4
   → Never: L3 → L1 (no feedback)
   
5. Confidence scores REQUIRED
   → Every output field must have confidence (0-100)
   → Never output raw values without confidence
   
6. Phase 0 must complete before Phase 1
   → Cannot skip modules
   → Cannot merge phases

🟡 IMPORTANT NOTES

• Tier 5 (Behavior) is most complex — start there early
• Tier 6 (Context) is bottleneck — optimize first
• Test often, especially edge cases (ATR spike, no volume, etc.)
• MarketContext schema is FROZEN — don't add fields without approval
```

---

## 13. Success Criteria (Phase 0 Complete)

```
✅ All 29 modules written and tested
✅ MarketContext fully populated every cycle
✅ Cycle time < 15 seconds (5 pairs)
✅ Confidence scores: 0-100 (not NaN, not >100)
✅ No crashes with 1 hour real IQ Option data
✅ Output explainable (can trace why signal was sent)
✅ Documentation complete (each module)
✅ Ready for Phase 1 (Strategy Integration)
```

---

## END OF CONTINUATION GUIDE

**This document contains everything needed to continue development in a new chat session.**

For the next chat:
1. Upload this file
2. Ask Claude to load context
3. Confirm understanding
4. Continue Phase 0 Tier 1 coding

---

**Project:** FINALSignal_BOT  
**Version:** Pre-Phase 0  
**Status:** Ready for Coding  
**Next Action:** Begin Tier 1 Implementation

**Created by:** Joy (Claude)  
**For:** Boss (Project Owner)  
**Date:** May 18, 2026
