"""
Orchestrator — Central Analysis Pipeline for FINALBOT

Flow per cycle:
    0. Handle OTC Volume (force 1.0)
    1. indicator_store.py -> Basic Indicators
    2. advanced_tools_manager.py -> Advanced Tools
    3. Run 5 Tier-1 engines in parallel
    4. market_state_classifier.py -> Classify state
    5. Save raw OHLCV to CSV
    6. Return full payload
"""

import logging
import concurrent.futures
import pandas as pd
import numpy as np
import os
import csv
import json
import yaml
import traceback
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from data_evaluate.orchestration.indicator_store.indicator_store import store
from data_evaluate.orchestration.advanced_tools.advanced_tools_manager import AdvancedToolsManager
from data_feed.csv_writer import read_csv_safe

from data_evaluate.models.market_context import MarketContext

# Import 5 Engines and Classifier
from data_evaluate.orchestration.market_classifier.trend_engine import TrendEngine
from data_evaluate.orchestration.market_classifier.strength_engine import StrengthEngine
from data_evaluate.orchestration.market_classifier.volatility_engine import VolatilityEngine
from data_evaluate.orchestration.market_classifier.structure_engine import StructureEngine
from data_evaluate.orchestration.market_classifier.mtf_engine import MTFEngine
from data_evaluate.orchestration.market_classifier.market_state_classifier import MarketStateClassifier
from data_evaluate.orchestration.check_news import check_news_impact

# Import 10 Supplementary Engines
from data_evaluate.orchestration.anomaly_detector import AnomalyDetector
from data_evaluate.orchestration.explainability_engine import ExplainabilityEngine
from data_evaluate.orchestration.liquidity_engine import LiquidityEngine
from data_evaluate.orchestration.noise_detector import NoiseDetector
from data_evaluate.orchestration.probability_estimator import ProbabilityEstimator
from data_evaluate.orchestration.signal_throttle import SignalThrottle
from data_evaluate.orchestration.context_synthesizer import ContextSynthesizer

from data_evaluate.orchestration.market_classifier.market_structure_engine import MarketStructureEngine
from data_evaluate.orchestration.market_classifier.market_pressure_analyzer import MarketPressureAnalyzer

logger = logging.getLogger("Orchestrator")


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy data types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return super(NumpyEncoder, self).default(obj)


