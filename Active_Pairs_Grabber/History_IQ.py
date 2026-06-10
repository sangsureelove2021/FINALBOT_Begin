"""
History_IQ.py — Historical Data Grabber for FINALBOT (Updated Version)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fetches and saves long-term historical candles from IQ Option
directly to well-structured CSV files. If a file already exists,
it merges the new data with the old data without duplicates.

Usage: python History_IQ.py
"""

import os
import sys
import time
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory (project root) to sys.path to allow running directly from IDLE or other folders
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Wrap standard output safely to prevent cp874/Windows terminal encoding crashes
class SafeStreamWrapper:
    def __init__(self, original_stream):
        self.original_stream = original_stream
        self.encoding = getattr(original_stream, 'encoding', None) or 'utf-8'

    def write(self, data):
        try:
            self.original_stream.write(data)
        except Exception:
            try:
                safe_data = data.encode('ascii', errors='backslashreplace').decode('ascii')
                self.original_stream.write(safe_data)
            except Exception:
                pass
        self.flush()

    def flush(self):
        if hasattr(self.original_stream, 'flush'):
            self.original_stream.flush()

    def __getattr__(self, attr):
        return getattr(self.original_stream, attr)

sys.stdout = SafeStreamWrapper(sys.stdout)
sys.stderr = SafeStreamWrapper(sys.stderr)

# Import the secure configuration adapter
from core.data.iq_option_adapter import IQOptionAdapter
from main import load_symbols

# Output directory for historical CSVs
OUTPUT_DIR = Path("historical_data")


