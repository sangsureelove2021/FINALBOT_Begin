# 🤖 FINALBOT MASTER BLUEPRINT: SYNTHESIZED ARCHITECTURE

> [!IMPORTANT]
> This document represents the fully synthesized production baseline of the FINALBOT architecture, covering the Intelligence OS, Pipeline OS, Scoring Systems, and the 14 M5 Binary trading strategies.

## 1. 🧠 Core Architecture

### Intelligence OS
The **Intelligence OS** acts as the contextual brain of FINALBOT. It runs continuously, analyzing multiple market dimensions (Volatility, Trend, Momentum, Structure, Multi-Timeframe) to generate real-time metrics and classify the current Market State. It ensures the trading system operates with context-awareness rather than relying on isolated indicator signals.

### Pipeline OS
The **Pipeline OS** is the sequential execution framework that orchestrates the flow from data ingestion to signal generation.
1. **Pre-Flight Check**: Validate broker feed, spread, and economic news calendars.
2. **Market State Verification**: Ensure the current state is not blacklisted.
3. **Strategy Evaluation**: Run the eligible strategies through their specific logic gates.
4. **Signal Confidence Scoring**: Calculate dynamic Entry and Block scores.
5. **Execution & Output**: Dispatch the final signal formatted via the Frozen Output Schema.

### Market States 📊
FINALBOT categorizes the market into distinct regimes to dynamically route strategy execution:

| ✅ Suitable States | ❌ Blocked States |
| :--- | :--- |
| `BREAKOUT_EMERGING` | `TRENDING_STRONG` |
| `ACCUMULATION` | `TRENDING_WEAK` |
| `SIDEWAY_RANGE` | `LIQUIDITY_VOID` |
| `REVERSAL_FORMING` | `CHOPPY_UNCERTAIN` |
| `DISTRIBUTION` | `TRANSITIONAL` / `UNCLEAR` |

---

## 2. 🧮 The Scoring System
The system uses a highly mathematical confidence model to approve or reject signals, ensuring high-probability M5 entries.

### 🟢 Entry Score (0-100)
- **Base Score:** 50 points.
- **Bonus Factors (up to +50):** 
  - Trend Strength: `Min(20, trend_strength / 5)`
  - Expansion Probability: `Min(15, expansion_probability / 7)`
  - MTF Alignment: `Min(10, alignment_score / 10)`
  - Quality Multipliers: Box Duration/Quality (+15) and Retest/Rejection Quality (+15).
- *Total is capped at a maximum of 100 points.*

### 🔴 Block Score (0-100)
- **Soft Blocks (Accumulated):** Trap Detection (+30), Noise Level (+20), Exhaustion Risk (+15), Reversal Risk (+15), Fatigue Risk (+20).
- **Hard Blocks (Instant 100):** Market State Blocked, Extreme Volatility, High Impact News (±15 mins), Anomaly Detected, Broker Feed Freeze.
- *Calculation:* `Confidence = Entry_Score * (1 - Block_Score / 200)`

### 🎯 Strategy Confidence (C_strategy)
Calculated continuously (0.0 to 1.0) using sub-scores:
`C_strategy = (0.40 × S_vol) + (0.30 × S_str) + (0.30 × S_mtf)`
*Signals fire only when the confidence exceeds strict thresholds.*

---

## 3. ⚔️ The 14 Trading Strategies

FINALBOT utilizes 14 distinct strategies, systematically categorized into Breakout, Reversal, and Trend modules.

### 🚀 Breakout Group
1. **COMPRESSION BREAKOUT:** Detects volatility squeezes (`atr_percentile <= 30`) followed by explosive expansion and Break of Structure (BOS). Targets `ACCUMULATION` and `BREAKOUT_EMERGING` states.

### 🔄 Reversal Group A (Price Action & Structure)
2. **PA SNR STRATEGY:** Trades sharp reversals at key Support/Resistance levels confirmed by raw price action.
3. **PIN BAR SCALPER:** Looks for strong rejection pin bars at local extremes, capitalizing on immediate liquidity sweeps.
4. **REJECTION 5M PA:** Identifies momentum rejection candles across the 5M timeframe for mean-reversion.
5. **SR FAKEOUT REJECTION:** Trades false breakouts (fakeouts) at major S/R boundaries where retail traps are triggered.

### 📉 Reversal Group B (Oscillator Confluence)
6. **BB RSI CONFLUENCE:** Combines Bollinger Band extreme touches with RSI divergence and overbought/oversold alignments.
7. **RSI EXTREME BOUNCE:** Capitalizes on RSI entering extreme zones (<20 or >80) and immediately snapping back.
8. **RSI REVERSAL:** Standard RSI divergence and level-crossing reversal strategy for standard ranging markets.

### ⚡ Reversal Group C (Momentum/Stochastic)
9. **ENGULFING MOMENTUM SCALPER:** Trades engulfing candlestick patterns forming precisely at momentum exhaustion inflection points.
10. **STOCHASTIC CROSSOVER:** Uses Stochastic Oscillator %K/%D crossovers in overbought/oversold regions for precision reversal timing.

### 📈 Trend Group
11. **EMA CROSSOVER:** Classic moving average crossover logic aligned strictly with the Higher Time Frame (HTF) trend direction.
12. **EMA RIBBON MOMENTUM:** Utilizes an EMA ribbon expansion to confirm strong directional momentum and ride the trend.
13. **MACD CROSSOVER:** Uses MACD histogram momentum and signal line crossovers to capture primary trend continuation.
14. **TRIPLE CONFLUENCE:** A high-conviction trend strategy requiring absolute alignment of Trend, Volatility, and Momentum indicators simultaneously.

---

## 4. ⚙️ Production Rules & Schema

### 🛡️ PRODUCTION M5 BINARY Baseline
> [!WARNING]
> These rules are absolute and must not be bypassed by any strategy or module.

1. **Strict M5 Evaluation:** All models evaluate exactly on the M5 timeframe, with expiry set to 1 M5 candle (5 minutes).
2. **Zero Repaint Policy:** Signals are exclusively processed at the *open* of a new candle using finalized data from the previous closed candle.
3. **Fail Fast Architecture:** If any pre-flight or hard block condition is met, strategy evaluation stops instantaneously.

### 📝 Frozen Output Schema (JSON)
All 14 strategies must compile their output into the following strictly typed JSON payload:

```json
{
  "timestamp": "2026-06-07T10:45:00Z",
  "symbol": "EURUSD",
  "strategy_id": "compression_breakout",
  "signal_direction": "CALL",
  "confidence_score": 85.5,
  "market_state": "BREAKOUT_EMERGING",
  "entry_score": 90,
  "block_score": 10,
  "fail_reason_code": "NONE",
  "audit_id": "REQ-102938"
}
```
