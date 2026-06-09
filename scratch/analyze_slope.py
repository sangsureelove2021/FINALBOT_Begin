import os
import sys
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
sys.path.append(os.path.abspath("e:/BOT_FINALBOT"))

from core.data.csv_data_adapter import CSVDataAdapter

def check_slope():
    data_adapter = CSVDataAdapter(data_dir="e:/BOT_FINALBOT/historical_data")
    symbol = "EURUSD"
    data_adapter.load_symbol_data(symbol, ['M5'])
    df = data_adapter.dfs[symbol]['M5']
    
    slopes = []
    momentums = []
    
    # Calculate rolling slopes of close tail(20)
    for i in range(200, len(df)):
        prices = df['close'].iloc[i-20:i]
        x = np.arange(len(prices))
        y = prices.values
        slope = float(np.polyfit(x, y, 1)[0])
        slopes.append(slope)
        
        # momentum
        current = prices.iloc[-1]
        past = prices.iloc[0]
        momentum = float(((current - past) / abs(past)) * 100) if past != 0 else 0
        momentums.append(momentum)
        
    slopes = pd.Series(slopes)
    momentums = pd.Series(momentums)
    
    print("Slope stats:")
    print(slopes.describe())
    print("\nAbsolute Slope stats:")
    print(slopes.abs().describe())
    
    print("\nMomentum stats:")
    print(momentums.describe())
    print("\nAbsolute Momentum stats:")
    print(momentums.abs().describe())
    
    # Check how many slopes would be > 0.0005
    print(f"\nNumber of slopes > 0.0005: {np.sum(slopes.abs() > 0.0005)} out of {len(slopes)}")
    # Check how many slopes would be >= 0.0001
    print(f"Number of slopes >= 0.0001: {np.sum(slopes.abs() >= 0.0001)} out of {len(slopes)}")
    print(f"Number of slopes >= 0.00002: {np.sum(slopes.abs() >= 0.00002)} out of {len(slopes)}")

if __name__ == '__main__':
    check_slope()
