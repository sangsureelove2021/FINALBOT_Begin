"""
Shared utilities for M5 Binary Options strategies.
All strategies target 5-minute expiry with mean-reversion / momentum logic
aligned to the v3 MarketStateClassifier states.
"""

from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from core.models.market_context import MarketContext

# States where reversal / range strategies are allowed
REVERSAL_STATES = frozenset({"EXHAUSTION_ZONE", "MEAN_REVERSION_ZONE", "CHOPPY_UNCERTAIN", "RANGE_BOUND", "TRENDING_OVEREXTENDED"})
# States where mild momentum strategies may operate
MOMENTUM_STATES = frozenset({"MEAN_REVERSION_ZONE", "CHOPPY_UNCERTAIN", "RANGE_BREAKOUT"})
BLOCKED_STATES = frozenset({"VOLATILITY_EXPANDING", "LIQUIDITY_VOID"})

MIN_CANDLES = 50
PAYOUT_BREAKEVEN_WR = 0.5405  # 35 stake, 85% payout


def get_market_state(context: MarketContext) -> Tuple[str, str]:
    state = "UNCLEAR"
    lifecycle = "FRESH"
    if isinstance(context.market_state, dict):
        state = context.market_state.get("state", "UNCLEAR").upper()
        lifecycle = context.market_state.get("lifecycle", "FRESH").upper()
    elif isinstance(context.market_state, str):
        state = context.market_state.upper()
    return state, lifecycle


def get_m5_df(context: MarketContext, min_len: int = MIN_CANDLES) -> Optional[pd.DataFrame]:
    df = context.candles.get("M5")
    if df is None or len(df) < min_len:
        return None
    return df


def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat(
        [high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))


def calc_bollinger(close: pd.Series, window: int = 20, std_mult: float = 2.0):
    mid = close.rolling(window).mean()
    std = close.rolling(window).std(ddof=0)
    upper = mid + std_mult * std
    lower = mid - std_mult * std
    return mid, upper, lower


def calc_stochastic(
    df: pd.DataFrame, k_period: int = 14, d_period: int = 3
) -> Tuple[pd.Series, pd.Series]:
    low_min = df["low"].rolling(k_period).min()
    high_max = df["high"].rolling(k_period).max()
    denom = (high_max - low_min).replace(0, 1e-9)
    k = 100 * (df["close"] - low_min) / denom
    d = k.rolling(d_period).mean()
    return k, d


def calc_adx(df: pd.DataFrame, period: int = 14) -> float:
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat(
        [high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()],
        axis=1,
    ).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    up = high.diff()
    down = -low.diff()
    pos_dm = np.where((up > down) & (up > 0), up, 0)
    neg_dm = np.where((down > up) & (down > 0), down, 0)
    pos_di = 100 * pd.Series(pos_dm).ewm(alpha=1 / period, adjust=False).mean() / (atr + 1e-9)
    neg_di = 100 * pd.Series(neg_dm).ewm(alpha=1 / period, adjust=False).mean() / (atr + 1e-9)
    dx = 100 * (pos_di - neg_di).abs() / (pos_di + neg_di + 1e-9)
    adx = dx.ewm(alpha=1 / period, adjust=False).mean()
    val = float(adx.iloc[-1])
    return val if not np.isnan(val) else 20.0


def cluster_sr_levels(
    df: pd.DataFrame, lookback: int = 30, window: int = 3, threshold: float = 0.00025
) -> Tuple[List[float], List[float]]:
    highs = df["high"].values
    lows = df["low"].values
    start = max(window, len(df) - lookback)
    end = len(df) - window
    supports, resistances = [], []

    for i in range(start, end):
        if all(highs[i] > highs[i - j] and highs[i] > highs[i + j] for j in range(1, window + 1)):
            resistances.append(highs[i])
        if all(lows[i] < lows[i - j] and lows[i] < lows[i + j] for j in range(1, window + 1)):
            supports.append(lows[i])

    def _cluster(levels: List[float]) -> List[float]:
        if not levels:
            return []
        levels = sorted(levels)
        clusters, curr = [], [levels[0]]
        for lvl in levels[1:]:
            if (lvl - curr[0]) / curr[0] <= threshold:
                curr.append(lvl)
            else:
                clusters.append(float(np.mean(curr)))
                curr = [lvl]
        clusters.append(float(np.mean(curr)))
        return clusters

    return _cluster(supports), _cluster(resistances)


