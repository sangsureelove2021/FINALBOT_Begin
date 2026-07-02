import logging
from pathlib import Path
from typing import Dict, Any, Union
from datetime import datetime

logger = logging.getLogger("FINALBOT.AI_PROMPT")



import yaml
import numpy as np


def _clean_dict(obj):
    if isinstance(obj, dict):
        return {k: _clean_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_clean_dict(x) for x in obj]
    elif isinstance(obj, np.generic):
        return obj.item()
    else:
        return obj


def _get_first_present(values, default="NONE"):
    for value in values:
        if value is not None and value != "" and value != "NONE" and value != "NOT_AVAILABLE":
            return value
    return default


def _normalize_context(context: dict) -> dict:
    if not isinstance(context, dict):
        raise TypeError("context must be a dictionary")

    meta = context.get("meta", {}) if isinstance(context.get("meta"), dict) else {}
    market_context = context.get("market_context", {}) if isinstance(context.get("market_context"), dict) else {}
    market_state = context.get("market_state", {}) if isinstance(context.get("market_state"), dict) else {}
    timeframes = context.get("timeframes", {}) if isinstance(context.get("timeframes"), dict) else {}
    m1 = context.get("m1", {}) if isinstance(context.get("m1"), dict) else {}
    m5 = context.get("m5", {}) if isinstance(context.get("m5"), dict) else {}
    m15 = context.get("m15", {}) if isinstance(context.get("m15"), dict) else {}
    news = context.get("news", {}) if isinstance(context.get("news"), dict) else {}
    price_action = context.get("price_action", {}) if isinstance(context.get("price_action"), dict) else {}
    volume = context.get("volume", {}) if isinstance(context.get("volume"), dict) else {}
    analysis = context.get("analysis", {}) if isinstance(context.get("analysis"), dict) else {}
    decision_layer = context.get("decision_layer", {}) if isinstance(context.get("decision_layer"), dict) else {}
    engines = context.get("engines", {}) if isinstance(context.get("engines"), dict) else {}

    normalized = {
        "meta": {
            "timestamp": _get_first_present([meta.get("timestamp"), context.get("timestamp")], "NOT_AVAILABLE"),
            "symbol": _get_first_present([meta.get("symbol"), context.get("symbol")], "NOT_AVAILABLE"),
            "session": _get_first_present([meta.get("session")], "NOT_AVAILABLE"),
            "price": _get_first_present([meta.get("price"), meta.get("close"), meta.get("current_price"), context.get("current_price")], "NOT_AVAILABLE"),
            "data_age_ms": _get_first_present([meta.get("data_age_ms")], "NOT_AVAILABLE"),
            "data_quality": _get_first_present([meta.get("data_quality")], "NOT_AVAILABLE"),
            "data_age_ms_m1": _get_first_present([meta.get("data_age_ms_m1")], "NOT_AVAILABLE"),
            "data_quality_m1": _get_first_present([meta.get("data_quality_m1")], "NOT_AVAILABLE"),
            "data_age_ms_m5": _get_first_present([meta.get("data_age_ms_m5")], "NOT_AVAILABLE"),
            "data_quality_m5": _get_first_present([meta.get("data_quality_m5")], "NOT_AVAILABLE"),
        },
        "market_context": {
            "state": _get_first_present([market_context.get("state"), market_state.get("state")], "NOT_AVAILABLE"),
            "description": _get_first_present([market_context.get("description"), market_state.get("description")], "NOT_AVAILABLE"),
            "volatility_regime": _get_first_present([market_context.get("volatility_regime")], "NOT_AVAILABLE"),
            "news_impact": _get_first_present([market_context.get("news_impact"), news.get("impact")], "NOT_AVAILABLE"),
            "expected_volatility_%": _get_first_present([market_context.get("expected_volatility_%")], "NOT_AVAILABLE"),
        },
        "timeframes": {
            "m1": {
                "last_candle": _get_first_present([timeframes.get("m1", {}).get("last_candle"), m1.get("close")], "NOT_AVAILABLE"),
                "ema5": _get_first_present([timeframes.get("m1", {}).get("ema5"), m1.get("ema5"), m1.get("ema_5")], "NOT_AVAILABLE"),
                "ema20": _get_first_present([timeframes.get("m1", {}).get("ema20"), m1.get("ema20"), m1.get("ema_20")], "NOT_AVAILABLE"),
                "rsi": _get_first_present([timeframes.get("m1", {}).get("rsi"), m1.get("rsi"), m1.get("rsi14")], "NOT_AVAILABLE"),
                "stoch_k": _get_first_present([timeframes.get("m1", {}).get("stoch_k"), m1.get("stoch_k")], "NOT_AVAILABLE"),
                "stoch_d": _get_first_present([timeframes.get("m1", {}).get("stoch_d"), m1.get("stoch_d")], "NOT_AVAILABLE"),
                "macd": _get_first_present([timeframes.get("m1", {}).get("macd"), m1.get("macd")], "NOT_AVAILABLE"),
                "macd_signal": _get_first_present([timeframes.get("m1", {}).get("macd_signal"), m1.get("macd_signal")], "NOT_AVAILABLE"),
            },
            "m5": {
                "bias": _get_first_present([timeframes.get("m5", {}).get("bias"), m5.get("bias")], "NOT_AVAILABLE"),
                "ema5": _get_first_present([timeframes.get("m5", {}).get("ema5"), m5.get("ema5"), m5.get("ema_5")], "NOT_AVAILABLE"),
                "ema10": _get_first_present([timeframes.get("m5", {}).get("ema10"), m5.get("ema10"), m5.get("ema_10")], "NOT_AVAILABLE"),
                "ema20": _get_first_present([timeframes.get("m5", {}).get("ema20"), m5.get("ema20"), m5.get("ema_20")], "NOT_AVAILABLE"),
                "ema50": _get_first_present([timeframes.get("m5", {}).get("ema50"), m5.get("ema50"), m5.get("ema_50")], "NOT_AVAILABLE"),
                "bb_upper": _get_first_present([timeframes.get("m5", {}).get("bb_upper"), m5.get("bb_upper")], "NOT_AVAILABLE"),
                "bb_lower": _get_first_present([timeframes.get("m5", {}).get("bb_lower"), m5.get("bb_lower")], "NOT_AVAILABLE"),
                "bb_width": _get_first_present([timeframes.get("m5", {}).get("bb_width"), m5.get("bb_width")], "NOT_AVAILABLE"),
                "rsi": _get_first_present([timeframes.get("m5", {}).get("rsi"), m5.get("rsi"), m5.get("rsi14")], "NOT_AVAILABLE"),
                "stoch_k": _get_first_present([timeframes.get("m5", {}).get("stoch_k"), m5.get("stoch_k")], "NOT_AVAILABLE"),
                "stoch_d": _get_first_present([timeframes.get("m5", {}).get("stoch_d"), m5.get("stoch_d")], "NOT_AVAILABLE"),
                "macd": _get_first_present([timeframes.get("m5", {}).get("macd"), m5.get("macd")], "NOT_AVAILABLE"),
                "macd_signal": _get_first_present([timeframes.get("m5", {}).get("macd_signal"), m5.get("macd_signal")], "NOT_AVAILABLE"),
                "adx": _get_first_present([timeframes.get("m5", {}).get("adx"), m5.get("adx")], "NOT_AVAILABLE"),
                "atr": _get_first_present([timeframes.get("m5", {}).get("atr"), m5.get("atr"), m5.get("atr14")], "NOT_AVAILABLE"),
                "support": _get_first_present([timeframes.get("m5", {}).get("support"), m5.get("support")], "NOT_AVAILABLE"),
                "resistance": _get_first_present([timeframes.get("m5", {}).get("resistance"), m5.get("resistance")], "NOT_AVAILABLE"),
                "pivot": _get_first_present([timeframes.get("m5", {}).get("pivot"), m5.get("pivot")], "NOT_AVAILABLE"),
            },
            "m15": {
                "bias": _get_first_present([timeframes.get("m15", {}).get("bias"), m15.get("bias")], "NOT_AVAILABLE"),
            },
        },
        "price_action": {
            "pattern": _get_first_present([price_action.get("pattern")], "NOT_AVAILABLE"),
            "last_candle_bias": _get_first_present([price_action.get("last_candle_bias")], "NOT_AVAILABLE"),
            "body_strength": _get_first_present([price_action.get("body_strength")], "NOT_AVAILABLE"),
            "wick_dominance": _get_first_present([price_action.get("wick_dominance")], "NOT_AVAILABLE"),
            "momentum_bias": _get_first_present([price_action.get("momentum_bias")], "NOT_AVAILABLE"),
            "move_quality": _get_first_present([price_action.get("move_quality")], "NOT_AVAILABLE"),
            "trap_alert": _get_first_present([price_action.get("trap_alert")], False),
            "sr_interaction": _get_first_present([price_action.get("sr_interaction")], "NOT_AVAILABLE"),
        },
        "volume": {
            "tick_volume": _get_first_present([volume.get("tick_volume"), m5.get("volume")], 0),
            "volume_momentum": _get_first_present([volume.get("volume_momentum"), m5.get("volume_trend")], "NOT_AVAILABLE"),
            "volume_vs_average": _get_first_present([volume.get("volume_vs_average"), m5.get("volume_ratio")], "NOT_AVAILABLE"),
        },
        "analysis": {
            "trend_direction": _get_first_present([analysis.get("trend_direction")], "NOT_AVAILABLE"),
            "trend_type": _get_first_present([analysis.get("trend_type")], "NOT_AVAILABLE"),
            "trend_strength_score": _get_first_present([analysis.get("trend_strength_score"), analysis.get("trend_strength")], 0),
            "mtf_alignment_%": _get_first_present([analysis.get("mtf_alignment_%"), engines.get("mtf", {}).get("alignment_score")], "NOT_AVAILABLE"),
            "compression_quality_%": _get_first_present([analysis.get("compression_quality_%"), engines.get("volatility", {}).get("compression_quality")], "NOT_AVAILABLE"),
            "exhaustion_risk_%": _get_first_present([analysis.get("exhaustion_risk_%"), engines.get("strength", {}).get("exhaustion_risk")], "NOT_AVAILABLE"),
            "bos_detected": _get_first_present([analysis.get("bos_detected")], False),
        },

        "decision_layer": {
            "tradeable": _get_first_present([decision_layer.get("tradeable")], False),
            "stability_score": _get_first_present([decision_layer.get("stability_score")], 0),
            "quality_score": _get_first_present([decision_layer.get("quality_score")], 0),
            "risk_level": _get_first_present([decision_layer.get("risk_level")], "NOT_AVAILABLE"),
            "confidence_score": _get_first_present([decision_layer.get("confidence_score")], 0),
            "suggested_expiry_minutes": _get_first_present([decision_layer.get("suggested_expiry_minutes")], 0),
            "suggested_action": _get_first_present([decision_layer.get("suggested_action")], "NOT_AVAILABLE"),
            "final_reason_th": _get_first_present([decision_layer.get("final_reason_th")], "NOT_AVAILABLE"),
        },
    }

    if "market_context" in context and isinstance(context.get("market_context"), dict):
        normalized["market_context"] = {
            "state": _get_first_present([context["market_context"].get("state"), normalized["market_context"]["state"]], "NOT_AVAILABLE"),
            "description": _get_first_present([context["market_context"].get("description"), normalized["market_context"]["description"]], "NOT_AVAILABLE"),
            "volatility_regime": _get_first_present([context["market_context"].get("volatility_regime"), normalized["market_context"]["volatility_regime"]], "NOT_AVAILABLE"),
            "news_impact": _get_first_present([context["market_context"].get("news_impact"), normalized["market_context"]["news_impact"]], "NOT_AVAILABLE"),
            "expected_volatility_%": _get_first_present([context["market_context"].get("expected_volatility_%"), normalized["market_context"]["expected_volatility_%"]], "NOT_AVAILABLE"),
        }

    if "timeframes" in context and isinstance(context.get("timeframes"), dict):
        normalized["timeframes"] = {
            "m1": {
                "last_candle": _get_first_present([context["timeframes"].get("m1", {}).get("last_candle"), normalized["timeframes"]["m1"]["last_candle"]], "NOT_AVAILABLE"),
                "ema5": _get_first_present([context["timeframes"].get("m1", {}).get("ema5"), normalized["timeframes"]["m1"]["ema5"]], "NOT_AVAILABLE"),
                "ema20": _get_first_present([context["timeframes"].get("m1", {}).get("ema20"), normalized["timeframes"]["m1"]["ema20"]], "NOT_AVAILABLE"),
                "rsi": _get_first_present([context["timeframes"].get("m1", {}).get("rsi"), normalized["timeframes"]["m1"]["rsi"]], "NOT_AVAILABLE"),
                "stoch_k": _get_first_present([context["timeframes"].get("m1", {}).get("stoch_k"), normalized["timeframes"]["m1"]["stoch_k"]], "NOT_AVAILABLE"),
                "stoch_d": _get_first_present([context["timeframes"].get("m1", {}).get("stoch_d"), normalized["timeframes"]["m1"]["stoch_d"]], "NOT_AVAILABLE"),
                "macd": _get_first_present([context["timeframes"].get("m1", {}).get("macd"), normalized["timeframes"]["m1"]["macd"]], "NOT_AVAILABLE"),
                "macd_signal": _get_first_present([context["timeframes"].get("m1", {}).get("macd_signal"), normalized["timeframes"]["m1"]["macd_signal"]], "NOT_AVAILABLE"),
            },
            "m5": {
                "bias": _get_first_present([context["timeframes"].get("m5", {}).get("bias"), normalized["timeframes"]["m5"]["bias"]], "NOT_AVAILABLE"),
                "ema5": _get_first_present([context["timeframes"].get("m5", {}).get("ema5"), normalized["timeframes"]["m5"]["ema5"]], "NOT_AVAILABLE"),
                "ema10": _get_first_present([context["timeframes"].get("m5", {}).get("ema10"), normalized["timeframes"]["m5"]["ema10"]], "NOT_AVAILABLE"),
                "ema20": _get_first_present([context["timeframes"].get("m5", {}).get("ema20"), normalized["timeframes"]["m5"]["ema20"]], "NOT_AVAILABLE"),
                "ema50": _get_first_present([context["timeframes"].get("m5", {}).get("ema50"), normalized["timeframes"]["m5"]["ema50"]], "NOT_AVAILABLE"),
                "bb_upper": _get_first_present([context["timeframes"].get("m5", {}).get("bb_upper"), normalized["timeframes"]["m5"]["bb_upper"]], "NOT_AVAILABLE"),
                "bb_lower": _get_first_present([context["timeframes"].get("m5", {}).get("bb_lower"), normalized["timeframes"]["m5"]["bb_lower"]], "NOT_AVAILABLE"),
                "bb_width": _get_first_present([context["timeframes"].get("m5", {}).get("bb_width"), normalized["timeframes"]["m5"]["bb_width"]], "NOT_AVAILABLE"),
                "rsi": _get_first_present([context["timeframes"].get("m5", {}).get("rsi"), normalized["timeframes"]["m5"]["rsi"]], "NOT_AVAILABLE"),
                "stoch_k": _get_first_present([context["timeframes"].get("m5", {}).get("stoch_k"), normalized["timeframes"]["m5"]["stoch_k"]], "NOT_AVAILABLE"),
                "stoch_d": _get_first_present([context["timeframes"].get("m5", {}).get("stoch_d"), normalized["timeframes"]["m5"]["stoch_d"]], "NOT_AVAILABLE"),
                "macd": _get_first_present([context["timeframes"].get("m5", {}).get("macd"), normalized["timeframes"]["m5"]["macd"]], "NOT_AVAILABLE"),
                "macd_signal": _get_first_present([context["timeframes"].get("m5", {}).get("macd_signal"), normalized["timeframes"]["m5"]["macd_signal"]], "NOT_AVAILABLE"),
                "adx": _get_first_present([context["timeframes"].get("m5", {}).get("adx"), normalized["timeframes"]["m5"]["adx"]], "NOT_AVAILABLE"),
                "atr": _get_first_present([context["timeframes"].get("m5", {}).get("atr"), normalized["timeframes"]["m5"]["atr"]], "NOT_AVAILABLE"),
                "support": _get_first_present([context["timeframes"].get("m5", {}).get("support"), normalized["timeframes"]["m5"]["support"]], "NOT_AVAILABLE"),
                "resistance": _get_first_present([context["timeframes"].get("m5", {}).get("resistance"), normalized["timeframes"]["m5"]["resistance"]], "NOT_AVAILABLE"),
                "pivot": _get_first_present([context["timeframes"].get("m5", {}).get("pivot"), normalized["timeframes"]["m5"]["pivot"]], "NOT_AVAILABLE"),
            },
            "m15": {
                "bias": _get_first_present([context["timeframes"].get("m15", {}).get("bias"), normalized["timeframes"]["m15"]["bias"]], "NOT_AVAILABLE"),
            },
        }

    if "analysis" in context and isinstance(context.get("analysis"), dict):
        normalized["analysis"] = {
            "trend_direction": _get_first_present([context["analysis"].get("trend_direction"), normalized["analysis"]["trend_direction"]], "NOT_AVAILABLE"),
            "trend_type": _get_first_present([context["analysis"].get("trend_type"), normalized["analysis"]["trend_type"]], "NOT_AVAILABLE"),
            "trend_strength_score": _get_first_present([context["analysis"].get("trend_strength_score"), context["analysis"].get("trend_strength"), normalized["analysis"]["trend_strength_score"]], 0),
            "mtf_alignment_%": _get_first_present([context["analysis"].get("mtf_alignment_%"), normalized["analysis"]["mtf_alignment_%"]], "NOT_AVAILABLE"),
            "compression_quality_%": _get_first_present([context["analysis"].get("compression_quality_%"), normalized["analysis"]["compression_quality_%"]], "NOT_AVAILABLE"),
            "exhaustion_risk_%": _get_first_present([context["analysis"].get("exhaustion_risk_%"), normalized["analysis"]["exhaustion_risk_%"]], "NOT_AVAILABLE"),
            "bos_detected": _get_first_present([context["analysis"].get("bos_detected"), normalized["analysis"]["bos_detected"]], False),
        }



    if "decision_layer" in context and isinstance(context.get("decision_layer"), dict):
        normalized["decision_layer"] = {
            "tradeable": _get_first_present([context["decision_layer"].get("tradeable"), normalized["decision_layer"]["tradeable"]], False),
            "stability_score": _get_first_present([context["decision_layer"].get("stability_score"), normalized["decision_layer"]["stability_score"]], 0),
            "quality_score": _get_first_present([context["decision_layer"].get("quality_score"), normalized["decision_layer"]["quality_score"]], 0),
            "risk_level": _get_first_present([context["decision_layer"].get("risk_level"), normalized["decision_layer"]["risk_level"]], "NOT_AVAILABLE"),
            "confidence_score": _get_first_present([context["decision_layer"].get("confidence_score"), normalized["decision_layer"]["confidence_score"]], 0),
            "suggested_expiry_minutes": _get_first_present([context["decision_layer"].get("suggested_expiry_minutes"), normalized["decision_layer"]["suggested_expiry_minutes"]], 0),
            "suggested_action": _get_first_present([context["decision_layer"].get("suggested_action"), normalized["decision_layer"]["suggested_action"]], "NOT_AVAILABLE"),
            "final_reason_th": _get_first_present([context["decision_layer"].get("final_reason_th"), normalized["decision_layer"]["final_reason_th"]], "NOT_AVAILABLE"),
        }

    return normalized


