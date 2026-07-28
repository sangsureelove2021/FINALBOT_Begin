"""
Advanced Analytics Dashboard

Compare strategies, analyze correlation, ML metrics.
"""

import sys
import os
import threading
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

def setup_logging():
    """Setup logging to both console and file."""
    # Create logs directory if not exists
    log_dir = "all_filelogs/system_logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),  # Console
            logging.FileHandler(log_file)      # File
        ]
    )
    
    logger.info(f"Logging to file: {log_file}")

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

_PRINT_LOCK = threading.Lock()
_LOGGING_INITIALIZED = False

def setup_logging():
    global _LOGGING_INITIALIZED
    if _LOGGING_INITIALIZED:
        return
    
    sys.stdout = SafeStreamWrapper(sys.stdout)
    sys.stderr = SafeStreamWrapper(sys.stderr)

    os.makedirs("all_filelogs/system_logs", exist_ok=True)
    log_file_name = f"all_filelogs/system_logs/bot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        handlers=[
            logging.FileHandler(log_file_name, encoding='utf-8')
        ]
    )
    _LOGGING_INITIALIZED = True

def thai_console_log(msg: str):
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
        # Ultimate fallback - write to file only
        try:
            logging.getLogger("FINALBOT").error(f"Console output error: {e}")
            logging.getLogger("FINALBOT").info(msg)
        except:
            pass  # Silent fallback

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
            # Fallback to simple output
            try:
                print(f"PRICE UPDATE: Balance=${balance:.2f}")
            except:
                pass  # Silent fallback

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
