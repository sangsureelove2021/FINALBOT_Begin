import sys
import os
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Tuple
import bisect

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

# Load M1 and M5 CSVs for both symbols
def load_data(symbol):
    m1_path = PROJECT_ROOT / f"historical_data/history_{symbol.replace('-', '_')}_M1.csv"
    m5_path = PROJECT_ROOT / f"historical_data/history_{symbol.replace('-', '_')}_M5.csv"
    
    m1_df = pd.read_csv(m1_path, index_col='timestamp', parse_dates=True)
    m5_df = pd.read_csv(m5_path, index_col='timestamp', parse_dates=True)
    
    if m1_df.index.tzinfo is None:
        m1_df.index = m1_df.index.tz_localize(timezone.utc)
    if m5_df.index.tzinfo is None:
        m5_df.index = m5_df.index.tz_localize(timezone.utc)
        
    return m1_df, m5_df

print("Loading data...")
eurusd_m1, eurusd_m5 = load_data("EURUSD")
otc_m1, otc_m5 = load_data("EURUSD-OTC")

def find_swings(df_m5, swing_window=2):
    """Detect swings and return list of (index, value)"""
    highs = df_m5['high']
    lows = df_m5['low']
    n = len(df_m5)
    
    swing_highs = []
    swing_lows = []
    
    for i in range(swing_window, n - swing_window):
        # Swing High
        is_high = True
        for j in range(1, swing_window + 1):
            if highs.iloc[i] < highs.iloc[i-j] or highs.iloc[i] < highs.iloc[i+j]:
                is_high = False
                break
        if is_high:
            swing_highs.append((i, float(highs.iloc[i])))
            
        # Swing Low
        is_low = True
        for j in range(1, swing_window + 1):
            if lows.iloc[i] > lows.iloc[i-j] or lows.iloc[i] > lows.iloc[i+j]:
                is_low = False
                break
        if is_low:
            swing_lows.append((i, float(lows.iloc[i])))
            
    return swing_highs, swing_lows

def precompute_levels_and_trends(df_m5, swing_highs, swing_lows):
    n = len(df_m5)
    resistances = [None] * n
    supports = [None] * n
    trends = ['RANGE'] * n
    
    sh_indices = [idx for idx, val in swing_highs]
    sl_indices = [idx for idx, val in swing_lows]
    
    for i in range(n):
        pos_h = bisect.bisect_left(sh_indices, i)
        pos_l = bisect.bisect_left(sl_indices, i)
        
        if pos_h > 0:
            resistances[i] = swing_highs[pos_h - 1][1]
        if pos_l > 0:
            supports[i] = swing_lows[pos_l - 1][1]
            
        if pos_h >= 2 and pos_l >= 2:
            sh1 = swing_highs[pos_h - 2][1]
            sh2 = swing_highs[pos_h - 1][1]
            sl1 = swing_lows[pos_l - 2][1]
            sl2 = swing_lows[pos_l - 1][1]
            
            if sh2 > sh1 and sl2 > sl1:
                trends[i] = 'UP'
            elif sh2 < sh1 and sl2 < sl1:
                trends[i] = 'DOWN'
                
    return resistances, supports, trends

