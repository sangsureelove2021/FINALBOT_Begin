# 🚀 FINAL_BOT — Intelligent Automated Trading System

> **FINALBOT** คือระบบเทรดไบนารีออปชันอัตโนมัติ (IQ Option) ที่ทำงานแบบ **Event-Driven Pipeline 4 ส่วน**
> ทุกส่วนส่งงานต่อกันผ่าน **ไฟล์บนดิสก์ (SSD) เท่านั้น** — ไม่ส่ง object ผ่าน RAM ข้ามส่วน (Zero RAM Transfer)

📅 **เอกสารนี้ปรับปรุงให้ตรงกับโค้ดจริง ณ commit `7740970` (22 ก.ย. 2026 / branch `main`)**
ทุกข้อความด้านล่างตรวจสอบจาก source code จริง ไม่ใช่จากเอกสารชุดเก่า
ถ้าโค้ดกับเอกสารขัดกัน ให้ยึด **โค้ด** เป็นหลัก แล้วมาแก้เอกสารนี้ตาม

---

## 🔴 สถานะปัจจุบัน (อ่านก่อนรัน)

| หัวข้อ | สถานะจริง |
|:---|:---|
| **รันบน OS ไหนได้** | ⛔ **Windows เท่านั้น** — `runner.py` import `msvcrt` ระดับ module และใช้ `msvcrt.locking()` ทำ single-instance lock → บน Linux/macOS จะ `ImportError` ทันที |
| **สตาร์ทได้ไหมตอนนี้** | ❌ **ไม่ได้** — `ExecutorManager.__init__` (และ `runner.py:169`) import `data_trade.execution_gate.chronos_dispatcher` ซึ่ง **ไฟล์นี้ไม่มีอยู่ใน repo** → `ModuleNotFoundError` ก่อนถึง warm-up **ทุกโหมด** รวมถึง `strategies_mode` (ดู P1) |
| **โหมดที่ตั้งไว้ใน config** | `strategies_mode` (โหมด Believe) |
| **เคยรันผ่านจริงครั้งสุดท้าย** | 4 ก.ย. 2569 (log `logs/console_boss/01.txt`) — ตอนนั้นยังใช้ `ml_mode` และไฟล์ `chronos_dispatcher.py` ยังอยู่ |
| **ออเดอร์จริงในประวัติ** | มี 1 รายการ `WIN +29.26` (28 ส.ค. 2569, `EURUSDOTC`, engine `LightGBM`) ที่เหลือเป็น `SIM_*` (จำลอง) และ `PENDING` |
| **Python ที่ใช้พัฒนา** | 3.12 (win32) ตาม log — โค้ดใช้ type hint `set[str]` / `list[str]` จึงต้องมี **Python ≥ 3.9** |
| **มี `requirements.txt` ไหม** | ❌ ไม่มี — ดูรายชื่อ dependency จริงได้ที่ [Getting Started → ข้อ 2](#2-dependency-ที่โค้ด-import-จริง) |

---

## 🌟 Key Features (ที่มีจริงในโค้ด)

- 🎯 **Pre-Trade Asset Screening** — คัดคู่เงินจาก 34 คู่ (SET A 13 คู่ + SET B 21 คู่ OTC) กรอง **Payout ≥ 84%** แล้ววิเคราะห์ **7 Quant Skills + 4 Binary Edges + Support/Resistance Room-to-Run** จัดอันดับและตัดตอนเหลือ Top 4
- 🏗️ **4-Part Pipeline + Zero RAM Transfer** — `data_feed` → `data_evaluate` → `data_decision` → `data_trade` ส่งต่อกันด้วยไฟล์ `.csv` / `.txt` / `.json` บนดิสก์
- 🧠 **3 สมองตัดสินใจ** — `ml_mode` (LightGBM + Chronos), `ai_mode` (Google Gemini), `strategies_mode` (Believe rule-based) เลือกได้ทีละ 1 โหมดต่อ 1 process
- 🛡️ **Execution Gate + Money Manager** — เกตตรวจสอบ 15 ข้อ (`part4-regime-gated-trend-v1`) และเงื่อนไขความเสี่ยง 7 ข้อ ก่อนยิงออเดอร์
- ⚡ **Time-Synced Loop** — ซิงค์เวลาเซิร์ฟเวอร์โบรกเกอร์ (`time_offset`) แล้วรันทุกรอบที่ **วินาทีที่ 1.500 ของทุกนาที** (timezone Asia/Bangkok UTC+7)
- 🧾 **Fail-Fast ทุกจุด** — ตามกฎ `agent.md` ข้อ 7: ห้ามมี fallback, ข้อมูลไม่ครบ/คำนวณไม่ได้ = `raise` ทันที

---

## 🏛️ System Architecture

### Phase 0 + 4 Parts

| ส่วน | โมดูล | หน้าที่จริงในโค้ด | สถานะ |
|:---|:---|:---|:---:|
| **Phase 0** | `symbols_scanner/`<br>`config_setting/symbols_selection.py` | คัดคู่เงิน 34 คู่ → กรอง Payout ≥ 84% → 7 Skills + 4 Edges + S/R → Rank → บันทึก Top 4 | 🔒 ใช้งานได้ดี<br>(มี 2 เส้นทาง ดู [Getting Started → ข้อ 4](#4-running)) |
| **Part 1** | `data_feed/` | เชื่อมต่อ IQ Option → sync เวลาเซิร์ฟเวอร์ → warm-up 250 แท่ง → ingest รายนาที → validate → เขียน CSV 8 คอลัมน์ | 🔒 เสถียร (ประกาศว่า Immutable) |
| **Part 2** | `data_evaluate/` | อ่าน CSV จากดิสก์ → คำนวณ indicator ผ่าน `IndicatorStore` (SSOT) → รัน Engines + Advanced Tools → เขียน payload `.txt` | 🔒 เสถียร (ประกาศว่า Immutable) |
| **Part 3** | `data_decision/` | อ่าน payload `.txt` ไฟล์ล่าสุด → วิเคราะห์ตามโหมด → เขียน decision `.json` | 🛠️ กำลังพัฒนา (พบบั๊ก P2, P3) |
| **Part 4** | `data_trade/` | อ่าน decision `.json` → ผ่าน ExecutionGate 15 ข้อ + MoneyManager 7 ข้อ → ยิงออเดอร์ → ติดตามผล | 🛠️ กำลังพัฒนา (พบบั๊ก P1, P4) |

### Timeframe ที่ใช้จริง

| โหมด | Timeframe | หมายเหตุ |
|:---|:---|:---|
| `strategies_mode` | **S30, M1, M5** | `settings.json → data_feed.data_adapter.strategies_timeframes = ["S30","M1","M5"]` และ `strategies_enable_m15 = false` → **ไม่ดึง M15** |
| `ml_mode` / `ai_mode` | M1, M5, M15 | ใช้ M15 เป็นแนวโน้มหลักตาม System Prompt |

> ⚠️ ข้อความใน console ยังพิมพ์ว่า *"ตรวจสอบข้อมูลแท่งเทียนสมบูรณ์ (M1/M5/M15 ครบ 250 แท่ง)"* แม้ในโหมด strategies จะไม่ใช้ M15 — เป็นข้อความที่ hardcode ไว้ใน `monitoring/console_dashboard.py:show_data_prep_result()`

---

## 🔄 Data Flow ต่อ 1 รอบ (1 นาที)

`runner.py → DataFeedRunner.start()` วนลูปนี้ทุกนาทีที่ `:01.500` (เวลาไทย):

```text
[Phase 0] symbol_mode == "bot"
   config_setting/symbols_selection.run_selector()
   → อ่าน config_setting/symbols_user.json (SET_A 13 + SET_B 21 = 34 คู่)
   → กรอง payout ≥ 84, ให้คะแนน 7 Skills + 4 Edges + Room-to-Run
   → atomic write → config_setting/symbols.json  {symbols:[...], payouts:{...}}

[Part 1] data_feed.data_adapter.DataAdapter
   ingest_cycle(symbols)               → อัปเดตแท่ง S30/M1/M5 ต่อคู่เงิน (thread pool ≤ 20 worker)
   → validate (gap / stale / quality)  → FAIL-FAST ถ้าแท่งขาด
   → csv_queue.flush()                 → data_base/output_feed/<SYMBOL>/<SYMBOL>_<TF>.csv  (8 คอลัมน์)
   → ConsoleUI.show_prices_and_balance()

[Part 2] data_evaluate/<mode>/orchestrator.py
   evaluate_cycle(symbols)             → อ่าน CSV จากดิสก์ (ไม่รับ DataFrame ผ่าน RAM)
   → IndicatorStore.calculate_all()    → SSOT ของ indicator ทั้งหมด
   → Engines (trend/strength/volatility/structure/mtf) + MarketStateClassifier + Advanced Tools
   → _enrich_believe_analysis()        → (เฉพาะ strategies_mode)
   → _format_core_analysis_output()    → payload .txt
   → data_base/output_evaluate/<mode>/<SYMBOL>/<ID>.txt   (retention 30 ไฟล์ล่าสุด/คู่เงิน)

[Part 3] data_decision.decision_manager.DecisionManager
   process_latest(symbols)             → เลือก payload .txt ใหม่ล่าสุดที่ยังไม่ประมวลผล
   → strategies_mode : believe_analyzer.analyze_payload_file()
   → ai_mode         : SystemPrompt.process_ai_decision()  (Gemini)
   → ml_mode         : MLDispatcher.process_payload_file() (LightGBM + Chronos)
   → data_base/output_decision/{strategies_decision|ai_decision}/<SYMBOL>/<ID>.json

[Part 4] data_trade.executor_manager.ExecutorManager
   process_decision_files(symbols)     → อ่าน decision .json ล่าสุด
   → ExecutionGate.evaluate_decision() → 15 เกต (ต้อง expiry=5 นาที, confidence ≥ 55, ADX ≥ 20, ไม่ CHOPPY, ...)
   → MoneyManager.can_trade()          → 7 เงื่อนไขความเสี่ยง
   → BrokerExecutor.execute_order()    → api.buy(stake, symbol, call|put, 5)  retry 3 ครั้ง
   → OrderTracker.track_order()        → thread pool รอ settle → WIN/LOSE/EQUAL
   → data_base/trade_result/trades_history.csv + data_base/output_trade/decision_gate_audit.csv
```

**ID ของ payload** มีรูปแบบ `<SYMBOL ไม่ขีด><MMDDHHMMSS>` เช่น `EURGBPOTC0920015903` = EURGBP-OTC, 20 ก.ย. เวลา 01:59:03

---

## 🗂️ Project Directory Structure (ของจริง)

```text
FINALBOT_Begin/
├── main.py                     # entry point → ConsoleUI.show_startup() + PureAIRunner().start()
├── runner.py                   # DataFeedRunner (alias PureAIRunner) — ตัวควบคุมลูปหลัก
├── agent.md                    # กฎวินัย AI 27 ข้อ (Strict Coding Rules) — ต้องอ่านก่อนแก้โค้ด
├── readme.md                   # เอกสารนี้
│
├── config_setting/             # Single Source of Truth ของ config
│   ├── settings.json           # ⚠️ มี iq_email / iq_password เป็น plaintext (ดู ส่วนที่ 16)
│   ├── symbols.json            # ผลลัพธ์ Top 4 ที่บอทใช้จริง + payouts
│   ├── symbols_user.json       # SET_A (13) / SET_B (21) = 34 คู่ ให้ run_selector อ่าน
│   ├── symbol_mapper.json      # map ชื่อคู่เงินระหว่าง IQ_OPTION / QUOTEX / POCKET_OPTION
│   ├── config_loader.py        # load_settings(), get_symbols_with_payouts(), get_iq_credentials()
│   ├── symbols_selection.py    # ✅ ตัวที่ใช้จริง (runner เรียก run_selector)
│   └── symbols_selector.py     # ⚠️ dead code — ไม่มีที่ไหน import (ซ้ำกับข้างบน 35 KB)
│
├── symbols_scanner/            # [Phase 0] แบบ standalone (รันมือแยกจากบอท)
│   ├── main_filter.py          # มี __main__ → เขียน symbols_trade.json + symbols_onoff_*.txt
│   ├── secondary_filter.py     # ⚠️ เป็น library ล้วน ไม่มี __main__ (สั่งรันตรง ๆ ไม่ได้)
│   ├── iq_symbols_grabber.py   # ดึงรายชื่อคู่เงิน/payout จาก IQ Option
│   ├── symbols_user_config.txt # รายชื่อ 34 คู่ (คนละไฟล์กับ config_setting/symbols_user.json)
│   ├── settings_filter.json    # ⚠️ มี iq_email / iq_password ซ้ำอีกชุด
│   └── symbols_scanner_readme.md
│
├── data_feed/                  # [Part 1]
│   ├── data_adapter.py         # DataAdapter — warmup_all_symbols(), ingest_cycle(), ensure_connected()
│   ├── data_validator.py       # ตรวจ gap / continuity / overlap / stale
│   ├── data_cache_store.py     # cache แท่งเทียนใน RAM (ใช้เฉพาะใน Part 1)
│   ├── data_processor.py       # resample M1 → M5/M15
│   ├── csv_writer.py, csv_queue.py, csv_manager.py, csv_time_sync.py
│   ├── exceptions.py
│   └── bridge_adapter/
│       ├── broker_factory.py            # สร้าง adapter ตาม active_broker
│       ├── abstract_class.py
│       ├── bridge_iq_adapter/           # ✅ ใช้งานได้จริง (connection / rest_fetcher / stream_manager)
│       ├── bridge_pocket_adapter/       # ⚠️ stub 59 บรรทัด — ยังไม่ทำงาน
│       └── bridge_quotex_adapter/       # ⚠️ stub 59 บรรทัด — ยังไม่ทำงาน
│
├── data_evaluate/              # [Part 2] — ⚠️ โค้ดซ้ำกัน 3 ชุด (ml_mode / ai_mode / strategies_mode)
│   ├── mode_loader.py          # normalize_evaluate_mode(), load_orchestrator_class(), mode_output_dir()
│   ├── ml_mode/                #   orchestrator.py 1,319 บรรทัด + orchestration/ + news_calendar.py
│   ├── ai_mode/                #   orchestrator.py 1,319 บรรทัด (เหมือน ml_mode)
│   └── strategies_mode/        #   orchestrator.py 1,358 บรรทัด (+ _enrich_believe_analysis)
│       └── orchestration/
│           ├── indicator_store/         # ⭐ SSOT: CoreIndicators + IndicatorStore + structural_metrics
│           ├── market_classifier/       # trend / strength / volatility / structure / mtf / pressure / state
│           ├── advanced_tools/          # 10 ตัว: behavior, candle_pattern, conflict, continuation, divergence,
│           │                            #   efficiency, persistence, transition, price_action, trap_detector
│           ├── context_synthesizer.py, explainability_engine.py, liquidity_engine.py
│           ├── noise_detector.py, probability_estimator.py, signal_throttle.py, trap_detector.py
│           └── base_engine.py
│
├── data_decision/              # [Part 3]
│   ├── decision_manager.py     # ⭐ ตัวประสานงานหลัก — โหมดไหนก็ผ่านที่นี่
│   ├── ai_analysis/
│   │   ├── artificial_intelligence/
│   │   │   ├── ai_dispatcher.py    # SystemPrompt, SYSTEM_PROMPT, prewarm_and_test_ai, process_ai_decision
│   │   │   ├── gemini_bridge.py    # google-genai, model gemini-3.5-flash-lite, limit 500/day
│   │   │   └── deepseek_bridge.py  # stub 48 บรรทัด
│   │   └── machine_learning/
│   │       ├── ml_dispatcher.py, dual_brain.py, feature_extractor.py
│   │       ├── machine_lightgbm.py, machine_chronos.py
│   │       └── machine_learning_model/   # lightgbm_binary_model.pkl, EURUSD_lightgbm/
│   └── strategies_analysis/
│       └── believe_strategies/believe_analyzer.py   # ⭐ analyze_payload_file() (68 บรรทัด)
│
├── data_trade/                 # [Part 4]
│   ├── executor_manager.py     # ExecutorManager — process_decision_files() คือเส้นทางที่ใช้จริง
│   ├── payload_sanitizer.py
│   └── execution_gate/
│       ├── gate_controller.py  # ExecutionGate (POLICY_VERSION part4-regime-gated-trend-v1)
│       ├── money_manager.py    # MoneyManager — 7 เงื่อนไข
│       ├── broker_executor.py  # BrokerExecutor — api.buy() + retry 3
│       ├── order_tracker.py    # OrderTracker — settle WIN/LOSE/EQUAL + เขียน CSV
│       └── chronos_dispatcher.py   # ❌ ไฟล์นี้หายไปจาก repo (ดู P1)
│
├── monitoring/
│   └── console_dashboard.py    # ConsoleUI (ข้อความ console ภาษาไทย), setup_logging(), thai_console_log()
│
├── data_base/                  # ผลลัพธ์ทั้งหมด
│   ├── output_feed/<SYMBOL>/<SYMBOL>_<TF>.csv     # timestamp,open,high,low,close,volume,age,quality
│   ├── output_evaluate/<mode>/<SYMBOL>/<ID>.txt   # payload (repo ปัจจุบัน: โฟลเดอร์นี้ยังไม่ถูกสร้าง)
│   ├── output_decision/ai_decision/<SYMBOL>/      # .txt (JSON 7 ฟิลด์) + decisions.csv
│   ├── output_decision/strategies_decision/<SYM>/ # .json
│   └── output_trade/decision_gate_audit.csv       # audit ของเกต (มีข้อมูลจริงถึง 20 ก.ย. 2569)
│
├── logs/
│   ├── console_boss/01.txt                        # ⭐ log console จริงจากการรัน 4 ก.ย. 2569
│   ├── logs_data_feed/errors/error.log            # ⚠️ 30 MB
│   ├── logs_data_feed/warnings/warning.log        # ⚠️ 3.8 MB
│   ├── logs_data_evaluate/{errors,warnings}/
│   ├── logs_data_trade/trades_history.csv
│   ├── session_backups/                           # ⚠️ สำเนา repo ทั้งชุด 2 ชุด (~หลายสิบ MB)
│   └── runner.lock                                # single-instance lock (Windows)
│
├── backups/                    # ⚠️ session backup 16 ชุด — ไม่ควรอยู่ใน git
├── docs/                       # เอกสารภาษาไทย Part 1–4 + E-BOOK กลยุทธ์
├── .agents/skills_67/          # ชุด skill ของ AI agent (solana, polymarket, quant ฯลฯ) — ไม่เกี่ยวกับบอท
├── .github/github-app.yml
└── .vscode/settings.json
```

---

## 🧠 3 โหมดการทำงาน

เลือกได้ **ทีละ 1 โหมดต่อ 1 process** (`data_evaluate/mode_loader.py` โหลด orchestrator แยก namespace กัน)

| โหมด | สมอง | ค่า config ที่เกี่ยวข้อง | สถานะจริง |
|:---|:---|:---|:---|
| `strategies_mode` | **Believe** (rule-based 100%) | `active_mode: "strategies_mode"` | ⚠️ logic ครบ แต่ **ยังยิงออเดอร์แทบไม่ได้** เพราะ ExecutionGate ถูกเขียนมาเพื่อ M15 (ดู P2) และตอนนี้ติด P1 อยู่ |
| `ai_mode` | **Google Gemini** `gemini-3.5-flash-lite` | `ai_mode.provider`, `primary_model`, `primary_daily_limit: 500`, `min_confidence: 55` | ⚠️ ต้องมี `GEMINI_API_KEY_1..3` ใน env / `.env` (ช่อง `gemini_api_key` ใน settings.json **ไม่ถูกใช้**) |
| `ml_mode` | **LightGBM + Chronos** | `ml_mode.model: "CHRONOS_2_ONNX"`, `min_confidence: 55` | ❌ พัง — path `chronos2_model_path` ชี้ไป `data_trade\execution_gate\chronos-2-onnx\model.onnx` ซึ่งไม่มีไฟล์ `.onnx` ใด ๆ ใน repo |

**การสลับโหมด**

```bash
python runner.py --mode strategies     # หรือ --strategies
python runner.py --mode ai             # หรือ --ai
python runner.py --mode ml             # หรือ --ml
python runner.py                       # ใช้ active_mode จาก settings.json
```

> ⚠️ CLI มีผลก็ต่อเมื่อรัน `runner.py` ตรง ๆ เท่านั้น — `main.py` เรียก `PureAIRunner()` เฉย ๆ ทำให้ `parse_cli_mode()` อ่าน `sys.argv` เอง (ยังได้ผลเหมือนกัน) แต่ `main.py` ไม่ได้ส่ง mode ต่อ

---

## 📄 Payload Schema (ความจริง vs "99 บรรทัด")

เอกสารชุดเก่าและ `agent.md` ข้อ 20 ระบุว่า payload ต้อง **"99 บรรทัดพอดีเป๊ะ"** — **ตอนนี้ไม่จริงแล้ว**

`_format_core_analysis_output()` ใน orchestrator แต่ละโหมดสร้างจำนวนบรรทัดต่างกัน:

| โหมด | จำนวน entry ที่ `app()` | จำนวนบรรทัดในไฟล์ | มีบล็อก `believe_strategy:` |
|:---|:---:|:---:|:---:|
| `ml_mode` | 100 | 99 บรรทัด + trailing newline | ❌ |
| `ai_mode` | 100 | 99 บรรทัด + trailing newline | ❌ |
| `strategies_mode` | **115** | **114 บรรทัด** + trailing newline | ✅ (6 ฟิลด์) |

**โครงสร้าง payload (strategies_mode — 114 บรรทัด)**

```yaml
ID:EURGBPOTC0920015903          # ไม่มี space หลัง ":"
meta:                           # timestamp, symbol, ai_model, session, m1_open/age/quality, m5_open/age/quality
s30:                            # s30_bias (BULLISH/BEARISH จาก close >= open), open/high/low/close/volume
market_context:                 # mtf_state, mtf_description, m5_volatility_regime, m5_news_impact, m5_expected_volatility_%
timeframes:
  m1:                           # m1_bias, m1_last_candle, ema5, ema20, rsi, stoch_k, stoch_d, macd, macd_signal
    ohlcv:                      # m1_open/high/low/close/volume
  m5:                           # m5_bias, ema5/10/20/50, bb_upper/lower/width, rsi, stoch_k/d, macd/signal,
                                #   adx, atr, support, resistance, pivot
    ohlcv:                      # m5_open/high/low/close/volume
  m15:                          # m15_bias  ← ใน strategies_mode ค่าจะว่าง เพราะไม่ดึง M15
price_action:                   # m5_pa_* 13 ฟิลด์ (pattern, body_strength, trap_alert, divergence_alert, ...)
volume:                         # m5_tick_volume, m5_volume_momentum, m5_volume_vs_average
analysis:                       # m5_trend_direction/type/strength, mtf_alignment_%, compression_quality_%,
                                #   exhaustion_risk_%, bos_detected, mtf_conflict_score, transition_risk, persistence_score
decision_layer:                 # dl_tradeable, dl_stability_score, dl_quality_score, dl_risk_level,
                                #   ai_confidence_score / ai_suggested_expiry_minutes / ai_suggested_action
                                #   = "รอการวิเคราะห์จาก AI" (ให้ Part 3 เติม)
believe_strategy:               # believe_status, believe_direction, believe_confidence, believe_score,
                                #   extreme_believe_active, extreme_believe_setup
```

**Retention policy:** เก็บ **30 ไฟล์ล่าสุดต่อคู่เงิน** ลบไฟล์เก่าอัตโนมัติ (`_save_txt_payload`) — ตรงตามเอกสารเดิม ✅

**ตำแหน่งไฟล์:** `data_base/output_evaluate/<mode>/<SYMBOL>/<ID>.txt`
(เปลี่ยนจาก `data_base/evaluate_output/` และ `data_evaluate/payload_output/` ที่เอกสารเก่า/log เก่าอ้างถึง)

---

## 📈 กลยุทธ์ Believe — เอกสาร vs โค้ดจริง

ส่วนนี้คือจุดที่ readme เดียวคลาดเคลื่อนจากโค้ดมากที่สุด ตารางซ้ายคือสิ่งที่เอกสารเดิมระบุ
ตารางขวาคือสิ่งที่ `_enrich_believe_analysis()` ทำจริงใน `data_evaluate/strategies_mode/orchestrator.py`

| หัวข้อ | 📘 เอกสารเดิม | 💻 โค้ดจริง |
|:---|:---|:---|
| **TF ที่คำนวณ trigger** | S30 เป็น primary signal chart | **คำนวณบน M1** (`believe_payload.timeframe = "M1"`) โดย S30 เป็น `entry_timeframe` และ M5 เป็น `context_timeframe` |
| **Bollinger %B** | Period 20, StdDev 2; แตะ 0 = CALL / แตะ 1 = PUT | คำนวณจาก `m1.bb_upper/bb_lower` → `%B = (close-lower)/(upper-lower)`; ยืนยันขาขึ้นเมื่อ **%B ≤ 0.20** (แตะขอบเมื่อ ≤ 0.15 / ≥ 0.85) น้ำหนัก **0.15** |
| **Stochastic** | 13-10-3, เส้น 10/90, hook + ข้าม 50 | ✅ `CoreIndicators.calculate_stochastic()` ใช้ **13-10-3 จริง** (`rolling(13)` → `rolling(10)` → `rolling(3)`) แต่เงื่อนไขที่ให้คะแนนคือ `stoch_k ≤ 10` = OVERSOLD_10 / `≥ 90` = OVERBOUGHT_90 น้ำหนัก **0.25** (hook/kd_cross/crossed_50 ถูกคำนวณเก็บไว้แต่ **ไม่ใช้ให้คะแนน**) |
| **MA Crossover** | Fast (แดง) ตัด Slow (เขียว) | ใช้ **EMA5 vs EMA10** (`ema_fast` vs `ema_slow`) + `close >= ema_fast or close > ema20`; สถานะ `GOLDEN_CROSS / DEATH_CROSS / FLAT` น้ำหนัก **0.30** |
| **RSI** | ไม่ระบุ | มีจริง — `rsi14 < 30` (bullish) / `> 70` (bearish) น้ำหนัก **0.15** |
| **MACD** | ใช้เฉพาะระดับ EXTREME | ใช้ทุกระดับ — `macd > macd_signal` น้ำหนัก **0.10** |
| **Divergence** | ใช้เฉพาะระดับ EXTREME | ให้คะแนนทุกระดับเมื่อ `divergence_detected` และทิศตรงกัน น้ำหนัก **0.15** |
| **Risk filter ผ่าน** | — | `+0.05` ทั้งสองฝั่ง เมื่อไม่มี `trap_alert in (TRAP, GRID_BLOCK)` และไม่มี pattern `DOJI / GRAY_DOJI` |
| **เกณฑ์ตัดสิน** | ต้องเข้าเงื่อนไข 3 ตัวพร้อมกัน | **Weighted score** — `bullish_score ≥ 0.60` **และ** `bullish_structure` → `BUY`; `≥ 0.75` → `EXTREME_BELIEVE` (`belief_summary.status = "active"`) มิฉะนั้น `watch` |
| **Expiry** | 5 นาที | ✅ 5 นาที (`holding_period_minutes: 5`, `analysis_window: "5 x M1 candles"`) |
| **Output** | CALL / PUT / WAIT | `signal_direction` = **BUY / SELL / WAIT** → `believe_analyzer._direction()` แปลงเป็น CALL / PUT |

### 🔀 Believe ระดับ EXTREME
`extreme_believe_active = true` เมื่อ `max(bullish_score, bearish_score) ≥ 0.75` **และ** มีสัญญาณแล้ว
นอกจากนี้ยังคำนวณ `ap_confirmation` (แหล่ง: BOLLINGER, STOCH, MACD, MOMENTUM) และ `ns_confirmation`
(แหล่ง: RSI, STOCH, STRUCTURE — active เมื่อ `|RSI-50| < 20` และ `|STOCH_K-50| < 20`) เก็บไว้ใน payload
แต่ **ทั้งสองบล็อกนี้ไม่ได้ถูกเขียนลงไฟล์ .txt และไม่ได้ถูกใช้ตัดสินใจ** — เป็นข้อมูลใน RAM เท่านั้น

### 🧮 Part 3 ตัดสินอย่างไร (`believe_analyzer.analyze_payload_file`)
```text
อ่าน payload .txt → parse เป็น dict {key: value} (lowercase key)
s30 = s30_bias / s30_direction          (BULLISH→CALL, BEARISH→PUT)
m1  = m1_bias  / m1_direction
m5  = m5_bias  / m5_direction
believe = believe_direction             (BUY→CALL, SELL→PUT)

action = believe  ถ้า believe == s30 == m1  และ (m5 ว่าง หรือ m5 == m1)
         มิฉะนั้น = WAIT

confidence_score = HIGH → 85.0 | MEDIUM → 70.0 | อื่น ๆ → 60.0
expiry_minutes   = 5 (คงที่)
engine_used      = "STRATEGY_BELIEVE"
```
> ⚠️ ในโหมด strategies `s30_bias` มาจาก **สีแท่ง S30** (close ≥ open = BULLISH) ไม่ใช่จาก indicator
> และ `m1_bias` / `m5_bias` มาจาก engine ของ Part 2 — ทั้งสามต้องชี้ทางเดียวกับ Believe ถึงจะยิง

---

## 🛡️ Execution Gate + Money Management (ของจริง)

### ExecutionGate — `POLICY_VERSION = "part4-regime-gated-trend-v1"`

เอกสารเดิมบอกว่า "24-point Execution Gate" และ "Confidence ≥ 60%" — **ไม่ตรงโค้ด**
โค้ดจริงมี **15 ข้อตรวจสอบ** และ threshold คือ **55%** (จาก `settings.json → ai_mode.min_confidence`)

| # | เกต | ค่าคงที่ |
|:--:|:---|:---|
| 1 | `action` ต้องเป็น `CALL` หรือ `PUT` | ถ้า `WAIT` → reject "No trade signal" |
| 2 | `expiry_minutes` **ต้องเท่ากับ 5 เท่านั้น** | ค่าอื่น → reject |
| 3 | `confidence_score ≥ min_confidence` | **55.0** (clamp 0–100) |
| 4 | `agreement_valid` ต้องเป็น true | Gemini/Chronos เห็นไม่ตรงกัน → reject |
| 5 | ต้องมี `m15_direction` | อ่านจาก `m15_bias` / `primary_direction` |
| 6 | ต้องมี `m5_direction` | อ่านจาก `m5_bias` / `m5_trend_direction` |
| 7 | ต้องมี `m5_regime` | อ่านจาก `m5_trend_type` / `regime` |
| 8 | ต้องมี `m5_adx` | — |
| 9 | `m5_adx ≥ MIN_ADX` | **20.0** |
| 10 | ต้องมี `risk_level` | — |
| 11 | `risk_level` ต้องไม่อยู่ใน `{HIGH, CRITICAL, EXTREME}` | — |
| 12 | คุณภาพข้อมูลต้องไม่ `STALE/LOW/POOR/INVALID/BAD` | `m1_quality`, `m5_quality`, `data_quality` |
| 13 | `quality_score ≥ MIN_DATA_QUALITY` | **50.0** |
| 14 | `regime` ต้องไม่เท่ากับ `CHOPPY` | — |
| 15 | `m15_direction` ต้องเท่ากับ `m5_direction` **และ** action ต้องตามทิศนั้น (ห้าม counter-trend) | `UP` → CALL, `DOWN` → PUT |

**ผลลัพธ์:** `approved = action in (CALL, PUT) and ไม่มี rejection_reasons` → ถ้าไม่ผ่าน จะบังคับ `action = "WAIT"`
และต่อท้ายเหตุผลด้วย `" — WAIT"`

### MoneyManager — 7 เงื่อนไข (`can_trade()`)

| # | เงื่อนไข | ค่าใน `settings.json` | ค่า default ในคลาส |
|:--:|:---|:---|:---|
| 1 | ห้ามยิงซ้ำคู่เงินที่มีออเดอร์ค้าง | — | — |
| 2 | `max_concurrent_orders` | **100** | 3 |
| 3 | `max_daily_trades` | **200** | 20 |
| 4 | `max_consecutive_losses` + `cooldown_minutes` | **100** / **5** นาที | 3 / 5 |
| 5 | Stop Loss รายวัน `max_daily_loss` | **500** | 500 |
| 6 | Take Profit รายวัน `max_daily_profit` | **1000** | 1000 |
| 7 | `balance ≥ stake_per_trade` | **35** | 35 |

> ⚠️ ค่าที่ตั้งไว้ตอนนี้ (100 / 200 / 100) **สูงจนแทบไม่ตัดการทำงานเลย** — risk limit ที่มีผลจริงมีแค่ SL/TP รายวันกับ balance
> ข้อ 4 จะไม่ทำงานถูกต้อง เพราะ `MoneyManager` อ่านประวัติจาก `data_base/output_trade/trades_history.csv`
> แต่ `OrderTracker` เขียนลง `data_base/trade_result/trades_history.csv` (คนละไฟล์ → restart แล้วตัวนับรีเซ็ตเป็น 0)

### BrokerExecutor
- validate: `symbol` เป็น string ไม่ว่าง / `action in (CALL, PUT)` / **`expiry_minutes == 5` (hard fail-fast)** / `stake > 0` / api มี `.buy()`
- เรียก `broker_adapter.ensure_connected()` ก่อนทุกครั้ง
- ยิงผ่าน `api.buy(stake, symbol, "call"|"put", 5)` — **retry สูงสุด 3 ครั้ง ห่าง 1 วินาที** แล้ว `raise RuntimeError` (Fail-Fast)
- `_try_digital_v2()` (Digital Option, timeout 3 วิ) **มีโค้ดอยู่แต่ไม่เคยถูกเรียก** — dead code
- หน่วยเงินใน log พิมพ์เป็น **THB** แต่ยอด balance จากโบรกเกอร์แสดงเป็น **$** — หน่วยไม่สอดคล้องกัน

---

## ⚙️ Getting Started

### 1. ความต้องการของระบบ
- **Windows 10/11** (จำเป็น — ใช้ `msvcrt`)
- **Python 3.10 – 3.12** (log การพัฒนาใช้ 3.12.0 win32)
- บัญชี **IQ Option** (DEMO หรือ LIVE)
- Internet สำหรับดึงราคา + ปฏิทินข่าวเศรษฐกิจ (ForexFactory)

### 2. Dependency ที่โค้ด import จริง
```text
pandas  numpy  PyYAML  requests  beautifulsoup4  python-dotenv
google-genai          # ⚠️ SDK ตัวใหม่ — ไม่ใช่ google-generativeai ที่เอกสารเก่าระบุ
iqoptionapi           # unofficial fork ที่รองรับ get_all_init() / start_candles_one_stream
lightgbm              # เฉพาะ ml_mode
onnxruntime           # เฉพาะ ml_mode (Chronos-2 ONNX) + ต้องมีไฟล์ model.onnx ซึ่ง repo ไม่มี
```
> ❌ **ไม่ได้ใช้ `ta-lib`** — indicator ทั้งหมดเขียนเองใน `data_evaluate/*/orchestration/indicator_store/core_indicators.py`
> ❌ repo **ไม่มี `requirements.txt` / `pyproject.toml`**

### 3. Configuration

| ค่า | อยู่ที่ | หมายเหตุ |
|:---|:---|:---|
| IQ Option email / password | `config_setting/settings.json → account.iq_email / iq_password` | ⚠️ plaintext ใน git — `config_loader.get_iq_credentials()` ระบุชัดว่า *"no env vars, no .env file"* |
| IQ Option (สำหรับสแกนเนอร์) | `symbols_scanner/settings_filter.json → account` | ⚠️ ซ้ำอีกชุด |
| Gemini API key | **environment เท่านั้น** — `GEMINI_API_KEY_1`, `_2`, `_3` (หรือ `GEMINI_API_KEY` แบบ legacy) | `gemini_bridge.py` เรียก `load_dotenv()` จึงใส่ในไฟล์ `.env` ที่ root ได้; ช่อง `ai_mode.gemini_api_key` ใน settings.json **ไม่ถูกอ่าน** |
| โหมด / risk / payout | `config_setting/settings.json` | ดู [`settings.json` ฉบับเต็ม](#-settingsjson-ฉบับเต็ม) |
| รายชื่อคู่เงิน (โหมด bot) | `config_setting/symbols_user.json` | SET_A 13 + SET_B 21 |
| รายชื่อคู่เงิน (สแกนเนอร์ standalone) | `symbols_scanner/symbols_user_config.txt` | คนละไฟล์กับข้างบน ⚠️ |

### 4. Running

> 🔴 **ตอนนี้รันไม่ผ่าน** จนกว่าจะแก้ P1 (`chronos_dispatcher.py` หาย) — ดู [P1](#-p1--chronos_dispatcherpy-หายไปจาก-repo--สตาร์ทไม่ได้เลย)

**เส้นทาง A — ผ่านบอท (แนะนำ)** : บอทคัดคู่เงินเองอัตโนมัติทุกครั้งที่สตาร์ท เมื่อ `symbol_mode = "bot"`
```bash
python runner.py                      # ใช้ active_mode จาก settings.json (ตอนนี้ = strategies_mode)
python runner.py --mode strategies    # บังคับโหมด Believe
python main.py                        # เหมือนรัน runner.py แต่แสดง startup banner เพิ่ม
```

**เส้นทาง B — สแกนเนอร์ standalone (Phase 0 แยก)**
```bash
python symbols_scanner/main_filter.py
```
- อ่าน `symbols_scanner/symbols_user_config.txt` + `symbols_scanner/settings_filter.json`
- เขียนรายงาน `symbols_scanner/symbols_onoff_YYYYMMDD_HHMM.txt` (เก็บไฟล์ล่าสุดไฟล์เดียว ลบของเก่าทิ้ง)
- เขียน `symbols_scanner/symbols_trade.json` — **⚠️ ไฟล์นี้บอทไม่ได้อ่าน** (docstring ระบุเองว่า *"Standalone - ไม่ส่งออกไปบอท"*)

> ❌ คำสั่ง `python symbols_scanner/secondary_filter.py` ที่ readme เดิมระบุ **ใช้ไม่ได้** — ไฟล์นี้เป็น library ล้วน ไม่มี `if __name__ == "__main__"`
> ✅ ผู้ที่เขียน `config_setting/symbols.json` จริง ๆ คือ `config_setting/symbols_selection.run_selector()` ซึ่ง `runner.py` เรียกให้อัตโนมัติ

---

## 🖥️ Console Output จริง

> ⚠️ log ข้างบนนี้มาจากการรัน **`ml_mode` เวอร์ชันก่อน refactor** (ยังใช้เส้นทาง `_flush_pending` ที่เรียก Gemini+Chronos พร้อมกัน)
> บรรทัด `[AI Analysis] [SYM:WAIT(45%)] ...` มาจาก `ConsoleUI.show_ai_analysis_complete()` ซึ่ง **เส้นทางปัจจุบัน (`process_decision_files`) ไม่ได้เรียก**
> ดังนั้นถ้ารันโค้ดชุดนี้วันนี้ จะเห็นแค่ `[ Payload Export: n/m | ... ]` และ `[Bot Evaluate Market Complete n asset]` (ดู P9 ข)
> ข้อความ console ทั้งหมดมาจาก `monitoring/console_dashboard.py` และใช้เวลาไทย (UTC+7) ผ่าน `thai_console_log()`

```text
17:29:17 - กำลังเชื่อมต่อโบรกเกอร์  | IQ Option
17:29:20 - เชื่อมต่อ IQ Option สำเร็จ
17:29:22 - ค้นหาและตรวจประเมินรายการสินทรัพย์ที่เหมาะสม
17:29:24 - ส่งออกรายชื่อสินทรัพย์ที่เหมาะสมกับการเทรดแล้ว
17:29:24 - ตรวจพบรายการสินทรัพย์ : EURUSD, EURGBP, GBPUSD, USDJPY
17:29:24 - Time Sync : -0.631s
17:29:24 - บัญชี DEMO | ยอดเงิน: $9908.30
17:29:24 - ระบบรายงานข่าวเศรษฐกิจและการเงิน : วันศุกร์ ที่ 4 กันยายน 2569 : By Athena(Ai)
17:29:26 - เชื่อมต่อสมองกล ML สำเร็จ (Model: PURE_LIGHTGBM [LightGBM + Chronos] พร้อมใช้งาน)
17:29:26 - กำลังเตรียมข้อมูลสินทรัพย์ 4 รายการ : EURUSD, EURGBP, GBPUSD, USDJPY
17:29:30 - ตรวจสอบข้อมูลแท่งเทียนสมบูรณ์ (M1/M5/M15 ครบ 250 แท่ง) : พร้อม 4 รายการ
17:29:30 - เข้าสู่การวิเคราะห์สัญญาณในอีก 30.6 วินาที  (เริ่ม 17:30:01)
17:30:04 - [EURUSD:1.16185] [EURGBP:0.85894] [GBPUSD:1.35265] [USDJPY:156.33500] :: TOTAL=$9908.30
17:30:04 - [Bot Evaluate Market Complete 4 asset]
17:30:10 - [AI Analysis] [EURGBP:WAIT(45%)] [USDJPY:WAIT(45%)] [GBPUSD:WAIT(45%)] [EURUSD:WAIT(55%)]
```

ข้อความที่โหมด strategies จะแสดงแทนบรรทัด ML:
```text
17:29:26 - เปิดใช้งาน Strategies mode
17:29:24 - ตรวจพบรายการสินทรัพย์ : AUDJPY-OTC pay 86% : EURUSD-OTC pay 88% : USDCAD-OTC pay 86% : GBPUSD-OTC pay 87%
```

บรรทัดที่พิมพ์ตอนยิงออเดอร์ / จบสัญญา:
```text
[<payload_id>:<action>:<expiry>นาที:<stake>THB] [ID:<order_id>]
[<payload_id>:<action>:<expiry>นาที:<stake>THB] [ID:<order_id>] [WIN:+29.26THB::9,937THB]
```

**ลำดับการสตาร์ทตามโค้ด (`DataFeedRunner.__init__` → `start()`)**
1. โหลด `settings.json` (reload) → สร้าง single-instance lock `logs/runner.lock`
2. ตัดสินโหมด (CLI ชนะ `active_mode`)
3. เชื่อมต่อโบรกเกอร์ผ่าน `BrokerFactory` → ถ้าไม่สำเร็จ `os._exit(1)`
4. ลงทะเบียน `OP_code.ACTIVES` จาก `api.get_all_init()` (turbo + binary)
5. ถ้า `symbol_mode == "bot"` → รัน `run_selector()` เขียน `symbols.json`
6. โหลด symbols + payouts → แสดง Time Sync offset
7. ดึง balance → **ถ้าดึงไม่ได้ `raise RuntimeError` (Fail-Fast)**
8. โหลด orchestrator ของโหมดที่เลือก + override `data_evaluate.output_dir` เป็นโฟลเดอร์ของโหมด
9. Pre-warm สมอง (ml → Chronos / ai → Gemini / strategies → log อย่างเดียว)
10. สร้าง `DecisionManager` (Part 3) + `ExecutorManager` (Part 4) ← **💥 พังตรงนี้ (P1)**
11. `warmup_all_symbols()` → 250 แท่ง/TF → ถ้าไม่มีคู่ไหนผ่านเลย `raise RuntimeError`
12. นับถอยหลังไป `:01.500` → วนลูป `run_cycle()`

---

## 📁 Output Files

| ไฟล์ | เขียนโดย | schema |
|:---|:---|:---|
| `data_base/output_feed/<SYM>/<SYM>_<TF>.csv` | `csv_writer.py` (Part 1) | 8 คอลัมน์: `timestamp, open, high, low, close, volume, age, quality` (250 แถว + header) — `quality` เช่น `FRESH` / `STALE` |
| `data_base/output_feed/<SYM>/summary_<sym>.txt` | Part 1 | สรุปสถานะคู่เงิน |
| `data_base/output_evaluate/<mode>/<SYM>/<ID>.txt` | orchestrator (Part 2) | payload 99 หรือ 114 บรรทัด (ตามโหมด) — retention 30 ไฟล์ |
| `data_base/output_decision/strategies_decision/<SYM>/<ID>.json` | `DecisionManager` | decision ของโหมด Believe (atomic write `.tmp` → `os.replace` + `fsync`) |
| `data_base/output_decision/ai_decision/<SYM>/<ID>.txt` | `SystemPrompt._save_decision_txt()` | **เนื้อหาเป็น JSON 7 ฟิลด์**: `ID, symbol, action, expiry_minutes, confidence_score, reason_th` |
| `data_base/output_decision/ai_decision/<SYM>/decisions.csv` | `SystemPrompt._save_decision_csv()` | SSOT ของ decision ฝั่ง AI |
| `data_base/output_decision/ai_decision/<SYM>/<ID>.json` | `DecisionManager._atomic_json()` | ⚠️ repo ปัจจุบันมี **0 ไฟล์** — เพราะ `ENABLE_DECISION_JSON = False` ปิดการเขียนฝั่ง dispatcher (ดู P3) |
| `data_base/output_trade/decision_gate_audit.csv` | `ExecutorManager` | 14 คอลัมน์: `timestamp, symbol, payload_id, prompt_filepath, gemini_action, gemini_confidence, chronos_action, chronos_confidence, agreement_valid, gate_approved, final_action, final_confidence, reason, broker_result` |
| `data_base/trade_result/trades_history.csv` + `<SYM>.csv` | `OrderTracker` | `timestamp, order_id, symbol, action, stake, expiry_minutes, result, profit_amount, confidence_score, ai_engine, reason_th` — ⚠️ repo ไม่มีโฟลเดอร์นี้ (ยังไม่เคยเทรดสำเร็จในรอบปัจจุบัน) |
| `logs/logs_data_trade/trades_history.csv` | log | มีข้อมูลจริง 6 แถว (SIM + WIN 1 รายการ) |
| `data_evaluate/<mode>/data_evaluate/orchestration/calendar_YYYY-MM-DD.txt` | `news_calendar.py` | ปฏิทินข่าว 1 ไฟล์/วัน ลบของเก่าอัตโนมัติ — ⚠️ path ที่โค้ดคำนวณจริง **ซ้อน `data_evaluate` สองชั้น** (ดู P7) ส่วนไฟล์ที่มีอยู่ใน repo ตอนนี้อยู่ที่ `data_evaluate/<mode>/orchestration/calendar_2026-09-21.txt` ซึ่งเป็นผลงานของโค้ดเวอร์ชันเก่า |
| `logs/runner.lock` | `runner.py` | single-instance lock (Windows `msvcrt.locking`) |

---

## 🔧 `settings.json` ฉบับเต็ม

ค่าจริง ณ commit นี้ (ตัด `iq_email` / `iq_password` ออกเพื่อความปลอดภัย)

```jsonc
{
  "symbol_mode": "bot",              // "bot" = บอทคัดเอง | ค่าอื่น = ใช้ symbols.json คงที่
  "max_symbols": 4,                  // ตัดตอน Top N
  "min_payout": 84,                  // เกณฑ์ payout ขั้นต่ำ (%)
  "active_mode": "strategies_mode",  // ml_mode | ai_mode | strategies_mode

  "account": {
    "account_type": "DEMO",          // DEMO | LIVE
    "iq_email": "<redacted>",
    "iq_password": "<redacted>",
    "stake_per_trade": 35,
    "max_daily_profit": 1000,        // TP รายวัน
    "max_daily_loss": 500,           // SL รายวัน
    "max_daily_trades": 200,         // ⚠️ สูงมาก = เกือบไม่ตัด
    "max_concurrent_orders": 100,    // ⚠️ สูงมาก = เกือบไม่ตัด
    "max_consecutive_losses": 100,   // ⚠️ สูงมาก = cooldown แทบไม่ทำงาน
    "cooldown_minutes": 5
  },

  "ml_mode": {
    "enabled": true,
    "model": "CHRONOS_2_ONNX",
    "min_confidence": 55,
    "use_chronos": true,
    "chronos2_model_path": "data_trade\\execution_gate\\chronos-2-onnx\\model.onnx"  // ❌ ไฟล์ไม่มีอยู่
  },

  "ai_mode": {
    "enabled": true,
    "provider": "GEMINI",
    "primary_model": "gemini-3.5-flash-lite",
    "primary_daily_limit": 500,
    "secondary_model": "gemini-3.5-flash-lite",   // agent.md ระบุ gemini-3.1-flash-lite — โค้ดบังคับใช้ primary
    "secondary_daily_limit": 0,                   // 0 = ปิดช่องทางสำรอง
    "gemini_api_key": "",                          // ⚠️ ไม่ถูกอ่าน — ใช้ env GEMINI_API_KEY_1..3
    "deepseek_session_index": 1,
    "timeout_seconds": 25,
    "max_consecutive_failures": 3,
    "min_confidence": 55
  },

  "session": { "trading_hours": "00.00-24.00", "timezone": "Asia/Bangkok" },
  "active_broker": "IQ_OPTION",        // QUOTEX / POCKET_OPTION เป็น stub ยังไม่ทำงาน

  "data_feed": {
    "enable_csv_export": true,
    "csv_manager": { "base_dir": "data_base/output_feed" },
    "data_adapter": {
      "default_candle_count": 250,
      "min_candle_count": 21,
      "strategies_timeframes": ["S30", "M1", "M5"],
      "strategies_enable_m15": false,   // ← เหตุผลที่ m15_bias ว่างในโหมด Believe
      "m5_seconds": 300, "m15_seconds": 900, "s30_seconds": 30,
      "retry_attempts": 0,              // Zero Tolerance — ไม่ retry
      "retry_delay": 0
    }
  },

  "data_evaluate": {
    "enable_txt_export": true,
    "output_dir": "data_base/output_evaluate",
    "mode_output_dirs": {
      "ml_mode": "data_base/output_evaluate/ml_mode",
      "ai_mode": "data_base/output_evaluate/ai_mode",
      "strategies_mode": "data_base/output_evaluate/strategies_mode"
    }
  },

  "data_decision": {
    "output_dir": "data_base/output_decision",
    "ai_output_dir": "data_base/output_decision/ai_decision",
    "strategies_output_dir": "data_base/output_decision/strategies_decision"
  },

  "data_trade": {
    "enable_live_execution": true,      // false = SIGNAL_ONLY (ไม่ยิงออเดอร์จริง)
    "trade_history_file": "data_base/output_trade/trades_history.csv"   // ⚠️ คนละที่กับที่ OrderTracker เขียน
  }
}
```

---

## 🐛 ข้อบกพร่องที่พบในโค้ดปัจจุบัน (ยังไม่แก้)

เอกสารนี้บันทึกไว้เพื่อให้รู้ว่า **ทำไมบอทยังไม่เทรด** — เรียงตามความรุนแรง

### 🔴 P1 — `chronos_dispatcher.py` หายไปจาก repo → สตาร์ทไม่ได้เลย
```text
data_trade/executor_manager.py:45
    from data_trade.execution_gate.chronos_dispatcher import ChronosDispatcher
ModuleNotFoundError: No module named 'data_trade.execution_gate.chronos_dispatcher'
```
- เรียกใน `ExecutorManager.__init__` ซึ่ง `DataFeedRunner.__init__` สร้างแบบไม่มีเงื่อนไข → **พังทุกโหมด แม้จะใช้ strategies_mode**
- `runner.py:169` ก็ import ตัวเดียวกันนี้ในสาขา `ml_mode`
- `settings.json → ml_mode.chronos2_model_path` ชี้ไป `data_trade\execution_gate\chronos-2-onnx\model.onnx` — **ไม่มีไฟล์ `.onnx` ใด ๆ ใน repo**
- log 4 ก.ย. 2569 ยังเชื่อมต่อ Chronos สำเร็จ แสดงว่าไฟล์เคยมีอยู่ แล้วหายไปตอน commit ภายหลัง
- **ทางแก้:** กู้ไฟล์จากเครื่องเดิม/branch อื่น หรือเอา import ออกชั่วคราวถ้าจะรันเฉพาะ `strategies_mode`

### 🔴 P2 — ExecutionGate ออกแบบมาเพื่อ M15 แต่โหมด Believe ไม่มี M15 จริง → เกตตรวจผิดตัว + reject เกินจำเป็น
ผมทดสอบ regex ของ `ExecutionGate._extract_evidence()` กับ payload จริงแล้ว — **มันอ่านฟิลด์ที่ย่อหน้าได้ปกติ** (parse ได้ 86 key จากไฟล์ตัวอย่าง) ปัญหาจริงอยู่ที่ **ความไม่เข้ากันของ schema** ระหว่าง Part 2 โหมด strategies กับ Part 4:

| ประเด็น | รายละเอียด |
|:---|:---|
| **M15 ปลอม** | `orchestrator.py:240` ทำ `candles_dict.setdefault('M15', candles_dict['M5'])` → `m15_bias` ใน payload **คือค่าที่คำนวณจากแท่ง M5** ไม่ใช่ M15 จริง (มีเฉพาะ strategies_mode — ai/ml mode ไม่มีบรรทัดนี้) |
| **เกตข้อ 15 ไร้ความหมาย** | `m15_direction != m5_direction` → reject "M15/M5 direction conflict" **เป็นไปไม่ได้เลย** เพราะทั้งสองอ่านจาก M5 ก้อนเดียวกัน → เท่ากันเสมอ |
| **ขัด comment ตัวเอง** | comment เหนือบรรทัดนั้นเขียนว่า *"without presenting M5 as an independent M15 feed"* แต่โค้ดทำตรงข้าม และ comment ถัดไประบุว่า *"Timeframe sync is strictly prohibited... Data from M1, M5, M15 must remain independent"* |
| **ขัดกฎ Fail-Fast** | `agent.md` Rule 7 ห้ามใช้ข้อมูลแทน (fallback) โดยเด็ดขาด — การเอา M5 ไปสวมเป็น M15 คือ fallback ตรง ๆ |
| **เกตที่ reject จริงในโหมดนี้** | เพราะ M15 ผ่านเสมอ ตัวที่จะตัดสัญญาณจริงคือ: `regime == CHOPPY`, `adx < 20`, `dl_risk_level in {HIGH, CRITICAL, EXTREME}`, `dl_quality_score < 50`, `m1_quality/m5_quality = STALE`, และ `confidence < 55` |
| **Confidence ผ่านง่าย** | `believe_analyzer` ให้ 85 (HIGH) / 70 (MEDIUM) / **60 (ค่า default เมื่อ `believe_confidence` เป็น LOW หรืออ่านไม่ได้)** → ผ่านเกณฑ์ 55 ทั้งสามกรณี รวมถึงกรณีที่ Believe บอก `LOW` ด้วย |

> 🔎 ตัวอย่าง payload เก่าที่ตรวจ: `m5_trend_type: CHOPPY`, `dl_risk_level: HIGH`, `dl_quality_score: 53`
> → แค่ 2 ค่าแรกก็ reject แล้ว 2 ข้อ นี่น่าจะเป็นสาเหตุที่ log ช่วง 20 ก.ย. มีแต่ `WAIT`

**ทางแก้ที่ควรทำ:** ให้ Part 4 มี policy แยกต่อโหมด (เช่น `part4-believe-s30-v1` ที่ใช้ S30+M1 แทน M15+M5) หรือเปิด `strategies_enable_m15 = true` เพื่อให้ M15 เป็นของจริง แล้วเลิก alias

### 🟠 P3 — Part 3 เขียน `.json` แต่ฝั่ง AI/ML dispatcher เขียนแค่ `.txt` → ไฟล์ decision สะสมสองแบบ
- `DecisionManager._atomic_json()` เขียน `.../<ID>.json` ✅ (ทุกโหมด)
- แต่ใน `ai_mode` / `ml_mode` มีผู้เขียน **สองรายลงโฟลเดอร์เดียวกัน** `data_base/output_decision/ai_decision/<SYM>/`
  - `SystemPrompt` (dispatcher) → `.txt` (เนื้อหาเป็น JSON) + `decisions.csv` + `<SYM>_decisions.csv`
    เพราะ `ENABLE_DECISION_JSON = False` ปิดการเขียน `.json` ของตัวเองไว้
  - `DecisionManager` → `<ID>.json`
- `ExecutorManager._latest_decision_file()` กรองเฉพาะ `*.json` → อ่านของ `DecisionManager` เท่านั้น
- **หลักฐานใน repo:** `output_decision/` มี `.txt` **354 ไฟล์** และ `.json` **0 ไฟล์**
  → แปลว่าที่ผ่านมาไฟล์ decision ทั้งหมดมาจาก dispatcher (เส้นทางเก่า `_flush_pending`) และ **`DecisionManager` ยังไม่เคยเขียนไฟล์สำเร็จเลยสักครั้ง**
- **ผล:** ถ้ารันเส้นทางใหม่ (`process_decision_files`) ใน ai/ml mode แล้วยังไม่มี `.json` → `continue` เงียบ ๆ ไม่ยิง ไม่แจ้ง error (ขัดกฎ No Silent Failures ข้อ 1)
- **หมายเหตุ:** `strategies_mode` ไม่กระทบข้อนี้ เพราะมี `DecisionManager` เป็นผู้เขียน `.json` เพียงรายเดียว

### 🟠 P4 — `runner.py` สาขา `ai_mode` อ้างตัวแปรที่ยังไม่ประกาศ → `NameError`
```python
# runner.py:175-179  (ภายใน if ai_enabled:)
SystemPrompt.prewarm_and_test_ai(self.symbols)
provider = ai_cfg.get("provider", "GEMINI")          # ❌ ai_cfg ไม่เคยถูกกำหนด
primary_model = ai_cfg.get("primary_model") or ...
```
- ต้องเป็น `ai_cfg = self.settings.get("ai_mode", {})` ก่อนใช้งาน
- **ผล:** รัน `python runner.py --mode ai` → `NameError: name 'ai_cfg' is not defined`

### 🟠 P5 — เส้นทาง trade แบบ Gemini + Chronos เป็น dead code
- `ExecutorManager.on_orchestrator_payload_saved()` → `_flush_pending()` → `process_ai_decisions_concurrent()`
  เป็นเส้นทางที่เขียน `decision_gate_audit.csv` (มีข้อมูลจริงถึง 20 ก.ย. 2569)
- แต่ **ไม่มีโค้ดที่ไหนเรียก `on_orchestrator_payload_saved()` เลย** — `runner.py` เรียกแค่ `process_decision_files()`
- docstring หัวไฟล์ `executor_manager.py` ยังอธิบาย flow แบบเก่าอยู่ → ทำความเข้าใจผิดได้ง่าย

### 🟡 P6 — `MoneyManager` อ่านประวัติคนละไฟล์กับที่ `OrderTracker` เขียน
- อ่าน: `data_base/output_trade/trades_history.csv` (จาก `settings.json → data_trade.trade_history_file`)
- เขียน: `data_base/trade_result/trades_history.csv` (hardcode ใน `OrderTracker.__init__`)
- **ผล:** restart แล้ว `daily_pnl / daily_trades / consecutive_losses / last_loss_time` รีเซ็ตเป็น 0 → SL/TP รายวันและ cooldown ผิดเพี้ยน

### 🟠 P7 — ปฏิทินข่าว: path ซ้อนกันสองชั้น + fail-fast ถ้าเน็ตล่มตอนสตาร์ท
`data_evaluate/<mode>/news_calendar.py`
```python
BASE_DIR   = Path(__file__).resolve().parent.parent      # = data_evaluate/<mode>/
OUTPUT_DIR = BASE_DIR / "data_evaluate" / "orchestration" # = data_evaluate/<mode>/data_evaluate/orchestration/
```
- path ที่คำนวณได้จึง **ซ้อน `data_evaluate` สองชั้น** และไม่ตรงกับไฟล์ที่มีอยู่จริงใน repo
  (`data_evaluate/strategies_mode/orchestration/calendar_2026-09-21.txt`) — เป็นผลงานของโค้ดเวอร์ชันก่อนจัดโฟลเดอร์ใหม่
- `ensure_calendar_news()` ถูกเรียกใน `Orchestrator.__init__` และ **ถ้ายังไม่มีไฟล์ของวันนี้ จะดึงสดจาก ForexFactory เสมอ**
  (`https://www.forexfactory.com/calendar`) → ถ้าเน็ตล่ม/โดน block/parse ไม่ผ่าน จะ `raise`
- `Orchestrator.__init__` ครอบด้วย `try/except` ที่ `logger.exception(...)` แล้ว **`raise` ต่อ** → **บอทสตาร์ทไม่ติด**
- **ผล:** ต่อให้แก้ P1 แล้ว บอทยังอาจตายที่ขั้นตอนนี้ถ้าดึงข่าวไม่สำเร็จ (และ path ที่เขียนก็ผิดที่)
- **ทางแก้:** เปลี่ยน `BASE_DIR` เป็น `Path(__file__).resolve().parent` แล้วชี้ `OUTPUT_DIR` ไป `orchestration/` ตรง ๆ
  และพิจารณาไม่ให้ news calendar เป็น hard dependency ของการสตาร์ท

### 🟡 P8 — ข้อมูลตัวอย่างใน repo เป็นของโค้ดเวอร์ชันเก่า → รันทับของเก่าจะ fail-fast
สำรวจ `data_base/` ณ commit นี้:

| สิ่งที่พบ | จำนวน | ผลกระทบ |
|:---|:---:|:---|
| `data_base/output_feed/<SYM>/` | 19 คู่เงิน | มีแต่ `_M1.csv`, `_M5.csv`, `_M15.csv` |
| `*_S30.csv` | **0 ไฟล์** | Part 2 โหมด strategies อ่าน `S30/M1/M5` จากดิสก์แบบ fail-fast → `FileNotFoundError: FAIL-FAST: CSV file not found for <SYM> S30` ทันที |
| `data_base/output_evaluate/` | **ไม่มีโฟลเดอร์** | payload ไม่เคยถูกสร้างภายใต้โครงโฟลเดอร์ใหม่ |
| `data_base/output_decision/**/*.json` | **0 ไฟล์** | มีแต่ `.txt` 354 ไฟล์ (ดู P3) |
| `data_base/trade_result/` | **ไม่มีโฟลเดอร์** | `OrderTracker` ยังไม่เคยเขียนผลเทรดในรอบปัจจุบัน |
| `decision_gate_audit.csv` | อ้าง path `data_base/evaluate_output\...` | เป็น path เก่าที่ยกเลิกไปแล้ว (มี mixed separator `\` กับ `/` ด้วย) |

> ✅ **ไม่ใช่บั๊กของโค้ด** — `data_adapter.py` เวอร์ชันปัจจุบันเขียน S30 CSV ถูกต้องแล้ว
> (`for tf, df in [('S30', ...), ('M1', ...), ('M5', ...)]`)
> แต่แปลว่า **ข้อมูลใน repo เป็นของเวอร์ชันก่อนมี S30** → ถ้ารัน Part 2 ทับข้อมูลเก่าโดยไม่ warm-up ใหม่จะล่มทันที
> และ `.csv` ชุดนี้ (9.1 MB) ไม่ควรถูก commit ตั้งแต่แรก

### 🟡 P9 — `BaseEngine.analyze()` signature/type-hint เลื่อน + console รายงาน "สำเร็จ" แม้ทุกคู่เงินล้มเหลว

**(ก) Type hint โกหก (ขัด `agent.md` Rule 2)**
```python
# data_evaluate/<mode>/orchestration/base_engine.py:47
def analyze(self, payload: Dict[str, Any], **kwargs) -> Dict[str, Any]:   # ← ประกาศเป็น Dict
# data_evaluate/<mode>/orchestration/advanced_tools/advanced_tools_manager.py:44-52
candle_data = self.candle_pattern.analyze(df_m5)                          # ← จริง ๆ ส่ง pd.DataFrame
conflict_data = self.conflict.analyze(df_m5, basic_payload=basic_payload) # ← subclass รับ candles_df
```
- subclass ทั้ง 10 ตัวประกาศ `_analyze(self, candles_df: pd.DataFrame, **kwargs)` — ไม่มีตัวไหน override `analyze()`
- ตอนนี้ **รันผ่าน** (ผม repro แล้ว: `basic_payload` ไหลเข้า `**kwargs` ไปถึง `_analyze` ได้) แต่พึ่งพาพฤติกรรมโดยบังเอิญ
- error log 17 ส.ค. 2569 มี `TypeError: BaseEngine.analyze() got multiple values for argument 'payload'` **343 ครั้ง** — เป็น signature เวอร์ชันเก่า ซึ่งถูกแก้ไปแล้วในโค้ดปัจจุบัน
- `BaseEngine.analyze()` ยังทำ `if payload is None: raise` กับ `validate_input(payload)` โดยสมมติว่าเป็น dict → ถ้า subclass ไหนเพิ่ม `validate_input` ที่เรียก `.get()` จะพังทันที

**(ข) `ConsoleUI.show_payload_export()` นับรวมของที่ fail เป็น "สำเร็จ"**
```python
# monitoring/console_dashboard.py:417-419
thai_console_log(f"[ Payload Export: {len(ready)}/{len(ready)+len(failed)} | Failed: {...} ]")
thai_console_log(f"[Bot Evaluate Market Complete {len(ready)} asset]")
```
และ `Orchestrator.evaluate_cycle()` เก็บ exception ของแต่ละคู่เงินไว้เป็น `logger.exception(...)` แล้ว **วนต่อจนครบ** ก่อนจะพิมพ์บรรทัดนี้
→ ถ้า Part 2 พัง **ทุก** คู่เงิน console ยังขึ้น `[Bot Evaluate Market Complete 0 asset]` โดยไม่มีข้อความเตือนบนจอ
(ขัดกฎ No Silent Failures — ต้องเปิด `logs/logs_data_evaluate/errors/error.log` ดูเองจึงจะรู้)

**(ค) docstring จำนวนบรรทัดไม่ตรง**
`evaluate_cycle()` เขียนว่า *"writes 100-line prompt payload"* — จริง ๆ คือ 114 บรรทัด (strategies) / 99 บรรทัด (ai/ml)

### 🟡 P10 — `.gitignore` มี backtick คร่อมไว้ทั้งไฟล์
```text
```            ← บรรทัด 1
# Python
__pycache__/
...
```            ← บรรทัดสุดท้าย
```
- backtick ไม่ใช่ pattern ที่ git เข้าใจ → บรรทัดแรก/สุดท้ายเป็นแค่ comment ประหลาด
- ผลข้างเคียงที่เห็นชัด: `__pycache__/` และ `*.pyc` **ถูก commit จริง** (มี 45 ไฟล์ `.pyc` ใน repo)

### 🟡 P11 — `data_evaluate/` โค้ดซ้ำ 3 ชุด
- `ml_mode/`, `ai_mode/`, `strategies_mode/` มี `orchestration/` เหมือนกันแทบทุกไฟล์ (indicator_store, market_classifier, advanced_tools)
- ต่างกันแค่ `orchestrator.py` (1,319 / 1,319 / 1,358 บรรทัด)
- ขัดกับกฎ SSOT (Rule 10) ที่ `agent.md` ตั้งไว้เอง — แก้บั๊ก 1 จุดต้องแก้ 3 ที่

### 🟡 P12 — dead code / ไฟล์ที่ไม่ควรมีใน git
| รายการ | รายละเอียด |
|:---|:---|
| `config_setting/symbols_selector.py` (35 KB) | ไม่มีที่ไหน import — `runner.py` ใช้ `symbols_selection.py` |
| `broker_executor._try_digital_v2()` | ไม่เคยถูกเรียก |
| `data_feed/bridge_pocket_adapter/`, `bridge_quotex_adapter/` | stub 59 บรรทัด ยังไม่ทำงาน |
| `data_decision/.../deepseek_bridge.py` | stub 48 บรรทัด |
| `backups/` (16 session), `logs/session_backups/` (2 ชุด) | สำเนา repo ทั้งชุด รวม credential ซ้ำหลายชุด |
| `logs/logs_data_feed/errors/error.log` | 30 MB |
| `.agents/skills_67/` | ชุด skill ของ AI agent (Solana/Polymarket/quant) ไม่เกี่ยวกับบอท — 679 ไฟล์ `.md` |
| `__pycache__/`, `*.pyc` | 45 ไฟล์ — 1 ในนั้นมี credential ฝังอยู่ |

### 🟡 P13 — ความไม่สอดคล้องอื่น ๆ ที่ควรทราบ

| หัวข้อ | รายละเอียด |
|:---|:---|
| หน่วยเงิน | log/console พิมพ์ `THB` แต่ balance จากโบรกเกอร์เป็น `$` และ `stake_per_trade = 35` ไม่ระบุว่าหน่วยไหน |
| `ai_confidence_score` | payload เติม `"รอการวิเคราะห์จาก AI"` (ภาษาไทย) → `_fmt_num()` คืน string ไทย → ฝั่ง gate แปลงเป็น float ไม่ได้ |
| console message | `show_data_prep_result()` hardcode "M1/M5/M15" แม้โหมด strategies จะใช้ S30/M1/M5 |
| `s30_bias` ไม่ใช่อินดิเคเตอร์ | Part 2 กำหนด `s30_bias = BULLISH ถ้า close >= open` (แค่สีแท่ง S30) แต่ `believe_analyzer` บังคับให้ `believe == s30 == m1` → สัญญาณถูกกรองทิ้งราวครึ่งหนึ่งโดยสุ่ม เพราะสีแท่ง S30 ไม่เกี่ยวกับ logic ของ Believe |
| `believe_confidence = LOW` ยังได้ confidence ผ่าน gate | `believe_analyzer` map `HIGH→85 / MEDIUM→70 / อื่น ๆ→60` และ gate ต้องการ ≥ 55 → แม้ Believe บอก LOW (คะแนนไม่ถึง 0.60) ก็ยังได้ 60 ซึ่งผ่าน gate (ปกติจะติด `action = WAIT` ก่อนหน้านั้นอยู่แล้ว) |
| docstring ล้าสมัย | `ai_dispatcher.py` อ้าง `data_base/ai_decision_output/` • `executor_manager.py` อธิบาย flow `_flush_pending` ที่ตายแล้ว • `evaluate_cycle()` อ้าง "100-line payload" • `config_loader.py` อ้าง `config/settings.json` (จริงคือ `config_setting/settings.json`) |
| รายชื่อคู่เงิน 2 ชุด | `config_setting/symbols_user.json` (13+21) กับ `symbols_scanner/symbols_user_config.txt` (13+21) เนื้อหาตรงกันแต่เป็น **คนละไฟล์ คนละฟอร์แมต** → แก้ที่เดียวแล้วลืมอีกที่จะพลาดแบบเงียบ ๆ |
| `agent.md` Rule 20/23/26 | ยังอ้าง "99 บรรทัด", `data_base/orchestrator/`, `data_base/evaluate_output/`, SET A 14 / SET B 20, `symbols_scanner/symbols.json` — **ล้าสมัยทั้งหมด** (จริง: 99/114 บรรทัด, `output_evaluate/<mode>/`, SET A 13 / SET B 21, `symbols_trade.json`) |
| `docs/` Part 2–4 | เนื้อในเหมือนกันทั้ง 3 ไฟล์ (copy-paste) และยังอ้าง "99 บรรทัด + 24 Execution Gates" |
| `logs/runner.lock` | ถูก commit ขึ้น git — เป็น lock ของ Windows `msvcrt` ไม่ควรมีใน repo |
| `.vscode/settings.json` | `.gitignore` ระบุให้ ignore แต่ถูก commit อยู่ |

---

## 🗃️ ประวัติการย้าย path (พบจาก log) + error เก่าที่แก้แล้ว

### path ที่ถูกย้ายมาแล้วหลายรอบ — เอกสาร/log เก่าอ้างชื่อที่ไม่มีอยู่จริงแล้ว

| ประเภท | path เก่า (ยังปรากฏใน log / เอกสาร / audit CSV) | path ปัจจุบัน (ตาม `settings.json`) |
|:---|:---|:---|
| CSV ราคา (Part 1 → 2) | `data_base/feed_output/iq_option/<SYM>/`<br>`data_feed/ohclv_output/iq_option/<SYM>/` *(สะกด `ohclv` ผิด)* | `data_base/output_feed/<SYM>/` |
| payload (Part 2 → 3) | `data_evaluate/payload_output/<SYM>/`<br>`data_base/orchestrator/<SYM>/`<br>`data_base/evaluate_output/<SYM>/` | `data_base/output_evaluate/<mode>/<SYM>/` |
| decision (Part 3 → 4) | `data_base/ai_decision_output/<SYM>/` *(ยังมีอยู่ใน docstring ของ `ai_dispatcher.py`)* | `data_base/output_decision/{ai_decision\|strategies_decision}/<SYM>/` |
| ผลเทรด | — | `data_base/trade_result/` (OrderTracker) ⚠️ ขัดกับ `data_base/output_trade/` (MoneyManager) — ดู P6 |
| source code Part 2 | `data_evaluate/orchestrator.py`, `data_evaluate/orchestration/...` | `data_evaluate/<mode>/orchestrator.py` — แต่ **import ในโค้ดยังเขียน `from data_evaluate.orchestration...`** โดย `mode_loader._install_mode_namespace()` แอบ trampoline `sys.modules["data_evaluate.orchestration"].__path__` ไปชี้โฟลเดอร์ของโหมดตอน runtime |

> ⚠️ เพราะ trampoline นี้ `data_evaluate/orchestration/` **ไม่มีอยู่จริงบนดิสก์** และ `data_evaluate/` ไม่มี `__init__.py`
> → ถ้า import `data_evaluate.orchestration.*` ก่อนที่ `load_orchestrator_class()` จะรัน จะได้ `ModuleNotFoundError`
> และ docstring ใน `ai_dispatcher.py` / `order_tracker.py` / `executor_manager.py` ยังอ้าง path เก่าอยู่ทั้งหมด

### error ใน log ที่ **แก้ไปแล้วในโค้ดปัจจุบัน** (อย่าหลงไปแก้ซ้ำ)

| error ที่พบใน log | จำนวน | สถานะปัจจุบัน |
|:---|:---:|:---|
| `TypeError: BaseEngine.analyze() got multiple values for argument 'payload'` (17 ส.ค. 2569) | 343 | ✅ แก้แล้ว — subclass ปัจจุบันไม่ override `analyze()` (แต่ยังเหลือปัญหา type hint — ดู P9 ก) |
| `ValueError: Division by zero in RSI calculation (avg_loss contains 0)` (19 ส.ค. 2569) | 8 | ✅ แก้แล้ว — `_calculate_rsi` ใน `divergence_analyzer` ถูกลบออก เปลี่ยนไปใช้ `CoreIndicators.calc_rsi_series()` ที่มี `.replace(0, 1e-9)` |
| `FileNotFoundError: CSV file not found for <SYM> M5 at data_base/feed_output/...` (28 ส.ค. 2569) | หลายร้อย | ✅ แก้แล้วด้วยการย้าย path → `data_base/output_feed/` (แต่ข้อมูลใน repo ยังเป็นของเก่า — ดู P8) |

### error ใน log ที่ **ยังต้องระวัง**

| error | จำนวน | สาเหตุ |
|:---|:---:|:---|
| `RuntimeError: FAIL-FAST: AI a...` / `FAIL-FAST: Gemi...` | 1,681 / 1,529 | Gemini ตอบไม่ตรง schema / quota หมด / timeout — เกิดในเส้นทางเก่า |
| `RuntimeError: IQ Option connection lost — no retry allowed` | 577 | Zero Tolerance (`retry_attempts: 0`) — เน็ตสะดุดครั้งเดียว = บอทตายทั้งกระบวนการ (`os._exit`) |
| `FAIL-FAST Data gap detected (39060.0s > 300s)` | หลายร้อย | เกิดเมื่อสตาร์ทบอททิ้งช่วงข้ามวัน แล้วเจอ CSV เก่าในดิสก์ → validator มองว่าแท่งขาด 10+ ชั่วโมง |
| `Cannot acquire lock for stream GBPUSD-OTC within 8s` / `start_candles_one_stream late for 20 sec` | — | stream ของ IQ Option ช้ากว่า 8 วิ (20 ก.ย. 2569 — error ล่าสุดใน log) |
| `ValueError: X has 5 features, but HistGradientBoosting...` | 4 | model `.pkl` กับ feature set ไม่ตรงกัน (ml_mode) |

---

## 🔐 ความปลอดภัย (ต้องทำด่วน)

🔴 **credential จริงถูก commit ขึ้น public repo**

| ไฟล์ | สิ่งที่รั่ว |
|:---|:---|
| `config_setting/settings.json` | `account.iq_email` + `account.iq_password` (plaintext) |
| `symbols_scanner/settings_filter.json` | ชุดเดียวกัน |
| `logs/session_backups/*/config_setting/settings.json` (4 ไฟล์) | ชุดเดียวกัน |
| `logs/session_backups/*/config_setting/grabber/settings.json` | ชุดเดียวกัน |
| `config_setting/__pycache__/config_loader.cpython-312.pyc` | string ฝังใน bytecode |

**ขั้นตอนแก้ที่แนะนำ**
1. **เปลี่ยนรหัสผ่าน IQ Option ทันที** — ต่อให้เป็นบัญชี DEMO อีเมลนั้นมักใช้ร่วมกับบัญชีจริง
2. ย้าย credential ออกไป `.env` (ซึ่ง `.gitignore` ครอบคลุมอยู่แล้ว) แล้วแก้ `config_loader.get_iq_credentials()` ให้อ่านจาก env
   — ตอนนี้ docstring ระบุชัดว่า *"no env vars, no .env file"* จึงต้องแก้โค้ดด้วย ไม่ใช่แค่ย้ายไฟล์
3. `git rm --cached` ไฟล์ `settings.json`, `settings_filter.json`, `__pycache__/`, `logs/`, `backups/` แล้วแก้ `.gitignore` (เอา backtick ออก)
4. **ลบประวัติ git** ด้วย `git filter-repo` หรือ BFG — เพราะ credential ยังอยู่ใน commit เก่าถึงจะลบไฟล์แล้วก็ตาม
5. ถ้า repo ยัง public → **ตั้งเป็น private** จนกว่าจะล้างประวัติเสร็จ
6. Gemini API key ตอนนี้ปลอดภัย (อ่านจาก env เท่านั้น) — ตรวจว่า `.env` ไม่ถูก track

---

## 🛡️ Strict System Disciplines (Core Rules)

กฎฉบับเต็ม 27 ข้ออยู่ใน **`agent.md`** — นี่คือข้อที่เกี่ยวกับสถาปัตยกรรมโดยตรง

1. **Immutability of Part 1 & 2** — `data_feed/` และ `data_evaluate/` ถือว่าเสร็จสมบูรณ์ **ห้ามแก้** (Rule 18)
2. **Single Source of Truth (SSOT)** — ห้ามคำนวณ indicator ซ้ำ ทุกโมดูลต้องอ้างอิง `IndicatorStore` (Rule 10)
   > ⚠️ ในทางปฏิบัติ `data_evaluate/` มีโค้ดซ้ำ 3 ชุด — ขัดกฎข้อนี้อยู่ (ดู P11)
3. **Single Gateway Read Authority** — มีเฉพาะ `orchestrator.py` (Part 2) ที่อ่าน raw CSV และมีเฉพาะ dispatcher ของ Part 3
   (`ml_dispatcher.py` / `ai_dispatcher.py` / `believe_analyzer.py`) อ่านไฟล์ payload (Rule 8)
4. **Payload Schema + Retention** — เก็บ **30 ไฟล์ล่าสุดต่อคู่เงิน** (Rule 20)
   > ⚠️ ตัวเลข "99 บรรทัด" ใน Rule 20 ล้าสมัยแล้ว — ตอนนี้ 99 (ai/ml) หรือ 114 (strategies) บรรทัด
5. **Fail-Fast / No Fallback** — จุดใดผิดพลาดหรือข้อมูลหาย ต้อง `raise` ทันที ห้ามประมาณค่าหรือใช้ข้อมูลเก่า (Rule 7)
6. **No Silent Failures** — ห้าม `except: print(e)` ต้อง `traceback.print_exc()` / `logging.exception()` และบอกว่าพังตรงไหน (Rule 1)
7. **Background Process Rule** — ทดสอบผ่าน `runner.py` ใน terminal ที่เปิดอยู่เท่านั้น **ห้ามรันค้างเบื้องหลัง** เทสต์เสร็จต้อง kill ทันที (Rule 14)
8. **Strict Explicit Consent** — AI ห้ามแก้โค้ดหรือรันอะไรที่ไม่ได้รับคำสั่งตรง ๆ แม้ระบบจะ auto-approve ก็ตาม (Rule 6)
9. **Single Daily News Calendar** — เก็บ `calendar_YYYY-MM-DD.txt` ไว้ 1 ไฟล์/วัน ลบของเก่าอัตโนมัติ (Rule 22)

---

## 📚 Documentation

| เอกสาร | path จริง | หมายเหตุ |
|:---|:---|:---|
| กฎวินัย AI 27 ข้อ | `agent.md` | ⭐ ต้องอ่านก่อนแก้โค้ด (บางข้อล้าสมัย — ดู P13) |
| Part 1 data_feed | `docs/กระบวนการทำงานของบอท Part1 data_feed/กระบวนการทำงานของบอท Part1 data_feed.md` | |
| Part 2 data_evaluate | `docs/กระบวนการทำงานของบอท Part2 data_evaluate/กระบวนการทำงานของบอท Part2 data_evaluate.md` | ⚠️ เนื้อในซ้ำกับ Part 3/4 |
| Part 3 data_decision | `docs/กระบวนการทำงานของบอท Part3 data_decision/กระบวนการทำงานของบอท ส่วนที่ 3 OUTPUT.md` | ⚠️ ชื่อไฟล์ยังไม่ตรงกับชื่อโฟลเดอร์ |
| Part 4 data_trade | `docs/กระบวนการทำงานของบอท Part4 data_trade/กระบวนการทำงานของบอท Part4 data_trade.md` | ⚠️ เนื้อในซ้ำกับ Part 2/3 |
| E-BOOK กลยุทธ์ V.1 | `docs/strategies/E-BOOK [V.1] ทำกำไร 10 วินาที by nemesis.pdf` | ต้นฉบับกลยุทธ์ Believe |
| E-BOOK กลยุทธ์ V.2 | `docs/strategies/E-BOOK [V.2] ติดปีกทำกำไรด้วยแท่ง10 วิ V.2.pdf` | |
| Gemini prompt | `docs/strategies/คำสั่งพร้อมส์ Ai.txt`, `docs/strategies/Gemini API.txt` | |
| เอกสารสแกนเนอร์ | `symbols_scanner/symbols_scanner_readme.md` | 37 KB |
| ~~Model Critique & Roadmap~~ | — | ❌ **ไม่มีไฟล์นี้อยู่จริง** (readme เดิมลิงก์ไว้) |

---

## 📝 Changelog ของเอกสารนี้

| วันที่ | การเปลี่ยนแปลง |
|:---|:---|
| **22 ก.ย. 2026** | **เขียนใหม่ทั้งหมดให้ตรงกับโค้ดจริง** — แก้ชื่อโมดูล Part 3 (`ai_analysis/` → `data_decision/`), เพิ่ม `strategies_mode` ที่เป็นโหมด active, แก้จำนวนบรรทัด payload (99 → 99/114 ตามโหมด), แก้ "24 Execution Gates / Confidence ≥ 60%" → **15 เกต / 55%**, แก้ "LightGBM + Amazon Chronos + Gemini Flash Lite" → ค่าจริงจาก config, ลบ dependency ที่ไม่ใช้ (`ta-lib`, `google-generativeai`), แก้คำสั่งรัน Phase 0 (`secondary_filter.py` รันไม่ได้), แทน console output ภาษาอังกฤษด้วย log จริงภาษาไทย, เพิ่ม Data Flow / Output Files / settings.json ฉบับเต็ม, เพิ่ม **หมวด P1–P13 (ข้อบกพร่องที่พบ)**, **หมวดประวัติการย้าย path + error เก่าที่แก้แล้ว**, และ **หมวดความปลอดภัย (credential รั่ว)**, ลบลิงก์ `MODEL_CRITIQUE_AND_ROADMAP.md` ที่ไม่มีอยู่จริง, ปรับ directory structure ให้ตรงของจริง |
| ก่อนหน้า | ฉบับเดิม (สำรองไว้ที่ `readme.md.bak-20260922`) |

---

> **⚠️ Disclaimer**
> ระบบนี้จัดทำขึ้นเพื่อวัตถุประสงค์ทางการศึกษาและการวิจัยเชิงปริมาณเท่านั้น
> การเทรดไบนารีออปชันมีความเสี่ยงสูงมากและอาจไม่เหมาะกับนักลงทุนทุกคน
> **สถานะปัจจุบันของโค้ดยังมีข้อบกพร่องระดับ "สตาร์ทไม่ติด" (P1) และระดับ "เกตตัดสินผิดตัว เพราะออกแบบมาเพื่อ M15 ที่โหมด Believe ไม่มีจริง" (P2)**
> ห้ามใช้กับเงินจริงจนกว่าจะแก้และทดสอบในบัญชี DEMO อย่างครอบคลุมแล้ว
> ผลการเทรดในอดีต (WIN 1 รายการ) ไม่ได้การันตีผลลัพธ์ในอนาคต
