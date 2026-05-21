"""
Replay Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Replay historical candles through bot pipeline.
Used for backtesting and strategy validation.
"""

import logging
import pandas as pd
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ReplayResult:
    """Result of single replay cycle."""
    timestamp: datetime
    symbol: str
    signal: str  # 'CALL', 'PUT', 'NO_SIGNAL'
    confidence: int
    order_id: Optional[str] = None
    pnl: float = 0.0
    notes: str = ""


class ReplayEngine:
    """
    Replay bot through historical candle data.
    
    Usage:
        engine = ReplayEngine(bot)
        results = engine.replay(candles_dict, symbols=['EURUSD'])
        metrics = engine.calculate_metrics(results)
    """
    
    def __init__(self, bot_runner):
        """
        Initialize replay engine.
        
        Args:
            bot_runner: BotRunner instance to replay through
        """
        self.bot = bot_runner
        self.results: List[ReplayResult] = []
        self.cycle_count = 0
    
    def replay(self, candles_dict: Dict[str, Dict[str, pd.DataFrame]],
              symbols: List[str],
              on_signal: Optional[Callable] = None) -> List[ReplayResult]:
        """
        Replay candles through bot.
        
        Args:
            candles_dict: {symbol: {timeframe: DataFrame}}
            symbols: List of symbols to replay
            on_signal: Callback function for each signal
        
        Returns:
            List of ReplayResult objects
        """
        logger.info(f"🔄 Starting replay for {len(symbols)} symbols...")
        self.results = []
        self.cycle_count = 0
        
        # Get minimum candle count across all TF/symbols
        min_candles = self._get_min_candle_count(candles_dict, symbols)
        logger.info(f"📊 Replaying {min_candles} candle cycles...")
        
        # Replay each candle
        for i in range(min_candles):
            self.cycle_count += 1
            
            # Prepare candle slice for this cycle
            candle_slice = {}
            for symbol in symbols:
                candle_slice[symbol] = {}
                for tf, df in candles_dict[symbol].items():
                    # Take first i+1 candles (incremental)
                    candle_slice[symbol][tf] = df.iloc[:i+1]
            
            # Update bot's buffer with slice
            for symbol in symbols:
                for tf, df in candle_slice[symbol].items():
                    self.bot.candle_buffer.append(symbol, tf, df)
            
            # Run bot cycle
            results_per_symbol = self.bot.run_cycle()
            
            # Record results
            for symbol, result in results_per_symbol.items():
                if result['executed']:
                    replay_result = ReplayResult(
                        timestamp=datetime.utcnow(),
                        symbol=symbol,
                        signal=result['signal'],
                        confidence=result.get('confidence', 0),
                        order_id=result.get('order_id'),
                        notes=f"Cycle {self.cycle_count}"
                    )
                    self.results.append(replay_result)
                    
                    if on_signal:
                        on_signal(replay_result)
            
            # Progress indicator
            if self.cycle_count % 100 == 0:
                logger.info(f"  Progress: {self.cycle_count}/{min_candles} cycles")
        
        logger.info(f"✅ Replay complete: {len(self.results)} signals generated")
        return self.results
    
    def calculate_metrics(self, results: Optional[List[ReplayResult]] = None) -> Dict:
        """
        Calculate performance metrics.
        
        Args:
            results: List of ReplayResult (default: self.results)
        
        Returns:
            Dictionary of metrics
        """
        if results is None:
            results = self.results
        
        if not results:
            return {
                'total_signals': 0,
                'total_calls': 0,
                'total_puts': 0,
                'call_ratio': 0.0,
                'put_ratio': 0.0,
                'avg_confidence': 0.0,
                'signals_per_cycle': 0.0,
            }
        
        calls = [r for r in results if r.signal == 'CALL']
        puts = [r for r in results if r.signal == 'PUT']
        total = len(results)
        
        metrics = {
            'total_signals': total,
            'total_calls': len(calls),
            'total_puts': len(puts),
            'call_ratio': len(calls) / total * 100 if total > 0 else 0.0,
            'put_ratio': len(puts) / total * 100 if total > 0 else 0.0,
            'avg_confidence': sum(r.confidence for r in results) / total if total > 0 else 0.0,
            'signals_per_cycle': total / self.cycle_count if self.cycle_count > 0 else 0.0,
            'signals_per_symbol': self._get_signals_per_symbol(results),
        }
        
        return metrics
    
    def _get_min_candle_count(self, candles_dict: Dict, symbols: List[str]) -> int:
        """Get minimum candle count across all symbols/TF."""
        min_count = float('inf')
        for symbol in symbols:
            for tf, df in candles_dict[symbol].items():
                min_count = min(min_count, len(df))
        return int(min_count) if min_count != float('inf') else 0
    
    def _get_signals_per_symbol(self, results: List[ReplayResult]) -> Dict[str, int]:
        """Count signals per symbol."""
        counts = {}
        for result in results:
            counts[result.symbol] = counts.get(result.symbol, 0) + 1
        return counts
    
    def export_results(self, filepath: str) -> None:
        """Export results to CSV."""
        if not self.results:
            logger.warning("No results to export")
            return
        
        data = []
        for r in self.results:
            data.append({
                'timestamp': r.timestamp.isoformat(),
                'symbol': r.symbol,
                'signal': r.signal,
                'confidence': r.confidence,
                'order_id': r.order_id,
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        logger.info(f"✅ Results exported to {filepath}")
