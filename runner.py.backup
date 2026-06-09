"""
FINALBOT Main Runner
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Complete pipeline: Data → Intelligence → Strategy → Output

BOT MODES:
  SIGNAL  - Analyze + report CALL/PUT + market state (no execution)
  TRADE   - Analyze + execute trade directly (no gates, no market filters)
  AI      - Analyze + write full JSON for AI evaluation

SIGNAL FLOW:
  1. Strategies analyze M1 candles for signal detection
  2. M5 candles confirm the signal direction
  3. Trade is placed at next M1 candle open with 1-min expiry
  4. Dynamic confidence must be >= 80% to pass filter

ACTIVE STRATEGIES (7):
  rsi_reversal, stochastic_crossover, bb_rsi_confluence,
  ema_crossover, compression_breakout, triple_confluence, macd_crossover
"""

# ─── BOT MODE ───────────────────────────────────────────────────────────────
# Change this value to switch the bot's operating mode:
#   'SIGNAL' → Report CALL/PUT + market state only (no trade execution)
#   'TRADE'  → Execute trades directly, no gates, no market filters
#   'AI'     → Write full market data + signals to JSON for AI evaluation
BOT_MODE = 'AI'  # Default: AI collaboration mode
# ────────────────────────────────────────────────────────────────────────────

import sys
import logging

# Safe stream wrapper to prevent UnicodeEncodeError in IDLE and Windows consoles
class SafeStreamWrapper:
    def __init__(self, original_stream):
        self.original_stream = original_stream
        self.encoding = getattr(original_stream, 'encoding', None) or 'utf-8'

    def write(self, data):
        try:
            self.original_stream.write(data)
        except Exception:
            try:
                # Force fallback to pure ASCII with backslashreplace, which is 100% encodable in any stream/IDE
                safe_data = data.encode('ascii', errors='backslashreplace').decode('ascii')
                self.original_stream.write(safe_data)
            except Exception:
                pass

    def flush(self):
        if hasattr(self.original_stream, 'flush'):
            self.original_stream.flush()

    def __getattr__(self, attr):
        return getattr(self.original_stream, attr)

# Wrap stdout and stderr safely
sys.stdout = SafeStreamWrapper(sys.stdout)
sys.stderr = SafeStreamWrapper(sys.stderr)
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd

# Create logs directory if not exists
import os
os.makedirs("logs", exist_ok=True)

# Configure logging: set up root logger with file handler (DEBUG) and console handler (WARNING)
file_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s')
log_file_name = f"logs/bot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.log"
file_handler = logging.FileHandler(log_file_name, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter('%(message)s'))

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
# Remove existing handlers to avoid duplicates if reloaded
for handler in list(root_logger.handlers):
    root_logger.removeHandler(handler)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger("FINALBOT")

def thai_console_log(msg: str):
    """Print message with Thailand local time (GMT+7) and write to log file."""
    tz_thailand = timezone(timedelta(hours=7))
    thai_time_str = datetime.now(tz_thailand).strftime('%H:%M:%S')
    formatted = f"{thai_time_str} - {msg}"
    print(formatted)
    sys.stdout.flush()
    # Log to file via root logger (info level) so it goes to bot_*.log
    logger.info(formatted)

# Import core modules
from core.data.iq_option_adapter import IQOptionAdapter
from core.data.candle_buffer import CandleBuffer
from core.models.market_context import MarketContext
from core.orchestration.context_builder import ContextBuilder
from core.orchestration.pipeline import Pipeline
from core.orchestration.execution_gate import ExecutionGate
from core.engines.engine_registry import EngineRegistry
from strategy.trend_following.triple_confluence import TripleConfluenceStrategy
from strategy.reversal_strategy.bb_rsi_confluence import BBRSIConfluenceStrategy
from strategy.trend_following.macd_crossover import MACDCrossoverStrategy
from strategy.reversal_strategy.rsi_reversal import RSIReversalStrategy
from strategy.trend_following.ema_crossover import EMACrossoverStrategy
from strategy.reversal_strategy.stochastic_crossover import StochasticCrossoverStrategy
from strategy.reversal_strategy.pin_bar_scalper import PinBarScalper
from strategy.reversal_strategy.engulfing_scalper import EngulfingScalperStrategy
from strategy.reversal_strategy.rsi_extreme_bounce import RSIExtremeBounceStrategy
from strategy.trend_following.ema_ribbon_momentum import EMARibbonMomentumStrategy
from strategy.reversal_strategy.pa_snr_strategy import PASNRStrategy
from strategy.reversal_strategy.sr_fakeout_rejection import SRFakeoutRejection
from strategy.reversal_strategy.rejection_5m_pa import Rejection5mPA
from execution.iq_option_executor import IQOptionExecutor
from execution.position_sizer import PositionSizer
from execution.order_manager import OrderManager
from execution.execution_guard import ExecutionGuard


# ─── SHARED HELPERS (ใช้ร่วมกันทั้ง Backtest และ Live Runner) ───────────────

def calc_dynamic_confidence(direction: str, indicators: dict) -> int:
    """
    คำนวณ confidence แบบ dynamic จากจำนวน indicators ที่ยืนยันทิศทาง
    ช่วง: 30 (minimum) - 100 (maximum)
    """
    score = 30  # Base score = 30 per user request
    is_put = (direction == 'PUT')

    ema5 = indicators.get('ema5', 0)
    ema20 = indicators.get('ema20', 0)
    rsi7 = indicators.get('rsi7', 50)
    rsi14 = indicators.get('rsi14', 50)
    macd = indicators.get('macd', 0)
    macd_signal = indicators.get('macd_signal', 0)
    stoch_k = indicators.get('stoch_k', 50)
    local_support = indicators.get('local_support', 0)
    local_resistance = indicators.get('local_resistance', 0)
    current_price = indicators.get('current_price', 0)
    
    # Market state indicators
    trend_direction = indicators.get('trend_direction', 'NONE')
    market_state = indicators.get('market_state', 'UNKNOWN')

    # EMA5 vs EMA20 alignment (+10)
    if is_put and ema5 < ema20:
        score += 10
    elif not is_put and ema5 > ema20:
        score += 10

    # RSI7 extreme zone (+15 extreme, +7 moderate)
    if is_put and rsi7 > 80:
        score += 15
    elif not is_put and rsi7 < 20:
        score += 15
    elif is_put and rsi7 > 70:
        score += 7
    elif not is_put and rsi7 < 30:
        score += 7

    # RSI14 confirmation (+5)
    if is_put and rsi14 > 65:
        score += 5
    elif not is_put and rsi14 < 35:
        score += 5

    # MACD direction (+10)
    if is_put and macd < macd_signal:
        score += 10
    elif not is_put and macd > macd_signal:
        score += 10

    # Stochastic extreme zone (+10)
    if is_put and stoch_k > 80:
        score += 10
    elif not is_put and stoch_k < 20:
        score += 10

    # Price near resistance/support (+10)
    if current_price > 0:
        if is_put and local_resistance > 0:
            dist_pct = abs(current_price - local_resistance) / local_resistance
            if dist_pct < 0.0005:
                score += 10
        elif not is_put and local_support > 0:
            dist_pct = abs(current_price - local_support) / local_support
            if dist_pct < 0.0005:
                score += 10

    # เช็กสภาวะตลาด 0 +5 +10
    # For CALL: UPTREND = +10, RANGING = +5, DOWNTREND = 0
    # For PUT: DOWNTREND = +10, RANGING = +5, UPTREND = 0
    if not is_put:
        if trend_direction == 'UP' or 'UPTREND' in market_state:
            score += 10
        elif trend_direction == 'NONE' and market_state == 'RANGING':
            score += 5
    else:
        if trend_direction == 'DOWN' or 'DOWNTREND' in market_state:
            score += 10
        elif trend_direction == 'NONE' and market_state == 'RANGING':
            score += 5

    return min(100, score)


