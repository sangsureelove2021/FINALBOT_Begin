import pandas as pd
import numpy as np

# Load M5 history
df = pd.read_csv("historical_data/history_EURUSD_OTC_M5.csv")

# Standardize timestamps
time_col = 'from' if 'from' in df.columns else 'timestamp' if 'timestamp' in df.columns else 'time'
df['datetime_parsed'] = pd.to_datetime(df[time_col], unit='s' if time_col == 'from' else None, utc=True)
df.set_index('datetime_parsed', inplace=True)
df.sort_index(inplace=True)

# Calculate indicators
close_m5 = df['close']
high_m5 = df['high']
low_m5 = df['low']

local_support_3c = low_m5.shift(3).rolling(window=10).min()
local_resistance_3c = high_m5.shift(3).rolling(window=10).max()

min_low_3c = low_m5.rolling(window=3).min()
max_high_3c = high_m5.rolling(window=3).max()

touched_support_3c = min_low_3c <= local_support_3c * 1.001
touched_resistance_3c = max_high_3c >= local_resistance_3c * 0.999

print(f"Total rows: {len(df)}")
print(f"touched_support_3c True count: {touched_support_3c.sum()} ({touched_support_3c.sum()/len(df)*100:.2f}%)")
print(f"touched_resistance_3c True count: {touched_resistance_3c.sum()} ({touched_resistance_3c.sum()/len(df)*100:.2f}%)")

# Let's check with smaller buffers:
for b in [1.0005, 1.0002, 1.0001, 1.0]:
    ts = min_low_3c <= local_support_3c * b
    tr = max_high_3c >= local_resistance_3c * (2.0 - b)
    print(f"Buffer {b}: Support True={ts.sum()} ({ts.sum()/len(df)*100:.2f}%), Resistance True={tr.sum()} ({tr.sum()/len(df)*100:.2f}%)")
