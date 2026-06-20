# BOT_ANALYSIS

## SECTION 1 — โครงสร้างไฟล์
### Tree Output
```text
BOT_FINALBOT/
 Active_Pairs_Grabber/
    historical_data/
       history_AUDUSD_M1.csv
       history_AUDUSD_M15.csv
       history_AUDUSD_M5.csv
       history_AUDUSD_M60.csv
       history_EURGBP_M1.csv
       history_EURGBP_M15.csv
       history_EURGBP_M5.csv
       history_EURGBP_M60.csv
       history_EURGBP_OTC_M1.csv
       history_EURGBP_OTC_M15.csv
       history_EURGBP_OTC_M5.csv
       history_EURGBP_OTC_M60.csv
       history_EURJPY_M1.csv
       history_EURJPY_M15.csv
       history_EURJPY_M5.csv
       history_EURJPY_M60.csv
       history_EURJPY_OTC_M1.csv
       history_EURJPY_OTC_M15.csv
       history_EURJPY_OTC_M5.csv
       history_EURJPY_OTC_M60.csv
       history_EURUSD_M1.csv
       history_EURUSD_M15.csv
       history_EURUSD_M5.csv
       history_EURUSD_M60.csv
       history_EURUSD_OTC_M1.csv
       history_EURUSD_OTC_M15.csv
       history_EURUSD_OTC_M5.csv
       history_EURUSD_OTC_M60.csv
       history_GBPUSD_M1.csv
       history_GBPUSD_M15.csv
       history_GBPUSD_M5.csv
       history_GBPUSD_M60.csv
       history_GBPUSD_OTC_M1.csv
       history_GBPUSD_OTC_M15.csv
       history_GBPUSD_OTC_M5.csv
       history_GBPUSD_OTC_M60.csv
       history_USDJPY_M1.csv
       history_USDJPY_M15.csv
       history_USDJPY_M5.csv
       history_USDJPY_M60.csv
       history_USDJPY_OTC_M1.csv
       history_USDJPY_OTC_M15.csv
       history_USDJPY_OTC_M5.csv
       history_USDJPY_OTC_M60.csv
    active_symbols.txt
    grabber.py
    History_IQ.py
 candle_data/
 config/
    settings.json
    settings_backup.json
    symbols.txt
 core/
    ai_analysis/
       __init__.py
       ai_engine.py
       ai_fusion_gate.py
       deepseek_agent_bridge.py
    data/
       __init__.py
       candle_buffer.py
       csv_data_adapter.py
       data_source.py
       data_validator.py
       iq_option_adapter.py
       timeframe_sync.py
    engines/
       __init__.py
       analytical_utils.py
       anomaly_detector.py
       base_engine.py
       behavior_analyzer.py
       candle_pattern_analyzer.py
       confidence_framework.py
       conflict_analyzer.py
       context_synthesizer.py
       continuation_analyzer.py
       divergence_analyzer.py
       efficiency_analyzer.py
       engine_registry.py
       engine_setup.py
       explainability_engine.py
       liquidity_engine.py
       market_pressure_analyzer.py
       market_state_classifier.py
       market_structure_engine.py
       mtf_engine.py
       noise_detector.py
       performance_tracker.py
       persistence_analyzer.py
       price_action_handler.py
       probability_estimator.py
       regime_quality_scorer.py
       signal_quality_scorer.py
       strength_engine.py
       structure_engine.py
       transition_analyzer.py
       trap_detector.py
       trend_engine.py
       volatility_engine.py
    exceptions/
       __init__.py
       context_exceptions.py
       engine_exceptions.py
       validation_exceptions.py
    interfaces/
       __init__.py
       context_interface.py
       engine_interface.py
       strategy_interface.py
    logging/
       trade_logger.py
    ml/
       __init__.py
       signal_optimizer.py
    models/
       __init__.py
       candle.py
       engine_output.py
       market_context.py
       score.py
       signal.py
    orchestration/
       __init__.py
       context_builder.py
       execution_gate.py
       pipeline.py
       signal_throttle.py
    scoring/
       __init__.py
       block_scorer.py
       confidence_scorer.py
       entry_scorer.py
       score_aggregator.py
       score_normalizer.py
    ui_generator/
       __init__.py
    __init__.py
    ai_inventory.py
    all_ai_models.py
    config_loader.py
 docs/
    Dictation_DS/
        BOSS/
           บอส/
              Boss Gemini Antigravity.txt
              Boss Gemini deepseek.txt
              DeepSeek Agent.bat
           Boss Gemini Antigravity.txt
           Boss Gemini deepseek.txt
           DEEPSEEK.txt
           User_To_Deepseek.txt
           เรียก DeepSeek Agent -โฟลเดอร์บอท.bat
           เรียก DeepSeek Agent.bat
        DS_AGENT_PROMPT OVERVIEW.md
 execution/
    __init__.py
    execution_guard.py
    iq_option_executor.py
    order_manager.py
    portfolio_balancer.py
    position_sizer.py
    signal_throttle.py
 memory/
 monitoring/
    __init__.py
    advanced_dashboard.py
    health_monitor.py
    logger.py
    performance_monitor.py
    reporter.py
    signal_notifier.py
 scratch/
    gen_tree.py
    gen_tree_utf8.py
    inspect_data.py
    run_interactive.bat
    run_visible.bat
    test_agent.py
    test_fibonacci.py
    test_file_redirect.py
    workspace_tree.md
 tests/
    BackTest/
 utils/
    __init__.py
    math_utils.py
    order_logger.py
    time_utils.py
    trade_logger.py
    validators.py
 .env
 .env.example
 .gitignore
 analysis.json
 antigravity_cli.py
 dashboard.py
 DS_PROGRESS.md
 FinalBOT.md
 main.py
 Market1.txt
 market_analysis_result.json
 output.json
 requirements.txt
 response.json
 runner.py
 temp_ds_044241.txt
 temp_ds_045612.txt
 temp_ds_055522.txt
 temp_ds_105259.txt
 temp_ds_151648.txt
 temp_ds_162015.txt
 temp_ds_162609.txt
 temp_ds_172231.txt
 temp_ds_174229.txt
 temp_ds_175302.txt
 temp_ds_181710.txt
 temp_ds_220156.txt
 temp_ds_230501.txt
 temp_ds_233825.txt
 temp_out.txt
 trade_analysis.json
 tree_output.txt
 tree_output_cmd.txt
```

