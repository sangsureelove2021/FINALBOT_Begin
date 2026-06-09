import os
import json

test_dir = r"C:\Users\Administrator\Downloads\TEST"
files = ["backtest_with_outcomes.json", "backtest_without_outcomes.json", "backtest_signals.json", "ai trade.json", "data trade.json"]

for f_name in files:
    f_path = os.path.join(test_dir, f_name)
    if not os.path.exists(f_path):
        continue
    try:
        with open(f_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            symbols = set(entry.get("symbol") for entry in data if entry.get("symbol"))
            print(f"{f_name}: Unique Symbols: {list(symbols)} | Total entries: {len(data)}")
        else:
            print(f"{f_name}: Dict keys: {list(data.keys())}")
    except Exception as e:
        print(f"Error reading {f_name}: {e}")