def build_template_prompt(context: dict) -> str:
    # 1. Clean the context (remove numpy types)
    normalized_ctx = _clean_dict(_normalize_context(context))

    # 2. Dump as YAML using the canonical payload schema
    yaml_str = yaml.dump(normalized_ctx, allow_unicode=True, sort_keys=False, default_flow_style=False)

    return yaml_str.strip()


def build_instruction_block(context: dict) -> str:
    normalized_ctx = _clean_dict(_normalize_context(context))
    meta = normalized_ctx.get("meta", {})
    symbol = str(meta.get("symbol", "UNKNOWN")).replace("-", "").replace("_", "").replace(" ", "")
    timestamp = str(meta.get("timestamp", datetime.now().strftime("%Y-%m-%dT%H:%M:%S")))
    ts_clean = timestamp.replace('-', '').replace(':', '').replace('T', '').replace('.', '')[:14]
    prompt_id = f"{symbol}{ts_clean}"

    return f"ID:{prompt_id}\n"


def build_full_prompt(context: dict) -> str:
    normalized_ctx = _clean_dict(_normalize_context(context))
    payload_yaml = yaml.dump(normalized_ctx, allow_unicode=True, sort_keys=False, default_flow_style=False).strip()
    instruction_block = build_instruction_block(context)

    return f"{instruction_block}{payload_yaml}"


