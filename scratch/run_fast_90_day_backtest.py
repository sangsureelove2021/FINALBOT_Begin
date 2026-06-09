import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd
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

# Import all strategy classes
from strategy.reversal_strategy.rejection_5m_pa import Rejection5mPAStrategy
from strategy.trend_following.ema_crossover import EMACrossoverStrategy
from strategy.trend_following.macd_crossover import MACDCrossoverStrategy
from strategy.reversal_strategy.stochastic_crossover import StochasticCrossoverStrategy
from strategy.reversal_strategy.rsi_reversal import RSIReversalStrategy
from strategy.reversal_strategy.bb_rsi_confluence import BBRSIConfluenceStrategy
from strategy.reversal_strategy.pin_bar_scalper import PinBarScalperStrategy
from strategy.reversal_strategy.engulfing_scalper import EngulfingScalperStrategy
from strategy.reversal_strategy.rsi_extreme_bounce import RSIExtremeBounceStrategy
from strategy.trend_following.ema_ribbon_momentum import EMARibbonMomentumStrategy
from strategy.reversal_strategy.pa_snr_strategy import PriceActionSRStrategy
from strategy.reversal_strategy.sr_fakeout_rejection import SRFakeoutRejectionStrategy
from strategy.trend_following.triple_confluence import TripleConfluenceStrategy
from strategy.compression_breakout.strategy import CompressionBreakoutStrategy

class MockContext:
    def __init__(self, symbol, timestamp, candles):
        self.symbol = symbol
        self.timestamp = timestamp
        self.candles = candles

def write_progress(pct, status="running", results=None):
    progress_file = PROJECT_ROOT / "logs" / "backtest_status.json"
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump({
            "status": status,
            "progress": pct,
            "results": results
        }, f, indent=2, ensure_ascii=False)

