"""
Fast strategy diagnosis - simplified backtest for quick analysis
Tests each strategy independently on 4 pairs x 3 days
"""
import json
import sys
from datetime import timedelta, timezone
from pathlib import Path
import traceback

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

STAKE = 35.0
PAYOUT = 0.85
BREAKEVEN_WR = 54.05  # at 85% payout

SYMBOLS = ["EURGBP-OTC", "EURUSD-OTC", "GBPUSD-OTC", "USDJPY-OTC"]
DAYS = 3


def load_csv(symbol, tf):
    """Load CSV data directly"""
    for data_dir in ("Active_Pairs_Grabber/historical_data", "historical_data"):
        path = PROJECT_ROOT / data_dir / f"history_{symbol}_{tf}.csv"
        if path.exists():
            df = pd.read_csv(path, parse_dates=["timestamp"], index_col="timestamp")
            if df.index.tzinfo is None:
                df.index = df.index.tz_localize(timezone.utc)
            return df
    return None


def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def calc_rsi(series, period=7):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))


def calc_bb(series, period=20, std_dev=2):
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    return sma, sma + std_dev * std, sma - std_dev * std


def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = calc_ema(series, fast)
    ema_slow = calc_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calc_ema(macd_line, signal)
    return macd_line, signal_line


def calc_stoch(high, low, close, k_period=14, d_period=3):
    lowest_low = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low).replace(0, 1e-10)
    d = k.rolling(d_period).mean()
    return k, d


def calc_atr(high, low, close, period=14):
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def find_sr_levels(high, low, close, lookback=50):
    """Simple S/R detection"""
    recent = close.iloc[-lookback:]
    levels = []
    for i in range(2, len(recent) - 2):
        if recent.iloc[i] > recent.iloc[i-1] and recent.iloc[i] > recent.iloc[i-2] and \
           recent.iloc[i] > recent.iloc[i+1] and recent.iloc[i] > recent.iloc[i+2]:
            levels.append(("R", float(recent.iloc[i])))
        if recent.iloc[i] < recent.iloc[i-1] and recent.iloc[i] < recent.iloc[i-2] and \
           recent.iloc[i] < recent.iloc[i+1] and recent.iloc[i] < recent.iloc[i+2]:
            levels.append(("S", float(recent.iloc[i])))
    return levels


# ============================================================
# Strategy Functions - return ("CALL", score) or ("PUT", score) or None
# ============================================================

def strat_ema_crossover(m5, idx):
    if idx < 30: return None
    ema8 = calc_ema(m5["close"], 8).iloc[idx-1:idx+1]
    ema21 = calc_ema(m5["close"], 21).iloc[idx-1:idx+1]
    prev_diff = ema8.iloc[0] - ema21.iloc[0]
    curr_diff = ema8.iloc[1] - ema21.iloc[1]
    if prev_diff <= 0 < curr_diff:
        return ("CALL", 70)
    elif prev_diff >= 0 > curr_diff:
        return ("PUT", 70)
    return None


def strat_macd_crossover(m5, idx):
    if idx < 40: return None
    macd, signal = calc_macd(m5["close"])
    prev_diff = macd.iloc[idx-1] - signal.iloc[idx-1]
    curr_diff = macd.iloc[idx] - signal.iloc[idx]
    if prev_diff <= 0 < curr_diff:
        return ("CALL", 68)
    elif prev_diff >= 0 > curr_diff:
        return ("PUT", 68)
    return None


def strat_rsi_extreme(m5, idx):
    if idx < 20: return None
    rsi = calc_rsi(m5["close"], 7)
    r = rsi.iloc[idx]
    p = rsi.iloc[idx-1]
    if p < 25 and r > 25:
        return ("CALL", 72)
    elif p > 75 and r < 75:
        return ("PUT", 72)
    return None


