import json
import os
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/Administrator/Downloads/BOT_FINALBOT/BOT_FINALBOT")
signals_path = PROJECT_ROOT / "logs" / "backtest_signals.json"

if not signals_path.exists():
    print(f"ERROR: {signals_path} does not exist.")
    exit(1)

with open(signals_path, "r", encoding="utf-8") as f:
    try:
        data = json.load(f)
    except Exception as e:
        print(f"ERROR reading JSON: {e}")
        exit(1)

# Extract only compression_breakout losses
comp_losses = []
for entry in data:
    if entry.get("strategy") == "compression_breakout":
        outcome = entry.get("trade_outcome")
        if outcome and outcome.get("won") is False:
            comp_losses.append(entry)

print(f"TOTAL COMPRESSION_BREAKOUT LOSSES FOUND IN JSON: {len(comp_losses)}")
print("="*60)

if not comp_losses:
    print("No compression_breakout losses found in JSON. Let's list all compression_breakout entries in JSON to see if trade_outcome is missing.")
    count_comp = sum(1 for x in data if x.get("strategy") == "compression_breakout")
    print(f"Total compression_breakout entries in JSON (with or without outcome): {count_comp}")
    
    # Just list states of all compression_breakout entries as an alternative
    states = {}
    for entry in data:
        if entry.get("strategy") == "compression_breakout":
            st = entry.get("state", "UNKNOWN")
            states[st] = states.get(st, 0) + 1
    print("\nRecorded states for all compression_breakout entries:")
    for st, c in states.items():
        print(f"- {st}: {c} times")
else:
    # We found exact losses! Let's summarize the state
    states = {}
    for entry in comp_losses:
        st = entry.get("state", "UNKNOWN")
        states[st] = states.get(st, 0) + 1
        
    print("RECORDED MARKET STATES FOR LOSSES (trade_outcome = False):")
    for st, c in sorted(states.items(), key=lambda x: x[1], reverse=True):
        pct = c / len(comp_losses) * 100
        print(f"- {st:<30}: {c:<4} times ({pct:.2f}%)")
