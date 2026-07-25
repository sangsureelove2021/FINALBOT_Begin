# Python Debugging Guide for Quantitative Trading

## 1. Essential Debugging Tools

### Built-in Python Debugger (pdb)
```python
import pdb; pdb.set_trace()  # Python 3.7+
breakpoint()  # Python 3.7+ (preferred)
```

**Key pdb Commands:**
- `n` (next) - Execute next line
- `s` (step) - Step into function
- `c` (continue) - Continue execution
- `p variable` - Print variable value
- `pp variable` - Pretty print variable
- `l` (list) - Show current code context
- `q` (quit) - Exit debugger
- `h` (help) - Show help

### IPython Debugger (ipdb)
```bash
pip install ipdb
```
```python
import ipdb; ipdb.set_trace()
```

## 2. Trading-Specific Debugging Strategies

### Logging Framework
```python
import logging
import logging.handlers
import sys
from datetime import datetime

# Configure detailed logging
def setup_trading_logger(name, log_file='trading.log', level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler with formatting
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console.setFormatter(console_format)
    logger.addHandler(console)
    
    # Rotating file handler for debugging details
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_trading_logger('trading_bot')
```

### Data Validation with Assertions
```python
def validate_trade_params(symbol, price, volume, stop_loss, take_profit):
    """Critical validation for trading parameters"""
    assert symbol is not None and isinstance(symbol, str), "Symbol must be non-empty string"
    assert price > 0, f"Price must be positive: {price}"
    assert volume > 0, f"Volume must be positive: {volume}"
    assert 0 < stop_loss < price, f"Stop-loss must be between 0 and price: {stop_loss}"
    assert take_profit > price, f"Take-profit must be greater than price: {take_profit}"
    return True
```

## 3. Advanced Debugging Techniques

### Using traceback for Error Analysis
```python
import traceback
import sys

def debug_exception():
    """Capture and analyze exceptions"""
    try:
        # Your trading code here
        risky_trade_calculation()
    except Exception as e:
        # Log full stack trace
        logger.error(f"Exception occurred: {e}")
        logger.error(traceback.format_exc())
        
        # Get detailed frame info
        exc_type, exc_value, exc_tb = sys.exc_info()
        logger.error(f"Error type: {exc_type}")
        logger.error(f"Line number: {exc_tb.tb_lineno}")
        
        # Print local variables at error point
        import pprint
        logger.error("Local variables at error:")
        logger.error(pprint.pformat(traceback.tb_frame.f_locals))
```

### Performance Profiling for Trading
```python
import cProfile
import pstats
import io
from contextlib import contextmanager
import time

@contextmanager
def profile_trading_operation(operation_name):
    """Profile specific trading operations"""
    profiler = cProfile.Profile()
    profiler.enable()
    start_time = time.time()
    
    try:
        yield
    finally:
        end_time = time.time()
        profiler.disable()
        
        # Get stats
        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats('cumtime')
        stats.print_stats(20)  # Top 20 functions
        
        logger.info(f"{operation_name} completed in {end_time - start_time:.4f} seconds")
        logger.debug(f"Performance stats:\n{stream.getvalue()}")

# Usage
with profile_trading_operation("strategy_execution"):
    execute_trading_strategy()
```

### Memory Debugging
```python
import tracemalloc
import gc

def debug_memory_leak():
    """Track memory usage in trading loops"""
    tracemalloc.start()
    
    try:
        # Your trading operations
        for i in range(1000):
            process_trade()
            
            # Check memory every 100 iterations
            if i % 100 == 0:
                current, peak = tracemalloc.get_traced_memory()
                logger.debug(f"Iteration {i}: Current memory {current / 1024:.2f} KB, Peak {peak / 1024:.2f} KB")
                
                # Force garbage collection
                gc.collect()
                
                # Get memory allocation stats
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')[:10]
                for stat in top_stats:
                    logger.debug(f"Memory allocation: {stat}")
    finally:
        tracemalloc.stop()
```

