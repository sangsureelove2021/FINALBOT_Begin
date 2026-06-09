"""
Offline Backtest Engine for FINALBOT (SELECTIVE CHECKPOINTS - ONLY 5 & 10 ACTIVE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Simulates last 30 days of trading (April 27 - May 27, 2026)
on EURUSD using 2000 THB capital and 35 THB stake per trade.
Enforces ONLY:
- Checkpoint 5: Trap Detection (Blocks trade if trap_detected is True)
- Checkpoint 10: Volatility Regime check (Blocks trade if regime is EXTREME)

Bypasses all other 11 checkpoints:
- Bypasses Time-of-day filter (trades 24 hours a day)
- Bypasses Daily trade limit (no limit)
- Bypasses Post-loss cooldown (no cooldown)
- Bypasses Entry Score, Block Score, Confidence, and MTF alignment checks
"""

import os
import sys
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np

# Prevent UnicodeEncodeError on Windows terminals
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Ensure project root is in sys.path
sys.path.append(os.path.abspath("e:/BOT_FINALBOT"))

from core.data.csv_data_adapter import CSVDataAdapter
from core.orchestration.context_builder import ContextBuilder
from core.engines.engine_registry import EngineRegistry

# Import only necessary engines for 10x speedup
from core.engines.trend_engine import TrendEngine
from core.engines.strength_engine import StrengthEngine
from core.engines.volatility_engine import VolatilityEngine
from core.engines.structure_engine import StructureEngine
from core.engines.mtf_engine import MTFEngine
from core.engines.market_state_classifier import MarketStateClassifier
from core.engines.trap_detector import TrapDetector  # Required for Checkpoint 5

from strategy.compression_breakout.strategy import CompressionBreakoutStrategy

