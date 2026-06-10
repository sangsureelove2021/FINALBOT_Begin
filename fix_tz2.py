with open('runner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix lines 1397-1399 (0-indexed)
# We'll search for the pattern
for i in range(len(lines)):
    if 'start_dt = pd.to_datetime(start_date_str)' in lines[i]:
        # replace the next lines
        lines[i+1] = '                # Make timezone-aware UTC\n'
        lines[i+2] = '                if start_dt.tzinfo is None:\n'
        lines[i+3] = '                    start_dt = start_dt.tz_localize("UTC")\n'
        lines[i+4] = '                else:\n'
        lines[i+5] = '                    start_dt = start_dt.tz_convert("UTC")\n'
        # skip the old lines
        break

for i in range(len(lines)):
    if 'end_dt = pd.to_datetime(end_date_str)' in lines[i]:
        lines[i+1] = '                # Make timezone-aware UTC\n'
        lines[i+2] = '                if end_dt.tzinfo is None:\n'
        lines[i+3] = '                    end_dt = end_dt.tz_localize("UTC")\n'
        lines[i+4] = '                else:\n'
        lines[i+5] = '                    end_dt = end_dt.tz_convert("UTC")\n'
        break

with open('runner.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed")
