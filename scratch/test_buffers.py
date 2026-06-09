import pandas as pd
import numpy as np
from datetime import datetime, timezone

# Load historical data
m5_path = "historical_data/history_EURUSD_OTC_M5.csv"
df_m5 = pd.read_csv(m5_path)

# Parse times
time_col = 'from' if 'from' in df_m5.columns else 'timestamp'
df_m5['datetime_parsed'] = pd.to_datetime(df_m5[time_col], unit='s' if time_col == 'from' else None, utc=True)
df_m5.set_index('datetime_parsed', inplace=True)
df_m5.sort_index(inplace=True)

close_m5 = df_m5['close']
high_m5 = df_m5['high']
low_m5 = df_m5['low']

# Base indicators
df_m5['ema5'] = close_m5.ewm(span=5, adjust=False).mean()
df_m5['ema20'] = close_m5.ewm(span=20, adjust=False).mean()
df_m5['ema50'] = close_m5.ewm(span=50, adjust=False).mean()
df_m5['ema100'] = close_m5.ewm(span=100, adjust=False).mean()
df_m5['prev_ema5'] = df_m5['ema5'].shift(1)
df_m5['prev_ema20'] = df_m5['ema20'].shift(1)

# RSI
delta = close_m5.diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
avg_gain = gain.ewm(alpha=1/7, adjust=False).mean()
avg_loss = loss.ewm(alpha=1/7, adjust=False).mean()
rs = avg_gain / avg_loss.replace(0, 1e-10)
df_m5['rsi7'] = 100 - (100 / (1 + rs))
df_m5['prev_rsi7'] = df_m5['rsi7'].shift(1)

# Stoch
lowest_low = low_m5.rolling(window=14).min()
highest_high = high_m5.rolling(window=14).max()
denom = (highest_high - lowest_low).replace(0, 1e-10)
df_m5['stoch_k'] = 100 * (close_m5 - lowest_low) / denom
df_m5['stoch_d'] = df_m5['stoch_k'].rolling(window=3).mean()
df_m5['prev_stoch_k'] = df_m5['stoch_k'].shift(1)
df_m5['prev_stoch_d'] = df_m5['stoch_d'].shift(1)

# BB
ma14 = close_m5.rolling(window=14).mean()
std14 = close_m5.rolling(window=14).std(ddof=0)
df_m5['bb_upper'] = ma14 + 1.8 * std14
df_m5['bb_lower'] = ma14 - 1.8 * std14

# MACD
ema12 = close_m5.ewm(span=12, adjust=False).mean()
ema26 = close_m5.ewm(span=26, adjust=False).mean()
df_m5['macd_line'] = ema12 - ema26
df_m5['macd_signal'] = df_m5['macd_line'].ewm(span=9, adjust=False).mean()
df_m5['prev_macd_line'] = df_m5['macd_line'].shift(1)
df_m5['prev_macd_signal'] = df_m5['macd_signal'].shift(1)

# Local Support & Resistance
df_m5['local_support'] = low_m5.shift(1).rolling(window=10).min()
df_m5['local_resistance'] = high_m5.shift(1).rolling(window=10).max()
df_m5['local_support_3c'] = low_m5.shift(3).rolling(window=10).min()
df_m5['local_resistance_3c'] = high_m5.shift(3).rolling(window=10).max()

# ATR
tr1 = high_m5 - low_m5
tr2 = (high_m5 - close_m5.shift(1)).abs()
tr3 = (low_m5 - close_m5.shift(1)).abs()
tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
df_m5['atr14'] = tr.rolling(window=14).mean()
df_m5['atr_percentile'] = df_m5['atr14'].rolling(window=100).apply(
    lambda x: (x <= x[-1]).sum() / len(x) * 100 if len(x) > 0 else 50.0, raw=True
)

bbw = df_m5['bb_upper'] - df_m5['bb_lower']
bbw_ratio = bbw / bbw.rolling(window=100).mean().replace(0, 1e-10)
comp_quality = 100.0 - (bbw_ratio - 0.8).clip(lower=0) * 100 - (df_m5['atr_percentile'] - 20).clip(lower=0) * 0.8
df_m5['compression_quality'] = comp_quality.clip(lower=0, upper=100)

recent_atr = df_m5['atr14'].rolling(window=10).mean()
past_atr = df_m5['atr14'].shift(10).rolling(window=10).mean()
df_m5['expansion_prob'] = np.where(
    recent_atr < past_atr,
    np.where(recent_atr / past_atr.replace(0, 1e-10) < 0.8, 70, 55),
    40
)

df_m5['min_low_3c'] = low_m5.rolling(window=3).min()
df_m5['max_high_3c'] = high_m5.rolling(window=3).max()

