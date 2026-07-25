# Python Debugging Cheat Sheet 🐍

## Quick Reference for Trading System Debugging

### 1. 🛠️ Essential Tools

| Tool | When to Use | Example |
|------|-------------|---------|
| `pdb` | Built-in debugger | `import pdb; pdb.set_trace()` |
| `breakpoint()` | Python 3.7+ preferred | `breakpoint()` |
| `ipdb` | Enhanced with completion | `import ipdb; ipdb.set_trace()` |
| `pudb` | GUI debugger | `pip install pudb; pudb.set_trace()` |
| `logging` | Production logging | `import logging` |

### 2. 🔍 pdb Commands

```python
# Quick commands
n         # next line
s         # step into function
c         # continue execution
q         # quit debugger
p var     # print variable
pp var    # pretty print variable
l         # list code context
w         # where (show stack trace)
u/d       # up/down stack frames
!expr     # execute expression
help      # show help

# Example session
breakpoint()  # Start debugger
# (Pdb) p price
# (Pdb) n
# (Pdb) c
```

### 3. 📝 Logging Setup

```python
import logging

# Quick setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Advanced setup
logger = logging.getLogger(__name__)
handler = logging.FileHandler('debug.log')
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

# Trading-specific logging
logger.info(f"Trade executed: {side} {volume} @ {price}")
logger.warning(f"Stop-loss triggered at {price}")
logger.error(f"Order failed: {error}", exc_info=True)
```

### 4. ⚡ Common Debugging Patterns

```python
# Print variables
def calculate_position(price, balance):
    print(f"DEBUG: price={price}, balance={balance}")
    # Your code

# Assertions for validation
def process_trade(symbol, price, volume):
    assert symbol and isinstance(symbol, str), "Invalid symbol"
    assert price > 0, f"Invalid price: {price}"
    assert volume > 0, f"Invalid volume: {volume}"
    # Your code

# Try/Except with detailed logging
import traceback
def handle_trade():
    try:
        # Your trading code
        pass
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
        raise
```

### 5. 🎯 Decorators for Debugging

```python
# Function timing
import time
def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - start:.4f}s")
        return result
    return wrapper

# Logging function arguments
def log_args(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        return func(*args, **kwargs)
    return wrapper

# Usage
@timer
@log_args
def execute_trade(side, price, volume):
    # Your trading code
    pass
```

### 6. 📊 Data Validation

```python
# Check for NaN
import math
def is_valid_price(price):
    return isinstance(price, (int, float)) and not math.isnan(price) and price > 0

# Check data structure
def validate_market_data(data):
    required_fields = ['symbol', 'price', 'volume', 'timestamp']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    return True

# Check numeric ranges
def validate_stop_loss(entry_price, stop_loss):
    if stop_loss >= entry_price:
        raise ValueError(f"Stop-loss {stop_loss} must be below entry {entry_price}")
```

### 7. 🚀 Performance Debugging

```python
import cProfile
import pstats

# Profile code
profiler = cProfile.Profile()
profiler.enable()
# Your trading code
profiler.disable()

# Get stats
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(20)  # Top 20 functions

# Use with context manager
@contextmanager
def profile_trading():
    import cProfile
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        yield
    finally:
        profiler.disable()
        # Process stats
```

### 8. 🧠 Memory Debugging

```python
import tracemalloc
import gc

# Track memory usage
tracemalloc.start()

# Your code

# Get memory stats
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current/1024/1024:.2f}MB")
print(f"Peak memory: {peak/1024/1024:.2f}MB")

# Force garbage collection
gc.collect()

# Get allocation snapshot
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')[:10]
for stat in top_stats:
    print(stat)
```

### 9. 🌐 Remote Debugging

```python
# PyCharm Remote
import pydevd_pycharm
pydevd_pycharm.settrace('localhost', port=12345)

# VS Code Remote
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()

# Manual socket debugger
import socket
def debug_socket(message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('localhost', 9999))
        s.sendall(message.encode())
```

### 10. 🔧 Quick Fixes for Common Issues

