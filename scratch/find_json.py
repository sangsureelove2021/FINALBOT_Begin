import os
import glob

base_dir = r"C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT"
pattern = os.path.join(base_dir, "**", "*.json")
json_files = glob.glob(pattern, recursive=True)

print("Found JSON files:")
for f in json_files:
    print(f)
