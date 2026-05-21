"""
Import Validation Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verify all critical imports work correctly.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_core_models_import():
    """Test core models import."""
    try:
        from core.models import Candle, Signal, MarketContext, Score, EngineOutput
        logger.info("✅ Core models import successful")
        assert Candle is not None
        assert Signal is not None
        assert MarketContext is not None
    except Exception as e:
        logger.error(f"❌ Core models import failed: {e}")
        raise


def test_engines_import():
    """Test engine imports."""
    try:
        from core.engines.trend_engine import TrendEngine
        from core.engines.strength_engine import StrengthEngine
        from core.engines.volatility_engine import VolatilityEngine
        logger.info("✅ Engines import successful")
    except Exception as e:
        logger.error(f"❌ Engines import failed: {e}")
        raise


def test_strategies_import():
    """Test strategy imports."""
    try:
        from strategy.compression_breakout.strategy import CompressionBreakoutStrategy
        from strategy.reversal_strategy.reversal_strategy import ReversalStrategy
        from strategy.trend_following.trend_strategy import TrendFollowingStrategy
        logger.info("✅ Strategies import successful")
    except Exception as e:
        logger.error(f"❌ Strategies import failed: {e}")
        raise


def test_execution_import():
    """Test execution layer imports."""
    try:
        from execution.position_sizer import PositionSizer
        from execution.order_manager import OrderManager
        from execution.iq_option_executor import IQOptionExecutor
        logger.info("✅ Execution layer import successful")
    except Exception as e:
        logger.error(f"❌ Execution import failed: {e}")
        raise


def test_ml_import():
    """Test ML framework imports."""
    try:
        from core.ml import SignalOptimizer, SignalRecord
        from execution.portfolio_balancer import PortfolioBalancer
        logger.info("✅ ML framework import successful")
    except Exception as e:
        logger.error(f"❌ ML import failed: {e}")
        raise


def test_monitoring_import():
    """Test monitoring imports."""
    try:
        from monitoring.advanced_dashboard import AdvancedDashboard, StrategyStats
        from monitoring.logger import BotLogger
        logger.info("✅ Monitoring import successful")
    except Exception as e:
        logger.error(f"❌ Monitoring import failed: {e}")
        raise


if __name__ == "__main__":
    logger.info("Running import validation tests...\n")
    
    try:
        test_core_models_import()
        test_engines_import()
        test_strategies_import()
        test_execution_import()
        test_ml_import()
        test_monitoring_import()
        
        logger.info("\n" + "="*60)
        logger.info("✅✅✅ ALL IMPORT TESTS PASSED")
        logger.info("="*60)
    except Exception as e:
        logger.error(f"\n❌ Import validation failed: {e}")
        sys.exit(1)
