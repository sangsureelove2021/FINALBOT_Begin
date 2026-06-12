"""
FINALBOT Backtesting Engine

Offline historical backtester that replicates the live bot's core
logic, indicator calculations, and entry/veto gates.
"""

import sys
import os
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path so we can import core and strategy modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Setup directories
BACKTEST_DIR = PROJECT_ROOT / "backtest"
DATA_DIR = BACKTEST_DIR / "data test"
RESULTS_DIR = BACKTEST_DIR / "results"
LOGS_DIR = BACKTEST_DIR / "logs"
CONFIGS_DIR = BACKTEST_DIR / "configs"

for folder in [DATA_DIR, RESULTS_DIR, LOGS_DIR, CONFIGS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Configure logging
log_file = LOGS_DIR / f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Backtester")

def get_session(utc_hour: int) -> str:
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

def calc_dynamic_confidence(direction: str, indicators: dict) -> int:
    score = 30  # Base score = 30 per user request
    is_put = (direction == 'PUT')

    ema5 = indicators.get('ema5', 0)
    ema20 = indicators.get('ema20', 0)
    rsi7 = indicators.get('rsi7', 50)
    rsi14 = indicators.get('rsi14', 50)
    macd = indicators.get('macd', 0)
    macd_signal = indicators.get('macd_signal', 0)
    stoch_k = indicators.get('stoch_k', 50)
    local_support = indicators.get('local_support', 0)
    local_resistance = indicators.get('local_resistance', 0)
    current_price = indicators.get('current_price', 0)
    
    trend_direction = indicators.get('trend_direction', 'NONE')
    market_state = indicators.get('market_state', 'UNKNOWN')

    # EMA5 vs EMA20 alignment (+10)
    if is_put and ema5 < ema20:
        score += 10
    elif not is_put and ema5 > ema20:
        score += 10

    # RSI7 extreme zone (+15 extreme, +7 moderate)
    if is_put and rsi7 > 80:
        score += 15
    elif not is_put and rsi7 < 20:
        score += 15
    elif is_put and rsi7 > 70:
        score += 7
    elif not is_put and rsi7 < 30:
        score += 7

    # RSI14 confirmation (+5)
    if is_put and rsi14 > 65:
        score += 5
    elif not is_put and rsi14 < 35:
        score += 5

    # MACD direction (+10)
    if is_put and macd < macd_signal:
        score += 10
    elif not is_put and macd > macd_signal:
        score += 10

    # Stochastic extreme zone (+10)
    if is_put and stoch_k > 80:
        score += 10
    elif not is_put and stoch_k < 20:
        score += 10

    # Price near resistance/support (+10)
    if current_price > 0:
        if is_put and local_resistance > 0:
            dist_pct = abs(current_price - local_resistance) / local_resistance
            if dist_pct < 0.0005:
                score += 10
        elif not is_put and local_support > 0:
            dist_pct = abs(current_price - local_support) / local_support
            if dist_pct < 0.0005:
                score += 10

    # Trend vs Ranging (+10 / +5)
    if not is_put:
        if trend_direction == 'UP' or 'UPTREND' in market_state:
            score += 10
        elif trend_direction == 'NONE' and market_state == 'RANGING':
            score += 5
    else:
        if trend_direction == 'DOWN' or 'DOWNTREND' in market_state:
            score += 10
        elif trend_direction == 'NONE' and market_state == 'RANGING':
            score += 5

    return min(100, score)

def calc_rsi(prices: pd.Series, period: int) -> float:
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    if len(prices) > period:
        avg_gain = gain.copy()
        avg_loss = loss.copy()
        avg_gain.iloc[period] = gain.iloc[1:period+1].mean()
        avg_loss.iloc[period] = loss.iloc[1:period+1].mean()
        avg_gain = avg_gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
        avg_loss = avg_loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    else:
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        
    rs = avg_gain / avg_loss.replace(0, 1e-10)
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])

