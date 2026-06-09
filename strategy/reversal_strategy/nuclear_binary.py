import logging
import uuid
from typing import Dict, Any
import pandas as pd
import numpy as np

from strategy.base_strategy import BaseStrategy
from core.models.market_context import MarketContext

logger = logging.getLogger(__name__)

class NuclearBinaryStrategy(BaseStrategy):
    """
    Ultimate Binary Options 5M Strategy (Nuclear Authorization)
    Combines BB, RSI, and Price Action Rejection.
    """
    STRATEGY_NAME = "nuclear_binary"
    REQUIRED_MARKET_STATE = "any"
    MIN_CONFIDENCE = 0.0

    def is_eligible(self, context: MarketContext) -> bool:
        if not context or not context.symbol:
            return False
        return True

    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        audit_id = str(uuid.uuid4())

        if not self.is_eligible(context):
            return self._build_no_setup(audit_id, "NOT_ELIGIBLE")

        df = context.candles.get('M5') or context.candles.get('M1')
        if df is None or len(df) < 50:
            return self._build_no_setup(audit_id, "INSUFFICIENT_DATA")

        try:
            close_p = df['close']
            high_p = df['high']
            low_p = df['low']
            open_p = df['open']
            
            # BB
            bb_window = 20
            bb_std = 2.0
            rolling_mean = close_p.rolling(window=bb_window).mean()
            rolling_std = close_p.rolling(window=bb_window).std(ddof=0)
            upper_band = rolling_mean + (bb_std * rolling_std)
            lower_band = rolling_mean - (bb_std * rolling_std)
            
            # RSI
            delta = close_p.diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            rs = gain / (loss + 1e-9)
            rsi = 100 - (100 / (1 + rs))

            c_open = float(open_p.iloc[-1])
            c_close = float(close_p.iloc[-1])
            c_high = float(high_p.iloc[-1])
            c_low = float(low_p.iloc[-1])
            
            body_size = abs(c_close - c_open)
            upper_wick = c_high - max(c_open, c_close)
            lower_wick = min(c_open, c_close) - c_low
            
            ub = float(upper_band.iloc[-1])
            lb = float(lower_band.iloc[-1])
            current_rsi = float(rsi.iloc[-1])
            
            # State eligibility
            market_state_name = "UNCLEAR"
            if isinstance(context.market_state, dict):
                market_state_name = context.market_state.get('state', 'UNCLEAR').upper()
            elif hasattr(context, 'market_state') and isinstance(context.market_state, str):
                market_state_name = context.market_state.upper()
                
            if market_state_name not in ["EXHAUSTION_ZONE", "MEAN_REVERSION_ZONE", "CHOPPY_UNCERTAIN"]:
                return self._build_no_setup(audit_id, "MARKET_STATE_BLOCKED", {"state": market_state_name})

            action = "NO_SETUP"
            
            # Stricter conditions on M5 candle: RSI < 35 / > 65, touch BB, clear rejection wick
            if c_low <= lb and current_rsi < 35:
                if lower_wick >= body_size * 0.5: # Clear rejection from bottom
                    action = "CALL"
            elif c_high >= ub and current_rsi > 65:
                if upper_wick >= body_size * 0.5: # Clear rejection from top
                    action = "PUT"
                    
            if action == "NO_SETUP":
                return self._build_no_setup(audit_id, "NO_SIGNAL")

            return {
                "strategy_name": self.STRATEGY_NAME,
                "eligible": True,
                "action": action,
                "entry_score": 85.0,
                "block_score": 0.0,
                "strategy_confidence": 0.9,
                "direction_confidence": 0.9,
                "expected_state": market_state_name,
                "fail_reason_code": None,
                "audit_id": audit_id,
                "expiry": "M5",
                "details": {"rsi": current_rsi}
            }

        except Exception as e:
            logger.error(f"Error evaluating {self.STRATEGY_NAME}: {e}")
            return self._build_no_setup(audit_id, f"ERROR_{str(e).upper().replace(' ', '_')}")

    def _build_no_setup(self, audit_id: str, reason: str, details: dict = None) -> Dict[str, Any]:
        if details is None:
            details = {}
        return {
            "strategy_name": self.STRATEGY_NAME,
            "eligible": True if reason != "MARKET_STATE_BLOCKED" else False,
            "action": "NO_SETUP",
            "entry_score": 0.0,
            "block_score": 100.0,
            "strategy_confidence": 0.0,
            "direction_confidence": 0.0,
            "expected_state": "UNCLEAR",
            "fail_reason_code": reason,
            "audit_id": audit_id,
            "expiry": "M5",
            "details": details
        }
