"""
FINALBOT — Main Entry Point
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Quick start bot for EURUSD-OTC trading

Usage:
    python main.py
    
Or use runner.py for more control
"""

import sys
from runner import BotRunner

if __name__ == "__main__":
    try:
        print("🚀 FINALBOT Starting...\n")
        
        # Create bot with default config
        bot = BotRunner(
            symbols=['EURUSD-OTC'],
            capital=2000.0,
            use_mock=False  # LIVE MODE
        )
        
        # Run backtest (5 cycles to test, then continuous)
        print("Running 5 test cycles first...\n")
        bot.run_backtest(num_cycles=5)
        
        # Show final status
        status = bot.get_status()
        print("\n✅ Bot ready for live trading")
        print(f"Status: {status}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