def fetch_history(adapter, symbol: str, timeframe: str, target_count: int) -> pd.DataFrame:
    """
    Download a large number of historical candles from IQ Option using
    recursive timestamp shifting (pagination).
    """
    size = adapter._TF_SECONDS.get(timeframe, 60)
    all_candles = []
    end_time = time.time()
    
    print(f"\n>>> [DOWNLOAD] Starting download of {target_count} candles for {symbol} ({timeframe})...")
    
    while len(all_candles) < target_count:
        batch_size = min(1000, target_count - len(all_candles))
        try:
            # Direct REST API call on the active API stream wrapper
            raw = adapter.api.get_candles(symbol, size, batch_size, end_time)
            
            if not raw or not isinstance(raw, list):
                print("   [INFO] Empty or invalid batch returned. Ending download loop.")
                break
                
            df_batch = pd.DataFrame(raw)
            if df_batch.empty:
                print("   [INFO] No more historical data found. Ending download loop.")
                break
            
            # Prepend/append candles
            all_candles.extend(raw)
            
            # Shift end_time to the oldest candle in the batch (first item has the lowest timestamp)
            oldest_timestamp = int(raw[0]["from"])
            end_time = oldest_timestamp - 1
            
            print(f"   -> Progress: {len(all_candles)} / {target_count} candles successfully retrieved...")
            
            # Brief cooldown to respect API rate limits
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   [ERROR] Exception encountered during pagination: {e}")
            break
            
    if not all_candles:
        return pd.DataFrame()
        
    # Standardize and clean the dataset
    df = pd.DataFrame(all_candles)
    df = df.drop_duplicates(subset=['from'])
    
    # Standardize column mappings (low/high instead of min/max)
    df = df.rename(columns={"max": "high", "min": "low"})
    
    # Format datetimes
    df["timestamp"] = pd.to_datetime(df["from"], unit="s")
    for col in ("open", "close", "high", "low"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["volume"] = pd.to_numeric(df.get("volume", 0), errors="coerce").fillna(0.0)
    
    # Filter rows with complete pricing
    df = df.dropna(subset=["open", "close", "high", "low"])
    
    # Select clean columns
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    
    # Sort oldest-first (standard chronological database format)
    df = df.sort_values(by="timestamp").reset_index(drop=True)
    
    return df


def main():
    print("="*80)
    print("=== FINALBOT HISTORICAL DATA GRABBER (History_IQ) ===")
    print("="*80)
    
    # Step 1: Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 2: Load active symbols capped at 6 (same as bot)
    try:
        symbols = load_symbols()[:6]
        print(f"[OK] Loaded symbols to fetch (capped at 6): {symbols}")
    except Exception as e:
        print(f"[ERROR] Failed to load symbols.txt: {e}")
        sys.exit(1)
        
    # Step 3: Define timeframes (same as bot)
    timeframes = ['M1', 'M5', 'M15', 'M60']
    print(f"[OK] Target timeframes: {timeframes}")
    
    # Step 4: Ask for download volume in days
    num_days = 3.0
    try:
        user_input = input("\nEnter number of days of history to fetch [Default: 3]: ").strip()
        if user_input:
            num_days = float(user_input)
    except Exception:
        pass
    print(f"[OK] Target history duration: {num_days} days")
        
    print(f"\n[INIT] Connecting to IQ Option API using your config settings...")
    try:
        from core.config_loader import get_account_type
        account_type = get_account_type()
        
        # Instantiate secure adapter (locked live connection)
        adapter = IQOptionAdapter(account_type=account_type)
        if not adapter.is_connected():
            raise RuntimeError("API adapter failed to connect")
    except Exception as e:
        print(f"[FATAL] Failed to connect to IQ Option API: {e}")
        sys.exit(1)
        
    print("\n" + "="*80)
    print("[RUN] Starting Historical Fetch Cycles...")
    print("="*80)
    
    success_count = 0
    total_downloads = len(symbols) * len(timeframes)
    
    for symbol in symbols:
        for tf in timeframes:
            try:
                # Calculate target candle count dynamically based on the requested days
                minutes_per_candle = {'M1': 1, 'M5': 5, 'M15': 15, 'M60': 60}.get(tf, 1)
                candles_per_day = 1440 / minutes_per_candle
                target_count = int(num_days * candles_per_day)
                
                print(f"\n[CALC] Timeframe {tf} for {symbol}: {num_days} days -> {target_count} candles calculated.")
                
                df = fetch_history(adapter, symbol, tf, target_count)
                if df.empty:
                    print(f"   ❌ [FAILED] Downloaded 0 candles for {symbol} ({tf})")
                    continue
                    
                # Save as premium formatted CSV
                file_name = f"history_{symbol.replace('-OTC', '_OTC')}_{tf}.csv"
                file_path = OUTPUT_DIR / file_name
                
                # --- [ส่วนที่เพิ่มใหม่] ตรวจสอบไฟล์เดิมเพื่อนำมาเขียนต่อและลบตัวซ้ำ ---
                if file_path.exists():
                    try:
                        df_existing = pd.read_csv(file_path)
                        # แปลงเวลาให้เป็นรูปแบบเดียวกันก่อนทำการรวมข้อมูล
                        df_existing["timestamp"] = pd.to_datetime(df_existing["timestamp"])
                        
                        # รวมข้อมูลเก่าและใหม่เข้าด้วยกัน
                        df = pd.concat([df_existing, df], ignore_index=True)
                        
                        # ลบแท่งเทียนที่เวลาตรงกันซ้ำออก และเรียงลำดับเวลาใหม่จากเก่าไปใหม่
                        df = df.drop_duplicates(subset=['timestamp'])
                        df = df.sort_values(by="timestamp").reset_index(drop=True)
                        print(f"   🔄 [MERGE] Found existing file. Successfully merged new data with history.")
                    except Exception as merge_err:
                        print(f"   ⚠️ [WARNING] Could not merge with existing file, overwriting instead: {merge_err}")
                # -----------------------------------------------------------------
                
                df.to_csv(file_path, index=False, date_format="%Y-%m-%d %H:%M:%S")
                print(f"   ✅ [SAVED] Successfully wrote {len(df)} candles -> {file_path}")
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ [ERROR] Failed during processing for {symbol} ({tf}): {e}")
                
            # Cooldown between symbols/timeframes
            time.sleep(1.0)
            
    print("\n" + "="*80)
    print("=== SUMMARY REPORT ===")
    print("="*80)
    print(f"Total downloads planned : {total_downloads}")
    print(f"Successfully completed  : {success_count} / {total_downloads}")
    print(f"Saved directory         : {OUTPUT_DIR.resolve()}")
    print("All data is formatted chronologically: timestamp,open,high,low,close,volume")
    print("Ready for offline historical validation and strategy checks!")
    print("="*80)


if __name__ == "__main__":
    main()