def strat_bb_rsi(m5, idx):
    if idx < 25: return None
    close = m5["close"].iloc[idx]
    sma, upper, lower = calc_bb(m5["close"])
    rsi = calc_rsi(m5["close"], 7)
    r = rsi.iloc[idx]
    if close <= lower.iloc[idx] and r < 30:
        return ("CALL", 75)
    elif close >= upper.iloc[idx] and r > 70:
        return ("PUT", 75)
    return None


def strat_pin_bar(m5, idx):
    if idx < 5: return None
    o = m5["open"].iloc[idx]
    h = m5["high"].iloc[idx]
    l = m5["low"].iloc[idx]
    c = m5["close"].iloc[idx]
    body = abs(c - o)
    rng = h - l
    if rng < 1e-8: return None
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    
    # Bullish pin bar
    if lower_wick > body * 2 and lower_wick > upper_wick * 2 and lower_wick > rng * 0.6:
        return ("CALL", 70)
    # Bearish pin bar
    if upper_wick > body * 2 and upper_wick > lower_wick * 2 and upper_wick > rng * 0.6:
        return ("PUT", 70)
    return None


def strat_engulfing(m5, idx):
    if idx < 2: return None
    o1, c1 = m5["open"].iloc[idx-1], m5["close"].iloc[idx-1]
    o2, c2 = m5["open"].iloc[idx], m5["close"].iloc[idx]
    body1 = abs(c1 - o1)
    body2 = abs(c2 - o2)
    # Bullish engulfing
    if c1 < o1 and c2 > o2 and c2 > o1 and o2 < c1 and body2 > body1:
        return ("CALL", 68)
    # Bearish engulfing
    if c1 > o1 and c2 < o2 and c2 < o1 and o2 > c1 and body2 > body1:
        return ("PUT", 68)
    return None


def strat_stoch_cross(m5, idx):
    if idx < 20: return None
    k, d = calc_stoch(m5["high"], m5["low"], m5["close"])
    k_curr, d_curr = k.iloc[idx], d.iloc[idx]
    k_prev, d_prev = k.iloc[idx-1], d.iloc[idx-1]
    if k_prev < d_prev and k_curr > d_curr and k_curr < 25:
        return ("CALL", 68)
    elif k_prev > d_prev and k_curr < d_curr and k_curr > 75:
        return ("PUT", 68)
    return None


def strat_sr_rejection(m5, idx):
    if idx < 55: return None
    levels = find_sr_levels(m5["high"].iloc[:idx], m5["low"].iloc[:idx], m5["close"].iloc[:idx])
    if not levels: return None
    c = m5["close"].iloc[idx]
    h = m5["high"].iloc[idx]
    l = m5["low"].iloc[idx]
    o = m5["open"].iloc[idx]
    atr = calc_atr(m5["high"], m5["low"], m5["close"]).iloc[idx]
    if pd.isna(atr) or atr < 1e-8: return None
    
    for typ, lvl in levels[-10:]:
        dist = abs(c - lvl) / atr
        if dist > 1.5: continue
        # Rejection from resistance
        if typ == "R" and h >= lvl and c < lvl and c < o:
            return ("PUT", 72)
        # Rejection from support
        if typ == "S" and l <= lvl and c > lvl and c > o:
            return ("CALL", 72)
    return None


def strat_compression_breakout(m5, idx):
    if idx < 30: return None
    bb_width = []
    sma, upper, lower = calc_bb(m5["close"])
    for i in range(idx-10, idx+1):
        if i < 0 or i >= len(m5): continue
        w = (upper.iloc[i] - lower.iloc[i]) / sma.iloc[i] if sma.iloc[i] > 0 else 0
        bb_width.append(w)
    if len(bb_width) < 11: return None
    
    avg_prev = np.mean(bb_width[:-1])
    curr = bb_width[-1]
    
    # Squeeze then expansion
    if curr > avg_prev * 1.5 and avg_prev < 0.003:
        c = m5["close"].iloc[idx]
        if c > upper.iloc[idx]:
            return ("CALL", 72)
        elif c < lower.iloc[idx]:
            return ("PUT", 72)
    return None


