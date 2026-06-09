import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

log_path = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\b404dbf9-3da4-487c-b16b-f013f9f80451\.system_generated\logs\transcript.jsonl")

if not log_path.exists():
    print("Log file does not exist.")
    sys.exit(0)

keywords = ["นักฆ่า", "ก่อการร้าย", "ฆ่า", "หัวหน้า", "killer", "terrorist", "assassin"]

found = []
with open(log_path, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        try:
            data = json.loads(line)
            content = data.get("content", "")
            if any(kw in content or kw in content.lower() for kw in keywords):
                found.append((idx, data.get("source"), content))
        except Exception:
            pass

print(f"Found {len(found)} matches in transcript:")
for idx, source, content in found[-5:]:
    print(f"Step {idx} ({source}): {content[:300]}...")