# Precompute data for both symbols to run at maximum speed
def prepare_symbol_cache(symbol, m1_df, m5_df, start_dt, end_dt):
    # Slice M5 index to range
    ref_timestamps = m5_df.index[(m5_df.index >= start_dt) & (m5_df.index <= end_dt)]
    
    # Pre-map M1 searchsorted indices
    m1_times = m1_df.index
    m1_pos_mapping = [m1_times.searchsorted(ts, side='right') for ts in ref_timestamps]
    
    # Pre-map indices in M5
    m5_loc_mapping = [m5_df.index.get_loc(ts) for ts in ref_timestamps]
    
    # Pre-fetch M1 OHLC arrays for fast O(1) index access
    m1_open = m1_df['open'].values
    m1_high = m1_df['high'].values
    m1_low = m1_df['low'].values
    m1_close = m1_df['close'].values
    
    # Expiry forward price lookup maps
    # Store close prices at 1m, 2m, 3m, 5m expiry offsets
    expiries = [1, 2, 3, 5]
    expiry_price_maps = {}
    for exp in expiries:
        prices = []
        for ts in ref_timestamps:
            expiry_time = ts + timedelta(minutes=exp)
            # Fetch expiry close price
            exit_price = None
            if expiry_time in m1_df.index:
                exit_price = float(m1_df.loc[expiry_time, 'close'])
            elif expiry_time in m5_df.index:
                exit_price = float(m5_df.loc[expiry_time, 'close'])
            else:
                closest_idx = m1_times.get_indexer([expiry_time], method='bfill')[0]
                if closest_idx != -1:
                    exit_price = float(m1_open[closest_idx]) # fallback to open or close
            prices.append(exit_price)
        expiry_price_maps[exp] = prices
        
    return {
        'ref_timestamps': ref_timestamps,
        'm1_pos_mapping': m1_pos_mapping,
        'm5_loc_mapping': m5_loc_mapping,
        'm1_open': m1_open,
        'm1_high': m1_high,
        'm1_low': m1_low,
        'm1_close': m1_close,
        'expiry_price_maps': expiry_price_maps
    }

start_dt = datetime(2026, 4, 29, 0, 0, tzinfo=timezone.utc)
end_dt = datetime(2026, 5, 29, 0, 0, tzinfo=timezone.utc)

print("Pre-mapping data structures...")
eurusd_cache = prepare_symbol_cache("EURUSD", eurusd_m1, eurusd_m5, start_dt, end_dt)
otc_cache = prepare_symbol_cache("EURUSD-OTC", otc_m1, otc_m5, start_dt, end_dt)

# Pre-calculate swings and levels for swing_window in (2, 3)
precomputed_swings = {}
for sw in [2, 3]:
    # EURUSD
    sh_eur, sl_eur = find_swings(eurusd_m5, swing_window=sw)
    res_eur, sup_eur, tr_eur = precompute_levels_and_trends(eurusd_m5, sh_eur, sl_eur)
    # OTC
    sh_otc, sl_otc = find_swings(otc_m5, swing_window=sw)
    res_otc, sup_otc, tr_otc = precompute_levels_and_trends(otc_m5, sh_otc, sl_otc)
    
    precomputed_swings[sw] = {
        'EURUSD': (res_eur, sup_eur, tr_eur),
        'EURUSD-OTC': (res_otc, sup_otc, tr_otc)
    }

