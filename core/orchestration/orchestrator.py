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

        self.orchestrator_log_dir = os.path.join("logs", "logs_orchestrator")
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
        ai_context: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        
        import pandas as pd
        candles_dict = {}
        data_iq_dir = os.path.join("data", "DATA IQ")
        sym_prefix = symbol.replace("-", "_")
        
        for tf in ["M1", "M5", "M15"]:
            csv_path = os.path.join(data_iq_dir, f"{sym_prefix}_{tf}.csv")
            if not os.path.exists(csv_path):
                logger.warning(f"No {tf} CSV for {symbol}")
                raise ValueError(f"No {tf} data for {symbol}")
            try:
                df = pd.read_csv(csv_path)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.set_index('timestamp')
                candles_dict[tf] = df
            except Exception as e:
                logger.exception(f"Failed to read {csv_path}")
                raise
                
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
                raise ValueError("MarketStateClassifier not initialized")
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
                'stability_score': state_data['metrics']['alignment_score'] if state_data else 50,
                'quality_score': state_data['quality_score'] if state_data else 50,
                'risk_level': state_data['risk_level'] if state_data else 'MEDIUM',
                'confidence_score': 'รอการวิเคราะห์จาก AI',
                'suggested_expiry_minutes': 'รอการวิเคราะห์จาก AI',
                'suggested_action': 'รอการวิเคราะห์จาก AI',
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
                
            try:
                txt_filepath = self._save_txt_payload(symbol, formatted_payload)
                from core.ai_analysis.prompt_ai_context import build_prompt
                build_prompt(txt_filepath)
            except Exception as e:
                logger.error(f"Orchestrator failed to build prompt text for {symbol}: {e}")
                
            self.last_payload = formatted_payload
            return formatted_payload
        except Exception as e:
            raise

    def _format_payload(self, p: dict) -> dict:
        """
        Build a structured payload from the data already produced by the indicator store,
        advanced tools, and market classification engines.
        No fallbacks — if a required field is missing, raise immediately.
        """
        is_otc = 'OTC' in str(p.get('symbol', '')).upper()

        # ── Direct extraction helpers (no fallback) ──────────────────────
        def _req(d: dict, *keys):
            """Require a value — raise ValueError if missing or None."""
            curr = d
            for k in keys:
                if not isinstance(curr, dict) or k not in curr:
                    raise ValueError(f"Required field missing: {' -> '.join(str(x) for x in keys)}")
                curr = curr[k]
            if curr is None:
                raise ValueError(f"Required field is None: {' -> '.join(str(x) for x in keys)}")
            return curr

        def _derive_session():
            now_utc = datetime.now(timezone.utc)
            h = now_utc.hour
            if 0 <= h < 7:   return "SYDNEY/TOKYO"
            elif 7 <= h < 12: return "LONDON_OPEN"
            elif 12 <= h < 16: return "NY/LONDON_OVERLAP"
            elif 16 <= h < 21: return "NY_AFTERNOON"
            else:             return "SYDNEY_OPEN"

        # ── Extract core blocks ───────────────────────────────────────────
        m5   = _req(p, 'm5')
        m1   = p.get('m1')  # optional: may be omitted by caller
        meta = _req(p, 'meta')
        pa   = _req(p, 'price_action')
        eng  = _req(p, 'engines')
        dl   = _req(p, 'decision_layer')
        mc   = _req(p, 'market_context')

        # ── meta block ────────────────────────────────────────────────────
        meta_block = {
            'timestamp':   _req(p, 'timestamp'),
            'symbol':      _req(p, 'symbol'),
            'session':     meta.get('session') or _derive_session(),
            'price':       _req(meta, 'close'),
            'data_age_ms': _req(meta, 'data_age_ms'),
            'data_quality': _req(meta, 'data_quality'),
            'data_age_ms_m1': meta.get('data_age_ms_m1', meta.get('data_age_ms')),
            'data_quality_m1': meta.get('data_quality_m1', meta.get('data_quality')),
            'data_age_ms_m5': meta.get('data_age_ms_m5', meta.get('data_age_ms')),
            'data_quality_m5': meta.get('data_quality_m5', meta.get('data_quality')),
        }
        # Optionally expose per-timeframe price if available.
        # Prefer explicit values provided in `meta` (price_m1/price_m5),
        # otherwise derive from the timeframe data if present.
        if 'price_m1' in meta:
            meta_block['price_m1'] = meta['price_m1']
        else:
            if m1 and isinstance(m1, dict):
                price_m1 = m1.get('close', m1.get('open'))
                if price_m1 is not None:
                    meta_block['price_m1'] = price_m1

        if 'price_m5' in meta:
            meta_block['price_m5'] = meta['price_m5']
        else:
            if m5 and isinstance(m5, dict):
                price_m5 = m5.get('close', m5.get('open', meta.get('close')))
                if price_m5 is not None:
                    meta_block['price_m5'] = price_m5

        # ── market_context block ──────────────────────────────────────────
        mc_block = {
            'state':               _req(mc, 'state'),
            'description':         _req(mc, 'description'),
            'volatility_regime':   _req(p, 'analysis', 'volatility_regime'),
            'news_impact':         'NONE_OTC' if is_otc else _req(mc, 'news_impact'),
            'expected_volatility_%': _req(mc, 'expected_volatility_%'),
        }

        # ── timeframes.m1 block (optional) ───────────────────────────────
        m1_block = None
        if m1 and isinstance(m1, dict):
            close_price = _req(meta, 'close')
            m1_open = m1.get('open', meta.get('open'))
            m1_block = {
                'last_candle':  'BULLISH' if close_price > m1_open else 'BEARISH',
                'ema5':         _req(m1, 'ema5'),
                'ema20':        _req(m1, 'ema20'),
                'rsi':          _req(m1, 'rsi14'),
                'stoch_k':      _req(m1, 'stoch_k'),
                'stoch_d':      _req(m1, 'stoch_d'),
                'macd':         _req(m1, 'macd'),
                'macd_signal':  _req(m1, 'macd_signal'),
            }

        # ── timeframes.m5 block ───────────────────────────────────────────
        m5_block = {
            'bias':        _req(m5, 'bias'),
            'ema5':        _req(m5, 'ema5'),
            'ema10':       _req(m5, 'ema10'),
            'ema20':       _req(m5, 'ema20'),
            'ema50':       _req(m5, 'ema50'),
            'bb_upper':    _req(m5, 'bb_upper'),
            'bb_lower':    _req(m5, 'bb_lower'),
            'bb_width':    _req(m5, 'bb_width'),
            'rsi':         _req(m5, 'rsi14'),
            'stoch_k':     _req(m5, 'stoch_k'),
            'stoch_d':     _req(m5, 'stoch_d'),
            'macd':        _req(m5, 'macd'),
            'macd_signal': _req(m5, 'macd_signal'),
            'adx':         _req(m5, 'adx'),
            'atr':         _req(m5, 'atr14'),
            'support':     _req(m5, 'support'),
            'resistance':  _req(m5, 'resistance'),
            'pivot':       _req(m5, 'pivot'),
        }

        # ── timeframes.m15 block ──────────────────────────────────────────
        m15_block = {
            'bias': _req(p, 'm15', 'bias'),
        }

        # ── price_action block ────────────────────────────────────────────
        pa_block = {
            'pattern':         _req(pa, 'pattern'),
            'last_candle_bias':_req(pa, 'last_candle_bias'),
            'body_strength':   _req(pa, 'body_strength'),
            'wick_dominance':  _req(pa, 'wick_dominance'),
            'momentum_bias':   _req(pa, 'momentum_bias'),
            'move_quality':    _req(pa, 'move_quality'),
            'trap_alert':      _req(pa, 'trap_alert'),
            'sr_interaction':  _req(pa, 'sr_interaction'),
        }

        # ── volume block ─────────────────────────────────────────────────
        if is_otc:
            vol_block = {
                'tick_volume':      1.0,
                'volume_momentum':  'NO_VOLUME_DATA',
                'volume_vs_average': 1.0,
            }
        else:
            vol_block = {
                'tick_volume':       _req(m5, 'volume'),
                'volume_momentum':   _req(pa, 'volume_momentum'),
                'volume_vs_average': _req(m5, 'volume_ratio'),
            }

        # ── analysis block ────────────────────────────────────────────────
        analysis_block = {
            'trend_direction':      _req(p, 'analysis', 'trend_direction'),
            'trend_type':           _req(p, 'analysis', 'trend_type'),
            'trend_strength_score': (p.get('analysis', {}) or {}).get('trend_strength') if (p.get('analysis') and 'trend_strength' in p.get('analysis')) else _req(eng, 'trend', 'strength'),
            'mtf_alignment_%':      _req(eng, 'mtf', 'alignment_score'),
            'compression_quality_%':_req(eng, 'volatility', 'compression_quality'),
            'exhaustion_risk_%':    _req(eng, 'strength', 'exhaustion_risk'),
            'bos_detected':         _req(eng, 'structure', 'bos_detected'),
        }

        # ── decision_layer block ──────────────────────────────────────────
        decision_block = {
            'tradeable':              _req(dl, 'tradeable'),
            'stability_score':        _req(dl, 'stability_score'),
            'quality_score':          _req(dl, 'quality_score'),
            'risk_level':             _req(dl, 'risk_level'),
            'confidence_score':       _req(dl, 'confidence_score'),
            'suggested_expiry_minutes': _req(dl, 'suggested_expiry_minutes'),
            'suggested_action':       _req(dl, 'suggested_action'),
            'final_reason_th':        _req(dl, 'final_reason_th'),
        }

        timeframes = {}
        if m1_block is not None:
            timeframes['m1'] = m1_block
        if m5_block is not None:
            timeframes['m5'] = m5_block
        if m15_block is not None:
            timeframes['m15'] = m15_block

        return {
            'meta':           meta_block,
            'market_context': mc_block,
            'timeframes':     timeframes,
            'price_action':   pa_block,
            'volume':         vol_block,
            'analysis':       analysis_block,
            'decision_layer': decision_block,
        }

    def _run_engines_parallel(self, symbol: str, payload: dict, candles_dict: dict):
        import copy
        safe_payload = copy.deepcopy(payload)
        tasks: Dict[str, tuple] = {
            'trend':      (self.trend_engine.analyze,      (safe_payload,),      {}),
            'strength':   (self.strength_engine.analyze,   (safe_payload,),      {}),
            'volatility': (self.volatility_engine.analyze, (safe_payload,),      {}),
            'structure':  (self.structure_engine.analyze,  (safe_payload,),      {}),
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
            # Clean numpy objects by routing through JSON encoder
            cleaned_fp = json.loads(json.dumps(fp, cls=NumpyEncoder))
            return yaml.dump(cleaned_fp, allow_unicode=True, sort_keys=False, indent=2)
        except Exception as e:
            raise

    def _save_txt_payload(self, symbol: str, formatted_payload: dict) -> str:
        date_str = datetime.now().strftime('%Y%m%d%H%M%S')
        symbol_dir = os.path.join(self.orchestrator_log_dir, symbol.replace("-", "_"))
        os.makedirs(symbol_dir, exist_ok=True)
        filename = f"{symbol.replace('-', '_')}_{date_str}.txt"
        filepath = os.path.join(symbol_dir, filename)
        
        yaml_text = self._generate_yaml_text(symbol, formatted_payload)
        
        meta = formatted_payload.get("meta", {})
        timestamp_str = str(meta.get("timestamp", datetime.now().strftime("%Y-%m-%dT%H:%M:%S")))
        ts_clean = timestamp_str.replace('-', '').replace(':', '').replace('T', '').replace('.', '')[:14]
        prompt_id = f"{symbol.replace('-', '').replace('_', '')}{ts_clean}"
        
        final_text = f"ID:{prompt_id}\n{yaml_text}"
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(final_text)
            
        return filepath

