import os
import sys
import time
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.data.iq_option_adapter import IQOptionAdapter

OUTPUT_DIR = Path("historical_data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

symbol = "EURUSD-OTC"
timeframes = ['M1', 'M5', 'M15', 'M60']
days = 5

def fetch_history(adapter, symbol, tf, target_count):
    size = adapter._TF_SECONDS.get(tf, 60)
    all_candles = []
    end_time = time.time()
    
    print(f"Downloading {target_count} candles for {symbol} ({tf})...")
    
    while len(all_candles) < target_count:
        batch_size = min(1000, target_count - len(all_candles))
        try:
            raw = adapter.api.get_candles(symbol, size, batch_size, end_time)
            if not raw or not isinstance(raw, list):
                break
            all_candles.extend(raw)
            oldest_timestamp = int(raw[0]["from"])
            end_time = oldest_timestamp - 1
            print(f"   -> Retrieved {len(all_candles)} / {target_count}")
            time.sleep(0.5)
        except Exception as e:
            print(f"   [ERROR] {e}")
            break
            
    if not all_candles:
        return pd.DataFrame()
        
    df = pd.DataFrame(all_candles)
    df = df.drop_duplicates(subset=['from'])
    df = df.rename(columns={"max": "high", "min": "low"})
    df["timestamp"] = pd.to_datetime(df["from"], unit="s")
    for col in ("open", "close", "high", "low"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["volume"] = pd.to_numeric(df.get("volume", 0), errors="coerce").fillna(0.0)
    df = df.dropna(subset=["open", "close", "high", "low"])
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    df = df.sort_values(by="timestamp").reset_index(drop=True)
    return df

def main():
    try:
        from core.config_loader import get_account_type
        account_type = get_account_type()
        adapter = IQOptionAdapter(account_type=account_type)
        if not adapter.is_connected():
            print("Failed to connect")
            return
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    for tf in timeframes:
        minutes = {'M1': 1, 'M5': 5, 'M15': 15, 'M60': 60}.get(tf, 1)
        target = int((days * 1440) / minutes)
        
        df = fetch_history(adapter, symbol, tf, target)
        if not df.empty:
            file_name = f"history_EURUSD_OTC_{tf}.csv"
            file_path = OUTPUT_DIR / file_name
            df.to_csv(file_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
            print(f"Saved {len(df)} candles to {file_path}")
            print(f"Data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        else:
            print(f"Failed to fetch {tf}")
            
if __name__ == "__main__":
    main()
