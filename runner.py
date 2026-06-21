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
os.makedirs("logs", exist_ok=True)
log_file_name = f"logs/system_logs/bot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler(log_file_name, encoding='utf-8')
    ]
)
logger = logging.getLogger("FINALBOT")

def thai_console_log(msg: str):
    tz_thailand = timezone(timedelta(hours=7))
    thai_time_str = datetime.now(tz_thailand).strftime('%H:%M:%S')
    print(f"{thai_time_str} - {msg}")
    sys.stdout.flush()

# Core imports
from core.data.iq_option_adapter import IQOptionAdapter
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
        
        # Display balance
        try:
            balance = self.data_adapter.api.get_balance()
        except:
            balance = 0.0
            
        thai_console_log(f"บัญชี {self.account_type} | Balance: ${balance:.2f}")

        # Initialize DeepSeek bridge
        ai_cfg = self.settings.get("ai_mode", {})
        agent_cmd = ai_cfg.get("agent_command", "deepseek-agent")
        timeout_sec = ai_cfg.get("timeout_seconds", 45)
        self.ai_bridge = DeepSeekAgentBridge(agent_command=agent_cmd, timeout_seconds=timeout_sec)
        
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
        
        # Check readiness
        import os
        import pandas as pd
        
        ready_symbols = []
        not_ready_count = 0
        for sym in self.symbols:
            try:
                # Need M1, M5, M15
                m1 = self.data_adapter.get_candles(sym, 'M1', 200)
                m5 = self.data_adapter.get_candles(sym, 'M5', 200)
                m15 = self.data_adapter.get_candles(sym, 'M15', 200)
                
                if (m1 is not None and len(m1) >= 200) and \
                   (m5 is not None and not m5.empty) and \
                   (m15 is not None and not m15.empty):
                   
                    # Write to CSV
                    save_dir = os.path.join("data", "csv", sym.replace("-OTC", "_OTC"))
                    os.makedirs(save_dir, exist_ok=True)
                    m1.to_csv(os.path.join(save_dir, "M1.csv"))
                    m5.to_csv(os.path.join(save_dir, "M5.csv"))
                    m15.to_csv(os.path.join(save_dir, "M15.csv"))
                    
                    ready_symbols.append(sym)
                else:
                    not_ready_count += 1
                    logger.warning(f"{sym} data incomplete. Dropped.")
            except Exception as e:
                not_ready_count += 1
                logger.warning(f"Failed to fetch {sym}: {e}")
                
        self.symbols = ready_symbols
        ready_count = len(self.symbols)
        thai_console_log(f"ข้อมูลพร้อมเทรด {ready_count} รายการ  ไม่พร้อมเทรด {not_ready_count} รายการ")
        
        profit_pct = account_cfg.get("take_profit_percent", 2.0)
        loss_pct = account_cfg.get("stop_loss_percent", 3.5)
        trade_hours = self.settings.get("session", {}).get("trading_hours", "11.00-23.00")
        
        mode_str = f"[MODE : AI_BOT][Stake:{self.stake}][Profit:{profit_pct}%][Loss:{loss_pct}%][Orderlimit:{max_conc}][Time:{trade_hours}]"
        thai_console_log(mode_str)
        thai_console_log("รอให้จบแท่งเทียน 1 m เพื่อเข้าสู่การวิเคราะห์สัญญาณ (เริ่มต้นที่วินาทีที่ 3)...")


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
                    self.order_manager.close_trade(
                        order_id=order_id,
                        exit_price=trade.entry_price,
                        pnl=pnl,
                        notes=f"Settled via IQ Option API (status: {win_status}, pnl: {pnl})",
                        current_time=now
                    )
                    thai_console_log(f"{'ชนะ' if won else 'แพ้'} {trade.symbol} (ID: {order_id}) | PnL: {pnl:.2f}")
                except Exception as e:
                    logger.error(f"Failed to settle trade {order_id}: {e}")

        try:
            balance = self.data_adapter.api.get_balance()
            if balance is not None:
                balance_str = f" | Balance: {balance:.2f}"
            else:
                balance_str = ""
        except Exception:
            balance_str = ""

        # Process symbols concurrently to prevent AI analysis from blocking the 1-minute loop
        import concurrent.futures
        
        def process_symbol(symbol):
            log_data = None
            try:
                # Fetch M1 candles first for exact 1-minute timestamp tracking
                candles_m1 = self.data_adapter.get_candles(symbol, 'M1', 200)
                if candles_m1 is None or candles_m1.empty or len(candles_m1) < 2:
                    return
                
                # Use only completed candles
                completed_candles_m1 = candles_m1.iloc[:-1]
                last_ts_m1 = completed_candles_m1.index[-1]
                
                # Avoid analyzing the same M1 candle twice (ensures exactly 1 run per minute)
                if self.last_processed_candle[symbol] == last_ts_m1:
                    return
                
                # Always mark as processed immediately so we don't retry failed candles within the same minute
                self.last_processed_candle[symbol] = last_ts_m1

                # Fetch 5-minute candles
                candles = self.data_adapter.get_candles(symbol, 'M5', 200)
                if candles is None or candles.empty or len(candles) < 21:
                    return
                    
                completed_candles = candles.iloc[:-1]
                
                # Resample M15 from M5 to save API calls
                candles_m15 = candles.resample('15min').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
                
                candles_dict = {'M5': completed_candles, 'M1': completed_candles_m1, 'M15': candles_m15.iloc[:-1] if not candles_m15.empty else pd.DataFrame()}
                
                # Export to CSV organized by currency pair
                import os
                save_dir = os.path.join("data", "csv", symbol.replace("-OTC", "_OTC"))
                os.makedirs(save_dir, exist_ok=True)
                candles_m1.to_csv(os.path.join(save_dir, "M1.csv"))
                candles.to_csv(os.path.join(save_dir, "M5.csv"))
                candles_m15.to_csv(os.path.join(save_dir, "M15.csv"))
                
                # --- 1. Orchestrator Data Pipeline ---
                try:
                    log_data = self.orchestrator.process_cycle(
                        symbol=symbol,
                        candles_dict=candles_dict,
                        ai_context=None
                    )
                    if log_data:
                        log_path = self.trade_logger.save_log(log_data)
                        
                    # Extract current price and rsi for console log
                    from core.indicator_store import store
                    payload = store.get_payload(symbol)
                    m5_inds = payload.get('m5', {})
                    current_price = m5_inds.get('close', float(completed_candles['close'].iloc[-1]))
                    rsi = m5_inds.get('rsi14', 50.0)
                    
                except Exception as e:
                    logger.error(f"Orchestrator cycle failed for {symbol}: {e}")
                    current_price = float(completed_candles['close'].iloc[-1])
                    rsi = 50.0
                
                thai_console_log(f"[{symbol}; {current_price:.5f}]{balance_str}")
                
                # Call DeepSeek Brain
                ai_context_to_send = None
                if getattr(self, "use_advanced_ai_context", True) and 'log_data' in locals() and log_data:
                    log_data_copy = dict(log_data)
                    log_data_copy["is_advanced"] = True
                    ai_context_to_send = log_data_copy
                    
                insight = self.ai_bridge.analyze_market(ai_context_to_send)
                if not insight:
                    return
                
                thai_console_log(f"AI: {insight.action} ({insight.confidence}%)")
                
                if insight.action in ["CALL", "PUT"] and insight.confidence >= 70:
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
                logger.error(f"Symbol {symbol} processing failed: {ex}")

        # Run all symbols concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.symbols)) as executor:
            futures = [executor.submit(process_symbol, sym) for sym in self.symbols]
            concurrent.futures.wait(futures)

    def start(self):
        import time
        from datetime import datetime
        while True:
            try:
                now = datetime.now()
                # Calculate seconds until the next minute's 3rd second.
                # If current second is >= 3, we wait until next minute's 3rd second.
                if now.second < 3:
                    sleep_sec = 3 - now.second
                else:
                    sleep_sec = 60 - now.second + 3
                
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