class Orchestrator:
    def __init__(self, trade_logger=None):
        self.trade_logger = trade_logger
        self.advanced_tools = AdvancedToolsManager()
        
        # ── Tier-1 engines ────────────
        self.trend_engine = TrendEngine()
        self.strength_engine = StrengthEngine()
        self.volatility_engine = VolatilityEngine()
        self.structure_engine = StructureEngine()
        self.mtf_engine = MTFEngine()

        # ── 10 Supplementary Modules ──────────────────────────────────────
        self.anomaly_detector = AnomalyDetector()
        self.explainability_engine = ExplainabilityEngine()
        self.liquidity_engine = LiquidityEngine()
        self.noise_detector = NoiseDetector()
        self.probability_estimator = ProbabilityEstimator()
        self.signal_throttle = SignalThrottle()
        self.context_synthesizer = ContextSynthesizer()
        self.market_structure_engine = MarketStructureEngine()
        self.market_pressure_analyzer = MarketPressureAnalyzer()

        # ── Tier-2 classifier ────────────────────────────────────────────
        self.classifier: Optional[MarketStateClassifier] = None
        try:
            from config_setting.config_loader import load_settings
            _cfg = load_settings(reload=False)["thresholds"]
            self.classifier = MarketStateClassifier(config=_cfg)
            logger.info("MarketStateClassifier initialised")
        except Exception as e:
            raise

        self.csv_dir = os.path.join("all_filelogs", "all_process")
        os.makedirs(self.csv_dir, exist_ok=True)

        self.json_dir = os.path.join("all_filelogs", "json_process")
        os.makedirs(self.json_dir, exist_ok=True)

        self.ai_log_dir = os.path.join("all_filelogs", "logs_ai")
        os.makedirs(self.ai_log_dir, exist_ok=True)

        self.orchestrator_log_dir = os.path.join("all_filelogs", "logs_orchestrator")
        os.makedirs(self.orchestrator_log_dir, exist_ok=True)

        self.ai_memory = []
        self.last_payload = None

    def update_ai_memory(self, symbol: str, action: str, reason: str):
        self.ai_memory.append({
            'symbol': symbol,
            'action': action,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        })
        if len(self.ai_memory) > 5:
            self.ai_memory.pop(0)

    def process_cycle(
        self,
        symbol: str,
        ai_context: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        
        import pandas as pd
        candles_dict = {}

        # Path under Rule 7
        base_iq_dir = os.path.join("data_base", "csv", "iq_option")

        # Handle symbol name variations (EURUSD-OTC vs EURUSD_OTC)
        symbol_hyphenated = symbol.replace('_', '-')
        symbol_underscored = symbol.replace('-', '_')

        symbol_dir = os.path.join(base_iq_dir, symbol)
        if not os.path.exists(symbol_dir):
            symbol_dir = os.path.join(base_iq_dir, symbol_hyphenated)
            if not os.path.exists(symbol_dir):
                symbol_dir = os.path.join(base_iq_dir, symbol_underscored)

        for tf in ["M1", "M5", "M15"]:
            possible_paths = [
                os.path.join(symbol_dir, f"{symbol}_{tf}.csv"),
                os.path.join(symbol_dir, f"{symbol_hyphenated}_{tf}.csv"),
                os.path.join(symbol_dir, f"{symbol_underscored}_{tf}.csv"),
            ]
            csv_path = next((p for p in possible_paths if os.path.exists(p)), possible_paths[0])

            if not os.path.exists(csv_path):
                logger.warning(f"No {tf} CSV for {symbol} at {csv_path}")
                raise ValueError(f"No {tf} data for {symbol}")
            try:
                df = read_csv_safe(csv_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                df = df[~df.index.duplicated(keep='last')]
                candles_dict[tf] = df
            except Exception as e:
                logger.exception(f"Failed to read {csv_path}")
                raise
                
        # Warm-up Candle Lookback Check (Fail-Fast)
        min_required_candles = {
            'M1': 100,
            'M5': 250,
            'M15': 50
        }
        for tf, min_req in min_required_candles.items():
            df_tf = candles_dict.get(tf)
            if df_tf is None or len(df_tf) < min_req:
                raise ValueError(f"FAIL-FAST: Insufficient {tf} warm-up candles (minimum {min_req} required)")

        final_payload = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }
        
        # ── 0.1 Timeframe Synchronization (REMOVED) ───────────────────────
        # Note: Timeframe sync is strictly prohibited in Part 2 per specs.
        # Data from M1, M5, M15 must remain independent.


        # ── 0. Handle OTC Volume ────────────────────────────────────────
        is_otc = "OTC" in symbol.upper()
        if is_otc:
            candles_dict = {k: v.copy() for k, v in candles_dict.items()}
            for tf in ['M1', 'M5', 'M15']:
                if tf in candles_dict and not candles_dict[tf].empty:
                    # Modify in place safely
                    candles_dict[tf].loc[:, 'volume'] = 1.0

        # ── 1. Save OHLCV CSV ───────────────────────────────────────────
        # ย้ายไปเซฟตอนจบ process_cycle เพื่อให้ได้ข้อมูลครบทุกตัว

        # ── 2. Basic Indicators (indicator_store.py) ────────────────────
        try:
            store.calculate_all(symbol, candles_dict, forming_data=None)
            basic_payload = store.get_payload(symbol)
            final_payload.update(basic_payload) # merge m1, m5, ohlcv
        except Exception as e:
            raise

        # ── 3. Advanced Tools ───────────────────────────────────────────
        try:
            df_m5 = candles_dict['M5']
            if isinstance(df_m5, pd.DataFrame) and not df_m5.empty:
                advanced_data = self.advanced_tools.analyze_all(symbol, basic_payload, df_m5)
                final_payload.update(advanced_data)
                
        except Exception as e:
            raise

        # ── 4. 5 Engines in parallel ────────────────────────────────────
        try:
            # Zero Tolerance validation before running engines
            if not candles_dict:
                raise ValueError("FAIL-FAST: Missing candles_dict for engine execution")
            for tf in ['M1', 'M5', 'M15']:
                if tf not in candles_dict or candles_dict[tf] is None or candles_dict[tf].empty:
                    raise ValueError(f"FAIL-FAST: Invalid {tf} data in candles_dict")
                if len(candles_dict[tf]) < 50:
                    raise ValueError(f"FAIL-FAST: Insufficient {tf} candles (minimum 50 required)")
            
            # Validate basic payload structure
            required_payload_fields = ['m5', 'm1', 'ohlcv', 'price_action']
            for field in required_payload_fields:
                if field not in final_payload or final_payload[field] is None:
                    raise ValueError(f"FAIL-FAST: Missing required payload field: {field}")
            
            trend_data, strength_data, volatility_data, structure_data, mtf_data = \
                self._run_engines_parallel(symbol, final_payload, candles_dict)
                
            final_payload['analysis'] = {
                'trend_direction': trend_data['direction'],
                'trend_strength': trend_data['strength'],
                'trend_type': trend_data['type'],
                'volatility_regime': volatility_data['regime']
            }
            final_payload['engines'] = {
                'trend': trend_data,
                'strength': strength_data,
                'volatility': volatility_data,
                'structure': structure_data,
                'mtf': mtf_data
            }
        except Exception as e:
            raise

        # ── 5. Market State Classifier ──────────────────────────────────
        state_data = None
        try:
            if not self.classifier:
                raise ValueError("FAIL-FAST: MarketStateClassifier not initialized")
                
            # Zero Tolerance validation before classification
            if not isinstance(final_payload, dict):
                raise ValueError("FAIL-FAST: final_payload must be a dictionary")
            if not trend_data or not strength_data or not volatility_data or not structure_data or not mtf_data:
                raise ValueError("FAIL-FAST: Missing engine data for classification")
            if not candles_dict:
                raise ValueError("FAIL-FAST: Missing candles_dict for classification")
                
            state_data = self.classifier.analyze(
                payload=final_payload,
                symbol=symbol,
                trend_data=trend_data,
                strength_data=strength_data,
                volatility_data=volatility_data,
                structure_data=structure_data,
                mtf_data=mtf_data,
                candles_dict=candles_dict
            )
            
            # Validate state_data structure
            if not isinstance(state_data, dict):
                raise ValueError("FAIL-FAST: MarketStateClassifier returned non-dict")
            if 'state' not in state_data or state_data['state'] is None:
                raise ValueError("FAIL-FAST: MarketStateClassifier missing required field: state")
                
            final_payload['market_state'] = state_data['state']
            final_payload['market_state_full'] = state_data
        except Exception as e:
            raise

        # ── 5.05 10 Supplementary Engines Execution ─────────────────────
        try:
            supp_engines = self._run_supplementary_engines(
                symbol=symbol,
                payload=final_payload,
                candles_dict=candles_dict,
                trend_data=trend_data,
                strength_data=strength_data,
                volatility_data=volatility_data,
                structure_data=structure_data,
                mtf_data=mtf_data,
                state_data=state_data
            )
            final_payload['supplementary_engines'] = supp_engines
        except Exception as e:
            logger.exception(f"Error running supplementary engines for {symbol}: {e}")
            traceback.print_exc()
            raise

        # ── 5.1 Append Group B specific fields ──────────────────────────
        try:
            m5_data = final_payload['m5']
            atr = m5_data['atr14']
            close_price = final_payload['meta']['close']
            try:
                import math
                if isinstance(close_price, (int, float)) and close_price > 0 and not math.isnan(close_price):
                    expected_vol = round((atr / close_price) * 100, 3)
                else:
                    raise ValueError("Failed to calculate expected_vol: close_price invalid")
            except (ZeroDivisionError, ValueError, TypeError) as e:
                raise ValueError("Failed to calculate expected_vol") from e

            m1_data = final_payload['m1']
            vol_ratio = m1_data['volume_ratio']
            news_impact = check_news_impact(symbol)

            if is_otc:
                # OTC pairs do not have reliable news and volume from the regular market calendar.
                # We preserve the structural fields but mark them explicitly and use neutral values so
                # downstream AI, strategy, and classifier logic can treat OTC as "not applicable" without
                # introducing a zero-bias or misleading numeric signal.
                news_impact = 'NONE_OTC'
                if 'm5' in final_payload and isinstance(final_payload['m5'], dict):
                    final_payload['m5']['volume'] = 1.0
                    final_payload['m5']['volume_ratio'] = 1.0
                    final_payload['m5']['volume_trend'] = 'NO_VOLUME_DATA'
                if 'm1' in final_payload and isinstance(final_payload['m1'], dict):
                    final_payload['m1']['volume'] = 1.0
                    final_payload['m1']['volume_ratio'] = 1.0

            final_payload['market_context'] = {
                'state': final_payload['market_state'],
                'description': state_data['description'] if state_data else 'NONE',
                'breakout_prob': state_data.get('breakout_prob', 0) if state_data else 0,
                'reversal_prob': state_data.get('reversal_prob', 0) if state_data else 0,
                'volatility_regime': final_payload['analysis']['volatility_regime'],
                'news_impact': news_impact,
                'expected_volatility_%': expected_vol,
                'recent_ai_memory': list(self.ai_memory)
            }

            final_payload['decision_layer'] = {
                'tradeable': state_data['tradeable'] if state_data else True,
                'stability_score': state_data['metrics']['alignment_score'] if state_data else 50,
                'quality_score': state_data['quality_score'] if state_data else 50,
                'risk_level': state_data['risk_level'] if state_data else 'MEDIUM',
                'confidence_score': "รอการวิเคราะห์จาก AI",
                'suggested_expiry_minutes': "รอการวิเคราะห์จาก AI",
                'suggested_action': "รอการวิเคราะห์จาก AI",
                'final_reason_th': "รอการวิเคราะห์จาก AI"
            }
        except Exception as e:
            raise

        # ── 5.5 Deduplicate Payload ──────────────────────────────────────
        try:
            final_payload = self._deduplicate_payload(final_payload)
        except Exception as e:
            raise

        # ── 6. Save Full Payload to CSV ─────────────────────────────────
        # Skip CSV save - only save TXT as requested
        # try:
        #     self._save_full_csv(symbol, final_payload, candles_dict['M1'])
        # except Exception as e:
        #     raise

        # ── 7. Format Payload ───────────────────────────────────────────
        try:
            formatted_payload = self._format_payload(final_payload)

            # Skip JSON save - only save TXT as requested
            # try:
            #     self._save_formatted_json(symbol, formatted_payload)
            # except Exception as e:
            #     raise

            try:
                txt_filepath = self._save_txt_payload(symbol, formatted_payload)
            except Exception as e:
                logger.exception(f"Orchestrator failed to save txt payload for {symbol}: {e}")
                raise
                
            self.last_payload = formatted_payload
            store.clear_symbol(symbol)  # Clean up memory leak
            return formatted_payload
        except Exception as e:
            raise

    def _format_payload(self, p: dict) -> dict:
        """
        Build a structured payload from the data already produced by the indicator store,
        advanced tools, and market classification engines.
        No fallbacks — if a required field is missing, raise immediately.
        This new version reorganizes the output for better readability in the TXT log,
        grouping core analytical fields at the top.
        """
        is_otc = 'OTC' in str(p.get('symbol', '')).upper()

        def _req(d: dict, *keys):
            curr = d
            for k in keys:
                if not isinstance(curr, dict) or k not in curr:
                    raise ValueError(f"Required field missing: {' -> '.join(str(x) for x in keys)}")
                curr = curr[k]
            if curr is None:
                raise ValueError(f"Required field is None: {' -> '.join(str(x) for x in keys)}")
            return curr

        m5   = _req(p, 'm5')
        m1   = _req(p, 'm1')
        meta = _req(p, 'meta')
        pa   = _req(p, 'price_action')
        eng  = _req(p, 'engines')
        dl   = _req(p, 'decision_layer')
        mc   = _req(p, 'market_context')
        
        # ─── CORE ANALYSIS (74 Fields) ───────────────────────────────────
        core_analysis = {
            # --- Market Context & State (5 fields) ---
            'state': _req(mc, 'state'),
            'description': _req(mc, 'description'),
            'volatility_regime': _req(p, 'analysis', 'volatility_regime'),
            'news_impact': 'NONE_OTC' if is_otc else _req(mc, 'news_impact'),
            'expected_volatility_%': _req(mc, 'expected_volatility_%'),
            
            # --- M5 Indicators (18 fields) ---
            'm5_bias': _req(m5, 'bias'),
            'm5_ema5': _req(m5, 'ema5'),
            'm5_ema10': _req(m5, 'ema10'),
            'm5_ema20': _req(m5, 'ema20'),
            'm5_ema50': _req(m5, 'ema50'),
            'm5_bb_upper': _req(m5, 'bb_upper'),
            'm5_bb_lower': _req(m5, 'bb_lower'),
            'm5_bb_width': _req(m5, 'bb_width'),
            'm5_rsi': _req(m5, 'rsi14'),
            'm5_stoch_k': _req(m5, 'stoch_k'),
            'm5_stoch_d': _req(m5, 'stoch_d'),
            'm5_macd': _req(m5, 'macd'),
            'm5_macd_signal': _req(m5, 'macd_signal'),
            'm5_adx': _req(m5, 'adx'),
            'm5_atr': _req(m5, 'atr14'),
            'm5_support': _req(m5, 'support'),
            'm5_resistance': _req(m5, 'resistance'),
            'm5_pivot': _req(m5, 'pivot'),
            
            # --- M1 Indicators (8 fields) ---
            'm1_last_candle': 'BULLISH' if _req(meta, 'close') > (_req(m1, 'open') if 'open' in m1 else _req(meta, 'open')) else 'BEARISH',
            'm1_ema5': _req(m1, 'ema5'),
            'm1_ema20': _req(m1, 'ema20'),
            'm1_rsi': _req(m1, 'rsi14'),
            'm1_stoch_k': _req(m1, 'stoch_k'),
            'm1_stoch_d': _req(m1, 'stoch_d'),
            'm1_macd': _req(m1, 'macd'),
            'm1_macd_signal': _req(m1, 'macd_signal'),
            
            # --- M15 Indicators (1 field) ---
            'm15_bias': _req(p, 'm15', 'bias'),
            
            # --- Advanced Tools (Price Action & Volume) (11 fields) ---
            'pa_pattern': _req(pa, 'pattern'),
            'pa_last_candle_bias': _req(pa, 'last_candle_bias'),
            'pa_body_strength': _req(pa, 'body_strength'),
            'pa_wick_dominance': _req(pa, 'wick_dominance'),
            'pa_momentum_bias': _req(pa, 'momentum_bias'),
            'pa_move_quality': _req(pa, 'move_quality'),
            'pa_trap_alert': _req(pa, 'trap_alert'),
            'pa_sr_interaction': _req(pa, 'sr_interaction'),
            'vol_tick_volume': 1.0 if is_otc else _req(m5, 'volume'),
            'vol_momentum': 'NO_VOLUME_DATA' if is_otc else _req(pa, 'volume_momentum'),
            'vol_vs_average': 1.0 if is_otc else _req(m5, 'volume_ratio'),

            # --- Tier-1 Engine Analysis (15 fields) ---
            'eng_trend_direction': _req(eng, 'trend', 'direction'),
            'eng_trend_strength': _req(eng, 'trend', 'strength'),
            'eng_trend_type': _req(eng, 'trend', 'type'),
            'eng_strength_momentum_bias': _req(eng, 'strength', 'momentum_level'),
            'eng_strength_momentum_strength': _req(eng, 'strength', 'strength_score'),
            'eng_strength_exhaustion_risk': _req(eng, 'strength', 'exhaustion_risk'),
            'eng_volatility_regime': _req(eng, 'volatility', 'regime'),
            'eng_volatility_compression_detected': _req(eng, 'volatility', 'spike_detected'),
            'eng_volatility_compression_quality': _req(eng, 'volatility', 'compression_quality'),
            'eng_volatility_score': _req(eng, 'volatility', 'volatility_score'),
            'eng_structure_type': _req(eng, 'structure', 'structure_type'),
            'eng_structure_bos_detected': _req(eng, 'structure', 'bos_detected'),
            'eng_mtf_alignment_score': _req(eng, 'mtf', 'alignment_score'),
            'eng_mtf_htf_direction': _req(eng, 'mtf', 'htf_direction'),

            # --- Decision Layer (8 fields) ---
            'dl_tradeable': _req(dl, 'tradeable'),
            'dl_stability_score': _req(dl, 'stability_score'),
            'dl_quality_score': _req(dl, 'quality_score'),
            'dl_risk_level': _req(dl, 'risk_level'),
            'dl_confidence_score': _req(dl, 'confidence_score'),
            'dl_suggested_expiry_minutes': _req(dl, 'suggested_expiry_minutes'),
            'dl_suggested_action': _req(dl, 'suggested_action'),
            'dl_final_reason_th': _req(dl, 'final_reason_th'),
        }

        # ─── SUPPLEMENTARY DATA (Remaining Fields) ───────────────────────
        def _derive_session():
            now_utc = datetime.now(timezone.utc)
            h = now_utc.hour
            if 0 <= h < 7:   return "SYDNEY/TOKYO"
            elif 7 <= h < 12: return "LONDON_OPEN"
            elif 12 <= h < 16: return "NY/LONDON_OVERLAP"
            elif 16 <= h < 21: return "NY_AFTERNOON"
            else:             return "SYDNEY_OPEN"

        supplementary_data = {
            'meta': {
                'timestamp': p.get('timestamp', datetime.now().isoformat()),
                'symbol': _req(p, 'symbol'),
                'session': meta.get('session') or _derive_session(),
                'm1_open': _req(meta, 'm1_open'),
                'm1_age': _req(meta, 'm1_age'),
                'm1_quality': _req(meta, 'm1_quality'),
                'm5_open': _req(meta, 'm5_open'),
                'm5_age': _req(meta, 'm5_age'),
                'm5_quality': _req(meta, 'm5_quality'),
            },
            'ohlcv': {
                'm1': { 'open': _req(m1, 'open'), 'high': _req(m1, 'high'), 'low': _req(m1, 'low'), 'close': _req(m1, 'close'), 'volume': 'NONE_OTC' if is_otc else _req(m1, 'volume') },
                'm5': { 'open': _req(m5, 'open'), 'high': _req(m5, 'high'), 'low': _req(m5, 'low'), 'close': _req(m5, 'close'), 'volume': 'NONE_OTC' if is_otc else _req(m5, 'volume') },
            },
            'full_engine_output': _req(p, 'engines'),
            'full_market_state': _req(p, 'market_state_full'),
            'supplementary_engines': p.get('supplementary_engines', {}),
            'recent_ai_memory': list(self.ai_memory),
        }

        # --- Final Assembly ---
        return {
            'core_analysis': core_analysis,
            'supplementary_data': supplementary_data,
        }

    def _run_engines_parallel(self, symbol: str, payload: dict, candles_dict: dict):
        import copy
        safe_payload = copy.deepcopy(payload)
        tasks: Dict[str, tuple] = {
            'trend':      (self.trend_engine.analyze,      (safe_payload,),      {'candles_dict': candles_dict}),
            'strength':   (self.strength_engine.analyze,   (safe_payload,),      {'candles_dict': candles_dict}),
            'volatility': (self.volatility_engine.analyze, (safe_payload,),      {'candles_dict': candles_dict}),
            'structure':  (self.structure_engine.analyze,  (safe_payload,),      {'candles_dict': candles_dict}),
            'mtf':        (self.mtf_engine.analyze,        (safe_payload,),      {'candles_dict': candles_dict})
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
                    raise

        # Zero Tolerance: Validate all engine results
        if len(results) < 5:
            missing = set(['trend', 'strength', 'volatility', 'structure', 'mtf']) - set(results.keys())
            raise ValueError(f"FAIL-FAST: {len(missing)} engines failed to produce results: {missing}")
            
        # Validate each engine result structure
        required_engine_fields = {
            'trend': ['direction', 'strength', 'slope', 'momentum', 'type', 'confidence'],
            'strength': ['adx', 'di_plus', 'di_minus', 'rsi', 'momentum_level', 'strength_score', 'exhaustion_risk'],
            'volatility': ['regime', 'spike_detected', 'compression_quality', 'volatility_score'],
            'structure': ['structure_type', 'bos_detected', 'support_levels', 'resistance_levels'],
            'mtf': ['alignment_score', 'htf_direction']
        }
        
        for engine_name, result in results.items():
            if result is None:
                raise ValueError(f"FAIL-FAST: {engine_name} returned None")
            if not isinstance(result, dict):
                raise ValueError(f"FAIL-FAST: {engine_name} returned non-dict: {type(result)}")
                
            required_fields = required_engine_fields[engine_name]
            for field in required_fields:
                if field not in result or result[field] is None:
                    raise ValueError(f"FAIL-FAST: {engine_name} missing required field: {field}")
                    
        return (
            results['trend'],
            results['strength'],
            results['volatility'],
            results['structure'],
            results['mtf'],
        )

    def _run_supplementary_engines(
        self,
        symbol: str,
        payload: Dict[str, Any],
        candles_dict: Dict[str, pd.DataFrame],
        trend_data: Dict[str, Any],
        strength_data: Dict[str, Any],
        volatility_data: Dict[str, Any],
        structure_data: Dict[str, Any],
        mtf_data: Dict[str, Any],
        state_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Executes 10 supplementary engines in strict compliance with AGENTS.md.
        No silent failures, strict type checking, and defensive validation.
        """
        if not isinstance(candles_dict, dict) or 'M5' not in candles_dict:
            raise ValueError("[SupplementaryEngines] FAIL-FAST: candles_dict missing 'M5'")

        df_m5 = candles_dict['M5']
        if not isinstance(df_m5, pd.DataFrame) or df_m5.empty:
            raise ValueError("[SupplementaryEngines] FAIL-FAST: df_m5 is not a valid non-empty DataFrame")

        # 1. Execute 6 DataFrame-based engines
        try:
            ms_res = self.market_structure_engine.analyze(df_m5)
            if not isinstance(ms_res, dict):
                raise ValueError("[MarketStructureEngine] returned non-dict result")
        except Exception as e:
            logger.exception(f"[MarketStructureEngine] Error during analysis: {e}")
            traceback.print_exc()
            raise

        try:
            mp_res = self.market_pressure_analyzer.analyze(df_m5)
            if not isinstance(mp_res, dict):
                raise ValueError("[MarketPressureAnalyzer] returned non-dict result")
        except Exception as e:
            logger.exception(f"[MarketPressureAnalyzer] Error during analysis: {e}")
            traceback.print_exc()
            raise

        try:
            if state_data and 'metrics' in state_data:
                m = state_data['metrics']
                overall = m.get('regime_quality_score', 50)
                rq_res = {
                    'consistency_score': m.get('consistency_score', 50),
                    'cleanliness_score': m.get('cleanliness_score', 50),
                    'directionality_score': m.get('directionality_score', 50),
                    'overall_quality': overall,
                    'is_tradeable_regime': overall >= 60,
                    'confidence': min(100, overall + 10)
                }
            else:
                rq_res = {}
        except Exception as e:
            logger.exception(f"[RegimeQualityScorer] Error mapping from state_data: {e}")
            traceback.print_exc()
            raise

        try:
            liq_res = self.liquidity_engine.analyze(df_m5)
            if not isinstance(liq_res, dict):
                raise ValueError("[LiquidityEngine] returned non-dict result")
        except Exception as e:
            logger.exception(f"[LiquidityEngine] Error during analysis: {e}")
            traceback.print_exc()
            raise

        try:
            noise_res = self.noise_detector.analyze(df_m5)
            if not isinstance(noise_res, dict):
                raise ValueError("[NoiseDetector] returned non-dict result")
        except Exception as e:
            logger.exception(f"[NoiseDetector] Error during analysis: {e}")
            traceback.print_exc()
            raise

        try:
            anom_res = self.anomaly_detector.analyze(df_m5)
            if not isinstance(anom_res, dict):
                raise ValueError("[AnomalyDetector] returned non-dict result")
        except Exception as e:
            logger.exception(f"[AnomalyDetector] Error during analysis: {e}")
            traceback.print_exc()
            raise

        # 2. Build MarketContext for synthesis engines
        try:
            ctx = MarketContext.build_from_candles(symbol, candles_dict, timeframe="M5")
            ctx.trend = trend_data
            ctx.strength = strength_data
            ctx.volatility = volatility_data
            ctx.structure = structure_data
            ctx.market_structure = ms_res
            ctx.mtf = mtf_data
            ctx.market_state = state_data.get('state', 'UNKNOWN') if isinstance(state_data, dict) else str(state_data)
            ctx.regime_quality = rq_res
            ctx.orderflow = mp_res
            ctx.anomaly = anom_res
            ctx.liquidity = liq_res
            ctx.noise = noise_res
            ctx.price_action = payload.get('price_action', {})

            # Set default dicts for safety if not populated
            if not ctx.continuation: ctx.continuation = {'continuation_probability': 50, 'bias': 'NONE'}
            if not ctx.divergence: ctx.divergence = {'divergence_detected': False, 'divergence_type': 'NONE', 'divergence_strength': 0}
            if not ctx.candle_patterns: ctx.candle_patterns = {'bias': 'NONE', 'pattern_strength': 0}
            if not ctx.conflict: ctx.conflict = {'ema_direction': 'NONE', 'conflict_score': 0}
            if not ctx.efficiency: ctx.efficiency = {'overall_efficiency': 50}
            if not ctx.traps: ctx.traps = {'trap_detected': False, 'trap_type': 'NONE'}
            if not ctx.transition: ctx.transition = {'in_transition': False, 'transition_type': 'NONE'}
            if not ctx.signal_quality: ctx.signal_quality = {'quality_score': 50, 'grade': 'C', 'confirmation_score': 50}
            if not ctx.confidence_framework: ctx.confidence_framework = {'confidence_tier': 'MEDIUM', 'final_confidence': 50}
        except Exception as e:
            logger.exception(f"[MarketContext] Failed to build context for synthesis: {e}")
            traceback.print_exc()
            raise

        # 3. Execute 3 context-based synthesis engines
        try:
            syn_res = self.context_synthesizer.analyze(context=ctx)
            if not isinstance(syn_res, dict):
                raise ValueError("[ContextSynthesizer] returned non-dict result")
            ctx.synthesized_context = syn_res
        except Exception as e:
            logger.exception(f"[ContextSynthesizer] Error during analysis: {e}")
            traceback.print_exc()
            raise

        try:
            prob_res = self.probability_estimator.analyze(context=ctx)
            if not isinstance(prob_res, dict):
                raise ValueError("[ProbabilityEstimator] returned non-dict result")
            ctx.move_probability = prob_res
        except Exception as e:
            logger.exception(f"[ProbabilityEstimator] Error during analysis: {e}")
            traceback.print_exc()
            raise

        try:
            exp_res = self.explainability_engine.analyze(context=ctx)
            if not isinstance(exp_res, dict):
                raise ValueError("[ExplainabilityEngine] returned non-dict result")
            ctx.explainability = exp_res
        except Exception as e:
            logger.exception(f"[ExplainabilityEngine] Error during analysis: {e}")
            traceback.print_exc()
            raise

        # 4. Check SignalThrottle
        try:
            action = payload.get('decision_layer', {}).get('suggested_action', 'WAIT')
            allowed, reason = self.signal_throttle.allow(symbol, action)
            throttle_res = {
                'allowed': bool(allowed),
                'reason': str(reason),
                'status': self.signal_throttle.get_status()
            }
        except Exception as e:
            logger.exception(f"[SignalThrottle] Error during throttle check: {e}")
            traceback.print_exc()
            raise

        return {
            'anomaly_detector': anom_res,
            'explainability_engine': exp_res,
            'liquidity_engine': liq_res,
            'noise_detector': noise_res,
            'probability_estimator': prob_res,
            'signal_throttle': throttle_res,
            'context_synthesizer': syn_res,
            'market_structure_engine': ms_res,
            'market_pressure_analyzer': mp_res,
            'regime_quality_scorer': rq_res,
        }

    def _log_red(self, msg: str):
        logger.error(f"[ORCHESTRATOR ERROR] {msg}")

    def _deduplicate_payload(self, p: dict) -> dict:
        """Remove redundant raw values from engines and market_state to shrink payload."""
        if 'engines' in p:
            e = p['engines']
            if 'strength' in e:
                for k in ['adx', 'di_plus', 'di_minus', 'rsi', 'macd', 'roc']:
                    e['strength'].pop(k, None)
            if 'volatility' in e:
                for k in ['atr', 'atr_percentile', 'bbw', 'stddev']:
                    e['volatility'].pop(k, None)
            if 'structure' in e:
                for k in ['support_levels', 'resistance_levels', 'box_duration', 'box_tightness']:
                    e['structure'].pop(k, None)
            if 'trend' in e:
                e['trend'].pop('slope', None)
                
        if 'market_state_full' in p and 'metrics' in p['market_state_full']:
            ms = p['market_state_full']['metrics']
            for k in ['adx', 'rsi', 'atr_percentile', 'bbw', 'trend_direction', 'trend_strength', 
                      'trend_slope', 'trend_type', 'momentum_level', 'strength_score', 
                      'volatility_regime', 'volatility_score', 'structure_type', 'bos_detected',
                      'breakout_prob', 'reversal_prob', 'alignment_score', 'htf_direction']:
                ms.pop(k, None)
                
        return p

    def _flatten_dict(self, d: dict, parent_key: str = '', sep: str = '_') -> dict:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, (list, tuple)):
                items.append((new_key, str(v)))
            elif not isinstance(v, pd.DataFrame):
                items.append((new_key, v))
        return dict(items)

    def _save_full_csv(self, symbol: str, final_payload: dict, df_m1: pd.DataFrame):
        if df_m1 is None or df_m1.empty:
            return
            
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"{symbol.replace('-', '_')}_{date_str}.csv"
        filepath = os.path.join(self.csv_dir, filename)
        
        last_row = df_m1.iloc[-1]
        
        # Flatten the final payload
        flat_payload = self._flatten_dict(final_payload)
        
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:00')
        # We want OHLCV at the front
        row_data = {
            'timestamp': current_timestamp,
            'open': last_row['open'],
            'high': last_row['high'],
            'low': last_row['low'],
            'close': last_row['close'],
            'volume': last_row['volume']
        }
        
        # Add all other data
        for k, v in flat_payload.items():
            if k not in row_data and k != 'timestamp':
                row_data[k] = v
                
        file_exists = os.path.isfile(filepath) and os.path.getsize(filepath) > 0
        
        # Read existing headers if file exists
        existing_headers = []
        if file_exists:
            try:
                # Optimized verification (Rule 5 & 1): Read headers and last line only to prevent I/O bottlenecks
                last_timestamp = None
                with open(filepath, mode='r', newline='', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > 0:
                        existing_headers = list(csv.reader([lines[0]]))[0]
                        if 'timestamp' in existing_headers:
                            ts_index = existing_headers.index('timestamp')
                            if len(lines) > 1:
                                last_row = list(csv.reader([lines[-1]]))[0]
                                if len(last_row) > ts_index:
                                    last_timestamp = last_row[ts_index]
                                    
                if last_timestamp == current_timestamp:
                    # Timestamp already exists, skip writing to prevent duplicate log pollution
                    return
            except Exception as e:
                # Rule 1: No Silent Failures & preserve stack trace
                logger.exception(f"Orchestrator failed to inspect CSV headers or duplicate timestamp: {e}")
                raise
                    
        # If new columns appear, we might miss them in the old file, but we will append using DictWriter
        fieldnames = list(row_data.keys())
        if file_exists:
            # Add any new keys to fieldnames that aren't in existing_headers
            for k in fieldnames:
                if k not in existing_headers:
                    existing_headers.append(k)
            fieldnames = existing_headers
            
        with open(filepath, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            if not file_exists:
                writer.writeheader()
            writer.writerow(row_data)

    def _save_formatted_json(self, symbol: str, formatted_payload: dict):
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"{symbol.replace('-', '_')}_{date_str}.json"
        filepath = os.path.join(self.json_dir, filename)

        with open(filepath, mode='w', encoding='utf-8') as f:
            json.dump(formatted_payload, f, ensure_ascii=False, indent=4, cls=NumpyEncoder)

    def _generate_yaml_text(self, symbol: str, fp: dict) -> str:
        """Generates a YAML string from the formatted payload and aligns colons."""
        try:
            # Clean numpy objects by routing through JSON encoder
            cleaned_fp = json.loads(json.dumps(fp, cls=NumpyEncoder))
            raw_yaml = yaml.dump(cleaned_fp, allow_unicode=True, sort_keys=False, indent=2)
            
            # Align colons for better readability
            lines = raw_yaml.split('\n')
            aligned_lines = []
            for line in lines:
                if ':' in line and not line.strip().endswith(':'):
                    k, v = line.split(':', 1)
                    # Find how many leading spaces the key has
                    leading_spaces = len(k) - len(k.lstrip())
                    # Format key padded to 25 characters (minus leading spaces to keep total width consistent)
                    padded_k = k.ljust(25)
                    aligned_lines.append(f"{padded_k}: {v.strip()}")
                else:
                    aligned_lines.append(line)
                    
            return '\n'.join(aligned_lines)
        except Exception as e:
            raise

    def _format_core_analysis_output(self, formatted_payload: dict, prompt_id: str) -> str:
        core = formatted_payload.get("core_analysis", {})
        supp = formatted_payload.get("supplementary_data", {})
        meta = supp.get("meta", {})
        ohlcv = supp.get("ohlcv", {})
        m1_ohlcv = ohlcv.get("m1", {})
        m5_ohlcv = ohlcv.get("m5", {})

        def _fmt_bool(v):
            if isinstance(v, bool):
                return "true" if v else "false"
            if str(v).lower() in ("true", "false"):
                return str(v).lower()
            return str(v)

        lines = [
            f"ID:{prompt_id}",
            "meta:",
            f"  timestamp: '{meta.get('timestamp', '')}'",
            f"  symbol: {meta.get('symbol', '')}",
            f"  session: {meta.get('session', '')}",
            f"  m1_open: {meta.get('m1_open', '')}",
            f"  m1_age: {meta.get('m1_age', '')}",
            f"  m1_quality: {meta.get('m1_quality', '')}",
            f"  m5_open: {meta.get('m5_open', '')}",
            f"  m5_age: {meta.get('m5_age', '')}",
            f"  m5_quality: {meta.get('m5_quality', '')}",
            "market_context:",
            f"  state: {core.get('state', '')}",
            f"  description: {core.get('description', '')}",
            f"  volatility_regime: {core.get('volatility_regime', '')}",
            f"  news_impact: {core.get('news_impact', '')}",
            f"  expected_volatility_%: {core.get('expected_volatility_%', '')}",
            "timeframes:",
            "  m1:",
            f"    last_candle: {core.get('m1_last_candle', '')}",
            f"    ema5: {core.get('m1_ema5', '')}",
            f"    ema20: {core.get('m1_ema20', '')}",
            f"    rsi: {core.get('m1_rsi', '')}",
            f"    stoch_k: {core.get('m1_stoch_k', '')}",
            f"    stoch_d: {core.get('m1_stoch_d', '')}",
            f"    macd: {core.get('m1_macd', '')}",
            f"    macd_signal: {core.get('m1_macd_signal', '')}",
            "    ohclv:",
            f"      open: {m1_ohlcv.get('open', '')}",
            f"      high: {m1_ohlcv.get('high', '')}",
            f"      low: {m1_ohlcv.get('low', '')}",
            f"      close: {m1_ohlcv.get('close', '')}",
            f"      volume: {m1_ohlcv.get('volume', '')}",
            "  m5:",
            f"    bias: {core.get('m5_bias', '')}",
            f"    ema5: {core.get('m5_ema5', '')}",
            f"    ema10: {core.get('m5_ema10', '')}",
            f"    ema20: {core.get('m5_ema20', '')}",
            f"    ema50: {core.get('m5_ema50', '')}",
            f"    bb_upper: {core.get('m5_bb_upper', '')}",
            f"    bb_lower: {core.get('m5_bb_lower', '')}",
            f"    bb_width: {core.get('m5_bb_width', '')}",
            f"    rsi: {core.get('m5_rsi', '')}",
            f"    stoch_k: {core.get('m5_stoch_k', '')}",
            f"    stoch_d: {core.get('m5_stoch_d', '')}",
            f"    macd: {core.get('m5_macd', '')}",
            f"    macd_signal: {core.get('m5_macd_signal', '')}",
            f"    adx: {core.get('m5_adx', '')}",
            f"    atr: {core.get('m5_atr', '')}",
            f"    support: {core.get('m5_support', '')}",
            f"    resistance: {core.get('m5_resistance', '')}",
            f"    pivot: {core.get('m5_pivot', '')}",
            "    ohclv:",
            f"      open: {m5_ohlcv.get('open', '')}",
            f"      high: {m5_ohlcv.get('high', '')}",
            f"      low: {m5_ohlcv.get('low', '')}",
            f"      close: {m5_ohlcv.get('close', '')}",
            f"      volume: {m5_ohlcv.get('volume', '')}",
            "  m15:",
            f"    bias: {core.get('m15_bias', '')}",
            "price_action:",
            f"  pattern: {core.get('pa_pattern', '')}",
            f"  last_candle_bias: {core.get('pa_last_candle_bias', '')}",
            f"  body_strength: {core.get('pa_body_strength', '')}",
            f"  wick_dominance: {core.get('pa_wick_dominance', '')}",
            f"  momentum_bias: {core.get('pa_momentum_bias', '')}",
            f"  move_quality: {core.get('pa_move_quality', '')}",
            f"  trap_alert: {core.get('pa_trap_alert', '')}",
            f"  sr_interaction: {core.get('pa_sr_interaction', '')}",
            "volume:",
            f"  tick_volume: {core.get('vol_tick_volume', '')}",
            f"  volume_momentum: {core.get('vol_momentum', '')}",
            f"  volume_vs_average: {core.get('vol_vs_average', '')}",
            "analysis:",
            f"  trend_direction: {core.get('eng_trend_direction', '')}",
            f"  trend_type: {core.get('eng_trend_type', '')}",
            f"  trend_strength_score: {core.get('eng_trend_strength', '')}",
            f"  mtf_alignment_%: {core.get('eng_mtf_alignment_score', '')}",
            f"  compression_quality_%: {core.get('eng_volatility_compression_quality', '')}",
            f"  exhaustion_risk_%: {core.get('eng_strength_exhaustion_risk', '')}",
            f"  bos_detected: {_fmt_bool(core.get('eng_structure_bos_detected', ''))}",
            "decision_layer:",
            f"  tradeable: {_fmt_bool(core.get('dl_tradeable', ''))}",
            f"  stability_score: {core.get('dl_stability_score', '')}",
            f"  quality_score: {core.get('dl_quality_score', '')}",
            f"  risk_level: {core.get('dl_risk_level', '')}",
            f"  confidence_score: {core.get('dl_confidence_score', '')}",
            f"  suggested_expiry_minutes: {core.get('dl_suggested_expiry_minutes', '')}",
            f"  suggested_action: {core.get('dl_suggested_action', '')}",
            f"  final_reason_th: {core.get('dl_final_reason_th', '')}",
            ""
        ]
        return "\n".join(lines)

    def _save_txt_payload(self, symbol: str, formatted_payload: dict) -> str:
        meta = formatted_payload.get("supplementary_data", {}).get("meta", {})
        timestamp_str = str(meta.get("timestamp", datetime.now().strftime("%Y-%m-%dT%H:%M:%S")))
        ts_clean = timestamp_str.replace('-', '').replace(':', '').replace('T', '').replace('.', '')[:14]
        time_part = ts_clean[4:14]
        prompt_id = f"{symbol.replace('-', '').replace('_', '')}{time_part}"
        
        formatted_output = self._format_core_analysis_output(formatted_payload, prompt_id)
        
        filename = f"{prompt_id}.txt"
        symbol_dir = os.path.join(self.orchestrator_log_dir, symbol)
        os.makedirs(symbol_dir, exist_ok=True)
        filepath = os.path.join(symbol_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(formatted_output)

        return filepath
