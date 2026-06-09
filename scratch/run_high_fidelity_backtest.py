import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd

PROJECT_ROOT = Path("c:/Users/Administrator/Downloads/BOT_FINALBOT/BOT_FINALBOT")
sys.path.insert(0, str(PROJECT_ROOT))

# Safe stream wrapper for Windows console encoding
class SafeStreamWrapper:
    def __init__(self, original_stream):
        self.original_stream = original_stream
    def write(self, data):
        try:
            self.original_stream.write(data)
        except Exception:
            try:
                safe_data = data.encode('ascii', errors='backslashreplace').decode('ascii')
                self.original_stream.write(safe_data)
            except Exception:
                pass
    def flush(self):
        if hasattr(self.original_stream, 'flush'):
            self.original_stream.flush()
    def __getattr__(self, attr):
        return getattr(self.original_stream, attr)

sys.stdout = SafeStreamWrapper(sys.stdout)
sys.stderr = SafeStreamWrapper(sys.stderr)

import logging
from runner import BotRunner
from core.data.csv_data_adapter import CSVDataAdapter

# Suppress verbose logging
logging.basicConfig(level=logging.ERROR)
for l_name in ["FINALBOT", "runner", "core", "execution", "strategy"]:
    logging.getLogger(l_name).setLevel(logging.ERROR)
    logging.getLogger(l_name).propagate = False

class BypassExecutionGate:
    def evaluate(self, context, recommendation):
        return {
            'approved': True,
            'reason': "Bypass for backtest",
            'blocked_by': None,
            'risk_score': 0
        }

class BypassExecutionGuard:
    def check(self, signal_data):
        return {'allowed': True, 'reason': "Bypass for backtest", 'veto_code': None}
    def record_trade_opened(self):
        pass
    def record_trade_result(self, won, profit_loss):
        pass

def run_backtest_for_symbol(symbol, bot, csv_adapter, start_dt, end_dt):
    print(f"\n⏳ Loading historical M5, M15, M60, and M1 candles for {symbol}...")
    timeframes = ["M1", "M5", "M15", "M60"]
    if not csv_adapter.load_symbol_data(symbol, timeframes):
        print(f"❌ Error: Failed to load CSV data files for {symbol}")
        return []

    # Standardize timezone to UTC
    for tf in timeframes:
        df = csv_adapter.dfs[symbol][tf]
        if df.index.tzinfo is None:
            df.index = df.index.tz_localize(timezone.utc)
        else:
            df.index = df.index.tz_convert(timezone.utc)
        csv_adapter.dfs[symbol][tf] = df

    # Get M5 timestamps for the loop
    m5_df = csv_adapter.dfs[symbol]["M5"]
    ref_timestamps = m5_df.index
    
    valid_indices = [
        i for i, ts in enumerate(ref_timestamps)
        if start_dt <= ts <= end_dt
    ]
    
    if not valid_indices:
        print(f"❌ Error: No M5 data found for {symbol} in the specified window.")
        return []
        
    start_index = min(valid_indices)
    end_index = max(valid_indices)
    
    trade_history = []
    
    print(f"🔄 Running simulation for {symbol} ({len(valid_indices)} M5 bars)...")
    
    # Loop M5 ticks
    for i in range(start_index, end_index + 3):
        if i >= len(ref_timestamps):
            break
        timestamp = ref_timestamps[i]
        
        # A. Settle active expired trades (5 minutes = option expiry duration)
        active_trades = list(bot.order_manager.active_trades.items())
        for order_id, trade in active_trades:
            if trade.symbol == symbol and timestamp >= trade.entry_time + timedelta(minutes=5):
                if timestamp in m5_df.index:
                    exit_price = float(m5_df.loc[timestamp, "close"])
                    won = False
                    if trade.direction == 'CALL':
                        won = exit_price > trade.entry_price
                    elif trade.direction == 'PUT':
                        won = exit_price < trade.entry_price
                        
                    pnl = trade.amount * 0.85 if won else -trade.amount
                    
                    # Close trade
                    bot.order_manager.close_trade(
                        order_id=order_id,
                        exit_price=exit_price,
                        pnl=pnl,
                        notes=f"Settle at {timestamp.isoformat()}"
                    )
                    
                    # Calculate MAE, MFE
                    mae, mfe, price_trajectory = 0.0, 0.0, [exit_price]
                    try:
                        m1_df = csv_adapter.dfs[symbol]["M1"]
                        m1_slice = m1_df.loc[trade.entry_time : timestamp]
                        if not m1_slice.empty:
                            highs = m1_slice['high'].tolist()
                            lows = m1_slice['low'].tolist()
                            price_trajectory = m1_slice['close'].tolist()
                            
                            if trade.direction == 'CALL':
                                mae = float(max(0.0, trade.entry_price - min(lows)))
                                mfe = float(max(0.0, max(highs) - trade.entry_price))
                            elif trade.direction == 'PUT':
                                mae = float(max(0.0, max(highs) - trade.entry_price))
                                mfe = float(max(0.0, trade.entry_price - min(lows)))
                    except:
                        pass
                        
                    trade_record = {
                        'timestamp': trade.entry_time.isoformat(),
                        'symbol': symbol,
                        'direction': trade.direction,
                        'entry_price': trade.entry_price,
                        'exit_price': exit_price,
                        'won': won,
                        'pnl': pnl,
                        'strategy': trade.notes,
                        'mae': mae,
                        'mfe': mfe,
                        'price_trajectory': price_trajectory
                    }
                    trade_history.append(trade_record)
                    
                    result_emoji = "🟢 WIN" if won else "🔴 LOSS"
                    print(f"[{trade.entry_time.strftime('%Y-%m-%d %H:%M:%S')}] {symbol} {trade.direction:<4} | Price: {trade.entry_price:.5f} -> {exit_price:.5f} | {result_emoji} | PnL: {pnl:+.2f} THB (MAE: {mae:.5f}, MFE: {mfe:.5f})")

        # B. Set simulated clock cursor
        csv_adapter.set_simulated_time(timestamp)
        
        # C. Prevent duplicate trades on the same symbol
        if bot.order_manager.get_active_trades(symbol):
            continue
            
        # D. Run bot pipeline
        result = bot.run_single_cycle(symbol)
        
        if result.get('executed') and result.get('order_id'):
            order_id = result['order_id']
            if order_id in bot.order_manager.active_trades:
                trade = bot.order_manager.active_trades[order_id]
                trade.entry_time = timestamp
                trade.notes = result.get('strategy', 'unknown')
                
    return trade_history

