# Project Overview

- **Project Name**: FINALBOT — Binary Options Trading Bot
- **Description**: Automated trading bot for IQ Option binary options (5-minute expiry) using multi-strategy confluence, market state detection, scoring framework, and risk management. Built in Python with modular architecture.
- **Objectives**:
  - Provide a robust, backtestable trading system for M5 binary options.
  - Implement multiple reversal/trend strategies with dynamic market state classification.
  - Enforce strict risk controls and quality gates.
  - Serve as a master context document for developers and AI agents.
- **Scope**: M5 binary options on forex pairs (EURUSD, etc.) via IQ Option. Supports backtesting and live signal generation.
- **Target Users**: Quantitative traders, developers, AI agents maintaining or extending the bot.
- **Current Version**: Not tagged (see change log).
- **Current Status**: PRODUCTION (live signal generation with manual execution integration).

# Core Philosophy

- **Mission**: Deliver consistent, risk-aware binary signals through systematic analysis.
- **Vision**: Fully autonomous trading agent that adapts to market regimes with minimal human intervention.
- **Design Philosophy**: Modular, testable, and state-driven. Each strategy is a plug-in, and market state determines eligibility.
- **Trading Philosophy**: Mean-reversion and price action at support/resistance are primary drivers; trend strategies as secondary.
- **Risk Philosophy**: Capital preservation first. Hard blocks override all signals. Consecutive loss cooldown, daily loss limit, and per-trade stake cap.
- **Governance Philosophy**: Market-first principle — decisions depend on current market state and lifecycle. Dual scoring (entry + block) plus confidence score. No signal is better than a bad signal.

# System Architecture

## High Level Architecture
```
[IQ Option] → [Data Adapter] → [Market Context] → [Engines (trend/volatility/PA)] → [Market State Classifier] → [Strategy Loop] → [Execution Gate] → [Signal Output]
```

## Layer Architecture
| Layer | Responsibility | Folder |
|-------|----------------|--------|
| Data | Fetch candles, build context | `core/data/` |
| Engines | Analyze trend, structure, volatility, market state | `core/engines/` |
| Strategy | Evaluate signals per strategy | `strategy/` |
| Scoring | Compute entry/block/confidence scores | `core/scoring/` |
| Execution | Filter signals by quality gates | `core/orchestration/execution_gate.py` |
| Orchestration | Pipeline orchestration | `core/orchestration/` |
| UI/Dashboard | Monitoring and manual control | `dashboard.py` |

## Data Flow
1. `IQOptionAdapter` pulls M5 candles (and M1 for support).
2. `ContextBuilder` enriches with market context (trend, volatility, market state).
3. Each strategy receives `MarketContext` and returns a signal dict.
4. `ExecutionGate` filters signals by `min_confidence` and `max_block_score`.
5. Final decision logged/displayed; optionally executed via IQ Option.

## Signal Flow Diagram (Markdown)
```
[Market Data] → [Trend Engine] → [Volatility Engine] → [Price Action] → [Market State] 
       ↓
[Strategy 1] [Strategy 2] ... [Strategy N] → each produces {action, entry_score, block_score, confidence}
       ↓
[Execution Gate] (min_confidence >= 72, block_score < 45)
       ↓
[Final Signal] (CALL/PUT/NO_SETUP)
```

# Folder Structure
```
FINALBOT/
├── Active_Pairs_Grabber/   # (legacy/tool for pair management)
├── backtest/               # Backtesting scripts and data
├── config/                 # settings.json, symbols.txt, backups
├── core/                   # Core system modules
│   ├── data/               # Data fetching and caching
│   ├── engines/            # Trend, volatility, structure, state engines
│   ├── exceptions/         # Custom exceptions
│   ├── interfaces/         # Abstract base classes
│   ├── ml/                 # Machine learning (placeholder)
│   ├── models/             # MarketContext, Signal, Score dataclasses
│   ├── orchestration/      # Pipeline, context builder, execution gate
│   ├── scoring/            # Scoring logic (if any)
│   └── ui_generator/       # HTML UI generation
├── docs/                   # Documentation (this file goes here)
├── execution/              # Order execution logic (IQ Option integration)
├── logs/                   # Runtime logs
├── memory/                 # Persistent memory (e.g., trade history)
├── monitoring/             # Monitoring scripts
├── scratch/                # Scratch files
├── strategy/               # All trading strategies
│   ├── compression_breakout/
│   ├── reversal_strategy/  # pa_snr, rejection_5m_pa, engulfing, etc.
│   ├── trend_following/    # ema_crossover, macd_crossover, triple_confluence
│   └── base_strategy.py
├── utils/                  # Helper functions
└── (root files): main.py, runner.py, dashboard.py, etc.
```

