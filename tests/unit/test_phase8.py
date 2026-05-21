"""
PHASE 8 Tests: Advanced Features
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test V2, V3 strategies, ML optimizer, portfolio balancer, dashboard.
"""

import logging
from datetime import datetime
from core.models import Candle, MarketContext
from strategy.reversal_strategy.reversal_strategy import ReversalStrategy
from strategy.trend_following.trend_strategy import TrendFollowingStrategy
from core.ml.signal_optimizer import SignalOptimizer, SignalRecord
from execution.portfolio_balancer import PortfolioBalancer
from monitoring.advanced_dashboard import AdvancedDashboard

logger = logging.getLogger(__name__)


def test_reversal_strategy():
    """Test V2 Reversal Strategy."""
    logger.info("Testing Reversal Strategy V2...")
    
    strategy = ReversalStrategy()
    assert strategy.name == "Reversal Pattern V2"
    assert strategy.version == "2.0"
    
    # Create test context
    context = MarketContext()
    context.candles = [
        Candle(
            timestamp=datetime.now(),
            open=100 + i,
            high=102 + i,
            low=98 + i,
            close=101 + i,
            volume=1000,
        )
        for i in range(20)
    ]
    
    signal = strategy.analyze(context)
    assert signal is not None
    assert signal.direction in ["CALL", "PUT", "NO_SIGNAL"]
    
    logger.info(f"✅ Reversal Strategy test passed")


def test_trend_following_strategy():
    """Test V3 Trend Following Strategy."""
    logger.info("Testing Trend Following Strategy V3...")
    
    strategy = TrendFollowingStrategy()
    assert strategy.name == "Trend Following V3"
    assert strategy.version == "3.0"
    
    # Create uptrend context
    context = MarketContext()
    context.candles = [
        Candle(
            timestamp=datetime.now(),
            open=100 + i * 0.5,
            high=102 + i * 0.5,
            low=99 + i * 0.5,
            close=101 + i * 0.5,
            volume=1000,
        )
        for i in range(50)
    ]
    context.market_state = "TRENDING_UP"
    context.noise_level = 20
    
    signal = strategy.analyze(context)
    assert signal is not None
    
    logger.info(f"✅ Trend Following Strategy test passed")


def test_signal_optimizer():
    """Test ML Signal Optimizer."""
    logger.info("Testing Signal Optimizer...")
    
    optimizer = SignalOptimizer()
    
    # Add sample signals
    for i in range(100):
        record = SignalRecord(
            timestamp=datetime.now(),
            symbol="EURUSD",
            direction="CALL" if i % 2 == 0 else "PUT",
            entry_confidence=50 + i % 50,
            actual_result="WIN" if i % 3 == 0 else "LOSS",
            pnl=100 if i % 3 == 0 else -50,
        )
        optimizer.record_signal(record)
    
    # Train model
    model = optimizer.train_model()
    assert optimizer.trained
    assert 'overall_win_rate' in model
    assert 'total_signals' in model
    
    # Test confidence optimization
    optimized = optimizer.optimize_confidence("CALL", 60)
    assert 0 <= optimized <= 100
    
    logger.info(f"✅ Signal Optimizer test passed")


def test_portfolio_balancer():
    """Test Portfolio Balancer."""
    logger.info("Testing Portfolio Balancer...")
    
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    balancer = PortfolioBalancer(symbols, total_capital=2000)
    
    # Check equal weights initially
    weights = balancer.symbol_weights
    assert len(weights) == 3
    assert abs(sum(weights.values()) - 1.0) < 0.01
    
    # Test capital allocation
    for symbol in symbols:
        capital = balancer.get_capital_allocation(symbol)
        assert 0 < capital <= 2000
    
    # Test risk distribution
    dist = balancer.get_risk_distribution()
    assert abs(sum(dist.values()) - 100) < 1
    
    logger.info(f"✅ Portfolio Balancer test passed")


def test_advanced_dashboard():
    """Test Advanced Dashboard."""
    logger.info("Testing Advanced Dashboard...")
    
    dashboard = AdvancedDashboard()
    
    # Register strategies
    dashboard.register_strategy("Reversal", "2.0")
    dashboard.register_strategy("TrendFollowing", "3.0")
    
    # Record some trades
    dashboard.record_trade("Reversal_v2.0", "EURUSD", "WIN", 150)
    dashboard.record_trade("Reversal_v2.0", "EURUSD", "LOSS", -50)
    dashboard.record_trade("TrendFollowing_v3.0", "GBPUSD", "WIN", 200)
    
    # Test comparison
    comparison = dashboard.get_strategy_comparison()
    assert len(comparison) == 2
    
    # Test symbol performance
    perf = dashboard.get_symbol_performance()
    assert "EURUSD" in perf or "GBPUSD" in perf
    
    # Test report
    report = dashboard.generate_report()
    assert "STRATEGY COMPARISON" in report
    assert "SYMBOL PERFORMANCE" in report
    
    logger.info(f"✅ Advanced Dashboard test passed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_reversal_strategy()
    test_trend_following_strategy()
    test_signal_optimizer()
    test_portfolio_balancer()
    test_advanced_dashboard()
    
    logger.info(f"\n✅ ALL PHASE 8 TESTS PASSED\n")