### Entry Point
ไฟล์หลักที่เป็น Entry Point คือ **`main.py`** ซึ่งทำการโหลด Symbols แล้วรันบอทจากคลาส `BotRunner` ใน `runner.py`

---

## SECTION 2 — Main Loop & Entry Logic

### Main Loop
คัดลอกส่วนที่เป็น Main Loop (`runner.py`):
```python
    def run_cycle(self):
        # Ensure connection is active before processing (handles WinError 10054 drops)
        try:
            self.data_adapter.ensure_connected()
        except Exception as e:
            logger.error(f"Failed to check/restore connection: {e}")
            return

        # Settle expired trades
        now = datetime.now(timezone.utc)
        for order_id, trade in list(self.order_manager.active_trades.items()):
            elapsed = (now - trade.entry_time).total_seconds()
            
            # Parse dynamic expiry time (e.g., "M3" -> 3 minutes)
            expiry_val = getattr(trade, 'expiry', 'M5')
            try:
                if isinstance(expiry_val, str) and expiry_val.startswith('M'):
                    duration_mins = int(expiry_val[1:])
                else:
                    duration_mins = int(expiry_val)
            except:
                duration_mins = 5
                
            if elapsed >= (duration_mins * 60):
                try:
                    # check_win_v4 gets from socket cache directly, much less likely to block
                    # Returns: (win_status, profit_amount)
                    win_status, profit = self.executor.api.check_win_v4(int(order_id))
                    pnl = float(profit)
                    won = pnl > 0
                    self.order_manager.close_trade(
                        order_id=order_id,
                        exit_price=trade.entry_price,
                        pnl=pnl,
                        notes=f"Settled via IQ Option API (status: {win_status}, pnl: {pnl})",
                        current_time=now
                    )
                    thai_console_log(f"🏆 Trade {order_id} Settled. PnL: {pnl} | Won: {won}")
                except Exception as e:
                    logger.error(f"Failed to settle trade {order_id}: {e}")

        # Process each symbol
        for symbol in self.symbols:
            # Allow multiple active trades (removed double trade check)
            # if self.order_manager.get_active_trades(symbol):
            #     continue
                
            # Fetch 5-minute candles
            candles = self.data_adapter.get_candles(symbol, 'M5', 100)
            if candles.empty or len(candles) < 20:
                continue
                
            # Use only completed candles to prevent repainting
            completed_candles = candles.iloc[:-1]
            last_ts = completed_candles.index[-1]
            
            # Avoid analyzing the same candle twice
            if self.last_processed_candle[symbol] == last_ts:
                continue
```

### Entry Logic
คัดลอกส่วนเงื่อนไข Entry Logic (`runner.py`):
```python
            if insight.action in ["CALL", "PUT"] and insight.confidence >= 70:
                direction = insight.action.lower()
                expiry_seconds = insight.expiry * 60
                thai_console_log(f"🔥 Executing {insight.action} on {symbol} with stake {self.stake} ({insight.expiry}m Expiry)")
                try:
                    # Execute trade using executor's send_order method
                    result = self.executor.send_order(
                        symbol=symbol,
                        direction=insight.action,
                        amount=self.stake,
                        expiry=f"M{insight.expiry}"
                    )
```

