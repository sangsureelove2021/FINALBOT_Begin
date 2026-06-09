"""
FINALBOT — Main Entry Point
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Quick start: python main.py

Currency pairs are loaded from symbols.txt next to this file (one per line).
"""

import sys
import os
from pathlib import Path

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



PROJECT_ROOT = Path(__file__).resolve().parent
SYMBOLS_FILE = PROJECT_ROOT / "symbols.txt"

# Make setup_engines importable as `from main import setup_engines`
from core.engines.engine_setup import setup_engines  # noqa: F401


def setup_pipeline(registry=None):
    """Build a ready-to-run Pipeline from settings.json active_strategies."""
    from core.config_loader import load_settings, get_execution_gate
    from core.orchestration.context_builder import ContextBuilder
    from core.orchestration.pipeline import Pipeline
    from core.orchestration.execution_gate import ExecutionGate
    from strategy.compression_breakout.strategy import CompressionBreakoutStrategy
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

    settings = load_settings()
    active = settings.get("active_strategies", ["rejection_5m_pa"])
    strategies = [strategy_mapping[n]() for n in active if n in strategy_mapping]

    eg_config = get_execution_gate()
    registry = registry or setup_engines()
    return Pipeline(
        context_builder=ContextBuilder(registry),
        strategies=strategies,
        execution_gate=ExecutionGate(
            min_confidence=eg_config.get("min_confidence", 72),
            max_block_score=eg_config.get("max_block_score", 45),
        ),
    )


def load_symbols(path: str = None) -> list:
    """Load trading pairs from settings.json (single source of truth), with fallback to symbols.txt."""
    try:
        from core.config_loader import get_symbols
        symbols = get_symbols()
        if symbols:
            return symbols
    except Exception:
        pass

    p = Path(path) if path else SYMBOLS_FILE
    if not p.is_file():
        raise FileNotFoundError(
            f"symbols.txt not found at {p} — create it next to main.py"
        )
    seen, symbols = set(), []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s and not s.startswith("#") and s not in seen:
                seen.add(s)
                symbols.append(s)
    if not symbols:
        raise RuntimeError(f"{p} is empty — add at least one pair")
    return symbols



def main():
    import logging
    from core.config_loader import get_use_mock, get_account_type, get_capital
    from runner import BotRunner, thai_console_log

    logger = logging.getLogger("FINALBOT")
    thai_console_log("FINALBOT Starting...")
    symbols = load_symbols()
    thai_console_log(f"คู่เงิน ({len(symbols)}): {', '.join(symbols)}")

    bot = BotRunner(
        symbols=symbols,
        capital=get_capital(),
        use_mock=get_use_mock(),
        account_type=get_account_type(),
    )

    thai_console_log("ทดสอบ 1 รอบก่อนเริ่ม Live...")
    bot.run_backtest(num_cycles=1)

    thai_console_log("เริ่ม Live Mode — วิเคราะห์ทุกแท่ง M1 (Ctrl+C หยุด)")
    bot.run_live(interval_seconds=60)



if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
