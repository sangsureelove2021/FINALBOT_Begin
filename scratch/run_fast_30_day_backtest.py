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

from strategy.reversal_strategy.rejection_5m_pa import Rejection5mPAStrategy

class MockContext:
    def __init__(self, symbol, timestamp, candles):
        self.symbol = symbol
        self.timestamp = timestamp
        self.candles = candles

def run_fast_backtest_for_symbol(symbol, start_dt, end_dt):
    print(f"\n⏳ Loading historical data for {symbol}...")
    
    # Load M1 and M5 data
    m1_path = PROJECT_ROOT / f"historical_data/history_{symbol.replace('-', '_')}_M1.csv"
    m5_path = PROJECT_ROOT / f"historical_data/history_{symbol.replace('-', '_')}_M5.csv"
    
    if not m1_path.exists() or not m5_path.exists():
        print(f"❌ Error: CSV files not found for {symbol}")
        return []
        
    m1_df = pd.read_csv(m1_path, index_col='timestamp', parse_dates=True)
    m5_df = pd.read_csv(m5_path, index_col='timestamp', parse_dates=True)
    
    # Localize or convert index to UTC
    if m1_df.index.tzinfo is None:
        m1_df.index = m1_df.index.tz_localize(timezone.utc)
    if m5_df.index.tzinfo is None:
        m5_df.index = m5_df.index.tz_localize(timezone.utc)
        
    # Get M5 timestamps in the range
    ref_timestamps = m5_df.index[(m5_df.index >= start_dt) & (m5_df.index <= end_dt)]
    
    if len(ref_timestamps) == 0:
        print(f"❌ Error: No M5 data found in the specified window.")
        return []
        
    trade_history = []
    balance = 2000.0
    active_trade = None # Only allow 1 active trade at a time
    
    strategy = Rejection5mPAStrategy()
    
    print(f"🔄 Running fast simulation for {symbol} ({len(ref_timestamps)} M5 bars)...")
    
    # Searchsorted indices lookup optimization
    m1_times = m1_df.index
    m5_times = m5_df.index
    
    for timestamp in ref_timestamps:
        # A. Settle active trade if expired
        if active_trade is not None:
            entry_time = active_trade['entry_time']
            expiry_time = entry_time + timedelta(minutes=1) # 1-minute expiry for M1 strategy!
            if timestamp >= expiry_time:
                # Find exit price in M1 at expiry_time (or M5)
                # Since M1 is 1-minute, expiry_time should exist in M1
                exit_price = None
                if expiry_time in m1_df.index:
                    exit_price = float(m1_df.loc[expiry_time, 'close'])
                elif expiry_time in m5_df.index:
                    exit_price = float(m5_df.loc[expiry_time, 'close'])
                else:
                    # fallback to closest index
                    closest_idx = m1_df.index.get_indexer([expiry_time], method='bfill')[0]
                    if closest_idx != -1:
                        exit_price = float(m1_df.iloc[closest_idx]['close'])
                        
                if exit_price is not None:
                    won = False
                    if active_trade['direction'] == 'CALL':
                        won = exit_price > active_trade['entry_price']
                    elif active_trade['direction'] == 'PUT':
                        won = exit_price < active_trade['entry_price']
                        
                    pnl = active_trade['amount'] * 0.85 if won else -active_trade['amount']
                    balance += pnl
                    
                    trade_record = {
                        'timestamp': entry_time.isoformat(),
                        'symbol': symbol,
                        'direction': active_trade['direction'],
                        'entry_price': active_trade['entry_price'],
                        'exit_price': exit_price,
                        'won': won,
                        'pnl': pnl,
                        'balance': balance,
                        'strategy': active_trade['strategy']
                    }
                    trade_history.append(trade_record)
                    active_trade = None
                else:
                    active_trade = None
        
        # B. Skip signal generation if we have an active trade
        if active_trade is not None:
            continue
            
        # C. Slice historical data strictly up to the current timestamp
        # Using fast binary search slicing
        pos_m1 = m1_times.searchsorted(timestamp, side='right')
        pos_m5 = m5_times.searchsorted(timestamp, side='right')
        
        if pos_m1 < 21 or pos_m5 < 21:
            continue
            
        m1_sliced = m1_df.iloc[:pos_m1]
        m5_sliced = m5_df.iloc[:pos_m5]
        
        # Slice to drop the last uncompleted active candle
        m1_completed = m1_sliced.iloc[:-1].tail(200)
        m5_completed = m5_sliced.iloc[:-1].tail(200)
        
        candles = {
            'M1': m1_completed,
            'M5': m5_completed
        }
        
        context = MockContext(symbol, timestamp, candles)
        
        # Evaluate strategy
        result = strategy.evaluate(context)
        action = result.get('action')
        
        if action in ('CALL', 'PUT'):
            current_price = float(m1_completed['close'].iloc[-1])
            active_trade = {
                'entry_time': timestamp,
                'direction': action,
                'entry_price': current_price,
                'amount': 35.0,
                'strategy': strategy.STRATEGY_NAME
            }
            
    return trade_history

def main():
    # 30 days: 2026-04-29 to 2026-05-29
    start_dt = datetime(2026, 4, 29, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 5, 29, 0, 0, tzinfo=timezone.utc)
    
    print("="*80)
    print("🚀 HYPER-SPEED OFFLINE BACKTEST (IN-MEMORY)")
    print("="*80)
    
    eurusd_trades = run_fast_backtest_for_symbol("EURUSD", start_dt, end_dt)
    otc_trades = run_fast_backtest_for_symbol("EURUSD-OTC", start_dt, end_dt)
    
    all_trades = eurusd_trades + otc_trades
    
    print("\n" + "="*80)
    print("📊 30-DAY BACKTEST SUMMARY REPORT")
    print("="*80)
    
    for symbol, trades_list in [("EURUSD", eurusd_trades), ("EURUSD-OTC", otc_trades)]:
        total = len(trades_list)
        print(f"\nAsset: {symbol}")
        print(f"  Total Trades : {total}")
        if total > 0:
            wins = sum(1 for t in trades_list if t['won'])
            losses = total - wins
            wr = (wins / total) * 100
            pnl = sum(t['pnl'] for t in trades_list)
            print(f"  Wins         : {wins} 🟢")
            print(f"  Losses       : {losses} 🔴")
            print(f"  Win Rate     : {wr:.2f}%")
            print(f"  Net PnL      : {pnl:+.2f} USD")
        else:
            print("  No trades triggered.")
            
    print("\n" + "="*80)
    total_overall = len(all_trades)
    print(f"Overall Total Trades : {total_overall}")
    if total_overall > 0:
        wins = sum(1 for t in all_trades if t['won'])
        losses = total_overall - wins
        wr = (wins / total_overall) * 100
        pnl = sum(t['pnl'] for t in all_trades)
        print(f"Overall Wins         : {wins} 🟢")
        print(f"Overall Losses       : {losses} 🔴")
        print(f"Overall Win Rate     : {wr:.2f}%")
        print(f"Overall Net PnL      : {pnl:+.2f} USD")
    print("="*80)
    
    # Save the output files
    output_dir = Path("C:/Users/Administrator/Downloads/TEST")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "backtest_with_outcomes.json", "w", encoding="utf-8") as f:
        json.dump(all_trades, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
