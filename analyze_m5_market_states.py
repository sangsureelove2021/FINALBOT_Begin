import pandas as pd
import numpy as np
from datetime import datetime
from core.engines.market_state_classifier import MarketStateClassifier

def analyze_market_states():
    # Load CSV data
    df = pd.read_csv('backtest/data test/history_EURUSD_M5.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
    df.set_index('timestamp', inplace=True)
    
    # Filter for May 8, 2026
    df = df.loc['2026-05-08 00:00':'2026-05-08 23:59']
    
    if len(df) == 0:
        print("No data found for 2026-05-08 in EURUSD_M5.csv")
        return
        
    print(f"Total candles found for 2026-05-08: {len(df)}")
    
    # Initialize Classifier
    classifier = MarketStateClassifier()
    
    # We need to simulate a rolling window because the classifier needs at least 100 candles.
    # To accurately simulate what the bot saw on May 8, we should ideally feed it data leading up to each point.
    # We will load the full dataset, then iterate through May 8.
    full_df = pd.read_csv('backtest/data test/history_EURUSD_M5.csv')
    full_df['timestamp'] = pd.to_datetime(full_df['timestamp'], unit='s', utc=True)
    full_df.set_index('timestamp', inplace=True)
    full_df.sort_index(inplace=True)
    
    target_times = df.index
    
    previous_state = None
    changes = []
    
    print("| Time (UTC) | Market State | Quality Score | Confidence | Description |")
    print("|---|---|---|---|---|")
    
    for t in target_times:
        # Get up to 150 candles to avoid memory/time bloat
        # Assuming index is sorted
        pos = full_df.index.get_loc(t)
        if isinstance(pos, slice):
            pos = pos.stop - 1
        elif isinstance(pos, np.ndarray):
            pos = np.where(pos)[0][-1]
        
        start_pos = max(0, pos - 150)
        window_df = full_df.iloc[start_pos:pos+1].copy()
        
        if len(window_df) < 100:
            current_state = "NOT_ENOUGH_DATA"
            quality = 0
            conf = 0
            desc = ""
        else:
            result = classifier.analyze(window_df)
            current_state = result.get('state', 'UNKNOWN')
            quality = result.get('quality_score', 0)
            conf = result.get('confidence', 0)
            desc = result.get('description', '')
            
        if current_state != previous_state:
            print(f"| {t.strftime('%H:%M')} | **{current_state}** | {quality} | {conf}% | {desc} |")
            previous_state = current_state

if __name__ == "__main__":
    analyze_market_states()
