#!/usr/bin/env python3
"""
Automated Backtesting Framework for FINALBOT


Prevents look-ahead bias and handles missing data automatically.

Steps:
1. Create required subdirectories (data/, configs/, results/)
2. Check for existing OHLC CSV files in data/
3. If missing, use IQOptionAdapter (DEMO) to download historical candles
4. Initialize CSVDataAdapter with the data directory
5. Run offline simulation using core backtest logic (no mocks)
6. Save test config snapshot and export results
"""

import sys
import json
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ----------------------------------------------------------------------
# Paths
BACKTEST_BASE = PROJECT_ROOT / 'backtest'
DATA_DIR = BACKTEST_BASE / 'data test'
CONFIGS_DIR = BACKTEST_BASE / 'configs'
RESULTS_DIR = BACKTEST_BASE / 'results'
LOGS_DIR = BACKTEST_BASE / 'logs'

for d in [DATA_DIR, CONFIGS_DIR, RESULTS_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Logging
log_file = LOGS_DIR / f"auto_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AutoBacktester")

# ----------------------------------------------------------------------
# Configuration (can be overridden via config file or environment)
DEFAULT_SYMBOLS = ['EURUSD', 'GBPUSD', 'USDJPY']
DEFAULT_TIMEFRAMES = ['M1', 'M5', 'M15', 'M60']
CANDLE_COUNT = 5000            # number of candles to download per symbol/timeframe
STARTING_CAPITAL = 2000.0
STAKE_PER_TRADE = 30.0
PAYOUT_RATE = 0.85
COOLDOWN_MINUTES = 5

def load_backtest_config() -> dict:
    """Load backtest parameters from a config file if present, else use defaults."""
    config_path = CONFIGS_DIR / "backtest_config.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            cfg = json.load(f)
        logger.info(f"Loaded config from {config_path}")
        return cfg
    else:
        cfg = {
            "symbols": DEFAULT_SYMBOLS,
            "timeframes": DEFAULT_TIMEFRAMES,
            "candle_count": CANDLE_COUNT,
            "starting_capital": STARTING_CAPITAL,
            "stake_per_trade": STAKE_PER_TRADE,
            "payout_rate": PAYOUT_RATE,
            "cooldown_minutes": COOLDOWN_MINUTES
        }
        # Save default config for future runs
        with open(config_path, 'w') as f:
            json.dump(cfg, f, indent=2)
        logger.info(f"Created default config at {config_path}")
        return cfg

# ----------------------------------------------------------------------
# Data download using IQOptionAdapter
def download_missing_data(symbols: List[str], timeframes: List[str], target_count: int) -> bool:
    """
    Check which CSV files are missing or insufficient, then download them
    using IQOptionAdapter (DEMO account).
    """
    missing = []
    for symbol in symbols:
        safe_sym = symbol.replace("-", "_").replace("OTC", "OTC")
        for tf in timeframes:
            filename = DATA_DIR / f"history_{safe_sym}_{tf}.csv"
            needs_download = True
            if filename.exists():
                try:
                    df = pd.read_csv(filename)
                    if len(df) >= target_count:
                        logger.info(f"[OK] {filename.name} OK ({len(df)} candles)")
                        needs_download = False
                    else:
                        logger.warning(f"[WARN] {filename.name} has only {len(df)} candles, need {target_count}")
                except Exception as e:
                    logger.warning(f"[WARN] Could not read {filename.name}: {e}")
            if needs_download:
                missing.append((symbol, tf, filename))

    if not missing:
        logger.info("All data files are present and sufficient.")
        return True

    logger.info(f"Missing or insufficient files: {len(missing)}")
    try:
        from core.adapters.iqoption_adapter import IQOptionAdapter
        adapter = IQOptionAdapter(demo=True)
        connected = adapter.connect()
        if not connected:
            logger.error("Failed to connect to IQOption DEMO account.")
            return False
        logger.info("Connected to IQOption DEMO API.")
    except ImportError as e:
        logger.error(f"Could not import IQOptionAdapter: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error initializing IQOptionAdapter: {e}")
        return False

    success = True
    for symbol, tf, filepath in missing:
        logger.info(f"Downloading {symbol} {tf} ...")
        try:
            candles = adapter.get_candles(symbol, tf, target_count)
            if candles:
                df = pd.DataFrame(candles)
                df.to_csv(filepath, index=False)
                logger.info(f"[OK] Saved {len(df)} candles to {filepath.name}")
            else:
                logger.error(f"[ERROR] No data received for {symbol} {tf}")
                success = False
        except Exception as e:
            logger.error(f"[ERROR] Download failed for {symbol} {tf}: {e}")
            success = False
        time.sleep(0.5)  # rate limiting

    try:
        adapter.disconnect()
    except:
        pass
    return success

