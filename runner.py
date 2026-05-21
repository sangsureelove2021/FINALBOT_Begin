"""
FINALBOT Main Runner
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Complete pipeline: Data → Intelligence → Strategy → Execution

Status: READY TO RUN (Mock mode)
- Intelligence OS: ✅ (25 engines, 8 tiers)
- Data Layer: ✅ (IQ Option adapter + buffer)
- Strategy: ✅ (Compression Breakout)
- Execution: ✅ (Position sizer + order executor)
"""

import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/bot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("FINALBOT")

# Import core modules
from core.data.iq_option_adapter import IQOptionAdapter
from core.data.candle_buffer import CandleBuffer
from core.models.market_context import MarketContext
from core.orchestration.context_builder import ContextBuilder
from core.orchestration.pipeline import Pipeline
from core.orchestration.execution_gate import ExecutionGate
from core.engines.engine_registry import EngineRegistry
from strategy.compression_breakout.strategy import CompressionBreakoutStrategy
from execution.iq_option_executor import IQOptionExecutor
from execution.position_sizer import PositionSizer
from execution.order_manager import OrderManager
from execution.execution_guard import ExecutionGuard


class BotRunner:
    """Main bot orchestrator."""
    
    def __init__(self,
                 symbols: List[str] = None,
                 timeframes: List[str] = None,
                 capital: float = 2000.0,
                 use_mock: bool = True):
        """
        Initialize bot.
        
        Args:
            symbols: List of pairs to trade (default: EURUSD-OTC)
            timeframes: Timeframes to analyze
            capital: Account balance (THB)
            use_mock: Use mock data/execution
        """
        self.symbols = symbols or ['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC', 'NZDUSD-OTC']
        self.timeframes = timeframes or ['M1', 'M5', 'M15', 'M60', 'D1']
        self.capital = capital
        self.use_mock = use_mock
        
        logger.info("🚀 FINALBOT initializing...")
        logger.info(f"   Symbols: {', '.join(self.symbols)}")
        logger.info(f"   Timeframes: {', '.join(self.timeframes)}")
        logger.info(f"   Capital: {capital} THB")
        logger.info(f"   Mode: {'MOCK' if use_mock else 'LIVE'}")
        
        # Initialize components
        self.data_adapter = IQOptionAdapter(use_mock=use_mock)
        self.candle_buffer = CandleBuffer(size=500)
        
        # Intelligence layer
        self.engine_registry = EngineRegistry()
        # Get all engines from registry (all tiers)
        all_engines = []
        for tier in self.engine_registry.list_tiers():
            all_engines.extend(self.engine_registry.get_by_tier(tier))
        self.engines = all_engines
        self.context_builder = ContextBuilder(self.engines)
        self.intelligence_pipeline = Pipeline(self.engines)
        
        # Strategy
        self.strategy = CompressionBreakoutStrategy()
        
        # Risk gates
        self.execution_gate = ExecutionGate()
        self.execution_guard = ExecutionGuard(capital)
        
        # Execution
        self.executor = IQOptionExecutor(use_mock=use_mock)
        self.position_sizer = PositionSizer(capital=capital)
        self.order_manager = OrderManager()
        
        # Statistics
        self.cycle_count = 0
        self.signal_count = {sym: 0 for sym in self.symbols}
        self.last_execution_time = {}
        
        logger.info("✅ Bot initialized successfully\n")
    
    def run_single_cycle(self, symbol: str) -> Dict:
        """
        Execute one analysis cycle for a symbol.
        
        Returns:
            Cycle result with signal/execution info
        """
        try:
            # Step 1: Fetch data
            logger.debug(f"📊 Fetching data for {symbol}...")
            candles_dict = self.data_adapter.get_multi_timeframe(
                symbol, self.timeframes, count=200
            )
            
            # Step 2: Update buffer
            for tf, candles in candles_dict.items():
                self.candle_buffer.append(symbol, tf, candles)
            
            # Step 3: Build market context
            context = MarketContext.build_from_candles(
                symbol, candles_dict, self.engines
            )
            
            # Step 4: Run intelligence pipeline
            logger.debug(f"🧠 Running intelligence pipeline for {symbol}...")
            pipeline_result = self.intelligence_pipeline.execute(context)
            context = pipeline_result['context']
            
            # Step 5: Strategy decision
            logger.debug(f"📈 Evaluating strategy for {symbol}...")
            signal = self.strategy.evaluate(context)
            
            if signal['action'] == 'NO_SIGNAL':
                return {
                    'symbol': symbol,
                    'signal': 'NO_SIGNAL',
                    'reason': signal.get('reason', 'No setup detected'),
                    'executed': False,
                }
            
            # Step 6: Signal veto (first gate)
            veto_result = self.execution_gate.check(signal, context)
            if not veto_result.get('allowed', True):
                logger.warning(f"🚫 Signal rejected (veto): {veto_result.get('reason', 'Unknown')}")
                return {
                    'symbol': symbol,
                    'signal': 'VETOED',
                    'reason': veto_result.get('reason', 'Veto applied'),
                    'executed': False,
                }
            
            # Step 7: Execution guard (second gate)
            guard_result = self.execution_guard.check(symbol, signal)
            if not guard_result['allowed']:
                logger.warning(f"🛑 Execution rejected (guard): {guard_result['reason']}")
                return {
                    'symbol': symbol,
                    'signal': 'BLOCKED',
                    'reason': guard_result['reason'],
                    'executed': False,
                }
            
            # Step 8: Position sizing
            ps_result = self.position_sizer.calculate(
                entry_price=context['structure']['support'],
                stop_loss_price=context['structure']['support'] - 0.0010,
                direction=signal['direction']
            )
            
            if not ps_result.is_valid:
                logger.warning(f"❌ Position sizing rejected: {ps_result.reason}")
                return {
                    'symbol': symbol,
                    'signal': 'SIZING_FAILED',
                    'reason': ps_result.reason,
                    'executed': False,
                }
            
            # Step 9: Execute trade
            logger.info(f"✅ EXECUTING: {signal['direction']} {ps_result.amount:.0f}x {symbol}")
            order_result = self.executor.send_order(
                symbol=symbol,
                direction=signal['direction'],
                amount=ps_result.amount,
                expiry='M5'
            )
            
            if order_result.status != 'failed':
                # Register in order manager
                self.order_manager.add_trade(
                    order_id=order_result.order_id,
                    symbol=symbol,
                    direction=signal['direction'],
                    amount=ps_result.amount,
                    entry_price=context['structure']['support'],
                    expiry='M5'
                )
                self.signal_count[symbol] += 1
                self.last_execution_time[symbol] = datetime.utcnow()
            
            return {
                'symbol': symbol,
                'signal': signal['direction'],
                'amount': ps_result.amount,
                'order_id': order_result.order_id,
                'confidence': signal.get('confidence', 0),
                'executed': True,
            }
        
        except Exception as e:
            logger.error(f"❌ Error in cycle for {symbol}: {e}")
            return {
                'symbol': symbol,
                'signal': 'ERROR',
                'reason': str(e),
                'executed': False,
            }
    
    def run_cycle(self) -> Dict:
        """
        Execute one full cycle across all symbols.
        
        Returns:
            Dictionary of results per symbol
        """
        self.cycle_count += 1
        logger.info(f"\n{'='*80}")
        logger.info(f"⏱️  CYCLE #{self.cycle_count} | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*80}")
        
        results = {}
        for symbol in self.symbols:
            result = self.run_single_cycle(symbol)
            results[symbol] = result
            
            if result['executed']:
                logger.info(f"✅ {symbol}: {result['signal']} @ confidence {result['confidence']}%")
            else:
                logger.debug(f"⏭️  {symbol}: {result['signal']}")
        
        return results
    
    def run_backtest(self, num_cycles: int = 10) -> None:
        """
        Run backtest (multiple cycles).
        
        Args:
            num_cycles: Number of cycles to execute
        """
        logger.info(f"\n🔄 Starting backtest: {num_cycles} cycles...\n")
        
        for i in range(num_cycles):
            self.run_cycle()
        
        logger.info("\n" + "="*80)
        logger.info("📊 BACKTEST SUMMARY")
        logger.info("="*80)
        logger.info(f"Cycles executed: {self.cycle_count}")
        logger.info(f"Signals per symbol: {self.signal_count}")
        
        # Order manager stats
        self.order_manager.print_summary()
    
    def get_status(self) -> Dict:
        """Get current bot status."""
        stats = self.order_manager.get_stats()
        sizer_stats = self.position_sizer.get_stats()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'cycles': self.cycle_count,
            'data_connected': self.data_adapter.is_connected(),
            'executor_connected': self.executor.is_connected(),
            'mode': 'MOCK' if self.use_mock else 'LIVE',
            'active_trades': len(self.order_manager.active_trades),
            'total_trades': stats['total_trades'],
            'total_pnl': stats['total_pnl'],
            'win_rate': stats['win_rate'],
            'daily_risk_used': f"{sizer_stats['daily_risk_percent']:.2f}%",
            'signals_per_symbol': self.signal_count,
        }


def main():
    """Main entry point."""
    try:
        # Initialize bot
        bot = BotRunner(
            symbols=['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC', 'AUDUSD-OTC', 'NZDUSD-OTC'],
            capital=2000.0,
            use_mock=False  # LIVE MODE with credentials
        )
        
        # Run backtest
        bot.run_backtest(num_cycles=5)
        
        # Final status
        logger.info("\n📍 FINAL STATUS:")
        import json
        logger.info(json.dumps(bot.get_status(), indent=2))
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
