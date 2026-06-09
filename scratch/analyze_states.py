import os
import sys
from datetime import datetime, timezone, timedelta
import pandas as pd

# Ensure project root is in sys.path
sys.path.append(os.path.abspath("e:/BOT_FINALBOT"))

from core.data.csv_data_adapter import CSVDataAdapter
from core.orchestration.context_builder import ContextBuilder
from core.engines.engine_setup import setup_engines

def analyze_states():
    data_adapter = CSVDataAdapter(data_dir="e:/BOT_FINALBOT/historical_data")
    timeframes = ['M1', 'M5', 'M15', 'M60']
    symbol = "EURUSD"
    data_adapter.load_symbol_data(symbol, timeframes)
    
    engine_registry = setup_engines()
    context_builder = ContextBuilder(engine_registry)
    
    start_time = datetime(2026, 4, 27, 0, 0, tzinfo=timezone.utc)
    end_time = datetime(2026, 5, 27, 23, 15, tzinfo=timezone.utc)
    
    m5_df = data_adapter.dfs[symbol]['M5']
    timeline = m5_df.loc[start_time:end_time].index
    
    state_counts = {}
    total_cycles = 0
    
    print("Analyzing states over timeline window...")
    
    for current_tick in timeline:
        local_tick = current_tick + timedelta(hours=7)
        
        # Only in trading window
        if not (17 <= local_tick.hour < 23):
            continue
            
        data_adapter.set_simulated_time(current_tick)
        
        try:
            candles_dict = data_adapter.get_multi_timeframe(symbol, timeframes, count=300)
            from core.data.timeframe_sync import TimeframeSync
            synced = TimeframeSync(primary='M5').sync(candles_dict)
            context = context_builder.build(symbol, synced, 'M5')
            
            state_str = context.market_state.get('state', 'UNKNOWN') if isinstance(context.market_state, dict) else context.market_state
            state_counts[state_str] = state_counts.get(state_str, 0) + 1
            total_cycles += 1
            
        except Exception as e:
            pass
            
    print(f"\nTotal cycles evaluated: {total_cycles}")
    print("Market State Distribution:")
    for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True):
        print(f" - {state}: {count} ({count/total_cycles*100:.1f}%)")

if __name__ == '__main__':
    analyze_states()
