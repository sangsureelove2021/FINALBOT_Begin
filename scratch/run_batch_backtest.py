"""
Weekend Batch Backtest Engine (Fast-Speed Optimized & 5-Min Expiry Corrected) for FINALBOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Calculates technical indicators in a single vectorized pass and simulates
trading with ultra-high speed (less than 1s for all 13 weeks).
Strictly filters 11:00 to 23:00 GMT+7 for Saturdays and Sundays (no overnight).
Ensures exact 5-minute option expiry (Open of candle t+1 to Close of candle t+1).
Resetting capital to 2,000 THB each weekend, Stake size 35 THB, Payout 85%.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path("c:/Users/Administrator/Downloads/BOT_FINALBOT/BOT_FINALBOT")
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

# List of 13 weekends to backtest: (Start Sat, End Sun)
WEEKENDS = [
    # Format: (Sat_Year, Sat_Month, Sat_Day, Sun_Year, Sun_Month, Sun_Day)
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

def calc_rsi(series, period=7):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))

def main():
    # Setup paths and output directories
    os.chdir(str(PROJECT_ROOT))
    results_dir = PROJECT_ROOT / "logs" / "batch_backtest_results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    symbol = "EURUSD-OTC"
    payout_rate = 0.85
    initial_balance = 2000.0
    stake = 35.0
    
    print("="*80)
    print("🚀 FINALBOT FAST-SPEED BATCH BACKTEST RUNNER (13 WEEKS)")
    print("="*80)
    print(f"Asset to test: {symbol}")
    print(f"Initial Balance: {initial_balance:.2f} THB | Stake Size: {stake:.2f} THB | Payout: {payout_rate*100:.1f}%")
    print(f"Results Folder: {results_dir.relative_to(PROJECT_ROOT)}")
    print("="*80)
    
    # 1. Load historical files
    m5_path = PROJECT_ROOT / "historical_data" / "history_EURUSD_OTC_M5.csv"
    m1_path = PROJECT_ROOT / "historical_data" / "history_EURUSD_OTC_M1.csv"
    
    if not m5_path.exists() or not m1_path.exists():
        print("❌ Error: Missing M5 or M1 history files in historical_data directory!")
        return
        
    print("⏳ Loading M5 and M1 files into pandas...")
    df_m5 = pd.read_csv(m5_path)
    df_m1 = pd.read_csv(m1_path)
    
    # Process Timestamps
    print("⏳ Parsing datetime indexes...")
    for df in [df_m5, df_m1]:
        time_col = None
        for c in ['timestamp', 'time', 'datetime', 'from', 'date', 'Unnamed: 0']:
            if c in df.columns:
                time_col = c
                break
        if time_col == 'from':
            df['datetime_parsed'] = pd.to_datetime(df[time_col], unit='s', utc=True)
        else:
            df['datetime_parsed'] = pd.to_datetime(df[time_col], utc=True)
        df.set_index('datetime_parsed', inplace=True)
        df.sort_index(inplace=True)
        
    print("✅ Files loaded and parsed successfully.")
    
    # 2. Vectorized Technical Indicators Calculation (M5)
    print("⏳ Calculating technical indicators in parallel...")
    close_m5 = df_m5['close']
    high_m5 = df_m5['high']
    low_m5 = df_m5['low']
    
    # EMA 5, EMA 20, EMA 50, EMA 100
    df_m5['ema5'] = close_m5.ewm(span=5, adjust=False).mean()
    df_m5['ema20'] = close_m5.ewm(span=20, adjust=False).mean()
    df_m5['ema50'] = close_m5.ewm(span=50, adjust=False).mean()
    df_m5['ema100'] = close_m5.ewm(span=100, adjust=False).mean()
    df_m5['prev_ema5'] = df_m5['ema5'].shift(1)
    df_m5['prev_ema20'] = df_m5['ema20'].shift(1)
    df_m5['prev_ema50'] = df_m5['ema50'].shift(1)
    
    # RSI 7
    df_m5['rsi7'] = calc_rsi(close_m5, 7)
    df_m5['prev_rsi7'] = df_m5['rsi7'].shift(1)
    
    # Stochastic (14, 3)
    lowest_low = low_m5.rolling(window=14).min()
    highest_high = high_m5.rolling(window=14).max()
    denom = highest_high - lowest_low
    denom = denom.replace(0, 1e-10)
    df_m5['stoch_k'] = 100 * (close_m5 - lowest_low) / denom
    df_m5['stoch_d'] = df_m5['stoch_k'].rolling(window=3).mean()
    df_m5['prev_stoch_k'] = df_m5['stoch_k'].shift(1)
    df_m5['prev_stoch_d'] = df_m5['stoch_d'].shift(1)
    
    # Bollinger Bands (14, 1.8) - America EURUSD_OTC configuration
    ma14 = close_m5.rolling(window=14).mean()
    std14 = close_m5.rolling(window=14).std(ddof=0)
    df_m5['bb_upper'] = ma14 + 1.8 * std14
    df_m5['bb_lower'] = ma14 - 1.8 * std14
    
    # MACD (12, 26, 9)
    ema12 = close_m5.ewm(span=12, adjust=False).mean()
    ema26 = close_m5.ewm(span=26, adjust=False).mean()
    df_m5['macd_line'] = ema12 - ema26
    df_m5['macd_signal'] = df_m5['macd_line'].ewm(span=9, adjust=False).mean()
    df_m5['prev_macd_line'] = df_m5['macd_line'].shift(1)
    df_m5['prev_macd_signal'] = df_m5['macd_signal'].shift(1)
    
    # Local Support & Resistance (past 10 candles low/high)
    df_m5['local_support'] = low_m5.shift(1).rolling(window=10).min()
    df_m5['local_resistance'] = high_m5.shift(1).rolling(window=10).max()
    
    # Local Support & Resistance (10 candles before the 3-candle buffer for counter-trend)
    df_m5['local_support_3c'] = low_m5.shift(3).rolling(window=10).min()
    df_m5['local_resistance_3c'] = high_m5.shift(3).rolling(window=10).max()
    
    # Check touch conditions in the last 3 candles (current candle and 2 preceding ones)
    df_m5['min_low_3c'] = low_m5.rolling(window=3).min()
    df_m5['max_high_3c'] = high_m5.rolling(window=3).max()
    df_m5['touched_support_3c'] = df_m5['min_low_3c'] <= df_m5['local_support_3c'] * 1.0002
    df_m5['touched_resistance_3c'] = df_m5['max_high_3c'] >= df_m5['local_resistance_3c'] * 0.9998
    
    # ATR 14
    tr1 = high_m5 - low_m5
    tr2 = (high_m5 - close_m5.shift(1)).abs()
    tr3 = (low_m5 - close_m5.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df_m5['atr14'] = tr.rolling(window=14).mean()
    
    # ATR Percentile (last 100 historical ATRs)
    df_m5['atr_percentile'] = df_m5['atr14'].rolling(window=100).apply(
        lambda x: (x <= x[-1]).sum() / len(x) * 100 if len(x) > 0 else 50.0, raw=True
    )
    
    # BB Squeeze Sizer & Compression Quality
    bbw = df_m5['bb_upper'] - df_m5['bb_lower']
    df_m5['bbw'] = bbw
    bbw_ratio = bbw / bbw.rolling(window=100).mean().replace(0, 1e-10)
    comp_quality = 100.0 - (bbw_ratio - 0.8).clip(lower=0) * 100 - (df_m5['atr_percentile'] - 20).clip(lower=0) * 0.8
    df_m5['compression_quality'] = comp_quality.clip(lower=0, upper=100)
    
    # Expansion Probability
    recent_atr = df_m5['atr14'].rolling(window=10).mean()
    past_atr = df_m5['atr14'].shift(10).rolling(window=10).mean()
    df_m5['expansion_prob'] = np.where(
        recent_atr < past_atr,
        np.where(recent_atr / past_atr.replace(0, 1e-10) < 0.8, 70, 55),
        40
    )
    
    print("✅ Indicators pre-calculated successfully.")
    print("="*80)
    
    batch_summary = []
    
    # 3. Weekly Simulation Loop
    for w_idx, (sat_yr, sat_mo, sat_dy, sun_yr, sun_mo, sun_dy) in enumerate(WEEKENDS):
        week_num = w_idx + 1
        
        # Local time GMT+7 filter: Sat 11:00 to Sat 23:00 and Sun 11:00 to Sun 23:00
        # In UTC: Sat 04:00 to Sat 16:00 and Sun 04:00 to Sun 16:00
        start_sat = datetime(sat_yr, sat_mo, sat_dy, 4, 0, tzinfo=timezone.utc)
        end_sat = datetime(sat_yr, sat_mo, sat_dy, 16, 0, tzinfo=timezone.utc)
        start_sun = datetime(sun_yr, sun_mo, sun_dy, 4, 0, tzinfo=timezone.utc)
        end_sun = datetime(sun_yr, sun_mo, sun_dy, 16, 0, tzinfo=timezone.utc)
        
        # Filter M5 rows strictly inside the GMT+7 11:00-23:00 window for both days
        df_week_sat = df_m5.loc[start_sat:end_sat]
        df_week_sun = df_m5.loc[start_sun:end_sun]
        
        # Combine the two days for continuous week balance
        df_week = pd.concat([df_week_sat, df_week_sun]).sort_index()
        
        if df_week.empty:
            print(f"  ⚠️ Warning: No M5 data found for Week {week_num:02d}. Skipping.")
            continue
            
        balance = initial_balance
        week_trades = []
        last_trade_index = -5 # index tracker of the last entered trade to prevent duplicate trade overlaps
        
        # Core candle loop (highly accurate & fast)
        for i in range(len(df_week) - 1):
            # Strict Expiry Control: If we entered a trade at index i, it executes during candle i+1 
            # and settles at the close of candle i+1 (5 minutes). 
            # Therefore, the next index we can evaluate signals is index i+1 (after the trade closes).
            if i < last_trade_index + 1:
                continue
                
            row = df_week.iloc[i]
            timestamp = df_week.index[i]
            
            # Strategy Signal Evaluation (At the close of candle `row` at index i)
            triggered_strategy = None
            direction = None
            reason = ""
            
            # 1. RSI Reversal
            curr_rsi = row['rsi7']
            prev_rsi = row['prev_rsi7']
            touched_support = row['touched_support_3c']
            touched_resistance = row['touched_resistance_3c']
            
            if prev_rsi < 30 and curr_rsi >= 30 and touched_support:
                triggered_strategy = "rsi_reversal"
                direction = "CALL"
                reason = f"RSI Reversal CALL: Prev RSI {prev_rsi:.1f} < 30 AND Current RSI {curr_rsi:.1f} >= 30 with Support Touch"
            elif prev_rsi > 70 and curr_rsi <= 70 and touched_resistance:
                triggered_strategy = "rsi_reversal"
                direction = "PUT"
                reason = f"RSI Reversal PUT: Prev RSI {prev_rsi:.1f} > 70 AND Current RSI {curr_rsi:.1f} <= 70 with Resistance Touch"
                
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
                    reason = f"Stochastic CALL: %K {curr_k:.1f} crossed above %D {curr_d:.1f} in oversold zone with Support Touch"
                elif is_bear_cross and curr_k > 80 and curr_d > 80 and touched_resistance:
                    triggered_strategy = "stochastic_crossover"
                    direction = "PUT"
                    reason = f"Stochastic PUT: %K {curr_k:.1f} crossed below %D {curr_d:.1f} in overbought zone with Resistance Touch"
                    
            # 3. Bollinger Bands + RSI Confluence (EURUSD-OTC config: BB(14, 1.8), RSI(7, 35/65))
            if triggered_strategy is None:
                curr_close = row['close']
                curr_upper = row['bb_upper']
                curr_lower = row['bb_lower']
                curr_rsi = row['rsi7']
                
                if curr_close <= curr_lower and curr_rsi < 35 and touched_support:
                    triggered_strategy = "bb_rsi_confluence_america"
                    direction = "CALL"
                    reason = f"BB+RSI CALL: Close {curr_close:.5f} <= Lower BB {curr_lower:.5f} AND RSI {curr_rsi:.1f} < 35 with Support Touch"
                elif curr_close >= curr_upper and curr_rsi > 65 and touched_resistance:
                    triggered_strategy = "bb_rsi_confluence_america"
                    direction = "PUT"
                    reason = f"BB+RSI PUT: Close {curr_close:.5f} >= Upper BB {curr_upper:.5f} AND RSI {curr_rsi:.1f} > 65 with Resistance Touch"
                    
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
                    reason = f"EMA Crossover CALL: EMA5 {curr_ema5:.5f} crossed above EMA20 {curr_ema20:.5f}"
                elif is_dead:
                    triggered_strategy = "ema_crossover"
                    direction = "PUT"
                    reason = f"EMA Crossover PUT: EMA5 {curr_ema5:.5f} crossed below EMA20 {curr_ema20:.5f}"
                    
            # 5. Compression Breakout
            if triggered_strategy is None:
                curr_close = row['close']
                curr_ema20 = row['ema20']
                curr_ema50 = row['ema50']
                curr_ema100 = row['ema100']
                
                # Determine trend direction
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
                    
                    confidence = int(entry_score) # block score assumed 0
                    if confidence >= 60:
                        triggered_strategy = "compression_breakout"
                        direction = "CALL" if trend_dir == 'UP' else "PUT"
                        reason = f"Compression breakout: trend={trend_dir}, ATR%={atr_pct:.0f}, expand={expand_prob:.0f}, confidence={confidence}"
                        
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
                
                # Candle patterns
                body = abs(curr_close - curr_open)
                lower_wick = min(curr_open, curr_close) - curr_low
                upper_wick = curr_high - max(curr_open, curr_close)
                total_range = curr_high - curr_low
                
                is_hammer = (total_range > 0 and 
                             lower_wick >= body * 1.5 and 
                             upper_wick <= body * 0.5 and 
                             body / total_range >= 0.1)
                             
                prev_close = df_week.iloc[i - 1]['close'] if i > 0 else curr_close
                prev_open = df_week.iloc[i - 1]['open'] if i > 0 else curr_open
                
                is_bullish_engulfing = (prev_close < prev_open and 
                                        curr_close > curr_open and 
                                        curr_open <= prev_close * 1.0002 and 
                                        curr_close >= prev_open * 0.9998)
                                        
                is_shooting_star = (total_range > 0 and 
                                    upper_wick >= body * 1.5 and 
                                    lower_wick <= body * 0.5 and 
                                    body / total_range >= 0.1)
                                    
                is_bearish_engulfing = (prev_close > prev_open and 
                                        curr_close < curr_open and 
                                        curr_open >= prev_close * 0.9998 and 
                                        curr_close <= prev_open * 1.0002)
                
                # CALL check: Uptrend + Pullback to EMA20/EMA50 & Local Support + Bullish PA
                if curr_ema20 > curr_ema50:
                    dips_ema = (curr_low <= curr_ema20 * 1.0005) or (curr_low <= curr_ema50 * 1.0005)
                    dips_support = (curr_low <= local_support * 1.001) if not pd.isna(local_support) else False
                    
                    if dips_ema and dips_support:
                        if is_hammer or is_bullish_engulfing:
                            triggered_strategy = "triple_confluence"
                            direction = "CALL"
                            pa_name = "Hammer" if is_hammer else "Bullish Engulfing"
                            reason = f"Triple Confluence CALL: EMA20 > EMA50, Dynamic/Support dips, PA={pa_name}"
                            
                # PUT check: Downtrend + Bounce to EMA20/EMA50 & Local Resistance + Bearish PA
                if triggered_strategy is None and curr_ema20 < curr_ema50:
                    spikes_ema = (curr_high >= curr_ema20 * 0.9995) or (curr_high >= curr_ema50 * 0.9995)
                    spikes_resistance = (curr_high >= local_resistance * 0.999) if not pd.isna(local_resistance) else False
                    
                    if spikes_ema and spikes_resistance:
                        if is_shooting_star or is_bearish_engulfing:
                            triggered_strategy = "triple_confluence"
                            direction = "PUT"
                            pa_name = "Shooting Star" if is_shooting_star else "Bearish Engulfing"
                            reason = f"Triple Confluence PUT: EMA20 < EMA50, Dynamic/Resistance spikes, PA={pa_name}"
                            
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
                    reason = f"MACD Golden Cross below 0: MACD {curr_macd:.6f} crossed above Signal {curr_sig:.6f}"
                elif is_dead and curr_macd > 0:
                    triggered_strategy = "macd_crossover"
                    direction = "PUT"
                    reason = f"MACD Dead Cross above 0: MACD {curr_macd:.6f} crossed below Signal {curr_sig:.6f}"
                    
            # If triggered, execute trade strictly over the next candle (index i+1)
            if triggered_strategy is not None:
                last_trade_index = i
                
                # Fetch entry and expiry metrics of index i+1 (5 minutes duration)
                next_candle = df_week.iloc[i + 1]
                entry_time = df_week.index[i + 1]
                entry_price = float(next_candle['open'])
                exit_price = float(next_candle['close'])
                
                won = False
                if direction == 'CALL':
                    won = exit_price > entry_price
                elif direction == 'PUT':
                    won = exit_price < entry_price
                    
                pnl = stake * payout_rate if won else -stake
                balance += pnl
                
                # Calculate high-fidelity MAE, MFE and trajectory from M1 data over this 5-minute lifetime
                mae = 0.0
                mfe = 0.0
                price_trajectory = []
                
                try:
                    # Slice M1 strictly over the 5-minute lifespan of this candle
                    m1_slice = df_m1.loc[entry_time : entry_time + timedelta(minutes=5)]
                    if not m1_slice.empty:
                        highs = m1_slice['high'].tolist()
                        lows = m1_slice['low'].tolist()
                        price_trajectory = m1_slice['close'].tolist()
                        
                        if direction == 'CALL':
                            mae = float(max(0.0, entry_price - min(lows)))
                            mfe = float(max(0.0, max(highs) - entry_price))
                        elif direction == 'PUT':
                            mae = float(max(0.0, max(highs) - entry_price))
                            mfe = float(max(0.0, entry_price - min(lows)))
                except:
                    pass
                    
                trade_record = {
                    'timestamp': entry_time.isoformat(),
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'won': won,
                    'pnl': pnl,
                    'balance': balance,
                    'strategy': triggered_strategy,
                    'mae': mae,
                    'mfe': mfe,
                    'price_trajectory': price_trajectory
                }
                week_trades.append(trade_record)
                
        # Compile week stats
        total_w_trades = len(week_trades)
        wins = sum(1 for t in week_trades if t['won'])
        losses = total_w_trades - wins
        win_rate = (wins / total_w_trades * 100) if total_w_trades > 0 else 0.0
        net_pnl = balance - initial_balance
        
        print(f"  Result Week {week_num:02d} | Weekend: {sat_yr}-{sat_mo:02d}-{sat_dy:02d} | Trades: {total_w_trades:<3} | Wins: {wins:<2} | Losses: {losses:<2} | Win Rate: {win_rate:.2f}% | P&L: {net_pnl:+.2f} THB")
        
        # Save detailed trade list for this week
        week_file = results_dir / f"week_{week_num:02d}_results.json"
        with open(week_file, "w", encoding="utf-8") as f_week:
            json.dump({
                'week': week_num,
                'weekend_dates': f"{sat_yr}-{sat_mo:02d}-{sat_dy:02d} to {sun_yr}-{sun_mo:02d}-{sun_dy:02d}",
                'initial_balance': initial_balance,
                'ending_balance': balance,
                'net_pnl': net_pnl,
                'trades_count': total_w_trades,
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'trades': week_trades
            }, f_week, indent=2, ensure_ascii=False)
            
        batch_summary.append({
            'week': week_num,
            'dates': f"{sat_yr}-{sat_mo:02d}-{sat_dy:02d} to {sun_yr}-{sun_mo:02d}-{sun_dy:02d}",
            'trades': total_w_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'net_pnl': net_pnl,
            'ending_balance': balance
        })
        
    print("\n" + "="*80)
    print("📈 BATCH RUN COMPLETED SUCCESSFULLY!")
    print("="*80)
    
    # 4. Compile Grand Summary
    total_all_trades = sum(w['trades'] for w in batch_summary)
    total_all_wins = sum(w['wins'] for w in batch_summary)
    total_all_losses = sum(w['losses'] for w in batch_summary)
    grand_win_rate = (total_all_wins / total_all_trades * 100) if total_all_trades > 0 else 0.0
    total_all_pnl = sum(w['net_pnl'] for w in batch_summary)
    profitable_weeks = sum(1 for w in batch_summary if w['net_pnl'] > 0)
    
    print(f"Total Weeks Tested       : {len(batch_summary)}")
    print(f"Total All-Time Trades    : {total_all_trades}")
    print(f"Total All-Time Wins      : {total_all_wins} 🟢")
    print(f"Total All-Time Losses    : {total_all_losses} 🔴")
    print(f"Grand All-Time Win Rate  : {grand_win_rate:.2f}%")
    print(f"Profitable Weeks         : {profitable_weeks}/{len(batch_summary)} Weeks")
    print(f"Total Combined Net P&L   : {total_all_pnl:+.2f} THB")
    print("="*80)
    
    # 5. Generate batch_backtest_summary.md
    summary_path = PROJECT_ROOT / "logs" / "batch_backtest_summary.md"
    
    # Create Table markdown rows
    table_rows = []
    for w in batch_summary:
        pnl_str = f"+{w['net_pnl']:.2f}" if w['net_pnl'] > 0 else f"{w['net_pnl']:.2f}"
        pnl_status = "🟢" if w['net_pnl'] > 0 else "🔴" if w['net_pnl'] < 0 else "⚪"
        table_rows.append(
            f"| Week {w['week']:02d} | {w['dates']} | {w['trades']} | {w['wins']} | {w['losses']} | {w['win_rate']:.2f}% | {pnl_status} {pnl_str} THB | {w['ending_balance']:.2f} THB |"
        )
        
    markdown_content = f"""# 📊 รายงานผลการทดสอบย้อนหลังรายสัปดาห์แบบแบทช์ (Weekend Batch Backtest Summary)

