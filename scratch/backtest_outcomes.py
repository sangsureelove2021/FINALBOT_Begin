import json

json_path = r"C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\ดเ่.json"

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

total_trades = 0
bot_wins = 0
bot_losses = 0
bot_pnl = 0.0

athena_trades = 0
athena_wins = 0
athena_losses = 0
athena_pnl = 0.0

skipped_trades = 0
skipped_wins = 0
skipped_losses = 0
skipped_pnl = 0.0

for idx, entry in enumerate(data):
    outcome = entry.get("trade_outcome")
    if not outcome:
        continue
        
    total_trades += 1
    won = outcome.get("won", False)
    pnl = outcome.get("pnl", 0.0)
    
    # 1. Original Bot Performance
    if won:
        bot_wins += 1
    else:
        bot_losses += 1
    bot_pnl += pnl
    
    # 2. Athena AI V2 Performance
    direction = entry.get("direction") # Already contains our V2 arbitrated direction (CALL/PUT/NOTRADE)
    
    if direction == "NOTRADE":
        skipped_trades += 1
        if won:
            skipped_wins += 1
        else:
            skipped_losses += 1
        skipped_pnl += pnl
    else:
        athena_trades += 1
        if won:
            athena_wins += 1
        else:
            athena_losses += 1
        athena_pnl += pnl

print("--- BACKTEST RESULTS ---")
print(f"Total Signals in File with Outcomes: {total_trades}")
print(f"Original Bot:")
print(f"  - Trades Taken: {total_trades}")
print(f"  - Wins: {bot_wins} | Losses: {bot_losses}")
print(f"  - Win Rate: {bot_wins / total_trades * 100:.2f}%")
print(f"  - Total PnL: ${bot_pnl:.2f}")
print(f"Athena AI (V2 Filtered):")
print(f"  - Trades Taken: {athena_trades}")
print(f"  - Wins: {athena_wins} | Losses: {athena_losses}")
print(f"  - Win Rate: {athena_wins / athena_trades * 100:.2f}%" if athena_trades > 0 else "  - Win Rate: N/A")
print(f"  - Total PnL: ${athena_pnl:.2f}")
print(f"Filtered Out (NOTRADE):")
print(f"  - Saved Trades (Avoided): {skipped_trades}")
print(f"  - Avoided Losses: {skipped_losses} | Missed Wins: {skipped_wins}")
print(f"  - Avoided PnL Impact: ${skipped_pnl:.2f}")
