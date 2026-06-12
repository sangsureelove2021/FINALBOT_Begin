#!/usr/bin/env python3
"""
Simple script to run FINALBOT backtest.
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from runner import BotRunner
from core.config_loader import get_account_type, get_capital

def main():
    print(f"[INFO] Starting backtest...")
    
    account_type = get_account_type()
    capital = get_capital()
    
    print(f"[INFO] Capital: {capital}, Account type: {account_type}")
    
    bot = BotRunner(
        symbols=None,  # Loads from symbols.txt capped at 6
        capital=capital,
        account_type=account_type
    )
    
    start_time = time.time()
    
    # Run backtest - this uses the configured date range from settings.json
    bot.run_backtest()
    
    elapsed = time.time() - start_time
    print(f"\n[INFO] Backtest completed in {elapsed:.2f} seconds.")
    
    # Check results file
    results_file = PROJECT_ROOT / "backtest" / "results" / "orders_backtest.jsonl"
    if results_file.exists():
        with open(results_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"\n[RESULTS] Found {len(lines)} trades logged in {results_file}")
        if lines:
            print("\nFirst few trades:")
            for i, line in enumerate(lines[:10]):
                print(f"  {i+1}: {line.strip()}")
    else:
        print(f"\n[RESULTS] No orders_backtest.jsonl file found. No trades were executed.")
        
    # Also check for any other result files
    results_dir = PROJECT_ROOT / "backtest" / "results"
    if results_dir.exists():
        csv_files = list(results_dir.glob("*.csv"))
        if csv_files:
            print(f"\n[RESULTS] Found CSV result files:")
            for csv_file in csv_files:
                # Get file modification time
                mtime = csv_file.stat().st_mtime
                print(f"  - {csv_file.name} (modified: {time.ctime(mtime)})")
        
        json_files = list(results_dir.glob("*.json"))
        if json_files:
            print(f"\n[RESULTS] Found JSON result files:")
            for json_file in json_files:
                mtime = json_file.stat().st_mtime
                print(f"  - {json_file.name} (modified: {time.ctime(mtime)})")

if __name__ == "__main__":
    main()