def download_historical_candles(api, symbol: str, timeframe: str, target_count: int = 5000) -> Optional[pd.DataFrame]:
    tf_seconds = {'M1': 60, 'M5': 300, 'M15': 900, 'M60': 3600}
    size = tf_seconds.get(timeframe, 300)
    all_candles = []
    end_time = time.time()
    
    logger.info(f"Downloading {target_count} candles for {symbol} ({timeframe}) from broker...")
    
    while len(all_candles) < target_count:
        batch_size = min(1000, target_count - len(all_candles))
        try:
            raw = api.get_candles(symbol, size, batch_size, end_time)
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            break
            
        if not raw or not isinstance(raw, list) or len(raw) == 0:
            logger.warning("No more candles returned from API.")
            break
            
        raw.sort(key=lambda x: x['from'])
        all_candles = raw + all_candles
        
        oldest_ts = raw[0]['from']
        end_time = oldest_ts - 1
        
        logger.info(f"Downloaded batch. Total candles fetched: {len(all_candles)}/{target_count}")
        time.sleep(0.5)
        
    if not all_candles:
        return None
        
    df = pd.DataFrame(all_candles)
    df = df.rename(columns={"max": "high", "min": "low"})
    df["timestamp"] = pd.to_datetime(df["from"], unit="s")
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"])
    return df

def check_and_sync_data(symbols: list, timeframes: list, target_count: int = 5000) -> bool:
    """Check if local CSV files exist and have enough rows. If not, download from IQ Option."""
    settings_file = PROJECT_ROOT / "config" / "settings.json"
    with open(settings_file, "r") as f:
        settings = json.load(f)
        
    creds = settings.get("account", {})
    email = creds.get("iq_email")
    password = creds.get("iq_password")
    
    if not email or not password:
        logger.error("IQ Option credentials not found in settings.json")
        return False
        
    api = None
    connected = False
    
    for symbol in symbols:
        safe_sym = symbol.replace("-OTC", "_OTC")
        for tf in timeframes:
            filename = DATA_DIR / f"history_{safe_sym}_{tf}.csv"
            needs_download = True
            
            if filename.exists():
                try:
                    df = pd.read_csv(filename)
                    if len(df) >= target_count:
                        logger.info(f"[OK] {filename.name} has {len(df)} candles. OK.")
                        needs_download = False
                    else:
                        logger.warning(f"[WARN] {filename.name} has only {len(df)} candles (target {target_count}). Downloading...")
                except Exception as e:
                    logger.error(f"Error reading {filename}: {e}. Will re-download.")
            else:
                logger.warning(f"[WARN] {filename.name} does not exist. Downloading...")
                
            if needs_download:
                if not connected:
                    try:
                        from iqoptionapi.stable_api import IQ_Option
                        logger.info(f"Connecting to IQ Option to download missing data...")
                        api = IQ_Option(email, password)
                        ok, reason = api.connect()
                        if not ok:
                            logger.error(f"Connection failed: {reason}")
                            return False
                        connected = True
                    except Exception as e:
                        logger.error(f"Failed to initialize IQ Option API: {e}")
                        return False
                
                df_new = download_historical_candles(api, symbol, tf, target_count)
                if df_new is not None:
                    df_new.to_csv(filename, index=False)
                    logger.info(f"[SAVE] Saved {len(df_new)} candles to {filename}")
                else:
                    logger.error(f"[ERR] Failed to download candles for {symbol} ({tf})")
                    return False
                    
    return True

