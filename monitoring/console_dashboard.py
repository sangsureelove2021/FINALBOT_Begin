"""
Advanced Analytics Dashboard

Compare strategies, analyze correlation, ML metrics.
"""

import sys
import os
import threading
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

class SafeStreamWrapper:
    def __init__(self, original_stream):
        self.original_stream = original_stream
        self.encoding = getattr(original_stream, 'encoding', None) or 'utf-8'

    def write(self, data):
        try:
            self.original_stream.write(data)
        except Exception:
            try:
                # Force fallback to pure ASCII with backslashreplace
                safe_data = data.encode('ascii', errors='backslashreplace').decode('ascii')
                self.original_stream.write(safe_data)
            except Exception:
                pass

    def flush(self):
        if hasattr(self.original_stream, 'flush'):
            self.original_stream.flush()

    def __getattr__(self, attr):
        return getattr(self.original_stream, attr)

class AutoFlushRotatingFileHandler(RotatingFileHandler):
    """RotatingFileHandler that automatically flushes to disk after every record (Zero Log Buffer Loss)."""
    def emit(self, record):
        super().emit(record)
        self.flush()

class ExactLevelFilter(logging.Filter):
    """Filter that allows log records matching a specific level range, suppressing SEC_TRACK."""
    def __init__(self, min_level: int, max_level: int = logging.CRITICAL + 10):
        super().__init__()
        self.min_level = min_level
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if "[SEC_TRACK]" in msg:
            return False
        return self.min_level <= record.levelno <= self.max_level

class ConsoleHandler(logging.StreamHandler):
    """Handler for Terminal console output, filtering out [SEC_TRACK] messages."""
    def __init__(self, stream=None):
        super().__init__(stream or sys.stdout)
        self.addFilter(ExactLevelFilter(min_level=logging.INFO))

_PRINT_LOCK = threading.Lock()
_LOGGING_INITIALIZED = False

