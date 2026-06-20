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
log_file_name = f"logs/bot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler(log_file_name, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
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

class PureAIRunner:
    def __init__(self):
        # Load settings
        from core.config_loader import load_settings
        self.settings = load_settings(reload=False)
        
        account_cfg = self.settings.get("account", {})
        self.account_type = account_cfg.get("account_type", "PRACTICE")
        self.symbols = self.settings.get("symbols", ["EURUSD"])
        self.capital = self.settings.get("capital", {}).get("starting_balance", 1000)
        self.stake = self.settings.get("capital", {}).get("stake_per_trade", 10)
        
        # Initialize adapter and executor
        self.data_adapter = IQOptionAdapter(account_type=self.account_type)
        if not self.data_adapter.is_connected():
            thai_console_log("❌ Failed to connect to IQ Option.")
            sys.exit(1)
            
        self.executor = IQOptionExecutor(adapter=self.data_adapter, account_type=self.account_type)
        
        # Pull max_concurrent from settings, default to 5 if not set
        max_conc = self.settings.get("limits", {}).get("max_concurrent", 5)
        self.order_manager = OrderManager(max_concurrent=max_conc)
        
        # Initialize DeepSeek bridge
        ai_cfg = self.settings.get("ai_mode", {})
        agent_cmd = ai_cfg.get("agent_command", "deepseek-agent")
        timeout_sec = ai_cfg.get("timeout_seconds", 45)
        self.ai_bridge = DeepSeekAgentBridge(agent_command=agent_cmd, timeout_seconds=timeout_sec)
        self.trade_logger = TradeLogger()  # Initialize trade logger
        
        self.last_processed_candle = {sym: None for sym in self.symbols}
        thai_console_log(f"🚀 Pure AI Bot initialized. Account: {self.account_type} | Stake: {self.stake} | Symbols: {self.symbols}")

    def calc_rsi(self, prices, period=14):
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])

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
                
            close_prices = completed_candles['close']
            high_prices = completed_candles['high']
            low_prices = completed_candles['low']
            
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
            
            current_price = float(close_prices.iloc[-1])
            
            # Create a simple mock context object for the bridge
            class SimpleContext:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)
            
            context = SimpleContext(
                symbol=symbol,
                current_price=current_price,
                trend="bullish" if ema20 > ema50 else "bearish",
                volatility="high" if (bb_upper - bb_lower) / bb_mid > 0.01 else "low",
                support_resistance=f"Support: {low_prices.iloc[-10:].min():.5f}, Resistance: {high_prices.iloc[-10:].max():.5f}",
                rsi=rsi,
                macd=curr_macd - curr_macd_sig,
                market_state="normal"
            )
            
            # --- Trade Logging (data_A.json format) ---
            try:
                # Fetch additional timeframes for comprehensive logging
                candles_m1 = self.data_adapter.get_candles(symbol, 'M1', 100)
                candles_m15 = self.data_adapter.get_candles(symbol, 'M15', 100)
                candles_dict = {'M5': candles, 'M1': candles_m1, 'M15': candles_m15}
                
                log_data = self.trade_logger.build_log_data(
                    symbol=symbol,
                    candles_dict=candles_dict,
                    primary_timeframe='M5',
                    ai_context=context
                )
                if log_data:
                    log_path = self.trade_logger.save_log(log_data)
                    if log_path:
                        thai_console_log(f"📝 Trade log saved: {log_path}")
            except Exception as e:
                logger.error(f"Trade logging failed for {symbol}: {e}")
            
            thai_console_log(f"📊 Sending M5 indicators for {symbol} to DeepSeek: Price={current_price:.5f}, RSI={rsi:.2f}, MACD={context.macd:.6f}, EMA20={ema20:.5f}")
            
            # Call DeepSeek Brain
            insight = self.ai_bridge.analyze_market(context)
            if not insight:
                continue
                
            self.last_processed_candle[symbol] = last_ts
            
            thai_console_log(f"🧠 DeepSeek Decision: {insight.action} | Confidence: {insight.confidence}% | Expiry Chosen: {insight.expiry}m | Reason: {insight.reason}")
            
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
                    if result.status == 'executed':
                        order_id = result.order_id
                        # Record trade in order manager using its add_trade method
                        self.order_manager.add_trade(
                            order_id=str(order_id),
                            symbol=symbol,
                            direction=insight.action,
                            amount=self.stake,
                            entry_price=current_price,
                            expiry=f"M{insight.expiry}"
                        )
                        thai_console_log(f"✅ Trade executed successfully. Order ID: {order_id}")
                    else:
                        thai_console_log(f"❌ Execution failed for {symbol}: {result.reason}")
                except Exception as e:
                    logger.error(f"Execution exception: {e}")

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

if __name__ == "__main__":
    runner = PureAIRunner()
    runner.start()
