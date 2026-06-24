"""
Orchestrator — Central Analysis Pipeline for FINALBOT

Flow per cycle:
    1. store.calculate_all()                → คำนวณ indicators จาก candles_dict
    2. parallel: run 5 Tier-1 engines       → ด้วย ThreadPoolExecutor (max_workers=5)
        - TrendEngine.analyze(M5)           → trend_data
        - StrengthEngine.analyze(M5)        → strength_data
        - VolatilityEngine.analyze(M5)      → volatility_data
        - StructureEngine.analyze(M15|M5)   → structure_data
        - MTFEngine.analyze(candles_dict)   → mtf_data
    3. MarketStateClassifier.analyze(...)   → จำแนกสภาวะตลาด
    4. trade_logger.build_log_data(...)     → รวบรวม log ส่งต่อ AI Bridge
"""

import logging
import concurrent.futures
import pandas as pd
from typing import Dict, Any, Optional

from core.indicator_store import store
from core.engines.trend_engine import TrendEngine
from core.engines.strength_engine import StrengthEngine
from core.engines.volatility_engine import VolatilityEngine
from core.engines.structure_engine import StructureEngine
from core.engines.mtf_engine import MTFEngine
from core.engines.market_state_classifier import MarketStateClassifier
from core.logging.trade_logger import TradeLogger

logger = logging.getLogger("Orchestrator")


