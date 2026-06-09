import sys
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
    symbol = "EURUSD-OTC"
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
        
    # Import all 14 strategies
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

    all_strategies = [
        Rejection5mPAStrategy(),
        EMACrossoverStrategy(),
        MACDCrossoverStrategy(),
        StochasticCrossoverStrategy(),
        RSIReversalStrategy(),
        BBRSIConfluenceStrategy(),
        PinBarScalperStrategy(),
        EngulfingScalperStrategy(),
        RSIExtremeBounceStrategy(),
        EMARibbonMomentumStrategy(),
        PriceActionSRStrategy(),
        SRFakeoutRejectionStrategy(),
        TripleConfluenceStrategy(),
        CompressionBreakoutStrategy()
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
    
    # Register ALL 14 strategies in the runner and pipeline
    bot.active_strategies = all_strategies
    bot.strategies = all_strategies
    bot.intelligence_pipeline.strategies = all_strategies
    
    bot.position_sizer.calculate = lambda confidence=None: 35.0
    
    m5_df = csv_adapter.dfs[symbol]["M5"]
    ref_timestamps = m5_df.index
    
    # 04/06/2026 from 01:00 to 23:00 ICT (Thai time)
    # Start: 2026-06-04 01:00:00 ICT = 2026-06-03 18:00:00 UTC
    # End: 2026-06-04 23:00:00 ICT = 2026-06-04 16:00:00 UTC
    start_dt = datetime(2026, 6, 3, 18, 0, tzinfo=timezone.utc)
    end_dt = datetime(2026, 6, 4, 16, 0, tzinfo=timezone.utc)
    
    valid_indices = [
        i for i, ts in enumerate(ref_timestamps)
        if start_dt <= ts <= end_dt
    ]
    
    if not valid_indices:
        print("❌ Error: No M5 historical data found for specified window.")
        return
        
    start_index = min(valid_indices)
    end_index = max(valid_indices)
    
    payout_rate = 0.85
    balance = 2000.0
    
    state_transitions = []
    trade_logs = []
    current_state = None
    
    print(f"🔄 Starting backtest on EURUSD-OTC for June 4, 2026...")
    
    for i in range(start_index, end_index + 3):
        if i >= len(ref_timestamps):
            break
        timestamp = ref_timestamps[i]
        ict_time = timestamp + timedelta(hours=7)
        
        # A. Settle active expired trades
        active_trades = list(bot.order_manager.active_trades.items())
        for order_id, trade in active_trades:
            if timestamp >= trade.entry_time + timedelta(minutes=5):
                exit_price = float(m5_df.loc[timestamp, "close"])
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
                
                # Fetch detailed metrics from M1
                mae = 0.0
                mfe = 0.0
                try:
                    m1_df = csv_adapter.dfs[symbol]["M1"]
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
                
                # Update the corresponding record in trade_logs
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
        synced = TimeframeSync(primary='M5').sync(candles_dict)
        
        # Slice off the last candle of synced to prevent look-ahead bias
        for tf in list(synced.keys()):
            if len(synced[tf]) > 1:
                synced[tf] = synced[tf].iloc[:-1]
                
        context = bot.intelligence_pipeline.context_builder.build(symbol, synced, 'M5')
        if context:
            state_dict = context.market_state
            state_name = "UNKNOWN"
            if isinstance(state_dict, dict):
                state_name = state_dict.get('state', 'UNKNOWN').upper()
            elif isinstance(state_dict, str):
                state_name = state_dict.upper()
                
            # Log state transition
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
            # We evaluate each strategy manually to log detailed signal/no-setup data
            for strategy in all_strategies:
                try:
                    if not strategy.is_eligible(context):
                        continue
                    
                    res = strategy.evaluate(context)
                    action = res.get('action', 'NO_SETUP')
                    
                    # Log all CALL/PUT setups, even if blocked or not executed
                    if action in ('CALL', 'PUT') or res.get('entry_score', 0.0) > 0.0 or res.get('block_score', 0.0) > 0.0:
                        # Record a trade if the strategy returned a valid action
                        is_executed = False
                        order_id = None
                        
                        # Execute trade in simulation if action is CALL/PUT and not blocked
                        if action in ('CALL', 'PUT') and res.get('block_score', 0.0) < 100.0 and not bot.order_manager.get_active_trades(symbol):
                            order_id = str(uuid.uuid4())[:8]
                            from core.models.trade import Trade
                            trade = Trade(
                                order_id=order_id,
                                symbol=symbol,
                                direction=action,
                                amount=35.0,
                                entry_price=context.current_price,
                                entry_time=timestamp,
                                expiry='M5',
                                notes=strategy.strategy_name
                            )
                            bot.order_manager.active_trades[order_id] = trade
                            is_executed = True
                        
                        trade_logs.append({
                            'order_id': order_id,
                            'timestamp_ict': ict_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'strategy': strategy.strategy_name,
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
                            'is_executed': is_executed,
                            'settled': False,
                            'details': res.get('details', {})
                        })
                        if is_executed:
                            print(f"   🚀 Signal: {strategy.strategy_name} -> {action} @ {context.current_price:.5f} | Score: {res.get('entry_score', 0.0)} | Block: {res.get('block_score', 0.0)}")
                except Exception as e:
                    pass

    # Save report
    report_path = PROJECT_ROOT / "docs" / "Reversal Group A_EURUSD_OTC_june_4_backtest_report.md"
    
    total_trades = sum(1 for t in trade_logs if t['is_executed'] and t['settled'])
    won_trades = sum(1 for t in trade_logs if t['is_executed'] and t['settled'] and t['won'])
    win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0.0
    total_pnl = sum(t['pnl'] for t in trade_logs if t['is_executed'] and t['settled'])
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# REPORT: EURUSD-OTC 1-Day Backtest (04/06/2026)\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Executive Summary\n")
        f.write(f"- **Total Trades Executed**: {total_trades}\n")
        f.write(f"- **Wins**: {won_trades}\n")
        f.write(f"- **Losses**: {total_trades - won_trades}\n")
        f.write(f"- **Win Rate**: {win_rate:.2f}%\n")
        f.write(f"- **Total PnL**: {total_pnl:+.2f} THB\n")
        f.write(f"- **Ending Balance**: {2000.0 + total_pnl:.2f} THB\n\n")
        
        f.write("## 1. Market State Transitions & Strategy Eligibility\n")
        f.write("Below is the log of every market state transition detected, along with the strategies that were eligible for that state:\n\n")
        f.write("| Time (ICT Thai) | Old State | New State | Eligible Strategies |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for st in state_transitions:
            eligible_str = ", ".join(st['eligible_strategies'])
            f.write(f"| {st['timestamp_ict']} | {st['old_state']} | {st['new_state']} | {eligible_str} |\n")
            
        f.write("\n## 2. Detailed CALL/PUT Signals & Outcomes\n")
        f.write("Detailed logs of every signal check that yielded a pattern setup or signal:\n\n")
        f.write("| Time (ICT) | Strategy | Action | Entry Score | Block Score | Confidence | Execution | Outcome | PnL | Fail Reason | details |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for t in trade_logs:
            exec_str = "Yes" if t['is_executed'] else "No (Blocked/Cooldown)"
            outcome_str = "WIN" if t['won'] is True else ("LOSS" if t['won'] is False else "N/A")
            pnl_str = f"{t['pnl']:+.2f}" if t['settled'] else "0.00"
            details_str = json.dumps(t['details'])
            f.write(f"| {t['timestamp_ict']} | {t['strategy']} | {t['action']} | {t['entry_score']:.1f} | {t['block_score']:.1f} | {t['confidence']:.2f} | {exec_str} | {outcome_str} | {pnl_str} | {t['fail_reason_code']} | {details_str} |\n")
            
    print(f"\n✅ Backtest completed. Report saved to: docs/Reversal Group A_EURUSD_OTC_june_4_backtest_report.md")

if __name__ == "__main__":
    main()
