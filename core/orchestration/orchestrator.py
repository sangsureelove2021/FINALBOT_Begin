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
            _cfg = load_settings(reload=False).get("thresholds", {})
            self.classifier = MarketStateClassifier(config=_cfg)
            logger.info("MarketStateClassifier initialised")
        except Exception as e:
            logger.error(f"Failed to init MarketStateClassifier: {e}")

        self.csv_dir = os.path.join("logs", "all_process")
        os.makedirs(self.csv_dir, exist_ok=True)

        self.json_dir = os.path.join("logs", "json_process")
        os.makedirs(self.json_dir, exist_ok=True)
        
        self.ai_memory = []

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
        
        primary_df = candles_dict.get('M5')
        if not isinstance(primary_df, pd.DataFrame) or primary_df.empty:
            logger.warning(f"No M5 data for {symbol}")
            return None

        final_payload = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        }

        # ── 0. Handle OTC Volume ────────────────────────────────────────
        is_otc = "OTC" in symbol.upper()
        if is_otc:
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
            self._log_red(f"IndicatorStore failed for {symbol}: {e}")
            traceback.print_exc()
            return None

        # ── 3. Advanced Tools ───────────────────────────────────────────
        try:
            df_m5 = candles_dict.get('M5')
            if isinstance(df_m5, pd.DataFrame) and not df_m5.empty:
                advanced_data = self.advanced_tools.analyze_all(symbol, basic_payload, df_m5)
                final_payload.update(advanced_data)
                
        except Exception as e:
            self._log_red(f"AdvancedTools failed for {symbol}: {e}")
            traceback.print_exc()
            return None

        # ── 4. 5 Engines in parallel ────────────────────────────────────
        try:
            trend_data, strength_data, volatility_data, structure_data, mtf_data = \
                self._run_engines_parallel(symbol, final_payload)
                
            final_payload['analysis'] = {
                'trend_direction': trend_data.get('direction', 'NONE'),
                'trend_strength': trend_data.get('strength', 0),
                'trend_type': trend_data.get('type', 'CHOPPY'),
                'volatility_regime': volatility_data.get('regime', 'NORMAL')
            }
            final_payload['engines'] = {
                'trend': trend_data,
                'strength': strength_data,
                'volatility': volatility_data,
                'structure': structure_data,
                'mtf': mtf_data
            }
        except Exception as e:
            self._log_red(f"Engines failed for {symbol}: {e}")
            traceback.print_exc()
            return None

        # ── 5. Market State Classifier ──────────────────────────────────
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
                final_payload['market_state'] = state_data.get('state', 'UNCLEAR')
                final_payload['market_state_full'] = state_data
            else:
                final_payload['market_state'] = 'UNCLEAR'
        except Exception as e:
            self._log_red(f"MarketState Classifier failed for {symbol}: {e}")
            traceback.print_exc()
            return None

        # ── 5.1 Append Group B specific fields ──────────────────────────
        try:
            m5_data = final_payload.get('m5', {})
            atr = m5_data.get('atr14', 0)
            close_price = final_payload.get('meta', {}).get('close', 1)
            expected_vol = round((atr / close_price) * 100, 3) if close_price else 0.0

            final_payload['signals'] = {
                'triggered': [],
                'count': 0,
                'top_signal': 'NO'
            }
            
            m1_data = final_payload.get('m1', {})
            vol_ratio = m1_data.get('volume_ratio', 1.0)
            news_impact = check_news_impact(symbol)

            final_payload['market_context'] = {
                'state': final_payload.get('market_state', 'UNCLEAR'),
                'description': state_data.get('description', 'NONE') if 'state_data' in locals() and state_data else 'NONE',
                'volatility_regime': final_payload.get('analysis', {}).get('volatility_regime', 'NORMAL'),
                'news_impact': news_impact,
                'expected_volatility_%': expected_vol,
                'recent_ai_memory': list(self.ai_memory)
            }

            final_payload['decision_layer'] = {
                'tradeable': state_data.get('tradeable', True) if 'state_data' in locals() and state_data else True,
                'tradeable_reason': 'Passed basic checks',
                'confidence_score': 0,
                'stability_score': state_data.get('metrics', {}).get('alignment_score', 50) if 'state_data' in locals() and state_data else 50,
                'quality_score': 50,
                'risk_level': 'MEDIUM',
                'suggested_expiry_minutes': 5,
                'suggested_action': 'WAIT',
                'final_reason_th': 'รอการวิเคราะห์จาก AI'
            }
        except Exception as e:
            self._log_red(f"Group B formatting failed for {symbol}: {e}")

        # ── 5.5 Deduplicate Payload ──────────────────────────────────────
        try:
            final_payload = self._deduplicate_payload(final_payload)
        except Exception as e:
            logger.warning(f"Dedup payload failed for: {e}")

        # ── 6. Save Full Payload to CSV ─────────────────────────────────
        try:
            self._save_full_csv(symbol, final_payload, candles_dict.get('M1'))
        except Exception as e:
            self._log_red(f"Full CSV Saving failed for {symbol}: {e}")

        # ── 7. Format Payload ───────────────────────────────────────────
        try:
            formatted_payload = self._format_payload(final_payload)
            try:
                self._save_formatted_json(symbol, formatted_payload)
            except Exception as e:
                self._log_red(f"JSON Saving failed for {symbol}: {e}")
            return formatted_payload
        except Exception as e:
            self._log_red(f"Payload Formatting failed for {symbol}: {e}")
            traceback.print_exc()
            return final_payload

    def _format_payload(self, p: dict) -> dict:
        """
        ประกอบร่างข้อมูล (Payload Formatting) ให้ได้โครงสร้างตรงกับที่ต้องการ
        ห้ามมีการคำนวณใหม่เด็ดขาด หากไม่มีข้อมูลให้ใส่ 'NONE'
        """
        def _get(d, key_path, default="NONE"):
            if not isinstance(key_path, (list, tuple)):
                key_path = [key_path]
            curr = d
            for k in key_path:
                if isinstance(curr, dict) and k in curr:
                    curr = curr[k]
                else:
                    return default
            return curr if curr is not None else default

        def _get_fallback(d, paths, default="NONE"):
            for path in paths:
                val = _get(d, path, default=None)
                if val is not None and val != "NONE":
                    return val
            return default

        formatted = {
            "meta": {
                "timestamp": _get(p, 'timestamp'),
                "symbol": _get(p, 'symbol'),
                "session": _get(p, ['meta', 'session']),
                "price": _get(p, ['meta', 'close']),
                "data_age_ms": _get(p, ['meta', 'data_age_ms']),
                "data_quality": _get(p, ['meta', 'data_quality'])
            },
            "market_context": {
                "state": _get_fallback(p, [['market_context', 'state'], 'market_state']),
                "description": _get(p, ['market_context', 'description']),
                "volatility_regime": _get_fallback(p, [['market_context', 'volatility_regime'], ['analysis', 'volatility_regime']]),
                "news_impact": _get(p, ['market_context', 'news_impact']),
                "expected_volatility_%": _get(p, ['market_context', 'expected_volatility_%']),
                "recent_ai_memory": _get(p, ['market_context', 'recent_ai_memory'], [])
            },
            "timeframes": {
                "m1": {
                    "last_candle": _get(p, ['meta', 'close']),
                    "ema5": _get(p, ['m1', 'ema5']),
                    "ema20": _get(p, ['m1', 'ema20']),
                    "rsi": _get(p, ['m1', 'rsi14']),
                    "stoch_k": _get(p, ['m1', 'stoch_k']),
                    "stoch_d": _get(p, ['m1', 'stoch_d']),
                    "macd": _get(p, ['m1', 'macd']),
                    "macd_signal": _get(p, ['m1', 'macd_signal'])
                },
                "m5": {
                    "bias": _get(p, ['m5', 'bias']),
                    "ema5": _get(p, ['m5', 'ema5']),
                    "ema10": _get(p, ['m5', 'ema10']),
                    "ema20": _get(p, ['m5', 'ema20']),
                    "ema50": _get(p, ['m5', 'ema50']),
                    "bb_upper": _get(p, ['m5', 'bb_upper']),
                    "bb_lower": _get(p, ['m5', 'bb_lower']),
                    "bb_width": _get(p, ['m5', 'bb_width']),
                    "rsi": _get(p, ['m5', 'rsi14']),
                    "stoch_k": _get(p, ['m5', 'stoch_k']),
                    "stoch_d": _get(p, ['m5', 'stoch_d']),
                    "macd": _get(p, ['m5', 'macd']),
                    "macd_signal": _get(p, ['m5', 'macd_signal']),
                    "adx": _get(p, ['m5', 'adx']),
                    "atr": _get(p, ['m5', 'atr14']),
                    "support": _get(p, ['m5', 'support']),
                    "resistance": _get(p, ['m5', 'resistance']),
                    "pivot": _get(p, ['m5', 'pivot'])
                },
                "m15": {
                    "bias": _get(p, ['m15', 'bias'])
                }
            },
            "price_action": {
                "pattern": _get(p, ['price_action', 'pattern']),
                "last_candle_bias": _get(p, ['price_action', 'last_candle_bias']),
                "body_strength": _get(p, ['price_action', 'body_strength']),
                "wick_dominance": _get(p, ['price_action', 'wick_dominance']),
                "momentum_bias": _get(p, ['price_action', 'momentum_bias']),
                "move_quality": _get(p, ['price_action', 'move_quality']),
                "trap_alert": _get(p, ['price_action', 'trap_alert']),
                "sr_interaction": _get(p, ['price_action', 'sr_interaction'])
            },
            "volume": {
                "tick_volume": _get(p, ['m5', 'volume']),
                "volume_momentum": _get(p, ['m5', 'volume_trend']),
                "volume_vs_average": _get(p, ['m5', 'volume_ratio'])
            },
            "analysis": {
                "trend_direction": _get(p, ['analysis', 'trend_direction']),
                "trend_type": _get(p, ['analysis', 'trend_type']),
                "trend_strength_score": _get_fallback(p, [['analysis', 'trend_strength_score'], ['analysis', 'trend_strength']], 0),
                "mtf_alignment_%": _get(p, ['engines', 'mtf', 'alignment_score']),
                "compression_quality_%": _get(p, ['engines', 'volatility', 'compression_quality']),
                "exhaustion_risk_%": _get(p, ['engines', 'strength', 'exhaustion_risk']),
                "bos_detected": _get(p, ['analysis', 'bos_detected'], False)
            },
            "signals": {
                "triggered": _get(p, ['signals', 'triggered'], []),
                "count": _get(p, ['signals', 'count'], 0),
                "top_signal": _get(p, ['signals', 'top_signal'], "NO")
            },
            "decision_layer": {
                "tradeable": _get(p, ['decision_layer', 'tradeable'], False),
                "tradeable_reason": _get(p, ['decision_layer', 'tradeable_reason']),
                "confidence_score": _get(p, ['decision_layer', 'confidence_score']),
                "stability_score": _get(p, ['decision_layer', 'stability_score']),
                "quality_score": _get(p, ['decision_layer', 'quality_score']),
                "risk_level": _get(p, ['decision_layer', 'risk_level']),
                "suggested_expiry_minutes": _get(p, ['decision_layer', 'suggested_expiry_minutes']),
                "suggested_action": _get(p, ['decision_layer', 'suggested_action']),
                "final_reason_th": _get(p, ['decision_layer', 'final_reason_th'])
            }
        }
        
        # Override specific default handling for types
        if formatted["signals"]["triggered"] == "NONE":
            formatted["signals"]["triggered"] = []
        if formatted["signals"]["count"] == "NONE":
            formatted["signals"]["count"] = 0
        if formatted["analysis"]["trend_strength_score"] == "NONE":
            formatted["analysis"]["trend_strength_score"] = 0
        if formatted["analysis"]["bos_detected"] == "NONE":
            formatted["analysis"]["bos_detected"] = False
        if formatted["decision_layer"]["tradeable"] == "NONE":
            formatted["decision_layer"]["tradeable"] = False
        if formatted["price_action"]["pattern"] == "NONE":
            formatted["price_action"]["pattern"] = "NONE"

        return formatted

    def _run_engines_parallel(self, symbol: str, payload: dict):
        tasks: Dict[str, tuple] = {
            'trend':      (self.trend_engine.analyze,      (payload,),      {}),
            'strength':   (self.strength_engine.analyze,   (payload,),      {}),
            'volatility': (self.volatility_engine.analyze, (payload,),      {}),
            'structure':  (self.structure_engine.analyze,  (payload,),      {}),
            'mtf':        (self.mtf_engine.analyze,        (payload,),      {})
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
                    self._log_red(f"{label}_engine raised: {exc}")
                    engine_map = {
                        'trend': self.trend_engine, 'strength': self.strength_engine,
                        'volatility': self.volatility_engine, 'structure': self.structure_engine,
                        'mtf': self.mtf_engine
                    }
                    results[label] = engine_map[label].get_neutral_state()

        return (
            results.get('trend',      self.trend_engine.get_neutral_state()),
            results.get('strength',   self.strength_engine.get_neutral_state()),
            results.get('volatility', self.volatility_engine.get_neutral_state()),
            results.get('structure',  self.structure_engine.get_neutral_state()),
            results.get('mtf',        self.mtf_engine.get_neutral_state()),
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
                except StopIteration:
                    file_exists = False
                
                if file_exists:
                    try:
                        ts_index = existing_headers.index('timestamp')
                        for row in reader:
                            if len(row) > ts_index and row[ts_index] == current_timestamp:
                                # Timestamp already exists, skip writing to prevent duplicates
                                return
                    except ValueError:
                        pass
                    
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
