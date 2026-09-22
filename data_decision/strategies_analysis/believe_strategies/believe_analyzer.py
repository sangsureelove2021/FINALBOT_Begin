"""Disk-backed Believe strategy analyzer.

The analyzer reads the immutable evaluation payload itself.  It never receives
an in-memory payload from Part 2.
"""

import re
from typing import Any, Dict, Optional


def _read_fields(payload_path: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    with open(payload_path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            fields[key.strip().lower()] = value.strip().strip("'\"")
    return fields


def _direction(value: Any) -> Optional[str]:
    text = str(value or "").upper()
    if text in {"UP", "UPTREND", "BULLISH", "CALL", "BUY", "LONG"}:
        return "CALL"
    if text in {"DOWN", "DOWNTREND", "BEARISH", "PUT", "SELL", "SHORT"}:
        return "PUT"
    return None


def analyze_payload_file(symbol: str, payload_path: str) -> Dict[str, Any]:
    """Produce a conservative CALL/PUT/WAIT strategy decision from a payload file."""
    fields = _read_fields(payload_path)
    s30 = _direction(fields.get("s30_bias") or fields.get("s30_direction"))
    m1 = _direction(fields.get("m1_bias") or fields.get("m1_direction"))
    m5 = _direction(fields.get("m5_bias") or fields.get("m5_direction"))
    believe = _direction(fields.get("believe_direction"))
    # S30 is the entry trigger, M1 is the primary confirmation for the
    # five-minute hold, and M5 is only the higher-timeframe context filter.
    action = believe if believe and believe == s30 == m1 and (m5 is None or m5 == m1) else "WAIT"
    confidence = 0.0
    if action != "WAIT":
        confidence = {"HIGH": 85.0, "MEDIUM": 70.0}.get(
            str(fields.get("believe_confidence", "")).upper(), 60.0
        )

    return {
        "ID": fields.get("id") or payload_path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1].rsplit(".", 1)[0],
        "symbol": symbol,
        "action": action,
        "expiry_minutes": 5,
        "confidence_score": confidence,
        "engine_used": "STRATEGY_BELIEVE",
        "believe_status": fields.get("believe_status", "watch"),
        "believe_direction": believe or "WAIT",
        "s30_direction": s30 or "UNKNOWN",
        "m1_direction": m1 or "UNKNOWN",
        "m5_direction": m5 or "UNKNOWN",
        "extreme_believe_active": str(
            fields.get("extreme_believe_active", "false")
        ).lower() == "true",
        "reason_th": (
            f"Believe direction confirmed by S30 entry and primary M1 confirmation; M5 context aligned ({action})"
            if action != "WAIT"
            else "Believe strategy requires S30 entry, M1 primary confirmation, and non-conflicting M5 context"
        ),
    }