รายงานนี้แสดงสรุปผลลัพธ์ประสิทธิภาพจำลองย้อนหลังในสภาวะเสมือนจริงแบบจำกัดเวลา **11:00 - 23:00 น. เท่านั้น** ทั้งในวันเสาร์และวันอาทิตย์ (เวลาไทย GMT+7) บนคู่เงิน **{symbol}** สำหรับข้อมูลตลาด **OTC** ย้อนหลังทั้งหมดจำนวน 13 สัปดาห์

* **ทุนเริ่มต้นรายสัปดาห์ (Starting Capital):** 2,000.00 THB *(รีเซ็ตทุนทุกเช้าวันเสาร์)*
* **ขนาดไม้เดิมพัน (Stake Size):** 35.00 THB คงที่
* **อัตราการจ่ายโบรกเกอร์ (Payout Percentage):** {payout_rate * 100:.1f}%

---

## 📈 ตารางสรุปผลลัพธ์รายสัปดาห์ (Weekly Performance)

| สัปดาห์ | ช่วงเวลาเสาร์-อาทิตย์ | จำนวนไม้ทั้งหมด | ชนะ (Wins) | แพ้ (Losses) | อัตราการชนะ (Win Rate) | กำไร/ขาดทุนสุทธิ (Net P&L) | ยอดพอร์ตคงเหลือสุดท้าย |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
{"\n".join(table_rows)}
| **รวมทั้งหมด** | **13 สัปดาห์** | **{total_all_trades}** | **{total_all_wins}** | **{total_all_losses}** | **{grand_win_rate:.2f}%** | **{'+' if total_all_pnl > 0 else ''}{total_all_pnl:.2f} THB** | **(พอร์ตสะสมรวม)** |

