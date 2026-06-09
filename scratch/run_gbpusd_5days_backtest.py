import sys
import os
import codecs
import json
import uuid
import math
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd

# Add project root to path
PROJECT_ROOT = Path("c:/Users/Administrator/Downloads/BOT_FINALBOT/BOT_FINALBOT")
sys.path.insert(0, str(PROJECT_ROOT))

# Safe stream wrapper
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

# Suppress verbose logging
logging.basicConfig(level=logging.ERROR)
for l_name in ["FINALBOT", "runner", "core", "execution", "strategy"]:
    logging.getLogger(l_name).setLevel(logging.ERROR)

class BypassExecutionGate:
    def evaluate(self, context, recommendation):
        return {
            'approved': True,
            'reason': "Bypass for backtest",
            'blocked_by': None,
            'risk_score': 0
        }

class BypassExecutionGuard:
    def check(self, signal_data):
        return {'allowed': True, 'reason': "Bypass for backtest", 'veto_code': None}
    def record_trade_opened(self):
        pass
    def record_trade_result(self, won, profit_loss):
        pass

def main():
    symbol = "GBPUSD"
    csv_adapter = CSVDataAdapter(data_dir="historical_data")
    timeframes = ["M1", "M5", "M15", "M60"]
    
    if not csv_adapter.load_symbol_data(symbol, timeframes):
        print("❌ Error: Failed to load CSV data files.")
        return
        
    for tf in timeframes:
        df = csv_adapter.dfs[symbol][tf]
        if df.index.tzinfo is None:
            df.index = df.index.tz_localize(timezone.utc)
        else:
            df.index = df.index.tz_convert(timezone.utc)
        csv_adapter.dfs[symbol][tf] = df
        
    from strategy.trend_following.ema_crossover import EMACrossoverStrategy

    all_strategies = [
        EMACrossoverStrategy(),
    ]
    
    bot = BotRunner(
        symbols=[symbol],
        capital=2000.0,
        use_mock=True,
        account_type="PRACTICE"
    )
    
    bot.bot_mode = 'TRADE'
    bot.data_adapter = csv_adapter
    bot.executor.use_mock = True
    bot.use_mock = True
    bot.execution_gate = BypassExecutionGate()
    bot.intelligence_pipeline.execution_gate = bot.execution_gate
    bot.execution_guard = BypassExecutionGuard()
    
    bot.active_strategies = all_strategies
    bot.strategies = all_strategies
    bot.intelligence_pipeline.strategies = all_strategies
    
    bot.position_sizer.calculate = lambda confidence=None: 35.0
    
    m1_df = csv_adapter.dfs[symbol]["M1"]
    ref_timestamps = m1_df.index
    
    # --- 5 DAYS (Monday May 18 to Friday May 22) ---
    start_dt = datetime(2026, 5, 17, 17, 0, tzinfo=timezone.utc) # May 18 00:00 ICT
    end_dt = datetime(2026, 5, 22, 16, 55, tzinfo=timezone.utc)   # May 22 23:55 ICT
    
    valid_indices = [
        i for i, ts in enumerate(ref_timestamps)
        if start_dt <= ts <= end_dt
    ]
    
    if not valid_indices:
        print("❌ Error: No M1 historical data found for specified window.")
        return
        
    start_index = min(valid_indices)
    end_index = max(valid_indices)
    
    payout_rate = 0.85
    balance = 2000.0
    
    state_transitions = []
    trade_logs = []
    current_state = None
    
    print(f"\n🔄 Starting 5-DAY backtest on {symbol} (May 18 to May 22)...")
    
    for i in range(start_index, end_index + 10):
        if i >= len(ref_timestamps):
            break
        timestamp = ref_timestamps[i]
        ict_time = timestamp + timedelta(hours=7)
        
        active_trades = list(bot.order_manager.active_trades.items())
        for order_id, trade in active_trades:
            expiry_minutes = 5 if trade.expiry == 'M5' else (2 if trade.expiry == 'M2' else 1)
            
            if timestamp >= trade.entry_time + timedelta(minutes=expiry_minutes):
                exit_price = float(m1_df.loc[timestamp, "close"])
                won = False
                if trade.direction == 'CALL':
                    won = exit_price > trade.entry_price
                elif trade.direction == 'PUT':
                    won = exit_price < trade.entry_price
                    
                pnl = trade.amount * payout_rate if won else -trade.amount
                balance += pnl
                
                bot.order_manager.close_trade(
                    order_id=order_id,
                    exit_price=exit_price,
                    pnl=pnl,
                    notes=f"Settle at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                mae = 0.0
                mfe = 0.0
                try:
                    m1_slice = m1_df.loc[trade.entry_time : timestamp]
                    if not m1_slice.empty:
                        highs = m1_slice['high'].tolist()
                        lows = m1_slice['low'].tolist()
                        if trade.direction == 'CALL':
                            mae = float(max(0.0, trade.entry_price - min(lows)))
                            mfe = float(max(0.0, max(highs) - trade.entry_price))
                        else:
                            mae = float(max(0.0, max(highs) - trade.entry_price))
                            mfe = float(max(0.0, trade.entry_price - min(lows)))
                except:
                    pass
                
                for log in trade_logs:
                    if log['order_id'] == order_id:
                        log['exit_price'] = exit_price
                        log['won'] = won
                        log['pnl'] = pnl
                        log['mae'] = mae
                        log['mfe'] = mfe
                        log['settled'] = True
                        break
        
        csv_adapter.set_simulated_time(timestamp)
        
        candles_dict = {}
        for tf in timeframes:
            count = 300 if tf in ("M1", "M5") else (150 if tf == "M15" else 100)
            candles_dict[tf] = csv_adapter.get_candles(symbol, tf, count)
            
        from core.data.timeframe_sync import TimeframeSync
        synced = TimeframeSync(primary='M1').sync(candles_dict)
        
        for tf in list(synced.keys()):
            if len(synced[tf]) > 1:
                synced[tf] = synced[tf].iloc[:-1]
                
        context = bot.intelligence_pipeline.context_builder.build(symbol, synced, 'M1')
        if context:
            state_dict = context.market_state
            state_name = "UNKNOWN"
            if isinstance(state_dict, dict):
                state_name = state_dict.get('state', 'UNKNOWN').upper()
            elif isinstance(state_dict, str):
                state_name = state_dict.upper()
                
            if state_name != current_state:
                current_state = state_name

        if not bot.order_manager.get_active_trades(symbol) and i <= end_index:
            for strategy in all_strategies:
                try:
                    if not strategy.is_eligible(context):
                        continue
                    
                    res = strategy.evaluate(context)
                    action = res.get('action', 'NO_SETUP')
                    
                    if action in ('CALL', 'PUT') and res.get('block_score', 0.0) < 100.0 and res.get('entry_score', 0.0) >= 51.0:
                        from execution.order_manager import Trade
                        
                        # Single M5 Order
                        order_id = str(uuid.uuid4())[:8] + "_m5"
                        trade = Trade(
                            order_id=order_id,
                            symbol=symbol,
                            direction=action,
                            amount=35.0,
                            entry_price=context.current_price,
                            entry_time=timestamp,
                            expiry='M5',
                            status='pending',
                            notes=strategy.strategy_name
                        )
                        bot.order_manager.active_trades[order_id] = trade
                        
                        trade_logs.append({
                            'order_id': order_id,
                            'timestamp_ict': ict_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'strategy': strategy.strategy_name,
                            'expiry': 'M5',
                            'action': action,
                            'entry_score': res.get('entry_score', 0.0),
                            'block_score': res.get('block_score', 0.0),
                            'entry_price': context.current_price,
                            'exit_price': None,
                            'won': None,
                            'pnl': 0.0,
                            'is_executed': True,
                            'settled': False
                        })
                        
                        # Print dot for progress
                        sys.stdout.write(".")
                        sys.stdout.flush()
                            
                except Exception as e:
                    pass

    report_path = PROJECT_ROOT / "docs" / f"{symbol}_5days_backtest_report.md"
    
    total_trades = sum(1 for t in trade_logs if t['is_executed'] and t['settled'])
    won_trades = sum(1 for t in trade_logs if t['is_executed'] and t['settled'] and t['won'])
    win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0.0
    total_pnl = sum(t['pnl'] for t in trade_logs if t['is_executed'] and t['settled'])
    
    with codecs.open(str(report_path), "w", encoding="utf-8") as f:
        f.write("# REPORT: GBPUSD 5-Day Backtest (May 18 - 22, 2026)\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Executive Summary\n")
        f.write(f"- **Total Trades Executed**: {total_trades}\n")
        f.write(f"- **Wins**: {won_trades}\n")
        f.write(f"- **Losses**: {total_trades - won_trades}\n")
        f.write(f"- **Win Rate**: {win_rate:.2f}%\n")
        f.write(f"- **Total PnL**: {total_pnl:+.2f} THB\n")
        f.write(f"- **Ending Balance**: {2000.0 + total_pnl:.2f} THB\n\n")
        
        f.write("## Detailed Trades Log\n")
        f.write("| Time (ICT) | Expiry | Action | Score | Entry Price | Exit Price | Outcome | PnL |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for t in trade_logs:
            if not t['is_executed']: continue
            outcome_str = "WIN" if t['won'] is True else ("LOSS" if t['won'] is False else "N/A")
            f.write(f"| {t['timestamp_ict']} | {t['expiry']} | {t['action']} | {t['entry_score']:.1f} | {t['entry_price']:.5f} | {t['exit_price']:.5f} | {outcome_str} | {t['pnl']:+.2f} |\n")
            
    print(f"\n✅ Backtest completed. Trades: {total_trades}. Win Rate: {win_rate:.2f}%. Report saved to: docs/{symbol}_5days_backtest_report.md")

if __name__ == "__main__":
    main()
