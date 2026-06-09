"""
Quick Backtest: 3 Days, 4 Pairs - Identify Losing Strategies
Run this script directly to identify losing strategies.
"""
import pandas as pd
import numpy as np
from pathlib import Path

STAKE = 35.0
PAYOUT = 0.85

def load_m5_data(pair):
    """Load M5 CSV data for a pair"""
    path = Path(__file__).parent.parent / "historical_data" / f"history_{pair}_M5.csv"
    if not path.exists():
        path = Path(__file__).parent.parent / "historical_data" / f"history_{pair.replace('-', '_')}_M5.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["timestamp"], index_col="timestamp")
    return df

def backtest_sma_cross(df, fast=5, slow=20):
    df = df.copy()
    df["sma_fast"] = df["close"].rolling(fast).mean()
    df["sma_slow"] = df["close"].rolling(slow).mean()
    df["signal"] = 0
    df.loc[df["sma_fast"] > df["sma_slow"], "signal"] = 1
    df.loc[df["sma_fast"] < df["sma_slow"], "signal"] = -1
    df["position"] = df["signal"].shift(1)
    df["returns"] = df["close"].pct_change() * df["position"]
    total = df["returns"].sum() * 10000
    trades = df["position"].diff().abs().sum()
    return {"return": total, "trades": trades}

def backtest_rsi(df, period=14, oversold=30, overbought=70):
    df = df.copy()
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss.replace(0, 1e-10)
    df["rsi"] = 100 - (100 / (1 + rs))
    df["signal"] = 0
    df.loc[df["rsi"] < oversold, "signal"] = 1
    df.loc[df["rsi"] > overbought, "signal"] = -1
    df["position"] = df["signal"].shift(1)
    df["returns"] = df["close"].pct_change() * df["position"]
    total = df["returns"].sum() * 10000
    trades = df["position"].diff().abs().sum()
    return {"return": total, "trades": trades}

def backtest_macd(df, fast=12, slow=26, signal=9):
    df = df.copy()
    exp1 = df["close"].ewm(span=fast, adjust=False).mean()
    exp2 = df["close"].ewm(span=slow, adjust=False).mean()
    df["macd"] = exp1 - exp2
    df["signal_line"] = df["macd"].ewm(span=signal, adjust=False).mean()
    df["signal"] = 0
    df.loc[df["macd"] > df["signal_line"], "signal"] = 1
    df.loc[df["macd"] < df["signal_line"], "signal"] = -1
    df["position"] = df["signal"].shift(1)
    df["returns"] = df["close"].pct_change() * df["position"]
    total = df["returns"].sum() * 10000
    trades = df["position"].diff().abs().sum()
    return {"return": total, "trades": trades}

def backtest_bollinger(df, period=20, std_dev=2):
    df = df.copy()
    df["sma"] = df["close"].rolling(period).mean()
    df["std"] = df["close"].rolling(period).std()
    df["upper"] = df["sma"] + df["std"] * std_dev
    df["lower"] = df["sma"] - df["std"] * std_dev
    df["signal"] = 0
    df.loc[df["close"] < df["lower"], "signal"] = 1
    df.loc[df["close"] > df["upper"], "signal"] = -1
    df["position"] = df["signal"].shift(1)
    df["returns"] = df["close"].pct_change() * df["position"]
    total = df["returns"].sum() * 10000
    trades = df["position"].diff().abs().sum()
    return {"return": total, "trades": trades}

def backtest_breakout(df, period=20):
    df = df.copy()
    df["high_period"] = df["high"].rolling(period).max()
    df["low_period"] = df["low"].rolling(period).min()
    df["signal"] = 0
    df.loc[df["close"] > df["high_period"].shift(1), "signal"] = 1
    df.loc[df["close"] < df["low_period"].shift(1), "signal"] = -1
    df["position"] = df["signal"].shift(1)
    df["returns"] = df["close"].pct_change() * df["position"]
    total = df["returns"].sum() * 10000
    trades = df["position"].diff().abs().sum()
    return {"return": total, "trades": trades}

def backtest_mean_reversion(df, period=20):
    df = df.copy()
    df["sma"] = df["close"].rolling(period).mean()
    df["signal"] = 0
    df.loc[df["close"] < df["sma"], "signal"] = 1
    df.loc[df["close"] > df["sma"], "signal"] = -1
    df["position"] = df["signal"].shift(1)
    df["returns"] = df["close"].pct_change() * df["position"]
    total = df["returns"].sum() * 10000
    trades = df["position"].diff().abs().sum()
    return {"return": total, "trades": trades}

def backtest_stochastic(df, period=14, oversold=20, overbought=80):
    df = df.copy()
    low_min = df["low"].rolling(period).min()
    high_max = df["high"].rolling(period).max()
    df["k"] = 100 * ((df["close"] - low_min) / (high_max - low_min).replace(0, 1e-10))
    df["signal"] = 0
    df.loc[df["k"] < oversold, "signal"] = 1
    df.loc[df["k"] > overbought, "signal"] = -1
    df["position"] = df["signal"].shift(1)
    df["returns"] = df["close"].pct_change() * df["position"]
    total = df["returns"].sum() * 10000
    trades = df["position"].diff().abs().sum()
    return {"return": total, "trades": trades}

BACKTEST_FUNCS = {
    "SMA_Cross_5_20": backtest_sma_cross,
    "RSI_14": backtest_rsi,
    "MACD_12_26_9": backtest_macd,
    "Bollinger_20_2": backtest_bollinger,
    "Breakout_20": backtest_breakout,
    "MeanReversion_20": backtest_mean_reversion,
    "Stochastic_14": backtest_stochastic,
}

def main():
    pairs = ["EURGBP_OTC", "EURUSD_OTC", "GBPUSD_OTC", "USDJPY_OTC"]
    all_results = {}
    losing_strategies = []
    
    for pair in pairs:
        print(f"\n{'='*60}")
        print(f"Pair: {pair} (M5)")
        print(f"{'='*60}")
        df = load_m5_data(pair)
        if df is None:
            print("  No data found!")
            continue
        
        # Take last 3 days (approx 864 M5 candles)
        df_3d = df.tail(864).copy()
        print(f"  Data range: {df_3d.index[0]} -> {df_3d.index[-1]}")
        print(f"  Total M5 candles: {len(df_3d)}")
        
        all_results[pair] = {}
        for strat_key, strat_func in BACKTEST_FUNCS.items():
            try:
                res = strat_func(df_3d)
                all_results[pair][strat_key] = res
                ret = res["return"]
                trades = res["trades"]
                status = "+" if ret > 0 else "X"
                print(f"  {strat_key:22} | Return: {ret:+8.2f} pips | Trades: {trades:4.0f} | {status}")
                if ret < 0:
                    losing_strategies.append({"pair": pair, "strategy": strat_key, "return": ret, "trades": trades})
            except Exception as e:
                print(f"  {strat_key:22} | ERROR: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY: LOSING STRATEGIES (Avoid these)")
    print(f"{'='*60}")
    losing_strategies.sort(key=lambda x: x["return"])
    for item in losing_strategies:
        print(f"  {item['pair']:12} | {item['strategy']:22} | {item['return']:+8.2f} pips | {item['trades']:4.0f} trades")
    
    print(f"\nTotal losing strategies found: {len(losing_strategies)}")
    
    # Save results
    output_path = Path(__file__).parent.parent / "logs" / "backtest_results.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"results": all_results, "losing_strategies": losing_strategies}, f, indent=2)
    print(f"\nResults saved to: {output_path}")

if __name__ == "__main__":
    main()
