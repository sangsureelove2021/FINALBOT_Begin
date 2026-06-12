#!/usr/bin/env python3
"""Forex M5 Binary Options Signal Analyzer"""
import csv
import os
from datetime import datetime
from pathlib import Path

def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        gains.append(change if change > 0 else 0)
        losses.append(-change if change < 0 else 0)
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100 if avg_gain > 0 else 50
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_sma(prices, period):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calculate_atr(rows, period=20):
    """rows: list of dicts with 'high','low','close'"""
    if len(rows) < period:
        return None
    trs = []
    for i in range(-period, 0):
        high = float(rows[i]['high'])
        low = float(rows[i]['low'])
        prev_close = float(rows[i-1]['close']) if i > -len(rows) else high
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    return sum(trs) / period

def analyze_pair(csv_path):
    """Return dict with signal and metrics"""
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if len(rows) < 50:
        return {'error': 'Insufficient data', 'pair': Path(csv_path).stem}
    
    # Use last 200 candles for stability
    data = rows[-200:]
    closes = [float(r['close']) for r in data]
    highs = [float(r['high']) for r in data]
    lows = [float(r['low']) for r in data]
    current_close = closes[-1]
    
    sma20 = calculate_sma(closes, 20)
    sma50 = calculate_sma(closes, 50)
    rsi = calculate_rsi(closes, 14)
    atr = calculate_atr(data, 20)
    support_20 = min(lows[-20:])
    resistance_20 = max(highs[-20:])
    
    # Binary Option M5 Signal Logic
    # Conservative: trend + momentum
    signal = "NO SIGNAL"
    confidence = 0
    if sma20 and rsi:
        if current_close > sma20 and rsi > 50 and rsi < 70:
            signal = "CALL"
            confidence = (rsi - 50) / 20  # 0 to 1
        elif current_close < sma20 and rsi < 50 and rsi > 30:
            signal = "PUT"
            confidence = (50 - rsi) / 20
        elif current_close > sma20 and rsi >= 70:
            signal = "CALL (OVERBOUGHT - RISKY)"
            confidence = 0.5
        elif current_close < sma20 and rsi <= 30:
            signal = "PUT (OVERSOLD - RISKY)"
            confidence = 0.5
    
    return {
        'pair': Path(csv_path).stem.replace('history_', ''),
        'last_time': data[-1]['timestamp'],
        'close': round(current_close, 5),
        'sma20': round(sma20, 5) if sma20 else None,
        'sma50': round(sma50, 5) if sma50 else None,
        'rsi': round(rsi, 1) if rsi else None,
        'atr': round(atr, 5) if atr else None,
        'support': round(support_20, 5),
        'resistance': round(resistance_20, 5),
        'signal': signal,
        'confidence': round(confidence * 100, 1)
    }

def main():
    data_dir = Path(r'C:\Users\Administrator\Documents\GitHub\BOT_FINALBOT\backtest\data test')
    m5_files = list(data_dir.glob('*_M5.csv'))
    if not m5_files:
        print("No M5 CSV files found.")
        return
    
    print("="*80)
    print(f"Forex Binary Options M5 Signal Analysis - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print(f"{'Pair':<12} {'Last Close':<12} {'SMA20':<12} {'RSI':<8} {'ATR':<10} {'Signal':<20} {'Conf%':<8}")
    print("-"*80)
    
    results = []
    for f in sorted(m5_files):
        try:
            res = analyze_pair(f)
            if 'error' in res:
                print(f"{res['pair']:<12} ERROR: {res['error']}")
            else:
                results.append(res)
                print(f"{res['pair']:<12} {res['close']:<12} {res['sma20']:<12} {res['rsi']:<8} {res['atr']:<10} {res['signal']:<20} {res['confidence']:<8}")
        except Exception as e:
            print(f"Error analyzing {f.name}: {e}")
    
    print("\n" + "="*80)
    print("SUMMARY RECOMMENDATIONS FOR M5 BINARY OPTIONS:")
    print("-"*80)
    for r in results:
        if r['signal'] != "NO SIGNAL":
            print(f"{r['pair']}: {r['signal']} (Confidence: {r['confidence']}%) - Close: {r['close']}, RSI: {r['rsi']}")
        else:
            print(f"{r['pair']}: No clear signal - RSI {r['rsi']} near 50 or sideways.")
    print("\nNote: Binary options on M5 require fast execution. Suggested expiry: 5-10 minutes.")
    print("Always use stop-loss equivalent (risk per trade <=2% of capital).")

if __name__ == "__main__":
    main()
