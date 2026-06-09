import json

json_path = r"C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\data trade.json"
proposed_path = r"C:\Users\Administrator\.gemini\antigravity\brain\bf808087-316a-4062-af9c-a51da648c8ed\scratch\proposed_arbitration.txt"

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Read proposed decisions
decisions = {}
import re
with open(proposed_path, "r", encoding="utf-8") as f:
    content = f.read()

blocks = content.split("-" * 50)
for block in blocks:
    idx_match = re.search(r"Index:\s*(\d+)", block)
    if idx_match:
        idx = int(idx_match.group(1))
        prop_match = re.search(r"Proposed:\s*(\w+)", block)
        if prop_match:
            decisions[idx] = prop_match.group(1)

# Apply decisions
modified_count = 0
for idx in range(len(data)):
    if idx in decisions:
        orig = data[idx]["direction"]
        new_val = decisions[idx]
        if orig != new_val:
            data[idx]["direction"] = new_val
            modified_count += 1

# Overwrite JSON file
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Successfully applied changes! Modified {modified_count} entries.")