### Timing Logic
คัดลอกการเปิดไม้และการวนรอบ (`runner.py`):
```python
    def start(self):
        while True:
            try:
                self.run_cycle()
                time.sleep(5)
            except KeyboardInterrupt:
                thai_console_log("Stopping bot...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(5)
```

---

## SECTION 3 — Indicator & Signal Logic

### Strategy List
ระบุชื่อ Strategy ทั้งหมดที่มีในระบบ (`main.py`):
```python
    strategy_mapping = {
        "rejection_5m_pa": Rejection5mPA,
        "ema_crossover": EMACrossoverStrategy,
        "macd_crossover": MACDCrossoverStrategy,
        "stochastic_crossover": StochasticCrossoverStrategy,
        "rsi_reversal": RSIReversalStrategy,
        "bb_rsi_confluence": BBRSIConfluenceStrategy,
        "pin_bar_scalper": PinBarScalper,
        "engulfing_scalper": EngulfingScalperStrategy,
        "rsi_extreme_bounce": RSIExtremeBounceStrategy,
        "ema_ribbon_momentum": EMARibbonMomentumStrategy,
        "pa_snr": PASNRStrategy,
        "sr_fakeout_rejection": SRFakeoutRejection,
        "triple_confluence": TripleConfluenceStrategy,
        "compression_breakout": CompressionBreakoutStrategy,
        "velocity_layer": VelocityLayerStrategy,
        "fakeout_trap_rider": FakeoutTrapRiderStrategy,
        "zscore_bandit": ZScoreBanditStrategy,
        "range_bounce_arbitrage": RangeBounceArbitrageStrategy,
        "stochastic_sniping": StochasticSnipingStrategy,
    }
```

### Indicator Calculation
คัดลอกส่วนของ Indicator (EMA, Bollinger Bands, RSI, MACD) (`runner.py`):
```python
    def calc_rsi(self, prices, period=14):
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])

    # ... inside run_cycle ...

            # Calculate Indicators
            ema20 = float(close_prices.ewm(span=20, adjust=False).mean().iloc[-1])
            ema50 = float(close_prices.ewm(span=50, adjust=False).mean().iloc[-1])
            
            ma20 = close_prices.rolling(window=20).mean()
            std20 = close_prices.rolling(window=20).std(ddof=0)
            bb_upper = float((ma20 + 2 * std20).iloc[-1])
            bb_lower = float((ma20 - 2 * std20).iloc[-1])
            bb_mid = float(ma20.iloc[-1])
            
            rsi = self.calc_rsi(close_prices, 14)
            
            # MACD
            ema12 = close_prices.ewm(span=12, adjust=False).mean()
            ema26 = close_prices.ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            curr_macd = float(macd_line.iloc[-1])
            curr_macd_sig = float(signal_line.iloc[-1])
```

### Signal Logic (DeepSeek Integration)
คัดลอกส่วนตัดสินใจ (`runner.py`):
```python
            insight = self.ai_bridge.analyze_market(context)
            if not insight:
                continue
                
            self.last_processed_candle[symbol] = last_ts
            
            thai_console_log(f"🧠 DeepSeek Decision: {insight.action} | Confidence: {insight.confidence}% | Expiry Chosen: {insight.expiry}m | Reason: {insight.reason}")
            
            if insight.action in ["CALL", "PUT"] and insight.confidence >= 70:
```

---

## SECTION 4 — IQ Option API Integration

### Connect / Reconnect
โค้ดเชื่อมต่อจากไฟล์ `core/data/iq_option_adapter.py`:
```python
        try:
            from iqoptionapi.stable_api import IQ_Option
        except ImportError as e:
            raise RuntimeError(
                "iqoptionapi library not installed. Run: pip install iqoptionapi"
            ) from e

        logger.info(f"[CONN] Connecting to IQ Option ({account_type}) as {self.email}...")
        self.api = IQ_Option(self.email, self.password)
        ok, reason = self.api.connect()
        if not ok:
            raise RuntimeError(f"IQ Option login failed: {reason}")
```

โค้ด Reconnect จากไฟล์ `core/data/iq_option_adapter.py`:
```python
    def ensure_connected(self) -> None:
        """Reconnect if the websocket dropped (called before each fetch)."""
        if not self.api:
            return
        try:
            if not self.api.check_connect():
                logger.warning("[WARN]  IQ Option connection lost — reconnecting...")
                ok, reason = self.api.connect()
                if ok:
                    try:
                        self.api.change_balance(self.account_type)
                    except Exception:
                        pass
                    logger.info(" Reconnected")
                else:
                    logger.error(f"[ERROR] Reconnect failed: {reason}")
        except Exception as e:
            logger.error(f"[ERROR] ensure_connected error: {e}")
```

