import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath("."))

def generate_sample_csvs():
    target_dir = os.path.join("data_base", "csv", "iq_option", "EURUSD-OTC")
    os.makedirs(target_dir, exist_ok=True)

    base_time = datetime.now() - timedelta(hours=30)
    
    # Generate M1 (350 candles)
    m1_dates = [base_time + timedelta(minutes=i) for i in range(350)]
    np.random.seed(42)
    price = 1.0850
    m1_rows = []
    for dt in m1_dates:
        change = np.random.normal(0, 0.0001)
        open_p = price
        close_p = price + change
        high_p = max(open_p, close_p) + abs(np.random.normal(0, 0.00005))
        low_p = min(open_p, close_p) - abs(np.random.normal(0, 0.00005))
        volume = float(np.random.randint(10, 100))
        m1_rows.append({
            'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'open': round(open_p, 6),
            'high': round(high_p, 6),
            'low': round(low_p, 6),
            'close': round(close_p, 6),
            'volume': volume
        })
        price = close_p
        
    df_m1 = pd.DataFrame(m1_rows)
    df_m1.to_csv(os.path.join(target_dir, "EURUSD-OTC_M1.csv"), index=False)

    # Generate M5 (300 candles)
    m5_dates = [base_time + timedelta(minutes=5*i) for i in range(300)]
    price = 1.0850
    m5_rows = []
    for dt in m5_dates:
        change = np.random.normal(0, 0.0003)
        open_p = price
        close_p = price + change
        high_p = max(open_p, close_p) + abs(np.random.normal(0, 0.0001))
        low_p = min(open_p, close_p) - abs(np.random.normal(0, 0.0001))
        volume = float(np.random.randint(50, 500))
        m5_rows.append({
            'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'open': round(open_p, 6),
            'high': round(high_p, 6),
            'low': round(low_p, 6),
            'close': round(close_p, 6),
            'volume': volume
        })
        price = close_p
    df_m5 = pd.DataFrame(m5_rows)
    df_m5.to_csv(os.path.join(target_dir, "EURUSD-OTC_M5.csv"), index=False)

    # Generate M15 (100 candles)
    m15_dates = [base_time + timedelta(minutes=15*i) for i in range(100)]
    price = 1.0850
    m15_rows = []
    for dt in m15_dates:
        change = np.random.normal(0, 0.0005)
        open_p = price
        close_p = price + change
        high_p = max(open_p, close_p) + abs(np.random.normal(0, 0.0002))
        low_p = min(open_p, close_p) - abs(np.random.normal(0, 0.0002))
        volume = float(np.random.randint(150, 1500))
        m15_rows.append({
            'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'open': round(open_p, 6),
            'high': round(high_p, 6),
            'low': round(low_p, 6),
            'close': round(close_p, 6),
            'volume': volume
        })
        price = close_p
    df_m15 = pd.DataFrame(m15_rows)
    df_m15.to_csv(os.path.join(target_dir, "EURUSD-OTC_M15.csv"), index=False)
    print(f"Sample CSVs generated in {target_dir}")

def test_orchestrator():
    from data_evaluate.orchestrator import Orchestrator
    orc = Orchestrator()
    print("Testing Orchestrator.process_cycle('EURUSD-OTC')...")
    res = orc.process_cycle("EURUSD-OTC")
    print("SUCCESS! process_cycle executed without errors.")
    print("Core Analysis state:", res['core_analysis']['state'])
    print("Supplementary engines executed:", list(res['supplementary_data']['supplementary_engines'].keys()))

if __name__ == "__main__":
    generate_sample_csvs()
    test_orchestrator()
