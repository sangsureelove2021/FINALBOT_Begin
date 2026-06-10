with open('runner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the lines 1453-1460 or similar
for i in range(len(lines)):
    if 'if start_dt:' in lines[i] and 'backtest_timestamps = []' in lines[i+1] if i+1 < len(lines) else False:
        # Replace the block
        indent = '        '
        new_block = [
            '        # Convert aware datetimes to naive for comparison with CSV timestamps (which are tz-naive)\n',
            '        naive_start = start_dt.tz_localize(None) if start_dt and start_dt.tzinfo is not None else start_dt\n',
            '        naive_end = end_dt.tz_localize(None) if end_dt and end_dt.tzinfo is not None else end_dt\n',
            '        \n',
            '        if start_dt:\n',
            '            backtest_timestamps = []\n',
            '            for t in sorted_timestamps:\n',
            '                if naive_start and t < naive_start:\n',
            '                    continue\n',
            '                if naive_end and t > naive_end:\n',
            '                    continue\n',
            '                backtest_timestamps.append(t)\n',
            '        else:\n',
            '            days_to_test = 30\n',
            '            last_timestamp = sorted_timestamps[-1]\n',
            '            start_timestamp = last_timestamp - timedelta(days=days_to_test)\n',
            '            backtest_timestamps = [t for t in sorted_timestamps if t >= start_timestamp]\n',
        ]
        # Find the end of the block (the line after the else block)
        end_idx = i
        while end_idx < len(lines) and 'backtest_timestamps = [t for t in sorted_timestamps if t >= start_timestamp]' not in lines[end_idx]:
            end_idx += 1
        end_idx += 1  # include that line
        lines[i:end_idx] = new_block
        break

with open('runner.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed timezone comparison")
