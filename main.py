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
    logger = logging.getLogger("FINALBOT")
    ConsoleUI.show_startup()
    
    bot = PureAIRunner()
    ConsoleUI.show_live_mode_start()
    bot.start()

def load_symbols():
    """Load symbols from settings.json - Single Source of Truth"""
    from config_setting.config_loader import get_symbols
    try:
        symbols = get_symbols()
        if not symbols:
            raise Exception("No symbols found in settings.json")
        return symbols
    except Exception as e:
        logger.error(f"Failed to load symbols from settings.json: {e}")
        raise Exception(f"Configuration error: symbols not loaded from settings.json — bot stopped")

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