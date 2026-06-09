import json
from pathlib import Path

results_dir = Path("logs/batch_backtest_results")
strategy_stats = {}

for file in sorted(results_dir.glob("week_*_results.json")):
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        trades = data.get("trades", [])
        for t in trades:
            strat = t.get("strategy")
            won = t.get("won")
            pnl = t.get("pnl")
            
            if strat not in strategy_stats:
                strategy_stats[strat] = {'trades': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0}
                
            stats = strategy_stats[strat]
            stats['trades'] += 1
            if won:
                stats['wins'] += 1
            else:
                stats['losses'] += 1
            stats['pnl'] += pnl
    except Exception as e:
        pass

print("STRATEGY PERFORMANCE BREAKDOWN:")
for s, stats in sorted(strategy_stats.items(), key=lambda x: x[1]['pnl'], reverse=True):
    wr = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0.0
    print(f"| {s:<26} | {stats['trades']:<5} | {stats['wins']:<4} | {stats['losses']:<4} | {wr:.2f}% | {stats['pnl']:+.2f} THB |")
