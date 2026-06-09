"""
Test Fixture: Sample MarketContext
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pre-populated MarketContext objects for testing scoring, strategy,
and execution-gate logic without running the full engine pipeline.
"""

from datetime import datetime, timezone
from core.models.market_context import MarketContext


def make_bullish_context(symbol: str = "EURUSD-OTC") -> MarketContext:
    """A clean, tradeable bullish breakout context."""
    ctx = MarketContext(symbol=symbol, timestamp=datetime.now(timezone.utc),
                        timeframe="M5", current_price=1.0900)
    ctx.trend = {"direction": "UP", "strength": 80, "confidence": 85,
                 "type": "IMPULSIVE", "reversal_risk": 20}
    ctx.strength = {"adx": 35, "rsi": 60, "momentum_level": "STRONG",
                    "exhaustion_risk": 20}
    ctx.volatility = {"regime": "NORMAL", "atr_percentile": 25,
                      "expansion_probability": 70}
    ctx.mtf = {"alignment_score": 80, "htf_ltf_conflict": False,
               "htf_direction": "UP"}
    ctx.market_state = "BREAKING_OUT"
    ctx.traps = {"trap_detected": False}
    ctx.noise = {"noise_level": 20}
    ctx.anomaly = {"anomaly_detected": False}
    return ctx


def make_bearish_context(symbol: str = "EURUSD-OTC") -> MarketContext:
    """A clean, tradeable bearish breakout context."""
    ctx = make_bullish_context(symbol)
    ctx.trend["direction"] = "DOWN"
    ctx.mtf["htf_direction"] = "DOWN"
    ctx.current_price = 1.0800
    return ctx


def make_choppy_context(symbol: str = "EURUSD-OTC") -> MarketContext:
    """A low-quality context that should be blocked."""
    ctx = MarketContext(symbol=symbol, timestamp=datetime.now(timezone.utc),
                        timeframe="M5", current_price=1.0850)
    ctx.trend = {"direction": "NONE", "strength": 20, "confidence": 25,
                 "type": "CHOPPY", "reversal_risk": 70}
    ctx.strength = {"adx": 12, "rsi": 50, "momentum_level": "WEAK",
                    "exhaustion_risk": 75}
    ctx.volatility = {"regime": "EXTREME", "atr_percentile": 90,
                      "expansion_probability": 40}
    ctx.mtf = {"alignment_score": 30, "htf_ltf_conflict": True,
               "htf_direction": "NONE"}
    ctx.market_state = "CHOPPY"
    ctx.traps = {"trap_detected": True, "trap_type": "WICK_TRAP"}
    ctx.noise = {"noise_level": 80}
    ctx.anomaly = {"anomaly_detected": True}
    return ctx


def make_empty_context(symbol: str = "TEST") -> MarketContext:
    """An empty context as produced when no data is available."""
    ctx = MarketContext(symbol=symbol, timestamp=datetime.now(timezone.utc),
                        timeframe="M5", current_price=0.0)
    ctx.add_error("No candle data available")
    return ctx
