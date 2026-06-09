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

# Import necessary engines
from core.engines.trend_engine import TrendEngine
from core.engines.strength_engine import StrengthEngine
from core.engines.volatility_engine import VolatilityEngine
from core.engines.structure_engine import StructureEngine
from core.engines.mtf_engine import MTFEngine
from core.engines.market_state_classifier import MarketStateClassifier
from core.engines.trap_detector import TrapDetector

from strategy.compression_breakout.strategy import CompressionBreakoutStrategy

def analyze():
    data_adapter = CSVDataAdapter(data_dir="e:/BOT_FINALBOT/historical_data")
    timeframes = ['M1', 'M5', 'M15', 'M60']
    symbol = "EURUSD"
    data_adapter.load_symbol_data(symbol, timeframes)

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
    
    start_time = datetime(2026, 4, 27, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2026, 5, 27, 23, 15, tzinfo=timezone.utc)
    
    m5_df = data_adapter.dfs[symbol]['M5']
    timeline = m5_df.loc[start_time:end_time].index
    
    # Financial parameters
    initial_balance = 2000.0
    balance = initial_balance
    stake = 35.0
    payout_multiplier = 0.85
    win_payout = stake * payout_multiplier
    
    trades_in_window = []
    total_trades = []
    
    print("Running timeline analysis...")
    
    for current_tick in timeline:
        local_tick = current_tick + timedelta(hours=7)
        data_adapter.set_simulated_time(current_tick)
        
        try:
            candles_dict = data_adapter.get_multi_timeframe(symbol, timeframes, count=300)
            from core.data.timeframe_sync import TimeframeSync
            synced = TimeframeSync(primary='M5').sync(candles_dict)
            
            context = context_builder.build(symbol, synced, 'M5')
            recommendation = strategy.evaluate(context)
            
            if recommendation.get('action') == 'NO_SIGNAL':
                continue
                
            # ด่าน 5 & 10
            if context.traps.get('trap_detected'):
                continue
            regime = context.volatility.get('regime', 'NORMAL')
            if regime == 'EXTREME':
                continue
                
            direction = recommendation.get('action')
            entry_price = float(synced['M5']['close'].iloc[-1])
            
            try:
                current_idx = m5_df.index.get_loc(current_tick)
                next_candle = m5_df.iloc[current_idx + 1]
                exit_price = float(next_candle['close'])
                
                close_change = exit_price - entry_price
                if direction == 'CALL':
                    won = close_change > 0
                else:
                    won = close_change < 0
                    
                pnl = win_payout if won else -stake
                balance += pnl
                
                trade_info = {
                    'local_time': local_tick,
                    'direction': direction,
                    'result': 'WIN' if won else 'LOSS',
                    'pnl': pnl,
                }
                
                total_trades.append(trade_info)
                
                # Check if local time falls into 01:00 - 12:00
                hour = local_tick.hour
                if 1 <= hour < 12:
                    trades_in_window.append(trade_info)
                    
                if balance < stake:
                    break
            except IndexError:
                pass
        except Exception as e:
            pass

    # Print summary for 01:00 - 12:00
    print("\n" + "="*50)
    print("ANALYSIS REPORT FOR WINDOW 01:00 - 12:00")
    print("="*50)
    print(f"Total Trades in this window: {len(trades_in_window)}")
    
    if trades_in_window:
        wins = [t for t in trades_in_window if t['result'] == 'WIN']
        losses = [t for t in trades_in_window if t['result'] == 'LOSS']
        win_rate = (len(wins) / len(trades_in_window)) * 100
        total_pnl = sum(t['pnl'] for t in trades_in_window)
        
        print(f"Wins  : {len(wins)}")
        print(f"Losses: {len(losses)}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Net PnL in this window: {total_pnl:+.2f} THB")
    else:
        print("No trades occurred in this window.")
        
    # Also print overall stats for context
    print("\n" + "="*50)
    print("OVERALL BACKTEST STATISTICS")
    print("="*50)
    print(f"Total Trades Executed: {len(total_trades)}")
    print(f"Total Wins  : {len([t for t in total_trades if t['result'] == 'WIN'])}")
    print(f"Total Losses: {len([t for t in total_trades if t['result'] == 'LOSS'])}")
    print(f"Ending Balance: {balance:.2f} THB")
    print("="*50)

if __name__ == '__main__':
    analyze()
