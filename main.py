"""
FINALBOT — Main Entry Point

Quick start: python main.py
"""

import sys
import logging
from monitoring.console_dashboard import ConsoleUI, logger, setup_logging
from runner import PureAIRunner

setup_logging()

def main():
    """Main entry point for FINALBOT"""
    ConsoleUI.show_startup()
    
    bot = PureAIRunner()
    ConsoleUI.show_live_mode_start()
    bot.start()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹ Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)