```plain
BOT_FINALBOT/
├── Active_Pairs_Grabber/
│   ├── historical_data/
│   │   ├── history_AUDUSD_M1.csv
│   │   ├── history_AUDUSD_M15.csv
│   │   ├── history_AUDUSD_M5.csv
│   │   ├── history_AUDUSD_M60.csv
│   │   ├── history_EURGBP_M1.csv
│   │   ├── history_EURGBP_M15.csv
│   │   ├── history_EURGBP_M5.csv
│   │   ├── history_EURGBP_M60.csv
│   │   ├── history_EURGBP_OTC_M1.csv
│   │   ├── history_EURGBP_OTC_M15.csv
│   │   ├── history_EURGBP_OTC_M5.csv
│   │   ├── history_EURGBP_OTC_M60.csv
│   │   ├── history_EURJPY_M1.csv
│   │   ├── history_EURJPY_M15.csv
│   │   ├── history_EURJPY_M5.csv
│   │   ├── history_EURJPY_M60.csv
│   │   ├── history_EURJPY_OTC_M1.csv
│   │   ├── history_EURJPY_OTC_M15.csv
│   │   ├── history_EURJPY_OTC_M5.csv
│   │   ├── history_EURJPY_OTC_M60.csv
│   │   ├── history_EURUSD_M1.csv
│   │   ├── history_EURUSD_M15.csv
│   │   ├── history_EURUSD_M5.csv
│   │   ├── history_EURUSD_M60.csv
│   │   ├── history_EURUSD_OTC_M1.csv
│   │   ├── history_EURUSD_OTC_M15.csv
│   │   ├── history_EURUSD_OTC_M5.csv
│   │   ├── history_EURUSD_OTC_M60.csv
│   │   ├── history_GBPUSD_M1.csv
│   │   ├── history_GBPUSD_M15.csv
│   │   ├── history_GBPUSD_M5.csv
│   │   ├── history_GBPUSD_M60.csv
│   │   ├── history_GBPUSD_OTC_M1.csv
│   │   ├── history_GBPUSD_OTC_M15.csv
│   │   ├── history_GBPUSD_OTC_M5.csv
│   │   ├── history_GBPUSD_OTC_M60.csv
│   │   ├── history_USDJPY_M1.csv
│   │   ├── history_USDJPY_M15.csv
│   │   ├── history_USDJPY_M5.csv
│   │   ├── history_USDJPY_M60.csv
│   │   ├── history_USDJPY_OTC_M1.csv
│   │   ├── history_USDJPY_OTC_M15.csv
│   │   ├── history_USDJPY_OTC_M5.csv
│   │   └── history_USDJPY_OTC_M60.csv
│   ├── active_symbols.txt
│   ├── grabber.py
│   └── History_IQ.py
├── backtest/
│   ├── configs/
│   │   ├── settings_snap_20260610_223351.json
│   │   ├── settings_snap_20260610_223553.json
│   │   └── settings_snap_20260610_224105.json
│   ├── data test/
│   │   ├── history_AUDUSD_M1.csv
│   │   ├── history_AUDUSD_M15.csv
│   │   ├── history_AUDUSD_M5.csv
│   │   ├── history_AUDUSD_M60.csv
│   │   ├── history_EURGBP_M1.csv
│   │   ├── history_EURGBP_M15.csv
│   │   ├── history_EURGBP_M5.csv
│   │   ├── history_EURGBP_M60.csv
│   │   ├── history_EURGBP_OTC_M1.csv
│   │   ├── history_EURGBP_OTC_M15.csv
│   │   ├── history_EURGBP_OTC_M5.csv
│   │   ├── history_EURGBP_OTC_M60.csv
│   │   ├── history_EURJPY_M1.csv
│   │   ├── history_EURJPY_M15.csv
│   │   ├── history_EURJPY_M5.csv
│   │   ├── history_EURJPY_M60.csv
│   │   ├── history_EURJPY_OTC_M1.csv
│   │   ├── history_EURJPY_OTC_M15.csv
│   │   ├── history_EURJPY_OTC_M5.csv
│   │   ├── history_EURJPY_OTC_M60.csv
│   │   ├── history_EURUSD_M1.csv
│   │   ├── history_EURUSD_M15.csv
│   │   ├── history_EURUSD_M5.csv
│   │   ├── history_EURUSD_M60.csv
│   │   ├── history_EURUSD_OTC_M1.csv
│   │   ├── history_EURUSD_OTC_M15.csv
│   │   ├── history_EURUSD_OTC_M5.csv
│   │   ├── history_EURUSD_OTC_M60.csv
│   │   ├── history_GBPUSD_M1.csv
│   │   ├── history_GBPUSD_M15.csv
│   │   ├── history_GBPUSD_M5.csv
│   │   ├── history_GBPUSD_M60.csv
│   │   ├── history_GBPUSD_OTC_M1.csv
│   │   ├── history_GBPUSD_OTC_M15.csv
│   │   ├── history_GBPUSD_OTC_M5.csv
│   │   ├── history_GBPUSD_OTC_M60.csv
│   │   ├── history_USDJPY_M1.csv
│   │   ├── history_USDJPY_M15.csv
│   │   ├── history_USDJPY_M5.csv
│   │   ├── history_USDJPY_M60.csv
│   │   ├── history_USDJPY_OTC_M1.csv
│   │   ├── history_USDJPY_OTC_M15.csv
│   │   ├── history_USDJPY_OTC_M5.csv
│   │   └── history_USDJPY_OTC_M60.csv
│   ├── logs test/
│   ├── results/
│   ├── auto_backtester.py
│   └── backtester.py
├── config/
│   ├── settings.json
│   └── symbols.txt
├── core/
│   ├── data/
│   │   ├── __init__.py
│   │   ├── candle_buffer.py
│   │   ├── csv_data_adapter.py
│   │   ├── data_source.py
│   │   ├── data_validator.py
│   │   ├── dummy_data.py
│   │   ├── iq_option_adapter.py
│   │   └── __pycache__/ (excluded)
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── backtest_engine.py
│   │   ├── live_engine.py
│   │   └── signal_engine.py
│   ├── intelligence/
│   │   ├── __init__.py
│   │   ├── market_intelligence.py
│   │   ├── regime_detector.py
│   │   └── sentiment_analyzer.py
│   ├── __init__.py
│   └── orchestration.py
├── dashboard.py
├── docs/
│   ├── analysis_reports/
│   │   ├── Reversal Group A_NUCLEAR_BINARY_review_report.md
│   │   ├── Reversal Group A_NUCLEAR_BINARY_specification.md
│   │   ├── Reversal Group A_PA_SNR_STRATEGY_review_report.md
│   │   ├── Reversal Group A_PA_SNR_STRATEGY_specification.md
│   │   ├── Reversal Group A_PIN_BAR_SCALPER_review_report.md
│   │   ├── Reversal Group A_PIN_BAR_SCALPER_specification.md
│   │   ├── Reversal Group A_REJECTION_5M_PA_review_report.md
│   │   ├── Reversal Group A_REJECTION_5M_PA_specification.md
│   │   ├── Reversal Group A_SR_FAKEOUT_REJECTION_review_report.md
│   │   ├── Reversal Group A_SR_FAKEOUT_REJECTION_specification.md
│   │   ├── Reversal Group B_BB_RSI_CONFLUENCE_review_report.md
│   │   ├── Reversal Group B_BB_RSI_CONFLUENCE_specification.md
│   │   ├── Reversal Group B_RSI_EXTREME_BOUNCE_review_report.md
│   │   ├── Reversal Group B_RSI_EXTREME_BOUNCE_specification.md
│   │   ├── Reversal Group B_RSI_REVERSAL_review_report.md
│   │   ├── Reversal Group B_RSI_REVERSAL_specification.md
│   │   ├── Reversal Group C_ENGULFING_SCALPER_review_report.md
│   │   ├── Reversal Group C_ENGULFING_SCALPER_specification.md
│   │   ├── Reversal Group C_STOCHASTIC_CROSSOVER_review_report.md
│   │   ├── Reversal Group C_STOCHASTIC_CROSSOVER_specification.md
│   │   ├── rewrite.py
│   │   ├── temp_core.txt
│   │   ├── Trend Group_EMA_CROSSOVER_review_report.md
│   │   ├── Trend Group_EMA_CROSSOVER_specification.md
│   │   ├── Trend Group_EMA_RIBBON_MOMENTUM_review_report.md
│   │   ├── Trend Group_EMA_RIBBON_MOMENTUM_specification.md
│   │   ├── Trend Group_MACD_CROSSOVER_review_report.md
│   │   ├── Trend Group_MACD_CROSSOVER_specification.md
│   │   ├── Trend Group_TRIPLE_CONFLUENCE_review_report.md
│   │   ├── Trend Group_TRIPLE_CONFLUENCE_specification.md
│   │   ├── เอกสาร_FINALBOT_โครงสร้างบอทไม่ผ่าน แต่เป็นคัมภีร์ได้.md
│   │   ├── เอกสารโครงสร้าง_BOT_FINALBOT_Architecture.md
│   │   ├── แนวทาง_Chat01_FINALBOT_Blueprint_GUIDE.md
│   │   ├── แนวทาง_Chat02_FINALBOT_Core_Intelligence.md
│   │   ├── แนวทาง_Chat03_FINALBOT_CONTINUATION GUIDE.md
│   │   ├── แนวทาง_FINALBOT_ARCHITECTURE_REVIEW.md
│   │   ├── แนวทาง_FINALBOT_MARKET_INTELLIGENCE_SPEC.md
│   │   ├── แนวทาง_FINALBOT_ROADMAP.md
│   │   ├── แนวทาง_FINALBOT_STRATEGY_FEASIBILITY_5M_COMPRESSION_BREAKOUT.md
│   │   ├── แนวทาง_FINALBOT_Strategy_Pre_Intelligence.md
│   │   └── แนวทางเตรียมสร้าง_FINALBOT_PYTHON MODUL.md
│   └── README.md
├── execution/
│   ├── __init__.py
│   ├── execution_guard.py
│   ├── iq_option_executor.py
│   ├── order_manager.py
│   ├── portfolio_balancer.py
│   ├── position_sizer.py
│   └── signal_throttle.py
├── logs/
│   ├── bot_20260610_132138.log
│   ├── bot_20260610_133045.log
│   ├── bot_20260610_134032.log
│   ├── bot_20260610_134814.log
│   ├── market_state.json
│   ├── market_state_EURGBP-OTC.json
│   ├── market_state_EURJPY-OTC.json
│   ├── market_state_EURUSD-OTC.json
│   ├── market_state_GBPUSD-OTC.json
│   └── market_state_USDJPY-OTC.json
├── main.py
├── memory/
├── monitoring/
│   ├── __init__.py
│   ├── advanced_dashboard.py
│   ├── health_monitor.py
│   ├── logger.py
│   ├── performance_monitor.py
│   ├── reporter.py
│   └── signal_notifier.py
├── README.md
├── refactor_strategies.py
├── requirements.txt
├── runner.py
├── scratch/
│   ├── gen_tree.py
│   ├── gen_tree_utf8.py
│   ├── test_fibonacci.py
│   └── workspace_tree.md
├── simple_runner.py
├── SOUL.md
├── strategy/
│   ├── compression_breakout/
│   │   ├── __init__.py
│   │   ├── block_rules.py
│   │   ├── config.json
│   │   ├── entry_rules.py
│   │   ├── strategy.py
│   │   └── strategy_manifest.json
│   ├── reversal_strategy/
│   │   ├── bb_rsi_confluence.py
│   │   ├── engulfing_scalper.py
│   │   ├── future
│   │   ├── nuclear_binary.py
│   │   ├── pa_snr_strategy.py
│   │   ├── pin_bar_scalper.py
│   │   ├── rejection_5m_pa.py
│   │   ├── reversal_strategy.py
│   │   ├── rsi_extreme_bounce.py
│   │   ├── rsi_reversal.py
│   │   ├── sr_fakeout_rejection.py
│   │   └── stochastic_crossover.py
│   ├── trend_following/
│   │   ├── ema_crossover.py
│   │   ├── ema_ribbon_momentum.py
│   │   ├── macd_crossover.py
│   │   ├── trend_strategy.py
│   │   └── triple_confluence.py
│   ├── __init__.py
│   ├── base_strategy.py
│   ├── m5_binary_core.py
│   └── strategy_registry.py
├── symbols.txt
├── tests/
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── sample_candles.py
│   │   └── sample_context.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_end_to_end.py
│   │   └── test_strategy.py
│   ├── replay/
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_engines.py
│   │   ├── test_import_validation.py
│   │   ├── test_models.py
│   │   ├── test_orchestration.py
│   │   ├── test_phase8.py
│   │   └── test_scoring.py
│   └── __init__.py
├── test_push.txt
├── USER.md
└── utils/
    ├── __init__.py
    ├── math_utils.py
    ├── time_utils.py
    └── validators.py
```