def strat_triple_confluence(m5, idx):
    if idx < 40: return None
    ema8 = calc_ema(m5["close"], 8).iloc[idx]
    ema21 = calc_ema(m5["close"], 21).iloc[idx]
    ema50 = calc_ema(m5["close"], 50).iloc[idx]
    rsi = calc_rsi(m5["close"], 7).iloc[idx]
    macd_line, signal_line = calc_macd(m5["close"])
    macd_val = macd_line.iloc[idx]
    signal_val = signal_line.iloc[idx]
    
    # Bullish: all aligned
    if ema8 > ema21 > ema50 and rsi > 50 and macd_val > signal_val:
        return ("CALL", 72)
    elif ema8 < ema21 < ema50 and rsi < 50 and macd_val < signal_val:
        return ("PUT", 72)
    return None


def strat_ema_ribbon(m5, idx):
    if idx < 55: return None
    ema8 = calc_ema(m5["close"], 8).iloc[idx]
    ema13 = calc_ema(m5["close"], 13).iloc[idx]
    ema21 = calc_ema(m5["close"], 21).iloc[idx]
    ema34 = calc_ema(m5["close"], 34).iloc[idx]
    ema55 = calc_ema(m5["close"], 55).iloc[idx]
    c = m5["close"].iloc[idx]
    
    if c > ema8 > ema13 > ema21 > ema34 > ema55:
        return ("CALL", 70)
    elif c < ema8 < ema13 < ema21 < ema34 < ema55:
        return ("PUT", 70)
    return None


STRATEGIES = {
    "ema_crossover": strat_ema_crossover,
    "macd_crossover": strat_macd_crossover,
    "rsi_extreme_bounce": strat_rsi_extreme,
    "bb_rsi_confluence": strat_bb_rsi,
    "pin_bar_scalper": strat_pin_bar,
    "engulfing_scalper": strat_engulfing,
    "stochastic_crossover": strat_stoch_cross,
    "sr_fakeout_rejection": strat_sr_rejection,
    "compression_breakout": strat_compression_breakout,
    "triple_confluence": strat_triple_confluence,
    "ema_ribbon_momentum": strat_ema_ribbon,
}


def run_backtest(symbol, days):
    """Run backtest for one symbol across all strategies"""
    m5 = load_csv(symbol, "M5")
    m1 = load_csv(symbol, "M1")
    
    if m5 is None or m1 is None:
        return {"error": f"No data for {symbol}"}
    
    end_ts = m5.index[-1]
    start_ts = end_ts - timedelta(days=days)
    m5_window = m5.loc[start_ts:end_ts]
    
    results = {}
    
    for strat_name, strat_func in STRATEGIES.items():
        balance = 2000.0
        wins = losses = 0
        open_trade = None
        
        for i in range(len(m5_window)):
            ts = m5_window.index[i]
            # Get global index in m5
            global_idx = m5.index.get_loc(ts)
            
            if open_trade:
                expiry_ts = open_trade["entry_ts"] + timedelta(minutes=5)
                if ts >= expiry_ts:
                    idx_1m = m1.index.searchsorted(expiry_ts, side="right") - 1
                    idx_1m = max(0, min(idx_1m, len(m1) - 1))
                    exit_price = float(m1.iloc[idx_1m]["close"])
                    won = (
                        exit_price > open_trade["entry"]
                        if open_trade["action"] == "CALL"
                        else exit_price < open_trade["entry"]
                    )
                    pnl = STAKE * PAYOUT if won else -STAKE
                    balance += pnl
                    if won:
                        wins += 1
                    else:
                        losses += 1
                    open_trade = None
            
            if open_trade:
                continue
            
            try:
                signal = strat_func(m5, global_idx)
                if signal is None:
                    continue
                
                action, score = signal
                if score < 65:  # Minimum entry score
                    continue
                
                # Enter trade at M1 close
                idx_1m = m1.index.searchsorted(ts, side="right") - 1
                idx_1m = max(0, min(idx_1m, len(m1) - 1))
                entry_price = float(m1.iloc[idx_1m]["close"])
                
                open_trade = {
                    "action": action,
                    "entry": entry_price,
                    "entry_ts": ts.to_pydatetime().replace(tzinfo=timezone.utc),
                }
            except Exception:
                continue
        
        total = wins + losses
        results[strat_name] = {
            "trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / total * 100, 2) if total else 0.0,
            "pnl": round(balance - 2000.0, 2),
        }
    
    return results