### Candle Data Retrieval
โค้ดดึงแท่งเทียนจากไฟล์ `core/data/iq_option_adapter.py`:
```python
        # 2. Fallback to standard REST HTTP request
        def _fetch() -> Optional[pd.DataFrame]:
            with _CANDLES_LOCK:
                try:
                    raw = self.api.get_candles(symbol, size, count, end_timestamp)
                except Exception as e:
                    logger.error(f"[ERROR] get_candles({symbol}/{timeframe}): {e}")
                    return None
            if not raw:
                return None
            df = pd.DataFrame(raw)
            if df.empty:
                return None
            df = df.rename(columns={"max": "high", "min": "low"})
            need = {"from", "open", "close", "high", "low"}
            if not need.issubset(df.columns):
                return None
            df["timestamp"] = pd.to_datetime(df["from"], unit="s")
            for col in ("open", "close", "high", "low"):
                df[col] = pd.to_numeric(df[col], errors="coerce")
```

### Open Order
โค้ดเปิดออเดอร์จากไฟล์ `execution/iq_option_executor.py`:
```python
    def _api_order(self, symbol: str, direction: str,
                   amount: float, expiry: str) -> OrderResult:
        """
        Place a real binary-option order via the IQ Option API.

        Uses the community `iqoptionapi` library. IQ Option has no
        official API — verify method names against the installed
        library version, and ALWAYS test on a DEMO account first.

        Args:
            symbol: e.g. 'EURUSD-OTC'
            direction: 'CALL' (up) or 'PUT' (down)
            amount: stake size
            expiry: 'M1', 'M5', etc.

        Returns:
            OrderResult with the broker's order id and status.
        """
        if not self.api:
            raise RuntimeError("API not initialized")

        # Parse duration dynamically (e.g. 'M3' -> 3, '3' -> 3)
        duration = 5
        if isinstance(expiry, str):
            if expiry.startswith('M'):
                try:
                    duration = int(expiry[1:])
                except:
                    duration = self._EXPIRY_MINUTES.get(expiry, 5)
            else:
                try:
                    duration = int(expiry)
                except:
                    duration = 5
        elif isinstance(expiry, (int, float)):
            duration = int(expiry)
            
        action = direction.lower()  # iqoptionapi expects 'call' / 'put'
        timestamp = datetime.now(timezone.utc).isoformat()

        # iqoptionapi: buy(amount, active, action, duration)
        # returns (success: bool, order_id)
        try:
            success, order_id = self.api.buy(amount, symbol, action, duration)
```

---

## SECTION 5 — Config & Parameters

### Initial Parameters & Configuration
คัดลอกจาก `config/settings.json`:
```json
{
  "_comment": "FINALBOT settings. account_type=PRACTICE uses the IQ Option demo account (fake money). Change to REAL only after demo testing is complete.",
  "account": {
    "account_type": "PRACTICE",
    "trading_mode": "Ai_BOT",
    "iq_email": "venuz20152565@gmail.com",
    "iq_password": "2856101607mM@"
  },
  "symbols": [
    "EURUSD", "EURGBP", "EURJPY", "EURUSD-OTC"
  ],
  "capital": {
    "starting_balance": 2000,
    "stake_per_trade": 35,
    "stake_locked": false
  },
  "limits": {
    "max_concurrent": 9999,
    "max_trades_per_session": 9999,
    "max_daily_profit": 9999,
    "max_daily_loss": 9999,
    "max_consecutive_losses": 9999,
    "cooldown_minutes_after_loss": 0,
    "_note": "Risk management disabled (set to 9999)."
  },
  "execution_gate": {
    "min_confidence": 75,
    "max_block_score": 30,
    "_note": "Strict quality threshold for better signals."
  },
  "session": {
    "trading_hours": "00:00-23:59",
    "timezone": "Asia/Bangkok"
  },
  "active_strategies": [
    "fakeout_trap_rider",
    "velocity_layer",
    "stochastic_sniping",
    "zscore_bandit",
    "range_bounce_arbitrage"
  ],
  "backtest": {
    "start_date": "2026-05-08 00:00:00",
    "end_date": "2026-05-08 23:59:59"
  },
  "ai_mode": {
    "enabled": true,
    "use_cli_agent": true,
    "agent_command": "deepseek-agent",
    "timeout_seconds": 75,
    "fallback_to_traditional": true,
    "weight_in_fusion": 0.4
  }
}
```
