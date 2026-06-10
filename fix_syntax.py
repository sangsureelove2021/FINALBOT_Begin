with open('runner.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the start of the backtest date handling
start_idx = None
for i, line in enumerate(lines):
    if 'backtest_cfg = settings.get("backtest", {})' in line:
        start_idx = i
        break

if start_idx is None:
    print("Could not find backtest section")
    exit(1)

# Locate the if start_date_str block
for i in range(start_idx, len(lines)):
    if 'if start_date_str:' in lines[i]:
        # Remove from this line until the line after the else block
        end_idx = i
        # Find where the else block ends (next line after the else block's content)
        while end_idx < len(lines) and 'days_back = 30' not in lines[end_idx]:
            end_idx += 1
        # Include the line with days_back = 30 and the following line
        end_idx += 2  # to include the log line
        # Replace with correct code
        new_block = [
            '        if start_date_str:\n',
            '            try:\n',
            '                start_dt = pd.to_datetime(start_date_str)\n',
            '                # Make timezone-aware UTC\n',
            '                if start_dt.tzinfo is None:\n',
            '                    start_dt = start_dt.tz_localize("UTC")\n',
            '                else:\n',
            '                    start_dt = start_dt.tz_convert("UTC")\n',
            '            except Exception as e:\n',
            '                logger.warning(f"Failed to parse start_date \'{start_date_str}\': {e}")\n',
            '        \n',
            '        if end_date_str:\n',
            '            try:\n',
            '                end_dt = pd.to_datetime(end_date_str)\n',
            '                # Make timezone-aware UTC\n',
            '                if end_dt.tzinfo is None:\n',
            '                    end_dt = end_dt.tz_localize("UTC")\n',
            '                else:\n',
            '                    end_dt = end_dt.tz_convert("UTC")\n',
            '            except Exception as e:\n',
            '                logger.warning(f"Failed to parse end_date \'{end_date_str}\': {e}")\n',
            '        \n',
            '        if start_dt:\n',
            '            thai_console_log(f"[BACKTEST] ช่วงการทดสอบ: ตั้งแต่ {start_date_str} ถึง {end_date_str or \'ปัจจุบัน\'}")\n',
            '            days_back = (datetime.now(timezone.utc) - start_dt).days + 2\n',
            '        else:\n',
            '            days_back = 30\n',
            '            thai_console_log(f"[BACKTEST] วันที่ต้องการทดสอบ: {days_back} วัน")\n',
        ]
        lines[i:end_idx] = new_block
        break

with open('runner.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Fixed syntax")
