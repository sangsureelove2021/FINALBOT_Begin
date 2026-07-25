import os
import sys
import time
import glob
import logging
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath("."))

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("5CyclesTest")

from runner import PureAIRunner

def audit_all_csvs():
    """
    Rigorously audit all CSV files in data_base/csv/iq_option/.
    Returns (is_valid, error_list, summary_dict)
    """
    files = glob.glob("data_base/csv/iq_option/**/*.csv", recursive=True)
    csv_files = [f for f in files if "anomaly_logs" not in f]
    
    all_errors = []
    summary = {}
    
    for filepath in sorted(csv_files):
        rel_path = os.path.relpath(filepath, "e:\\BOT_FINALBOT\\FINALBOT_Begin")
        file_errors = []
        
        try:
            df = pd.read_csv(filepath)
        except Exception as e:
            file_errors.append(f"Failed to read CSV: {e}")
            all_errors.append((rel_path, file_errors))
            continue
            
        if df.empty:
            file_errors.append("File is empty (0 rows)")
            all_errors.append((rel_path, file_errors))
            continue

        # 1. Column presence check
        expected_cols = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
        cols = set(df.columns)
        if not expected_cols.issubset(cols):
            file_errors.append(f"Missing columns: expected {expected_cols}, got {cols}")

        # 2. NaN / null / missing data check
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            file_errors.append(f"NaN / null values present: {null_counts[null_counts > 0].to_dict()}")

        # 3. Strict Type Validation
        try:
            df['ts'] = pd.to_datetime(df['timestamp'])
        except Exception as e:
            file_errors.append(f"Invalid timestamp formatting: {e}")

        for price_col in ['open', 'high', 'low', 'close']:
            if price_col in df.columns:
                if not pd.api.types.is_numeric_dtype(df[price_col]):
                    file_errors.append(f"Column '{price_col}' is not numeric (type={df[price_col].dtype})")
                elif (df[price_col] <= 0).any():
                    file_errors.append(f"Non-positive price found in '{price_col}'")

        if 'volume' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['volume']):
                file_errors.append(f"Column 'volume' is not numeric (type={df['volume'].dtype})")
            elif (df['volume'] < 0).any():
                file_errors.append("Negative volume found")

        # 4. Timestamp Continuity & Monotonicity
        if 'ts' in df.columns:
            # Duplicate timestamps
            dups = df['ts'].duplicated().sum()
            if dups > 0:
                file_errors.append(f"Duplicate timestamps found: {dups} duplicate rows")

            # Strict increasing order
            if not df['ts'].is_monotonic_increasing:
                file_errors.append("Timestamps are not strictly increasing")

        # 5. Price Boundary Validation (OHLC bounds)
        if {'open', 'high', 'low', 'close'}.issubset(cols):
            invalid_high = (df['high'] < df['open']) | (df['high'] < df['close']) | (df['high'] < df['low'])
            invalid_low = (df['low'] > df['open']) | (df['low'] > df['close']) | (df['low'] > df['high'])

            if invalid_high.any():
                file_errors.append(f"High price boundary violation in {invalid_high.sum()} rows (High < Open/Close/Low)")
            if invalid_low.any():
                file_errors.append(f"Low price boundary violation in {invalid_low.sum()} rows (Low > Open/Close/High)")

        summary[rel_path] = {
            "rows": len(df),
            "start_time": df['timestamp'].iloc[0] if 'timestamp' in df.columns and len(df) > 0 else "N/A",
            "end_time": df['timestamp'].iloc[-1] if 'timestamp' in df.columns and len(df) > 0 else "N/A",
            "errors_count": len(file_errors)
        }
        
        if file_errors:
            all_errors.append((rel_path, file_errors))

    is_valid = len(all_errors) == 0
    return is_valid, all_errors, summary


def main():
    logger.info("Initializing PureAIRunner...")
    bot = PureAIRunner()
    
    total_cycles = 5
    cycle_results = []
    
    for cycle_idx in range(1, total_cycles + 1):
        logger.info(f"\n=================== RUNNING CYCLE {cycle_idx}/{total_cycles} ===================")
        try:
            bot.run_cycle()
            # Wait for background CSV queue to flush completely
            logger.info("Flushing background CSV write queue...")
            bot.candle_adapter._csv_queue._queue.join()
            time.sleep(1) # brief settle time
        except Exception as e:
            logger.exception(f"Exception during cycle {cycle_idx}: {e}")
            print(f"CYCLE_{cycle_idx}_FAILED: {e}")
            sys.exit(1)
            
        logger.info(f"Auditing CSV files after Cycle {cycle_idx}...")
        is_valid, errors, summary = audit_all_csvs()
        
        cycle_results.append({
            "cycle": cycle_idx,
            "is_valid": is_valid,
            "errors": errors,
            "summary": summary
        })
        
        if not is_valid:
            logger.error(f"❌ AUDIT FAILED ON CYCLE {cycle_idx}!")
            for path, errs in errors:
                logger.error(f"  File: {path}")
                for err in errs:
                    logger.error(f"    - {err}")
            sys.exit(1)
        else:
            logger.info(f"✅ CYCLE {cycle_idx} AUDIT PASSED 100% (0 errors across all {len(summary)} CSV files)")

        # Short pause between cycles if not the last cycle
        if cycle_idx < total_cycles:
            logger.info("Waiting 3 seconds before next cycle...")
            time.sleep(3)

    logger.info("\n=================== ALL 5 CYCLES COMPLETED SUCCESSFULLY ===================")
    print("\nSUCCESS: All 5 consecutive cycles passed 100% zero-error verification!")

if __name__ == "__main__":
    main()
