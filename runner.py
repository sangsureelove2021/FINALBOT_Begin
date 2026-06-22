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
        
        # Candle data stores (DataFrame) — initialized on first fetch with 200 candles
        self.store_m1 = {sym: None for sym in self.symbols}
        self.store_m5 = {sym: None for sym in self.symbols}
        self.store_m15 = {sym: None for sym in self.symbols}
        
        # Track which time block was last fetched to avoid redundant API calls
        self.last_block_m5 = {sym: -1 for sym in self.symbols}
        self.last_block_m15 = {sym: -1 for sym in self.symbols}
        self._m5_csv_written = {sym: -1 for sym in self.symbols}
        
        # Display assets
        sym_len = len(self.symbols)
        sym_list = ", ".join(self.symbols)
        thai_console_log(f"รายการสินทรัพย์เพื่อเทรด {sym_len} รายการ : {sym_list}")
        
        thai_console_log("กำลังเตรียมข้อมูลสินทรัพย์")
        
        # Check readiness
        import os
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
                    
                    # เก็บข้อมูลลง store และตั้งค่า block สำหรับรันรอบต่อไป
                    self.store_m1[sym] = m1
                    self.store_m5[sym] = m5
                    self.store_m15[sym] = m15
                    
                    current_min = datetime.now(timezone.utc).minute
                    self.last_block_m5[sym] = current_min // 5
                    self.last_block_m15[sym] = current_min // 15
                    self._m5_csv_written[sym] = current_min // 5
                    
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
        thai_console_log("รอให้จบแท่งเทียน 1 m เพื่อเข้าสู่การวิเคราะห์สัญญาณ (เริ่มต้นที่วินาทีที่ 2)...")


    def fetch_and_save_data(self, symbol):
        try:
            # ใช้เวลาที่ซิงโครไนซ์กับโบรกเกอร์เพื่อหลีกเลี่ยง Clock Drift
            broker_now_epoch = time.time() + self.time_offset
            now_naive = datetime.fromtimestamp(broker_now_epoch, timezone.utc).replace(tzinfo=None)
            current_min = now_naive.minute
            
            # ============================================================
            # STEP 1: M1 — ดึงทุก 1 นาที
            # ============================================================
            if self.store_m1[symbol] is None:
                # ครั้งแรก: ดึง 200 แท่ง
                candles_m1 = self.data_adapter.get_candles(symbol, 'M1', 200)
                if candles_m1 is None or candles_m1.empty or len(candles_m1) < 2:
                    return None
                self.store_m1[symbol] = candles_m1
            else:
                # ครั้งต่อไป: ดึง 5 แท่ง (1 ใหม่ + 4 ย้อนหลังเช็คความถูกต้อง)
                fresh_m1 = self.data_adapter.get_candles(symbol, 'M1', 5)
                if fresh_m1 is not None and not fresh_m1.empty:
                    # ตรวจจับ Data Gap: ถ้าแท่งสุดท้ายใน store ห่างจากแท่งแรกที่ดึงมาเกิน 5 นาที = เน็ตหลุด
                    last_stored_ts = self.store_m1[symbol].index[-1]
                    first_fresh_ts = fresh_m1.index[0]
                    gap_seconds = (first_fresh_ts - last_stored_ts).total_seconds()
                    if gap_seconds > 300:  # ห่างเกิน 5 นาที = มี gap
                        logger.warning(f"[GAP] M1 {symbol}: detected {gap_seconds:.0f}s gap — refetching 200 candles")
                        full_m1 = self.data_adapter.get_candles(symbol, 'M1', 200)
                        if full_m1 is not None and not full_m1.empty:
                            self.store_m1[symbol] = full_m1
                    else:
                        # เช็คความถูกต้อง: เฉพาะแท่งที่ปิดสมบูรณ์แล้ว (ไม่รวม forming candle)
                        overlap = self.store_m1[symbol].index.intersection(fresh_m1.index)
                        if len(overlap) > 0:
                            # ตัดแท่งสุดท้ายออก (forming candle) ก่อนเทียบ
                            check_idx = overlap[:-1] if len(overlap) > 1 else overlap
                            if len(check_idx) > 0:
                                old_vals = self.store_m1[symbol].loc[check_idx[-4:]]
                                new_vals = fresh_m1.loc[check_idx[-4:]]
                                mismatch = (old_vals['close'] != new_vals['close']).any()
                                if mismatch:
                                    logger.warning(f"[VERIFY] M1 {symbol}: mismatch in completed candles — corrected")
                        # รวมข้อมูลใหม่เข้า store
                        combined = pd.concat([self.store_m1[symbol], fresh_m1])
                        combined = combined[~combined.index.duplicated(keep='last')].sort_index()
                        self.store_m1[symbol] = combined.tail(200)
            
            candles_m1 = self.store_m1[symbol]
            
            # ตัดแท่งที่กำลังวิ่ง (Forming Candle)
            if (now_naive - candles_m1.index[-1]).total_seconds() < 60:
                completed_m1 = candles_m1.iloc[:-1]
            else:
                completed_m1 = candles_m1
            
            if completed_m1.empty:
                return None
            
            # เขียน M1 CSV ทุก 1 นาที
            save_dir = os.path.join("data", "csv", symbol.replace("-OTC", "_OTC"))
            os.makedirs(save_dir, exist_ok=True)
            completed_m1.to_csv(os.path.join(save_dir, "M1.csv"))
            
            # ============================================================
            # STEP 2: M5 — ดึงทุก 5 นาที
            # ============================================================
            block_5m = current_min // 5
            
            if self.store_m5[symbol] is None:
                # ครั้งแรก: ดึง 200 แท่ง
                candles_m5 = self.data_adapter.get_candles(symbol, 'M5', 200)
                if candles_m5 is None or candles_m5.empty or len(candles_m5) < 21:
                    return None
                self.store_m5[symbol] = candles_m5
                self.last_block_m5[symbol] = block_5m
            elif block_5m != self.last_block_m5[symbol]:
                # ทุก 5 นาที: ดึง 5 แท่ง (1 ใหม่ + 4 ย้อนหลังเช็คความถูกต้อง)
                fresh_m5 = self.data_adapter.get_candles(symbol, 'M5', 5)
                if fresh_m5 is not None and not fresh_m5.empty:
                    # ตรวจจับ Data Gap
                    last_stored_ts = self.store_m5[symbol].index[-1]
                    first_fresh_ts = fresh_m5.index[0]
                    gap_seconds = (first_fresh_ts - last_stored_ts).total_seconds()
                    if gap_seconds > 1500:  # ห่างเกิน 25 นาที (5 แท่ง M5) = มี gap
                        logger.warning(f"[GAP] M5 {symbol}: detected {gap_seconds:.0f}s gap — refetching 200 candles")
                        full_m5 = self.data_adapter.get_candles(symbol, 'M5', 200)
                        if full_m5 is not None and not full_m5.empty:
                            self.store_m5[symbol] = full_m5
                    else:
                        # เช็คความถูกต้อง: เฉพาะแท่งที่ปิดสมบูรณ์แล้ว
                        overlap = self.store_m5[symbol].index.intersection(fresh_m5.index)
                        if len(overlap) > 0:
                            check_idx = overlap[:-1] if len(overlap) > 1 else overlap
                            if len(check_idx) > 0:
                                old_vals = self.store_m5[symbol].loc[check_idx[-4:]]
                                new_vals = fresh_m5.loc[check_idx[-4:]]
                                mismatch = (old_vals['close'] != new_vals['close']).any()
                                if mismatch:
                                    logger.warning(f"[VERIFY] M5 {symbol}: mismatch in completed candles — corrected")
                        combined = pd.concat([self.store_m5[symbol], fresh_m5])
                        combined = combined[~combined.index.duplicated(keep='last')].sort_index()
                        self.store_m5[symbol] = combined.tail(200)
                    self.last_block_m5[symbol] = block_5m
                else:
                    logger.warning(f"[FETCH] Failed to fetch M5 for {symbol} — will retry next minute")
            
            candles_m5 = self.store_m5[symbol]
            
            # ตัดแท่งที่กำลังวิ่ง
            if (now_naive - candles_m5.index[-1]).total_seconds() < 300:
                completed_m5 = candles_m5.iloc[:-1]
            else:
                completed_m5 = candles_m5
            
            # เขียน M5 CSV เฉพาะรอบที่ block 5 นาทีเปลี่ยน (ไม่เขียนซ้ำทุกนาที)
            if block_5m != self._m5_csv_written.get(symbol, -1):
                completed_m5.to_csv(os.path.join(save_dir, "M5.csv"))
                self._m5_csv_written[symbol] = block_5m
            
            block_15m = current_min // 15
            m5_updated = (self.last_block_m5[symbol] == block_5m)
            if self.store_m15[symbol] is None or (block_15m != self.last_block_m15[symbol] and m5_updated):
                # คำนวณ M15 จาก store M5 (Resample 3 แท่ง M5 = 1 แท่ง M15)
                candles_m15_calc = candles_m5.resample('15min').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                }).dropna()
                
                if not candles_m15_calc.empty:
                    # ตัดแท่งที่กำลังวิ่ง
                    if (now_naive - candles_m15_calc.index[-1]).total_seconds() < 900:
                        completed_m15_calc = candles_m15_calc.iloc[:-1]
                    else:
                        completed_m15_calc = candles_m15_calc
                    
                    if self.store_m15[symbol] is None:
                        self.store_m15[symbol] = completed_m15_calc
                    else:
                        # รวมข้อมูล M15 ที่คำนวณเข้ากับข้อมูลเดิมที่ดึงมาตอนเริ่มต้น
                        combined_m15 = pd.concat([self.store_m15[symbol], completed_m15_calc])
                        combined_m15 = combined_m15[~combined_m15.index.duplicated(keep='last')].sort_index()
                        self.store_m15[symbol] = combined_m15.tail(200)
                        
                    self.last_block_m15[symbol] = block_15m
                    
                    # เขียน M15 CSV ทุก 15 นาที
                    self.store_m15[symbol].to_csv(os.path.join(save_dir, "M15.csv"))
                else:
                    logger.warning(f"[CALC] Resampled M15 empty for {symbol} — will retry next minute")
            
            candles_m15 = self.store_m15[symbol]
            if candles_m15 is not None and not candles_m15.empty:
                if (now_naive - candles_m15.index[-1]).total_seconds() < 900:
                    completed_m15 = candles_m15.iloc[:-1]
                else:
                    completed_m15 = candles_m15
            else:
                completed_m15 = pd.DataFrame()
                
            current_price = float(candles_m1['close'].iloc[-1])
            return (symbol, (completed_m1, completed_m5, completed_m15, current_price))
            
        except Exception as ex:
            logger.error(f"Symbol {symbol} data fetching/saving failed: {ex}")
            return None

    def run_ai_analysis_and_trade(self, symbol, candles_dict, current_price):
        try:
            completed_m1 = candles_dict['M1']
            completed_m5 = candles_dict['M5']
            completed_m15 = candles_dict['M15']
            
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
                    
                # Extract rsi from indicator store
                from core.indicator_store import store
                payload = store.get_payload(symbol)
                m5_inds = payload.get('m5', {})
                rsi = m5_inds.get('rsi14', 50.0)
                
            except Exception as e:
                logger.error(f"Orchestrator cycle failed for {symbol}: {e}")
                rsi = 50.0
            
            thai_console_log(f"[{symbol}; {current_price:.5f}]")
            
            # Call DeepSeek Brain
            ai_context_to_send = None
            if getattr(self, "use_advanced_ai_context", True) and log_data:
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
                        if self.store_m1.get(trade.symbol) is not None:
                            exit_price = float(self.store_m1[trade.symbol]['close'].iloc[-1])
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
            if balance is not None:
                thai_console_log(f"ยอดเงินคงเหลือ: ${balance:.2f}")
        except Exception:
            pass

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
        for sym in self.symbols:
            res = None
            for f in futures:
                try:
                    result_val = f.result()
                    if result_val and result_val[0] == sym:
                        res = result_val[1]
                        break
                except Exception as e:
                    logger.error(f"Error getting future result for {sym}: {e}")
            
            if res is None:
                continue
                
            completed_m1, completed_m5, completed_m15, current_price = res
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
