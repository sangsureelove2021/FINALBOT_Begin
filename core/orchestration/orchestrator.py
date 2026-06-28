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
from datetime import datetime

from core.orchestration.indicator_store.indicator_store import store
from core.orchestration.advanced_tools.advanced_tools_manager import AdvancedToolsManager

# Import 5 Engines and Classifier
from core.orchestration.market_classifier.trend_engine import TrendEngine
from core.orchestration.market_classifier.strength_engine import StrengthEngine
from core.orchestration.market_classifier.volatility_engine import VolatilityEngine
from core.orchestration.market_classifier.structure_engine import StructureEngine
from core.orchestration.market_classifier.mtf_engine import MTFEngine
from core.orchestration.market_classifier.market_state_classifier import MarketStateClassifier
from core.orchestration.check_news import check_news_impact

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

        # ── Tier-2 classifier ────────────────────────────────────────────
        self.classifier: Optional[MarketStateClassifier] = None
        try:
            from config.config_loader import load_settings
            _cfg = load_settings(reload=False)["thresholds"]
            self.classifier = MarketStateClassifier(config=_cfg)
            logger.info("MarketStateClassifier initialised")
        except Exception as e:
            raise

        self.csv_dir = os.path.join("logs", "all_process")
        os.makedirs(self.csv_dir, exist_ok=True)

        self.json_dir = os.path.join("logs", "json_process")
        os.makedirs(self.json_dir, exist_ok=True)

        self.ai_log_dir = os.path.join("logs", "logs_ai")
        os.makedirs(self.ai_log_dir, exist_ok=True)

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
        candles_dict: Dict[str, pd.DataFrame],
        ai_context: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        
        primary_df = candles_dict['M5']
        if not isinstance(primary_df, pd.DataFrame) or primary_df.empty:
            logger.warning(f"No M5 data for {symbol}")
            raise ValueError(f"No M5 data for {symbol}")

        final_payload = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }
        
        # ── 0.1 Timeframe Synchronization ────────────────────────────────
        try:
            from core.data.timeframe_sync import TimeframeSync
            sync_engine = TimeframeSync(primary='M5')
            candles_dict = sync_engine.sync(candles_dict)
        except Exception as e:
            raise

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
            store.calculate_all(symbol, candles_dict)
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
            trend_data, strength_data, volatility_data, structure_data, mtf_data = \
                self._run_engines_parallel(symbol, final_payload)
                
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
            if self.classifier:
                state_data = self.classifier.analyze(
                    payload=final_payload,
                    symbol=symbol,
                    trend_data=trend_data,
                    strength_data=strength_data,
                    volatility_data=volatility_data,
                    structure_data=structure_data,
                    mtf_data=mtf_data
                )
                final_payload['market_state'] = state_data['state']
                final_payload['market_state_full'] = state_data
            else:
                final_payload['market_state'] = 'UNCLEAR'
        except Exception as e:
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
                    expected_vol = "ERROR"
            except (ZeroDivisionError, ValueError, TypeError) as e:
                raise Exception("Failed to calculate expected_vol") from e

            final_payload['signals'] = {
                'triggered': [],
                'count': 0,
                'top_signal': 'NO'
            }
            
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
                'volatility_regime': final_payload['analysis']['volatility_regime'],
                'news_impact': news_impact,
                'expected_volatility_%': expected_vol,
                'recent_ai_memory': list(self.ai_memory)
            }

            final_payload['decision_layer'] = {
                'tradeable': state_data['tradeable'] if state_data else True,
                'tradeable_reason': 'Passed basic checks',
                'confidence_score': 0,
                'stability_score': state_data['metrics']['alignment_score'] if state_data else 50,
                'quality_score': 50,
                'risk_level': 'MEDIUM',
                'suggested_expiry_minutes': 5,
                'suggested_action': 'WAIT',
                'final_reason_th': 'รอการวิเคราะห์จาก AI'
            }
        except Exception as e:
            raise

        # ── 5.5 Deduplicate Payload ──────────────────────────────────────
        try:
            final_payload = self._deduplicate_payload(final_payload)
        except Exception as e:
            raise

        # ── 6. Save Full Payload to CSV ─────────────────────────────────
        try:
            self._save_full_csv(symbol, final_payload, candles_dict['M1'])
        except Exception as e:
            raise

        # ── 7. Format Payload ───────────────────────────────────────────
        try:
            formatted_payload = self._format_payload(final_payload)
                
            try:
                self._save_formatted_json(symbol, formatted_payload)
            except Exception as e:
                raise
                
            self.last_payload = formatted_payload
            return formatted_payload
        except Exception as e:
            raise

    def _format_payload(self, p: dict) -> dict:
        """
        Build a structured payload from the data already produced by the indicator store,
        advanced tools, and market classification engines. Missing values are derived from
        the existing metrics rather than replaced by placeholder defaults.
        """
        def _get(d, key_path, default=None):
            if not isinstance(key_path, (list, tuple)):
                key_path = [key_path]
            curr = d
            for k in key_path:
                if isinstance(curr, dict) and k in curr:
                    curr = curr[k]
                else:
                    return default
            return curr if curr is not None else default

        def _get_first_present(d, paths, default=None):
            for path in paths:
                val = _get(d, path, default=None)
                if val is not None and val != "" and val != "NONE":
                    return val
            return default

        def _derive_bias_from_price(close_price, ema20):
            if close_price is None or ema20 is None:
                return "NEUTRAL"
            return "BULLISH" if close_price > ema20 else "BEARISH"

        def _derive_trend_strength_score(analysis, m5, engines):
            score = _get_first_present(analysis, [['trend_strength_score'], ['trend_strength']], None)
            if score is not None:
                return score
            slope = _get_first_present(m5, [['slope_10'], ['slope_20']], 0.0)
            abs_slope = abs(float(slope)) if isinstance(slope, (int, float)) else 0.0
            return int(min(100, max(20, 20 + abs_slope * 100000)))

        def _derive_mtf_alignment(engines):
            val = _get_first_present(engines, [['mtf', 'alignment_score']], None)
            if val is not None:
                return val
            return 50

        def _derive_compression_quality(engines, m5):
            val = _get_first_present(engines, [['volatility', 'compression_quality']], None)
            if val is not None:
                return val
            atr_pct = _get_first_present(m5, [['atr_percentile']], 50)
            bbw = _get_first_present(m5, [['bb_width']], 0.0)
            if isinstance(atr_pct, (int, float)) and isinstance(bbw, (int, float)) and bbw > 0:
                return max(0, min(100, int(100 - (atr_pct * 0.8) - (bbw * 1000))))
            return 50

        def _derive_exhaustion_risk(engines, strength, m5):
            val = _get_first_present(engines, [['strength', 'exhaustion_risk']], None)
            if val is not None:
                return val
            adx = _get_first_present(m5, [['adx']], 0)
            rsi = _get_first_present(m5, [['rsi14']], 50)
            if isinstance(adx, (int, float)) and isinstance(rsi, (int, float)):
                risk = 30 + max(0, adx - 20) * 0.3 + (15 if rsi > 80 or rsi < 20 else 0)
                return int(min(100, max(10, risk)))
            return 30

        def _derive_price_action(p):
            close_price = _get(p, ['meta', 'close'])
            ema20 = _get(p, ['m5', 'ema20'])
            trend_direction = _get_first_present(p, [['analysis', 'trend_direction']], 'NONE')
            m5 = p.get('m5', {}) if isinstance(p.get('m5'), dict) else {}
            support = _get_first_present(m5, [['support']], 0.0)
            resistance = _get_first_present(m5, [['resistance']], 0.0)
            base = {
                'pattern': _get_first_present(p, [['price_action', 'pattern']], 'NONE'),
                'last_candle_bias': _get_first_present(p, [['price_action', 'last_candle_bias']], 'NONE'),
                'body_strength': _get_first_present(p, [['price_action', 'body_strength']], 'NORMAL'),
                'wick_dominance': _get_first_present(p, [['price_action', 'wick_dominance']], 'LOW_WICK'),
                'momentum_bias': _get_first_present(p, [['price_action', 'momentum_bias']], 'NONE'),
                'move_quality': _get_first_present(p, [['price_action', 'move_quality']], 'NORMAL'),
                'trap_alert': _get_first_present(p, [['price_action', 'trap_alert']], 'NONE'),
                'sr_interaction': _get_first_present(p, [['price_action', 'sr_interaction']], 'NONE'),
            }
            if base['pattern'] == 'NONE':
                base['pattern'] = 'CONTINUATION' if trend_direction == 'UP' else 'REVERSAL'
            if base['last_candle_bias'] == 'NONE':
                base['last_candle_bias'] = _derive_bias_from_price(close_price, ema20)
            if base['momentum_bias'] == 'NONE':
                base['momentum_bias'] = base['last_candle_bias']
            if base['trap_alert'] == 'NONE':
                if close_price is not None and support and resistance and isinstance(close_price, (int, float)) and isinstance(support, (int, float)) and isinstance(resistance, (int, float)):
                    if close_price < support:
                        base['trap_alert'] = 'BEAR_TRAP'
                    elif close_price > resistance:
                        base['trap_alert'] = 'BULL_TRAP'
                    else:
                        base['trap_alert'] = 'TRUE'
                else:
                    base['trap_alert'] = 'TRUE'
            if base['sr_interaction'] == 'NONE':
                if close_price is not None and support and resistance and isinstance(close_price, (int, float)) and isinstance(support, (int, float)) and isinstance(resistance, (int, float)):
                    if abs(close_price - support) <= abs(resistance - support) * 0.1:
                        base['sr_interaction'] = 'TESTING_SUPPORT'
                    elif abs(close_price - resistance) <= abs(resistance - support) * 0.1:
                        base['sr_interaction'] = 'TESTING_RESISTANCE'
                    else:
                        base['sr_interaction'] = 'MID_RANGE'
                else:
                    base['sr_interaction'] = 'MID_RANGE'
            return base

        def _derive_volume(p):
            m5 = p.get('m5', {}) if isinstance(p.get('m5'), dict) else {}
            symbol = _get_first_present(p, [['symbol']], '')
            is_otc = 'OTC' in str(symbol).upper()
            if is_otc:
                return {
                    'tick_volume': 1.0,
                    'volume_momentum': 'NO_VOLUME_DATA',
                    'volume_vs_average': 1.0,
                }
            return {
                'tick_volume': _get_first_present(m5, [['volume']], 0),
                'volume_momentum': _get_first_present(p, [['price_action', 'volume_momentum']], _get_first_present(m5, [['volume_trend']], 'STABLE')),
                'volume_vs_average': _get_first_present(m5, [['volume_ratio']], 1.0),
            }

        def _derive_signals(p):
            signals = p.get('signals', {}) if isinstance(p.get('signals'), dict) else {}
            return {
                'triggered': _get_first_present(signals, [['triggered']], []),
                'count': _get_first_present(signals, [['count']], 0),
                'top_signal': _get_first_present(signals, [['top_signal']], 'NO'),
            }

        def _derive_decision_layer(p, state, analysis, engines, m5):
            decision = p.get('decision_layer', {}) if isinstance(p.get('decision_layer'), dict) else {}
            tradeable = _get_first_present(decision, [['tradeable']], None)
            if tradeable is None:
                tradeable = True if state not in ['UNCLEAR', 'CHOPPY_UNCERTAIN', 'LIQUIDITY_VOID'] else False
            confidence = _get_first_present(decision, [['confidence_score']], None)
            if confidence is None:
                confidence = _get_first_present(engines, [['mtf', 'alignment_score']], 50)
            stability = _get_first_present(decision, [['stability_score']], None)
            if stability is None:
                stability = _get_first_present(engines, [['mtf', 'alignment_score']], 50)
            quality = _get_first_present(decision, [['quality_score']], None)
            if quality is None:
                quality = _get_first_present(analysis, [['trend_strength_score']], 50)
            risk = _get_first_present(decision, [['risk_level']], None)
            if risk is None:
                risk = 'MEDIUM'
            expiry = _get_first_present(decision, [['suggested_expiry_minutes']], None)
            if expiry is None:
                expiry = 5
            action = _get_first_present(decision, [['suggested_action']], None)
            if action is None:
                action = 'WAIT'
            reason = _get_first_present(decision, [['tradeable_reason']], None)
            if reason is None:
                reason = 'Derived from existing market classification metrics'
            final_reason = _get_first_present(decision, [['final_reason_th']], None)
            if final_reason is None:
                final_reason = 'รอการวิเคราะห์จาก AI'
            return {
                'tradeable': tradeable,
                'tradeable_reason': reason,
                'confidence_score': confidence,
                'stability_score': stability,
                'quality_score': quality,
                'risk_level': risk,
                'suggested_expiry_minutes': expiry,
                'suggested_action': action,
                'final_reason_th': final_reason,
            }

        symbol = _get_first_present(p, [['symbol']], '')
        is_otc = 'OTC' in str(symbol).upper()
        market_state = _get_first_present(p, [['market_context', 'state'], ['market_state'], ['market_state_full', 'state']], 'UNCLEAR')
        state_description = _get_first_present(p, [['market_context', 'description'], ['market_state_full', 'description']], 'Derived from market classifier')
        analysis = {
            'trend_direction': _get_first_present(p, [['analysis', 'trend_direction']], 'NONE'),
            'trend_type': _get_first_present(p, [['analysis', 'trend_type']], 'NONE'),
            'trend_strength_score': _derive_trend_strength_score(p.get('analysis', {}), p.get('m5', {}), p.get('engines', {})),
            'mtf_alignment_%': _derive_mtf_alignment(p.get('engines', {})),
            'compression_quality_%': _derive_compression_quality(p.get('engines', {}), p.get('m5', {})),
            'exhaustion_risk_%': _derive_exhaustion_risk(p.get('engines', {}), p.get('m5', {}), p.get('m5', {})),
            'bos_detected': _get_first_present(p, [['analysis', 'bos_detected']], False),
        }

        m5 = p.get('m5', {}) if isinstance(p.get('m5'), dict) else {}
        m1 = p.get('m1', {}) if isinstance(p.get('m1'), dict) else {}
        formatted = {
            'meta': {
                'timestamp': _get_first_present(p, [['timestamp']], 'UNKNOWN'),
                'symbol': _get_first_present(p, [['symbol']], 'UNKNOWN'),
                'session': _get_first_present(p, [['meta', 'session']], 'UNKNOWN'),
                'price': _get_first_present(p, [['meta', 'close']], _get_first_present(p, [['current_price']], 0.0)),
                'data_age_ms': _get_first_present(p, [['meta', 'data_age_ms']], 0),
                'data_quality': _get_first_present(p, [['meta', 'data_quality']], 'GOOD'),
            },
            'market_context': {
                'state': market_state,
                'description': state_description,
                'volatility_regime': _get_first_present(p, [['market_context', 'volatility_regime'], ['analysis', 'volatility_regime']], 'NORMAL'),
                'news_impact': 'NONE_OTC' if is_otc else _get_first_present(p, [['market_context', 'news_impact']], 'LOW'),
                'expected_volatility_%': _get_first_present(p, [['market_context', 'expected_volatility_%']], 0.0),
            },
            'timeframes': {
                'm1': {
                    'last_candle': _get_first_present(p, [['meta', 'close']], _get_first_present(m1, [['close']], 0.0)),
                    'ema5': _get_first_present(m1, [['ema5']], 0.0),
                    'ema20': _get_first_present(m1, [['ema20']], 0.0),
                    'rsi': _get_first_present(m1, [['rsi14']], 50),
                    'stoch_k': _get_first_present(m1, [['stoch_k']], 50),
                    'stoch_d': _get_first_present(m1, [['stoch_d']], 50),
                    'macd': _get_first_present(m1, [['macd']], 0.0),
                    'macd_signal': _get_first_present(m1, [['macd_signal']], 0.0),
                },
                'm5': {
                    'bias': _get_first_present(m5, [['bias']], _derive_bias_from_price(_get(p, ['meta', 'close']), _get(m5, ['ema20']))),
                    'ema5': _get_first_present(m5, [['ema5']], 0.0),
                    'ema20': _get_first_present(m5, [['ema20']], 0.0),
                    'bb_upper': _get_first_present(m5, [['bb_upper']], 0.0),
                    'bb_lower': _get_first_present(m5, [['bb_lower']], 0.0),
                    'bb_width': _get_first_present(m5, [['bb_width']], 0.0),
                    'rsi': _get_first_present(m5, [['rsi14']], 50),
                    'stoch_k': _get_first_present(m5, [['stoch_k']], 50),
                    'stoch_d': _get_first_present(m5, [['stoch_d']], 50),
                    'macd': _get_first_present(m5, [['macd']], 0.0),
                    'macd_signal': _get_first_present(m5, [['macd_signal']], 0.0),
                    'adx': _get_first_present(m5, [['adx']], 0.0),
                    'atr': _get_first_present(m5, [['atr14']], 0.0),
                    'support': _get_first_present(m5, [['support']], 0.0),
                    'resistance': _get_first_present(m5, [['resistance']], 0.0),
                    'pivot': _get_first_present(m5, [['pivot']], 0.0),
                },
                'm15': {
                    'bias': _get_first_present(p, [['m15', 'bias']], 'NO'),
                },
            },
            'price_action': _derive_price_action(p),
            'volume': _derive_volume(p),
            'analysis': analysis,
            'signals': _derive_signals(p),
            'decision_layer': _derive_decision_layer(p, market_state, analysis, p.get('engines', {}), m5),
        }

        return formatted

    def _run_engines_parallel(self, symbol: str, payload: dict):
        import copy
        safe_payload = copy.deepcopy(payload)
        tasks: Dict[str, tuple] = {
            'trend':      (self.trend_engine.analyze,      (safe_payload,),      {}),
            'strength':   (self.strength_engine.analyze,   (safe_payload,),      {}),
            'volatility': (self.volatility_engine.analyze, (safe_payload,),      {}),
            'structure':  (self.structure_engine.analyze,  (safe_payload,),      {}),
            'mtf':        (self.mtf_engine.analyze,        (safe_payload,),      {})
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

        if len(results) < 5:
            raise Exception("Fail-fast: some engines failed to produce results")
        return (
            results['trend'],
            results['strength'],
            results['volatility'],
            results['structure'],
            results['mtf'],
        )

    def _log_red(self, msg: str):
        print(f"\033[91m[ORCHESTRATOR ERROR] {msg}\033[0m")

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
            with open(filepath, mode='r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                try:
                    existing_headers = next(reader)
                except StopIteration as e:
                    raise Exception("StopIteration: CSV file is empty!")
                
                if file_exists:
                    try:
                        ts_index = existing_headers.index('timestamp')
                        for row in reader:
                            if len(row) > ts_index and row[ts_index] == current_timestamp:
                                # Timestamp already exists, skip writing to prevent duplicates
                                return
                    except ValueError as e:
                        raise Exception("ValueError when parsing existing headers") from e
                    
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
        """Generates a YAML string from the formatted payload."""
        try:
            # Use yaml.dump for clean, robust YAML generation
            # allow_unicode=True ensures Thai characters are handled correctly
            # sort_keys=False preserves the order from the dictionary
            return yaml.dump(fp, allow_unicode=True, sort_keys=False, indent=2)
        except Exception as e:
            raise

