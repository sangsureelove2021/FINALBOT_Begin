import logging
from typing import Dict, Any, Union
from datetime import datetime

logger = logging.getLogger("FINALBOT.AI_PROMPT")

def build_advanced_prompt(context: dict) -> str:
    """
    Builds the advanced market analysis prompt using plain text format.
    Ensures no raw JSON is embedded to avoid Windows shell quoting issues.
    """
    if not isinstance(context, dict):
        raise TypeError("context must be a dictionary")
    
    # Ensure payload immutability (only reading values)
    meta = context.get("meta", {})
    mkt = context.get("market_context", {})
    tf = context.get("timeframes", {})
    m1 = tf.get("m1", {})
    m5 = tf.get("m5", {})
    m15 = tf.get("m15", {})
    pa = context.get("price_action", {})
    vol = context.get("volume", {})
    analysis = context.get("analysis", {})

    symbol = meta.get("symbol", "N/A")
    price = meta.get("price", context.get("current_price", 0))
    session = meta.get("session", "N/A")
    quality = meta.get("data_quality", "N/A")

    lines = [
        f"SYMBOL: {symbol}  |  PRICE: {price}  |  SESSION: {session}  |  DATA: {quality}",
        "",
        "=== M1 INDICATORS ===",
        f"  EMA5={m1.get('ema5','?')}  EMA20={m1.get('ema20','?')}",
        f"  RSI={m1.get('rsi','?')}  STOCH_K={m1.get('stoch_k','?')}  STOCH_D={m1.get('stoch_d','?')}",
        f"  MACD={m1.get('macd','?')}  SIGNAL={m1.get('macd_signal','?')}",
        "",
        "=== M5 INDICATORS ===",
        f"  BIAS={m5.get('bias','?')}  ADX={m5.get('adx','?')}  ATR={m5.get('atr','?')}",
        f"  EMA5={m5.get('ema5','?')}  EMA10={m5.get('ema10','?')}  EMA20={m5.get('ema20','?')}  EMA50={m5.get('ema50','?')}",
        f"  BB_UPPER={m5.get('bb_upper','?')}  BB_LOWER={m5.get('bb_lower','?')}  BB_WIDTH={m5.get('bb_width','?')}",
        f"  RSI={m5.get('rsi','?')}  STOCH_K={m5.get('stoch_k','?')}  STOCH_D={m5.get('stoch_d','?')}",
        f"  MACD={m5.get('macd','?')}  SIGNAL={m5.get('macd_signal','?')}",
        f"  SUPPORT={m5.get('support','?')}  RESISTANCE={m5.get('resistance','?')}  PIVOT={m5.get('pivot','?')}",
        "",
        "=== M15 INDICATORS ===",
        f"  BIAS={m15.get('bias','?')}",
        "",
        "=== MARKET CONTEXT ===",
        f"  STATE={mkt.get('state','?')}",
        f"  VOLATILITY={mkt.get('volatility_regime','?')}  NEWS_IMPACT={mkt.get('news_impact','?')}",
        f"  EXPECTED_VOLATILITY={mkt.get('expected_volatility_%','?')}%",
        "",
        "=== PRICE ACTION ===",
        f"  PATTERN={pa.get('pattern','?')}  CANDLE_BIAS={pa.get('last_candle_bias','?')}",
        f"  BODY_STRENGTH={pa.get('body_strength','?')}  MOMENTUM={pa.get('momentum_bias','?')}",
        f"  MOVE_QUALITY={pa.get('move_quality','?')}  TRAP_ALERT={pa.get('trap_alert','?')}",
        "",
        "=== VOLUME ===",
        f"  TICK_VOL={vol.get('tick_volume','?')}  MOMENTUM={vol.get('volume_momentum','?')}  VS_AVG={vol.get('volume_vs_average','?')}",
        "",
        "=== ANALYSIS ===",
        f"  TREND={analysis.get('trend_direction','?')}  TYPE={analysis.get('trend_type','?')}",
        f"  STRENGTH={analysis.get('trend_strength_score','?')}  MTF_ALIGN={analysis.get('mtf_alignment_%','?')}%",
        f"  BOS={analysis.get('bos_detected','?')}  EXHAUSTION_RISK={analysis.get('exhaustion_risk_%','?')}%",
        "",
        "=== TASK ===",
        "Read ALL market data above carefully.",
        "Output ONLY this JSON (no tool_call, no prose, no code block):",
        '{"action":"CALL or PUT or NO_TRADE","confidence":0-100,"expiry":1-5,"reason":"ภาษาไทย 20-40 คำ"}',
    ]
    return "\n".join(lines)


def build_legacy_prompt(context: dict) -> str:
    """
    Builds the legacy market analysis prompt.
    """
    if not isinstance(context, dict):
        raise TypeError("context must be a dictionary")
        
    symbol = context.get('symbol', 'EURUSD')
    current_price = context.get('current_price', 0.0)
    rsi = context.get('rsi', 50.0)
    macd = context.get('macd', 0.0)
    trend = context.get('trend', 'neutral')
    volatility = context.get('volatility', 'medium')
    support_resistance = context.get('support_resistance', 'N/A')
    
    prompt = f"""You are a professional binary options trader (NOT a coding assistant).
Your ONLY job right now is to read the market data below and output a JSON trading decision.

ABSOLUTE RULES — VIOLATION = TASK FAILURE:
- You are 100% DONE after typing the JSON. Do NOT call any tool.
- Do NOT call read_file, write_file, run_command, or ANY other tool.
- Do NOT output a tool_call block.
- Output ONLY the raw JSON object. Nothing before it. Nothing after it.
- All keys and string values MUST use double quotes.
- The "reason" field MUST be in Thai, 20-40 words.

EXPIRY: Choose 1-5 minutes based on volatility and trend strength.
ACTION: Must be exactly "CALL", "PUT", or "NO_TRADE".

MARKET DATA:
Symbol: {symbol}
Current Price: {current_price}
Timestamp: {datetime.now().isoformat()}

TECHNICAL INDICATORS:
- RSI (14): {rsi:.2f}
- MACD Histogram/Difference: {macd:.5f}
- Trend: {trend}
- Volatility: {volatility}
- Support/Resistance: {support_resistance}

YOUR FINAL RESPONSE (raw JSON only, no tool_call, no prose):
{{
  "action": "CALL",
  "confidence": 85,
  "expiry": 3,
  "reason": "เหตุผลสำคัญที่สุดเป็นภาษาไทย 20-40 คำ"
}}"""
    return prompt


def build_prompt(context: dict) -> str:
    """
    Unified entry point to construct a prompt based on the context type.
    """
    if not isinstance(context, dict):
        raise TypeError("context must be a dictionary")
        
    # Check if pre-formatted prompt text exists (from Orchestrator)
    if "text_prompt" in context:
        return context["text_prompt"]
    if "raw_text_prompt" in context:
        return context["raw_text_prompt"]
        
    try:
        if context.get("is_advanced"):
            return build_advanced_prompt(context)
        else:
            return build_legacy_prompt(context)
    except Exception as e:
        import traceback
        logger.exception("Failed to build prompt context")
        raise e
