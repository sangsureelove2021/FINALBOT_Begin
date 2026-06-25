"""
IQ Option Executor

Send trade orders to IQ Option via the live API.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class OrderResult:
    """Result of order execution."""
    order_id: str
    symbol: str
    direction: str
    amount: float
    expiry: str
    status: str  # 'pending', 'executed', 'failed'
    timestamp: str
    reason: str


class IQOptionExecutor:
    """
    Execute trades on IQ Option through the live API.
    """
    
    def __init__(self,
                 adapter=None,
                 email: Optional[str] = None,
                 password: Optional[str] = None,
                 account_type: str = "PRACTICE",
                 log_dir: str = "./logs",
                 api_token: Optional[str] = None):
        """
        Initialize executor.

        Args:
            adapter: an already-connected IQOptionAdapter (reuses its API).
            email / password: only used if adapter is None.
            account_type: 'PRACTICE' (demo) or 'REAL'.
            log_dir: directory for order logs.
            api_token: legacy, unused.
        """
        import os
        self.account_type = account_type
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        self.api = None
        self._order_counter = 0
        self._connected = False

        # Reuse adapter's API if available
        if adapter is not None and getattr(adapter, "api", None) is not None:
            self.api = adapter.api
            self._connected = True
            logger.info("[OK] Executor reusing IQ Option connection from adapter")
            return

        # Otherwise connect with own credentials (env > settings.json)
        if not (email and password):
            try:
                from config.config_loader import get_iq_credentials
                email, password = get_iq_credentials()
            except Exception:
                email = email or os.getenv("IQ_EMAIL", "")
                password = password or os.getenv("IQ_PASSWORD", "")
        if not email or not password:
            raise RuntimeError(
                "Executor needs credentials. Pass an `adapter`, or "
                "email/password, or set IQ_EMAIL / IQ_PASSWORD env vars."
            )

        try:
            from iqoptionapi.stable_api import IQ_Option
        except ImportError as e:
            raise RuntimeError(
                "iqoptionapi library not installed. Run: pip install iqoptionapi"
            ) from e

        self.api = IQ_Option(email, password)
        ok, reason = self.api.connect()
        if not ok:
            raise RuntimeError(f"Executor login failed: {reason}")
        try:
            self.api.change_balance(account_type)
        except Exception as e:
            logger.warning(f"[WARN] change_balance({account_type}) failed: {e}")
        self._connected = True
        mode = "DEMO" if account_type == "PRACTICE" else "REAL MONEY"
        logger.info(f"[CONN] Executor connected to IQ Option ({mode})")
    
    def is_connected(self) -> bool:
        """Check if connected to broker."""
        return self._connected and self.api is not None
    
    def send_order(self, symbol: str, direction: str, 
                   amount: float, expiry: str = 'M5') -> OrderResult:
        """
        Send buy/sell order.
        
        Args:
            symbol: 'EURUSD'
            direction: 'CALL' (up) or 'PUT' (down)
            amount: Trade size (contracts)
            expiry: 'M1', 'M5', 'M15' (expiration time)
        
        Returns:
            OrderResult with status
        """
        if direction not in ['CALL', 'PUT']:
            return OrderResult(
                order_id="INVALID", symbol=symbol, direction=direction,
                amount=amount, expiry=expiry, status='failed',
                timestamp=datetime.now(timezone.utc).isoformat(),
                reason=f"[ERR] Invalid direction: {direction}"
            )
        
        try:
            if not self._connected:
                return OrderResult(
                    order_id="DISCONNECTED", symbol=symbol, direction=direction,
                    amount=amount, expiry=expiry, status='failed',
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    reason="Executor is not connected to IQ Option",
                )
            return self._api_order(symbol, direction, amount, expiry)
        
        except Exception as e:
            logger.error(f"Order failed: {e}")
            return OrderResult(
                order_id="ERROR", symbol=symbol, direction=direction,
                amount=amount, expiry=expiry, status='failed',
                timestamp=datetime.now(timezone.utc).isoformat(),
                reason=f"[ERR] Exception: {str(e)}"
            )
    
    # Map expiry codes to duration in minutes
    _EXPIRY_MINUTES = {'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30, 'M60': 60}

    def _api_order(self, symbol: str, direction: str,
                   amount: float, expiry: str) -> OrderResult:
        """
        Place a real binary-option order via the IQ Option API.

        Uses the community `iqoptionapi` library. IQ Option has no
        official API — verify method names against the installed
        library version, and ALWAYS test on a DEMO account first.

        Args:
            symbol: e.g. 'EURUSD-OTC'
            direction: 'CALL' (up) or 'PUT' (down)
            amount: stake size
            expiry: 'M1', 'M5', etc.

        Returns:
            OrderResult with the broker's order id and status.
        """
        if not self.api:
            raise RuntimeError("API not initialized")

        # Parse duration dynamically (e.g. 'M3' -> 3, '3' -> 3)
        duration = 5
        if isinstance(expiry, str):
            if expiry.startswith('M'):
                try:
                    duration = int(expiry[1:])
                except:
                    duration = self._EXPIRY_MINUTES.get(expiry, 5)
            else:
                try:
                    duration = int(expiry)
                except:
                    duration = 5
        elif isinstance(expiry, (int, float)):
            duration = int(expiry)
            
        action = direction.lower()  # iqoptionapi expects 'call' / 'put'
        timestamp = datetime.now(timezone.utc).isoformat()

        # iqoptionapi: buy(amount, active, action, duration)
        # returns (success: bool, order_id)
        try:
            success, order_id = self.api.buy(amount, symbol, action, duration)
        except Exception as e:
            return OrderResult(
                order_id="ERROR", symbol=symbol, direction=direction,
                amount=amount, expiry=expiry, status="failed",
                timestamp=timestamp, reason=f"API buy() failed: {e}",
            )

        if not success:
            return OrderResult(
                order_id="REJECTED", symbol=symbol, direction=direction,
                amount=amount, expiry=expiry, status="failed",
                timestamp=timestamp,
                reason=f"Broker rejected order for {symbol}",
            )

        logger.info(f"[OK] LIVE order placed: {direction} {amount} {symbol} "
                    f"{expiry} (id={order_id})")
        return OrderResult(
            order_id=str(order_id), symbol=symbol, direction=direction,
            amount=amount, expiry=expiry, status="executed",
            timestamp=timestamp,
            reason=f"LIVE {direction} {amount:.0f}x {symbol} {expiry}",
        )

    def get_order_history(self, symbol: Optional[str] = None) -> list:
        """
        Get recent orders from log file.
        
        Args:
            symbol: Filter by symbol (None = all)
        
        Returns:
            List of orders
        """
        log_file = self.log_dir / f"orders_{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl"
        
        if not log_file.exists():
            return []
        
        orders = []
        with open(log_file, 'r') as f:
            for line in f:
                if line.strip():
                    order = json.loads(line)
                    if symbol is None or order['symbol'] == symbol:
                        orders.append(order)
        
        return orders
