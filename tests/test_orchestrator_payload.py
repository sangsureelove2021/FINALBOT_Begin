import unittest

from core.ai_analysis.prompt_ai_context import _normalize_context
from core.orchestration.orchestrator import Orchestrator


class OrchestratorPayloadTests(unittest.TestCase):
    def _make_orchestrator(self):
        return object.__new__(Orchestrator)

    def test_format_payload_computes_missing_values_without_none_fallback(self):
        orchestrator = self._make_orchestrator()
        payload = {
            "symbol": "EURUSD",
            "timestamp": "2026-06-29T12:00:00",
            "meta": {"close": 1.105, "session": "LONDON"},
            "m5": {
                "ema20": 1.100,
                "ema50": 1.095,
                "ema100": 1.090,
                "ema200": 1.085,
                "rsi14": 62,
                "stoch_k": 55,
                "stoch_d": 53,
                "macd": 0.0003,
                "macd_signal": 0.0001,
                "atr14": 0.0018,
                "atr_percentile": 40,
                "atr_zscore": 0.6,
                "bb_width": 0.0025,
                "volume": 1200,
                "volume_ratio": 1.4,
                "pivot": 1.103,
            },
            "m1": {
                "ema5": 1.104,
                "ema20": 1.101,
                "rsi14": 58,
                "stoch_k": 51,
                "stoch_d": 49,
                "macd": 0.00012,
                "macd_signal": 0.00005,
                "volume_ratio": 1.1,
            },
            "analysis": {
                "trend_direction": "UP",
                "trend_type": "IMPULSIVE",
                "trend_strength": 70,
                "volatility_regime": "HIGH",
            },
            "engines": {
                "trend": {"strength": 78, "confidence": 82},
                "strength": {"exhaustion_risk": 24},
                "volatility": {"compression_quality": 76},
                "mtf": {"alignment_score": 72},
            },
            "signals": {},
            "decision_layer": {},
            "price_action": {},
            "market_context": {"state": "TRENDING"},
            "market_state_full": {"state": "TRENDING_STRONG", "tradeable": True, "metrics": {"alignment_score": 72}},
        }

        formatted = orchestrator._format_payload(payload)

        self.assertEqual(formatted["timeframes"]["m5"]["bias"], "BULLISH")
        self.assertEqual(formatted["analysis"]["trend_strength_score"], 70)
        self.assertEqual(formatted["analysis"]["mtf_alignment_%"], 72)
        self.assertEqual(formatted["decision_layer"]["tradeable"], True)
        self.assertEqual(formatted["decision_layer"]["suggested_action"], "WAIT")

        def walk(obj):
            if isinstance(obj, dict):
                for value in obj.values():
                    walk(value)
            elif isinstance(obj, list):
                for value in obj:
                    walk(value)
            else:
                self.assertNotEqual(obj, "NONE")

        walk(formatted)

    def test_otc_payload_uses_neutral_volume_and_explicit_news_label(self):
        orchestrator = self._make_orchestrator()
        payload = {
            "symbol": "EURUSD_OTC",
            "timestamp": "2026-06-29T12:00:00",
            "meta": {"close": 1.103, "session": "LONDON"},
            "m5": {"ema20": 1.100, "ema50": 1.095, "ema100": 1.090, "ema200": 1.085, "rsi14": 60, "stoch_k": 52, "stoch_d": 50, "macd": 0.0002, "macd_signal": 0.0001, "atr14": 0.0016, "atr_percentile": 41, "atr_zscore": 0.5, "bb_width": 0.0022, "volume": 1200, "volume_ratio": 1.4, "pivot": 1.102},
            "m1": {"ema5": 1.102, "ema20": 1.101, "rsi14": 58, "stoch_k": 51, "stoch_d": 49, "macd": 0.0001, "macd_signal": 0.00005, "volume_ratio": 1.1},
            "analysis": {"trend_direction": "UP", "trend_type": "IMPULSIVE", "trend_strength": 68, "volatility_regime": "HIGH"},
            "engines": {"trend": {"strength": 74, "confidence": 80}, "strength": {"exhaustion_risk": 22}, "volatility": {"compression_quality": 75}, "mtf": {"alignment_score": 71}},
            "signals": {},
            "decision_layer": {},
            "price_action": {},
            "market_context": {"state": "TRENDING"},
        }

        formatted = orchestrator._format_payload(payload)

        self.assertEqual(formatted["market_context"]["news_impact"], "NONE_OTC")
        self.assertEqual(formatted["volume"]["tick_volume"], 1.0)
        self.assertEqual(formatted["volume"]["volume_momentum"], "NO_VOLUME_DATA")
        self.assertEqual(formatted["volume"]["volume_vs_average"], 1.0)

    def test_prompt_normalization_uses_explicit_not_available_markers(self):
        context = {
            "symbol": "EURUSD",
            "timestamp": "2026-06-29T12:00:00",
            "meta": {"close": 1.105},
            "m5": {"ema20": 1.100},
            "m1": {"ema20": 1.101},
            "analysis": {"trend_direction": "UP"},
            "engines": {},
            "market_context": {"state": "TRENDING"},
        }

        normalized = _normalize_context(context)

        self.assertEqual(normalized["market_context"]["description"], "NOT_AVAILABLE")
        self.assertEqual(normalized["price_action"]["pattern"], "NOT_AVAILABLE")
        self.assertEqual(normalized["volume"]["volume_momentum"], "NOT_AVAILABLE")


if __name__ == "__main__":
    unittest.main()
