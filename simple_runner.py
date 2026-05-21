"""
Simple FINALBOT Runner - Debug Mode
รันได้โดยไม่ต้องเรียก complex engines
"""

import sys
import logging
from datetime import datetime
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
)
logger = logging.getLogger("FINALBOT_DEBUG")

# Import core modules
from core.data.iq_option_adapter import IQOptionAdapter
from execution.order_manager import OrderManager
from execution.position_sizer import PositionSizer
from execution.iq_option_executor import IQOptionExecutor

class SimpleBot:
    """Simple bot for testing"""
    
    def __init__(self, symbols: List[str] = None, capital: float = 2000.0, use_mock: bool = True):
        self.symbols = symbols or ['EURUSD-OTC']
        self.capital = capital
        self.use_mock = use_mock
        
        logger.info("🚀 FINALBOT Simple Runner initializing...")
        logger.info(f"   Symbols: {', '.join(self.symbols)}")
        logger.info(f"   Capital: {capital} THB")
        logger.info(f"   Mode: {'MOCK' if use_mock else 'LIVE'}")
        
        # Initialize components
        self.data_adapter = IQOptionAdapter(use_mock=use_mock)
        self.executor = IQOptionExecutor(use_mock=use_mock)
        self.position_sizer = PositionSizer(capital=capital)
        self.order_manager = OrderManager()
        
        self.cycle_count = 0
        
        logger.info("✅ Bot initialized successfully\n")
    
    def run_cycles(self, num_cycles: int = 5):
        """Run multiple cycles"""
        logger.info(f"\n🔄 Running {num_cycles} cycles in MOCK mode...\n")
        
        for cycle in range(num_cycles):
            self.cycle_count += 1
            logger.info(f"⏱️  CYCLE #{self.cycle_count}")
            
            for symbol in self.symbols:
                try:
                    # Fetch data
                    candles_dict = self.data_adapter.get_multi_timeframe(symbol, count=200)
                    logger.info(f"✅ {symbol}: Data loaded ({len(candles_dict)} timeframes)")
                except Exception as e:
                    logger.error(f"❌ {symbol}: {e}")
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("📊 BACKTEST SUMMARY")
        logger.info("="*80)
        logger.info(f"Cycles executed: {self.cycle_count}")
        logger.info(f"Total symbols: {len(self.symbols)}")
        
        # Print order manager summary
        self.order_manager.print_summary()
        
        logger.info("\n📍 FINAL STATUS:")
        logger.info(f"  Mode: {'MOCK' if self.use_mock else 'LIVE'}")
        logger.info(f"  Cycles: {self.cycle_count}")
        logger.info(f"  Status: ✅ OK")


def main():
    """Main entry point"""
    try:
        bot = SimpleBot(
            symbols=['EURUSD-OTC', 'GBPUSD-OTC', 'USDJPY-OTC'],
            capital=2000.0,
            use_mock=True
        )
        
        bot.run_cycles(num_cycles=5)
        logger.info("\n✅ Bot completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
