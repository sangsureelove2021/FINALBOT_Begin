import os
import sys
from pathlib import Path
import pandas as pd

# Add parent directory
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from core.data.iq_option_adapter import IQOptionAdapter
from core.config_loader import load_settings

def test_grab():
    print("Starting data grab test...")
    settings = load_settings(reload=False)
    account_type = settings.get("account", {}).get("account_type", "PRACTICE")
    symbols = settings.get("symbols", ["EURUSD"])
    
    # Connect
    adapter = IQOptionAdapter(account_type=account_type)
    if not adapter.is_connected():
        print("Failed to connect to IQ Option")
        return
        
    for symbol in symbols[:1]: # Test first symbol
        print(f"Fetching data for {symbol}...")
        
        # M5 200 candles
        print("   -> Fetching M5 (200 candles)...")
        candles_m5 = adapter.get_candles(symbol, 'M5', 200)
        
        # M1 200 candles
        print("   -> Fetching M1 (200 candles)...")
        candles_m1 = adapter.get_candles(symbol, 'M1', 200)
        
        # M15 from M5
        print("   -> Calculating M15 from M5 via Pandas Resampling...")
        candles_m15 = candles_m5.resample('15min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        # Save files
        save_dir = os.path.join("data", "csv", symbol.replace("-OTC", "_OTC"))
        os.makedirs(save_dir, exist_ok=True)
        
        file_m1 = os.path.join(save_dir, "M1.csv")
        file_m5 = os.path.join(save_dir, "M5.csv")
        file_m15 = os.path.join(save_dir, "M15.csv")
        
        candles_m1.to_csv(file_m1)
        candles_m5.to_csv(file_m5)
        candles_m15.to_csv(file_m15)
        
        print(f"Data saved successfully at: {save_dir}")
        print(f"   - {file_m1} ({len(candles_m1)} candles)")
        print(f"   - {file_m5} ({len(candles_m5)} candles)")
        print(f"   - {file_m15} ({len(candles_m15)} candles)")

if __name__ == "__main__":
    test_grab()
