import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.DEBUG)

from core.ai_analysis.deepseek_agent_bridge import DeepSeekAgentBridge

class SimpleContext:
    def __init__(self):
        self.symbol = "EURUSD"
        self.current_price = 1.15679
        self.rsi = 36.60
        self.macd = -0.000017
        self.trend = "bearish"
        self.volatility = "medium"
        self.support_resistance = "Support: 1.15500, Resistance: 1.15800"

print("Initializing bridge...")
bridge = DeepSeekAgentBridge(agent_command="deepseek-agent", timeout_seconds=75)
context = SimpleContext()

print("Calling analyze_market...")
insight = bridge.analyze_market(context)
print("\n--- RESULTS ---")
if insight:
    print(f"Action: {insight.action}")
    print(f"Confidence: {insight.confidence}%")
    print(f"Expiry: {insight.expiry}m")
    print(f"Reason: {insight.reason}")
    print(f"Raw response: {insight.raw_response}")
else:
    print("No insight returned (None)")
