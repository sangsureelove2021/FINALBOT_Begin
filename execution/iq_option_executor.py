"""
IQ Option Executor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Send trade orders to IQ Option. Currently logs to file (mock mode).
Swap to real API: Replace log_order() with api.buy()/sell()
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass
import json
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
    Execute trades on IQ Option.
    
    Current Mode: MOCK (logs to file)
    
    To activate real trading:
    1. Set api_token in __init__
    2. Replace _log_order() with _api_order()
    3. pip install iqoptionapi
    
    DO NOT ENABLE REAL TRADING WITHOUT THOROUGH TESTING!
    """
    
    def __init__(self, api_token: Optional[str] = None, 
                 use_mock: bool = True,
                 log_dir: str = "./logs"):
        """
        Initialize executor.
        
        Args:
            api_token: IQ Option API token (None for mock)
            use_mock: Use mock mode (True = no real trades)
            log_dir: Directory for order logs
        """
        self.api_token = api_token
        self.use_mock = use_mock
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.api = None
        self._order_counter = 0
        self._connected = False
        
        if not use_mock and api_token:
            try:
                from iqoptionapi.api import IQOptionAPI
                self.api = IQOptionAPI("ws://", api_token, 1)
                self._connected = True
                logger.info("✅ IQ Option API connected (REAL MODE)")
            except Exception as e:
                logger.warning(f"⚠️ Could not connect to real API: {e}")
                logger.warning("🔄 Falling back to MOCK mode")
                self.use_mock = True
        else:
            logger.info("📝 Using MOCK mode (orders logged to file)")
    
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
                timestamp=datetime.utcnow().isoformat(),
                reason=f"❌ Invalid direction: {direction}"
            )
        
        try:
            if self.use_mock or not self._connected:
                return self._log_order(symbol, direction, amount, expiry)
            else:
                return self._api_order(symbol, direction, amount, expiry)
        
        except Exception as e:
            logger.error(f"Order failed: {e}")
            return OrderResult(
                order_id="ERROR", symbol=symbol, direction=direction,
                amount=amount, expiry=expiry, status='failed',
                timestamp=datetime.utcnow().isoformat(),
                reason=f"❌ Exception: {str(e)}"
            )
    
    def _log_order(self, symbol: str, direction: str, 
                   amount: float, expiry: str) -> OrderResult:
        """
        Log order to file (mock mode).
        
        In real mode, this is replaced with API call.
        """
        self._order_counter += 1
        order_id = f"MOCK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{self._order_counter:04d}"
        timestamp = datetime.utcnow().isoformat()
        
        result = OrderResult(
            order_id=order_id,
            symbol=symbol,
            direction=direction,
            amount=amount,
            expiry=expiry,
            status='pending',
            timestamp=timestamp,
            reason=f"✅ {direction} {amount:.0f}x {symbol} {expiry} [MOCK]"
        )
        
        # Log to file
        log_file = self.log_dir / f"orders_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps({
                'order_id': result.order_id,
                'symbol': result.symbol,
                'direction': result.direction,
                'amount': result.amount,
                'expiry': result.expiry,
                'timestamp': result.timestamp,
                'status': result.status,
            }) + '\n')
        
        logger.info(f"📝 {result.reason}")
        logger.debug(f"   Order ID: {order_id}")
        logger.debug(f"   Log: {log_file}")
        
        return result
    
    def _api_order(self, symbol: str, direction: str,
                   amount: float, expiry: str) -> OrderResult:
        """
        Send real order via IQ Option API (future implementation).
        """
        if not self.api:
            raise RuntimeError("API not initialized")
        
        # This will be implemented when real API key is provided
        # For now, fall back to mock
        logger.warning("Real API not yet implemented, using mock")
        return self._log_order(symbol, direction, amount, expiry)
    
    def get_order_history(self, symbol: Optional[str] = None) -> list:
        """
        Get recent orders from log file.
        
        Args:
            symbol: Filter by symbol (None = all)
        
        Returns:
            List of orders
        """
        log_file = self.log_dir / f"orders_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        
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
