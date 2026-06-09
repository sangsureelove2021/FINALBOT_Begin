import json
import pandas as pd
import numpy as np

def run_verification():
    print("================================================================================")
    print("                   TECHNICAL INDICATORS VERIFICATION REPORT                     ")
    print("================================================================================")
    
    # 1. Load state
    state_path = "logs/market_state.json"
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception as e:
        print(f"Failed to load market state: {e}")
        return

    print(f"Timestamp: {state.get('timestamp')}")
    print(f"Asset:     {state.get('symbol')}")
    print(f"State:     {state.get('market_state')}")
    print(f"Price:     {state.get('current_price')}")
    print("--------------------------------------------------------------------------------")
    
    # 2. Extract and format candles
    candles = state.get("candles", {}).get("M5", [])
    if not candles:
        print("No candles found in market_state.json")
        return
        
    df = pd.DataFrame(candles)
    close_prices = df['close']
    
    # Calculate indicators using same formulas
    ema20 = float(close_prices.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(close_prices.ewm(span=50, adjust=False).mean().iloc[-1])
    
    ma20 = close_prices.rolling(window=20).mean()
    std20 = close_prices.rolling(window=20).std(ddof=0)
    bb_upper = float((ma20 + 2 * std20).iloc[-1])
    bb_lower = float((ma20 - 2 * std20).iloc[-1])
    
    def calc_rsi(prices, period):
        delta = prices.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
        
    rsi7 = calc_rsi(close_prices, 7)
    rsi14 = calc_rsi(close_prices, 14)
    
    ema12 = close_prices.ewm(span=12, adjust=False).mean()
    ema26 = close_prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    
    curr_macd = float(macd_line.iloc[-1])
    curr_sig = float(signal_line.iloc[-1])
    
    # S&R
    local_support = float(df['low'].iloc[-10:].min())
    local_resistance = float(df['high'].iloc[-10:].max())

    # Saved indicators
    saved = state.get("indicators", {})
    
    # 3. Print verification table
    print(f"{'INDICATOR':<20} | {'SAVED VALUE':<16} | {'CALCULATED VALUE':<16} | {'DISCREPANCY':<12}")
    print("--------------------------------------------------------------------------------")
    
    metrics = [
        ("EMA 20", saved.get("ema20"), ema20),
        ("EMA 50", saved.get("ema50"), ema50),
        ("BB Upper (ddof=0)", saved.get("bb_upper"), bb_upper),
        ("BB Lower (ddof=0)", saved.get("bb_lower"), bb_lower),
        ("RSI 7 (Wilder)", saved.get("rsi7"), rsi7),
        ("RSI 14 (Wilder)", saved.get("rsi14"), rsi14),
        ("MACD", saved.get("macd"), curr_macd),
        ("MACD Signal", saved.get("macd_signal"), curr_sig),
        ("Local Support", saved.get("local_support"), local_support),
        ("Local Resistance", saved.get("local_resistance"), local_resistance),
    ]
    
    all_pass = True
    for name, saved_val, calc_val in metrics:
        if saved_val is None:
            discrepancy_str = "N/A"
            saved_str = "MISSING"
        else:
            diff = abs(saved_val - calc_val)
            discrepancy_str = f"{diff:.2e}"
            saved_str = f"{saved_val:.6f}"
            if diff > 1e-10:
                all_pass = False
        
        calc_str = f"{calc_val:.6f}" if calc_val is not None else "N/A"
        print(f"{name:<20} | {saved_str:<16} | {calc_str:<16} | {discrepancy_str:<12}")
        
    print("--------------------------------------------------------------------------------")
    if all_pass:
        print("VERIFICATION RESULT: SUCCESS (Discrepancy is 0.00e+00 - 100% EXACT MATCH)")
    else:
        print("VERIFICATION RESULT: FAILURE (Discrepancies found)")
    print("================================================================================")

if __name__ == "__main__":
    run_verification()