def run_backtest():
    logger.info("Starting Offline Backtest Run...")
    
    # 1. Load configuration
    settings_file = PROJECT_ROOT / "config" / "settings.json"
    with open(settings_file, "r") as f:
        settings = json.load(f)
        
    symbols = settings.get("symbols", ["EURUSD-OTC"])
    timeframes = ["M1", "M5", "M15", "M60"]
    capital = settings.get("capital", {}).get("starting_balance", 2000)
    stake = settings.get("capital", {}).get("stake_per_trade", 30)
    payout_rate = 0.85  # Standard payout rate
    
    # Save a snapshot of the current settings to configs folder
    config_snapshot = CONFIGS_DIR / f"settings_snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(config_snapshot, "w") as f_snap:
        json.dump(settings, f_snap, indent=2)
        
    # 2. Check and fetch data
    success = check_and_sync_data(symbols, timeframes, target_count=5000)
    if not success:
        logger.error("Data check or sync failed. Exiting backtester.")
        return
        
    # 3. Setup core engine pipeline
    from main import setup_pipeline
    pipeline = setup_pipeline()
    
    # 4. Initialize CSV Data Adapter
    from core.data.csv_data_adapter import CSVDataAdapter
    adapter = CSVDataAdapter(data_dir=str(DATA_DIR))
    
    # 5. Initialize Cooldown/Throttle system
    class OfflineSignalThrottle:
        def __init__(self, cooldown_minutes: int = 5):
            self.last_signal_time = {}
            self.cooldown_minutes = cooldown_minutes

        def allow(self, symbol: str, action: str, sim_time: datetime) -> bool:
            key = f"{symbol}_{action}"
            if key in self.last_signal_time:
                elapsed = sim_time - self.last_signal_time[key]
                if elapsed < timedelta(minutes=self.cooldown_minutes):
                    return False
            self.last_signal_time[key] = sim_time
            return True

    signal_throttle = OfflineSignalThrottle(cooldown_minutes=5)
    logger.info("OfflineSignalThrottle initialized using simulated time.")
    
    # Results containers
    all_trades = []
    
    for symbol in symbols:
        logger.info(f"[BOT] Processing symbol: {symbol}")
        
        # Load data for all timeframes
        adapter.load_symbol_data(symbol, timeframes)
        
        # Use M5 candles index to iterate the backtest
        m5_df = adapter.dfs[symbol]['M5']
        
        # Warmup period: start from index 200 to ensure indicators are fully calculated
        start_idx = 200
        end_idx = len(m5_df) - 5 # Leave room for 5-minute trade expiry check
        
        if end_idx <= start_idx:
            logger.error(f"Insufficient historical data for {symbol} to run backtest. (Rows: {len(m5_df)})")
            continue
            
        logger.info(f"Backtesting {symbol} from candle {start_idx} to {end_idx} (Total steps: {end_idx - start_idx})")
        
        current_balance = capital
        consecutive_losses = 0
        
        for i in range(start_idx, end_idx):
            current_m5_row = m5_df.iloc[i]
            sim_time = m5_df.index[i]
            
            # Advancing adapter simulation time
            adapter.set_simulated_time(sim_time)
            
            # Retrieve candles up to sim_time
            candles_dict = {}
            for tf in timeframes:
                candles_dict[tf] = adapter.get_candles(symbol, tf, count=300)
                
            # Build context
            context = pipeline.context_builder.build(symbol, candles_dict, 'M1')
            
            # Scorer computations
            context.set_score('confidence', pipeline.confidence_scorer.score(context))
            context.set_score('entry', pipeline.entry_scorer.score(context))
            context.set_score('block', pipeline.block_scorer.score(context))
            context.aggregated_score = context.get_score('confidence')
            
            current_price = getattr(context, 'current_price', 0.0)
            if current_price == 0.0 and not candles_dict['M5'].empty:
                current_price = float(candles_dict['M5']['close'].iloc[-1])
                
            state_str = 'UNKNOWN'
            if context.market_state:
                if isinstance(context.market_state, dict):
                    state_str = context.market_state.get('state', 'UNKNOWN')
                else:
                    state_str = str(context.market_state)
                    
            trend_dir = context.trend.get('direction', 'NONE') if context.trend else 'NONE'
            trend_strength = float(context.trend.get('strength', 0.0) if context.trend else 0.0)
            
            # Indicators for dynamic confidence
            close_prices = candles_dict['M5']['close']
            high_prices = candles_dict['M5']['high']
            low_prices = candles_dict['M5']['low']
            
            ema20 = float(close_prices.ewm(span=20, adjust=False).mean().iloc[-1])
            rsi7 = calc_rsi(close_prices, 7)
            rsi14 = calc_rsi(close_prices, 14)
            
            ema12 = close_prices.ewm(span=12, adjust=False).mean()
            ema26 = close_prices.ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            curr_macd = float(macd_line.iloc[-1])
            curr_sig = float(signal_line.iloc[-1])
            
            ema5 = close_prices.ewm(span=5, adjust=False).mean()
            curr_ema5 = float(ema5.iloc[-1])
            
            k_period = 14
            lowest_low = low_prices.rolling(window=k_period).min()
            highest_high = high_prices.rolling(window=k_period).max()
            stoch_denom = (highest_high - lowest_low).replace(0, 1e-10)
            stoch_k_series = 100 * (close_prices - lowest_low) / stoch_denom
            curr_stoch_k = float(stoch_k_series.iloc[-1])
            
            local_support = float(low_prices.iloc[-10:].min())
            local_resistance = float(high_prices.iloc[-10:].max())
            
            indicators_data = {
                'ema5': curr_ema5,
                'ema20': ema20,
                'rsi7': rsi7,
                'rsi14': rsi14,
                'macd': curr_macd,
                'macd_signal': curr_sig,
                'stoch_k': curr_stoch_k,
                'local_support': local_support,
                'local_resistance': local_resistance,
                'current_price': current_price,
                'trend_direction': trend_dir,
                'market_state': state_str
            }
            
            # Evaluate strategies
            triggered_signals = pipeline._evaluate_strategies(context)
            if not triggered_signals or triggered_signals.get('action') in ('NO_SIGNAL', 'NO_SETUP'):
                continue
                
            action = triggered_signals.get('action')
            strategy_name = triggered_signals.get('strategy_name', 'unknown')
            reason = triggered_signals.get('reason', '')
            
            # M5 direction confirmation
            confirmed = False
            if action == 'CALL':
                if rsi14 > 50 or current_price > ema20 or curr_macd > curr_sig:
                    confirmed = True
            elif action == 'PUT':
                if rsi14 < 50 or current_price < ema20 or curr_macd < curr_sig:
                    confirmed = True
                    
            if not confirmed:
                continue
                
            # Dynamic confidence filtering
            dynamic_conf = calc_dynamic_confidence(action, indicators_data)
            min_conf = pipeline.execution_gate.min_confidence if pipeline.execution_gate else 72
            
            if dynamic_conf < min_conf:
                continue
                
            # Cooldown logic check
            if signal_throttle and not signal_throttle.allow(symbol, action, sim_time):
                continue
                
            # Signal triggered! We place a trade.
            # Entry candle is M5 candle i. Entry price is close of candle i.
            # Expiry is M5 candle i + 1. Exit price is close of candle i + 1.
            next_m5_row = m5_df.iloc[i + 1]
            entry_price = current_m5_row['close']
            exit_price = next_m5_row['close']
            
            outcome = 'LOSS'
            pnl = -stake
            
            if action == 'CALL':
                if exit_price > entry_price:
                    outcome = 'WIN'
                    pnl = stake * payout_rate
                elif exit_price == entry_price:
                    outcome = 'TIE'
                    pnl = 0.0
            elif action == 'PUT':
                if exit_price < entry_price:
                    outcome = 'WIN'
                    pnl = stake * payout_rate
                elif exit_price == entry_price:
                    outcome = 'TIE'
                    pnl = 0.0
                    
            current_balance += pnl
            
            if outcome == 'LOSS':
                consecutive_losses += 1
            else:
                consecutive_losses = 0
                
            trade_record = {
                'timestamp': sim_time.strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': symbol,
                'strategy': strategy_name,
                'action': action,
                'confidence': dynamic_conf,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'outcome': outcome,
                'stake': stake,
                'pnl': pnl,
                'balance': current_balance,
                'market_state': state_str,
                'reason': reason
            }
            all_trades.append(trade_record)
            
            # Already registered in allow() call above
                
            logger.info(f"[{sim_time.strftime('%H:%M:%S')}] {action} on {symbol} via {strategy_name} -> {outcome} (PnL: {pnl:+.2f}, Balance: {current_balance:.2f})")
            
    # Compile and report backtest summary
    if not all_trades:
        logger.warning("No trades were taken during the backtest.")
        return
        
    df_trades = pd.DataFrame(all_trades)
    
    # Save detailed trades sheet to results folder
    result_csv = RESULTS_DIR / f"backtest_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_trades.to_csv(result_csv, index=False)
    logger.info(f"[SAVE] Detailed trades saved to {result_csv}")
    
    total_trades = len(df_trades)
    wins = len(df_trades[df_trades['outcome'] == 'WIN'])
    losses = len(df_trades[df_trades['outcome'] == 'LOSS'])
    ties = len(df_trades[df_trades['outcome'] == 'TIE'])
    win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0
    total_pnl = df_trades['pnl'].sum()
    
    summary = {
        'run_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'capital': capital,
        'stake': stake,
        'total_trades': total_trades,
        'wins': wins,
        'losses': losses,
        'ties': ties,
        'win_rate': round(win_rate, 2),
        'net_pnl': round(total_pnl, 2),
        'ending_balance': round(capital + total_pnl, 2)
    }
    
    summary_file = RESULTS_DIR / f"backtest_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, "w") as f_sum:
        json.dump(summary, f_sum, indent=2)
        
    logger.info("="*50)
    logger.info(f"[REPORT] BACKTEST SUMMARY REPORT")
    logger.info(f"Ending Balance: {summary['ending_balance']:.2f}")
    logger.info(f"Win Rate:       {summary['win_rate']}% ({wins} W / {losses} L)")
    logger.info(f"Total trades:   {total_trades}")
    logger.info(f"Net Profit/Loss: {total_pnl:+.2f}")
    logger.info("="*50)

if __name__ == "__main__":
    run_backtest()
