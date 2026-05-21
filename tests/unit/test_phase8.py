"""PHASE 8 Tests"""
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
    logger.info("Testing Reversal Strategy V2...")
    strategy = ReversalStrategy()
    assert strategy.name == "Reversal Pattern V2"
    context = MarketContext(timestamp=datetime.now(), pair="EURUSD", timeframe="M5", current_price=1.0850)
    context.candles = [Candle(timestamp=datetime.now(), open=100+i, high=102+i, low=98+i, close=101+i, volume=1000) for i in range(20)]
    result = strategy.evaluate(context)
    assert result is not None
    assert result['action'] in ["CALL", "PUT", "NO_SIGNAL"]
    logger.info(f"✅ Reversal Strategy test passed")

def test_trend_following_strategy():
    logger.info("Testing Trend Following Strategy V3...")
    strategy = TrendFollowingStrategy()
    assert strategy.name == "Trend Following V3"
    context = MarketContext(timestamp=datetime.now(), pair="EURUSD", timeframe="M5", current_price=1.0900)
    context.candles = [Candle(timestamp=datetime.now(), open=100+i*0.5, high=102+i*0.5, low=99+i*0.5, close=101+i*0.5, volume=1000) for i in range(50)]
    result = strategy.evaluate(context)
    assert result is not None
    assert result['action'] in ["CALL", "PUT", "NO_SIGNAL"]
    logger.info(f"✅ Trend Following Strategy test passed")

def test_signal_optimizer():
    logger.info("Testing Signal Optimizer...")
    optimizer = SignalOptimizer()
    for i in range(100):
        record = SignalRecord(timestamp=datetime.now(), symbol="EURUSD", direction="CALL" if i%2==0 else "PUT", entry_confidence=50+i%50, actual_result="WIN" if i%3==0 else "LOSS", pnl=100 if i%3==0 else -50)
        optimizer.record_signal(record)
    model = optimizer.train_model()
    assert optimizer.trained
    assert 'overall_win_rate' in model
    optimized = optimizer.optimize_confidence("CALL", 60)
    assert 0 <= optimized <= 100
    logger.info(f"✅ Signal Optimizer test passed")

def test_portfolio_balancer():
    logger.info("Testing Portfolio Balancer...")
    balancer = PortfolioBalancer(["EURUSD", "GBPUSD", "USDJPY"], total_capital=2000)
    weights = balancer.symbol_weights
    assert len(weights) == 3
    assert abs(sum(weights.values()) - 1.0) < 0.01
    for symbol in balancer.symbols:
        capital = balancer.get_capital_allocation(symbol)
        assert 0 < capital <= 2000
    dist = balancer.get_risk_distribution()
    assert abs(sum(dist.values()) - 100) < 1
    logger.info(f"✅ Portfolio Balancer test passed")

def test_advanced_dashboard():
    logger.info("Testing Advanced Dashboard...")
    dashboard = AdvancedDashboard()
    dashboard.register_strategy("Reversal", "2.0")
    dashboard.register_strategy("TrendFollowing", "3.0")
    dashboard.record_trade("Reversal_v2.0", "EURUSD", "WIN", 150)
    dashboard.record_trade("Reversal_v2.0", "EURUSD", "LOSS", -50)
    dashboard.record_trade("TrendFollowing_v3.0", "GBPUSD", "WIN", 200)
    comparison = dashboard.get_strategy_comparison()
    assert len(comparison) == 2
    perf = dashboard.get_symbol_performance()
    assert "EURUSD" in perf or "GBPUSD" in perf
    report = dashboard.generate_report()
    assert "STRATEGY COMPARISON" in report
    logger.info(f"✅ Advanced Dashboard test passed")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_reversal_strategy()
    test_trend_following_strategy()
    test_signal_optimizer()
    test_portfolio_balancer()
    test_advanced_dashboard()
    logger.info(f"\n✅ ALL PHASE 8 TESTS PASSED\n")
