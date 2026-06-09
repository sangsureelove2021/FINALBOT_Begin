import json
from pathlib import Path

results_dir = Path("logs/batch_backtest_results")
strategy_counts = {}
total_trades = 0

for file in results_dir.glob("*.json"):
    if file.name == "summary.json":
        continue
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            for t in data.get("trades", []):
                strat = t.get("strategy")
                strategy_counts[strat] = strategy_counts.get(strat, 0) + 1
                total_trades += 1
    except Exception as e:
        pass

print(f"Total Trades in JSON: {total_trades}")
for s, count in sorted(strategy_counts.items(), key=lambda x: x[1], reverse=True):
    print(f" - {s}: {count} ({count/total_trades*100:.2f}%)")