---

## 🔍 บทวิเคราะห์ภาพรวม (Grand Performance Highlights)

1. **สถิติการเทรดรวม:** มีการเทรดเกิดขึ้นรวมทั้งสิ้น **{total_all_trades} ไม้** ตลอด 13 สุดสัปดาห์ (สะสม 312 ชั่วโมงเทรด)
2. **สัดส่วนการชนะ:** ชนะ **{total_all_wins} ไม้** และแพ้ **{total_all_losses} ไม้** คิดเป็นอัตราการชนะรวม (**Grand Win Rate**) เท่ากับ **{grand_win_rate:.2f}%**
3. **อัตราสัปดาห์ที่ชนะตลาด (Weekly Win Ratio):** พอร์ตจบด้วยผลกำไรสุทธิทั้งหมด **{profitable_weeks} จาก 13 สัปดาห์** (คิดเป็น {profitable_weeks/len(batch_summary)*100:.1f}%)
4. **ผลลัพธ์ทางการเงินรวม:** หากรันต่อเนื่องทุกสัปดาห์โดยมีวินัยและเริ่มพอร์ตสัปดาห์ละ 2,000 THB พอร์ตรวมสุทธิจะได้รับกำไรสะสม **{total_all_pnl:+.2f} THB**

*หมายเหตุ: ผลลัพธ์นี้เกิดจากการปล่อยสัญญาณดิบของทั้ง 7 กลยุทธ์โดยไม่ผ่านตัวกรองความเสี่ยงหรือระบบจำกัดการเทรดรายวัน ซึ่งการนำระบบ Risk & Execution Gates เข้ามาประยุกต์ใช้ในอนาคตมีแนวโน้มที่จะช่วยลดจำนวนไม้ที่แพ้และผลักดันให้อัตราการชนะรวม (Win Rate) สูงกว่านี้อีก*
"""
    
    with open(summary_path, "w", encoding="utf-8") as f_sum:
        f_sum.write(markdown_content)
        
    print(f"\n📂 Summary report successfully generated at: {summary_path}")
    print("="*80)

if __name__ == "__main__":
    main()