class Orchestrator:
    """
    Coordinates the full analysis pipeline each trading cycle.

    Engines are created once in __init__ and reused across cycles to avoid
    overhead from repeated initialisation.
    """

    def __init__(self, trade_logger: TradeLogger):
        self.trade_logger = trade_logger

        # ── Tier-1 engines (created once, reused every cycle) ────────────
        self.trend_engine = TrendEngine()
        self.strength_engine = StrengthEngine()
        self.volatility_engine = VolatilityEngine()
        self.structure_engine = StructureEngine()
        self.mtf_engine = MTFEngine()

        # ── Tier-2 classifier ────────────────────────────────────────────
        self.classifier: Optional[MarketStateClassifier] = None
        try:
            from core.config_loader import load_settings
            _cfg = load_settings(reload=False).get("thresholds", {})
            self.classifier = MarketStateClassifier(config=_cfg)
            logger.info("MarketStateClassifier initialised")
        except Exception as e:
            logger.error(f"Failed to init MarketStateClassifier: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_cycle(
        self,
        symbol: str,
        candles_dict: Dict[str, pd.DataFrame],
        ai_context: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute one full analysis cycle for *symbol*.

        Parameters
        ----------
        symbol        : trading pair, e.g. "EURUSD-OTC"
        candles_dict  : mapping of timeframe → OHLCV DataFrame
                        expected keys: 'M1', 'M5', 'M15'
        ai_context    : optional upstream AI context object

        Returns
        -------
        log_data dict ready for downstream AI consumption, or None on failure.
        """
        primary_df = candles_dict.get('M5')
        if primary_df is None or primary_df.empty:
            logger.warning(f"No M5 data for {symbol}")
            return None

        # ── Step 1: IndicatorStore ──────────────────────────────────────
        store.calculate_all(symbol, candles_dict)

        # ── Step 2: Run 5 Tier-1 engines in parallel ────────────────────
        trend_data, strength_data, volatility_data, structure_data, mtf_data = \
            self._run_engines_parallel(symbol, candles_dict)

        # ── Step 2.5: Save Engine outputs to SSOT ───────────────────────
        store.set_engine_output(symbol, 'trend', trend_data)
        store.set_engine_output(symbol, 'strength', strength_data)
        store.set_engine_output(symbol, 'volatility', volatility_data)
        store.set_engine_output(symbol, 'structure', structure_data)
        store.set_engine_output(symbol, 'mtf', mtf_data)

        # ── Step 3: Market state classification ─────────────────────────
        payload = store.get_payload(symbol)
        
        market_state = self._classify(
            payload=payload,
            symbol=symbol,
            trend_data=trend_data,
            strength_data=strength_data,
            volatility_data=volatility_data,
            structure_data=structure_data,
            mtf_data=mtf_data,
        )

        # Save Classifier outputs to SSOT
        store.set_classified(symbol, market_state)

        # ── Step 4: Return final payload to Runner ───────────────────────
        # Bypass TradeLogger as requested by user. Return SSOT payload directly.
        final_payload = store.get_payload(symbol)
        final_payload['symbol'] = symbol
        return final_payload
    # ------------------------------------------------------------------
    # Private — parallel engine execution
    # ------------------------------------------------------------------

    def _run_engines_parallel(
        self,
        symbol: str,
        candles_dict: Dict[str, pd.DataFrame],
    ):
        """
        Submit all 5 Tier-1 engines to a ThreadPoolExecutor simultaneously.
        """
        payload = store.get_payload(symbol)
        
        # MTFEngine can still receive candles_dict if needed, but we pass payload to all.
        tasks: Dict[str, tuple] = {
            'trend':      (self.trend_engine.analyze,      (payload,),      {}),
            'strength':   (self.strength_engine.analyze,   (payload,),      {}),
            'volatility': (self.volatility_engine.analyze, (payload,),      {}),
            'structure':  (self.structure_engine.analyze,  (payload,),      {}),
            'mtf':        (self.mtf_engine.analyze,        (payload,),      {'candles_dict': candles_dict}),
        }

        results: Dict[str, Any] = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_label = {
                executor.submit(fn, *args, **kwargs): label
                for label, (fn, args, kwargs) in tasks.items()
            }

            for future in concurrent.futures.as_completed(future_to_label):
                label = future_to_label[future]
                try:
                    results[label] = future.result()
                except Exception as exc:
                    logger.error(f"{label}_engine raised: {exc}")
                    engine_map = {
                        'trend':      self.trend_engine,
                        'strength':   self.strength_engine,
                        'volatility': self.volatility_engine,
                        'structure':  self.structure_engine,
                        'mtf':        self.mtf_engine,
                    }
                    results[label] = engine_map[label].get_neutral_state()

        return (
            results.get('trend',      self.trend_engine.get_neutral_state()),
            results.get('strength',   self.strength_engine.get_neutral_state()),
            results.get('volatility', self.volatility_engine.get_neutral_state()),
            results.get('structure',  self.structure_engine.get_neutral_state()),
            results.get('mtf',        self.mtf_engine.get_neutral_state()),
        )

    # ------------------------------------------------------------------
    # Private — classification
    # ------------------------------------------------------------------

    def _classify(
        self,
        payload: dict,
        symbol: str,
        trend_data: dict,
        strength_data: dict,
        volatility_data: dict,
        structure_data: dict,
        mtf_data: dict,
    ) -> Dict[str, Any]:
        """
        Call MarketStateClassifier and normalise the result into market_state dict.
        All keys are guaranteed — no KeyError downstream.
        """
        # Fallback uses real engine data (not hardcoded)
        market_state: Dict[str, Any] = {
            'state':               'UNKNOWN',
            'confidence':          0,
            'quality_score':       0,
            'tradeable':           False,
            'stability':           0,
            'description':         '',
            'trend_direction':     trend_data.get('direction', 'NONE'),
            'trend_strength':      trend_data.get('strength', 0),
            'trend_type':          trend_data.get('type', 'CHOPPY'),
            'atr_percentile':      volatility_data.get('atr_percentile', 50),
            'volatility_label':    volatility_data.get('regime', 'NORMAL').lower(),
            'compression_quality': volatility_data.get('compression_quality', 0.0),
            'regime':              'ranging',
            'patterns':            [],
        }

        if self.classifier is None:
            return market_state

        try:
            result = self.classifier.analyze(
                payload,
                trend_data=trend_data,
                strength_data=strength_data,
                volatility_data=volatility_data,
                structure_data=structure_data,
                mtf_data=mtf_data,
                symbol=symbol,
            )

            if isinstance(result, dict):
                metrics = result.get('metrics', {})
                trend_dir = metrics.get('trend_direction', trend_data.get('direction', 'NONE'))
                regime = 'ranging' if trend_dir == 'NONE' else 'trending'
                comp_quality = volatility_data.get(
                    'compression_quality',
                    100.0 if metrics.get('compression_detected') else 0.0,
                )

                market_state.update({
                    'state':               result.get('state', 'UNKNOWN'),
                    'confidence':          result.get('confidence', 0),
                    'quality_score':       result.get('quality_score', 0),
                    'tradeable':           result.get('tradeable', False),
                    'stability':           result.get('stability', 0),
                    'description':         result.get('description', ''),
                    'trend_direction':     trend_dir,
                    'trend_strength':      metrics.get('trend_strength', trend_data.get('strength', 0)),
                    'trend_type':          trend_data.get('type', 'CHOPPY'),
                    'atr_percentile':      metrics.get('atr_percentile', volatility_data.get('atr_percentile', 50)),
                    'volatility_label':    metrics.get('volatility_regime', volatility_data.get('regime', 'NORMAL')).lower(),
                    'compression_quality': comp_quality,
                    'regime':              regime,
                    'patterns':            result.get('patterns', []),
                })

        except Exception as e:
            logger.error(f"MarketStateClassifier error for {symbol}: {e}")

        return market_state
