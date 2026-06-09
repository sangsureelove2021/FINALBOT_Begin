import os
import sys
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
sys.path.append(os.path.abspath("e:/BOT_FINALBOT"))

from core.data.csv_data_adapter import CSVDataAdapter

def check():
    data_adapter = CSVDataAdapter(data_dir="e:/BOT_FINALBOT/historical_data")
    symbol = "EURUSD"
    data_adapter.load_symbol_data(symbol, ['M5'])
    df = data_adapter.dfs[symbol]['M5']
    
    print(f"Total M5 candles: {len(df)}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    
    # Calculate EMAs
    df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    df['ema100'] = df['close'].ewm(span=100, adjust=False).mean()
    
    # Calculate direction
    def get_dir(row):
        price = row['close']
        ema20 = row['ema20']
        ema50 = row['ema50']
        ema100 = row['ema100']
        if price > ema20 > ema50 > ema100:
            return 'UP'
        elif price < ema20 < ema50 < ema100:
            return 'DOWN'
        return 'NONE'
        
    df['direction'] = df.apply(get_dir, axis=1)
    
    dir_counts = df['direction'].value_counts()
    print("\nDirection Distribution (Full Dataset):")
    print(dir_counts)
    
    # Squeeze / Volatility Percentile calculation check
    high_low = df['high'] - df['low']
    df['tr'] = np.maximum(high_low, np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
    df['atr'] = df['tr'].rolling(14).mean()
    
    # Let's see how many times direction is not NONE when we are in the trading hours (17:00 - 23:00 Bangkok time)
    # Bangkok is UTC+7, so 17:00-23:00 Bangkok is 10:00-16:00 UTC.
    df['hour_utc'] = df.index.hour
    df_window = df[(df['hour_utc'] >= 10) & (df['hour_utc'] < 16)]
    
    print(f"\nTrading window candles: {len(df_window)}")
    print("Direction Distribution (Trading Window):")
    print(df_window['direction'].value_counts())

if __name__ == '__main__':
    check()