WEEKENDS = [
    (2026, 2, 28, 2026, 3, 1),
    (2026, 3, 7, 2026, 3, 8),
    (2026, 3, 14, 2026, 3, 15),
    (2026, 3, 21, 2026, 3, 22),
    (2026, 3, 28, 2026, 3, 29),
    (2026, 4, 4, 2026, 4, 5),
    (2026, 4, 11, 2026, 4, 12),
    (2026, 4, 18, 2026, 4, 19),
    (2026, 4, 25, 2026, 4, 26),
    (2026, 5, 2, 2026, 5, 3),
    (2026, 5, 9, 2026, 5, 10),
    (2026, 5, 16, 2026, 5, 17),
    (2026, 5, 23, 2026, 5, 24)
]

for name, sup_b, res_b in [("1.001 (0.1%)", 1.001, 0.999), 
                           ("1.0002 (0.02%)", 1.0002, 0.9998), 
                           ("1.0 (Strict Touch)", 1.0, 1.0)]:
    
    df_m5['touched_support_3c'] = df_m5['min_low_3c'] <= df_m5['local_support_3c'] * sup_b
    df_m5['touched_resistance_3c'] = df_m5['max_high_3c'] >= df_m5['local_resistance_3c'] * res_b
    
    total_trades = 0
    total_wins = 0
    payout_rate = 0.85
    stake = 35.0
    total_pnl = 0.0
    
    for w_idx, (sat_yr, sat_mo, sat_dy, sun_yr, sun_mo, sun_dy) in enumerate(WEEKENDS):
        start_sat = datetime(sat_yr, sat_mo, sat_dy, 4, 0, tzinfo=timezone.utc)
        end_sat = datetime(sat_yr, sat_mo, sat_dy, 16, 0, tzinfo=timezone.utc)
        start_sun = datetime(sun_yr, sun_mo, sun_dy, 4, 0, tzinfo=timezone.utc)
        end_sun = datetime(sun_yr, sun_mo, sun_dy, 16, 0, tzinfo=timezone.utc)
        
        df_week_sat = df_m5.loc[start_sat:end_sat]
        df_week_sun = df_m5.loc[start_sun:end_sun]
        df_week = pd.concat([df_week_sat, df_week_sun]).sort_index()
        
        if df_week.empty:
            continue
            
        last_trade_index = -5
        
        for i in range(len(df_week) - 1):
            if i < last_trade_index + 1:
                continue
                
            row = df_week.iloc[i]
            triggered_strategy = None
            direction = None
            
            # 1. RSI Reversal
            curr_rsi = row['rsi7']
            prev_rsi = row['prev_rsi7']
            touched_support = row['touched_support_3c']
            touched_resistance = row['touched_resistance_3c']
            
            if prev_rsi < 30 and curr_rsi >= 30 and touched_support:
                triggered_strategy = "rsi_reversal"
                direction = "CALL"
            elif prev_rsi > 70 and curr_rsi <= 70 and touched_resistance:
                triggered_strategy = "rsi_reversal"
                direction = "PUT"
                
            # 2. Stochastic Crossover
            if triggered_strategy is None:
                curr_k = row['stoch_k']
                curr_d = row['stoch_d']
                prev_k = row['prev_stoch_k']
                prev_d = row['prev_stoch_d']
                
                is_bull_cross = prev_k <= prev_d and curr_k > curr_d
                is_bear_cross = prev_k >= prev_d and curr_k < curr_d
                
                if is_bull_cross and curr_k < 20 and curr_d < 20 and touched_support:
                    triggered_strategy = "stochastic_crossover"
                    direction = "CALL"
                elif is_bear_cross and curr_k > 80 and curr_d > 80 and touched_resistance:
                    triggered_strategy = "stochastic_crossover"
                    direction = "PUT"
                    
            # 3. Bollinger Bands + RSI
            if triggered_strategy is None:
                curr_close = row['close']
                curr_upper = row['bb_upper']
                curr_lower = row['bb_lower']
                curr_rsi = row['rsi7']
                
                if curr_close <= curr_lower and curr_rsi < 35 and touched_support:
                    triggered_strategy = "bb_rsi_confluence_america"
                    direction = "CALL"
                elif curr_close >= curr_upper and curr_rsi > 65 and touched_resistance:
                    triggered_strategy = "bb_rsi_confluence_america"
                    direction = "PUT"
                    
            # 4. EMA Crossover
            if triggered_strategy is None:
                curr_ema5 = row['ema5']
                curr_ema20 = row['ema20']
                prev_ema5 = row['prev_ema5']
                prev_ema20 = row['prev_ema20']
                
                is_golden = prev_ema5 <= prev_ema20 and curr_ema5 > curr_ema20
                is_dead = prev_ema5 >= prev_ema20 and curr_ema5 < curr_ema20
                
                if is_golden:
                    triggered_strategy = "ema_crossover"
                    direction = "CALL"
                elif is_dead:
                    triggered_strategy = "ema_crossover"
                    direction = "PUT"
                    
            # 5. Compression Breakout
            if triggered_strategy is None:
                curr_close = row['close']
                curr_ema20 = row['ema20']
                curr_ema50 = row['ema50']
                curr_ema100 = row['ema100']
                
                trend_dir = 'NONE'
                trend_strength = 0
                if curr_close > curr_ema20 > curr_ema50 > curr_ema100:
                    trend_dir = 'UP'
                    trend_strength = 80
                elif curr_close < curr_ema20 < curr_ema50 < curr_ema100:
                    trend_dir = 'DOWN'
                    trend_strength = 80
                    
                atr_pct = row['atr_percentile']
                expand_prob = row['expansion_prob']
                comp_qual = row['compression_quality']
                
                if trend_dir != 'NONE':
                    entry_score = 50 + (trend_strength / 5) + (expand_prob / 7)
                    if comp_qual > 75:
                        entry_score += 10
                    entry_score = min(100, entry_score)
                    
                    confidence = int(entry_score)
                    if confidence >= 60:
                        triggered_strategy = "compression_breakout"
                        direction = "CALL" if trend_dir == 'UP' else "PUT"
                        
            # 6. Triple Confluence
            if triggered_strategy is None:
                curr_ema20 = row['ema20']
                curr_ema50 = row['ema50']
                curr_low = row['low']
                curr_high = row['high']
                curr_open = row['open']
                curr_close = row['close']
                local_support = row['local_support']
                local_resistance = row['local_resistance']
                
                body = abs(curr_close - curr_open)
                lower_wick = min(curr_open, curr_close) - curr_low
                upper_wick = curr_high - max(curr_open, curr_close)
                total_range = curr_high - curr_low
                
                is_hammer = (total_range > 0 and lower_wick >= body * 1.5 and upper_wick <= body * 0.5 and body / total_range >= 0.1)
                prev_close_pr = df_week.iloc[i - 1]['close'] if i > 0 else curr_close
                prev_open_pr = df_week.iloc[i - 1]['open'] if i > 0 else curr_open
                is_bullish_engulfing = (prev_close_pr < prev_open_pr and curr_close > curr_open and curr_open <= prev_close_pr * 1.0002 and curr_close >= prev_open_pr * 0.9998)
                is_shooting_star = (total_range > 0 and upper_wick >= body * 1.5 and lower_wick <= body * 0.5 and body / total_range >= 0.1)
                is_bearish_engulfing = (prev_close_pr > prev_open_pr and curr_close < curr_open and curr_open >= prev_close_pr * 0.9998 and curr_close <= prev_open_pr * 1.0002)
                
                if curr_ema20 > curr_ema50:
                    dips_ema = (curr_low <= curr_ema20 * 1.0005) or (curr_low <= curr_ema50 * 1.0005)
                    dips_support = (curr_low <= local_support * 1.001) if not pd.isna(local_support) else False
                    if dips_ema and dips_support:
                        if is_hammer or is_bullish_engulfing:
                            triggered_strategy = "triple_confluence"
                            direction = "CALL"
                            
                if triggered_strategy is None and curr_ema20 < curr_ema50:
                    spikes_ema = (curr_high >= curr_ema20 * 0.9995) or (curr_high >= curr_ema50 * 0.9995)
                    spikes_resistance = (curr_high >= local_resistance * 0.999) if not pd.isna(local_resistance) else False
                    if spikes_ema and spikes_resistance:
                        if is_shooting_star or is_bearish_engulfing:
                            triggered_strategy = "triple_confluence"
                            direction = "PUT"
                            
            # 7. MACD Crossover
            if triggered_strategy is None:
                curr_macd = row['macd_line']
                curr_sig = row['macd_signal']
                prev_macd = row['prev_macd_line']
                prev_sig = row['prev_macd_signal']
                is_golden = prev_macd <= prev_sig and curr_macd > curr_sig
                is_dead = prev_macd >= prev_sig and curr_macd < curr_sig
                if is_golden and curr_macd < 0:
                    triggered_strategy = "macd_crossover"
                    direction = "CALL"
                elif is_dead and curr_macd > 0:
                    triggered_strategy = "macd_crossover"
                    direction = "PUT"
                    
            if triggered_strategy is not None:
                last_trade_index = i
                next_candle = df_week.iloc[i + 1]
                entry_price = float(next_candle['open'])
                exit_price = float(next_candle['close'])
                won = (exit_price > entry_price) if direction == 'CALL' else (exit_price < entry_price)
                
                total_trades += 1
                if won:
                    total_wins += 1
                    total_pnl += stake * payout_rate
                else:
                    total_pnl -= stake
                    
    win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0.0
    print(f"[{name}] Trades={total_trades} | Wins={total_wins} | WinRate={win_rate:.2f}% | NetPnL={total_pnl:+.2f} THB")