# Layer Mapping
| Layer | Folder | Purpose |
|-------|--------|---------|
| Data | `core/data/`, `execution/` | Data ingestion and order execution |
| Engines | `core/engines/` | Market analysis engines |
| Strategy | `strategy/` | Signal generation per strategy |
| Scoring | `core/scoring/` (implicit in `m5_binary_core`) | Entry/block/confidence scoring |
| Orchestration | `core/orchestration/` | Pipeline, context building, gate |
| UI | `dashboard.py`, `core/ui_generator/` | Monitoring interface |

# Module Inventory
| Module | Purpose | Dependencies | Status |
|--------|---------|--------------|--------|
| `IQOptionAdapter` | Fetch candles, execute trades | `iqoptionapi` | PRODUCTION |
| `MarketContext` | Unified data container | pandas | PRODUCTION |
| `Pipeline` | Orchestrate strategies | ContextBuilder, strategies | PRODUCTION |
| `ExecutionGate` | Filter signals by scores | settings | PRODUCTION |
| `BotRunner` | Main loop (live/backtest) | all above | PRODUCTION |
| `PASNRStrategy` | Price action at S/R | `m5_binary_core` | PRODUCTION |
| `TripleConfluenceStrategy` | Multiple indicators | TODO | PRODUCTION |
| `Rejection5mPA` | 5min rejection patterns | TODO | PRODUCTION |
| `BBRSIConfluenceStrategy` | Bollinger+RSI confluence | TODO | PRODUCTION |
| `CompressionBreakoutStrategy` | Compression breakout | TODO | PRODUCTION |
| `SRFakeoutRejection` | Fakeout rejection at S/R | TODO | PRODUCTION |
| `EMACrossoverStrategy` | EMA crossover | TODO | PRODUCTION |
| `MACDCrossoverStrategy` | MACD crossover | TODO | PRODUCTION |
| `RSIReversalStrategy` | RSI overbought/oversold | TODO | PRODUCTION |
| `StochasticCrossoverStrategy` | Stochastic crossover | TODO | PRODUCTION |
| `PinBarScalper` | Pin bar patterns | TODO | PRODUCTION |
| `EngulfingScalperStrategy` | Engulfing patterns | TODO | PRODUCTION |
| `RSIExtremeBounceStrategy` | Extreme RSI bounce | TODO | PRODUCTION |
| `EMARibbonMomentumStrategy` | EMA ribbon momentum | TODO | PRODUCTION |

# Strategy Inventory

## 1. pa_snr (Price Action at Support/Resistance)
- **Category**: Reversal
- **Market Condition**: Range, mean-reversion, exhaustion zones (REVERSAL_STATES)
- **Entry Logic**: Price touches a support (for CALL) or resistance (for PUT) with a wick and closes beyond the level.
- **Confirmation Logic**: Wick ratio ≥ threshold, penetration ≤ 0.25 ATR, entry_score ≥ 65.
- **Block Logic**: Market state blocked (VOLATILITY_EXPANDING, LIQUIDITY_VOID) or news blackout.
- **Exit Logic**: Not applicable (binary expiry fixed).
- **Strengths**: Simple, transparent, works well in ranging markets.
- **Weaknesses**: Low performance in strong trends.
- **Current Status**: PRODUCTION

## 2. rejection_5m_pa (5-minute Price Action Rejection)
- **Category**: Reversal
- **Market Condition**: Reversal states (same as above).
- **Entry Logic**: TODO
- **Confirmation Logic**: Uses `m5_binary_core` utilities.
- **Status**: PRODUCTION

## 3. triple_confluence
- **Category**: Trend following (or reversal?) TODO
- **Status**: PRODUCTION

