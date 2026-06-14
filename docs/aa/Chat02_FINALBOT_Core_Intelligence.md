# Trading Intelligence OS - Core Architecture

## 1. System Overview

ระบบนี้เป็น "Market Intelligence Platform" ไม่ใช่ trading bot แบบทั่วไป โดยมีเป้าหมายหลักคือการสร้างความเข้าใจตลาด (market cognition) ก่อนการตัดสินใจเทรด

ระบบถูกออกแบบให้เป็น modular intelligence system ที่แยก analysis engines ออกจาก strategy layer อย่างชัดเจน

## 2. Core Architecture Layers

### Layer 1: Data Foundation
- Candle Data Ingestion
- Market Feed Normalization
- Multi-Timeframe Alignment

### Layer 2: Market Intelligence Engines
- Structure Intelligence
- Volatility Intelligence
- Liquidity Intelligence
- Price Action Engine
- Noise Filter Engine

### Layer 3: State & Context Layer
- Market State Classifier
- Context Generator
- Regime Detection
- Shared Context Memory

### Layer 4: Scoring Layer
- Quality Score Engine
- Confidence Scoring
- Conflict Detection Score
- Fakeout Probability Model

### Layer 5: Strategy Layer
- Strategy Plugins (external modules)
- Signal Interpretation Layer
- Entry/Exit Decision Interface

## 3. Engine Responsibility Map

### Structure Intelligence
- Market structure (HH, HL, LH, LL)
- BOS / CHOCH detection
- Trend vs range classification

### Volatility Intelligence
- ATR behavior
- Compression / expansion cycles
- Volatility regime classification

### Liquidity Intelligence
- Stop hunt detection
- Equal high/low mapping
- Liquidity sweep identification

### Price Action Engine
- Candle classification
- Wick/body analysis
- Momentum candle detection

### Noise Filter
- Chaotic market detection
- Low-quality movement filtering
- Signal contamination scoring

## 4. Shared Context Architecture

All engines write into a shared context object:
- market_state
- volatility_state
- structure_state
- liquidity_state
- price_action_state
- noise_level
- confidence_score

Context is NOT isolated per engine but aggregated centrally.

## 5. Intelligence Flow

1. Data Ingestion
2. Parallel Engine Processing
3. Context Aggregation
4. Conflict Detection
5. Scoring Layer Execution
6. Strategy Access Layer
7. Decision Output (Signal or NO SIGNAL)

## 6. Scoring & Block Flow

- Each engine outputs score + confidence
- Scoring layer aggregates all signals
- Conflict layer can override scoring

**Rules:**
- High conflict → NO SIGNAL
- Low market quality → NO SIGNAL
- Low confidence → NO SIGNAL

## 7. Strategy Integration Model

Strategy is treated as a plugin:
- Reads shared context only
- Cannot modify core engines
- Cannot override block layer
- Outputs probabilistic decision only

**Strategy examples:**
- Trend Pullback
- Compression Breakout
- Liquidity Sweep Reversal

## 8. Phase-by-Phase Roadmap

### Phase 0 (Core Brain)
- Structure Intelligence
- Volatility Intelligence
- Market State Classifier
- Price Action Engine
- Liquidity Intelligence
- Noise Filter
- Context Generator
- Quality Framework

### Phase 1 (Context Layer)
- Conflict Detection
- Scoring System
- Confidence Model

### Phase 2 (Behavior Layer)
- Transition Intelligence
- Behavioral Persistence
- Efficiency Analysis

### Phase 3 (Advanced Intelligence)
- Statistical Models
- Probabilistic Forecasting
- Adaptive Weighting

### Phase 4 (AI Layer)
- Self-analysis
- Optimization Engine
- AI-assisted decision support

## 9. Risk / Complexity Analysis

### High Risk Areas
- Engine overlap (duplicate responsibility)
- Conflicting signals between layers
- Over-scoring complexity
- Latency in multi-engine processing

### Critical Design Rule
- **NO engine has trading authority**
- Only context + scoring is allowed
- Strategy is final consumer, not controller

## 10. Scalability & Future Expansion

System is designed for:
- Adding new intelligence engines without refactor
- Multiple strategies running in parallel
- AI integration at context layer
- Reinforcement learning in future phases

**Core principle:** "Add intelligence without breaking structure"

---

## Summary

This system is a modular market cognition framework where:
- Engines observe
- Context layer interprets
- Scoring layer evaluates
- Strategy layer consumes

*Not a trading bot, but a trading intelligence OS.*