def run_simulation():
    print("="*80)
    print("🚀 FINALBOT OFFLINE BACKTEST SIMULATOR (SELECTIVE CHECKPOINTS)")
    print("="*80)
    print("Asset       : EURUSD")
    print("Data Period : Last 30 Days (2026-04-27 to 2026-05-27)")
    print("Time Window : 24 Hours (UNLOCKED)")
    print("Starting Cap: 2000.00 THB")
    print("Stake Size  : 35.00 THB")
    print("Payout Rate : 85% (Win = +29.75 THB, Loss = -35.00 THB)")
    print("Active Locks: ONLY Checkpoint 5 (Trap) & Checkpoint 10 (Extreme Vol) 🛡️")
    print("Other Locks : ALL BYPASSED 🔓")
    print("="*80)

    # Initialize data source
    data_adapter = CSVDataAdapter(data_dir="e:/BOT_FINALBOT/historical_data")
    timeframes = ['M1', 'M5', 'M15', 'M60']
    symbol = "EURUSD"
    
    print("[INIT] Pre-loading historical CSV files into memory...")
    if not data_adapter.load_symbol_data(symbol, timeframes):
        print("❌ Error: Failed to load CSV data files.")
        return

    # Setup Optimized Engine Registry with essential engines + TrapDetector
    engine_registry = EngineRegistry()
    engine_registry.register(TrendEngine())
    engine_registry.register(StrengthEngine())
    engine_registry.register(VolatilityEngine())
    engine_registry.register(StructureEngine())
    engine_registry.register(MTFEngine())
    engine_registry.register(MarketStateClassifier())
    engine_registry.register(TrapDetector())
    
    context_builder = ContextBuilder(engine_registry)
    strategy = CompressionBreakoutStrategy()
    
    # Simulation parameters (exact 30 days)
    start_time = datetime(2026, 4, 27, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2026, 5, 27, 23, 15, tzinfo=timezone.utc)
    
    # Financial parameters
    initial_balance = 2000.0
    balance = initial_balance
    stake = 35.0
    payout_multiplier = 0.85
    win_payout = stake * payout_multiplier
    
    # Backtest statistics
    trades = [] # list of dicts
    
    # Load M5 index to loop through the timeline
    m5_df = data_adapter.dfs[symbol]['M5']
    timeline = m5_df.loc[start_time:end_time].index
    
    print(f"[START] Running timeline simulation over {len(timeline)} ticks of M5 candles...")
    
    for i, current_tick in enumerate(timeline):
        local_tick = current_tick + timedelta(hours=7)
        
        # Set the simulated time machine cursor
        data_adapter.set_simulated_time(current_tick)
        
        # Fetch multi-timeframe sliced data safely
        try:
            candles_dict = data_adapter.get_multi_timeframe(symbol, timeframes, count=300)
            
            # Align timeframes
            from core.data.timeframe_sync import TimeframeSync
            synced = TimeframeSync(primary='M5').sync(candles_dict)
            
            # 1. Build context (runs the registered engines)
            context = context_builder.build(symbol, synced, 'M5')
            
            # 2. Run Strategy
            recommendation = strategy.evaluate(context)
            
            if recommendation.get('action') == 'NO_SIGNAL':
                continue
                
            # --- EVALUATE ONLY CHECKPOINT 5 & 10 ---
            
            # ด่าน 5: Trap Detection
            if context.traps.get('trap_detected'):
                # print(f"[DEBUG BLOCK] Signal blocked by Checkpoint 5: Trap Detected")
                continue
                
            # ด่าน 10: Volatility Regime check
            regime = context.volatility.get('regime', 'NORMAL')
            if regime == 'EXTREME':
                # print(f"[DEBUG BLOCK] Signal blocked by Checkpoint 10: Extreme Volatility")
                continue
                
            # --- APPROVED BYPASSED SIGNAL ---
            direction = recommendation.get('action') # 'CALL' or 'PUT'
            entry_price = float(synced['M5']['close'].iloc[-1])
            
            # Settle trade based on next M5 candle close
            try:
                current_idx = m5_df.index.get_loc(current_tick)
                next_candle = m5_df.iloc[current_idx + 1]
                exit_price = float(next_candle['close'])
                
                # Determine win or loss
                close_change = exit_price - entry_price
                if direction == 'CALL':
                    won = close_change > 0
                else: # PUT
                    won = close_change < 0
                    
                pnl = win_payout if won else -stake
                balance += pnl
                
                trade_info = {
                    'local_time': local_tick.strftime('%Y-%m-%d %H:%M:%S'),
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'result': 'WIN 🟢' if won else 'LOSS 🔴',
                    'pnl': pnl,
                    'balance': balance,
                }
                trades.append(trade_info)
                
                print(f"✅ [{trade_info['local_time']}] {direction:<4} | Entry: {entry_price:.5f} -> Exit: {exit_price:.5f} | {trade_info['result']} | PnL: {pnl:+.2f} THB | Balance: {balance:.2f} THB")
                
                # If balance goes bankrupt, stop backtesting
                if balance < stake:
                    print("🚨 Bankrupt! Balance fell below minimum stake size. Stopping simulation.")
                    break
                    
            except IndexError:
                pass
                
        except Exception as ex:
            import traceback
            print(f"❌ Exception at {current_tick} (Local: {local_tick}): {ex}")
            traceback.print_exc()
            break

    # --- PRINT FINAL REPORT ---
    print("\n" + "="*80)
    print("📊 BACKTEST SIMULATION RESULTS SUMMARY (SELECTIVE CHECKPOINTS: 5 & 10 ONLY)")
    print("="*80)
    print(f"Total Trades Executed : {len(trades)}")
    
    if not trades:
        print("No trades were placed during this period.")
        print("="*80)
        return
        
    wins = [t for t in trades if 'WIN' in t['result']]
    losses = [t for t in trades if 'LOSS' in t['result']]
    win_rate = (len(wins) / len(trades)) * 100
    total_pnl = balance - initial_balance
    
    print(f"Wins                  : {len(wins)} 🟢")
    print(f"Losses                : {len(losses)} 🔴")
    print(f"Win Rate              : {win_rate:.1f}%")
    print(f"Starting Capital      : {initial_balance:.2f} THB")
    print(f"Ending Balance        : {balance:.2f} THB")
    print(f"Net Profit / Loss     : {total_pnl:+.2f} THB ({ (total_pnl / initial_balance) * 100:+.1f}%)")
    
    # Calculate max consecutive losses
    streak = 0
    max_streak = 0
    for t in trades:
        if 'LOSS' in t['result']:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    print(f"Max Consecutive Loss  : {max_streak} losses in a row")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_simulation()