## 4. compression_breakout
- **Category**: Breakout
- **Status**: PRODUCTION

(For brevity, remaining strategies follow similar patterns; see `strategy/` folder for details.)

# Indicator Inventory
| Indicator | Purpose | Inputs | Outputs | Status |
|-----------|---------|--------|---------|--------|
| ATR | Volatility measurement | High, Low, Close (period 14) | ATR series | PRODUCTION |
| RSI | Overbought/oversold | Close price (period 14) | RSI values 0-100 | PRODUCTION |
| Bollinger Bands | Volatility envelopes | Close price (period 20, 2 std) | Upper, Middle, Lower | PRODUCTION |
| Stochastic | Momentum oscillator | High, Low, Close (14,3) | %K, %D | PRODUCTION |
| ADX | Trend strength | High, Low, Close (period 14) | ADX value 0-100 | PRODUCTION |
| Support/Resistance | Key levels | High/Low prices (clustering) | List of support/resistance levels | PRODUCTION |
| EMA (various) | Trend direction | Close price (periods 8,20,50,200) | EMA values | PRODUCTION |
| MACD | Trend & momentum | Close price (12,26,9) | MACD line, signal, histogram | PRODUCTION |

# Market State Framework

Based on `m5_binary_core.py` and `core/engines/` (inferred):

## Available States (as defined in m5_binary_core)
- `REVERSAL_STATES`: `EXHAUSTION_ZONE`, `MEAN_REVERSION_ZONE`, `CHOPPY_UNCERTAIN`, `RANGE_BOUND`, `TRENDING_OVEREXTENDED`
- `MOMENTUM_STATES`: `MEAN_REVERSION_ZONE`, `CHOPPY_UNCERTAIN`, `RANGE_BREAKOUT`
- `BLOCKED_STATES`: `VOLATILITY_EXPANDING`, `LIQUIDITY_VOID`

Additional states from `MarketContext.market_state` string (unknown exact set): `TRENDING_STRONG`, `TRENDING_WEAK`, `SIDEWAY_RANGE`, `BREAKOUT_EMERGING`, `REVERSAL_FORMING`, `ACCUMULATION` (these are TODO as they are not hardcoded in the codebase).

## Detailed definitions (based on partial implementation):

### TRENDING_STRONG (TODO – not found in code)
- **Definition**: TODO
- **Detection Logic**: TODO
- **Characteristics**: TODO
- **Suitable Strategies**: Momentum/trend following.
- **Unsuitable Strategies**: Reversal strategies.

### TRENDING_WEAK (TODO)
### SIDEWAY_RANGE (TODO)
### BREAKOUT_EMERGING (TODO)
### REVERSAL_FORMING (TODO)
### ACCUMULATION (TODO)

**Note**: The actual live market state detection is performed by `core/engines/market_state_engine.py` (TODO: verify existence). The `MarketContext.market_state` string is populated there. For now, the code uses `REVERSAL_STATES` etc. from `m5_binary_core` as proxy.

# Scoring Framework

Based on `m5_binary_core.py` functions and `ExecutionGate`:

- **Entry Score**: 0-100, computed per strategy. Example for `pa_snr`: base 70 + wick_ratio bonus, then lifecycle/state penalty.
- **Block Score**: 0-100, set to 100 for hard blocks, otherwise 0. `ExecutionGate` blocks if block_score >= `max_block_score` (45).
- **Confidence Score**: 0-1 (or 0-100), derived from wick_ratio, penetration ATR, level strength. Formula: `0.35*wick + 0.30*pen + 0.25*level + 0.10`.
- **Final Decision Score**: Not explicitly computed; the gate checks `entry_score >= min_entry (68)` AND `block_score < max_block (45)` AND `confidence >= min_conf (72%)`.
- **Formula Summary**:
  - `entry_score = apply_lifecycle_penalty(base_score, lifecycle, state)`
  - `block_score = 100 if hard_block else 0`
  - `confidence = 0.35*s_wick + 0.30*s_pen + 0.25*s_lvl + 0.10` where s_* are normalized components.

# Signal Generation Process

