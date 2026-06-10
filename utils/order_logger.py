"""
Standardized order logging for both live and backtest modes.
Writes JSONL files with consistent trade details.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Global file paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LIVE_ORDERS_FILE = PROJECT_ROOT / "logs" / "orders.jsonl"
BACKTEST_ORDERS_FILE = PROJECT_ROOT / "backtest" / "results" / "orders_backtest.jsonl"

# Ensure directories exist
LIVE_ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
BACKTEST_ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _write_order(file_path: Path, order_data: Dict[str, Any]) -> None:
    """Write a single order as a JSON line to the specified file."""
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(order_data, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to write order log to {file_path}: {e}")


def log_live_order(order_details: Dict[str, Any]) -> None:
    """
    Log a live trade to logs/orders.jsonl.
    
    Expected order_details fields:
        - timestamp (str, ISO format)
        - symbol (str)
        - direction (str, "CALL" or "PUT")
        - amount (float)
        - entry_price (float)
        - expiry (str, e.g., "M1")
        - strategy (str)
        - confidence (int)
        - order_id (str)
        - status (str, e.g., "executed", "expired", "settled")
        - exit_price (float, optional)
        - pnl (float, optional)
        - outcome (str, optional, "WIN"/"LOSS"/"TIE")
        - notes (str, optional)
    """
    # Ensure timestamp is present
    if "timestamp" not in order_details:
        order_details["timestamp"] = datetime.utcnow().isoformat()
    _write_order(LIVE_ORDERS_FILE, order_details)


def log_backtest_order(order_details: Dict[str, Any]) -> None:
    """
    Log a backtest trade to backtest/results/orders_backtest.jsonl.
    Same schema as live orders.
    """
    if "timestamp" not in order_details:
        order_details["timestamp"] = datetime.utcnow().isoformat()
    _write_order(BACKTEST_ORDERS_FILE, order_details)


def log_trade_outcome(order_id: str, exit_price: float, pnl: float, outcome: str, notes: str = "", mode: str = "live") -> None:
    """
    Helper to update an existing trade with outcome. Since JSONL is append-only,
    this logs a separate outcome record with the same order_id. For backtesting,
    we typically log the full trade at expiry.
    """
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "order_id": order_id,
        "event_type": "outcome",
        "exit_price": exit_price,
        "pnl": pnl,
        "outcome": outcome,
        "notes": notes
    }
    if mode == "live":
        _write_order(LIVE_ORDERS_FILE, record)
    else:
        _write_order(BACKTEST_ORDERS_FILE, record)