## 4. Remote Debugging for Trading Bots

### Using PyCharm Remote Debugger
```python
import pydevd_pycharm
pydevd_pycharm.settrace('localhost', port=12345, stdoutToServer=True, stderrToServer=True)
```

### Using VS Code Remote Debugging
```python
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

## 5. Unit Testing for Trading Logic

```python
import unittest
from unittest.mock import Mock, patch
import pytest

class TestTradingStrategy(unittest.TestCase):
    def setUp(self):
        """Setup test environment"""
        self.strategy = MeanReversionStrategy()
        self.market_data = generate_test_data()
    
    def test_signal_generation(self):
        """Test signal generation logic"""
        signal = self.strategy.generate_signal(self.market_data)
        self.assertIn(signal, ['BUY', 'SELL', 'HOLD'])
    
    def test_risk_management(self):
        """Test position sizing with risk limits"""
        position = self.strategy.calculate_position_size(
            account_balance=10000,
            risk_per_trade=0.02,
            stop_loss_distance=0.01
        )
        self.assertLessEqual(position, 200)  # 2% of 10000 at 1% stop loss

# Run with: python -m unittest test_trading.py
```

## 6. Interactive Debugging in Jupyter Notebooks

```python
%pdb on  # Enable automatic debugging on error
%debug   # Enter debug mode after an error

# Interactive debugging magic
%pylab
from IPython.core.debugger import set_trace
```

## 7. Logging Best Practices for Trading

```python
# Structured logging with context
class TradingContextLogger:
    def __init__(self, logger):
        self.logger = logger
        self.context = {}
    
    def set_context(self, **kwargs):
        self.context.update(kwargs)
    
    def log_trade(self, operation, **details):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            **self.context,
            **details
        }
        self.logger.info(json.dumps(log_entry))

# Usage
trade_logger = TradingContextLogger(logger)
trade_logger.set_context(symbol='BTC/USD', strategy='mean_reversion')
trade_logger.log_trade('ENTRY', price=45000, volume=0.5, stop_loss=44500)
```

## 8. Quick Debugging Checklist

- [ ] Add breakpoints at strategic positions
- [ ] Log all input parameters
- [ ] Log all intermediate calculations
- [ ] Use assertions for validation
- [ ] Check for edge cases (zero values, negative prices)
- [ ] Implement try/except blocks with detailed logging
- [ ] Monitor memory usage in long-running loops
- [ ] Profile performance bottlenecks
- [ ] Write unit tests for critical functions
- [ ] Use version control for debugging changes

## 9. Common Python Trading Errors & Solutions

### Floating Point Precision
```python
# Use Decimal for monetary calculations
from decimal import Decimal, getcontext
getcontext().prec = 10
price = Decimal('45000.00') * Decimal('0.02')
```

### Timezone Issues
```python
import pytz
from datetime import datetime
utc_now = datetime.now(pytz.UTC)
trading_time = utc_now.astimezone(pytz.timezone('US/Eastern'))
```

### API Rate Limiting
```python
import time
from functools import wraps

def rate_limit(max_calls, period):
    def decorator(func):
        calls = []
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [call for call in calls if call > now - period]
            if len(calls) >= max_calls:
                sleep_time = period - (now - calls[0])
                time.sleep(sleep_time)
            calls.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

## 10. Recommended Tools

1. **PyCharm Professional** - Best for debugging
2. **VS Code with Python extension** - Good free alternative
3. **pdb** - Built-in but powerful
4. **ipdb** - Enhanced with tab completion
5. **Loguru** - Better logging library
6. **Sentry** - Production error tracking
7. **DataDog** - Performance monitoring

## 11. Quick Start Template

```python
#!/usr/bin/env python3
"""Trading Bot Debug Template"""
import logging
import sys
from pathlib import Path

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('debug.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Your trading code here
        logger.info("Starting trading bot...")
        
        # Add breakpoint for debugging
        breakpoint()
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Trading bot stopped")

if __name__ == "__main__":
    main()
```
