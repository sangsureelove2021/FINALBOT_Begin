import os
import pandas as pd
from pathlib import Path

data_dir = Path(r"c:\Users\Administrator\Documents\GitHub\BOT_FINALBOT\backtest\data test")
for file in data_dir.glob("*.csv"):
    try:
        df = pd.read_csv(file)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        print(f"{file.name}: {len(df)} rows, from {df['timestamp'].min()} to {df['timestamp'].max()}")
    except Exception as e:
        print(f"Error {file.name}: {e}")