def run_simulation_fast(cache, swing_data, config):
    ref_timestamps = cache['ref_timestamps']
    m1_pos_mapping = cache['m1_pos_mapping']
    m5_loc_mapping = cache['m5_loc_mapping']
    m1_open = cache['m1_open']
    m1_high = cache['m1_high']
    m1_low = cache['m1_low']
    m1_close = cache['m1_close']
    expiry_prices = cache['expiry_price_maps'][config['expiry_minutes']]
    
    resistances, supports, trends = swing_data
    
    trades = []
    active_trade = None
    
    for i in range(len(ref_timestamps)):
        timestamp = ref_timestamps[i]
        
        # Settle active trade
        if active_trade is not None:
            expiry_time = active_trade['expiry_time']
            if timestamp >= expiry_time:
                exit_price = expiry_prices[active_trade['ref_idx']]
                if exit_price is not None:
                    won = False
                    if active_trade['direction'] == 'CALL':
                        won = exit_price > active_trade['entry_price']
                    elif active_trade['direction'] == 'PUT':
                        won = exit_price < active_trade['entry_price']
                    trades.append(won)
                active_trade = None
                
        if active_trade is not None:
            continue
            
        m5_idx = m5_loc_mapping[i]
        resistance = resistances[m5_idx]
        support = supports[m5_idx]
        
        if resistance is None or support is None:
            continue
            
        pos_m1 = m1_pos_mapping[i]
        if pos_m1 < 2:
            continue
            
        # Get candles OHLC at pos_m1 - 2 (latest closed M1 candle)
        c_open = m1_open[pos_m1 - 2]
        c_high = m1_high[pos_m1 - 2]
        c_low = m1_low[pos_m1 - 2]
        c_close = m1_close[pos_m1 - 2]
        
        c_body = abs(c_close - c_open)
        lower_wick = min(c_open, c_close) - c_low
        upper_wick = c_high - max(c_open, c_close)
        
        # Session hour filter (GMT+7 hour)
        if config['use_session_filter']:
            gmt7_hour = (timestamp.hour + 7) % 24
            if not ((9 <= gmt7_hour <= 23) or (0 <= gmt7_hour <= 2)):
                continue
                
        trend = 'RANGE'
        if config['use_trend_filter']:
            trend = trends[m5_idx]
            
        # CALL
        if c_low <= support and c_close > support:
            if trend in ('UP', 'RANGE') or not config['use_trend_filter']:
                if lower_wick >= c_body * config['wick_body_ratio'] and (not config['strict_wick'] or lower_wick > upper_wick):
                    active_trade = {
                        'entry_time': timestamp,
                        'expiry_time': timestamp + timedelta(minutes=config['expiry_minutes']),
                        'direction': 'CALL',
                        'entry_price': c_close,
                        'ref_idx': i
                    }
                    continue
                    
        # PUT
        if c_high >= resistance and c_close < resistance:
            if trend in ('DOWN', 'RANGE') or not config['use_trend_filter']:
                if upper_wick >= c_body * config['wick_body_ratio'] and (not config['strict_wick'] or upper_wick > lower_wick):
                    active_trade = {
                        'entry_time': timestamp,
                        'expiry_time': timestamp + timedelta(minutes=config['expiry_minutes']),
                        'direction': 'PUT',
                        'entry_price': c_close,
                        'ref_idx': i
                    }
                    continue
                    
    return trades

# Grid search parameters
configs = []
for swing_w in [2, 3]:
    for expiry in [1, 2, 3, 5]:
        for trend_f in [True, False]:
            for session_f in [True, False]:
                for ratio in [1.0, 1.5, 2.0]:
                    for strict in [True, False]:
                        configs.append({
                            'swing_window': swing_w,
                            'expiry_minutes': expiry,
                            'use_trend_filter': trend_f,
                            'use_session_filter': session_f,
                            'wick_body_ratio': ratio,
                            'strict_wick': strict
                        })

print(f"Total configurations to test: {len(configs)}")

best_overall_wr = 0
best_config = None
results = []

for idx, config in enumerate(configs):
    swing_data_eur = precomputed_swings[config['swing_window']]['EURUSD']
    swing_data_otc = precomputed_swings[config['swing_window']]['EURUSD-OTC']
    
    eur_trades = run_simulation_fast(eurusd_cache, swing_data_eur, config)
    otc_trades = run_simulation_fast(otc_cache, swing_data_otc, config)
    
    total = len(eur_trades) + len(otc_trades)
    if total < 20: # skip config with too few trades
        continue
        
    wins = sum(1 for t in eur_trades if t) + sum(1 for t in otc_trades if t)
    wr = wins / total
    
    results.append((wr, total, config))
    
    if wr > best_overall_wr:
        best_overall_wr = wr
        best_config = config
        print(f"New Best: Win Rate = {wr*100:.2f}% | Trades = {total} | Config = {config}")

print("\n" + "="*80)
print("OPTIMIZATION COMPLETE")
print("="*80)
print(f"Best Win Rate: {best_overall_wr*100:.2f}%")
print(f"Best Config  : {best_config}")
print("="*80)

# Write optimization results to a file for review
with open(PROJECT_ROOT / "logs/optimization_results.json", "w") as f:
    json.dump({
        'best_win_rate': best_overall_wr,
        'best_config': best_config,
        'all_results': sorted([(r[0], r[1], r[2]) for r in results], reverse=True, key=lambda x: x[0])
    }, f, indent=2)
