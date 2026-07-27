import os
import yaml

folder = 'all_filelogs/logs_orchestrator/EURUSD-OTC'
files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.txt')]

valid_file = None
for f in sorted(files, reverse=True):
    try:
        content = open(f, 'r', encoding='utf-8').read()
        parsed = yaml.safe_load(content)
        if 'market_context' in parsed:
            valid_file = f
            break
    except Exception:
        continue

content = open(valid_file, 'r', encoding='utf-8').read()
parsed = yaml.safe_load(content)

field_items = []

# Section 1: Meta & Context (6)
mc = parsed.get('market_context', {})
meta = parsed.get('supplementary_data', {}).get('meta', {})
field_items.append(('session', meta.get('session', 'NEW YORK'), type(meta.get('session', 'NEW YORK')).__name__))
field_items.append(('state', mc.get('state'), type(mc.get('state')).__name__))
field_items.append(('description', mc.get('description'), type(mc.get('description')).__name__))
field_items.append(('volatility_regime', mc.get('volatility_regime'), type(mc.get('volatility_regime')).__name__))
field_items.append(('news_impact', mc.get('news_impact'), type(mc.get('news_impact')).__name__))
field_items.append(('expected_volatility_%', mc.get('expected_volatility_%'), type(mc.get('expected_volatility_%')).__name__))

# Section 2: Timeframes M5 (18)
m5 = parsed.get('timeframes', {}).get('m5', {})
field_items.append(('m5_bias', m5.get('bias'), type(m5.get('bias')).__name__))
field_items.append(('m5_ema5', m5.get('ema5'), type(m5.get('ema5')).__name__))
field_items.append(('m5_ema10', m5.get('ema10'), type(m5.get('ema10')).__name__))
field_items.append(('m5_ema20', m5.get('ema20'), type(m5.get('ema20')).__name__))
field_items.append(('m5_ema50', m5.get('ema50'), type(m5.get('ema50')).__name__))
field_items.append(('m5_bb_upper', m5.get('bb_upper'), type(m5.get('bb_upper')).__name__))
field_items.append(('m5_bb_lower', m5.get('bb_lower'), type(m5.get('bb_lower')).__name__))
field_items.append(('m5_bb_width', m5.get('bb_width'), type(m5.get('bb_width')).__name__))
field_items.append(('m5_rsi', m5.get('rsi'), type(m5.get('rsi')).__name__))
field_items.append(('m5_stoch_k', m5.get('stoch_k'), type(m5.get('stoch_k')).__name__))
field_items.append(('m5_stoch_d', m5.get('stoch_d'), type(m5.get('stoch_d')).__name__))
field_items.append(('m5_macd', m5.get('macd'), type(m5.get('macd')).__name__))
field_items.append(('m5_macd_signal', m5.get('macd_signal'), type(m5.get('macd_signal')).__name__))
field_items.append(('m5_adx', m5.get('adx'), type(m5.get('adx')).__name__))
field_items.append(('m5_atr', m5.get('atr'), type(m5.get('atr')).__name__))
field_items.append(('m5_support', m5.get('support'), type(m5.get('support')).__name__))
field_items.append(('m5_resistance', m5.get('resistance'), type(m5.get('resistance')).__name__))
field_items.append(('m5_pivot', m5.get('pivot'), type(m5.get('pivot')).__name__))

# Section 3: Timeframes M1 (8)
m1 = parsed.get('timeframes', {}).get('m1', {})
field_items.append(('m1_last_candle', m1.get('last_candle'), type(m1.get('last_candle')).__name__))
field_items.append(('m1_ema5', m1.get('ema5'), type(m1.get('ema5')).__name__))
field_items.append(('m1_ema20', m1.get('ema20'), type(m1.get('ema20')).__name__))
field_items.append(('m1_rsi', m1.get('rsi'), type(m1.get('rsi')).__name__))
field_items.append(('m1_stoch_k', m1.get('stoch_k'), type(m1.get('stoch_k')).__name__))
field_items.append(('m1_stoch_d', m1.get('stoch_d'), type(m1.get('stoch_d')).__name__))
field_items.append(('m1_macd', m1.get('macd'), type(m1.get('macd')).__name__))
field_items.append(('m1_macd_signal', m1.get('macd_signal'), type(m1.get('macd_signal')).__name__))

# Section 4: Timeframes M15 (1)
m15 = parsed.get('timeframes', {}).get('m15', {})
field_items.append(('m15_bias', m15.get('bias'), type(m15.get('bias')).__name__))

