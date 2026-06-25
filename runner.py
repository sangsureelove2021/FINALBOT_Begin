import sys
import logging
import os
import time
from datetime import datetime, timezone, timedelta
import pandas as pd

from monitoring.console_dashboard import ConsoleUI, logger, setup_logging

setup_logging()

# Core imports
from core.data.iq_option_adapter import IQOptionAdapter
from core.data.data_adapter import DataAdapter
from execution.iq_option_executor import IQOptionExecutor
from execution.order_manager import OrderManager
from core.ai_analysis.deepseek_agent_bridge import DeepSeekAgentBridge

from core.orchestration.orchestrator import Orchestrator

class PureAIRunner:
    def __init__(self):
        # Load settings
        from config.config_loader import load_settings
        self.settings = load_settings(reload=False)
        
        account_cfg = self.settings.get("account", {})
        self.account_type = account_cfg.get("account_type", "PRACTICE")
        self.symbols = self.settings.get("symbols", ["EURUSD"])
        self.stake = account_cfg.get("stake_per_trade", 10)
        
        # Initialize adapter and executor
        ConsoleUI.show_connection_attempt()
        self.data_adapter = IQOptionAdapter(account_type=self.account_type)
        if not self.data_adapter.is_connected():
            ConsoleUI.show_connection_failed()
            sys.exit(1)
            
        ConsoleUI.show_connection_success()
            
        self.executor = IQOptionExecutor(adapter=self.data_adapter, account_type=self.account_type)
        self.candle_adapter = DataAdapter(iq_adapter=self.data_adapter, base_dir="data/DATA IQ")
        
        # Display balance
        try:
            balance = self.data_adapter.api.get_balance()
        except Exception as e:
            logger.exception("Failed to get balance")
            balance = 0.0
            
        ConsoleUI.show_account_info(self.account_type, balance)

        # Calculate time offset between local clock and IQ Option server clock
        try:
            server_time = self.data_adapter.api.get_server_time()
            self.time_offset = server_time - time.time()
            ConsoleUI.show_time_offset(self.time_offset)
        except Exception as e:
            self.time_offset = 0.0
            logger.exception("Failed to get server time offset")

        # โหลด trading_mode
        from config.config_loader import get_trading_mode
        self.trading_mode = get_trading_mode()

        # Initialize DeepSeek bridge
        ai_cfg = self.settings.get("ai_mode", {})
        agent_cmd = ai_cfg.get("agent_command", "deepseek-agent")
        timeout_sec = ai_cfg.get("timeout_seconds", 45)
        cache_ttl = ai_cfg.get("cache_ttl_seconds", 5)
        max_failures = ai_cfg.get("max_consecutive_failures", 3)
        self.ai_bridge = DeepSeekAgentBridge(
            agent_command=agent_cmd,
            timeout_seconds=timeout_sec,
            cache_ttl_seconds=cache_ttl,
        )
        self.ai_bridge.max_failures = max_failures

        # โหลด thresholds จาก settings
        thresholds = self.settings.get("thresholds", {})
        self.min_confidence = thresholds.get("min_confidence",
                             self.settings.get("execution_gate", {}).get("min_confidence", 75))
        
        ConsoleUI.show_trading_mode(self.trading_mode)
        if "AI" in self.trading_mode:
            ConsoleUI.show_ai_checking()
            ai_reply = self.ai_bridge.check_readiness()
            if not ai_reply:
                ConsoleUI.show_ai_failed()
                sys.exit(1)
            ConsoleUI.show_ai_reply(ai_reply)
        
        # Pull max_concurrent from settings
        max_conc = self.settings.get("limits", {}).get("max_concurrent", 5)
        self.order_manager = OrderManager(max_concurrent=max_conc)
        self.use_advanced_ai_context = ai_cfg.get("use_advanced_context", True)
        
        from core.orchestration.indicator_store.indicator_store import store
        if "AI" in self.trading_mode:
            self.orchestrator = Orchestrator()
            self.pipeline = None
            self.bot_strategy = None
        else:
            self.orchestrator = Orchestrator() # Keep orchestrator for fallback if needed, or just let store handle calculation
            from main import setup_pipeline
            self.pipeline = setup_pipeline()
            from core.bot_strategy.strategy import BotStrategyProcessor
            self.bot_strategy = BotStrategyProcessor(self.settings)
        
        self.last_processed_candle = {sym: None for sym in self.symbols}

        # Display assets
        ConsoleUI.show_asset_list(self.symbols)
        
        ConsoleUI.show_data_prep_start()
        
        # Warm-up: fetch 200 candles per symbol and write initial CSVs via DataAdapter
        ready_symbols = []
        not_ready_count = 0
        for sym in self.symbols:
            if self.candle_adapter.init_symbol(sym):
                ready_symbols.append(sym)
            else:
                not_ready_count += 1
                logger.warning(f"{sym} data incomplete. Dropped.")
                
        self.symbols = ready_symbols
        ConsoleUI.show_data_prep_result(len(self.symbols), not_ready_count)
        
        # Initialize background AI executor and running flags
        import concurrent.futures
        self.ai_executor = concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(self.symbols)))
        self.ai_running = {sym: False for sym in self.symbols}
        
        # Subscribe to WebSocket streams for live data
        for sym in self.symbols:
            self.data_adapter.start_stream(sym, 'M1', 200)
            self.data_adapter.start_stream(sym, 'M5', 200)
        
        profit_pct = account_cfg.get("take_profit_percent", 2.0)
        loss_pct = account_cfg.get("stop_loss_percent", 3.5)
        trade_hours = self.settings.get("session", {}).get("trading_hours", "11.00-23.00")
        
        ConsoleUI.show_mode_summary(self.stake, profit_pct, loss_pct, max_conc, trade_hours)
        self._countdown_to_first_candle()


    def _countdown_to_first_candle(self):
        """แสดงเวลาที่จะเริ่มวิเคราะห์ครั้งแรก (แสดงข้อมูลเท่านั้น ไม่ sleep)"""
        now = datetime.now()
        if now.second < 2:
            remaining = 2 - now.second
        else:
            remaining = 60 - now.second + 2

        tz_thailand = timezone(timedelta(hours=7))
        target = datetime.now(tz_thailand) + timedelta(seconds=remaining)
        target_str = target.strftime('%H:%M:%S')
        ConsoleUI.show_countdown(remaining, target_str)

    def fetch_and_save_data(self, symbol):
        """Delegate all candle management to DataAdapter."""
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        broker_epoch = time.time() + self.time_offset
        return self.candle_adapter.update(symbol, broker_epoch=broker_epoch)

    def run_ai_analysis_and_trade(self, symbol, candles_dict, current_price):
        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        if not isinstance(candles_dict, dict):
            raise TypeError("candles_dict must be a dictionary")
        if not isinstance(current_price, (int, float)):
            raise TypeError("current_price must be a float or int")
        try:
            # --- 1. Orchestrator Data Pipeline ---
            log_data = None
            try:
                log_data = self.orchestrator.process_cycle(
                    symbol=symbol,
                    candles_dict=candles_dict,
                    ai_context=None
                )
            except Exception as e:
                logger.exception(f"Orchestrator cycle failed for {symbol}")

            # ถ้า Orchestrator crash หรือคืน None — ให้หยุดทำรายการ (ไม่ดึงจากที่อื่นแล้ว)
            if not log_data:
                logger.warning(f"Orchestrator returned no data for {symbol} — skipping AI call")
                return

            # สร้าง advanced context จาก log_data เพื่อส่งให้ AI และ Bot
            ai_context_to_send = dict(log_data)
            ai_context_to_send["is_advanced"] = True
            ai_context_to_send["current_price"] = current_price

            # Data structure for unified signal handling
            from collections import namedtuple
            Insight = namedtuple('Insight', ['action', 'confidence', 'expiry'])
            insight = None

            if "AI" in self.trading_mode:
                ai_insight = self.ai_bridge.analyze_market(ai_context_to_send)
                if ai_insight:
                    self.orchestrator.update_ai_memory(symbol, ai_insight.action, ai_insight.reason)
                    insight = Insight(action=ai_insight.action, confidence=ai_insight.confidence, expiry=ai_insight.expiry)
                    ConsoleUI.show_insight("AI", insight.action, insight.confidence)
                    
                    # Update the JSON with AI results
                    if log_data and 'decision_layer' in log_data:
                        log_data['decision_layer']['final_reason_th'] = ai_insight.reason
                        log_data['decision_layer']['suggested_action'] = ai_insight.action
                        log_data['decision_layer']['suggested_expiry_minutes'] = ai_insight.expiry
                        log_data['decision_layer']['confidence_score'] = ai_insight.confidence
                        try:
                            self.orchestrator._save_formatted_json(symbol, log_data)
                        except Exception as e:
                            logger.exception(f"Failed to update JSON with AI reason for {symbol}")
            else:
                if self.bot_strategy:
                    # Use standard BotStrategyProcessor with orchestrator payload
                    res = self.bot_strategy.analyze_market(ai_context_to_send)
                    insight = Insight(action=res.get('action', 'WAIT'), confidence=res.get('confidence', 0), expiry=res.get('expiry', 5))
                    ConsoleUI.show_insight("BOT Strategy", insight.action, insight.confidence)
                elif self.pipeline:
                    # pipeline using orchestrator payload
                    bot_signal = self.pipeline.execute(symbol, ai_context_to_send, 'M5')
                    if bot_signal:
                        insight = Insight(action=bot_signal.action, confidence=bot_signal.confidence, expiry=5)
                        ConsoleUI.show_insight("BOT Pipeline", insight.action, insight.confidence)

            if not insight:
                return
            
            if insight.action in ["CALL", "PUT"] and insight.confidence >= self.min_confidence:
                direction = insight.action.upper()
                expiry_time = insight.expiry
                
                if "AUTO" in self.trading_mode:
                    ConsoleUI.show_order_execution(insight.action, symbol, expiry_time)
                    try:
                        # Execute trade using executor's send_order method
                        result = self.executor.send_order(
                            symbol=symbol,
                            direction=direction,
                            amount=self.stake,
                            expiry=f"M{expiry_time}"
                        )
                        if result.status == 'executed':
                            order_id = result.order_id
                            # Record trade in order manager
                            self.order_manager.add_trade(
                                order_id=str(order_id),
                                symbol=symbol,
                                direction=insight.action,
                                amount=self.stake,
                                entry_price=current_price,
                                expiry=f"M{insight.expiry}"
                            )
                            ConsoleUI.show_order_success(order_id)
                        else:
                            ConsoleUI.show_order_failed(symbol, result.reason)
                    except Exception as e:
                        logger.exception("Execution exception")
                else:
                    # SIGNAL Mode - do not execute
                    ConsoleUI.show_signal_only(insight.action, symbol, expiry_time, self.trading_mode)
        except Exception as ex:
            logger.exception(f"Background AI task failed for {symbol}")
        finally:
            self.ai_running[symbol] = False


    def run_cycle(self):
        # Ensure connection is active before processing (handles WinError 10054 drops)
        try:
            self.data_adapter.ensure_connected()
        except Exception as e:
            logger.exception("Failed to check/restore connection")
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
            except Exception as e:
                logger.exception("Failed to parse expiry")
                duration_mins = 5
                
            if elapsed >= (duration_mins * 60):
                try:
                    # check_win_v3 gets from socket cache directly, much less likely to block
                    # Returns: profit_amount
                    profit = self.executor.api.check_win_v3(int(order_id))
                    if profit is None:
                        continue
                    pnl = float(profit)
                    won = pnl > 0
                    win_status = "win" if won else "loss" if pnl < 0 else "tie"
                    # ดึงราคาปัจจุบัน ณ เวลาที่หมดเวลาเพื่อเป็น Exit Price โดยประมาณ
                    exit_price = trade.entry_price
                    try:
                        m1_store = self.candle_adapter._store_m1.get(trade.symbol)
                        if m1_store is not None and not m1_store.empty:
                            if 'close' in m1_store.columns and len(m1_store) > 0:
                                exit_price = float(m1_store['close'].iloc[-1])
                    except Exception as e:
                        logger.exception(f"Failed to get exit price from M1 store for {trade.symbol}")
                        
                    self.order_manager.close_trade(
                        order_id=order_id,
                        exit_price=exit_price,
                        pnl=pnl,
                        notes=f"Settled via IQ Option API (status: {win_status}, pnl: {pnl})",
                        current_time=now
                    )
                    ConsoleUI.show_trade_result(won, trade.symbol, order_id, pnl)
                except Exception as e:
                    logger.exception(f"Failed to settle trade {order_id}")

        try:
            balance = self.data_adapter.api.get_balance()
        except Exception as e:
            logger.exception("Failed to get balance in run_cycle")
            balance = None

        # Run all symbols concurrently for data fetching and CSV writing
        if not self.symbols:
            logger.warning("[WARN] ไม่มีคู่เงินใดๆ ที่พร้อมทำงานในรอบนี้")
            return
            
        import concurrent.futures
        
        # Step 1: Fetch and save data concurrently (highly optimized, no AI blocking)
        sym_futures = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.symbols)) as executor:
            for sym in self.symbols:
                sym_futures[sym] = executor.submit(self.fetch_and_save_data, sym)
            concurrent.futures.wait(sym_futures.values())

        # Step 2: Spawn background AI analysis tasks
        prices_dict = {}
        for sym in self.symbols:
            try:
                result_val = sym_futures[sym].result()
            except Exception as e:
                logger.exception(f"Error getting future result for {sym}")
                continue

            if not result_val:
                continue

            # DataAdapter.update returns (symbol, m1, m5, m15, price)
            completed_m1, completed_m5, completed_m15, current_price = result_val[1:]
            prices_dict[sym] = current_price
            
            if completed_m1 is None or completed_m1.empty:
                logger.warning(f"completed_m1 is empty for {sym} - skipping AI cycle")
                continue
                
            last_ts_m1 = completed_m1.index[-1]
            
            # กันวิเคราะห์แท่งเดิมซ้ำ
            if self.last_processed_candle[sym] == last_ts_m1:
                continue
                
            # ตรวจสอบการรันซ้ำของ AI
            if self.ai_running.get(sym, False):
                logger.warning(f"[WARN] AI สำหรับ {sym} กำลังทำงานค้างอยู่จากนาทีที่แล้ว — ข้ามการเรียก AI รอบนี้เพื่อป้องกันโหลดทับซ้อน")
                continue
                
            self.last_processed_candle[sym] = last_ts_m1
            self.ai_running[sym] = True
            
            candles_dict = {
                'M1': completed_m1.copy(),
                'M5': completed_m5.copy(),
                'M15': completed_m15.copy()
            }
            self.ai_executor.submit(self.run_ai_analysis_and_trade, sym, candles_dict, current_price)

        # แสดงสรุปราคาและยอดเงินบรรทัดเดียว
        if prices_dict:
            ConsoleUI.show_prices_and_balance(prices_dict, balance)


    def start(self):
        import time
        from datetime import datetime
        while True:
            try:
                now = datetime.now()
                # Calculate seconds until the next minute's 2nd second.
                # If current second is >= 2, we wait until next minute's 2nd second.
                if now.second < 2:
                    sleep_sec = 2 - now.second
                else:
                    sleep_sec = 60 - now.second + 2
                
                time.sleep(sleep_sec)
                self.run_cycle()

            except KeyboardInterrupt:
                ConsoleUI.show_stopping()
                break
            except Exception as e:
                logger.exception("Error in main loop")
                time.sleep(5)

if __name__ == "__main__":
    runner = PureAIRunner()
    runner.start()
