import os
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

brain_dir = Path(r"C:\Users\Administrator\.gemini\antigravity\brain")
if not brain_dir.exists():
    print("Brain directory does not exist.")
    sys.exit(0)

keywords = ["นักฆ่า", "ก่อการร้าย", "ฆ่า", "หัวหน้า", "killer", "terrorist", "assassin"]

found = []
for folder in brain_dir.iterdir():
    if folder.is_dir():
        log_file = folder / ".system_generated" / "logs" / "transcript.jsonl"
        if log_file.exists():
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    for idx, line in enumerate(f):
                        try:
                            data = json.loads(line)
                            content = data.get("content", "")
                            if any(kw in content or kw in content.lower() for kw in keywords):
                                found.append((folder.name, idx, data.get("source"), content))
                        except Exception:
                            pass
                        except Exception as e:
                print(f"Error reading {log_file}: {e}")

print(f"Total global matches: {len(found)}")
for folder_name, idx, source, content in found:
    print(f"[{folder_name}] Step {idx} ({source}): {content[:400]}")
    print("="*60)
