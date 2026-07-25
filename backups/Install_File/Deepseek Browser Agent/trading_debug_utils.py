#!/usr/bin/env python3
"""
Trading System Debugging Utilities
Comprehensive debugging tools for quantitative trading systems
"""

import logging
import json
import time
import traceback
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
from contextlib import contextmanager
import inspect
from pathlib import Path


class TradingDebugger:
    """Advanced debugging utility for trading systems"""
    
    def __init__(self, log_file: str = "trading_debug.log", verbose: bool = True):
        self.log_file = log_file
        self.verbose = verbose
        self.logger = self._setup_logger()
        self.context = {}
        
    def _setup_logger(self) -> logging.Logger:
        """Setup debug logger with comprehensive formatting"""
        logger = logging.getLogger('TradingDebugger')
        logger.setLevel(logging.DEBUG)
        
        # File handler with full details
        fh = logging.FileHandler(self.log_file)
        fh.setLevel(logging.DEBUG)
        fh_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S.%f'[:-3]
        )
        fh.setFormatter(fh_format)
        logger.addHandler(fh)
        
        # Console handler for verbose output
        if self.verbose:
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.INFO)
            ch_format = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            ch.setFormatter(ch_format)
            logger.addHandler(ch)
        
        return logger
    
    def set_context(self, **kwargs) -> None:
        """Set contextual information for all logs"""
        self.context.update(kwargs)
        self.logger.debug(f"Context updated: {json.dumps(self.context)}")
    
    def debug_trade(self, trade_data: Dict[str, Any], operation: str) -> None:
        """Log detailed trade information"""
        trade_log = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'context': self.context,
            'trade_data': trade_data
        }
        self.logger.debug(f"TRADE: {json.dumps(trade_log, default=str)}")
    
    def log_state(self, state_data: Dict[str, Any], state_name: str) -> None:
        """Log system state for debugging"""
        state_log = {
            'timestamp': datetime.now().isoformat(),
            'state': state_name,
            'context': self.context,
            'data': state_data
        }
        self.logger.info(f"STATE: {json.dumps(state_log, default=str)}")
    
    @contextmanager
    def measure_performance(self, operation_name: str):
        """Context manager to measure performance of trading operations"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            end_memory = self._get_memory_usage()
            memory_change = end_memory - start_memory
            
            self.logger.debug(
                f"PERFORMANCE: {operation_name} | "
                f"Elapsed: {elapsed:.4f}s | "
                f"Memory Δ: {memory_change:.2f}MB | "
                f"Memory total: {end_memory:.2f}MB"
            )
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0


def debug_trade_function(func: Callable) -> Callable:
    """Decorator to debug trading functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        debugger = TradingDebugger(verbose=False)
        
        # Log function call
        func_args = inspect.signature(func).bind(*args, **kwargs)
        func_args.apply_defaults()
        
        debugger.logger.debug(
            f"FUNCTION_CALL: {func.__name__} | "
            f"Args: {func_args.arguments}"
        )
        
        try:
            with debugger.measure_performance(func.__name__):
                result = func(*args, **kwargs)
            
            debugger.logger.debug(
                f"FUNCTION_RESULT: {func.__name__} | "
                f"Result: {result}"
            )
            return result
            
        except Exception as e:
            debugger.logger.error(
                f"FUNCTION_ERROR: {func.__name__} | "
                f"Error: {e}\n{traceback.format_exc()}"
            )
            raise
    
    return wrapper


