"""
Trade data logger – saves market context JSON files to logs/logs_trade/
"""

import os
import json
from datetime import datetime
import logging

logger = logging.getLogger("TradeLogger")


def log_market_context(context, symbol_override=None):
    """
    Log the market context data (same as sent to AI) into a JSON file.
    
    Args:
        context: object with attributes: symbol, current_price, trend, volatility,
                 support_resistance, rsi, macd, market_state
        symbol_override: optional symbol string if context has no symbol
    """
    try:
        log_dir = "logs/logs_trade"
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Get symbol from context or override
        symbol = getattr(context, 'symbol', None) or symbol_override or "unknown"
        # Clean symbol for filename (remove any path separators)
        safe_symbol = symbol.replace('/', '_').replace('\\', '_')
        filename = f"{safe_symbol}_{timestamp_str}.json"
        filepath = os.path.join(log_dir, filename)
        
        # Build data dict exactly as it will be sent to AI
        data = {
            "timestamp": timestamp.isoformat(),
            "symbol": symbol,
            "current_price": getattr(context, 'current_price', None),
            "trend": getattr(context, 'trend', None),
            "volatility": getattr(context, 'volatility', None),
            "support_resistance": getattr(context, 'support_resistance', None),
            "rsi": getattr(context, 'rsi', None),
            "macd": getattr(context, 'macd', None),
            "market_state": getattr(context, 'market_state', None),
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Optional: print confirmation (but avoid clutter)
        # print(f"📝 Logged market context to {filepath}")
        
    except Exception as e:
        logger.error(f"Failed to log market context: {e}")
