import re

path = "runner.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the start_dt block
content = re.sub(
    r'(start_dt = pd\.to_datetime\(start_date_str\))\s+# Strip timezone to make naive UTC\s+if start_dt\.tzinfo is not None:\s+start_dt = start_dt\.tz_localize\(None\)',
    r'\1\n                # Make timezone-aware UTC\n                if start_dt.tzinfo is None:\n                    start_dt = start_dt.tz_localize("UTC")\n                else:\n                    start_dt = start_dt.tz_convert("UTC")',
    content,
    flags=re.DOTALL
)

# Replace the end_dt block
content = re.sub(
    r'(end_dt = pd\.to_datetime\(end_date_str\))\s+# Strip timezone to make naive UTC\s+if end_dt\.tzinfo is not None:\s+end_dt = end_dt\.tz_localize\(None\)',
    r'\1\n                # Make timezone-aware UTC\n                if end_dt.tzinfo is None:\n                    end_dt = end_dt.tz_localize("UTC")\n                else:\n                    end_dt = end_dt.tz_convert("UTC")',
    content,
    flags=re.DOTALL
)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed timezone handling in runner.py")