def debug_data_pipeline(step_name: str = None):
    """Decorator for debugging data pipeline steps"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            debugger = TradingDebugger(verbose=False)
            step = step_name or func.__name__
            
            # Log input data
            debugger.logger.debug(
                f"DATA_PIPELINE_START: {step} | "
                f"Input: {args[0] if args else kwargs.get('data', 'No data')}"
            )
            
            try:
                result = func(*args, **kwargs)
                
                # Log output data
                debugger.logger.debug(
                    f"DATA_PIPELINE_END: {step} | "
                    f"Output: {result}"
                )
                return result
                
            except Exception as e:
                debugger.logger.error(
                    f"DATA_PIPELINE_ERROR: {step} | "
                    f"Error: {e}\n{traceback.format_exc()}"
                )
                raise
        
        return wrapper
    return decorator


class DebuggableTradingBot:
    """Base class for trading bots with built-in debugging"""
    
    def __init__(self, name: str = "TradingBot"):
        self.name = name
        self.debugger = TradingDebugger(log_file=f"{name}.log")
        self.state = {}
        self.trade_history = []
        
    def log_trade(self, side: str, price: float, volume: float, **kwargs):
        """Log a trade execution"""
        trade_data = {
            'side': side,
            'price': price,
            'volume': volume,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        self.trade_history.append(trade_data)
        self.debugger.debug_trade(trade_data, 'TRADE_EXECUTION')
        
    def log_state(self, state_name: str, **kwargs):
        """Log current bot state"""
        self.state.update(kwargs)
        self.debugger.log_state(self.state, state_name)
        
    def validate_trade_params(self, side: str, price: float, volume: float):
        """Validate trade parameters"""
        try:
            assert side in ['BUY', 'SELL'], f"Invalid side: {side}"
            assert price > 0, f"Invalid price: {price}"
            assert volume > 0, f"Invalid volume: {volume}"
            return True
        except AssertionError as e:
            self.debugger.logger.error(f"Validation failed: {e}")
            return False
    
    def debug_simulation(self, iterations: int = 10):
        """Run a debug simulation of the trading bot"""
        self.debugger.logger.info(f"Starting debug simulation for {self.name}")
        
        with self.debugger.measure_performance(f"simulation_{self.name}"):
            for i in range(iterations):
                self.debugger.logger.debug(f"Simulation iteration {i+1}/{iterations}")
                
                # Simulate price and volume
                price = 100 + i * 0.5
                volume = 1 + i * 0.1
                side = 'BUY' if i % 2 == 0 else 'SELL'
                
                if self.validate_trade_params(side, price, volume):
                    self.log_trade(side, price, volume, iteration=i)
                    self.log_state(f'iteration_{i}', price=price, volume=volume)
                
                time.sleep(0.1)
        
        self.debugger.logger.info(f"Simulation complete: {len(self.trade_history)} trades logged")
        return self.trade_history
    
    def export_debug_data(self, filename: str = None):
        """Export debug data for analysis"""
        filename = filename or f"{self.name}_debug_export.json"
        export_data = {
            'bot_name': self.name,
            'export_timestamp': datetime.now().isoformat(),
            'state': self.state,
            'trade_history': self.trade_history,
            'total_trades': len(self.trade_history)
        }
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        self.debugger.logger.info(f"Debug data exported to {filename}")
        return filename


# Example usage and testing
def example_trading_function(price: float, volume: float):
    """Example trading function with debugging"""
    debugger = TradingDebugger()
    
    debugger.logger.info(f"Processing trade: {price} @ {volume}")
    
    # Simulate processing
    if price > 0 and volume > 0:
        return {'status': 'success', 'price': price, 'volume': volume}
    else:
        debugger.logger.error(f"Invalid trade parameters: price={price}, volume={volume}")
        return {'status': 'error', 'message': 'Invalid parameters'}


if __name__ == "__main__":
    # Test the debugging utilities
    print("Testing TradingDebugger utilities...")
    
    # Example 1: Basic debugging
    debugger = TradingDebugger(verbose=True)
    debugger.set_context(symbol='BTC/USD', strategy='mean_reversion')
    
    # Test trade logging
    debugger.log_trade(
        {'price': 45000, 'volume': 0.5, 'stop_loss': 44500, 'take_profit': 46000},
        'BUY_ENTRY'
    )
    
    # Example 2: Trading bot simulation
    bot = DebuggableTradingBot('TestBot')
    trades = bot.debug_simulation(iterations=5)
    bot.export_debug_data()
    
    # Example 3: Decorator usage
    @debug_trade_function
    def process_trade(symbol: str, price: float, volume: float):
        """Process a trade with automatic debugging"""
        return {
            'symbol': symbol,
            'price': price,
            'volume': volume,
            'timestamp': datetime.now().isoformat()
        }
    
    result = process_trade('ETH/USD', 2500, 2)
    print(f"Processed trade: {result}")
    
    print("\nDebugging utilities test complete!")
    print(f"Debug logs written to: {debugger.log_file}")
    print(f"Bot debug data exported to: {bot.export_debug_data()}")
