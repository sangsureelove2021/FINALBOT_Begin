import json
from pathlib import Path

filepath = Path("C:/Users/Administrator/Downloads/BOT_FINALBOT/BOT_FINALBOT/tests/BackTest/EURUSD/backtest_with_outcomes.json")

if not filepath.exists():
    print(f"File not found: {filepath}")
    exit(1)

with open(filepath, "r", encoding="utf-8") as f:
    trades = json.load(f)

print(f"Total Trades: {len(trades)}")

stats = {}
for t in trades:
    sym = t['symbol']
    strat = t['strategy']
    outcome = t.get('trade_outcome', {})
    if not outcome:
        continue
    won = outcome.get('won', False)
    pnl = outcome.get('pnl', 0.0)
    
    # Init symbol
    if sym not in stats:
        stats[sym] = {"total": 0, "wins": 0, "losses": 0, "pnl": 0.0, "strategies": {}}
        
    stats[sym]["total"] += 1
    if won:
        stats[sym]["wins"] += 1
    else:
        stats[sym]["losses"] += 1
    stats[sym]["pnl"] += pnl
    
    # Strategy stats
    if strat not in stats[sym]["strategies"]:
        stats[sym]["strategies"][strat] = {"total": 0, "wins": 0, "losses": 0, "pnl": 0.0}
    stats[sym]["strategies"][strat]["total"] += 1
    if won:
        stats[sym]["strategies"][strat]["wins"] += 1
    else:
        stats[sym]["strategies"][strat]["losses"] += 1
    stats[sym]["strategies"][strat]["pnl"] += pnl

# Total overall
overall = {"total": 0, "wins": 0, "losses": 0, "pnl": 0.0}

print("\n================ THURSDAY BACKTEST SUMMARY ================")
for sym, data in stats.items():
    wr = (data["wins"] / data["total"] * 100) if data["total"] > 0 else 0.0
    print(f"\nSymbol: {sym}")
    print(f"  - Total Trades: {data['total']}")
    print(f"  - Wins: {data['wins']} | Losses: {data['losses']}")
    print(f"  - Win Rate: {wr:.2f}%")
    print(f"  - Net PnL: {data['pnl']:.2f} USD")
    
    overall["total"] += data["total"]
    overall["wins"] += data["wins"]
    overall["losses"] += data["losses"]
    overall["pnl"] += data["pnl"]
    
    print("  - Per-Strategy Breakdown:")
    for strat, sdata in data["strategies"].items():
        swr = (sdata["wins"] / sdata["total"] * 100) if sdata["total"] > 0 else 0.0
        print(f"    * {strat}: {sdata['total']} trades, Wins: {sdata['wins']}, Win Rate: {swr:.2f}%, PnL: {sdata['pnl']:.2f} USD")

overall_wr = (overall["wins"] / overall["total"] * 100) if overall["total"] > 0 else 0.0
print("\n================ OVERALL SUMMARY ================")
print(f"Total Trades: {overall['total']}")
print(f"Total Wins: {overall['wins']} | Total Losses: {overall['losses']}")
print(f"Overall Win Rate: {overall_wr:.2f}%")
print(f"Overall Net PnL: {overall['pnl']:.2f} USD")