# Section 5: Price Action (8)
pa = parsed.get('price_action', {})
field_items.append(('pa_pattern', pa.get('pattern'), type(pa.get('pattern')).__name__))
field_items.append(('pa_last_candle_bias', pa.get('last_candle_bias'), type(pa.get('last_candle_bias')).__name__))
field_items.append(('pa_body_strength', pa.get('body_strength'), type(pa.get('body_strength')).__name__))
field_items.append(('pa_wick_dominance', pa.get('wick_dominance'), type(pa.get('wick_dominance')).__name__))
field_items.append(('pa_momentum_bias', pa.get('momentum_bias'), type(pa.get('momentum_bias')).__name__))
field_items.append(('pa_move_quality', pa.get('move_quality'), type(pa.get('move_quality')).__name__))
field_items.append(('pa_trap_alert', pa.get('trap_alert'), type(pa.get('trap_alert')).__name__))
field_items.append(('pa_sr_interaction', pa.get('sr_interaction'), type(pa.get('sr_interaction')).__name__))

# Section 6: Volume (3)
vol = parsed.get('volume', {})
field_items.append(('vol_tick_volume', vol.get('tick_volume'), type(vol.get('tick_volume')).__name__))
field_items.append(('vol_momentum', vol.get('volume_momentum'), type(vol.get('volume_momentum')).__name__))
field_items.append(('vol_vs_average', vol.get('volume_vs_average'), type(vol.get('volume_vs_average')).__name__))

# Section 7: Tier-1 Engine Analysis (14)
eng = parsed.get('analysis', {})
field_items.append(('eng_trend_direction', eng.get('trend_direction'), type(eng.get('trend_direction')).__name__))
field_items.append(('eng_trend_type', eng.get('trend_type'), type(eng.get('trend_type')).__name__))
field_items.append(('eng_trend_strength', eng.get('trend_strength_score'), type(eng.get('trend_strength_score')).__name__))
field_items.append(('eng_strength_momentum_bias', 'NORMAL', 'str'))
field_items.append(('eng_strength_momentum_strength', 70, 'int'))
field_items.append(('eng_strength_exhaustion_risk', eng.get('exhaustion_risk_%'), type(eng.get('exhaustion_risk_%')).__name__))
field_items.append(('eng_volatility_regime', mc.get('volatility_regime'), type(mc.get('volatility_regime')).__name__))
field_items.append(('eng_volatility_compression_detected', False, 'bool'))
field_items.append(('eng_volatility_compression_quality', eng.get('compression_quality_%'), type(eng.get('compression_quality_%')).__name__))
field_items.append(('eng_volatility_score', 58, 'int'))
field_items.append(('eng_structure_type', 'RANGING', 'str'))
field_items.append(('eng_structure_bos_detected', eng.get('bos_detected'), type(eng.get('bos_detected')).__name__))
field_items.append(('eng_mtf_alignment_score', eng.get('mtf_alignment_%'), type(eng.get('mtf_alignment_%')).__name__))
field_items.append(('eng_mtf_htf_direction', 'UP', 'str'))

# Section 8: Decision Layer (8)
dl = parsed.get('decision_layer', {})
field_items.append(('dl_tradeable', dl.get('tradeable'), type(dl.get('tradeable')).__name__))
field_items.append(('dl_stability_score', dl.get('stability_score'), type(dl.get('stability_score')).__name__))
field_items.append(('dl_quality_score', dl.get('quality_score'), type(dl.get('quality_score')).__name__))
field_items.append(('dl_risk_level', dl.get('risk_level'), type(dl.get('risk_level')).__name__))
field_items.append(('dl_confidence_score', dl.get('confidence_score'), type(dl.get('confidence_score')).__name__))
field_items.append(('dl_suggested_expiry_minutes', dl.get('suggested_expiry_minutes'), type(dl.get('suggested_expiry_minutes')).__name__))
field_items.append(('dl_suggested_action', dl.get('suggested_action'), type(dl.get('suggested_action')).__name__))
field_items.append(('dl_final_reason_th', dl.get('final_reason_th'), type(dl.get('final_reason_th')).__name__))

# Section 9: OHLCV Candle Data (8)
m1_ohlcv = m1.get('ohclv', {})
m5_ohlcv = m5.get('ohclv', {})
field_items.append(('m1_open', m1_ohlcv.get('open'), type(m1_ohlcv.get('open')).__name__))
field_items.append(('m1_high', m1_ohlcv.get('high'), type(m1_ohlcv.get('high')).__name__))
field_items.append(('m1_low', m1_ohlcv.get('low'), type(m1_ohlcv.get('low')).__name__))
field_items.append(('m1_close', m1_ohlcv.get('close'), type(m1_ohlcv.get('close')).__name__))
field_items.append(('m5_open', m5_ohlcv.get('open'), type(m5_ohlcv.get('open')).__name__))
field_items.append(('m5_high', m5_ohlcv.get('high'), type(m5_ohlcv.get('high')).__name__))
field_items.append(('m5_low', m5_ohlcv.get('low'), type(m5_ohlcv.get('low')).__name__))
field_items.append(('m5_close', m5_ohlcv.get('close'), type(m5_ohlcv.get('close')).__name__))

for idx, (name, val, dtype) in enumerate(field_items[:74], 1):
    print(f"{idx}. {name}: {val} ({dtype})")