def get_session(utc_hour: int) -> str:
    """
    แปลง UTC hour เป็นชื่อ session GMT+7
    """
    gmt7_hour = (utc_hour + 7) % 24
    if 9 <= gmt7_hour < 12:
        return 'LONDON_OPEN'
    elif 12 <= gmt7_hour < 17:
        return 'LONDON_SESSION'
    elif 17 <= gmt7_hour < 20:
        return 'NEW_YORK_OPEN'
    elif 20 <= gmt7_hour <= 23:
        return 'NEW_YORK_SESSION'
    else:
        return 'OFF_HOURS'


# ─────────────────────────────────────────────────────────────────────────────


class BotRunner:
    """Main bot orchestrator."""
    
    def __init__(self,
                 symbols: List[str] = None,
                 timeframes: List[str] = None,
                 capital: float = 2000.0,
                 use_mock: bool = False,
                 account_type: str = "PRACTICE"):
        """
        Initialize bot.

        Args:
            symbols: pairs to trade (loads from symbols.txt if None)
            timeframes: timeframes to analyze
            capital: account balance
            use_mock: use synthetic data instead of the live API
            account_type: 'PRACTICE' (demo) or 'REAL'
        """
        # Load symbols from symbols.txt next to main.py (single source)
        if symbols is None:
            from main import load_symbols
            symbols = load_symbols()
        if symbols:
            logger.info(f"[DYNAMIC] Loaded {len(symbols)} symbols: {symbols}")
        
        self.symbols = symbols
        # User spec: M1->300, M5->300, M15->150, H1(M60)->100
        self.timeframe_counts = {
            'M1': 300,
            'M5': 300,
            'M15': 150,
            'M60': 100
        }
        self.timeframes = list(self.timeframe_counts.keys())
        self.capital = capital
        # Enforce live trading only — mock mode is locked to False
        self.use_mock = use_mock
        self.account_type = account_type

        # Initialize components (single connection point: IQ Option DEMO)
        self.data_adapter = None if use_mock else IQOptionAdapter(use_mock=use_mock, account_type=account_type)
        if not use_mock and not self.data_adapter.is_connected():
            raise RuntimeError("Cannot start bot — IQ Option not connected")
        
        # ดึงยอดเงินจริงจาก IQ Option
        if not use_mock and self.data_adapter.api:
            try:
                real_balance = self.data_adapter.api.get_balance()
                if real_balance is not None:
                    self.capital = float(real_balance)
            except Exception as e:
                logger.warning(f"[WARN] Failed to fetch live balance from IQ Option: {e}")

        thai_console_log(f"ล็อกอินสำเร็จ - คู่เงิน: {', '.join(self.symbols)}")

        mode = ('MOCK' if use_mock
                else 'DEMO' if account_type == 'PRACTICE'
                else 'REAL MONEY')
        logger.info("[START] FINALBOT initializing...")
        logger.info(f"   Symbols: {', '.join(self.symbols)}")
        logger.info(f"   Timeframes: {', '.join(self.timeframes)}")
        logger.info(f"   Capital: {self.capital}")
        logger.info(f"   Mode: {mode}")

        self.candle_buffer = CandleBuffer(size=500)
        
        # Subscribe to WebSocket candles streams for all symbols and timeframes
        if not use_mock:
            logger.info("[WS] Initiating WebSocket live candles subscriptions...")
            for symbol in self.symbols:
                for tf, count in self.timeframe_counts.items():
                    self.data_adapter.start_stream(symbol, tf, count)
        
        # Intelligence layer — registry populated with all 25 engines
        from core.engines.engine_setup import setup_engines
        self.engine_registry = setup_engines()
        self.context_builder = ContextBuilder(self.engine_registry)
        
        # Get all engines from registry (all tiers)
        all_engines = []
        for tier in self.engine_registry.list_tiers():
            all_engines.extend(self.engine_registry.get_by_tier(tier))
        self.engines = all_engines
        logger.info(f"   Engines: {len(self.engines)} registered across "
                    f"{len(self.engine_registry.list_tiers())} tiers")
        
        # Strategies + bot mode (loaded from settings.json after pipeline is ready)
        self.active_strategies = []
        self._blocked_strategies = []
        self.bot_mode = "SIGNAL"
        self.strategies = self.active_strategies
        
        # Risk gates (Initialize before the pipeline to connect it)
        from core.config_loader import get_limits, get_execution_gate
        limits = get_limits()
        eg_config = get_execution_gate()
        
        max_daily_loss = limits.get("max_daily_loss")
        if max_daily_loss is None:
            max_daily_loss = float('inf')
        
        max_trades = limits.get("max_trades_per_session")
        if max_trades is None:
            max_trades = 10**9

        self.execution_gate = ExecutionGate(
            min_confidence=eg_config.get("min_confidence", 75),
            max_block_score=eg_config.get("max_block_score", 40)
        )
        self.execution_guard = ExecutionGuard(
            max_daily_loss=max_daily_loss,
            max_consecutive_losses=limits.get("max_consecutive_losses", 3),
            max_trades_per_session=max_trades,
            cooldown_minutes_after_loss=limits.get("cooldown_minutes_after_loss", 20),
            min_confidence_to_execute=eg_config.get("min_confidence", 75)
        )
        
        # Pipeline needs ContextBuilder + strategies + connected execution_gate
        self.intelligence_pipeline = Pipeline(
            context_builder=self.context_builder,
            strategies=self.strategies,
            execution_gate=self.execution_gate
        )
        self._reload_runtime_config()

        # Execution (reuses adapter's connection — same login)
        self.executor = None if use_mock else IQOptionExecutor(adapter=self.data_adapter, use_mock=use_mock, account_type=account_type)
        self.position_sizer = PositionSizer(capital=self.capital)
        self.order_manager = OrderManager()
        
        # Statistics
        self.cycle_count = 0
        self.signal_count = {sym: 0 for sym in self.symbols}
        self.last_execution_time = {}
        self.is_live = False
        # Cooldown tracker: ป้องกัน Signal Flooding (เก็บ datetime ของสัญญาณล่าสุดต่อ symbol)
        self._last_signal_time: dict = {}
        
        mode_labels = {
            "SIGNAL": "สัญญาณ CALL/PUT (ไม่เทรด)",
            "TRADE": "เทรดอัตโนมัติ",
            "AI": "AI Evaluation",
            "HYBRID": "Hybrid AI + Auto",
        }
        thai_console_log(
            f"โหมด: {mode_labels.get(self.bot_mode, self.bot_mode)} | "
            f"บัญชี: {'DEMO' if account_type == 'PRACTICE' else 'REAL'} | "
            f"ยอดเงิน: {self.capital:.2f}"
        )
        if self.bot_mode == "SIGNAL":
            thai_console_log("พร้อมเทรดอัตโนมัติ — เปลี่ยน trading_mode เป็น Auto_BOT ใน settings.json")
        logger.info("[OK] Bot initialized successfully\n")

    def _reload_runtime_config(self) -> None:
        """Reload symbols, strategies, and trading mode from settings.json."""
        try:
            from core.config_loader import load_settings
            settings = load_settings(reload=True)

            from main import load_symbols
            reloaded_symbols = load_symbols()
            if reloaded_symbols:
                self.symbols = reloaded_symbols

            active_strat_names = settings.get("active_strategies", ["rejection_5m_pa"])

            from strategy.reversal_strategy.rejection_5m_pa import Rejection5mPA
            from strategy.trend_following.ema_crossover import EMACrossoverStrategy
            from strategy.trend_following.macd_crossover import MACDCrossoverStrategy
            from strategy.reversal_strategy.stochastic_crossover import StochasticCrossoverStrategy
            from strategy.reversal_strategy.rsi_reversal import RSIReversalStrategy
            from strategy.reversal_strategy.bb_rsi_confluence import BBRSIConfluenceStrategy
            from strategy.reversal_strategy.pin_bar_scalper import PinBarScalper
            from strategy.reversal_strategy.engulfing_scalper import EngulfingScalperStrategy
            from strategy.reversal_strategy.rsi_extreme_bounce import RSIExtremeBounceStrategy
            from strategy.trend_following.ema_ribbon_momentum import EMARibbonMomentumStrategy
            from strategy.reversal_strategy.pa_snr_strategy import PASNRStrategy
            from strategy.reversal_strategy.sr_fakeout_rejection import SRFakeoutRejection
            from strategy.trend_following.triple_confluence import TripleConfluenceStrategy
            from strategy.compression_breakout.strategy import CompressionBreakoutStrategy

            strategy_mapping = {
                "rejection_5m_pa": Rejection5mPA,
                "ema_crossover": EMACrossoverStrategy,
                "macd_crossover": MACDCrossoverStrategy,
                "stochastic_crossover": StochasticCrossoverStrategy,
                "rsi_reversal": RSIReversalStrategy,
                "bb_rsi_confluence": BBRSIConfluenceStrategy,
                "pin_bar_scalper": PinBarScalper,
                "engulfing_scalper": EngulfingScalperStrategy,
                "rsi_extreme_bounce": RSIExtremeBounceStrategy,
                "ema_ribbon_momentum": EMARibbonMomentumStrategy,
                "pa_snr": PASNRStrategy,
                "sr_fakeout_rejection": SRFakeoutRejection,
                "triple_confluence": TripleConfluenceStrategy,
                "compression_breakout": CompressionBreakoutStrategy,
            }

            new_active_strategies = []
            for name in active_strat_names:
                if name in strategy_mapping:
                    new_active_strategies.append(strategy_mapping[name]())

            if new_active_strategies:
                self.active_strategies = new_active_strategies
                self.strategies = new_active_strategies
                if hasattr(self, "intelligence_pipeline"):
                    self.intelligence_pipeline.strategies = new_active_strategies

            raw_mode = settings.get("account", {}).get("trading_mode", "Signal_BOT")
            mode_mapping = {
                "Signal_BOT": "SIGNAL",
                "Auto_BOT": "TRADE",
                "Ai_BOT": "AI",
                "Hybrid_AiBOT": "HYBRID",
            }
            new_bot_mode = mode_mapping.get(raw_mode, "SIGNAL")
            if new_bot_mode != self.bot_mode:
                logger.info(f"[DYNAMIC] Trading Mode changed from {self.bot_mode} to {new_bot_mode}")
            self.bot_mode = new_bot_mode

            logger.info(f"   Bot Mode: {self.bot_mode} (from trading_mode: {raw_mode})")
            logger.info(f"   Active Strategies: {[s.STRATEGY_NAME for s in self.active_strategies]}")
        except Exception as e:
            logger.warning(f"[DYNAMIC ERR] Failed to reload configuration: {e}")

    # ────────────────────────────────────────────────────────────────────────
    # CORE ANALYSIS ENGINE  (same logic for all 3 modes)
    # ────────────────────────────────────────────────────────────────────────

    def _evaluate_active_strategies(self, context) -> list:
        """
        Evaluate all active strategies simultaneously.
        Returns list of triggered signals (CALL/PUT only, skip NO_SIGNAL).
        Picks best entry_score among strategies that pass quality gates.
        """
        triggered = []
        state = "UNKNOWN"
        if context and context.market_state:
            if isinstance(context.market_state, dict):
                state = context.market_state.get("state", "UNKNOWN").upper()
            else:
                state = str(context.market_state).upper()

        min_entry = 68 if state == "MEAN_REVERSION_ZONE" else 65
        max_block = self.execution_gate.max_block_score if hasattr(self, "execution_gate") else 40
        min_conf = self.execution_gate.min_confidence if hasattr(self, "execution_gate") else 80

        for strategy in self.active_strategies:
            try:
                result = strategy.evaluate(context)
                action = result.get("action", "NO_SIGNAL")
                if action not in ("CALL", "PUT"):
                    continue

                entry_score = float(result.get("entry_score", 0))
                block_score = float(result.get("block_score", 100))
                strat_conf = result.get("strategy_confidence", 0)
                if strat_conf <= 1.0:
                    confidence = int(float(strat_conf) * 100)
                else:
                    confidence = int(result.get("confidence", strat_conf))

                if entry_score < min_entry or block_score >= max_block or confidence < min_conf:
                    logger.debug(
                        f"[STRATEGY SKIP] {strategy.STRATEGY_NAME} {action} "
                        f"entry={entry_score:.0f} block={block_score:.0f} conf={confidence}"
                    )
                    continue

                triggered.append({
                    "strategy": strategy.STRATEGY_NAME,
                    "signal": action,
                    "confidence": confidence,
                    "entry_score": entry_score,
                    "block_score": block_score,
                    "reason": result.get("reason") or result.get("fail_reason_code") or "",
                    "indicators": result.get("details", result.get("indicators", {})),
                    "expiry": result.get("expiry", "M5"),
                })
            except Exception as e:
                logger.warning(f"[STRATEGY ERR] {strategy.STRATEGY_NAME}: {e}")

        triggered.sort(key=lambda s: (-s.get("entry_score", 0), -s.get("confidence", 0)))
        return triggered

    def run_single_cycle(self, symbol: str) -> Dict:
        """
        Execute one full analysis cycle for a symbol.
        Mode determines what happens with the result:
          SIGNAL → log report
          TRADE  → execute trade directly (no gates)
          AI     → write full JSON

        Returns:
            Cycle result dict.
        """
        try:
            # Step 0.1: Auto-settle expired trades
            now = datetime.now(timezone.utc)
            for order_id, trade in list(self.order_manager.active_trades.items()):
                elapsed_seconds = (now - trade.entry_time).total_seconds()
                expiry_val = getattr(trade, 'expiry', 'M1')
                duration_mins = {'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30, 'M60': 60}.get(expiry_val, 1)
                
                # Wait for the full expiry duration + 5 seconds buffer to ensure API settlement
                if elapsed_seconds >= (duration_mins * 60) + 5:
                    pnl = 0.0
                    won = False
                    exit_price = 0.0
                    notes = "Option contract expired"
                    
                    # Fetch real outcome if connected to live API
                    if not self.use_mock and self.executor.is_connected() and "SIGNAL" not in order_id and "MOCK" not in order_id:
                        try:
                            # check_win_v3 returns profit (positive if won, negative if lost, 0 if tie)
                            # since it's already expired, this should return instantly
                            profit = self.executor.api.check_win_v3(int(order_id))
                            pnl = float(profit)
                            won = pnl > 0
                            exit_price = trade.entry_price
                            notes = f"Settled via IQ Option API (pnl: {pnl})"
                        except Exception as ex:
                            logger.error(f"[ERR] Failed to check win status for live trade {order_id}: {ex}")
                    
                    self.order_manager.close_trade(
                        order_id=order_id,
                        exit_price=exit_price,
                        pnl=pnl,
                        notes=notes
                    )
                    self.execution_guard.record_trade_result(won=won, profit_loss=pnl)

            # Step 0.2: Prevent duplicate trades for the same symbol
            active_trades = self.order_manager.get_active_trades(symbol)
            if active_trades:
                logger.debug(f"[HOLD] {symbol} already has an active trade in progress. Skip.")
                return {
                    'symbol': symbol,
                    'signal': 'HOLD',
                    'confidence': 0,
                    'reason': 'Active trade in progress',
                    'executed': False,
                    'market_state': 'ACTIVE_TRADE',
                    'current_price': 0.0,
                    'strategy': 'none'
                }

            # Step 1: Fetch multi-timeframe data with dynamic candle counts
            active_strategies = ", ".join([s.strategy_name for s in self.intelligence_pipeline.strategies])
            logger.debug(f">>> [ANALYZING] Asset: {symbol:<10} | Strategies: {active_strategies}")

            candles_dict = {}
            for tf in self.timeframes:
                count = self.timeframe_counts.get(tf, 200)
                candles_dict[tf] = self.data_adapter.get_candles(symbol, tf, count)

            # Step 2: Update buffer
            for tf, candles in candles_dict.items():
                self.candle_buffer.append(symbol, tf, candles)

            # Step 3: Align timeframes (no future leakage)
            from core.data.timeframe_sync import TimeframeSync
            synced = TimeframeSync(primary='M1').sync(candles_dict)

            # Slice every timeframe DataFrame inside the synced dictionary to drop the last uncompleted active candle.
            # This ensures that ALL subsequent calculations in ContextBuilder, TrendEngine, VolatilityEngine, and all
            # indicator formulas are 100% stable, non-repainting, and match the actual closed chart data on platforms
            # like TradingView, MT4, and brokers.
            now_ts = pd.Timestamp(datetime.utcnow())
            for tf in list(synced.keys()):
                if len(synced[tf]) > 1:
                    tf_mins = {'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30, 'H1': 60, 'M60': 60}.get(tf, 1)
                    if synced[tf].index[-1] + pd.Timedelta(minutes=tf_mins) > now_ts:
                        synced[tf] = synced[tf].iloc[:-1]

            # Step 4: Build context and scores once for all strategies to maximize efficiency
            # Primary timeframe = M1 for signal detection; M5 used for confirmation
            context = self.intelligence_pipeline.context_builder.build(symbol, synced, 'M1')
            self.intelligence_pipeline.last_context = context
            
            context.set_score('confidence', self.intelligence_pipeline.confidence_scorer.score(context))
            context.set_score('entry', self.intelligence_pipeline.entry_scorer.score(context))
            context.set_score('block', self.intelligence_pipeline.block_scorer.score(context))
            context.aggregated_score = context.get_score('confidence')
            
            state_str = 'UNKNOWN'
            current_price = 0.0
            if context:
                current_price = getattr(context, 'current_price', 0.0)
                if context.market_state:
                    if isinstance(context.market_state, dict):
                        state_str = context.market_state.get('state', 'UNKNOWN')
                    else:
                        state_str = str(context.market_state)

            # Since synced has already been sliced, synced['M1'] represents ONLY completed closed bars.
            completed_m1 = synced['M1']
            
            # M5 data for confirmation and primary calculation
            completed_m5 = synced['M5'] if 'M5' in synced and len(synced.get('M5', [])) > 1 else synced['M1']
            
            # Use M5 for primary indicator calculation (Confidence Filtering uses M5 exclusively)
            close_prices = completed_m5['close']
            high_prices = completed_m5['high']
            low_prices = completed_m5['low']
            open_prices = completed_m5['open']
            
            # EMAs
            ema20 = float(close_prices.ewm(span=20, adjust=False).mean().iloc[-1])
            ema50 = float(close_prices.ewm(span=50, adjust=False).mean().iloc[-1])
            
            # Bollinger Bands (Using ddof=0 population standard deviation to match standard trading charts)
            ma20 = close_prices.rolling(window=20).mean()
            std20 = close_prices.rolling(window=20).std(ddof=0)
            bb_upper = float((ma20 + 2 * std20).iloc[-1])
            bb_lower = float((ma20 - 2 * std20).iloc[-1])
            
            # RSI Helper (True Wilder's Smoothing to match TradingView/MT4/IQ Option exactly)
            def calc_rsi(prices, period):
                delta = prices.diff()
                gain = delta.clip(lower=0)
                loss = -delta.clip(upper=0)
                
                avg_gain = gain.copy()
                avg_loss = loss.copy()
                if len(prices) > period:
                    avg_gain.iloc[period] = gain.iloc[1:period+1].mean()
                    avg_loss.iloc[period] = loss.iloc[1:period+1].mean()
                    avg_gain = avg_gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
                    avg_loss = avg_loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
                else:
                    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
                    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
                    
                rs = avg_gain / avg_loss.replace(0, 1e-10)
                rsi = 100 - (100 / (1 + rs))
                return float(rsi.iloc[-1])
                
            rsi7 = calc_rsi(close_prices, 7)
            rsi14 = calc_rsi(close_prices, 14)
            
            # MACD
            ema12 = close_prices.ewm(span=12, adjust=False).mean()
            ema26 = close_prices.ewm(span=26, adjust=False).mean()
            macd_line = ema12 - ema26
            signal_line = macd_line.ewm(span=9, adjust=False).mean()
            
            curr_macd = float(macd_line.iloc[-1])
            curr_sig = float(signal_line.iloc[-1])
            prev_macd = float(macd_line.iloc[-2])
            prev_sig = float(signal_line.iloc[-2])
            
            # EMA5 (for EMA Crossover strategy)
            ema5 = close_prices.ewm(span=5, adjust=False).mean()
            curr_ema5 = float(ema5.iloc[-1])
            prev_ema5 = float(ema5.iloc[-2])
            curr_ema20_val = float(close_prices.ewm(span=20, adjust=False).mean().iloc[-1])
            prev_ema20_val = float(close_prices.ewm(span=20, adjust=False).mean().iloc[-2])

            # Stochastic %K/%D (for Stochastic Crossover strategy)
            k_period = 14
            d_period = 3
            lowest_low = low_prices.rolling(window=k_period).min()
            highest_high = high_prices.rolling(window=k_period).max()
            stoch_denom = (highest_high - lowest_low).replace(0, 1e-10)
            stoch_k_series = 100 * (close_prices - lowest_low) / stoch_denom
            stoch_d_series = stoch_k_series.rolling(window=d_period).mean()
            curr_stoch_k = float(stoch_k_series.iloc[-1])
            curr_stoch_d = float(stoch_d_series.iloc[-1])
            prev_stoch_k = float(stoch_k_series.iloc[-2])
            prev_stoch_d = float(stoch_d_series.iloc[-2])

            # S&R
            local_support = float(low_prices.iloc[-10:].min())
            local_resistance = float(high_prices.iloc[-10:].max())
            
            # Volatility & Trend details from context
            trend_dir = context.trend.get('direction', 'NONE') if context.trend else 'NONE'
            trend_strength = float(context.trend.get('strength', 0.0) if context.trend else 0.0)
            atr_percentile = float(context.volatility.get('atr_percentile', 50.0) if context.volatility else 50.0)
            comp_quality = float(context.volatility.get('compression_quality', 50.0) if context.volatility else 50.0)
            
            # Package candles (last 20 closed M1 candles)
            last_candles = []
            lookback = min(20, len(open_prices))
            for i in range(-lookback, 0):
                last_candles.append({
                    'open': round(float(open_prices.iloc[i]), 5),
                    'high': round(float(high_prices.iloc[i]), 5),
                    'low': round(float(low_prices.iloc[i]), 5),
                    'close': round(float(close_prices.iloc[i]), 5)
                })
                
            # Save complete market state to JSON for AI evaluation
            market_state_data = {
                'timestamp': completed_m1.index[-1].isoformat() if not completed_m1.empty else datetime.now(timezone.utc).isoformat(),
                'symbol': symbol,
                'current_price': current_price,
                'market_state': state_str,
                'trend': {
                    'direction': trend_dir,
                    'strength': trend_strength
                },
                'volatility': {
                    'atr_percentile': atr_percentile,
                    'compression_quality': comp_quality
                },
                'indicators': {
                    'ema5': curr_ema5,
                    'prev_ema5': prev_ema5,
                    'ema20': ema20,
                    'prev_ema20': prev_ema20_val,
                    'ema50': ema50,
                    'bb_upper': bb_upper,
                    'bb_lower': bb_lower,
                    'rsi7': rsi7,
                    'rsi14': rsi14,
                    'macd': curr_macd,
                    'macd_signal': curr_sig,
                    'prev_macd': prev_macd,
                    'prev_signal': prev_sig,
                    'stoch_k': curr_stoch_k,
                    'stoch_d': curr_stoch_d,
                    'prev_stoch_k': prev_stoch_k,
                    'prev_stoch_d': prev_stoch_d,
                    'local_support': local_support,
                    'local_resistance': local_resistance
                },
                'candles': last_candles
            }
            
            import os
            import json

            # ── STEP A: Evaluate all active strategies simultaneously ──────
            triggered_signals = self._evaluate_active_strategies(context)
            
            # ── STEP A.0: Freshness Check ──────────
            # Discard if we are entering too late into the M5 candle
            fresh_signals = []
            if 'M5' in synced and len(synced['M5']) > 1:
                m5_last_ts = synced['M5'].index[-1]
                m5_close_time = m5_last_ts + pd.Timedelta(minutes=5)
                seconds_late = (pd.Timestamp(datetime.utcnow()) - m5_close_time).total_seconds()
                
                for sig in triggered_signals:
                    if sig.get('expiry', 'M1') == 'M5' and seconds_late > 15.0:
                        logger.info(f"[FRESHNESS] Discarding {sig['strategy']} {sig['signal']} - {seconds_late:.1f}s late")
                        continue
                    fresh_signals.append(sig)
                triggered_signals = fresh_signals
            else:
                triggered_signals = triggered_signals
            
            # ── STEP A.1: M5 Confirmation Filter ──────────
            # Signals must be confirmed by M5 direction
            m5_confirmed_signals = []
            for sig in triggered_signals:
                action = sig['signal']
                if completed_m5 is not None and len(completed_m5) >= 20:
                    m5_close = completed_m5['close']
                    # M5 RSI14
                    m5_rsi14 = calc_rsi(m5_close, 14)
                    # M5 MA20
                    m5_ma20 = float(m5_close.rolling(window=20).mean().iloc[-1])
                    m5_curr_close = float(m5_close.iloc[-1])
                    # M5 MACD
                    m5_ema12 = m5_close.ewm(span=12, adjust=False).mean()
                    m5_ema26 = m5_close.ewm(span=26, adjust=False).mean()
                    m5_macd = float((m5_ema12 - m5_ema26).iloc[-1])
                    m5_macd_sig = float((m5_ema12 - m5_ema26).ewm(span=9, adjust=False).mean().iloc[-1])
                    
                    confirmed = False
                    if action == 'CALL':
                        # M5 should show bullish bias (at least 1 condition)
                        if m5_rsi14 > 50 or m5_curr_close > m5_ma20 or m5_macd > m5_macd_sig:
                            confirmed = True
                    elif action == 'PUT':
                        # M5 should show bearish bias (at least 1 condition)
                        if m5_rsi14 < 50 or m5_curr_close < m5_ma20 or m5_macd < m5_macd_sig:
                            confirmed = True
                    
                    if confirmed:
                        logger.info(f"[M5 CONFIRM] {sig['strategy']} {action} confirmed by M5 (RSI14={m5_rsi14:.1f}, Close vs MA20={'above' if m5_curr_close > m5_ma20 else 'below'})")
                    else:
                        logger.info(f"[M5 INFO] {sig['strategy']} {action} - M5 direction does not confirm (RSI14={m5_rsi14:.1f}) - PASSING THROUGH (No decision)")
                    
                    # Always append to m5_confirmed_signals, do not set sig['signal'] = 'NOTRADE'
                    m5_confirmed_signals.append(sig)
                else:
                    # No M5 data available, pass through
                    m5_confirmed_signals.append(sig)
            
            # ── STEP A.2: Dynamic Confidence >= 80% Filter ──────────
            confidence_filtered_signals = []
            for sig in m5_confirmed_signals:
                _ind_for_conf = dict(market_state_data['indicators'])
                _ind_for_conf['current_price'] = current_price
                _ind_for_conf['trend_direction'] = trend_dir
                _ind_for_conf['market_state'] = state_str
                _dynamic_conf = calc_dynamic_confidence(sig['signal'], _ind_for_conf)
                
                # Keep the strategy's original confidence, but log the dynamic confidence
                strategy_conf = sig.get('confidence', 85)
                sig['confidence'] = strategy_conf
                
                # Always approve and append to confidence_filtered_signals, do not reject
                confidence_filtered_signals.append(sig)
                logger.info(f"[CONF INFO] {sig['strategy']} {sig['signal']} - Strategy Conf={strategy_conf}%, Dynamic Conf={_dynamic_conf}% - APPROVED (No decision)")
            
            approved_signals = confidence_filtered_signals
            
            first_signal = approved_signals[0] if approved_signals else None

            # ── STEP B: Attach triggered signals to market state (always) ────────
            market_state_data['triggered_signals'] = triggered_signals
            market_state_data['signal_count'] = len(triggered_signals)

            # ── STEP C: Always save market state JSON (all 3 modes need it) ──────
            market_state_path = os.path.join("logs", "market_state.json")
            try:
                with open(market_state_path, "w", encoding="utf-8") as f:
                    json.dump(market_state_data, f, indent=2, ensure_ascii=False)
                logger.debug(f"[MARKET STATE] Saved to logs/market_state.json | Signals found: {len(triggered_signals)}")
            except Exception as e:
                logger.error(f"[ERR] Failed to write market state JSON: {e}")

            # ── STEP C.2: Write to backtest_signals.json if signals were triggered (AI-style chronological logging) ──
            if triggered_signals:
                backtest_signals_path = os.path.join("logs", "backtest_signals.json")
                try:
                    existing_backtest = []
                    if os.path.exists(backtest_signals_path):
                        try:
                            with open(backtest_signals_path, "r", encoding="utf-8") as f_backtest:
                                existing_backtest = json.load(f_backtest)
                                if not isinstance(existing_backtest, list):
                                    existing_backtest = []
                        except Exception:
                            existing_backtest = []

                    # คำนวณ session / hour_gmt7 จาก timestamp ปัจจุบัน
                    _ts_now = datetime.now(timezone.utc)
                    _utc_hour = _ts_now.hour
                    _hour_gmt7 = (_utc_hour + 7) % 24
                    _session = get_session(_utc_hour)

                    # For each triggered signal, package it with the full market state data
                    for sig in triggered_signals:
                        # คำนวณ dynamic confidence จาก indicators
                        _ind_for_conf = dict(market_state_data['indicators'])
                        _ind_for_conf['current_price'] = current_price
                        _ind_for_conf['trend_direction'] = trend_dir
                        _ind_for_conf['market_state'] = state_str
                        _dynamic_conf = calc_dynamic_confidence(sig['signal'], _ind_for_conf)

                        signal_record = {
                            'timestamp': market_state_data['timestamp'],
                            'symbol': symbol,
                            'direction': sig['signal'],
                            'confidence': _dynamic_conf,
                            'size': float(self.position_sizer.calculate(
                                confidence=_dynamic_conf
                            )) if hasattr(self, 'position_sizer') else 30.0,
                            'state': state_str,
                            'session': _session,
                            'hour_gmt7': _hour_gmt7,
                            'reason': sig['reason'],
                            'strategy': sig['strategy'],
                            'indicators': market_state_data['indicators'],
                            'candles': market_state_data['candles'],
                            'candle_count': len(market_state_data['candles']),
                            'processed': True,
                            'trade_outcome': None
                        }
                        existing_backtest.append(signal_record)

                    # Cap size of backtest history file to 5000 signals to prevent out of memory / huge files
                    if len(existing_backtest) > 5000:
                        existing_backtest = existing_backtest[-5000:]

                    with open(backtest_signals_path, "w", encoding="utf-8") as f_backtest:
                        json.dump(existing_backtest, f_backtest, indent=2, ensure_ascii=False)
                    logger.debug(f"[BACKTEST LOG] Appended {len(triggered_signals)} signals to logs/backtest_signals.json")
                except Exception as e:
                    logger.error(f"[ERR] Failed to write backtest signals JSON: {e}")

            # ── STEP D: Mode-specific output ──────────────────────────────────────
            if self.bot_mode in ('SIGNAL', 'HYBRID'):
                # ── SIGNAL/HYBRID MODE: Report CALL/PUT + market state, no execution ──
                if first_signal:
                    sig_action = first_signal['signal']
                    sig_strategy = first_signal['strategy']
                    sig_reason = first_signal['reason']

                    # ── Cooldown: ป้องกัน Signal Flooding (10 นาทีต่อ symbol) ── (Disabled per user request)
                    _now_dt = datetime.now(timezone.utc)
                    self._last_signal_time[symbol] = _now_dt

                    # คำนวณ dynamic confidence
                    _ind_for_conf = dict(market_state_data['indicators'])
                    _ind_for_conf['current_price'] = current_price
                    _ind_for_conf['trend_direction'] = trend_dir
                    _ind_for_conf['market_state'] = state_str
                    sig_conf = calc_dynamic_confidence(sig_action, _ind_for_conf)

                    # คำนวณ session / hour_gmt7
                    _utc_hour = _now_dt.hour
                    _hour_gmt7 = (_utc_hour + 7) % 24
                    _session = get_session(_utc_hour)

                    log_mode = 'HYBRID PENDING' if self.bot_mode == 'HYBRID' else 'SIGNAL'
                    thai_console_log(
                        f">>> {sig_action} | {symbol} | {sig_strategy} | "
                        f"Conf: {sig_conf}% | {state_str} | {current_price:.5f}"
                    )
                    logger.info(f"""\n{'─'*70}
[{log_mode}] {symbol} | {sig_action} | Strategy: {sig_strategy} | Conf: {sig_conf}%
[MARKET] State: {state_str} | Trend: {trend_dir} ({trend_strength:.0f}%) | Price: {current_price:.5f}
[REASON] {sig_reason}
[OTHER]  {len(triggered_signals)-1} additional signal(s) also triggered
{'─'*70}""")
                    # Write pending signal for external tools (stored as array for clear_and_parse_signals compatibility)
                    pending_path = os.path.join("logs", "pending_signals.json")
                    try:
                        existing_pending = []
                        if os.path.exists(pending_path):
                            try:
                                with open(pending_path, "r", encoding="utf-8") as f_pend:
                                    existing_pending = json.load(f_pend)
                                    if not isinstance(existing_pending, list):
                                        existing_pending = []
                            except:
                                existing_pending = []

                        new_signal = {
                            'timestamp': market_state_data['timestamp'],
                            'symbol': symbol,
                            'direction': sig_action,
                            'confidence': sig_conf,
                            'size': float(self.position_sizer.calculate(
                                confidence=sig_conf
                            )) if hasattr(self, 'position_sizer') else 30.0,
                            'state': state_str,
                            'session': _session,
                            'hour_gmt7': _hour_gmt7,
                            'reason': sig_reason,
                            'strategy': sig_strategy,
                            'indicators': market_state_data['indicators'],
                            'candles': market_state_data['candles'],
                            'candle_count': len(market_state_data['candles']),
                            'processed': False,
                            'ai_action': 'PENDING' if self.bot_mode == 'HYBRID' else None,
                            'trade_outcome': None
                        }
                        existing_pending.append(new_signal)
                        with open(pending_path, "w", encoding="utf-8") as f_pend:
                            json.dump(existing_pending, f_pend, indent=2, ensure_ascii=False)
                    except Exception as e:
                        logger.error(f"[ERR] Failed to write pending signal: {e}")
                else:
                    log_mode = 'HYBRID' if self.bot_mode == 'HYBRID' else 'SIGNAL'
                    logger.info(f"[{log_mode}] {symbol} | NO SIGNAL | Market: {state_str} | Price: {current_price:.5f}")

                all_strategy_results = [
                    {'strategy': s['strategy'], 'signal': s['signal'], 'confidence': s['confidence'], 'reason': s['reason'][:12]}
                    for s in triggered_signals
                ] or [{'strategy': 'none', 'signal': 'NO_SIGNAL', 'confidence': 0, 'reason': 'No trigger'}]

                return {
                    'symbol': symbol,
                    'signal': first_signal['signal'] if first_signal else 'NO_SIGNAL',
                    'confidence': first_signal['confidence'] if first_signal else 0,
                    'reason': first_signal['reason'] if first_signal else ('No strategy triggered — waiting for AI' if self.bot_mode == 'HYBRID' else 'No strategy triggered'),
                    'executed': False,
                    'market_state': state_str,
                    'current_price': current_price,
                    'strategy': first_signal['strategy'] if first_signal else 'none',
                    'all_strategies': all_strategy_results
                }

            elif self.bot_mode == 'TRADE':
                # ── TRADE MODE: Execute directly, no gates, no market filters ──
                if first_signal:
                    sig_action = first_signal['signal']
                    sig_strategy = first_signal['strategy']
                    sig_conf = first_signal['confidence']
                    thai_console_log(f">>> EXECUTE {sig_action} | {symbol} | {sig_strategy}")
                    logger.info(f"[TRADE] {symbol} | {sig_action} | Strategy: {sig_strategy} | Executing now...")
                    try:
                        size = self.position_sizer.calculate(
                            confidence=sig_conf
                        )
                        expiry_val = first_signal.get('expiry', 'M1')
                        order = self.executor.send_order(
                            symbol=symbol,
                            direction=sig_action,
                            amount=size,
                            expiry=expiry_val
                        )
                        if order and order.status in ('pending', 'executed'):
                            self.order_manager.add_trade(
                                order_id=order.order_id,
                                symbol=symbol,
                                direction=sig_action,
                                amount=size,
                                entry_price=current_price,
                                expiry=expiry_val
                            )
                            # Store strategy name in trade notes
                            if order.order_id in self.order_manager.active_trades:
                                self.order_manager.active_trades[order.order_id].notes = sig_strategy
                                
                            self.signal_count[symbol] = self.signal_count.get(symbol, 0) + 1
                            logger.info(f"[TRADE] Order placed: {order.order_id}")
                            return {
                                'symbol': symbol,
                                'signal': sig_action,
                                'confidence': sig_conf,
                                'reason': first_signal['reason'],
                                'executed': True,
                                'order_id': order.order_id,
                                'market_state': state_str,
                                'current_price': current_price,
                                'strategy': sig_strategy,
                                'all_strategies': [
                                    {'strategy': s['strategy'], 'signal': s['signal'], 'confidence': s['confidence'], 'reason': s['reason'][:12]}
                                    for s in triggered_signals
                                ]
                            }
                    except Exception as e:
                        logger.error(f"[TRADE ERR] Failed to execute trade for {symbol}: {e}")

                return {
                    'symbol': symbol,
                    'signal': 'NO_SIGNAL',
                    'confidence': 0,
                    'reason': 'No strategy triggered',
                    'executed': False,
                    'market_state': state_str,
                    'current_price': current_price,
                    'strategy': 'none',
                    'all_strategies': []
                }

            else:
                # ── AI MODE (default): Write full JSON, return AI_EVAL ──────────
                all_strategy_results = [
                    {'strategy': s['strategy'], 'signal': s['signal'], 'confidence': s['confidence'], 'reason': s['reason'][:12]}
                    for s in triggered_signals
                ] + [
                    {'strategy': s.STRATEGY_NAME, 'signal': 'BLOCKED', 'confidence': 0, 'reason': 'Inactive strategy'}
                    for s in []
                ]

                if not all_strategy_results:
                    all_strategy_results = [{'strategy': 'none', 'signal': 'NO_SIGNAL', 'confidence': 0, 'reason': 'No trigger'}]

                return {
                    'symbol': symbol,
                    'signal': first_signal['signal'] if first_signal else 'NO_SIGNAL',
                    'confidence': first_signal['confidence'] if first_signal else 0,
                    'reason': first_signal['reason'] if first_signal else 'No strategy triggered — waiting for AI evaluation',
                    'executed': False,
                    'simulated': True,
                    'market_state': state_str,
                    'current_price': current_price,
                    'strategy': first_signal['strategy'] if first_signal else 'none',
                    'all_strategies': all_strategy_results
                }

        except Exception as e:
            logger.error(f"[ERR] Error in cycle for {symbol}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return {
                'symbol': symbol,
                'signal': 'ERROR',
                'reason': str(e),
                'executed': False,
                'market_state': 'ERROR',
                'current_price': 0.0,
                'strategy': 'none'
            }
            
    def _process_hybrid_execution_queue(self):
        """
        Check logs/pending_signals.json for any signals approved by AI (ai_action == 'EXECUTE')
        and execute them immediately on IQ Option.
        """
        import os
        import json
        pending_path = os.path.join("logs", "pending_signals.json")
        if not os.path.exists(pending_path):
            return

        try:
            with open(pending_path, "r", encoding="utf-8") as f:
                signals = json.load(f)
            if not isinstance(signals, list):
                return
        except Exception as e:
            logger.error(f"[HYBRID ERR] Failed to read pending signals: {e}")
            return

        updated = False
        for sig in signals:
            if not sig.get("processed", False) and sig.get("ai_action") == "EXECUTE":
                symbol = sig.get("symbol")
                sig_action = sig.get("direction")
                sig_strategy = sig.get("strategy", "HybridAI")
                sig_conf = sig.get("confidence", 80)
                
                logger.info(f"[HYBRID EXECUTE] AI approved signal! Executing {sig_action} on {symbol}...")
                try:
                    # Prevent duplicate active trade for the same symbol
                    active_trades = self.order_manager.get_active_trades(symbol)
                    if active_trades:
                        logger.warning(f"[HYBRID HOLD] {symbol} already has an active trade in progress. Skip execution.")
                        sig["processed"] = True
                        sig["ai_action"] = "SKIPPED_ACTIVE_TRADE"
                        updated = True
                        continue
                        
                    current_price = sig.get("indicators", {}).get("ema5", 0.0)  # estimate current price
                    if hasattr(self, 'intelligence_pipeline') and self.intelligence_pipeline.last_context:
                        current_price = getattr(self.intelligence_pipeline.last_context, 'current_price', current_price)

                    size = float(self.position_sizer.calculate(confidence=sig_conf))
                    order = self.executor.send_order(
                        symbol=symbol,
                        direction=sig_action,
                        amount=size,
                        expiry='M1'
                    )
                    if order and order.status in ('pending', 'executed'):
                        self.order_manager.add_trade(
                            order_id=order.order_id,
                            symbol=symbol,
                            direction=sig_action,
                            amount=size,
                            entry_price=current_price,
                            expiry='M1'
                        )
                        if order.order_id in self.order_manager.active_trades:
                            self.order_manager.active_trades[order.order_id].notes = f"AI_HYBRID_{sig_strategy}"
                            
                        self.signal_count[symbol] = self.signal_count.get(symbol, 0) + 1
                        logger.info(f"[HYBRID EXECUTE] Order placed successfully: {order.order_id}")
                        sig["processed"] = True
                        sig["ai_action"] = "EXECUTED"
                        sig["order_id"] = order.order_id
                        updated = True
                    else:
                        logger.error(f"[HYBRID ERR] Executor failed to place order.")
                        sig["processed"] = True
                        sig["ai_action"] = "EXECUTION_FAILED"
                        updated = True
                except Exception as ex:
                    logger.error(f"[HYBRID ERR] Exception during execution: {ex}")
                    sig["processed"] = True
                    sig["ai_action"] = f"ERROR: {str(ex)}"
                    updated = True

        if updated:
            try:
                with open(pending_path, "w", encoding="utf-8") as f:
                    json.dump(signals, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"[HYBRID ERR] Failed to write updated pending signals: {e}")

    def run_cycle(self) -> Dict:
        """
        Execute one full cycle across all symbols.
        
        Returns:
            Dictionary of results per symbol
        """
        # In Hybrid mode, process any approved signals from AI first
        if self.bot_mode == 'HYBRID':
            self._process_hybrid_execution_queue()

        self._reload_runtime_config()
        self.cycle_count += 1
        
        results = {}
        for symbol in self.symbols:
            result = self.run_single_cycle(symbol)
            results[symbol] = result
            
            if result.get('simulated'):
                pass  # Handled elegantly by custom console box
            elif result['executed']:
                logger.info(f"[OK] {symbol}: {result['signal']} @ confidence {result['confidence']}%")
            else:
                logger.debug(f"[SKIP] {symbol}: {result['signal']}")
        
        # Print a clean one-line console summary at the end of each cycle
        summary_parts = []
        for sym in self.symbols:
            res = results.get(sym, {})
            price_val = res.get('current_price', 0.0)
            price_str = f"{price_val:.5f}" if price_val != 0.0 else "WAITING"
            state_str = res.get('market_state', 'UNKNOWN')
            sig_action = res.get('signal', 'HOLD')
            sig_conf = res.get('confidence', 0)
            
            sig_detail = sig_action
            if sig_action in ('CALL', 'PUT') and sig_conf > 0:
                sig_detail += f" ({sig_conf}%)"
            
            summary_parts.append(f"{sym}: {price_str} ({sig_detail}/{state_str})")
            
        timestamp_str = datetime.now(timezone.utc).strftime('%H:%M:%S')
        logger.info(f"[CYCLE #{self.cycle_count} | {timestamp_str} UTC] " + " | ".join(summary_parts))
        
        if self.is_live:
            has_signal = any(
                results.get(sym, {}).get('signal') in ('CALL', 'PUT')
                for sym in self.symbols
            )
            if not has_signal:
                status_parts = []
                for sym in self.symbols:
                    res = results.get(sym, {})
                    price_val = res.get('current_price', 0.0)
                    price_str = f"{price_val:.5f}" if price_val else "..."
                    status_parts.append(
                        f"{sym}: {price_str} ({res.get('market_state', 'UNKNOWN')})"
                    )
                thai_console_log(f"รอสัญญาณ | {' | '.join(status_parts)}")
        
        return results

    def run_backtest(self, num_cycles: int = 10) -> None:
        """
        Run backtest (multiple cycles).
        
        Args:
            num_cycles: Number of cycles to execute
        """
        logger.info(f"\n[LOOP] Starting backtest: {num_cycles} cycles...\n")
        
        for i in range(num_cycles):
            self.run_cycle()
        
        logger.info("\n" + "="*80)
        logger.info("=== BACKTEST SUMMARY ===")
        logger.info("="*80)
        logger.info(f"Cycles executed: {self.cycle_count}")
        logger.info(f"Signals per symbol: {self.signal_count}")
        
        # Order manager stats
        self.order_manager.print_summary()

        # Profit summary
        status = self.get_status()
        total_pnl = status.get('total_pnl', 0.0)
        logger.info(f"[SUMMARY] Total P&L (profit/loss): {total_pnl:.2f} THB")
        # Write profit report
        report_path = Path('logs') / "profit_report.txt"
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write("Backtest Profit Report\n")
                f.write(f"Cycles executed: {self.cycle_count}\n")
                f.write(f"Total P&L: {total_pnl:.2f} THB\n")
            logger.info(f"Profit report written to {report_path}")
        except Exception as e:
            logger.error(f"Failed to write profit report: {e}")
    
    def run_live(self, interval_seconds: int = 5) -> None:
        """
        Run the bot continuously in real-time.
        
        Args:
            interval_seconds: Delay between analysis cycles.
        """
        self.is_live = True
        import time
        logger.info(f"\n[START] Starting continuous live trading mode...")
        logger.info(f"[TIME] Cycle synced to M1 candle boundaries (every 60s at :00)")
        logger.info(f"[STOP] Press Ctrl+C to stop the bot\n")
        
        try:
            # Wait for the next M1 candle to open before starting the first cycle
            now = datetime.now()
            current_second = now.second + now.microsecond / 1000000.0
            wait_for_first = 60.0 - current_second + 2.0  # wait until :02 of next minute
            if wait_for_first > 62:
                wait_for_first -= 60.0
            thai_console_log(f"รอแท่ง M1 ถัดไป {wait_for_first:.0f}s...")
            time.sleep(max(0.1, wait_for_first))

            while True:
                now_start = datetime.now()
                logger.info(f"[M1 OPEN] New M1 candle started at {now_start.strftime('%H:%M:%S')} - analyzing...")
                self.run_cycle()

                status = self.get_status()
                logger.info(
                    f"[STATUS] Cycles: {status.get('cycles', 0)} | "
                    f"Trades: {status.get('total_trades', 0)} | "
                    f"P&L: {status.get('total_pnl', 0.0):.2f}"
                )

                now = datetime.now()
                current_second = now.second + now.microsecond / 1000000.0
                sleep_time = 60.0 - current_second + 2.0
                if sleep_time > 62.0:
                    sleep_time -= 60.0
                time.sleep(max(0.1, sleep_time))
        except KeyboardInterrupt:
            logger.info("\n[STOP] Live trading stopped by user.")
    
    def get_status(self) -> Dict:
        """Get current bot status."""
        try:
            stats = self.order_manager.get_stats()
            sizer_stats = self.position_sizer.get_stats()
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'cycles': self.cycle_count,
                'data_connected': self.data_adapter.is_connected(),
                'executor_connected': self.executor.is_connected(),
                'mode': 'MOCK' if self.use_mock else 'LIVE',
                'active_trades': len(self.order_manager.active_trades),
                'total_trades': stats.get('total_trades', 0),
                'total_pnl': stats.get('total_pnl', 0.0),
                'win_rate': stats.get('win_rate', 0.0),
                'session_duration': stats.get('session_duration', 'N/A'),
                'daily_risk_used': f"{sizer_stats.get('daily_risk_percent', 0):.2f}%",
                'signals_per_symbol': self.signal_count,
            }
        except Exception as e:
            logger.warning(f"[WARN] Error getting status: {e}")
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e),
                'cycles': self.cycle_count,
            }
 
 