def main():
    write_progress(0, "running")
    
    # Load config settings
    settings_path = PROJECT_ROOT / "config" / "settings.json"
    with open(settings_path, "r", encoding="utf-8") as f:
        settings = json.load(f)
        
    symbols = settings.get("symbols", ["EURUSD"])
    active_strat_names = settings.get("active_strategies", ["rejection_5m_pa"])
    
    strategy_mapping = {
        "rejection_5m_pa": Rejection5mPAStrategy,
        "ema_crossover": EMACrossoverStrategy,
        "macd_crossover": MACDCrossoverStrategy,
        "stochastic_crossover": StochasticCrossoverStrategy,
        "rsi_reversal": RSIReversalStrategy,
        "bb_rsi_confluence": BBRSIConfluenceStrategy,
        "pin_bar_scalper": PinBarScalperStrategy,
        "engulfing_scalper": EngulfingScalperStrategy,
        "rsi_extreme_bounce": RSIExtremeBounceStrategy,
        "ema_ribbon_momentum": EMARibbonMomentumStrategy,
        "pa_snr_strategy": PriceActionSRStrategy,
        "sr_fakeout_rejection": SRFakeoutRejectionStrategy,
        "triple_confluence": TripleConfluenceStrategy,
        "compression_breakout": CompressionBreakoutStrategy
    }
    
    strategies = [strategy_mapping[name]() for name in active_strat_names if name in strategy_mapping]
    
    if not strategies:
        print("❌ Error: No active strategies selected.")
        write_progress(100, "error", {"error": "No active strategies selected."})
        return

    # 90-day simulation window (approx. March 1 to May 29, 2026)
    start_dt = datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 5, 29, 0, 0, tzinfo=timezone.utc)
    
    trade_history = []
    symbol_reports = {}
    
    # Process symbol by symbol
    for sym_idx, symbol in enumerate(symbols):
        print(f"⏳ Pre-loading data for {symbol}...")
        
        m1_path = PROJECT_ROOT / f"historical_data/history_{symbol.replace('-', '_')}_M1.csv"
        m5_path = PROJECT_ROOT / f"historical_data/history_{symbol.replace('-', '_')}_M5.csv"
        
        if not m1_path.exists() or not m5_path.exists():
            print(f"⚠️ Warning: CSV files not found for {symbol}. Skipping.")
            continue
            
        m1_df = pd.read_csv(m1_path, index_col='timestamp', parse_dates=True)
        m5_df = pd.read_csv(m5_path, index_col='timestamp', parse_dates=True)
        
        if m1_df.index.tzinfo is None:
            m1_df.index = m1_df.index.tz_localize(timezone.utc)
        if m5_df.index.tzinfo is None:
            m5_df.index = m5_df.index.tz_localize(timezone.utc)
            
        ref_timestamps = m5_df.index[(m5_df.index >= start_dt) & (m5_df.index <= end_dt)]
        if len(ref_timestamps) == 0:
            continue
            
        # Fast array pointers
        m1_times = m1_df.index
        m5_times = m5_df.index
        
        # Pre-cache M1 searchsorted indices
        m1_pos_mapping = [m1_times.searchsorted(ts, side='right') for ts in ref_timestamps]
        m1_close = m1_df['close'].values
        m1_open = m1_df['open'].values
        m1_high = m1_df['high'].values
        m1_low = m1_df['low'].values
        
        active_trades = {} # key: strategy_name -> trade_dict
        sym_trades = []
        
        for i in range(len(ref_timestamps)):
            timestamp = ref_timestamps[i]
            
            # Settle expired trades for each strategy
            for name in list(active_trades.keys()):
                trade = active_trades[name]
                expiry_minutes = 5 if trade['expiry'] == 'M5' else 1
                expiry_time = trade['entry_time'] + timedelta(minutes=expiry_minutes)
                
                if timestamp >= expiry_time:
                    exit_price = None
                    if expiry_time in m1_df.index:
                        exit_price = float(m1_df.loc[expiry_time, 'close'])
                    elif expiry_time in m5_df.index:
                        exit_price = float(m5_df.loc[expiry_time, 'close'])
                    else:
                        closest_idx = m1_times.get_indexer([expiry_time], method='bfill')[0]
                        if closest_idx != -1:
                            exit_price = float(m1_close[closest_idx])
                            
                    if exit_price is not None:
                        won = False
                        if trade['direction'] == 'CALL':
                            won = exit_price > trade['entry_price']
                        elif trade['direction'] == 'PUT':
                            won = exit_price < trade['entry_price']
                            
                        pnl = 30.0 * 0.85 if won else -30.0
                        sym_trades.append({
                            'timestamp': trade['entry_time'].isoformat(),
                            'symbol': symbol,
                            'direction': trade['direction'],
                            'entry_price': trade['entry_price'],
                            'exit_price': exit_price,
                            'won': won,
                            'pnl': pnl,
                            'strategy': name
                        })
                    del active_trades[name]
            
            # Get data slices
            pos_m1 = m1_pos_mapping[i]
            pos_m5 = m5_times.searchsorted(timestamp, side='right')
            
            if pos_m1 < 21 or pos_m5 < 21:
                continue
                
            m1_completed = m1_df.iloc[:pos_m1].iloc[:-1].tail(200)
            m5_completed = m5_df.iloc[:pos_m5].iloc[:-1].tail(200)
            
            candles = {'M1': m1_completed, 'M5': m5_completed}
            context = MockContext(symbol, timestamp, candles)
            
            # Evaluate all active strategies
            for strategy in strategies:
                name = strategy.STRATEGY_NAME
                
                # Prevent duplicate trades for the same strategy on this symbol
                if name in active_trades:
                    continue
                    
                result = strategy.evaluate(context)
                action = result.get('action')
                
                if action in ('CALL', 'PUT'):
                    current_price = float(m1_completed['close'].iloc[-1])
                    active_trades[name] = {
                        'entry_time': timestamp,
                        'direction': action,
                        'entry_price': current_price,
                        'expiry': result.get('expiry', 'M1')
                    }
                    
        # Symbol metrics summary
        total_sym = len(sym_trades)
        wins_sym = sum(1 for t in sym_trades if t['won'])
        losses_sym = total_sym - wins_sym
        wr_sym = (wins_sym / total_sym * 100) if total_sym > 0 else 0.0
        pnl_sym = sum(t['pnl'] for t in sym_trades)
        
        symbol_reports[symbol] = {
            'trades': total_sym,
            'wins': wins_sym,
            'losses': losses_sym,
            'win_rate': f"{wr_sym:.1f}%",
            'pnl': f"{pnl_sym:+.2f} USD"
        }
        
        trade_history.extend(sym_trades)
        
        # Calculate overall progress
        progress_pct = int((sym_idx + 1) / len(symbols) * 90)
        write_progress(progress_pct, "running")

    # Generate final stats
    total_trades = len(trade_history)
    wins = sum(1 for t in trade_history if t['won'])
    losses = total_trades - wins
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
    total_pnl = sum(t['pnl'] for t in trade_history)

    # Strategy stats
    strategy_reports = {}
    for name in active_strat_names:
        strat_trades = [t for t in trade_history if t['strategy'] == name]
        total_st = len(strat_trades)
        wins_st = sum(1 for t in strat_trades if t['won'])
        wr_st = (wins_st / total_st * 100) if total_st > 0 else 0.0
        pnl_st = sum(t['pnl'] for t in strat_trades)
        strategy_reports[name] = {
            'trades': total_st,
            'wins': wins_st,
            'losses': total_st - wins_st,
            'win_rate': f"{wr_st:.1f}%",
            'pnl': f"{pnl_st:+.2f} USD"
        }

    results = {
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'win_rate': f"{win_rate:.2f}%",
        'pnl': f"{total_pnl:+.2f} USD",
        'symbol_report': symbol_reports,
        'strategy_report': strategy_reports
    }
    
    print("\n✅ Simulation loop finished successfully!")
    print(results)
    
    # Save the output files
    output_dir = Path("C:/Users/Administrator/Downloads/TEST")
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "backtest_report_90_days.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    write_progress(100, "completed", results)

if __name__ == "__main__":
    main()
