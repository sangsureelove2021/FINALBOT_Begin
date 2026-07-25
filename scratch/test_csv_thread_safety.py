"""
Unit Test: Thread Synchronization & Safe CSV Read/Write Verification
"""

import os
import time
import threading
import pandas as pd
import numpy as np
from data_feed.csv_writer import CSVWriter, get_file_lock, read_csv_safe
from data_feed.csv_manager import CSVManager

def test_concurrent_csv_read_write():
    test_dir = os.path.abspath("scratch/test_csv_dir")
    os.makedirs(test_dir, exist_ok=True)
    test_file = os.path.join(test_dir, "EURUSD_M1_test.csv")
    
    # Clean up previous test file
    if os.path.exists(test_file):
        os.remove(test_file)
        
    writer = CSVWriter()
    
    # Create initial CSV dataframe
    dates = pd.date_range("2026-07-24 10:00", periods=50, freq="1min")
    initial_df = pd.DataFrame({
        "open": np.random.rand(50),
        "high": np.random.rand(50) + 1.0,
        "low": np.random.rand(50) - 0.5,
        "close": np.random.rand(50),
        "volume": np.random.randint(10, 100, 50)
    }, index=dates)
    
    writer.write(initial_df, test_file)
    print(f"[TEST] Initial CSV written: {test_file}")
    
    errors = []
    read_counts = [0]
    write_counts = [0]
    stop_event = threading.Event()
    
    def writer_thread_func():
        step = 0
        while not stop_event.is_set():
            step += 1
            try:
                ts = pd.to_datetime("2026-07-24 10:50") + pd.Timedelta(minutes=step)
                new_row = pd.DataFrame({
                    "open": [1.1000 + step * 0.0001],
                    "high": [1.1050 + step * 0.0001],
                    "low": [1.0950 + step * 0.0001],
                    "close": [1.1010 + step * 0.0001],
                    "volume": [100 + step]
                }, index=[ts])
                writer.write(new_row, test_file)
                write_counts[0] += 1
                time.sleep(0.01)
            except Exception as e:
                errors.append(f"Writer error: {e}")
                
    def reader_thread_func(reader_id: int):
        while not stop_event.is_set():
            try:
                df = read_csv_safe(test_file, index_col=0)
                if df is None or df.empty or len(df) < 50:
                    errors.append(f"Reader {reader_id} read empty or corrupted data!")
                read_counts[0] += 1
                time.sleep(0.005)
            except Exception as e:
                errors.append(f"Reader {reader_id} error: {e}")

    # Launch 1 writer thread and 5 reader threads concurrently
    writer_thread = threading.Thread(target=writer_thread_func)
    reader_threads = [threading.Thread(target=reader_thread_func, args=(i,)) for i in range(5)]
    
    writer_thread.start()
    for t in reader_threads:
        t.start()
        
    time.sleep(2.0)
    stop_event.set()
    
    writer_thread.join()
    for t in reader_threads:
        t.join()
        
    print(f"[TEST] Completed: Writes={write_counts[0]}, Reads={read_counts[0]}, Errors={len(errors)}")
    if errors:
        print("[TEST] ERRORS FOUND:")
        for err in errors:
            print(f"  - {err}")
        raise RuntimeError(f"Thread safety test failed with {len(errors)} errors")
    else:
        print("[TEST] SUCCESS: 100% Thread-Safe Read/Write Verified with ZERO errors!")

if __name__ == "__main__":
    test_concurrent_csv_read_write()
