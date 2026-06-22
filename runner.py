import sys
import logging
import os
import json
import time
from datetime import datetime, timezone, timedelta
import pandas as pd

# Safe stream wrapper for Windows console to prevent encoding errors
class SafeStreamWrapper:
    def __init__(self, original_stream):
        self.original_stream = original_stream
    def write(self, data):
        try:
            self.original_stream.write(data)
        except Exception:
            try:
                self.original_stream.write(data.encode('ascii', errors='backslashreplace').decode('ascii'))
            except Exception:
                pass
    def flush(self):
        if hasattr(self.original_stream, 'flush'):
            self.original_stream.flush()
    def __getattr__(self, attr):
        return getattr(self.original_stream, attr)

sys.stdout = SafeStreamWrapper(sys.stdout)
sys.stderr = SafeStreamWrapper(sys.stderr)

# Configure logging
os.makedirs("logs/system_logs", exist_ok=True)
log_file_name = f"logs/system_logs/bot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler(log_file_name, encoding='utf-8')
    ]
)
logger = logging.getLogger("FINALBOT")

import threading
_PRINT_LOCK = threading.Lock()

def thai_console_log(msg: str):
    tz_thailand = timezone(timedelta(hours=7))
    thai_time_str = datetime.now(tz_thailand).strftime('%H:%M:%S')
    with _PRINT_LOCK:
        print(f"{thai_time_str} - {msg}")
        sys.stdout.flush()

# Core imports
from core.data.iq_option_adapter import IQOptionAdapter
from core.data.data_adapter import DataAdapter
from execution.iq_option_executor import IQOptionExecutor
from execution.order_manager import OrderManager
from core.ai_analysis.deepseek_agent_bridge import DeepSeekAgentBridge
from core.logging.trade_logger import TradeLogger
from core.orchestrator import Orchestrator

