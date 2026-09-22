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
    """Produce a CALL/PUT/WAIT Believe decision from a payload file.

    Timeframe roles (per BOSS specification):
        S30 = Entry    -> the S30 candle must close in the trigger direction;
                          it supplies the entry timing/confirmation only.
        M1  = Trigger  -> the Believe indicator setup (BB %B + Stochastic +
                          MA cross) is evaluated on M1 by Part 2 and delivered
                          as ``believe_direction``; this is the signal itself.
        M5  = Context  -> higher-timeframe context; it must NOT oppose the
                          trigger.  An absent/neutral M5 passes.

    Decision rule:
        action = trigger  iff  trigger exists
                           and S30 entry aligns with trigger
                           and M5 context does not oppose trigger
                 else WAIT
    """
    fields = _read_fields(payload_path)

    # M1 = Trigger : Believe setup computed on M1 by Part 2.
    trigger = _direction(fields.get("believe_direction"))
    # S30 = Entry : entry candle direction.
    entry = _direction(fields.get("s30_bias") or fields.get("s30_direction"))
    # M5 = Context : higher-timeframe context.
    context = _direction(fields.get("m5_bias") or fields.get("m5_direction"))
    # Kept for transparency/audit only; M1's decision role is the trigger above.
    m1 = _direction(fields.get("m1_bias") or fields.get("m1_direction"))

    if trigger is None:
        action = "WAIT"
        block = "no Believe trigger on M1"
    elif entry != trigger:
        action = "WAIT"
        block = f"S30 entry ({entry or 'NONE'}) does not align with M1 trigger ({trigger})"
    elif context is not None and context != trigger:
        action = "WAIT"
        block = f"M5 context ({context}) opposes M1 trigger ({trigger})"
    else:
        action = trigger
        block = ""

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
        "believe_direction": trigger or "WAIT",
        "s30_direction": entry or "UNKNOWN",
        "m1_direction": m1 or "UNKNOWN",
        "m5_direction": context or "UNKNOWN",
        "extreme_believe_active": str(
            fields.get("extreme_believe_active", "false")
        ).lower() == "true",
        "reason_th": (
            f"M1 trigger {trigger} + S30 entry aligned + M5 context non-opposing ({action})"
            if action != "WAIT"
            else f"Believe WAIT: {block or 'trigger absent'} "
                 f"[trigger={trigger or 'NONE'}, entry={entry or 'NONE'}, context={context or 'NONE'}]"
        ),
    }