def _get_symbol_name(context: dict) -> str:
    if "meta" in context and "symbol" in context["meta"]:
        return str(context["meta"]["symbol"]).replace("-", "_")
    if "symbol" in context:
        return str(context["symbol"]).replace("-", "_")
    return "unknown_symbol"


HEADER = """คุณคือผู้เชี่ยวชาญด้านการวิเคราะห์ตลาด Binary Options ที่มีประสบการณ์มากกว่า 10 ปี คุณเชี่ยวชาญด้านการวิเคราะห์เชิงเทคนิคอย่างลึกซึ้ง ครอบคลุมทุกมิติของตลาด

═════════════════════════════════════════════════════════════
ข้อมูลสำคัญเพื่อนำไปวิเคราะห์สัญญาณ คุณต้องส่งผลการวิเคราะห์กลับมา ภายใน 15 วินาที หลังจากได้รับข้อมูลนี้
═════════════════════════════════════════════════════════════

"""

FOOTER = """
═══════════════════════════════════════════
OUTPUT FORMAT — กฎเด็ดขาด
═══════════════════════════════════════════

อ่านข้อมูล JSON ตลาดที่ให้มาแล้ว output เฉพาะ JSON นี้เท่านั้น:
{"action":"__","confidence":___,"expiry":__,"reason":_______"}

กฎ output:
- action: "CALL" | "PUT" | "NO_TRADE"
- confidence: ตัวเลขจำนวนเต็ม 0-100
- expiry: ตัวเลขจำนวนเต็ม 1-5 (นาที)
- reason: ภาษาไทย 20-40 คำ อธิบายเหตุผลหลักที่ทำให้ตัดสินใจ
"""

