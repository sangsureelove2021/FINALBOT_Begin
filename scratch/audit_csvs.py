import os
import glob
import pandas as pd
import numpy as np

def audit_file(filepath):
    errors = []
    warnings = []
    
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return [f"Could not read CSV file: {e}"], []

    if df.empty:
        return [f"CSV file is empty: {filepath}"], []
        
    expected_cols = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
    cols = set(df.columns)
    if not expected_cols.issubset(cols):
        errors.append(f"Missing required columns. Expected {expected_cols}, got {cols}")

    # NaN / Null check
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        errors.append(f"Null/NaN values found: {null_counts.to_dict()}")

    # Type validation & conversions
    try:
        df['ts'] = pd.to_datetime(df['timestamp'])
    except Exception as e:
        errors.append(f"Invalid timestamp format: {e}")
        
    for col in ['open', 'high', 'low', 'close']:
        if col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column {col} is not numeric: type {df[col].dtype}")
            elif (df[col] <= 0).any():
                errors.append(f"Non-positive values in column {col}")

    # Duplicates check
    if 'ts' in df.columns:
        dup_count = df['ts'].duplicated().sum()
        if dup_count > 0:
            errors.append(f"Duplicate timestamps found: {dup_count} duplicate rows out of {len(df)}")
            
        # Timestamp continuity check
        if not df['ts'].is_monotonic_increasing:
            errors.append("Timestamps are not strictly increasing (out of order)")

        # Interval check based on filename
        filename = os.path.basename(filepath)
        expected_diff_sec = None
        if "_M1.csv" in filename:
            expected_diff_sec = 60
        elif "_M5.csv" in filename:
            expected_diff_sec = 300
        elif "_M15.csv" in filename:
            expected_diff_sec = 900

        if expected_diff_sec and len(df) > 1:
            diffs = df['ts'].diff().dt.total_seconds().dropna()
            bad_diffs = diffs[diffs != expected_diff_sec]
            if len(bad_diffs) > 0:
                warnings.append(f"Timestamp gap/discontinuity detected: {len(bad_diffs)} non-standard steps (expected {expected_diff_sec}s). Sample diffs: {bad_diffs.head(5).tolist()}")

    # Price boundary checks
    if {'open', 'high', 'low', 'close'}.issubset(cols):
        invalid_high = (df['high'] < df['open']) | (df['high'] < df['close']) | (df['high'] < df['low'])
        invalid_low = (df['low'] > df['open']) | (df['low'] > df['close']) | (df['low'] > df['high'])
        
        if invalid_high.any():
            errors.append(f"High price boundary violation in {invalid_high.sum()} rows")
        if invalid_low.any():
            errors.append(f"Low price boundary violation in {invalid_low.sum()} rows")

    return errors, warnings

def main():
    pattern = "data_base/csv/iq_option/**/*.csv"
    files = glob.glob(pattern, recursive=True)
    print(f"Found {len(files)} CSV files in data_base/csv/iq_option/")
    
    total_errors = 0
    total_warnings = 0
    for f in sorted(files):
        if "anomaly_logs" in f:
            continue
        errors, warnings = audit_file(f)
        print(f"\nFile: {f}")
        print(f"  Rows: {len(pd.read_csv(f))}")
        if errors:
            print("  ERRORS:")
            for err in errors:
                print(f"    - {err}")
            total_errors += len(errors)
        else:
            print("  ERRORS: None (100% Valid Structure)")
            
        if warnings:
            print("  WARNINGS:")
            for w in warnings:
                print(f"    - {w}")
            total_warnings += len(warnings)

    print(f"\n--- AUDIT SUMMARY ---")
    print(f"Total Errors across files: {total_errors}")
    print(f"Total Warnings across files: {total_warnings}")

if __name__ == "__main__":
    main()
