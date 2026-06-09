import json

file_path = r"C:\Users\Administrator\Downloads\TEST\backtest_with_outcomes.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Count outcomes by won status and strategy
stats = {}
for entry in data:
    strat = entry.get("strategy")
    outcome = entry.get("trade_outcome", {})
    won = outcome.get("won", False)
    pnl = outcome.get("pnl", 0.0)
    
    if strat not in stats:
        stats[strat] = {"wins": 0, "losses": 0, "pnl": 0.0}
        
    if won:
        stats[strat]["wins"] += 1
    else:
        stats[strat]["losses"] += 1
    stats[strat]["pnl"] += pnl

print("--- STATS BY STRATEGY ---")
total_wins = 0
total_losses = 0
total_pnl = 0.0
for strat, s in stats.items():
    wins = s["wins"]
    losses = s["losses"]
    tot = wins + losses
    win_rate = (wins / tot * 100) if tot > 0 else 0
    pnl = s["pnl"]
    total_wins += wins
    total_losses += losses
    total_pnl += pnl
    print(f"{strat}:")
    print(f"  - Total Trades: {tot}")
    print(f"  - Wins: {wins} | Losses: {losses}")
    print(f"  - Win Rate: {win_rate:.2f}%")
    print(f"  - PnL: ${pnl:.2f}")

print("\n--- OVERALL BOT PERFORMANCE ---")
grand_total = total_wins + total_losses
overall_wr = (total_wins / grand_total * 100) if grand_total > 0 else 0
print(f"Grand Total Trades: {grand_total}")
print(f"Total Wins: {total_wins} | Total Losses: {total_losses}")
print(f"Overall Win Rate: {overall_wr:.2f}%")
print(f"Total PnL: ${total_pnl:.2f}")