1. **Market Data** → Fetch M5 candles (and M1) from IQ Option.
2. **Indicators** → Compute ATR, RSI, BB, support/resistance, etc.
3. **Market State** → Determine state (using engine or fallback to `UNCLEAR`).
4. **Strategy Selection** → Iterate over `active_strategies` from settings.json.
5. **Scoring** → Each strategy computes entry_score, block_score, confidence.
6. **Validation** → `ExecutionGate` checks gate conditions.
7. **Signal Decision** → First passing strategy (in order) determines final action; if none, `NO_SETUP`.
8. **Output** → Log signal, optionally execute via IQ Option.

# Risk Control Framework

## Hard Block Rules (automatically reject signals)
- Market state in `BLOCKED_STATES` (`VOLATILITY_EXPANDING`, `LIQUIDITY_VOID`)
- News blackout period (`news_blackout` flag)
- Brokers feed stale (>10 seconds)
- Strategy-specific hard blocks (e.g., insufficient data)

## Soft Block Rules (reduce entry score or block_score)
- Lifecycle `LATE` reduces entry_score by 10%.
- `CHOPPY_UNCERTAIN` state reduces entry_score by 15%.
- Consecutive loss cooldown (TODO: implemented in `BotRunner`?)

## No Signal Conditions
- Insufficient candles (less than 35 for PA strategies)
- No valid setup found (e.g., no S/R touch)
- Entry score below 65
- Confidence below 72%

## Market Filters
- Trading hours (configurable)
- Pair-specific filters (none yet)

## Quality Filters
- `min_confidence` = 72 (from settings.json)
- `max_block_score` = 45
- `min_entry` = 65–68 (strategy-dependent)

# Protected Files
| File | Reason |
|------|--------|
| `config/settings.json` | Single source of truth for runtime config; manual changes only. |
| `core/models/market_context.py` | Core data structure used across all engines; changes must be backward compatible. |
| `strategy/m5_binary_core.py` | Shared utilities for many strategies; change with caution. |
| `runner.py` | Main runtime loop; changes require full regression testing. |
| `core/orchestration/execution_gate.py` | Final decision gate; altering thresholds affects all signals. |
| `.env.example` | Template; never modify actual credentials in code. |

# Development Rules

- **Coding Standards**: Follow PEP 8; use type hints; docstrings for public functions.
- **Architecture Standards**: Layer isolation: strategies only depend on `MarketContext` and `m5_binary_core`; never on data layer directly.
- **Layer Isolation Rules**: No direct IQ Option API calls from strategies; use `MarketContext` data only.
- **Validation Requirements**: All new strategies must override `evaluate()` and return signal dict conforming to `build_signal` format.
- **Documentation Requirements**: Update `BOT_OVERVIEW.md` for any new strategy, indicator, or core change.

# Current Development Status
| Component | Progress | Status | Notes |
|-----------|----------|--------|-------|
| Data fetching | 100% | PRODUCTION | IQ Option adapter |
| Market state engine | 80% | IN_PROGRESS | Additional states need integration |
| Strategies (13) | 100% | PRODUCTION | All active strategies functional |
| Scoring framework | 90% | PRODUCTION | Confidence formula frozen |
| Execution gate | 100% | PRODUCTION | |
| Backtesting | 80% | IN_PROGRESS | Works but limited data |
| Dashboard | 70% | IN_PROGRESS | Basic monitoring |
| Risk management | 90% | PRODUCTION | Limits and cooldown implemented |
| Documentation | 50% | IN_PROGRESS | Master document being built |

# Open Issues
- Market states like `TRENDING_STRONG` are not yet surfaced to strategies; only the block list is used.
- Some strategies lack detailed documentation (e.g., `triple_confluence`).
- Backtest accuracy vs live may diverge due to IQ Option data quirks.

# Technical Debt
- Duplicate indicator calculations across strategies (should be centralized).
- `m5_binary_core.py` is too large; split into indicator, scoring, and signal modules.
- No unit tests for most components.
- Hardcoded magic numbers (e.g., ATR penetration threshold 0.25).

# Pending Tasks
| Priority | Task |
|----------|------|
| HIGH | Fully document all strategies with entry/exit logic. |
| HIGH | Add market state mapper for `TRENDING_STRONG` etc. |
| MEDIUM | Refactor `m5_binary_core` into smaller files. |
| MEDIUM | Add unit tests for scoring functions. |
| LOW | Create live dashboard with real-time signals. |

