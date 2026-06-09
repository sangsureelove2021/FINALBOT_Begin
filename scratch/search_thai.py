import os
import re

# Search for any python file containing print or logging with active symbols/pairs or Thai text
for root, dirs, files in os.walk("."):
    if any(x in root for x in [".venv", ".git", ".pytest_cache"]):
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                for idx, line in enumerate(lines):
                    # Check for Thai characters
                    if re.search(r'[\u0e00-\u0e7f]', line):
                        print(f"Thai in {path}:{idx+1}: {line.strip()}")
            except Exception as e:
                pass
