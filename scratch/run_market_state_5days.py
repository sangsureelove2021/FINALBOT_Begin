import sys
import os
import codecs
import json
import uuid
from datetime import datetime, timezone, timedelta
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path("c:/Users/Administrator/Downloads/BOT_FINALBOT/BOT_FINALBOT")
sys.path.insert(0, str(PROJECT_ROOT))



import logging
from runner import BotRunner
from core.data.csv_data_adapter import CSVDataAdapter

logging.basicConfig(level=logging.ERROR)
for l_name in ["FINALBOT", "runner", "core", "execution", "strategy"]:
    logging.getLogger(l_name).setLevel(logging.ERROR)

class BypassExecutionGuard:
    def check(self, signal_data):
        return {'allowed': True, 'reason': "Bypass", 'veto_code': None}
    def record_trade_opened(self): pass
    def record_trade_result(self, won, profit_loss): pass

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
        
    from strategy.reversal_strategy.nuclear_binary import NuclearBinaryStrategy

    all_strategies = [
        NuclearBinaryStrategy()
    ]
    
    from core.orchestration.execution_gate import ExecutionGate
    print("Initializing BotRunner...")
    bot = BotRunner(symbols=[symbol], capital=2000.0, use_mock=True, account_type="PRACTICE")
    print("BotRunner initialized.")
    bot.bot_mode = 'TRADE'
    bot.data_adapter = csv_adapter
    bot.execution_gate = ExecutionGate()
    bot.intelligence_pipeline.execution_gate = bot.execution_gate
    bot.execution_guard = BypassExecutionGuard()
    
    bot.active_strategies = all_strategies
    bot.strategies = all_strategies
    bot.intelligence_pipeline.strategies = all_strategies
    bot.position_sizer.calculate = lambda confidence=None: 35.0
    
    m1_df = csv_adapter.dfs[symbol]["M1"]
    ref_timestamps = m1_df.index
    
    # 5 DAYS (Monday May 18 to Friday May 22, 2026)
    start_dt = datetime(2026, 5, 17, 17, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 5, 22, 16, 55, tzinfo=timezone.utc)
    
    valid_indices = [i for i, ts in enumerate(ref_timestamps) if start_dt <= ts <= end_dt]
    if not valid_indices:
        print("❌ Error: No M1 historical data found.")
        return
        
    start_index = min(valid_indices)
    end_index = max(valid_indices)
    
    payout_rate = 0.85
    balance = 2000.0
    
    state_transitions = {}
    trade_logs = []
    current_state = None
    state_counts = {}
    
    print(f"\n🔄 Starting 5-DAY backtest on {symbol} (May 18-22)...")
    
    for i in range(start_index, end_index + 10):
        if i >= len(ref_timestamps): break
        timestamp = ref_timestamps[i]
        ict_time = timestamp + timedelta(hours=7)
        
        # Settle trades
        active_trades = list(bot.order_manager.active_trades.items())
        for order_id, trade in active_trades:
            if timestamp >= trade.entry_time + timedelta(minutes=5):
                exit_price = float(m1_df.loc[timestamp, "close"])
                won = (exit_price > trade.entry_price) if trade.direction == 'CALL' else (exit_price < trade.entry_price)
                pnl = trade.amount * payout_rate if won else -trade.amount
                balance += pnl
                bot.order_manager.close_trade(order_id, exit_price, pnl, "Settled", current_time=timestamp)
                
                for log in trade_logs:
                    if log['order_id'] == order_id:
                        log['exit_price'] = exit_price
                        log['won'] = won
                        log['pnl'] = pnl
                        log['settled'] = True
                        break
        
        csv_adapter.set_simulated_time(timestamp)
        candles_dict = {tf: csv_adapter.get_candles(symbol, tf, 300 if tf in ["M1","M5"] else 150) for tf in timeframes}
            
        from core.data.timeframe_sync import TimeframeSync
        synced = TimeframeSync(primary='M1').sync(candles_dict)
        for tf in list(synced.keys()):
            if len(synced[tf]) > 1: synced[tf] = synced[tf].iloc[:-1]
                
        context = bot.intelligence_pipeline.context_builder.build(symbol, synced, 'M1')
        if context:
            state_dict = context.market_state
            state_name = state_dict.get('state', 'UNKNOWN').upper() if isinstance(state_dict, dict) else (state_dict.upper() if isinstance(state_dict, str) else 'UNKNOWN')
            
            if state_name not in state_counts:
                state_counts[state_name] = 0
            state_counts[state_name] += 1
            
            if state_name != current_state:
                if current_state:
                    state_transitions[ict_time.strftime('%Y-%m-%d %H:%M:%S')] = f"{current_state} -> {state_name}"
                current_state = state_name

        if not bot.order_manager.get_active_trades(symbol) and i <= end_index:
            for strategy in all_strategies:
                try:
                    if not strategy.is_eligible(context): continue
                    res = strategy.evaluate(context)
                    action = res.get('action', 'NO_SETUP')
                    
                    if action in ('CALL', 'PUT') and res.get('block_score', 0.0) < 100.0 and res.get('entry_score', 0.0) >= 51.0:
                        rec = {'action': action, 'strategy': strategy}
                        gate_res = bot.execution_gate.evaluate(context, rec)
                        if gate_res.get('approved', False):
                            order_id = str(uuid.uuid4())[:8] + "_m5"
                            added = bot.order_manager.add_trade(
                                order_id=order_id, symbol=symbol, direction=action,
                                amount=35.0, entry_price=context.current_price,
                                expiry='M5', current_time=timestamp
                            )
                            if added:
                                trade_logs.append({
                                    'order_id': order_id, 'timestamp_ict': ict_time.strftime('%Y-%m-%d %H:%M:%S'),
                                    'strategy': strategy.strategy_name, 'action': action,
                                    'market_state': current_state,
                                    'entry_price': context.current_price, 'exit_price': None, 'won': None, 'pnl': 0.0, 'is_executed': True, 'settled': False
                                })
                                sys.stdout.write(".")
                                sys.stdout.flush()
                except Exception:
                    pass

    report_path = PROJECT_ROOT / "docs" / f"{symbol}_5days_market_state_report.md"
    total_trades = len(trade_logs)
    won_trades = sum(1 for t in trade_logs if t.get('won'))
    win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0.0
    total_pnl = sum(t['pnl'] for t in trade_logs)
    
    with codecs.open(str(report_path), "w", encoding="utf-8") as f:
        f.write("# REPORT: GBPUSD 5-Day Backtest with 14 Strategies & Market State (May 18 - 22, 2026)\n\n")
        f.write("## Market State Data\n")
        f.write("### Time Spent in Each State (Minutes)\n")
        for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"- **{state}**: {count} minutes\n")
            
        f.write("\n## Trading Summary\n")
        f.write(f"- **Total Trades Executed**: {total_trades}\n")
        f.write(f"- **Wins**: {won_trades}\n")
        f.write(f"- **Losses**: {total_trades - won_trades}\n")
        f.write(f"- **Win Rate**: {win_rate:.2f}%\n")
        f.write(f"- **Total PnL**: {total_pnl:+.2f} THB\n\n")
        
        f.write("## Trade Log\n")
        f.write("| Time (ICT) | State | Strategy | Action | Outcome | PnL |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for t in trade_logs:
            outcome = "WIN" if t['won'] else "LOSS"
            f.write(f"| {t['timestamp_ict']} | {t['market_state']} | {t['strategy']} | {t['action']} | {outcome} | {t['pnl']:+.2f} |\n")
            
    print(f"\n✅ Backtest completed. Trades: {total_trades}. Win Rate: {win_rate:.2f}%. Report saved to: docs/{symbol}_5days_market_state_report.md")

if __name__ == "__main__":
    main()
