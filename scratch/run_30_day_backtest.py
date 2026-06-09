import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd

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

import logging
from runner import BotRunner
from core.data.csv_data_adapter import CSVDataAdapter
from core.orchestration.context_builder import ContextBuilder
from core.engines.engine_registry import EngineRegistry

# Suppress verbose logging
logging.basicConfig(level=logging.ERROR)
for l_name in ["FINALBOT", "runner", "core", "execution", "strategy"]:
    logging.getLogger(l_name).setLevel(logging.ERROR)
    logging.getLogger(l_name).propagate = False

class BypassExecutionGate:
    def evaluate(self, context, recommendation):
        return {'approved': True, 'reason': "Bypass", 'blocked_by': None, 'risk_score': 0}

class BypassExecutionGuard:
    def check(self, signal_data): return {'allowed': True, 'reason': "Bypass", 'veto_code': None}
    def record_trade_opened(self): pass
    def record_trade_result(self, won, profit_loss): pass

def run_backtest_for_symbol(symbol, bot, csv_adapter, start_dt, end_dt):
    print(f"\n⏳ Loading historical M5, M15, M60, and M1 candles for {symbol}...")
    timeframes = ["M1", "M5", "M15", "M60"]
    if not csv_adapter.load_symbol_data(symbol, timeframes):
        return []

    for tf in timeframes:
        df = csv_adapter.dfs[symbol][tf]
        if df.index.tzinfo is None:
            df.index = df.index.tz_localize(timezone.utc)
        csv_adapter.dfs[symbol][tf] = df

    m5_df = csv_adapter.dfs[symbol]["M5"]
    ref_timestamps = m5_df.index
    
    valid_indices = [
        i for i, ts in enumerate(ref_timestamps)
        if start_dt <= ts <= end_dt
    ]
    
    if not valid_indices:
        print(f"❌ Error: No M5 data found in the specified window.")
        return []
        
    start_index = min(valid_indices)
    end_index = max(valid_indices)
    
    trade_history = []
    initial_balance = 2000.0
    balance = initial_balance
    
    print(f"🔄 Running simulation for {symbol} ({len(valid_indices)} M5 bars)...")
    
    # Loop M5 ticks
    for i in range(start_index, end_index + 3):
        if i >= len(ref_timestamps):
            break
        timestamp = ref_timestamps[i]
        
        # A. Settle active expired trades (5 minutes = option expiry duration)
        active_trades = list(bot.order_manager.active_trades.items())
        for order_id, trade in active_trades:
            if trade.symbol == symbol and timestamp >= trade.entry_time + timedelta(minutes=5):
                if timestamp in m5_df.index:
                    exit_price = float(m5_df.loc[timestamp, "close"])
                    won = False
                    if trade.direction == 'CALL':
                        won = exit_price > trade.entry_price
                    elif trade.direction == 'PUT':
                        won = exit_price < trade.entry_price
                        
                    pnl = trade.amount * 0.85 if won else -trade.amount
                    balance += pnl
                    
                    bot.order_manager.close_trade(
                        order_id=order_id,
                        exit_price=exit_price,
                        pnl=pnl,
                        notes=f"Settle at {timestamp.isoformat()}"
                    )
                    
                    trade_record = {
                        'timestamp': trade.entry_time.isoformat(),
                        'symbol': symbol,
                        'direction': trade.direction,
                        'entry_price': trade.entry_price,
                        'exit_price': exit_price,
                        'won': won,
                        'pnl': pnl,
                        'balance': balance,
                        'strategy': trade.notes
                    }
                    trade_history.append(trade_record)

        # B. Set simulated clock cursor
        csv_adapter.set_simulated_time(timestamp)
        
        # C. Prevent duplicate trades on the same symbol
        if bot.order_manager.get_active_trades(symbol):
            continue
            
        # D. Run bot pipeline
        result = bot.run_single_cycle(symbol)
        
        if result.get('executed') and result.get('order_id'):
            order_id = result['order_id']
            if order_id in bot.order_manager.active_trades:
                trade = bot.order_manager.active_trades[order_id]
                trade.entry_time = timestamp
                trade.notes = result.get('strategy', 'unknown')
                
    return trade_history

def main():
    os.chdir(str(PROJECT_ROOT))
    
    # 30 days: 2026-04-29 to 2026-05-29
    start_dt = datetime(2026, 4, 29, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 5, 29, 0, 0, tzinfo=timezone.utc)
    
    csv_adapter = CSVDataAdapter(data_dir="historical_data")
    
    bot = BotRunner(
        symbols=["EURUSD", "EURUSD-OTC"],
        capital=2000.0,
        use_mock=True,
        account_type="PRACTICE"
    )
    
    # Speed Optimization: Clear engines registry
    bot.engine_registry = EngineRegistry()
    bot.context_builder = ContextBuilder(bot.engine_registry)
    bot.intelligence_pipeline.context_builder = bot.context_builder
    
    bot.bot_mode = 'TRADE'
    bot.data_adapter = csv_adapter
    bot.executor.use_mock = True
    bot.use_mock = True
    bot.execution_gate = BypassExecutionGate()
    bot.intelligence_pipeline.execution_gate = bot.execution_gate
    bot.execution_guard = BypassExecutionGuard()
    bot.position_sizer.calculate = lambda confidence=None: 35.0
    
    print("="*80)
    print("🚀 FINALBOT 30-DAY HIGH-SPEED OFFLINE BACKTEST")
    print("="*80)
    print(f"Period              : 2026-04-29 to 2026-05-29 (30 Days)")
    print(f"Active Strategy     : Rejection 5m PA (11-Step Price Action Sequence)")
    print("="*80)
    
    # Run backtest for both symbols
    eurusd_trades = run_backtest_for_symbol("EURUSD", bot, csv_adapter, start_dt, end_dt)
    otc_trades = run_backtest_for_symbol("EURUSD-OTC", bot, csv_adapter, start_dt, end_dt)
    
    all_trades = eurusd_trades + otc_trades
    
    print("\n" + "="*80)
    print("📊 30-DAY BACKTEST SUMMARY REPORT")
    print("="*80)
    
    for symbol, trades_list in [("EURUSD", eurusd_trades), ("EURUSD-OTC", otc_trades)]:
        total = len(trades_list)
        print(f"\nAsset: {symbol}")
        print(f"  Total Trades : {total}")
        if total > 0:
            wins = sum(1 for t in trades_list if t['won'])
            losses = total - wins
            wr = (wins / total) * 100
            pnl = sum(t['pnl'] for t in trades_list)
            print(f"  Wins         : {wins} 🟢")
            print(f"  Losses       : {losses} 🔴")
            print(f"  Win Rate     : {wr:.2f}%")
            print(f"  Net PnL      : {pnl:+.2f} THB")
        else:
            print("  No trades triggered.")
            
    print("\n" + "="*80)
    total_overall = len(all_trades)
    print(f"Overall Total Trades : {total_overall}")
    if total_overall > 0:
        wins = sum(1 for t in all_trades if t['won'])
        losses = total_overall - wins
        wr = (wins / total_overall) * 100
        pnl = sum(t['pnl'] for t in all_trades)
        print(f"Overall Wins         : {wins} 🟢")
        print(f"Overall Losses       : {losses} 🔴")
        print(f"Overall Win Rate     : {wr:.2f}%")
        print(f"Overall Net PnL      : {pnl:+.2f} THB")
    print("="*80)
    
    # Save the output files
    output_dir = Path("C:/Users/Administrator/Downloads/TEST")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / "backtest_with_outcomes.json", "w", encoding="utf-8") as f:
        json.dump(all_trades, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
