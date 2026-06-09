import os
import glob

test_dir = r"C:\Users\Administrator\Downloads\TEST"
json_files = glob.glob(os.path.join(test_dir, "*.*"))

for f_path in json_files:
    if os.path.isdir(f_path):
        continue
    try:
        with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        count = content.lower().count("usd-otc")
        if count > 0:
            print(f"{os.path.basename(f_path)}: Found {count} occurrences of 'usd-otc'")
    except Exception as e:
        pass
