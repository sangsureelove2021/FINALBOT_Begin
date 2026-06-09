"""
High-Fidelity Offline Backtest Engine for FINALBOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Runs a comprehensive historical simulation on a single pair in TRADE mode.
- Whichever of the 4 active strategies triggers first is executed immediately.
- Bypasses all daily limits, cooldown periods, time filters, and risk gates.
- Records the complete market context and indicator details to logs/backtest_signals.json
  in the exact same structured format as AI mode.
- Evaluates outcome using forward-looking candle close at option expiry (5 min).
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd

# Add project root to path
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

# Suppress all verbose logging for maximum backtest speed and cleaner output
logging.basicConfig(level=logging.ERROR)
for l_name in ["FINALBOT", "runner", "core", "execution", "strategy"]:
    logging.getLogger(l_name).setLevel(logging.ERROR)
    logging.getLogger(l_name).propagate = False

# Bypass risk evaluation for backtest execution
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

def main():
    # 1. Setup paths and clear previous backtest logs
    os.chdir(str(PROJECT_ROOT))
    backtest_signals_path = PROJECT_ROOT / "logs" / "backtest_signals.json"
    if backtest_signals_path.exists():
        try:
            backtest_signals_path.unlink()
        except:
            pass
            
    print("="*80)
    print("🚀 FINALBOT HIGH-FIDELITY OFFLINE BACKTEST SIMULATOR")
    print("="*80)
    
    # 2. Select pair to test (Command line argument with EURUSD-OTC as fallback)
    symbol = sys.argv[1] if len(sys.argv) > 1 else "EURUSD-OTC"
    print(f"Asset to test: {symbol}")
    print("Bot operating mode: TRADE (No filters/gates, execute immediately)")
    print(f"Chronological AI-style logs: logs/backtest_signals.json")
    print("="*80)
    
    # 3. Load historical M5 data
    print("⏳ Loading historical M5, M15, M60, and M1 candles into memory...")
    csv_adapter = CSVDataAdapter(data_dir="historical_data")
    timeframes = ["M1", "M5", "M15", "M60"]
    
    if not csv_adapter.load_symbol_data(symbol, timeframes):
        print("❌ Error: Failed to load CSV data files. Please check historical_data folder.")
        return
        
    # Standardize timezone to UTC
    for tf in timeframes:
        df = csv_adapter.dfs[symbol][tf]
        if df.index.tzinfo is None:
            df.index = df.index.tz_localize(timezone.utc)
        else:
            df.index = df.index.tz_convert(timezone.utc)
        csv_adapter.dfs[symbol][tf] = df
        
    print("✅ All historical timeframes loaded successfully.")
    
    # 4. Instantiate BotRunner
    bot = BotRunner(
        symbols=[symbol],
        capital=2000.0,
        use_mock=True,
        account_type="PRACTICE"
    )
    
    # Configure bot settings for simulated backtest
    bot.bot_mode = 'TRADE'
    bot.data_adapter = csv_adapter
    bot.executor.use_mock = True
    bot.use_mock = True
    bot.execution_gate = BypassExecutionGate()
    bot.intelligence_pipeline.execution_gate = bot.execution_gate
    bot.execution_guard = BypassExecutionGuard()
    
    # Force sizer to return exactly 35.0 as requested by the user
    bot.position_sizer.calculate = lambda confidence=None: 35.0
    
    # Get M5 timestamps for the backtest loop
    m5_df = csv_adapter.dfs[symbol]["M5"]
    ref_timestamps = m5_df.index
    total_candles = len(ref_timestamps)
    
    # Filter M5 timestamps for exactly 2026-05-23 from 11:00 to 23:00 local time (GMT+7)
    # 11:00 GMT+7 = 04:00 UTC
    # 23:00 GMT+7 = 16:00 UTC
    start_dt = datetime(2026, 5, 23, 4, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 5, 23, 16, 0, tzinfo=timezone.utc)
    
    valid_indices = [
        i for i, ts in enumerate(ref_timestamps)
        if start_dt <= ts <= end_dt
    ]
    
    if not valid_indices:
        print("❌ Error: No M5 historical data found for 2026-05-23 in the specified window.")
        return
        
    start_index = min(valid_indices)
    end_index = max(valid_indices)
    
    initial_balance = 2000.0
    balance = initial_balance
    stake = 35.0
    payout_rate = 0.85
    
    trade_history = []
    
    print(f"📈 Backtest Date            : 2026-05-23")
    print(f"📈 Time Window (GMT+7 Local): 11:00 to 23:00")
    print(f"📈 Corresponding UTC Window   : {start_dt.strftime('%Y-%m-%d %H:%M:%S')} to {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📈 Starting Capital         : {initial_balance:.2f} THB")
    print(f"📈 Stake Size per Trade     : {stake:.2f} THB")
    print(f"📈 Total M5 Bars in Loop    : {len(valid_indices)}")
    print("🔄 Running simulation...")
    
    # Loop from start_index to end_index + 1 (plus allow 2 extra cycles to settle any final outstanding trade)
    for i in range(start_index, end_index + 3):
        if i >= len(ref_timestamps):
            break
        timestamp = ref_timestamps[i]
        
        # A. Settle active expired trades (5 minutes = option expiry duration)
        active_trades = list(bot.order_manager.active_trades.items())
        for order_id, trade in active_trades:
            if timestamp >= trade.entry_time + timedelta(minutes=5):
                # Fetch settlement price at expiration
                if timestamp in m5_df.index:
                    exit_price = float(m5_df.loc[timestamp, "close"])
                    
                    won = False
                    if trade.direction == 'CALL':
                        won = exit_price > trade.entry_price
                    elif trade.direction == 'PUT':
                        won = exit_price < trade.entry_price
                        
                    pnl = trade.amount * payout_rate if won else -trade.amount
                    balance += pnl
                    
                    # Preserve the original strategy name from trade.notes
                    strategy_name = trade.notes
                    
                    # Close trade in OrderManager
                    bot.order_manager.close_trade(
                        order_id=order_id,
                        exit_price=exit_price,
                        pnl=pnl,
                        notes=f"Settle at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    
                    # Calculate high-fidelity MAE, MFE and Price Trajectory using M1 data
                    mae = 0.0
                    mfe = 0.0
                    price_trajectory = []
                    
                    try:
                        m1_df = csv_adapter.dfs[symbol]["M1"]
                        # Slice M1 data for the 5-minute trade lifetime (inclusive of start and end)
                        m1_slice = m1_df.loc[trade.entry_time : timestamp]
                        if not m1_slice.empty:
                            highs = m1_slice['high'].tolist()
                            lows = m1_slice['low'].tolist()
                            price_trajectory = m1_slice['close'].tolist()
                            
                            if trade.direction == 'CALL':
                                # MAE: Maximum drop below entry price
                                min_low = min(lows)
                                mae = float(max(0.0, trade.entry_price - min_low))
                                # MFE: Maximum rise above entry price
                                max_high = max(highs)
                                mfe = float(max(0.0, max_high - trade.entry_price))
                            elif trade.direction == 'PUT':
                                # MAE: Maximum rise above entry price
                                max_high = max(highs)
                                mae = float(max(0.0, max_high - trade.entry_price))
                                # MFE: Maximum drop below entry price
                                min_low = min(lows)
                                mfe = float(max(0.0, trade.entry_price - min_low))
                    except Exception as ex:
                        mae = 0.0
                        mfe = 0.0
                        price_trajectory = [exit_price]

                    # Update backtest_signals.json with high-fidelity trade_outcome in Unified Schema
                    try:
                        if backtest_signals_path.exists():
                            with open(backtest_signals_path, "r", encoding="utf-8") as f_backtest:
                                records = json.load(f_backtest)
                                if isinstance(records, list):
                                    updated = False
                                    # Find matching record: same timestamp (approx), symbol, direction
                                    for rec in reversed(records):
                                        try:
                                            rec_time = datetime.fromisoformat(rec['timestamp'])
                                            if abs((rec_time - (trade.entry_time - timedelta(minutes=5))).total_seconds()) < 5 and rec['symbol'] == symbol and rec['direction'] == trade.direction:
                                                rec['trade_outcome'] = {
                                                    'won': won,
                                                    'exit_price': exit_price,
                                                    'exit_time': timestamp.isoformat(),
                                                    'pnl': pnl,
                                                    'max_adverse_excursion': mae,
                                                    'max_favorable_excursion': mfe,
                                                    'price_trajectory': price_trajectory
                                                }
                                                updated = True
                                                break
                                        except:
                                            continue
                                    
                                    if updated:
                                        with open(backtest_signals_path, "w", encoding="utf-8") as f_backtest:
                                            json.dump(records, f_backtest, indent=2, ensure_ascii=False)
                    except:
                        pass
                    
                    # Log result
                    trade_record = {
                        'timestamp': trade.entry_time.isoformat(),
                        'symbol': symbol,
                        'direction': trade.direction,
                        'entry_price': trade.entry_price,
                        'exit_price': exit_price,
                        'won': won,
                        'pnl': pnl,
                        'balance': balance,
                        'strategy': strategy_name,
                        'mae': mae,
                        'mfe': mfe
                    }
                    trade_history.append(trade_record)
                    
                    result_emoji = "🟢 WIN" if won else "🔴 LOSS"
                    print(f"[{trade.entry_time.strftime('%Y-%m-%d %H:%M:%S')}] {trade.direction:<4} | {strategy_name:<20} | Price: {trade.entry_price:.5f} -> {exit_price:.5f} | {result_emoji} | PnL: {pnl:+.2f} THB | Balance: {balance:.2f} THB (MAE: {mae:.5f}, MFE: {mfe:.5f})")
        
        # B. Set simulated clock cursor
        csv_adapter.set_simulated_time(timestamp)
        
        # C. Prevent duplicate trades on the same symbol
        if bot.order_manager.get_active_trades(symbol):
            continue
            
        # D. Run bot pipeline for this tick
        result = bot.run_single_cycle(symbol)
        
        # If trade triggered, update its entry time to the historical timestamp
        if result.get('executed') and result.get('order_id'):
            order_id = result['order_id']
            if order_id in bot.order_manager.active_trades:
                trade = bot.order_manager.active_trades[order_id]
                trade.entry_time = timestamp
                trade.notes = result.get('strategy', 'unknown')
                
    print("\n✅ Simulation complete!")
    
    # 5. Compile and print gorgeous summary report
    print("\n" + "="*80)
    print("📊 HISTORICAL BACKTEST PERFORMANCE REPORT")
    print("="*80)
    total_trades = len(trade_history)
    print(f"Total Trades Executed : {total_trades}")
    
    if total_trades == 0:
        print("No trades were triggered. Try checking strategy formulas or data range.")
        print("="*80)
        return
        
    wins = sum(1 for t in trade_history if t['won'])
    losses = total_trades - wins
    win_rate = (wins / total_trades) * 100
    total_pnl = balance - initial_balance
    
    print(f"Wins                  : {wins} 🟢")
    print(f"Losses                : {losses} 🔴")
    print(f"Win Rate (%)          : {win_rate:.2f}%")
    print(f"Starting Capital      : {initial_balance:.2f} THB")
    print(f"Ending Balance        : {balance:.2f} THB")
    print(f"Net Profit/Loss       : {total_pnl:+.2f} THB ({total_pnl/initial_balance*100:+.2f}%)")
    print("="*80)
    
    # Strategy Breakdown
    print("\nPER-STRATEGY BREAKDOWN:")
    print(f"{'STRATEGY':<25} | {'TRADES':<8} | {'WINS':<6} | {'LOSSES':<6} | {'WIN RATE':<10} | {'NET P&L':<15}")
    print("-"*78)
    
    strategies = set(t['strategy'] for t in trade_history)
    for strat in sorted(strategies):
        strat_trades = [t for t in trade_history if t['strategy'] == strat]
        st_count = len(strat_trades)
        st_wins = sum(1 for t in strat_trades if t['won'])
        st_losses = st_count - st_wins
        st_win_rate = (st_wins / st_count) * 100
        st_pnl = sum(t['pnl'] for t in strat_trades)
        print(f"{strat:<25} | {st_count:<8} | {st_wins:<6} | {st_losses:<6} | {st_win_rate:.1f}%     | {st_pnl:+.2f} THB")
    print("="*80 + "\n")
    
    # Write profit report file
    profit_report_path = PROJECT_ROOT / "logs" / "profit_report.txt"
    try:
        with open(profit_report_path, "w", encoding="utf-8") as f:
            f.write("FINALBOT Backtest Profit Report\n")
            f.write(f"Pair: {symbol}\n")
            f.write(f"Total Trades: {total_trades}\n")
            f.write(f"Win Rate: {win_rate:.2f}%\n")
            f.write(f"Net P&L: {total_pnl:.2f} THB\n")
        print(f"Profit report successfully exported to {profit_report_path}")
    except Exception as e:
        print(f"Error exporting profit report: {e}")

    # 6. Save the two requested JSON files (With & Without Outcomes)
    try:
        if backtest_signals_path.exists():
            with open(backtest_signals_path, "r", encoding="utf-8") as f_backtest:
                records = json.load(f_backtest)
            
            # File 1: With Outcomes (Full structure)
            with_outcomes_path = PROJECT_ROOT / "logs" / "backtest_with_outcomes.json"
            test_dir_with = Path("C:/Users/Administrator/Downloads/TEST/backtest_with_outcomes.json")
            
            with open(with_outcomes_path, "w", encoding="utf-8") as fw:
                json.dump(records, fw, indent=2, ensure_ascii=False)
            if test_dir_with.parent.exists():
                with open(test_dir_with, "w", encoding="utf-8") as fw_test:
                    json.dump(records, fw_test, indent=2, ensure_ascii=False)
            print(f"✅ Saved backtest_with_outcomes.json successfully.")
            
            # File 2: Without Outcomes (Strip 'trade_outcome' key)
            records_no_outcome = []
            for rec in records:
                rec_copy = rec.copy()
                if "trade_outcome" in rec_copy:
                    del rec_copy["trade_outcome"]
                records_no_outcome.append(rec_copy)
                
            without_outcomes_path = PROJECT_ROOT / "logs" / "backtest_without_outcomes.json"
            test_dir_without = Path("C:/Users/Administrator/Downloads/TEST/backtest_without_outcomes.json")
            
            with open(without_outcomes_path, "w", encoding="utf-8") as fwo:
                json.dump(records_no_outcome, fwo, indent=2, ensure_ascii=False)
            if test_dir_without.parent.exists():
                with open(test_dir_without, "w", encoding="utf-8") as fwo_test:
                    json.dump(records_no_outcome, fwo_test, indent=2, ensure_ascii=False)
            print(f"✅ Saved backtest_without_outcomes.json successfully.")
    except Exception as e:
        print(f"❌ Error generating outcome files: {e}")
        
if __name__ == "__main__":
    main()
