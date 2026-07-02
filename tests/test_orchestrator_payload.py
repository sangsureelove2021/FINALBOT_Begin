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
            "meta": {"close": 1.105, "open": 1.098, "session": "LONDON", "data_age_ms": 100000, "data_quality": "HIGH", "data_age_ms_m1": 100000, "data_quality_m1": "LOW", "data_age_ms_m5": 200000, "data_quality_m5": "MEDIUM"},
            "m5": {
                "bias": "BULLISH",
                "ema5": 1.102,
                "ema10": 1.098,
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
                "adx": 24,
                "atr_percentile": 40,
                "atr_zscore": 0.6,
                "bb_upper": 1.108,
                "bb_lower": 1.092,
                "bb_width": 0.0025,
                "volume": 1200,
                "volume_ratio": 1.4,
                "support": 1.091,
                "resistance": 1.103,
                "pivot": 1.103,
            },
            "m1": {
                "open": 1.103,
                "ema5": 1.104,
                "ema20": 1.101,
                "rsi14": 58,
                "stoch_k": 51,
                "stoch_d": 49,
                "macd": 0.00012,
                "macd_signal": 0.00005,
                "volume_ratio": 1.1,
            },
            "m15": {"bias": "BULLISH"},
            "analysis": {
                "trend_direction": "UP",
                "trend_type": "IMPULSIVE",
                "trend_strength": 70,
                "volatility_regime": "HIGH",
            },
            "engines": {
                "trend": {"strength": 78, "confidence": 82},
                "strength": {"exhaustion_risk": 24},
                "structure": {"bos_detected": False},
                "volatility": {"compression_quality": 76},
                "mtf": {"alignment_score": 72},
            },
            "signals": {},
            "decision_layer": {
                "tradeable": True,
                "stability_score": 55,
                "quality_score": 60,
                "risk_level": "LOW",
                "confidence_score": 80,
                "suggested_expiry_minutes": 5,
                "suggested_action": "WAIT",
                "final_reason_th": "EXPLAIN_NONE",
            },
            "price_action": {
                "pattern": "NO_PATTERN",
                "last_candle_bias": "BULLISH",
                "body_strength": 0.4,
                "wick_dominance": "HIGH",
                "momentum_bias": "UP",
                "move_quality": "GOOD",
                "trap_alert": False,
                "sr_interaction": "NO_INTERACTION",
                "volume_momentum": "STABLE",
            },
            "market_context": {"state": "TRENDING", "description": "Strong uptrend", "volatility_regime": "HIGH", "news_impact": "LOW", "expected_volatility_%": 18},
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
            "meta": {"close": 1.103, "open": 1.100, "session": "LONDON", "data_age_ms": 100000, "data_quality": "HIGH", "data_age_ms_m1": 100000, "data_quality_m1": "LOW", "data_age_ms_m5": 200000, "data_quality_m5": "MEDIUM"},
            "m5": {"bias": "BULLISH", "ema5": 1.102, "ema10": 1.098, "ema20": 1.100, "ema50": 1.095, "ema100": 1.090, "ema200": 1.085, "rsi14": 60, "stoch_k": 52, "stoch_d": 50, "macd": 0.0002, "macd_signal": 0.0001, "atr14": 0.0016, "adx": 24, "atr_percentile": 41, "atr_zscore": 0.5, "bb_upper": 1.105, "bb_lower": 1.095, "bb_width": 0.0022, "volume": 1200, "volume_ratio": 1.4, "support": 1.090, "resistance": 1.100, "pivot": 1.102},
            "m1": {"open": 1.100, "ema5": 1.102, "ema20": 1.101, "rsi14": 58, "stoch_k": 51, "stoch_d": 49, "macd": 0.0001, "macd_signal": 0.00005, "volume_ratio": 1.1},
            "m15": {"bias": "BULLISH"},
            "analysis": {"trend_direction": "UP", "trend_type": "IMPULSIVE", "trend_strength": 68, "volatility_regime": "HIGH"},
            "engines": {"trend": {"strength": 74, "confidence": 80}, "strength": {"exhaustion_risk": 22}, "structure": {"bos_detected": False}, "volatility": {"compression_quality": 75}, "mtf": {"alignment_score": 71}},
            "signals": {},
            "decision_layer": {
                "tradeable": False,
                "stability_score": 42,
                "quality_score": 52,
                "risk_level": "MEDIUM",
                "confidence_score": 70,
                "suggested_expiry_minutes": 5,
                "suggested_action": "WAIT",
                "final_reason_th": "NONE",
            },
            "price_action": {
                "pattern": "NONE",
                "last_candle_bias": "BEARISH",
                "body_strength": 0.3,
                "wick_dominance": "LOW",
                "momentum_bias": "DOWN",
                "move_quality": "FAIR",
                "trap_alert": False,
                "sr_interaction": "NONE",
                "volume_momentum": "STABLE",
            },
            "market_context": {"state": "TRENDING", "description": "OTC trend", "volatility_regime": "HIGH", "news_impact": "NONE", "expected_volatility_%": 15},
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
        self.assertEqual(normalized["meta"]["data_age_ms_m1"], "NOT_AVAILABLE")
        self.assertEqual(normalized["meta"]["data_quality_m5"], "NOT_AVAILABLE")


if __name__ == "__main__":
    unittest.main()
