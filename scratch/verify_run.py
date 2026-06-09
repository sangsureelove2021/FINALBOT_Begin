import sys
import os
from pathlib import Path

# Add root folder to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from runner import BotRunner

def verify():
    print("Initializing BotRunner in MOCK mode...")
    bot = BotRunner(
        symbols=['EURUSD-OTC', 'GBPUSD-OTC'],
        capital=2000.0,
        use_mock=True,
        account_type="PRACTICE"
    )
    print("Bot initialized successfully!")
    print("Running 2 test cycles...")
    bot.run_backtest(num_cycles=2)
    print("Verifying order manager status...")
    stats = bot.order_manager.get_stats()
    print(f"Stats: {stats}")
    print("Verification completed successfully!")

if __name__ == "__main__":
    verify()