def save_prompt_to_disk_raw(prompt_id: str, symbol_str: str, prompt: str) -> str:
    """Save the generated prompt to the workspace logs folder immediately."""
    project_root = Path(__file__).resolve().parents[2]
    history_folder = project_root / "logs" / "logs_ai" / symbol_str
    history_folder.mkdir(parents=True, exist_ok=True)
    history_file_path = history_folder / f"{prompt_id}.txt"
    history_file_path.write_text(prompt, encoding="utf-8")
    return str(history_file_path)


def build_prompt(filepath: str) -> str:
    """
    Unified entry point to construct a full prompt command from the payload file and save it to disk.
    """
    import os
    import re
    if not isinstance(filepath, str) or not os.path.exists(filepath):
        raise ValueError(f"Valid filepath required, got: {filepath}")

    try:
        # 1. Read the raw payload from orchestrator's txt file
        with open(filepath, "r", encoding="utf-8") as f:
            yaml_content = f.read()
            
        # 2. Extract ID from the first line (e.g. ID:EURGBP2026...)
        first_line = yaml_content.split('\n')[0].strip()
        if first_line.startswith("ID:"):
            prompt_id = first_line.replace("ID:", "")
        else:
            prompt_id = "UNKNOWN_ID"
            
        # Extract symbol from prompt_id for the folder name
        match = re.match(r"([A-Za-z]+)", prompt_id)
        symbol_str = match.group(1) if match else "UNKNOWN"
            
        # 3. Combine them exactly like the Boss's template
        final_prompt = f"{HEADER}{yaml_content}\n{FOOTER}"
        
        # 4. Save to logs_ai
        saved_path = save_prompt_to_disk_raw(prompt_id, symbol_str, final_prompt)
        logger.info(f"Prompt saved to {saved_path}")
        return final_prompt
    except Exception as e:
        logger.exception(f"Failed to build prompt context from {filepath}")
        raise Exception(str(e))
