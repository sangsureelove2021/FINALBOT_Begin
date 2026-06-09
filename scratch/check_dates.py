import os
import glob
import pandas as pd

folder = r"C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\historical_data"
files = glob.glob(os.path.join(folder, "history_EURUSD*.csv"))

print(f"{'Filename':<35} | {'Start Time':<20} | {'End Time':<20} | {'Rows'}")
print("-" * 90)

for f in sorted(files):
    name = os.path.basename(f)
    try:
        df = pd.read_csv(f)
        start = str(df['timestamp'].iloc[0]) if 'timestamp' in df.columns else 'N/A'
        end = str(df['timestamp'].iloc[-1]) if 'timestamp' in df.columns else 'N/A'
        count = len(df)
        print(f"{name:<35} | {start:<20} | {end:<20} | {count}")
    except Exception as e:
        print(f"{name:<35} | ERROR: {str(e)}")
