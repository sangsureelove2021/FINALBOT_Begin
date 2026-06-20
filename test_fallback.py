"""
ทดสอบ Fallback Analyzer
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from core.ai_analysis.fallback_analyzer import FallbackAnalyzer

class MockContext:
    def __init__(self):
        self.symbol = "EURUSD"
        self.current_price = 1.15679
        self.rsi = 36.60
        self.macd = -0.000017
        self.trend = "bearish"
        self.volatility = "medium"
        self.support_resistance = "Support: 1.15500, Resistance: 1.15800"

print("=" * 60)
print("Testing Fallback Analyzer")
print("=" * 60)

analyzer = FallbackAnalyzer()
context = MockContext()
result = analyzer.analyze(context)

print(f"\nResult:")
print(f"  Action: {result.action}")
print(f"  Confidence: {result.confidence}%")
print(f"  Expiry: {result.expiry}m")
print(f"  Reason: {result.reason}")
print("=" * 60)
