"""Verify all 11 strategies (7 original + 4 new) load and run without errors."""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from runner import BotRunner

def verify():
    print("=" * 60)
    print("Initializing BotRunner (MOCK mode)...")
    print("=" * 60)
    bot = BotRunner(
        symbols=['EURUSD-OTC'],
        capital=2000.0,
        use_mock=True,
        account_type="PRACTICE"
    )

    # List all active strategies
    print(f"\nActive strategies ({len(bot.active_strategies)}):")
    for i, s in enumerate(bot.active_strategies, 1):
        print(f"  {i:2d}. {s.STRATEGY_NAME}")

    # Run 2 test cycles
    print("\nRunning 2 test cycles...")
    bot.run_backtest(num_cycles=2)

    print(f"\nAll {len(bot.active_strategies)} strategies loaded and executed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    verify()