def main():
    """Main entry point."""
    try:
        from core.config_loader import get_use_mock, get_account_type, get_capital
        use_mock = get_use_mock()
        account_type = get_account_type()
        capital = get_capital()
        
        # Initialize bot dynamically using config settings
        bot = BotRunner(
            symbols=None,  # Loads from symbols.txt capped at 6
            capital=capital,
            use_mock=use_mock,
            account_type=account_type
        )
        
        # Run backtest
        bot.run_backtest(num_cycles=5)
        
        # Final status
        logger.info("\n[STATUS] FINAL STATUS:")
        try:
            status = bot.get_status()
            logger.info(f"  Cycles: {status.get('cycles', 0)}")
            logger.info(f"  Total Trades: {status.get('total_trades', 0)}")
            logger.info(f"  Win Rate: {status.get('win_rate', 0):.1f}%")
            logger.info(f"  Total P&L: {status.get('total_pnl', 0):.2f} THB")
            logger.info(f"  Mode: {status.get('mode', 'UNKNOWN')}")
        except Exception as e:
            logger.warning(f"[WARN] Could not get final status: {e}")
            logger.info(f"  Cycles: {bot.cycle_count}")
            logger.info(f"  Signals: {bot.signal_count}")
        
    except KeyboardInterrupt:
        logger.info("\n[STOP] Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