if __name__ == "__main__":
    all_results = {}
    
    for symbol in SYMBOLS:
        print(f"\n{'='*75}")
        print(f"  {symbol} | {DAYS} days | {STAKE}$ stake | {PAYOUT*100:.0f}% payout")
        print(f"{'='*75}")
        
        results = run_backtest(symbol, DAYS)
        all_results[symbol] = results
        
        if "error" in results:
            print(f"  ERROR: {results['error']}")
            continue
        
        for name, r in sorted(results.items(), key=lambda x: x[1]["pnl"]):
            wr = r["win_rate"]
            pnl = r["pnl"]
            trades = r["trades"]
            if trades == 0:
                flag = "⚫ IDLE"
            elif pnl < -50:
                flag = "🔴 KILL"
            elif pnl < 0:
                flag = "🟠 WEAK"
            elif wr < BREAKEVEN_WR:
                flag = "🟡 LOW_WR"
            else:
                flag = "🟢 OK"
            print(f"  {name:28s} | T:{trades:3d} | WR:{wr:5.1f}% | PnL:{pnl:+8.2f}$ | {flag}")
    
    # Grand summary
    print(f"\n\n{'='*75}")
    print(f"  GRAND SUMMARY (All {len(SYMBOLS)} pairs combined)")
    print(f"{'='*75}")
    
    agg = {}
    for symbol, results in all_results.items():
        if "error" in results:
            continue
        for name, r in results.items():
            if name not in agg:
                agg[name] = {"trades": 0, "wins": 0, "losses": 0, "pnl": 0, "pairs": 0}
            agg[name]["trades"] += r["trades"]
            agg[name]["wins"] += r["wins"]
            agg[name]["losses"] += r["losses"]
            agg[name]["pnl"] += r["pnl"]
            if r["trades"] > 0:
                agg[name]["pairs"] += 1
    
    print(f"  {'Strategy':28s} | {'Trades':>6} | {'WR':>6} | {'Total PnL':>10} | Avg/Pairs | Status")
    print(f"  {'-'*28}-+-{'-'*6}-+-{'-'*6}-+-{'-'*10}-+-{'-'*10}-+-{'-'*8}")
    
    for name, data in sorted(agg.items(), key=lambda x: x[1]["pnl"]):
        wr = round(data["wins"] / data["trades"] * 100, 2) if data["trades"] > 0 else 0
        pnl = data["pnl"]
        pairs = data["pairs"]
        avg = round(pnl / pairs, 2) if pairs > 0 else 0
        if data["trades"] == 0:
            flag = "⚫ IDLE"
        elif pnl < -100:
            flag = "🔴 KILL"
        elif pnl < 0:
            flag = "🟠 WEAK"
        elif wr < BREAKEVEN_WR:
            flag = "🟡 LOW_WR"
        else:
            flag = "🟢 OK"
        print(f"  {name:28s} | {data['trades']:6d} | {wr:5.1f}% | {pnl:+10.2f}$ | {avg:+8.2f}$ | {flag}")
    
    # Save
    out_path = PROJECT_ROOT / "logs" / "strategy_diagnosis.json"
    with open(str(out_path), "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved to: {out_path}")
