import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# Add project root to sys.path
base_dir = r"e:\BOT_FINALBOT\FINALBOT_Begin"
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

print("=== Starting Phase 2 Verification ===")

# Test 1: Check DataAdapter._add_age_and_quality
from data_feed.data_adapter import DataAdapter

dates = pd.date_range("2026-07-30 00:00:00", periods=5, freq="1min")
df_test = pd.DataFrame({
    'open': [1.0850, 1.0851, 1.0852, 1.0853, 1.0854],
    'high': [1.0855, 1.0856, 1.0857, 1.0858, 1.0859],
    'low': [1.0849, 1.0850, 1.0851, 1.0852, 1.0853],
    'close': [1.0851, 1.0852, 1.0853, 1.0854, 1.0855],
    'volume': [10, 20, 30, 40, 50]
}, index=dates)

now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
df_result = DataAdapter._add_age_and_quality(df_test, now_naive, 60)

print(f"Columns after _add_age_and_quality: {list(df_result.columns)}")
assert list(df_result.columns) == ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'age', 'quality'], \
    f"Columns mismatch: {list(df_result.columns)}"
assert df_result.shape[1] == 8, f"Expected 8 columns, got {df_result.shape[1]}"
print("Test 1 PASS: DataAdapter produces 8 standard columns with 'timestamp' as first column.")

# Test 2: Check CSVWriter output
from data_feed.csv_writer import CSVWriter, read_csv_safe

writer = CSVWriter()
test_csv_path = os.path.join(base_dir, "data_base", "csv", "iq_option", "TEST_SYMBOL", "TEST_SYMBOL_M1.csv")
if os.path.exists(test_csv_path):
    os.remove(test_csv_path)

writer.write(df_result, test_csv_path)

# Verify raw CSV header and contents
with open(test_csv_path, 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f.readlines() if line.strip()]

header = lines[0]
print(f"Raw CSV Header: {header}")
assert header == "timestamp,open,high,low,close,volume,age,quality", f"Unexpected header: {header}"

first_row = lines[1].split(',')
print(f"First Row Split: {first_row}")
assert len(first_row) == 8, f"Expected 8 values in CSV row, got {len(first_row)}"
print("Test 2 PASS: CSVWriter writes exactly 8 columns with index=False.")

# Test 3: Append to existing CSV and check merging with index=False
df_next = pd.DataFrame({
    'open': [1.0855],
    'high': [1.0860],
    'low': [1.0854],
    'close': [1.0858],
    'volume': [60]
}, index=pd.date_range("2026-07-30 00:05:00", periods=1, freq="1min"))

df_next_prep = DataAdapter._add_age_and_quality(df_next, now_naive, 60)
writer.write(df_next_prep, test_csv_path)

df_readback = read_csv_safe(test_csv_path)
print(f"Readback columns via read_csv_safe: {list(df_readback.columns)}")
assert list(df_readback.columns) == ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'age', 'quality'], \
    f"Merged readback mismatch: {list(df_readback.columns)}"
assert len(df_readback) == 6, f"Expected 6 rows after merge, got {len(df_readback)}"
print("Test 3 PASS: Merging CSV maintains 8 columns without duplicate index.")

# Clean up test file
if os.path.exists(test_csv_path):
    os.remove(test_csv_path)

print("=== ALL PHASE 2 TESTS PASSED 100% ===")
