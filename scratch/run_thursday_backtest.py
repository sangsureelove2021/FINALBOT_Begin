"""
Fast-Speed Vectorized Thursday Backtest Engine for FINALBOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Runs a comprehensive historical simulation on GBPUSD and GBPUSD-OTC specifically on Thursdays.
Filters data strictly from 11:00 to 23:00 GMT+7 (04:00 to 16:00 UTC).

Generates two JSON logs in C:/Users/Administrator/Downloads/TEST/ directory:
1. backtest_with_outcomes.json - [รูปแบบ 2 บันทึกผลเทรด] Includes outcomes and candles.
2. backtest_without_outcomes.json - [รูปแบบ 1 บันทึกสัญญาณ] Pure signals without outcomes.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np

PROJECT_ROOT = Path("C:/Users/Administrator/Downloads/BOT_FINALBOT/BOT_FINALBOT")
sys.path.insert(0, str(PROJECT_ROOT))

# Safe stream wrapper for Windows console encoding
class SafeStreamWrapper:
    def __init__(self, original_stream):
        self.original_stream = original_stream
    def write(self, data):
        try:
            self.original_stream.write(data)
        except Exception:
            try:
                safe_data = data.encode('ascii', errors='backslashreplace').decode('ascii')
                self.original_stream.write(safe_data)
            except Exception:
                pass
    def flush(self):
        if hasattr(self.original_stream, 'flush'):
            self.original_stream.flush()
    def __getattr__(self, attr):
        return getattr(self.original_stream, attr)

sys.stdout = SafeStreamWrapper(sys.stdout)
sys.stderr = SafeStreamWrapper(sys.stderr)

def calc_rsi(series, period=7):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))


def calc_dynamic_confidence(direction, row):
    """
    คำนวณ confidence แบบ dynamic จากจำนวน indicators ที่ยืนยันทิศทาง
    ช่วง: 40 (minimum) - 100 (maximum)
    """
    score = 40  # Base score
    is_put = (direction == 'PUT')

    # EMA5 vs EMA20 alignment (+10)
    if is_put and row['ema5'] < row['ema20']:
        score += 10
    elif not is_put and row['ema5'] > row['ema20']:
        score += 10

    # RSI7 extreme zone (+15)
    if is_put and row['rsi7'] > 80:
        score += 15
    elif not is_put and row['rsi7'] < 20:
        score += 15
    elif is_put and row['rsi7'] > 70:
        score += 7
    elif not is_put and row['rsi7'] < 30:
        score += 7

    # RSI14 confirmation (+5)
    if is_put and row['rsi14'] > 65:
        score += 5
    elif not is_put and row['rsi14'] < 35:
        score += 5

    # MACD direction (+10)
    if is_put and row['macd'] < row['macd_signal']:
        score += 10
    elif not is_put and row['macd'] > row['macd_signal']:
        score += 10

    # Stochastic extreme zone (+10)
    if is_put and row['stoch_k'] > 80:
        score += 10
    elif not is_put and row['stoch_k'] < 20:
        score += 10

    # Price near resistance/support (+10)
    close = row['close']
    if is_put and row['local_resistance'] > 0:
        dist_pct = abs(close - row['local_resistance']) / row['local_resistance']
        if dist_pct < 0.0005:
            score += 10
    elif not is_put and row['local_support'] > 0:
        dist_pct = abs(close - row['local_support']) / row['local_support']
        if dist_pct < 0.0005:
            score += 10

    return min(100, score)


def get_session(utc_hour):
    """
    แปลง UTC hour เป็นชื่อ session GMT+7
    """
    gmt7_hour = (utc_hour + 7) % 24
    if 9 <= gmt7_hour < 12:
        return 'LONDON_OPEN'
    elif 12 <= gmt7_hour < 17:
        return 'LONDON_SESSION'
    elif 17 <= gmt7_hour < 20:
        return 'NEW_YORK_OPEN'
    elif 20 <= gmt7_hour <= 23:
        return 'NEW_YORK_SESSION'
    else:
        return 'OFF_HOURS'

def run_fast_backtest(symbol):
    print(f"\n⏳ Loading data & calculating indicators for {symbol}...")
    m5_path = PROJECT_ROOT / "historical_data" / f"history_{symbol.replace('-', '_')}_M5.csv"
    m1_path = PROJECT_ROOT / "historical_data" / f"history_{symbol.replace('-', '_')}_M1.csv"
    
    if not m5_path.exists() or not m1_path.exists():
        print(f"❌ Missing files for {symbol}")
        return []
        
    df_m5 = pd.read_csv(m5_path)
    df_m1 = pd.read_csv(m1_path)
    
    for df in [df_m5, df_m1]:
        df['datetime'] = pd.to_datetime(df['timestamp'], utc=True)
        df.set_index('datetime', inplace=True)
        df.sort_index(inplace=True)
        
    close = df_m5['close']
    high = df_m5['high']
    low = df_m5['low']
    open_prices = df_m5['open']
    
    df_m5['ema5'] = close.ewm(span=5, adjust=False).mean()
    df_m5['ema20'] = close.ewm(span=20, adjust=False).mean()
    df_m5['ema50'] = close.ewm(span=50, adjust=False).mean()
    df_m5['prev_ema5'] = df_m5['ema5'].shift(1)
    df_m5['prev_ema20'] = df_m5['ema20'].shift(1)
    
    df_m5['rsi7'] = calc_rsi(close, 7)
    df_m5['rsi14'] = calc_rsi(close, 14)
    df_m5['prev_rsi7'] = df_m5['rsi7'].shift(1)
    
    lowest_low = low.rolling(window=14).min()
    highest_high = high.rolling(window=14).max()
    denom = (highest_high - lowest_low).replace(0, 1e-10)
    df_m5['stoch_k'] = 100 * (close - lowest_low) / denom
    df_m5['stoch_d'] = df_m5['stoch_k'].rolling(window=3).mean()
    df_m5['prev_stoch_k'] = df_m5['stoch_k'].shift(1)
    df_m5['prev_stoch_d'] = df_m5['stoch_d'].shift(1)
    
    # Bollinger Bands
    ma14 = close.rolling(window=14).mean()
    std14 = close.rolling(window=14).std(ddof=0)
    df_m5['bb_upper'] = ma14 + 1.8 * std14
    df_m5['bb_lower'] = ma14 - 1.8 * std14
    
    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df_m5['macd'] = ema12 - ema26
    df_m5['macd_signal'] = df_m5['macd'].ewm(span=9, adjust=False).mean()
    df_m5['prev_macd'] = df_m5['macd'].shift(1)
    df_m5['prev_signal'] = df_m5['macd_signal'].shift(1)
    
    # S&R Touches
    df_m5['local_support'] = low.shift(1).rolling(window=10).min()
    df_m5['local_resistance'] = high.shift(1).rolling(window=10).max()
    
    df_m5['local_support_3c'] = low.shift(3).rolling(window=10).min()
    df_m5['local_resistance_3c'] = high.shift(3).rolling(window=10).max()
    df_m5['min_low_3c'] = low.rolling(window=3).min()
    df_m5['max_high_3c'] = high.rolling(window=3).max()
    df_m5['touched_support_3c'] = df_m5['min_low_3c'] <= df_m5['local_support_3c'] * 1.0002
    df_m5['touched_resistance_3c'] = df_m5['max_high_3c'] >= df_m5['local_resistance_3c'] * 0.9998
    
    # Filter strictly for Thursdays, 11:00 - 23:00 GMT+7 (04:00 - 16:00 UTC)
    df_thurs = df_m5[df_m5.index.dayofweek == 3]
    df_filtered = df_thurs.between_time('04:00', '16:00').sort_index()
    
    if df_filtered.empty:
        return []
        
    trades = []
    last_trade_idx = -2
    last_trade_time = None  # Cooldown tracking: ป้องกัน Signal Flooding ภายใน 10 นาที

    for i in range(1, len(df_filtered) - 1):
        if i < last_trade_idx + 1:
            continue
            
        row = df_filtered.iloc[i]
        prev_row = df_filtered.iloc[i-1]
        
        # 1. Stochastic Crossover Strategy
        stoch_signal = None
        if (prev_row['prev_stoch_k'] < prev_row['prev_stoch_d'] and row['stoch_k'] > row['stoch_d'] and
            row['stoch_k'] < 20 and row['touched_support_3c']):
            stoch_signal = 'CALL'
        elif (prev_row['prev_stoch_k'] > prev_row['prev_stoch_d'] and row['stoch_k'] < row['stoch_d'] and
              row['stoch_k'] > 80 and row['touched_resistance_3c']):
            stoch_signal = 'PUT'
            
        # 2. RSI Reversal Strategy
        rsi_signal = None
        if row['rsi7'] < 10 and row['touched_support_3c']:
            rsi_signal = 'CALL'
        elif row['rsi7'] > 90 and row['touched_resistance_3c']:
            rsi_signal = 'PUT'
            
        # 3. BB RSI Confluence (Reverted to 35/65)
        bb_signal = None
        if row['close'] <= row['bb_lower'] and row['rsi7'] <= 35 and row['touched_support_3c']:
            bb_signal = 'CALL'
        elif row['close'] >= row['bb_upper'] and row['rsi7'] >= 65 and row['touched_resistance_3c']:
            bb_signal = 'PUT'
            
        # 4. EMA Crossover
        ema_signal = None
        if prev_row['prev_ema5'] <= prev_row['prev_ema20'] and row['ema5'] > row['ema20']:
            ema_signal = 'CALL'
        elif prev_row['prev_ema5'] >= prev_row['prev_ema20'] and row['ema5'] < row['ema20']:
            ema_signal = 'PUT'
            
        direction = rsi_signal or stoch_signal or bb_signal or ema_signal
        strategy_name = (
            "rsi_reversal" if rsi_signal else
            "stochastic_crossover" if stoch_signal else
            "bb_rsi_confluence" if bb_signal else
            "ema_crossover" if ema_signal else None
        )
        
        if direction:
            entry_time = df_filtered.index[i]

            # ── Cooldown: ป้องกัน Signal Flooding (ห้ามยิงซ้ำภายใน 10 นาที) ──
            if last_trade_time is not None:
                minutes_since_last = (entry_time - last_trade_time).total_seconds() / 60.0
                if minutes_since_last < 10:
                    continue

            exit_time = entry_time + timedelta(minutes=5)
            
            if exit_time in df_filtered.index:
                entry_price = float(row['close'])
                exit_price = float(df_filtered.loc[exit_time, 'close'])
                
                won = (direction == 'CALL' and exit_price > entry_price) or (direction == 'PUT' and exit_price < entry_price)
                pnl = 35.0 * 0.85 if won else -35.0

                # ── Dynamic Confidence (40-100) ──
                # เพิ่มค่า close ชั่วคราวใน row สำหรับการคำนวณ
                row_with_close = row.copy()
                row_with_close['close'] = entry_price
                dynamic_conf = calc_dynamic_confidence(direction, row_with_close)

                # ── Session & Hour GMT+7 ──
                utc_hour = entry_time.hour
                hour_gmt7 = (utc_hour + 7) % 24
                session = get_session(utc_hour)

                # ── Fetch M1 MAE / MFE ──
                mae, mfe, price_trajectory = 0.0, 0.0, [exit_price]
                try:
                    m1_slice = df_m1.loc[entry_time:exit_time]
                    if not m1_slice.empty:
                        highs, lows = m1_slice['high'].tolist(), m1_slice['low'].tolist()
                        price_trajectory = m1_slice['close'].tolist()
                        if direction == 'CALL':
                            mae = float(max(0.0, entry_price - min(lows)))
                            mfe = float(max(0.0, max(highs) - entry_price))
                        else:
                            mae = float(max(0.0, max(highs) - entry_price))
                            mfe = float(max(0.0, entry_price - min(lows)))
                except:
                    pass
                
                # ── Dynamic candle packaging (exactly last 20 candles prior to signal) ──
                last_candles = []
                idx_m5 = df_m5.index.get_loc(entry_time)
                lookback = min(20, idx_m5)
                for c_i in range(idx_m5 - lookback, idx_m5):
                    c_time = df_m5.index[c_i]
                    last_candles.append({
                        'open': round(float(open_prices.loc[c_time]), 5),
                        'high': round(float(high.loc[c_time]), 5),
                        'low': round(float(low.loc[c_time]), 5),
                        'close': round(float(close.loc[c_time]), 5)
                    })

                trades.append({
                    'timestamp': entry_time.strftime('%Y-%m-%dT%H:%M:%S+00:00'),
                    'symbol': symbol,
                    'direction': direction,
                    'confidence': dynamic_conf,
                    'size': 35.0,
                    'state': "TRENDING_WEAK" if "ema" in strategy_name else "RANGE",
                    'session': session,
                    'hour_gmt7': hour_gmt7,
                    'reason': f"{strategy_name.upper()} Triggered at {entry_price:.5f}",
                    'strategy': strategy_name,
                    'indicators': {
                        'ema5': round(float(row['ema5']), 5),
                        'prev_ema5': round(float(row['prev_ema5']), 5),
                        'ema20': round(float(row['ema20']), 5),
                        'prev_ema20': round(float(row['prev_ema20']), 5),
                        'ema50': round(float(row['ema50']), 5),
                        'bb_upper': round(float(row['bb_upper']), 5),
                        'bb_lower': round(float(row['bb_lower']), 5),
                        'rsi7': round(float(row['rsi7']), 2),
                        'rsi14': round(float(row['rsi14']), 2),
                        'macd': round(float(row['macd']), 6),
                        'macd_signal': round(float(row['macd_signal']), 6),
                        'prev_macd': round(float(row['prev_macd']), 6),
                        'prev_signal': round(float(row['prev_signal']), 6),
                        'stoch_k': round(float(row['stoch_k']), 2),
                        'stoch_d': round(float(row['stoch_d']), 2),
                        'prev_stoch_k': round(float(row['prev_stoch_k']), 2),
                        'prev_stoch_d': round(float(row['prev_stoch_d']), 2),
                        'local_support': round(float(row['local_support']), 5),
                        'local_resistance': round(float(row['local_resistance']), 5)
                    },
                    'candles': last_candles,
                    'candle_count': len(last_candles),
                    'processed': True,
                    'trade_outcome': {
                        'won': won,
                        'exit_price': round(exit_price, 5),
                        'exit_time': exit_time.strftime('%Y-%m-%dT%H:%M:%S+00:00'),
                        'pnl': round(pnl, 2)
                    }
                })
                last_trade_idx = i
                last_trade_time = entry_time  # อัปเดต cooldown timestamp
                
    return trades

def main():
    os.chdir(str(PROJECT_ROOT))
    all_trades = []
    
    for symbol in ["EURUSD", "EURUSD-OTC"]:
        all_trades.extend(run_fast_backtest(symbol))
        
    output_dir = Path("C:/Users/Administrator/Downloads/BOT_FINALBOT/BOT_FINALBOT/tests/BackTest/EURUSD")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ── รูปแบบ 2 บันทึกผลเทรด (With Outcomes and Candles) ──
    output_with = output_dir / "backtest_with_outcomes.json"
    with open(output_with, "w", encoding="utf-8") as f:
        json.dump(all_trades, f, indent=2, ensure_ascii=False)
        
    print(f"\n📊 Thursday Backtest Complete! Saved {len(all_trades)} trades to {output_with}")

if __name__ == "__main__":
    main()
