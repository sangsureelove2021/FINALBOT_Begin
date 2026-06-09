"""
3-Day Backtest: 4 Pairs OTC - Identify Losing Strategies
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
รัน backtest 3 วันล่าสุด 4 คู่เงิน OTC เพื่อหากลยุทธ์ที่ขาดทุน

Usage: python scratch/run_3day_backtest.py
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ============================================================================
# Helper Functions (from m5_binary_core)
# ============================================================================

def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()


def calc_bollinger(close: pd.Series, window: int = 20, std_mult: float = 2.0):
    mid = close.rolling(window).mean()
    std = close.rolling(window).std(ddof=0)
    upper = mid + std_mult * std
    lower = mid - std_mult * std
    return mid, upper, lower


def calc_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3):
    low_min = df["low"].rolling(k_period).min()
    high_max = df["high"].rolling(k_period).max()
    denom = (high_max - low_min).replace(0, 1e-9)
    k = 100 * (df["close"] - low_min) / denom
    d = k.rolling(d_period).mean()
    return k, d


def calc_adx(df: pd.DataFrame, period: int = 14) -> float:
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    up = high.diff()
    down = -low.diff()
    pos_dm = np.where((up > down) & (up > 0), up, 0)
    neg_dm = np.where((down > up) & (down > 0), down, 0)
    pos_di = 100 * pd.Series(pos_dm).ewm(alpha=1/period, adjust=False).mean() / (atr + 1e-9)
    neg_di = 100 * pd.Series(neg_dm).ewm(alpha=1/period, adjust=False).mean() / (atr + 1e-9)
    dx = 100 * (pos_di - neg_di).abs() / (pos_di + neg_di + 1e-9)
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    val = float(adx.iloc[-1])
    return val if not np.isnan(val) else 20.0


def candle_metrics(df: pd.DataFrame) -> Dict[str, float]:
    o, h, l, c = (float(df[x].iloc[-1]) for x in ("open", "high", "low", "close"))
    body = abs(c - o)
    height = h - l
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    return {
        "open": o, "high": h, "low": l, "close": c,
        "body": body, "height": height,
        "upper_wick": upper_wick, "lower_wick": lower_wick,
        "bullish": c > o, "bearish": c < o,
    }


def classify_market_state(df: pd.DataFrame) -> str:
    """Simple market state classification based on ADX"""
    adx = calc_adx(df)
    if adx < 20:
        return "CHOPPY_UNCERTAIN"
    elif 20 <= adx <= 35:
        return "MEAN_REVERSION_ZONE"
    else:
        return "VOLATILITY_EXPANDING"


# ============================================================================
# Strategy Implementations
# ============================================================================

def strategy_ema_crossover(df: pd.DataFrame) -> Dict[str, Any]:
    """EMA 8/21 crossover"""
    state = classify_market_state(df)
    if state == "VOLATILITY_EXPANDING":
        return {"action": "NO_SIGNAL", "reason": "BLOCKED"}
    
    close = df["close"]
    ema8 = close.ewm(span=8, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    
    e8_now, e21_now = float(ema8.iloc[-1]), float(ema21.iloc[-1])
    e8_prev, e21_prev = float(ema8.iloc[-2]), float(ema21.iloc[-2])
    
    adx = calc_adx(df)
    if adx < 18 or adx > 35:
        return {"action": "NO_SIGNAL", "reason": "ADX_OUT_OF_RANGE"}
    
    m = candle_metrics(df)
    atr_val = float(calc_atr(df).iloc[-1])
    
    if m["body"] < 0.12 * atr_val:
        return {"action": "NO_SIGNAL", "reason": "CANDLE_TOO_SMALL"}
    
    if e8_prev <= e21_prev and e8_now > e21_now and m["bullish"]:
        return {"action": "CALL", "entry_score": 75.0}
    elif e8_prev >= e21_prev and e8_now < e21_now and m["bearish"]:
        return {"action": "PUT", "entry_score": 75.0}
    
    return {"action": "NO_SIGNAL", "reason": "NO_CROSSOVER"}


def strategy_macd_crossover(df: pd.DataFrame) -> Dict[str, Any]:
    """MACD signal-line crossover"""
    state = classify_market_state(df)
    if state == "VOLATILITY_EXPANDING":
        return {"action": "NO_SIGNAL", "reason": "BLOCKED"}
    
    close = df["close"]
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal
    
    m_now, s_now = float(macd.iloc[-1]), float(signal.iloc[-1])
    m_prev, s_prev = float(macd.iloc[-2]), float(signal.iloc[-2])
    h_now, h_prev = float(hist.iloc[-1]), float(hist.iloc[-2])
    
    adx = calc_adx(df)
    if adx < 20 or adx > 38:
        return {"action": "NO_SIGNAL", "reason": "ADX_OUT_OF_RANGE"}
    
    m = candle_metrics(df)
    
    if m_prev <= s_prev and m_now > s_now and h_now > h_prev and m["bullish"]:
        return {"action": "CALL", "entry_score": 75.0}
    elif m_prev >= s_prev and m_now < s_now and h_now < h_prev and m["bearish"]:
        return {"action": "PUT", "entry_score": 75.0}
    
    return {"action": "NO_SIGNAL", "reason": "NO_MACD_CROSS"}


def strategy_rsi_reversal(df: pd.DataFrame) -> Dict[str, Any]:
    """RSI(7) reversal from midline stretch"""
    state = classify_market_state(df)
    if state not in ["CHOPPY_UNCERTAIN", "MEAN_REVERSION_ZONE"]:
        return {"action": "NO_SIGNAL", "reason": "BLOCKED"}
    
    rsi = calc_rsi(df["close"], 7)
    r_now, r_prev = float(rsi.iloc[-1]), float(rsi.iloc[-2])
    m = candle_metrics(df)
    
    if r_prev < 32 and r_now > r_prev and r_now < 45 and m["bullish"]:
        return {"action": "CALL", "entry_score": 72.0}
    elif r_prev > 68 and r_now < r_prev and r_now > 55 and m["bearish"]:
        return {"action": "PUT", "entry_score": 72.0}
    
    return {"action": "NO_SIGNAL", "reason": "NO_RSI_REVERSAL"}


def strategy_rsi_extreme_bounce(df: pd.DataFrame) -> Dict[str, Any]:
    """RSI extreme bounce"""
    state = classify_market_state(df)
    if state not in ["CHOPPY_UNCERTAIN", "MEAN_REVERSION_ZONE"]:
        return {"action": "NO_SIGNAL", "reason": "BLOCKED"}
    
    rsi = calc_rsi(df["close"], 14)
    r_now, r_prev = float(rsi.iloc[-1]), float(rsi.iloc[-2])
    m = candle_metrics(df)
    
    if r_prev < 25 and r_now > r_prev and r_now < 40 and m["bullish"]:
        return {"action": "CALL", "entry_score": 78.0}
    elif r_prev > 75 and r_now < r_prev and r_now > 60 and m["bearish"]:
        return {"action": "PUT", "entry_score": 78.0}
    
    return {"action": "NO_SIGNAL", "reason": "NO_EXTREME"}


def strategy_pin_bar_scalper(df: pd.DataFrame) -> Dict[str, Any]:
    """Pin bar at local S/R"""
    state = classify_market_state(df)
    if state not in ["CHOPPY_UNCERTAIN", "MEAN_REVERSION_ZONE"]:
        return {"action": "NO_SIGNAL", "reason": "BLOCKED"}
    
    m = candle_metrics(df)
    if m["height"] <= 0:
        return {"action": "NO_SIGNAL", "reason": "ZERO_HEIGHT"}
    
    body_ratio = m["body"] / m["height"]
    if body_ratio < 0.08:
        return {"action": "NO_SIGNAL", "reason": "DOJI"}
    
    action = "NO_SIGNAL"
    if m["lower_wick"] >= m["body"] * 1.8 and m["upper_wick"] <= m["body"] * 0.6 and m["bullish"]:
        action = "CALL"
    elif m["upper_wick"] >= m["body"] * 1.8 and m["lower_wick"] <= m["body"] * 0.6 and m["bearish"]:
        action = "PUT"
    
    if action == "NO_SIGNAL":
        return {"action": "NO_SIGNAL", "reason": "NO_PIN_BAR"}
    
    rsi3 = float(calc_rsi(df["close"], 3).iloc[-1])
    if action == "CALL" and rsi3 > 35:
        return {"action": "NO_SIGNAL", "reason": "RSI_NOT_EXTREME"}
    if action == "PUT" and rsi3 < 65:
        return {"action": "NO_SIGNAL", "reason": "RSI_NOT_EXTREME"}
    
    local_sup = float(df["low"].iloc[-10:-1].min())
    local_res = float(df["high"].iloc[-10:-1].max())
    
    if action == "CALL":
        if abs(m["low"] - local_sup) / local_sup > 0.0008:
            return {"action": "NO_SIGNAL", "reason": "OUTSIDE_SR"}
    else:
        if abs(m["high"] - local_res) / local_res > 0.0008:
            return {"action": "NO_SIGNAL", "reason": "OUTSIDE_SR"}
    
    return {"action": action, "entry_score": 78.0}


def strategy_engulfing_scalper(df: pd.DataFrame) -> Dict[str, Any]:
    """Engulfing pattern at range boundary"""
    state = classify_market_state(df)
    if state not in ["CHOPPY_UNCERTAIN", "MEAN_REVERSION_ZONE"]:
        return {"action": "NO_SIGNAL", "reason": "BLOCKED"}
    
    prev, curr = df.iloc[-2], df.iloc[-1]
    prev_body = abs(prev["close"] - prev["open"])
    curr_body = abs(curr["close"] - curr["open"])
    
    _, bb_upper, bb_lower = calc_bollinger(df["close"])
    upper, lower = float(bb_upper.iloc[-1]), float(bb_lower.iloc[-1])
    
    bullish_engulf = (
        prev["close"] < prev["open"]
        and curr["close"] > curr["open"]
        and curr["open"] <= prev["close"]
        and curr["close"] >= prev["open"]
        and curr_body > prev_body * 1.1
        and float(curr["low"]) <= lower * 1.0005
    )
    bearish_engulf = (
        prev["close"] > prev["open"]
        and curr["close"] < curr["open"]
        and curr["open"] >= prev["close"]
        and curr["close"] <= prev["open"]
        and curr_body > prev_body * 1.1
        and float(curr["high"]) >= upper * 0.9995
    )
    
    if bullish_engulf:
        return {"action": "CALL", "entry_score": 70.0}
    elif bearish_engulf:
        return {"action": "PUT", "entry_score": 70.0}
    
    return {"action": "NO_SIGNAL", "reason": "NO_ENGULFING"}


def strategy_bb_rsi_confluence(df: pd.DataFrame) -> Dict[str, Any]:
    """Bollinger + RSI confluence"""
    state = classify_market_state(df)
    if state not in ["CHOPPY_UNCERTAIN", "MEAN_REVERSION_ZONE"]:
        return {"action": "NO_SIGNAL", "reason": "BLOCKED"}
    
    close = df["close"]
    rsi = calc_rsi(close, 14)
    rsi_val = float(rsi.iloc[-1])
    rsi_prev = float(rsi.iloc[-2])
    
    _, bb_upper, bb_lower = calc_bollinger(close)
    upper, lower = float(bb_upper.iloc[-1]), float(bb_lower.iloc[-1])
    
    m = candle_metrics(df)
    near_lower = m["low"] <= lower * 1.0003
    near_upper = m["high"] >= upper * 0.9997
    
    if near_lower and rsi_val < 35 and rsi_val > rsi_prev and m["close"] > m["open"]:
        return {"action": "CALL", "entry_score": 72.0}
    elif near_upper and rsi_val > 65 and rsi_val < rsi_prev and m["close"] < m["open"]:
        return {"action": "PUT", "entry_score": 72.0}
    
    return {"action": "NO_SIGNAL", "reason": "NO_CONFLUENCE"}


def strategy_stochastic_crossover(df: pd.DataFrame) -> Dict[str, Any]:
    """Stochastic crossover"""
    state = classify_market_state(df)
    if state not in ["CHOPPY_UNCERTAIN", "MEAN_REVERSION_ZONE"]:
        return {"action": "NO_SIGNAL", "reason": "BLOCKED"}
    
    k, d = calc_stochastic(df)
    k_now, d_now = float(k.iloc[-1]), float(d.iloc[-1])
    k_prev, d_prev = float(k.iloc[-2]), float(d.iloc[-2])
    m = candle_metrics(df)
    
    if k_prev < 20 and k_now > d_now and k_prev <= d_prev and m["bullish"]:
        return {"action": "CALL", "entry_score": 70.0}
    elif k_prev > 80 and k_now < d_now and k_prev >= d_prev and m["bearish"]:
        return {"action": "PUT", "entry_score": 70.0}
    
    return {"action": "NO_SIGNAL", "reason": "NO_STOCHASTIC_CROSS"}


def strategy_compression_breakout(df: pd.DataFrame) -> Dict[str, Any]:
    """Bollinger squeeze breakout"""
    close = df["close"]
    mid, upper, lower = calc_bollinger(close)
    
    bw_now = (float(upper.iloc[-1]) - float(lower.iloc[-1])) / float(mid.iloc[-1])
    bw_prev = (float(upper.iloc[-2]) - float(lower.iloc[-2])) / float(mid.iloc[-2])
    
    # Squeeze: bandwidth contracting
    if bw_now < 0.002 and bw_now < bw_prev:
        m = candle_metrics(df)
        if m["close"] > float(upper.iloc[-1]) and m["bullish"]:
            return {"action": "CALL", "entry_score": 75.0}
        elif m["close"] < float(lower.iloc[-1]) and m["bearish"]:
            return {"action": "PUT", "entry_score": 75.0}
    
    return {"action": "NO_SIGNAL", "reason": "NO_BREAKOUT"}


# ============================================================================
# Backtest Engine
# ============================================================================

STRATEGIES = {
    "ema_crossover": strategy_ema_crossover,
    "macd_crossover": strategy_macd_crossover,
    "rsi_reversal": strategy_rsi_reversal,
    "rsi_extreme_bounce": strategy_rsi_extreme_bounce,
    "pin_bar_scalper": strategy_pin_bar_scalper,
    "engulfing_scalper": strategy_engulfing_scalper,
    "bb_rsi_confluence": strategy_bb_rsi_confluence,
    "stochastic_crossover": strategy_stochastic_crossover,
    "compression_breakout": strategy_compression_breakout,
}

STAKE = 35.0
PAYOUT = 0.85
MIN_CANDLES = 50


def load_data(pair: str) -> pd.DataFrame:
    """Load M5 CSV data"""
    path = project_root / "historical_data" / f"history_{pair}_M5.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["timestamp"], index_col="timestamp")
    return df


def run_backtest(pair: str, df: pd.DataFrame) -> Dict[str, Dict]:
    """Run backtest on all strategies for a pair"""
    # Take last 3 days (~864 M5 candles)
    df_3d = df.tail(864 + MIN_CANDLES).copy()
    
    results = {}
    for strat_name, strat_func in STRATEGIES.items():
        wins = 0
        losses = 0
        no_signals = 0
        total_pnl = 0.0
        
        # Walk-forward: test each candle from index MIN_CANDLES to n-2
        for i in range(MIN_CANDLES, len(df_3d) - 1):
            df_slice = df_3d.iloc[:i+1].copy()
            
            try:
                signal = strat_func(df_slice)
            except Exception:
                no_signals += 1
                continue
            
            if signal["action"] in ["CALL", "PUT"]:
                # Entry price = close of current candle
                entry_price = float(df_slice["close"].iloc[-1])
                # Expiry price = close of next candle (M5 expiry)
                expiry_price = float(df_3d["close"].iloc[i+1])
                
                # Determine win/loss
                if signal["action"] == "CALL":
                    won = expiry_price > entry_price
                else:  # PUT
                    won = expiry_price < entry_price
                
                if won:
                    wins += 1
                    total_pnl += STAKE * PAYOUT
                else:
                    losses += 1
                    total_pnl -= STAKE
            else:
                no_signals += 1
        
        total_trades = wins + losses
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
        
        results[strat_name] = {
            "wins": wins,
            "losses": losses,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "pnl": total_pnl,
            "no_signals": no_signals,
        }
    
    return results


def main():
    pairs = ["EURGBP_OTC", "EURUSD_OTC", "GBPUSD_OTC", "USDJPY_OTC"]
    
    print("=" * 80)
    print("3-DAY BACKTEST: 4 PAIRS OTC - LOSING STRATEGIES DETECTOR")
    print("=" * 80)
    
    all_results = {}
    strategy_totals = {}
    
    for pair in pairs:
        print(f"\n{'='*60}")
        print(f"Pair: {pair} (M5)")
        print(f"{'='*60}")
        
        df = load_data(pair)
        if df is None:
            print("  ❌ No data found!")
            continue
        
        df_3d = df.tail(864).copy()
        print(f"  Data range: {df_3d.index[0]} -> {df_3d.index[-1]}")
        print(f"  Total M5 candles: {len(df_3d)}")
        print()
        
        results = run_backtest(pair, df)
        all_results[pair] = results
        
        # Print results for this pair
        print(f"  {'Strategy':<25} | {'W':<4} | {'L':<4} | {'WR':<6} | {'P/L':<10}")
        print(f"  {'-'*55}")
        
        for strat_name, res in sorted(results.items(), key=lambda x: x[1]["pnl"]):
            wr = f"{res['win_rate']:.1f}%"
            pnl = f"{res['pnl']:+.2f}"
            status = "✅" if res['pnl'] > 0 else "❌" if res['pnl'] < 0 else "➖"
            print(f"  {strat_name:<25} | {res['wins']:<4} | {res['losses']:<4} | {wr:<6} | {pnl:<10} {status}")
            
            # Accumulate totals
            if strat_name not in strategy_totals:
                strategy_totals[strat_name] = {"wins": 0, "losses": 0, "pnl": 0.0, "pairs": 0}
            strategy_totals[strat_name]["wins"] += res["wins"]
            strategy_totals[strat_name]["losses"] += res["losses"]
            strategy_totals[strat_name]["pnl"] += res["pnl"]
            strategy_totals[strat_name]["pairs"] += 1
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY: ALL STRATEGIES (sorted by P/L, worst first)")
    print(f"{'='*80}")
    print(f"{'Strategy':<25} | {'Wins':<6} | {'Losses':<6} | {'WR':<7} | {'Total P/L':<12} | {'Status'}")
    print(f"{'-'*80}")
    
    losing_strategies = []
    for strat_name, totals in sorted(strategy_totals.items(), key=lambda x: x[1]["pnl"]):
        total_trades = totals["wins"] + totals["losses"]
        win_rate = (totals["wins"] / total_trades * 100) if total_trades > 0 else 0.0
        
        if totals["pnl"] < 0:
            status = "❌ AVOID"
            losing_strategies.append({
                "strategy": strat_name,
                "wins": totals["wins"],
                "losses": totals["losses"],
                "win_rate": win_rate,
                "pnl": totals["pnl"]
            })
        elif totals["pnl"] > 0:
            status = "✅ KEEP"
        else:
            status = "➖ NEUTRAL"
        
        print(f"{strat_name:<25} | {totals['wins']:<6} | {totals['losses']:<6} | {win_rate:>5.1f}% | {totals['pnl']:>+10.2f} | {status}")
    
    # Final report
    print(f"\n{'='*80}")
    print("🚨 LOSING STRATEGIES (AVOID THESE)")
    print(f"{'='*80}")
    
    if losing_strategies:
        print(f"\nพบ {len(losing_strategies)} กลยุทธ์ที่ขาดทุน:\n")
        for i, s in enumerate(losing_strategies, 1):
            print(f"  {i}. {s['strategy']}")
            print(f"     - Win Rate: {s['win_rate']:.1f}%")
            print(f"     - Total P/L: {s['pnl']:+.2f} THB")
            print(f"     - Trades: {s['wins']}W / {s['losses']}L")
            print()
    else:
        print("\n✅ ไม่พบกลยุทธ์ที่ขาดทุน! ทุกกลยุทธ์ทำกำไรได้")
    
    # Breakeven analysis
    print(f"\n{'='*80}")
    print("📊 BREAKEVEN ANALYSIS")
    print(f"{'='*80}")
    print(f"  Stake: {STAKE} THB, Payout: {PAYOUT*100}%")
    print(f"  Breakeven Win Rate: {1/(1+PAYOUT)*100:.1f}%")
    print(f"  กลยุทธ์ต้องมี Win Rate > {1/(1+PAYOUT)*100:.1f}% ถึงจะทำกำไร")
    
    # Save results
    import json
    output_path = project_root / "logs" / "backtest_3day_results.json"
    output_path.parent.mkdir(exist_ok=True)
    
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "pairs": pairs,
        "period": "3 days",
        "stake": STAKE,
        "payout": PAYOUT,
        "breakeven_wr": 1/(1+PAYOUT)*100,
        "results": all_results,
        "summary": strategy_totals,
        "losing_strategies": losing_strategies
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_path}")


if __name__ == "__main__":
    main()
