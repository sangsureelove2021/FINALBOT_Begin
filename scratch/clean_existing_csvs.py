import os
import glob
import pandas as pd

def clean_csv_file(filepath):
    try:
        df = pd.read_csv(filepath)
        if df.empty or 'timestamp' not in df.columns:
            return
        
        # Keep only standard columns
        cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        df = df[[c for c in cols if c in df.columns]]
        
        # Deduplicate based on timestamp, keep last
        df = df[~df['timestamp'].duplicated(keep='last')]
        
        # Sort by timestamp
        df['ts'] = pd.to_datetime(df['timestamp'])
        df.sort_values('ts', inplace=True)
        df.drop(columns=['ts'], inplace=True)
        
        # Write back clean file
        df.to_csv(filepath, index=False)
        print(f"Cleaned {filepath}: {len(df)} unique rows remaining.")
    except Exception as e:
        print(f"Failed to clean {filepath}: {e}")

def main():
    pattern = "data_base/csv/iq_option/**/*.csv"
    files = glob.glob(pattern, recursive=True)
    for f in files:
        if "anomaly_logs" in f:
            continue
        clean_csv_file(f)

if __name__ == "__main__":
    main()
