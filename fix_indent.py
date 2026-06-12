import re

with open('runner.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the broken block and replace it
pattern = r'        if start_date_str:\n            try:\n                start_dt = pd\.to_datetime\(start_date_str\)\n                # Make timezone-aware UTC\n                if start_dt\.tzinfo is None:\n                    start_dt = start_dt\.tz_localize\("UTC"\)\n                else:\n                    start_dt = start_dt\.tz_convert\("UTC"\)\n            try:\n                end_dt = pd\.to_datetime\(end_date_str\)\n                # Make timezone-aware UTC\n                if end_dt\.tzinfo is None:\n                    end_dt = end_dt\.tz_localize\("UTC"\)\n                else:\n                    end_dt = end_dt\.tz_convert\("UTC"\)\n            thai_console_log\(f"\[BACKTEST\] ช่วงการทดสอบ: ตั้งแต่ {start_date_str} ถึง {end_date_str or 'ปัจจุบัน'}"\)\n            days_back = \(datetime\.now\(timezone\.utc\) - start_dt\)\.days \+ 2\n        else:\n            days_back = 30\n            thai_console_log\(f"\[BACKTEST\] วันที่ต้องการทดสอบ: {days_back} วัน"\)'

replacement = '''        if start_date_str:
            try:
                start_dt = pd.to_datetime(start_date_str)
                # Make timezone-aware UTC
                if start_dt.tzinfo is None:
                    start_dt = start_dt.tz_localize("UTC")
                else:
                    start_dt = start_dt.tz_convert("UTC")
            except Exception as e:
                logger.warning(f"Failed to parse start_date '{start_date_str}': {e}")
        
        if end_date_str:
            try:
                end_dt = pd.to_datetime(end_date_str)
                # Make timezone-aware UTC
                if end_dt.tzinfo is None:
                    end_dt = end_dt.tz_localize("UTC")
                else:
                    end_dt = end_dt.tz_convert("UTC")
            except Exception as e:
                logger.warning(f"Failed to parse end_date '{end_date_str}': {e}")

        if start_dt:
            thai_console_log(f"[BACKTEST] ช่วงการทดสอบ: ตั้งแต่ {start_date_str} ถึง {end_date_str or 'ปัจจุบัน'}")
            days_back = (datetime.now(timezone.utc) - start_dt).days + 2
        else:
            days_back = 30
            thai_console_log(f"[BACKTEST] วันที่ต้องการทดสอบ: {days_back} วัน")'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('runner.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed indentation and exception blocks")
