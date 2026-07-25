# BOT_FINALBOT13 STG Architecture Tree

`	ext
BOT_FINALBOT/
├── .env
├── .env.example
├── .gitignore
├── antigravity_cli.py
├── browser_automation.js
├── calendar_news.py
├── main.py
├── n1
├── runner.py
├── run_auto.js
├── run_headless.js
├── .vscode/
│   ├── extensions.json
│   ├── launch.json
│   ├── prompts.json
│   └── settings.json
├── config/
│   ├── config_loader.py
│   ├── forge-agent.config.json
│   ├── settings.json
│   ├── settings_backup.json
│   └── symbols.txt
├── core/
│   ├── ai_analysis/
│   │   ├── deepseek_agent_bridge.py
│   │   ├── prompt_ai_context.py
│   │   ├── __init__.py
│   │   ├── Deepseek Browser Agent/
│   │   │   ├── .gitignore
│   │   │   ├── CHANGELOG.md
│   │   │   ├── CONTRIBUTING.md
│   │   │   ├── debugging_cheatsheet.md
│   │   │   ├── debug_checklist.py
│   │   │   ├── Dockerfile
│   │   │   ├── ds.bat
│   │   │   ├── DS_ANALYSIS_REPORT.md
│   │   │   ├── ds_config.json
│   │   │   ├── ds_test_log.md
│   │   │   ├── hello_world.py
│   │   │   ├── LICENSE
│   │   │   ├── package-lock.json
│   │   │   ├── package.json
│   │   │   ├── Plan_Edit_ds.md
│   │   │   ├── PYTHON_DEBUGGING_GUIDE.md
│   │   │   ├── README.md
│   │   │   ├── README_TH.md
│   │   │   ├── temp_env.cmd
│   │   │   ├── trading_debug_utils.py
│   │   │   ├── src/
│   │   │   │   ├── agent.js
│   │   │   │   ├── backup.js
│   │   │   │   ├── browser.js
│   │   │   │   ├── calibrate.js
│   │   │   │   ├── config.js
│   │   │   │   ├── index.js
│   │   │   │   ├── logger.js
│   │   │   │   ├── parser.js
│   │   │   │   ├── postinstall.js
│   │   │   │   ├── prompt.js
│   │   │   │   ├── tools.js
│   │   │   │   ├── trading/
│   │   │   │   │   ├── broker.js
│   │   │   │   │   ├── cli.js
│   │   │   │   │   ├── config.js
│   │   │   │   │   ├── index.js
│   │   │   │   │   ├── logger.js
│   │   │   │   │   ├── multiStrategy.example.js
│   │   │   │   │   ├── multiStrategy.js
│   │   │   │   │   ├── multiStrategy.test.js
│   │   │   │   │   ├── package.json
│   │   │   │   │   ├── QUICKSTART.md
│   │   │   │   │   ├── README.md
│   │   │   │   │   ├── risk.js
│   │   │   │   │   ├── scheduler.js
│   │   │   │   │   └── strategy.js
│   │   ├── Deepseek Browser Agent - สำเนา/
│   │   │   ├── .gitignore
│   │   │   ├── CHANGELOG.md
│   │   │   ├── CONTRIBUTING.md
│   │   │   ├── Dockerfile
│   │   │   ├── LICENSE
│   │   │   ├── package-lock.json
│   │   │   ├── package.json
│   │   │   ├── README.md
│   │   │   ├── README_TH.md
│   │   │   ├── src/
│   │   │   │   ├── agent.js
│   │   │   │   ├── backup.js
│   │   │   │   ├── browser.js
│   │   │   │   ├── calibrate.js
│   │   │   │   ├── config.js
│   │   │   │   ├── index.js
│   │   │   │   ├── logger.js
│   │   │   │   ├── parser.js
│   │   │   │   ├── postinstall.js
│   │   │   │   ├── prompt.js
│   │   │   │   └── tools.js
│   ├── bot_strategy/
│   │   └── strategy.py
│   ├── data/
│   │   ├── data_adapter.py
│   │   ├── data_source.py
│   │   ├── iq_option_adapter.py
│   │   ├── timeframe_sync.py
│   │   └── __init__.py
│   ├── exceptions/
│   │   ├── context_exceptions.py
│   │   ├── engine_exceptions.py
│   │   ├── validation_exceptions.py
│   │   └── __init__.py
│   ├── interfaces/
│   │   ├── context_interface.py
│   │   ├── engine_interface.py
│   │   ├── strategy_interface.py
│   │   └── __init__.py
│   ├── logging/
│   │   ├── performance_tracker_signal.py
│   │   └── signal_learning.py
│   ├── models/
│   │   ├── candle.py
│   │   ├── engine_output.py
│   │   ├── market_context.py
│   │   ├── score.py
│   │   ├── signal.py
│   │   └── __init__.py
│   ├── orchestration/
│   │   ├── anomaly_detector.py
│   │   ├── base_engine.py
│   │   ├── check_news.py
│   │   ├── context_builder.py
│   │   ├── context_synthesizer.py
│   │   ├── engine_registry.py
│   │   ├── engine_setup.py
│   │   ├── explainability_engine.py
│   │   ├── liquidity_engine.py
│   │   ├── noise_detector.py
│   │   ├── orchestrator.py
│   │   ├── pipeline.py
│   │   ├── probability_estimator.py
│   │   ├── signal_throttle.py
│   │   ├── trap_detector.py
│   │   ├── __init__.py
│   │   ├── advanced_tools/
│   │   │   ├── advanced_tools_manager.py
│   │   │   ├── behavior_analyzer.py
│   │   │   ├── candle_pattern_analyzer.py
│   │   │   ├── conflict_analyzer.py
│   │   │   ├── continuation_analyzer.py
│   │   │   ├── divergence_analyzer.py
│   │   │   ├── efficiency_analyzer.py
│   │   │   ├── persistence_analyzer.py
│   │   │   ├── price_action_handler.py
│   │   │   └── transition_analyzer.py
│   │   ├── indicator_store/
│   │   │   └── indicator_store.py
│   │   ├── market_classifier/
│   │   │   ├── market_pressure_analyzer.py
│   │   │   ├── market_state_classifier.py
│   │   │   ├── market_structure_engine.py
│   │   │   ├── mtf_engine.py
│   │   │   ├── regime_quality_scorer.py
│   │   │   ├── strength_engine.py
│   │   │   ├── structure_engine.py
│   │   │   ├── trend_engine.py
│   │   │   └── volatility_engine.py
│   ├── scoring/
│   │   ├── block_scorer.py
│   │   ├── confidence_framework.py
│   │   ├── confidence_scorer.py
│   │   ├── entry_scorer.py
│   │   ├── score_aggregator.py
│   │   ├── score_normalizer.py
│   │   ├── signal_quality_scorer.py
│   │   └── __init__.py
│   ├── ui_generator/
│   │   └── __init__.py
├── data/
│   ├── DATA IQ/
├── docs/
│   ├── FINALBOT.txt
│   ├── FINALSignal_BOT.xlsx
│   ├── FINALSignal_BOT_Tree.xlsx
│   ├── Payload_Audit_Report 2.xlsx
│   ├── Payload_Audit_Report.md
│   ├── Payload_Audit_Report.pdf
│   ├── transcript.jsonl
│   ├── transcript_full.jsonl
│   ├── Validation_Report_69_Items.xlsx
│   ├── About_Me/
│   │   ├── 0. ดัชนี_about_me.txt
│   │   ├── 1. about_me_Boss.md
│   │   ├── 2. about_me_deepseek_TH.md
│   │   └── 3. about_me_deepseek_EN.md
│   ├── Basic/
│   │   ├── logstrade ai - คำสั่ง.json
│   │   ├── SPEC_CLASSIFIER.md
│   │   ├── SPEC_COMPUTATION_FLOW.md
│   │   ├── SPEC_ENGINES.md
│   │   ├── SPEC_INDICATOR_STORE.md
│   │   ├── SPEC_TIMEFRAME_USAGE.md
│   │   └── TRADING_ARCHITECTURE.md
│   ├── Dictation_DS/
│   │   ├── AI_data_2.txt
│   │   ├── chat_history_raw.jsonl
│   │   ├── chat_history_short.jsonl
│   │   ├── chat_readable.md
│   │   ├── Data_AI.json
│   │   ├── DS_AGENT_PROMPT OVERVIEW.md
│   │   ├── Indicator.md
│   │   ├── logstrade ai - 69 data.json
│   │   ├── logstrade ai - คำสั่งพร้อมส์.json
│   │   ├── logstrade ai.json
│   │   ├── logstrade aiรร.json
│   │   ├── Log_AI.pdf
│   │   ├── MASTER_PLAN.md
│   │   ├── package-lock.json
│   │   ├── package.json
│   │   ├── Report2.md
│   │   ├── requirements.txt
│   │   ├── Walkthrough.md
│   │   ├── BOSS/
│   │   │   ├── AI01-DeepSeek Browser Agent.md
│   │   │   ├── AI03-ใช้ DeepSeek Browser AgentI เป็นสมองบอท.md
│   │   │   ├── Boss Gemini Antigravity.txt
│   │   │   ├── Boss Gemini deepseek.txt
│   │   │   ├── DEEPSEEK.txt
│   │   │   ├── User_To_Deepseek.txt
│   │   │   ├── เรียก DeepSeek Agent -โฟลเดอร์บอท.bat
│   │   │   ├── เรียก DeepSeek Agent.bat
│   │   │   ├── บอส/
│   │   │   │   ├── Boss Gemini Antigravity.txt
│   │   │   │   ├── Boss Gemini deepseek.txt
│   │   │   │   └── DeepSeek Agent.bat
├── execution/
│   ├── execution_gate.py
│   ├── execution_guard.py
│   ├── iq_option_executor.py
│   ├── order_manager.py
│   ├── portfolio_balancer.py
│   ├── position_sizer.py
│   ├── signal_throttle.py
│   └── __init__.py
├── monitoring/
│   ├── console_dashboard.py
│   ├── health_monitor.py
│   ├── logger.py
│   ├── performance_monitor.py
│   ├── reporter.py
│   ├── signal_notifier.py
│   ├── __init__.py
│   ├── advanced_dashboard/
│   │   └── advanced_dashboard.py
├── scratch/
│   ├── generate_excel.py
│   ├── gen_tree.py
│   ├── gen_tree_utf8.py
│   ├── inspect_data.py
│   ├── run_interactive.bat
│   ├── run_visible.bat
│   ├── test_agent.py
│   ├── test_fibonacci.py
│   ├── test_file_redirect.py
│   └── workspace_tree.md
├── tests/
│   ├── test_orchestrator_payload.py
│   └── test_prompt_payload_schema.py
├── utils/
│   ├── math_utils.py
│   ├── order_logger.py
│   ├── time_utils.py
│   ├── trade_logger.py
│   ├── validators.py
│   └── __init__.py
`