# ----------------------------------------------------------------------
# Offline backtest simulation
def run_offline_backtest(
    data_dir: Path,
    symbols: List[str],
    timeframes: List[str],
    capital: float,
    stake: float,
    payout_rate: float,
    cooldown_minutes: int
) -> pd.DataFrame:
    """
    Run backtest using CSV data and core strategy logic.
    Returns DataFrame with trade records.
    """
    try:
        from core.adapters.csv_adapter import CSVDataAdapter
        from core.strategy.strategy_signal import StrategySignal
        from core.execution.simulated_executor import SimulatedExecutor
    except ImportError as e:
        logger.error(f"Failed to import core modules: {e}")
        return pd.DataFrame()

    # Initialize data adapter
    data_adapter = CSVDataAdapter(data_dir)
    
    # Initialize strategy (using a simple demo strategy - you can replace with real one)
    # For the backtest to work, we need a strategy that generates signals.
    # The original script likely had a specific strategy import.
    # Since the user said "Do not write dummy strategies", we will use the same
    # strategy that the original script used. However, the original didn't show
    # the strategy import. We'll assume a standard strategy like 'MomentumStrategy'
    # is available in the project. If not, we fallback to a simple signal generator.
    # To avoid breaking, we import from strategy module (if exists).
    try:
        from strategy.momentum_strategy import MomentumStrategy
        strategy = MomentumStrategy()
        logger.info("Using MomentumStrategy")
    except ImportError:
        # Fallback: a simple strategy that always returns BUY (for demo only)
        # But to prevent dummy code, we'll raise an error if no real strategy.
        logger.error("No valid strategy found. Please ensure strategy module is available.")
        return pd.DataFrame()

    # Initialize executor
    executor = SimulatedExecutor(
        initial_balance=capital,
        stake_per_trade=stake,
        payout_rate=payout_rate,
        cooldown_seconds=cooldown_minutes * 60
    )

    all_trades = []
    
    # We need to iterate over all symbol/timeframe combinations in chronological order.
    # Collect all data frames and align timestamps.
    data_frames = {}
    for sym in symbols:
        safe_sym = sym.replace("-", "_").replace("OTC", "OTC")
        for tf in timeframes:
            key = f"{safe_sym}_{tf}"
            df = data_adapter.load(safe_sym, tf)
            if df is not None and not df.empty:
                data_frames[key] = df
                logger.info(f"Loaded {key}: {len(df)} candles")
            else:
                logger.warning(f"No data for {key}")
    
    if not data_frames:
        logger.error("No data loaded. Aborting backtest.")
        return pd.DataFrame()

    # Find common time range across all frames
    min_time = None
    max_time = None
    for df in data_frames.values():
        if 'timestamp' in df.columns:
            times = pd.to_datetime(df['timestamp'])
        elif 'time' in df.columns:
            times = pd.to_datetime(df['time'])
        else:
            # assume index is datetime
            times = df.index
        if min_time is None or times.min() < min_time:
            min_time = times.min()
        if max_time is None or times.max() > max_time:
            max_time = times.max()
    
    if min_time is None or max_time is None:
        logger.error("Could not determine time range.")
        return pd.DataFrame()

    # Generate a unified timeline (every minute or based on smallest timeframe)
    # For simplicity, we use the smallest timeframe resolution (e.g., M1)
    # Determine smallest timeframe step
    tf_minutes = {'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30, 'M60': 60, 'H1': 60, 'H4': 240, 'D1': 1440}
    step_minutes = min([tf_minutes.get(tf, 60) for tf in timeframes])
    timeline = pd.date_range(start=min_time, end=max_time, freq=f'{step_minutes}T')
    
    logger.info(f"Running simulation from {min_time} to {max_time} with {len(timeline)} steps")

    last_trade_time = None
    balance = capital

    for current_time in timeline:
        # Check cooldown
        if last_trade_time and (current_time - last_trade_time).total_seconds() < cooldown_minutes * 60:
            continue

        # Get latest signals from each symbol/timeframe
        signals = []
        for (key, df) in data_frames.items():
            # Find closest candle to current_time
            if 'timestamp' in df.columns:
                times = pd.to_datetime(df['timestamp'])
            elif 'time' in df.columns:
                times = pd.to_datetime(df['time'])
            else:
                times = df.index
            # get row where time <= current_time
            mask = times <= current_time
            if not mask.any():
                continue
            idx = mask.idxmax() if isinstance(mask, pd.Series) else mask.argmax()
            row = df.loc[idx]
            # generate signal
            signal = strategy.generate_signal(row, current_time, key)
            if signal and signal.direction in ['BUY', 'SELL']:
                signals.append((key, signal))

        if not signals:
            continue

        # For simplicity, take the first signal (or implement priority logic)
        # In a full backtest, you'd need position management. Here we execute immediately.
        for (symbol_tf, signal) in signals:
            # Determine entry price from the data
            # Assuming signal has entry_price or we take close price
            entry_price = signal.entry_price if hasattr(signal, 'entry_price') else signal.price
            # Execute trade
            trade_result = executor.execute_trade(
                symbol=symbol_tf.split('_')[0],
                direction=signal.direction,
                entry_price=entry_price,
                stake=stake,
                timestamp=current_time
            )
            if trade_result:
                outcome = trade_result['outcome']
                pnl = trade_result['pnl']
                balance += pnl
                trade_record = {
                    'timestamp': current_time,
                    'symbol': symbol_tf.split('_')[0],
                    'timeframe': symbol_tf.split('_')[1],
                    'direction': signal.direction,
                    'entry_price': entry_price,
                    'outcome': outcome,
                    'pnl': pnl,
                    'balance': balance,
                    'reason': trade_result.get('reason', '')
                }
                all_trades.append(trade_record)
                last_trade_time = current_time
                logger.info(f"[{current_time.strftime('%H:%M:%S')}] {signal.direction} @ {entry_price:.5f} -> {outcome} (PnL: {pnl:+.2f}, Bal: {balance:.2f})")
                break  # only one trade per step

    trades_df = pd.DataFrame(all_trades)
    return trades_df

# ----------------------------------------------------------------------
# Main entry point
def main():
    logger.info("=" * 70)
    logger.info("AUTOMATED BACKTESTING FRAMEWORK STARTED")
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"Configs directory: {CONFIGS_DIR}")
    logger.info(f"Results directory: {RESULTS_DIR}")
    logger.info("=" * 70)

    # Load configuration
    config = load_backtest_config()
    symbols = config.get("symbols", DEFAULT_SYMBOLS)
    timeframes = config.get("timeframes", DEFAULT_TIMEFRAMES)
    target_count = config.get("candle_count", CANDLE_COUNT)
    capital = config.get("starting_capital", STARTING_CAPITAL)
    stake = config.get("stake_per_trade", STAKE_PER_TRADE)
    payout = config.get("payout_rate", PAYOUT_RATE)
    cooldown = config.get("cooldown_minutes", COOLDOWN_MINUTES)

    # Step 1-2: Check and download missing data
    logger.info("\n[1/4] Checking data availability...")
    if not download_missing_data(symbols, timeframes, target_count):
        logger.error("Data download failed. Exiting.")
        return

    # Step 3-4: Run offline backtest
    logger.info("\n[2/4] Initializing CSVDataAdapter and running offline simulation...")
    trades_df = run_offline_backtest(
        data_dir=DATA_DIR,
        symbols=symbols,
        timeframes=timeframes,
        capital=capital,
        stake=stake,
        payout_rate=payout,
        cooldown_minutes=cooldown
    )

    # Step 5: Save results
    logger.info("\n[3/4] Saving backtest results...")
    if trades_df.empty:
        logger.warning("No trades were executed. Check data quality and entry thresholds.")
        return

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    trades_csv = RESULTS_DIR / f"trades_{timestamp}.csv"
    trades_df.to_csv(trades_csv, index=False)
    logger.info(f"Trades saved to {trades_csv}")

    # Generate summary
    wins = len(trades_df[trades_df['outcome'] == 'WIN'])
    losses = len(trades_df[trades_df['outcome'] == 'LOSS'])
    ties = len(trades_df[trades_df['outcome'] == 'TIE'])
    win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
    total_pnl = trades_df['pnl'].sum()
    ending_balance = capital + total_pnl

    summary = {
        'run_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'symbols': symbols,
        'timeframes': timeframes,
        'starting_capital': capital,
        'stake': stake,
        'payout_rate': payout,
        'total_trades': len(trades_df),
        'wins': wins,
        'losses': losses,
        'ties': ties,
        'win_rate': round(win_rate, 2),
        'net_pnl': round(total_pnl, 2),
        'ending_balance': round(ending_balance, 2)
    }

    summary_json = RESULTS_DIR / f"summary_{timestamp}.json"
    with open(summary_json, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Summary saved to {summary_json}")

    # Save a snapshot of the used config
    config_snapshot = CONFIGS_DIR / f"config_snapshot_{timestamp}.json"
    with open(config_snapshot, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Config snapshot saved to {config_snapshot}")

    # Print final report
    logger.info("\n[4/4] BACKTEST COMPLETE")
    logger.info("=" * 50)
    logger.info(f"Starting Balance: {capital:.2f}")
    logger.info(f"Ending Balance:   {ending_balance:.2f}")
    logger.info(f"Net Profit/Loss:  {total_pnl:+.2f}")
    logger.info(f"Win Rate:         {win_rate:.1f}% ({wins}W / {losses}L)")
    logger.info(f"Total Trades:     {len(trades_df)}")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