def main():
    os.chdir(str(PROJECT_ROOT))
    
    # Target date: Wednesday, May 27, 2026
    # 11:00 to 23:00 GMT+7 = 04:00 to 16:00 UTC
    start_dt = datetime(2026, 5, 27, 4, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 5, 27, 16, 0, tzinfo=timezone.utc)
    
    # Clear previous backtest logs
    backtest_signals_path = PROJECT_ROOT / "logs" / "backtest_signals.json"
    if backtest_signals_path.exists():
        try:
            backtest_signals_path.unlink()
        except:
            pass

    csv_adapter = CSVDataAdapter(data_dir="historical_data")
    
    # Instantiate BotRunner
    bot = BotRunner(
        symbols=["EURUSD", "EURUSD-OTC"],
        capital=2000.0,
        use_mock=True,
        account_type="PRACTICE"
    )
    
    bot.bot_mode = 'TRADE'
    bot.data_adapter = csv_adapter
    bot.executor.use_mock = True
    bot.use_mock = True
    bot.execution_gate = BypassExecutionGate()
    bot.intelligence_pipeline.execution_gate = bot.intelligence_pipeline.execution_gate
    bot.execution_guard = BypassExecutionGuard()
    bot.position_sizer.calculate = lambda confidence=None: 35.0
    
    print("="*80)
    print("🚀 FINALBOT BACKTEST (EURUSD-OTC)")
    print("="*80)
    print(f"Date                : Wednesday, 2026-05-27")
    print(f"Time Window (GMT+7) : 11:00 to 23:00")
    print(f"Active Strategy     : Rejection 5m PA (M1 patterns, M5 levels, 5m expiry)")
    print("="*80)
    
    otc_trades = run_backtest_for_symbol("EURUSD-OTC", bot, csv_adapter, start_dt, end_dt)
    all_trades = otc_trades
    
    print("\n" + "="*80)
    print("📊 BACKTEST SUMMARY REPORT")
    print("="*80)
    total_trades = len(all_trades)
    print(f"Total Trades Executed : {total_trades}")
    
    if total_trades == 0:
        print("No trades were triggered. This means no Price Action Rejections occurred at M5 levels.")
        print("="*80)
        return
        
    wins = sum(1 for t in all_trades if t['won'])
    losses = total_trades - wins
    win_rate = (wins / total_trades) * 100
    net_pnl = sum(t['pnl'] for t in all_trades)
    
    print(f"Wins                  : {wins} 🟢")
    print(f"Losses                : {losses} 🔴")
    print(f"Win Rate (%)          : {win_rate:.2f}%")
    print(f"Net Profit/Loss       : {net_pnl:+.2f} THB")
    print("="*80)
    
    # Save the output files
    output_dir = Path("C:/Users/Administrator/Downloads/TEST")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "backtest_with_outcomes.json", "w", encoding="utf-8") as f:
        json.dump(all_trades, f, indent=2, ensure_ascii=False)
        
    # Strip outcomes for without_outcomes
    no_outcomes = []
    for t in all_trades:
        t_copy = t.copy()
        if "trade_outcome" in t_copy:
            del t_copy["trade_outcome"]
        no_outcomes.append(t_copy)
        
    with open(output_dir / "backtest_without_outcomes.json", "w", encoding="utf-8") as f:
        json.dump(no_outcomes, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
