import os
import glob

search_terms = ["EURUSD, EURUSD-OTC", "บิน", "ออก"]
for root, dirs, files in os.walk("."):
    if ".venv" in root or ".git" in root or ".pytest_cache" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for term in search_terms:
                        if term in content:
                            print(f"Found '{term}' in {path}")
            except Exception as e:
                pass
