import json
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/Administrator/Downloads/BOT_FINALBOT/BOT_FINALBOT")
signals_path = PROJECT_ROOT / "logs" / "backtest_signals.json"

if not signals_path.exists():
    print("ERROR: logs/backtest_signals.json not found.")
    exit(1)

with open(signals_path, "rb") as f:
    raw_data = f.read()

# Let's fix the truncated JSON by finding the last fully closed object '}'
# We scan backwards to find the last '}'
fixed_data = None
for idx in range(len(raw_data) - 1, -1, -1):
    if raw_data[idx] == ord('}'):
        # Found last fully closed object. Let's slice up to here
        fixed_data = raw_data[:idx+1]
        break

if fixed_data is None:
    print("ERROR: Could not find any closed curly bracket in JSON.")
    exit(1)

# Now, we need to append the closing bracket ']' to make it a valid JSON array
try:
    decoded = fixed_data.decode("utf-8")
    # Strip any trailing comma or spaces before appending ']'
    decoded = decoded.strip()
    if decoded.endswith(","):
        decoded = decoded[:-1]
    decoded += "\n]"
    
    # Try parsing it!
    entries = json.loads(decoded)
    print(f"SUCCESS: Successfully parsed {len(entries)} valid entries from the repaired JSON!")
    
    # Save the repaired JSON back so it's clean
    with open(signals_path, "w", encoding="utf-8") as f_out:
        json.dump(entries, f_out, indent=2, ensure_ascii=False)
    print("Cleaned logs/backtest_signals.json saved successfully.")
    
    # 2. Extract and analyze compression_breakout entries
    comp_losses = []
    for entry in entries:
        if entry.get("strategy") == "compression_breakout":
            outcome = entry.get("trade_outcome")
            # In offline_backtest, if won is False, it's a loss
            if outcome and outcome.get("won") is False:
                comp_losses.append(entry)
                
    print(f"\nTOTAL COMPRESSION_BREAKOUT LOSSES IN JSON: {len(comp_losses)}")
    print("="*60)
    
    if not comp_losses:
        print("No compression_breakout losses with outcomes found in JSON.")
        # Print states of all compression_breakout entries in the JSON as an alternative
        states = {}
        for entry in entries:
            if entry.get("strategy") == "compression_breakout":
                st = entry.get("state", "UNKNOWN")
                states[st] = states.get(st, 0) + 1
        print("Recorded states for all compression_breakout entries in JSON:")
        for st, c in states.items():
            print(f"- {st}: {c} times")
    else:
        # Summarize the recorded states
        states = {}
        for entry in comp_losses:
            st = entry.get("state", "UNKNOWN")
            states[st] = states.get(st, 0) + 1
            
        print("RECORDED 'state' IN JSON FOR COMPRESSION_BREAKOUT LOSSES:")
        for st, c in sorted(states.items(), key=lambda x: x[1], reverse=True):
            pct = c / len(comp_losses) * 100
            print(f"- {st:<30}: {c:<4} times ({pct:.2f}%)")
            
except Exception as e:
    print(f"ERROR repairing JSON: {e}")