def setup_logging():
    global _LOGGING_INITIALIZED
    if _LOGGING_INITIALIZED:
        return
    
    sys.stdout = SafeStreamWrapper(sys.stdout)
    sys.stderr = SafeStreamWrapper(sys.stderr)

    base_log_dir = "logs/logs_data_feed"
    errors_dir = os.path.join(base_log_dir, "errors")
    warnings_dir = os.path.join(base_log_dir, "warnings")
    info_dir = os.path.join(base_log_dir, "system_info")
    all_runtime_dir = os.path.join(base_log_dir, "all_runtime")
    fallback_dir = os.path.join(base_log_dir, "fallback")

    os.makedirs(errors_dir, exist_ok=True)
    os.makedirs(warnings_dir, exist_ok=True)
    os.makedirs(info_dir, exist_ok=True)
    os.makedirs(all_runtime_dir, exist_ok=True)
    os.makedirs(fallback_dir, exist_ok=True)

    max_bytes = 50 * 1024 * 1024  # 50 MB
    backup_count = 1000

    error_log_path = os.path.join(errors_dir, "error.log")
    warning_log_path = os.path.join(warnings_dir, "warning.log")
    info_log_path = os.path.join(info_dir, "info.log")
    all_runtime_log_path = os.path.join(all_runtime_dir, "runtime.log")
    fallback_log_path = os.path.join(fallback_dir, "fallback.log")

    formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s')

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    # All Runtime Handler: all_runtime/runtime.log (100% events including [SEC_TRACK])
    all_runtime_handler = AutoFlushRotatingFileHandler(
        all_runtime_log_path, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    all_runtime_handler.setLevel(logging.INFO)
    all_runtime_handler.setFormatter(formatter)
    root_logger.addHandler(all_runtime_handler)

    # Error Handler: errors/error.log (ERROR, CRITICAL, Exceptions)
    error_handler = AutoFlushRotatingFileHandler(
        error_log_path, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(ExactLevelFilter(min_level=logging.ERROR))
    root_logger.addHandler(error_handler)

    # Warning Handler: warnings/warning.log (WARNING only)
    warning_handler = AutoFlushRotatingFileHandler(
        warning_log_path, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(formatter)
    warning_handler.addFilter(ExactLevelFilter(min_level=logging.WARNING, max_level=logging.WARNING))
    root_logger.addHandler(warning_handler)

    # Info Handler: system_info/info.log (INFO only)
    info_handler = AutoFlushRotatingFileHandler(
        info_log_path, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    info_handler.addFilter(ExactLevelFilter(min_level=logging.INFO, max_level=logging.INFO))
    root_logger.addHandler(info_handler)

    # Fallback Handler: fallback/fallback.log (WARNING+ for REST fallback events)
    fallback_handler = AutoFlushRotatingFileHandler(
        fallback_log_path, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    fallback_handler.setLevel(logging.WARNING)
    fallback_handler.setFormatter(formatter)

    class FallbackFilter(logging.Filter):
        """Only log records that contain [FALLBACK] in the message."""
        def filter(self, record):
            return "[FALLBACK]" in record.getMessage()
    fallback_handler.addFilter(FallbackFilter())
    root_logger.addHandler(fallback_handler)

    finalbot_logger = logging.getLogger("FINALBOT")
    finalbot_logger.setLevel(logging.INFO)
    finalbot_logger.handlers.clear()
    finalbot_logger.propagate = True

    _LOGGING_INITIALIZED = True

def thai_console_log(msg: str):
    if "[SEC_TRACK]" in msg:
        return
    tz_thailand = timezone(timedelta(hours=7))
    thai_time_str = datetime.now(tz_thailand).strftime('%H:%M:%S')
    try:
        with _PRINT_LOCK:
            print(f"{thai_time_str} - {msg}")
            # Only flush if it doesn't cause error
            try:
                sys.stdout.flush()
            except (OSError, IOError):
                pass  # Ignore flush errors
        # Also log to file to avoid silent failures
        logging.getLogger("FINALBOT").info(msg)
    except Exception as e:
        # Zero Tolerance: console errors must be logged
        logging.getLogger("FINALBOT").error(f"Console output error: {e}")
        raise RuntimeError(f"Console output failed: {e}")

logger = logging.getLogger("FINALBOT")


class ConsoleUI:
    """Handles all console UI formatting and printing."""
    
    @staticmethod
    def show_startup():
        thai_console_log("FINALBOT Running")

    @staticmethod
    def show_symbols_loaded(symbols):
        thai_console_log(f"คู่เงิน ({len(symbols)}): {', '.join(symbols)}")

    @staticmethod
    def show_live_mode_start():
        thai_console_log("เริ่ม Live Mode — วิเคราะห์ทุกแท่ง M1 (Ctrl+C หยุด)")

    @staticmethod
    def show_connection_attempt():
        thai_console_log("กำลังเชื่อมต่อโบรกเกอร์  | IQ Option")

    @staticmethod
    def show_connection_success():
        thai_console_log("เชื่อมต่อ IQ Option สำเร็จ")

    @staticmethod
    def show_connection_failed():
        thai_console_log("เชื่อมต่อ IQ Option ล้มเหลว")

    @staticmethod
    def show_account_info(account_type, balance):
        thai_console_log(f"บัญชี {account_type} | Balance: ${balance:.2f}")

    @staticmethod
    def show_time_offset(offset):
        thai_console_log(f"Time Sync : {offset:.3f}s")

    @staticmethod
    def show_trading_mode(mode, stake, profit_pct, loss_pct, max_conc, trade_hours):
        thai_console_log(f"Trading Mode: {mode} [Stake:{stake}][Profit:{profit_pct}%][Loss:{loss_pct}%][Orderlimit:{max_conc}][Time:{trade_hours}]")

    @staticmethod
    def show_ai_checking():
        thai_console_log("ตรวจเช็คความพร้อม DEEPSEEK AI")

    @staticmethod
    def show_ai_failed():
        thai_console_log("Failed to connect to AI. System stopped.")

    @staticmethod
    def show_ai_prompt_sent(count=0, skipped_symbols=None):
        if skipped_symbols is None:
            skipped_symbols = []
        
        msg = f"✅ ส่งคำสั่ง Prompt เข้า DeepSeek Agent สำเร็จ ({count} รายการ)!"
        if skipped_symbols:
            msg += f" | ⚠️ ข้ามรอบนี้: {', '.join(skipped_symbols)} (ทำงานค้างอยู่)"
        
        thai_console_log(msg)

    @staticmethod
    def show_ai_reply(reply):
        thai_console_log(f'"{reply}"')

    @staticmethod
    def show_asset_list(symbols):
        thai_console_log(f"ตรวจพบรายการสินทรัพย์ : {', '.join(symbols)}")

    @staticmethod
    def show_data_prep_start(symbols):
        thai_console_log(f"กำลังเตรียมข้อมูลสินทรัพย์ {len(symbols)} รายการ : {', '.join(symbols)}")

    @staticmethod
    def show_data_prep_result(ready_count, not_ready_count):
        thai_console_log(f"ข้อมูลพร้อมเทรด {ready_count} รายการ  ไม่พร้อมเทรด {not_ready_count} รายการ")

    @staticmethod
    def show_mode_summary(stake, profit_pct, loss_pct, max_conc, trade_hours):
        pass # Merged into show_trading_mode

    @staticmethod
    def show_news_status(msg):
        thai_console_log(msg)
    
    @staticmethod
    def show_calendar_status(msg):
        thai_console_log(msg)
    
    @staticmethod
    def show_balance(balance):
        thai_console_log(f"💰 ยอดเงินในระบบ: ${balance:.2f}")

    @staticmethod
    def show_countdown(remaining, target_str):
        thai_console_log(f"เข้าสู่การวิเคราะห์สัญญาณในอีก {remaining} วินาที  (เริ่ม {target_str})")

    @staticmethod
    def show_insight(source, action, confidence):
        thai_console_log(f"{source}: {action} ({confidence}%)")

    @staticmethod
    def show_order_execution(action, symbol, expiry_time):
        thai_console_log(f"ยิงออเดอร์ {action} {symbol} ({expiry_time} นาที)")

    @staticmethod
    def show_order_success(order_id):
        thai_console_log(f"   └─ ออเดอร์เข้าสำเร็จ (ID: {order_id})")

    @staticmethod
    def show_order_failed(symbol, reason):
        thai_console_log(f"Execution failed for {symbol}: {reason}")

    @staticmethod
    def show_signal_only(action, symbol, expiry_time, mode):
        thai_console_log(f"[SIGNAL ONLY] {action} {symbol} ({expiry_time} นาที) -> ไม่ได้ยิงออเดอร์ (Mode: {mode})")

    @staticmethod
    def show_trade_result(won, symbol, order_id, pnl):
        status = 'ชนะ' if won else 'แพ้'
        if pnl == 0:
            status = 'เสมอ'
        thai_console_log(f"{status} {symbol} (ID: {order_id}) | PnL: {pnl:.2f}")

    @staticmethod
    def show_prices_and_balance(prices_dict, balance):
        try:
            price_parts = [f"{sym}:{price:.5f}" for sym, price in prices_dict.items()]
            price_str = "][".join(price_parts)
            balance_str = f"${balance:.2f}" if balance is not None else "N/A"
            thai_console_log(f"[{price_str}] :: TOTAL={balance_str}")
        except Exception as e:
            # Log error to file and continue with basic output
            logging.getLogger("FINALBOT").error(f"Error in show_prices_and_balance: {e}")
            # Zero Tolerance: must show price information
            raise RuntimeError(f"Price display failed: {e}")

    @staticmethod
    def show_stopping():
        thai_console_log("Stopping bot...")


@dataclass
class StrategyStats:
    """Statistics for a single strategy."""
    name: str
    version: str
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0
    trades_by_symbol: Dict[str, int] = field(default_factory=dict)
    pnl_by_symbol: Dict[str, float] = field(default_factory=dict)
    
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0
        return self.wins / self.total_trades
    
    @property
    def pnl_per_trade(self) -> float:
        if self.total_trades == 0:
            return 0
        return self.total_pnl / self.total_trades


class AdvancedDashboard:
    """
    Compare multiple strategies and analyze performance.
    """
    
    def __init__(self):
        """Initialize dashboard."""
        self.strategies: Dict[str, StrategyStats] = {}
        self.correlation_data: Dict[str, List[float]] = {}
        self.ml_metrics: Dict[str, float] = {}
    
    def register_strategy(self, name: str, version: str):
        """Register strategy for tracking."""
        key = f"{name}_v{version}"
        self.strategies[key] = StrategyStats(name=name, version=version)
        logger.info(f" Strategy registered: {key}")
    
    def record_trade(self, strategy_key: str, symbol: str, result: str, pnl: float):
        """Record trade result."""
        if strategy_key not in self.strategies:
            return
        
        stats = self.strategies[strategy_key]
        stats.total_trades += 1
        
        if result == "WIN":
            stats.wins += 1
        else:
            stats.losses += 1
        
        stats.total_pnl += pnl
        
        # Track by symbol
        if symbol not in stats.trades_by_symbol:
            stats.trades_by_symbol[symbol] = 0
            stats.pnl_by_symbol[symbol] = 0
        
        stats.trades_by_symbol[symbol] += 1
        stats.pnl_by_symbol[symbol] += pnl
    
    def get_strategy_comparison(self) -> Dict:
        """Compare all strategies."""
        comparison = {}
        
        for key, stats in self.strategies.items():
            comparison[key] = {
                'name': stats.name,
                'version': stats.version,
                'total_trades': stats.total_trades,
                'win_rate': f"{stats.win_rate * 100:.1f}%",
                'total_pnl': f"{stats.total_pnl:.2f}",
                'pnl_per_trade': f"{stats.pnl_per_trade:.2f}",
                'symbol_performance': stats.pnl_by_symbol,
            }
        
        return comparison
    
    def get_symbol_performance(self) -> Dict[str, Dict]:
        """Get performance by symbol across all strategies."""
        symbols_perf = {}
        
        for strat_key, stats in self.strategies.items():
            for symbol, pnl in stats.pnl_by_symbol.items():
                if symbol not in symbols_perf:
                    symbols_perf[symbol] = {
                        'total_pnl': 0,
                        'strategy_count': 0,
                    }
                
                symbols_perf[symbol]['total_pnl'] += pnl
                symbols_perf[symbol]['strategy_count'] += 1
        
        return symbols_perf
    
    def record_ml_metric(self, metric_name: str, value: float):
        """Record ML optimization metric."""
        self.ml_metrics[metric_name] = value
        logger.info(f" ML Metric: {metric_name} = {value:.3f}")
    
    def generate_report(self) -> str:
        """Generate summary report."""
        report = f"\n{'='*60}\n"
        report += " ADVANCED ANALYTICS DASHBOARD\n"
        report += f"{'='*60}\n\n"
        
        # Strategy comparison
        report += " STRATEGY COMPARISON\n"
        report += f"{'-'*60}\n"
        for key, stats in self.strategies.items():
            report += f"{key}:\n"
            report += f"  Trades: {stats.total_trades} | WR: {stats.win_rate*100:.1f}%\n"
            report += f"  P&L: {stats.total_pnl:.2f} | Per Trade: {stats.pnl_per_trade:.2f}\n"
        
        # Symbol performance
        report += f"\n{'='*60}\n"
        report += " SYMBOL PERFORMANCE\n"
        report += f"{'-'*60}\n"
        perf = self.get_symbol_performance()
        for symbol, data in perf.items():
            report += f"{symbol}: P&L={data['total_pnl']:.2f} ({data['strategy_count']} strategies)\n"
        
        # ML metrics
        report += f"\n{'='*60}\n"
        report += " ML OPTIMIZATION METRICS\n"
        report += f"{'-'*60}\n"
        for metric, value in self.ml_metrics.items():
            report += f"{metric}: {value:.3f}\n"
        
        report += f"{'='*60}\n"
        return report