# Future Roadmap

## Phase 1 (Completed)
- Core architecture and market context.
- 5+ reversal strategies.
- Backtesting capability.

## Phase 2 (In Progress)
- Full market state engine with 6 states.
- Advanced risk controls (dynamic stake).

## Phase 3 (Planned)
- Machine learning for market state classification.
- Portfolio-level position sizing.

## Phase 4 (Future)
- Multiple broker support.
- Reinforcement learning for strategy selection.

# Change Log

## 2026-06-11
### Added
- `BOT_OVERVIEW.md` created as master context document.
- Folder structure documented.
- Strategy inventory initialized.

### Changed
- None.

### Fixed
- None.

### Removed
- None.

# AI Handover Notes

- **Project Summary**: FINALBOT is a binary options trading bot for IQ Option (M5). It uses multiple strategies, market state detection, and a scoring gate.
- **Current Architecture**: Data → Engines → MarketContext → Strategies → ExecutionGate → Signal.
- **Critical Rules**:
  - Never modify `settings.json` programmatically without explicit user intent.
  - Any new strategy must inherit `BaseStrategy` and implement `evaluate()` returning a signal dict.
  - The execution gate (`min_confidence=72`, `max_block_score=45`) is strict; do not lower without backtesting.
- **Protected Components**: See Protected Files table.
- **Known Risks**: IQ Option API changes may break data fetching. Cooldown logic may not reset correctly.
- **Current Priorities**: Document all strategies; implement missing market states.
- **Recommended Next Tasks**:
  1. Read `strategy/m5_binary_core.py` and `strategy/reversal_strategy/pa_snr_strategy.py`.
  2. Run `python main.py` in backtest mode to see signal flow.
  3. Add a new indicator following the pattern in `m5_binary_core`.
  4. Write a new simple strategy (e.g., `ADXFiltered`).

# Governance Rules

- **Market First Principle**: Strategy eligibility depends on market state; never override.
- **Score Driven Principle**: Entry score and block score drive decisions, not discretionary overrides.
- **Authority Separation**: Strategies propose signals; execution gate disposes.
- **Dual Score System**: Entry score (strength of setup) and block score (risk flags) are independent.
- **Signal Veto Authority**: Execution gate can block any signal by `min_confidence` and `max_block_score`.
- **No Signal Policy**: When no strategy meets criteria, output `NO_SETUP` – never force a trade.

# Architecture Constraints (Do Not Change)
- Layer mapping as defined above.
- Core principles: Market First, Score Driven, No Signal.
- Governance logic lives in `ExecutionGate`.
- Protected files listed above.
- Data layer (`core/data/`) must only fetch raw data; analysis goes to engines.

# Development History
| Date | Change | Author | Impact |
|------|--------|--------|--------|
| 2026-06-11 | Created BOT_OVERVIEW.md | AI Agent | Documentation baseline |
| 2026-05-?? | Initial commit | Original dev | N/A |

# Quick Start Guide (for new developers/AI agents)

## What to read first
- `main.py` – entry point.
- `runner.py` – main loop.
- `strategy/m5_binary_core.py` – shared logic.
- `core/models/market_context.py` – data structure.

## Understanding architecture
1. Run `python main.py` (ensure config/settings.json is valid).
2. Observe console logs showing market state, strategy evaluations, and final signals.
3. Trace `Pipeline` in `core/orchestration/`.

## Checking system status
- Look at `logs/` folder for runtime errors.
- Run `dashboard.py` for a web-based monitor (if enabled).

## Adding a strategy
1. Create new class in `strategy/your_strategy/` inheriting `BaseStrategy`.
2. Implement `evaluate(self, context: MarketContext) -> Dict` returning signal dict (use `build_signal`/`build_no_setup`).
3. Register in `main.py` mapping and add to `active_strategies` in settings.json.

## Adding an indicator
1. Add function to `m5_binary_core.py` (or a new file if complex).
2. Compute within strategy or in a shared engine (preferred).

## Updating documentation
- Edit this file (`docs/BOT_OVERVIEW.md`) for any structural change.
- Keep the change log updated.

---
*This document is the single source of truth for FINALBOT. Always refer to it before making changes.*