```python
# Issue: Division by zero
if denominator != 0:
    result = numerator / denominator
else:
    result = 0

# Issue: Floating point comparison
# DON'T: if price == 0.01:
# DO: if abs(price - 0.01) < 1e-10:

# Issue: Dictionary KeyError
# DON'T: value = data['price']
# DO: value = data.get('price', default_price)

# Issue: List index out of range
if len(data) > index:
    value = data[index]

# Issue: Timezone confusion
import pytz
utc_now = datetime.now(pytz.UTC)
local_time = utc_now.astimezone(pytz.timezone('US/Eastern'))
```

### 11. 🎮 Trading-Specific Debugging

```python
# Debug strategy signals
def debug_strategy_signal(signal, price, volume):
    print(f"Signal: {signal}, Price: {price}, Volume: {volume}")
    if signal == 'BUY':
        print("→ Execution: Buy order placed")
    elif signal == 'SELL':
        print("→ Execution: Sell order placed")

# Debug risk management
def debug_risk_calculation(position, stop_loss, take_profit):
    risk = (position - stop_loss) * volume
    reward = (take_profit - position) * volume
    ratio = reward / risk if risk > 0 else float('inf')
    print(f"Risk: ${risk:.2f}, Reward: ${reward:.2f}, R/R: {ratio:.2f}")

# Debug order execution
def debug_order_execution(order, status, error=None):
    print(f"Order: {order['id']}, Status: {status}")
    if error:
        print(f"Error: {error}")
```

### 12. 📈 Analysis Tools

```python
# Quick data inspection
def inspect_trading_data(data):
    print(f"Data shape: {len(data)} records")
    print(f"Columns: {list(data[0].keys()) if data else 'Empty'}")
    print(f"Sample: {data[0] if data else 'None'}")

# Performance metrics
def calculate_performance_metrics(trades):
    profits = [trade['profit'] for trade in trades]
    return {
        'total_trades': len(trades),
        'winning_trades': len([p for p in profits if p > 0]),
        'win_rate': len([p for p in profits if p > 0]) / len(profits),
        'average_profit': sum(profits) / len(profits),
        'total_profit': sum(profits)
    }
```

### 13. 🛡️ Error Handling Best Practices

```python
# Custom exceptions
class TradingError(Exception):
    pass

class OrderExecutionError(TradingError):
    pass

class RiskLimitError(TradingError):
    pass

# Specific error handling
def execute_order(order):
    try:
        # Execute order
        return submit_order(order)
    except OrderExecutionError as e:
        logger.error(f"Order failed: {e}")
        # Try again or cancel
    except RiskLimitError as e:
        logger.warning(f"Risk limit exceeded: {e}")
        # Adjust position
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        # Emergency shutdown
```

### 14. 🔄 Testing Patterns

```python
import unittest

class TestTradingStrategy(unittest.TestCase):
    def setUp(self):
        """Setup test environment"""
        self.strategy = MeanReversionStrategy()
    
    def test_with_valid_data(self):
        """Test with valid market data"""
        result = self.strategy.process(market_data)
        self.assertIsNotNone(result)
    
    def test_with_invalid_data(self):
        """Test with invalid data"""
        with self.assertRaises(ValueError):
            self.strategy.process(invalid_data)
    
    def test_edge_cases(self):
        """Test edge cases"""
        self.assertAlmostEqual(
            self.strategy.calculate_position(0), 
            0
        )
```

## Quick Command Reference

```bash
# Run with debugger
python -m pdb my_script.py

# Run with profiling
python -m cProfile -s cumtime my_script.py

# Run unit tests with output
python -m unittest -v test_trading.py

# Run with coverage
python -m coverage run -m unittest discover
python -m coverage report

# Check syntax
python -m py_compile my_script.py

# Run linter
python -m pylint my_script.py

# Find unused imports
python -m autoflake --check my_script.py
```

## Summary of Best Practices

1. **Start simple** - Use `print()` for quick debugging
2. **Progress to logging** - For production, use logging
3. **Use breakpoints** - For complex issues, use debugger
4. **Add assertions** - Validate critical data
5. **Write tests** - Prevent regression bugs
6. **Profile performance** - Identify bottlenecks
7. **Monitor memory** - Check for leaks
8. **Handle errors gracefully** - Always plan for failures
9. **Document assumptions** - Note what you expect
10. **Version control** - Track debugging changes