def is_news_blackout(context: MarketContext) -> bool:
    if getattr(context, "news_blackout", False):
        return True
    if isinstance(context.market_state, dict) and context.market_state.get("news_blackout"):
        return True
    return False


def is_broker_feed_stale(context: MarketContext, max_seconds: float = 10.0) -> bool:
    if context.timestamp is None:
        return False
    now = datetime.now(timezone.utc)
    ts = context.timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (now - ts).total_seconds() > max_seconds


def candle_metrics(df: pd.DataFrame) -> Dict[str, float]:
    o, h, l, c = (float(df[x].iloc[-1]) for x in ("open", "high", "low", "close"))
    body = abs(c - o)
    height = h - l
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    return {
        "open": o, "high": h, "low": l, "close": c,
        "body": body, "height": height,
        "upper_wick": upper_wick, "lower_wick": lower_wick,
        "bullish": c > o,
        "bearish": c < o,
    }


def apply_lifecycle_penalty(score: float, lifecycle: str, state: str) -> float:
    if lifecycle == "EXHAUSTED":
        return 0.0
    if lifecycle == "LATE":
        score *= 0.90
    if state == "CHOPPY_UNCERTAIN":
        score *= 0.85
    return max(0.0, min(100.0, score))


def confidence_from_components(
    wick_ratio: float, penetration_atr: float, level_strength: float = 50.0
) -> float:
    s_wick = min(1.0, max(0.0, (wick_ratio - 0.3) / 1.2))
    s_pen = min(1.0, penetration_atr / 0.25)
    s_lvl = min(1.0, level_strength / 100.0)
    raw = 0.35 * s_wick + 0.30 * s_pen + 0.25 * s_lvl + 0.10
    return max(0.0, min(1.0, raw))


def passes_quality_gate(
    entry_score: float,
    block_score: float,
    strategy_confidence: float,
    min_entry: float = 68.0,
    max_block: float = 45.0,
    min_conf_pct: int = 72,
) -> bool:
    conf_pct = int(strategy_confidence * 100) if strategy_confidence <= 1 else int(strategy_confidence)
    return entry_score >= min_entry and block_score < max_block and conf_pct >= min_conf_pct


def build_signal(
    strategy_name: str,
    action: str,
    entry_score: float,
    block_score: float,
    strategy_confidence: float,
    details: Optional[Dict] = None,
    audit_id: Optional[str] = None,
) -> Dict[str, Any]:
    conf = max(0.0, min(1.0, strategy_confidence))
    return {
        "strategy_name": strategy_name,
        "eligible": True,
        "action": action,
        "entry_score": max(0.0, min(100.0, entry_score)),
        "block_score": max(0.0, min(100.0, block_score)),
        "strategy_confidence": conf,
        "direction_confidence": conf,
        "confidence": int(conf * 100),
        "expected_state": details.get("market_state", "UNCLEAR") if details else "UNCLEAR",
        "fail_reason_code": None,
        "audit_id": audit_id or str(uuid.uuid4()),
        "expiry": "M5",
        "reason": details.get("pattern", action) if details else action,
        "details": details or {},
    }


def build_no_setup(
    strategy_name: str,
    reason: str,
    market_state: str = "UNCLEAR",
    details: Optional[Dict] = None,
    hard_block: bool = False,
) -> Dict[str, Any]:
    return {
        "strategy_name": strategy_name,
        "eligible": reason != "MARKET_STATE_BLOCKED",
        "action": "NO_SETUP",
        "entry_score": 0.0,
        "block_score": 100.0 if hard_block or reason == "MARKET_STATE_BLOCKED" else 0.0,
        "strategy_confidence": 0.0,
        "direction_confidence": 0.0,
        "confidence": 0,
        "expected_state": market_state,
        "fail_reason_code": reason,
        "audit_id": str(uuid.uuid4()),
        "expiry": "M5",
        "reason": reason,
        "details": details or {},
    }
