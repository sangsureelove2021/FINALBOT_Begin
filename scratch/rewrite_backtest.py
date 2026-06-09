import os
import codecs

backtest_code = """import sys
import os
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
    
    # --- CHANGED: Use M1 for stepping ---
    m1_df = csv_adapter.dfs[symbol]["M1"]
    ref_timestamps = m1_df.index
    
    # 07/05/2026 from 00:00 to 23:55 ICT (Thai time)
    start_dt = datetime(2026, 5, 6, 17, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 5, 7, 16, 55, tzinfo=timezone.utc)
    
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
    
    print(f"\\n🔄 Starting backtest on {symbol} for May 6, 2026 (M1 Stepping)...")
    
    for i in range(start_index, end_index + 10):
        if i >= len(ref_timestamps):
            break
        timestamp = ref_timestamps[i]
        ict_time = timestamp + timedelta(hours=7)
        
        # A. Settle active expired trades
        active_trades = list(bot.order_manager.active_trades.items())
        for order_id, trade in active_trades:
            # --- CHANGED: Handle dynamic expiry times ---
            expiry_minutes = 3 if trade.expiry == 'M3' else 5
            
            if timestamp >= trade.entry_time + timedelta(minutes=expiry_minutes):
                # --- CHANGED: Use M1 df for exit price ---
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
        
        # B. Set simulated clock cursor
        csv_adapter.set_simulated_time(timestamp)
        
        # Build context to check state transition
        candles_dict = {}
        for tf in timeframes:
            count = 300 if tf in ("M1", "M5") else (150 if tf == "M15" else 100)
            candles_dict[tf] = csv_adapter.get_candles(symbol, tf, count)
            
        from core.data.timeframe_sync import TimeframeSync
        synced = TimeframeSync(primary='M1').sync(candles_dict)
        
        # Slice off the last candle of synced to prevent look-ahead bias
        for tf in list(synced.keys()):
            if len(synced[tf]) > 1:
                synced[tf] = synced[tf].iloc[:-1]
                
        # Build context on M1 instead of M5 because we are evaluating every minute
        context = bot.intelligence_pipeline.context_builder.build(symbol, synced, 'M1')
        if context:
            state_dict = context.market_state
            state_name = "UNKNOWN"
            if isinstance(state_dict, dict):
                state_name = state_dict.get('state', 'UNKNOWN').upper()
            elif isinstance(state_dict, str):
                state_name = state_dict.upper()
                
            if state_name != current_state:
                eligible_strats = []
                for s in all_strategies:
                    if s.is_eligible(context):
                        eligible_strats.append(s.strategy_name)
                
                state_transitions.append({
                    'timestamp_utc': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'timestamp_ict': ict_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'old_state': current_state,
                    'new_state': state_name,
                    'eligible_strategies': eligible_strats
                })
                current_state = state_name
                print(f"[{ict_time.strftime('%H:%M:%S')}] State -> {state_name} | Eligible: {eligible_strats}")

        # D. Run pipeline to evaluate signals
        if not bot.order_manager.get_active_trades(symbol) and i <= end_index:
            for strategy in all_strategies:
                try:
                    if not strategy.is_eligible(context):
                        continue
                    
                    res = strategy.evaluate(context)
                    action = res.get('action', 'NO_SETUP')
                    
                    if action in ('CALL', 'PUT') or res.get('entry_score', 0.0) > 0.0 or res.get('block_score', 0.0) > 0.0:
                        is_executed = False
                        
                        if action in ('CALL', 'PUT') and res.get('block_score', 0.0) < 100.0 and res.get('entry_score', 0.0) >= 51.0 and not bot.order_manager.get_active_trades(symbol):
                            
                            # --- CHANGED: Shoot 2 orders (5M and 3M) ---
                            from execution.order_manager import Trade
                            
                            # Order M5
                            order_id_5m = str(uuid.uuid4())[:8] + "_5m"
                            trade_5m = Trade(
                                order_id=order_id_5m,
                                symbol=symbol,
                                direction=action,
                                amount=35.0,
                                entry_price=context.current_price,
                                entry_time=timestamp,
                                expiry='M5',
                                status='pending',
                                notes=strategy.strategy_name
                            )
                            bot.order_manager.active_trades[order_id_5m] = trade_5m
                            
                            trade_logs.append({
                                'order_id': order_id_5m,
                                'timestamp_ict': ict_time.strftime('%Y-%m-%d %H:%M:%S'),
                                'strategy': strategy.strategy_name,
                                'expiry': 'M5',
                                'action': action,
                                'entry_score': res.get('entry_score', 0.0),
                                'block_score': res.get('block_score', 0.0),
                                'confidence': res.get('strategy_confidence', 0.0),
                                'fail_reason_code': res.get('fail_reason_code'),
                                'entry_price': context.current_price,
                                'exit_price': None,
                                'won': None,
                                'pnl': 0.0,
                                'mae': 0.0,
                                'mfe': 0.0,
                                'is_executed': True,
                                'settled': False,
                                'details': res.get('details', {})
                            })
                            
                            # Order M3
                            order_id_3m = str(uuid.uuid4())[:8] + "_3m"
                            trade_3m = Trade(
                                order_id=order_id_3m,
                                symbol=symbol,
                                direction=action,
                                amount=35.0,
                                entry_price=context.current_price,
                                entry_time=timestamp,
                                expiry='M3',
                                status='pending',
                                notes=strategy.strategy_name
                            )
                            bot.order_manager.active_trades[order_id_3m] = trade_3m
                            
                            trade_logs.append({
                                'order_id': order_id_3m,
                                'timestamp_ict': ict_time.strftime('%Y-%m-%d %H:%M:%S'),
                                'strategy': strategy.strategy_name,
                                'expiry': 'M3',
                                'action': action,
                                'entry_score': res.get('entry_score', 0.0),
                                'block_score': res.get('block_score', 0.0),
                                'confidence': res.get('strategy_confidence', 0.0),
                                'fail_reason_code': res.get('fail_reason_code'),
                                'entry_price': context.current_price,
                                'exit_price': None,
                                'won': None,
                                'pnl': 0.0,
                                'mae': 0.0,
                                'mfe': 0.0,
                                'is_executed': True,
                                'settled': False,
                                'details': res.get('details', {})
                            })
                            
                            print(f"   🚀 Signal: {strategy.strategy_name} -> {action} @ {context.current_price:.5f} | Score: {res.get('entry_score', 0.0)} | FIRED BOTH 5M AND 3M ORDERS!")
                            
                        else:
                            # Not executed (blocked or no setup)
                            trade_logs.append({
                                'order_id': None,
                                'timestamp_ict': ict_time.strftime('%Y-%m-%d %H:%M:%S'),
                                'strategy': strategy.strategy_name,
                                'expiry': 'N/A',
                                'action': action,
                                'entry_score': res.get('entry_score', 0.0),
                                'block_score': res.get('block_score', 0.0),
                                'confidence': res.get('strategy_confidence', 0.0),
                                'fail_reason_code': res.get('fail_reason_code'),
                                'entry_price': context.current_price,
                                'exit_price': None,
                                'won': None,
                                'pnl': 0.0,
                                'mae': 0.0,
                                'mfe': 0.0,
                                'is_executed': False,
                                'settled': False,
                                'details': res.get('details', {})
                            })
                            
                except Exception as e:
                    pass

    # Save report
    report_path = PROJECT_ROOT / "docs" / f"{symbol}_may_6_backtest_report.md"
    
    total_trades = sum(1 for t in trade_logs if t['is_executed'] and t['settled'])
    won_trades = sum(1 for t in trade_logs if t['is_executed'] and t['settled'] and t['won'])
    win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0.0
    total_pnl = sum(t['pnl'] for t in trade_logs if t['is_executed'] and t['settled'])
    
    with codecs.open(str(report_path), "w", encoding="utf-8") as f:
        f.write("# REPORT: GBPUSD 1-Day Backtest (06/05/2026)\\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
        
        f.write("## Executive Summary\\n")
        f.write(f"- **Total Trades Executed**: {total_trades}\\n")
        f.write(f"- **Wins**: {won_trades}\\n")
        f.write(f"- **Losses**: {total_trades - won_trades}\\n")
        f.write(f"- **Win Rate**: {win_rate:.2f}%\\n")
        f.write(f"- **Total PnL**: {total_pnl:+.2f} THB\\n")
        f.write(f"- **Ending Balance**: {2000.0 + total_pnl:.2f} THB\\n\\n")
        
        f.write("## 1. Market State Transitions & Strategy Eligibility\\n")
        f.write("Below is the log of every market state transition detected, along with the strategies that were eligible for that state:\\n\\n")
        f.write("| Time (ICT Thai) | Old State | New State | Eligible Strategies |\\n")
        f.write("| :--- | :--- | :--- | :--- |\\n")
        for st in state_transitions:
            eligible_str = ", ".join(st['eligible_strategies'])
            f.write(f"| {st['timestamp_ict']} | {st['old_state']} | {st['new_state']} | {eligible_str} |\\n")
            
        f.write("\\n## 2. Detailed CALL/PUT Signals & Outcomes\\n")
        f.write("Detailed logs of every signal check that yielded a pattern setup or signal:\\n\\n")
        f.write("| Time (ICT) | Strategy | Expiry | Action | Entry Score | Block Score | Confidence | Execution | Outcome | PnL | Fail Reason | details |\\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\\n")
        for t in trade_logs:
            exec_str = "Yes" if t['is_executed'] else "No (Blocked/Cooldown)"
            outcome_str = "WIN" if t['won'] is True else ("LOSS" if t['won'] is False else "N/A")
            pnl_str = f"{t['pnl']:+.2f}" if t['settled'] else "0.00"
            details_str = json.dumps(t['details'])
            f.write(f"| {t['timestamp_ict']} | {t['strategy']} | {t['expiry']} | {t['action']} | {t['entry_score']:.1f} | {t['block_score']:.1f} | {t['confidence']:.2f} | {exec_str} | {outcome_str} | {pnl_str} | {t['fail_reason_code']} | {details_str} |\\n")
            
    print(f"\\n✅ Backtest completed. Report saved to: docs/{symbol}_may_6_backtest_report.md")

if __name__ == "__main__":
    main()
"""

with codecs.open("C:/Users/Administrator/Downloads/BOT_FINALBOT/BOT_FINALBOT/scratch/run_gbpusd_may_6_backtest.py", "w", encoding="utf-8") as f:
    f.write(backtest_code)
