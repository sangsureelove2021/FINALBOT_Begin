"""
Broker Executor for Part 3 Binary Options
=========================================
Directs order placement to IQ Option API via `api.buy()` with validation,
error handling, and execution logging.
"""

import time
import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("BrokerExecutor")


class BrokerExecutor:
    """Executes Binary Option buy orders against the broker connection."""

    def __init__(self):
        pass

    def _resolve_api(self, broker_or_adapter: Any) -> Any:
        """Extracts underlying iqoptionapi instance from adapter wrapper."""
        if hasattr(broker_or_adapter, "api"):
            return broker_or_adapter.api
        if hasattr(broker_or_adapter, "broker_adapter") and hasattr(broker_or_adapter.broker_adapter, "api"):
            return broker_or_adapter.broker_adapter.api
        if hasattr(broker_or_adapter, "data_adapter") and hasattr(broker_or_adapter.data_adapter, "api"):
            return broker_or_adapter.data_adapter.api
        return broker_or_adapter

    def execute_order(
        self,
        symbol: str,
        action: str,
        expiry_minutes: int,
        stake: float,
        broker_adapter: Any
    ) -> Dict[str, Any]:
        """
        Submits binary option order to broker.
        
        Args:
            symbol: Asset symbol (e.g. 'EURUSD' or 'EURUSD-OTC').
            action: 'CALL' or 'PUT'.
            expiry_minutes: Contract expiration duration in minutes (1-5).
            stake: Order amount (e.g. 35.0).
            broker_adapter: Broker facade instance.
            
        Returns:
            Execution result dict with status, order_id, symbol, action, stake, expiry_minutes, timestamp, error.
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError("FAIL-FAST: symbol must be a valid non-empty string")

        norm_action = action.strip().upper()
        if norm_action not in ("CALL", "PUT"):
            raise ValueError(f"FAIL-FAST: Invalid action '{action}', must be 'CALL' or 'PUT'")

        if not (1 <= expiry_minutes <= 5):
            raise ValueError(f"FAIL-FAST: Invalid expiry_minutes '{expiry_minutes}', must be between 1 and 5")

        if stake <= 0:
            raise ValueError(f"FAIL-FAST: Invalid stake amount '{stake}', must be positive")

        api = self._resolve_api(broker_adapter)
        if api is None or not hasattr(api, "buy"):
            raise RuntimeError("FAIL-FAST: Broker API object does not implement .buy() method")

        # Ensure connection before ordering
        if hasattr(broker_adapter, "ensure_connected"):
            try:
                broker_adapter.ensure_connected()
            except Exception as e:
                logger.exception(f"[BrokerExecutor] Failed ensure_connected check: {e}")
                raise

        tz_thailand = timezone(timedelta(hours=7))
        order_timestamp = datetime.now(tz_thailand).isoformat()
        act_param = "call" if norm_action == "CALL" else "put"

        logger.info(
            f"[BrokerExecutor] Sending Order -> Symbol: {symbol}, Action: {norm_action}, "
            f"Expiry: {expiry_minutes}m, Stake: {stake:.2f} THB"
        )

        try:
            start_t = time.time()
            status, result_id = api.buy(
                float(stake),
                str(symbol),
                str(act_param),
                int(expiry_minutes)
            )
            elapsed = round(time.time() - start_t, 3)

            if status and result_id is not None:
                order_id_str = str(result_id)
                logger.info(
                    f"[BrokerExecutor] Order Placed SUCCESS -> ID: {order_id_str}, "
                    f"Symbol: {symbol}, Action: {norm_action}, Elapsed: {elapsed}s"
                )
                return {
                    "status": "SUCCESS",
                    "order_id": order_id_str,
                    "symbol": symbol,
                    "action": norm_action,
                    "stake": float(stake),
                    "expiry_minutes": int(expiry_minutes),
                    "timestamp": order_timestamp,
                    "error": None,
                    "latency_sec": elapsed
                }
            else:
                error_reason = str(result_id) if result_id is not None else "Unknown broker rejection"
                logger.warning(
                    f"[BrokerExecutor] Order Placed FAILED -> Symbol: {symbol}, "
                    f"Action: {norm_action}, Reason: {error_reason}"
                )
                return {
                    "status": "FAILED",
                    "order_id": None,
                    "symbol": symbol,
                    "action": norm_action,
                    "stake": float(stake),
                    "expiry_minutes": int(expiry_minutes),
                    "timestamp": order_timestamp,
                    "error": error_reason,
                    "latency_sec": elapsed
                }

        except Exception as e:
            logger.exception(f"[BrokerExecutor] Exception occurred during order execution for {symbol}: {e}")
            traceback.print_exc()
            raise RuntimeError(f"FAIL-FAST: Broker order execution error for {symbol}: {e}") from e