class PureAIRunner:
    def __init__(self):
        # Load settings
        from core.config_loader import load_settings
        self.settings = load_settings(reload=False)
        
        account_cfg = self.settings.get("account", {})
        self.account_type = account_cfg.get("account_type", "PRACTICE")
        self.symbols = self.settings.get("symbols", ["EURUSD"])
        self.stake = account_cfg.get("stake_per_trade", 10)
        
        # Initialize adapter and executor
        thai_console_log("กำลังเชื่อมต่อ IQ Option...")
        self.data_adapter = IQOptionAdapter(account_type=self.account_type)
        if not self.data_adapter.is_connected():
            thai_console_log("เชื่อมต่อ IQ Option ล้มเหลว")
            sys.exit(1)
            
        thai_console_log("เชื่อมต่อ IQ Option สำเร็จ..")
            
        self.executor = IQOptionExecutor(adapter=self.data_adapter, account_type=self.account_type)
        self.candle_adapter = DataAdapter(iq_adapter=self.data_adapter, base_dir="data/DATA IQ")
        
        # Display balance
        try:
            balance = self.data_adapter.api.get_balance()
        except:
            balance = 0.0
            
        thai_console_log(f"บัญชี {self.account_type} | Balance: ${balance:.2f}")

        # Calculate time offset between local clock and IQ Option server clock
        try:
            server_time = self.data_adapter.api.get_server_time()
            self.time_offset = server_time - time.time()
            thai_console_log(f"เวลาเซิร์ฟเวอร์โบรกเกอร์ต่างจากเครื่อง: {self.time_offset:.2f} วินาที")
        except Exception as e:
            self.time_offset = 0.0
            logger.warning(f"Failed to get server time offset: {e}")

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
        
        thai_console_log("ตรวจเช็คความพร้อม DEEPSEEK AI")
        ai_reply = self.ai_bridge.check_readiness()
        if not ai_reply:
            thai_console_log("Failed to connect to AI. System stopped.")
            sys.exit(1)
        thai_console_log(f'"{ai_reply}"')
        
        # Pull max_concurrent from settings
        max_conc = self.settings.get("limits", {}).get("max_concurrent", 5)
        self.order_manager = OrderManager(max_concurrent=max_conc)
        self.use_advanced_ai_context = ai_cfg.get("use_advanced_context", True)
        self.trade_logger = TradeLogger()
        self.orchestrator = Orchestrator(trade_logger=self.trade_logger)
        
        self.last_processed_candle = {sym: None for sym in self.symbols}

        # Display assets
        sym_len = len(self.symbols)
        sym_list = ", ".join(self.symbols)
        thai_console_log(f"รายการสินทรัพย์เพื่อเทรด {sym_len} รายการ : {sym_list}")
        
        thai_console_log("กำลังเตรียมข้อมูลสินทรัพย์")
        
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
        ready_count = len(self.symbols)
        thai_console_log(f"ข้อมูลพร้อมเทรด {ready_count} รายการ  ไม่พร้อมเทรด {not_ready_count} รายการ")
        
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
        
        mode_str = f"[MODE : AI_BOT][Stake:{self.stake}][Profit:{profit_pct}%][Loss:{loss_pct}%][Orderlimit:{max_conc}][Time:{trade_hours}]"
        thai_console_log(mode_str)
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
        thai_console_log(f"เข้าสู่การวิเคราะห์สัญญาณในอีก {remaining} วินาที  (เริ่ม {target_str})")

    def fetch_and_save_data(self, symbol):
        """Delegate all candle management to DataAdapter."""
        broker_epoch = time.time() + self.time_offset
        return self.candle_adapter.update(symbol, broker_epoch=broker_epoch)

    def run_ai_analysis_and_trade(self, symbol, candles_dict, current_price):
        try:
            completed_m1 = candles_dict['M1']
            completed_m5 = candles_dict['M5']
            completed_m15 = candles_dict['M15']

            # --- 0. IndicatorStore warm-up ก่อนเสมอ (ป้องกัน indicators เป็น 0) ---
            from core.indicator_store import store
            try:
                store.calculate_all(symbol, candles_dict)
            except Exception as e:
                logger.error(f"IndicatorStore.calculate_all failed for {symbol}: {e}")

            # --- 1. Orchestrator Data Pipeline ---
            log_data = None
            try:
                log_data = self.orchestrator.process_cycle(
                    symbol=symbol,
                    candles_dict=candles_dict,
                    ai_context=None
                )
                if log_data:
                    self.trade_logger.save_log(log_data)
            except Exception as e:
                logger.error(f"Orchestrator cycle failed for {symbol}: {e}")

            # ถ้า Orchestrator crash หรือคืน None — สร้าง context จาก IndicatorStore โดยตรง
            if not log_data:
                logger.warning(f"Orchestrator returned no data for {symbol} — building fallback context")
                payload = store.get_payload(symbol)
                m5 = payload.get('m5', {})
                log_data = {
                    "symbol":        symbol,
                    "current_price": current_price,
                    "m5":            m5,
                    "m1":            payload.get('m1', {}),
                    "m15":           payload.get('m15', {}),
                    "price_action":  payload.get('price_action', {}),
                    "market_state":  payload.get('market_state', 'UNCLEAR'),
                    "analysis": {
                        "trend_direction": "NONE",
                        "trend_strength":  0,
                        "trend_type":      "CHOPPY",
                        "volatility_regime": "NORMAL",
                    },
                    "_fallback": True,
                }

            # ตรวจสอบว่า indicators มีค่าจริงหรือเป็น 0 ทั้งหมด
            m5_inds = log_data.get('m5', {})
            rsi = m5_inds.get('rsi14', 0.0)
            has_real_data = rsi != 0.0 and m5_inds.get('ema5', 0.0) != 0.0
            if not has_real_data:
                logger.warning(f"Indicators for {symbol} are all zero — IndicatorStore may not have warmed up yet, skipping AI call")
                return
                
            insight = self.ai_bridge.analyze_market(ai_context_to_send)
            if not insight:
                return
            
            thai_console_log(f"AI: {insight.action} ({insight.confidence}%)")
            
            if insight.action in ["CALL", "PUT"] and insight.confidence >= self.min_confidence:
                direction = insight.action.upper()
                expiry_time = insight.expiry
                thai_console_log(f"ยิงออเดอร์ {insight.action} {symbol} ({expiry_time} นาที)")
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
                        thai_console_log(f"   └─ ออเดอร์เข้าสำเร็จ (ID: {order_id})")
                    else:
                        thai_console_log(f"Execution failed for {symbol}: {result.reason}")
                except Exception as e:
                    logger.error(f"Execution exception: {e}")
        except Exception as ex:
            logger.error(f"Background AI task failed for {symbol}: {ex}")
        finally:
            self.ai_running[symbol] = False


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
                            exit_price = float(m1_store['close'].iloc[-1])
                    except Exception:
                        pass
                        
                    self.order_manager.close_trade(
                        order_id=order_id,
                        exit_price=exit_price,
                        pnl=pnl,
                        notes=f"Settled via IQ Option API (status: {win_status}, pnl: {pnl})",
                        current_time=now
                    )
                    thai_console_log(f"{'ชนะ' if won else 'แพ้'} {trade.symbol} (ID: {order_id}) | PnL: {pnl:.2f}")
                except Exception as e:
                    logger.error(f"Failed to settle trade {order_id}: {e}")

        try:
            balance = self.data_adapter.api.get_balance()
        except Exception:
            balance = None

        # Run all symbols concurrently for data fetching and CSV writing
        if not self.symbols:
            logger.warning("[WARN] ไม่มีคู่เงินใดๆ ที่พร้อมทำงานในรอบนี้")
            return
            
        import concurrent.futures
        
        # Step 1: Fetch and save data concurrently (highly optimized, no AI blocking)
        futures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.symbols)) as executor:
            for sym in self.symbols:
                futures.append(executor.submit(self.fetch_and_save_data, sym))
            concurrent.futures.wait(futures)

        # Step 2: Spawn background AI analysis tasks
        price_parts = []
        for sym in self.symbols:
            res = None
            for f in futures:
                try:
                    result_val = f.result()
                    # DataAdapter.update returns (symbol, m1, m5, m15, price)
                    if result_val and result_val[0] == sym:
                        res = result_val[1:]   # (m1, m5, m15, price)
                        break
                except Exception as e:
                    logger.error(f"Error getting future result for {sym}: {e}")
            
            if res is None:
                continue
                
            completed_m1, completed_m5, completed_m15, current_price = res
            price_parts.append(f"{sym}:{current_price:.5f}")
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
        if price_parts:
            price_str = "][".join(price_parts)
            balance_str = f"${balance:.2f}" if balance is not None else "N/A"
            thai_console_log(f"[{price_str}] :: TOTAL={balance_str}")


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
                thai_console_log("Stopping bot...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    runner = PureAIRunner()
    runner.start()
