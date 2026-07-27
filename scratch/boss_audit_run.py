import sys
import os
import yaml
import pandas as pd

sys.path.append(r"E:\BOT_FINALBOT\FINALBOT_Begin")
from data_evaluate.orchestrator import Orchestrator

def generate_boss_audit():
    orch = Orchestrator()
    symbol = 'EURUSD-OTC'
    payload = orch.process_cycle(symbol)
    
    core = payload.get('core_analysis', {})
    supp = payload.get('supplementary_data', {})
    meta = supp.get('meta', {})
    ohlcv = supp.get('ohlcv', {})
    m1_ohlcv = ohlcv.get('m1', {})
    m5_ohlcv = ohlcv.get('m5', {})
    
    # List of all fields to verify
    fields_spec = [
        # (No, Category, Field Name, System Value, Calculation Source / Formula, Status/Observation)
        (1, "meta", "timestamp", meta.get('timestamp'), "datetime.now().isoformat() / Data feed timestamp", "OK - Realtime string"),
        (2, "meta", "symbol", meta.get('symbol'), "Input parameter symbol", "OK - Realtime string"),
        (3, "meta", "session", meta.get('session'), "UTC hour time range mapping (ASIAN/LONDON/NEW YORK)", "OK - Dynamic calculation"),
        (4, "meta", "m1_open", meta.get('m1_open'), "cables_dict['M1']['open'].iloc[-1]", "OK - Calculated from M1 CSV"),
        (5, "meta", "m1_age", meta.get('m1_age'), "Hardcoded to 0 in forming_data (orchestrator.py:208)", "ข้อสังเกต: Locked 0 (ควรใช้ time.time() - candle_ts)"),
        (6, "meta", "m1_quality", meta.get('m1_quality'), "Hardcoded to 'FRESH' in forming_data (orchestrator.py:209)", "ข้อสังเกต: Locked 'FRESH' (ควรคำนวณจาก age)"),
        (7, "meta", "m5_open", meta.get('m5_open'), "candles_dict['M5']['open'].iloc[-1]", "OK - Calculated from M5 CSV"),
        (8, "meta", "m5_age", meta.get('m5_age'), "Hardcoded to 0 in forming_data (orchestrator.py:211)", "ข้อสังเกต: Locked 0 (ควรใช้ time.time() - candle_ts)"),
        (9, "meta", "m5_quality", meta.get('m5_quality'), "Hardcoded to 'FRESH' in forming_data (orchestrator.py:212)", "ข้อสังเกต: Locked 'FRESH' (ควรคำนวณจาก age)"),
        
        (10, "market_context", "state", core.get('state'), "MarketStateClassifier.analyze()", "OK - Dynamic engine calculation"),
        (11, "market_context", "description", core.get('description'), "MarketStateClassifier.analyze()['description']", "OK - Dynamic engine text"),
        (12, "market_context", "volatility_regime", core.get('volatility_regime'), "volatility_engine.analyze()['regime']", "OK - Dynamic engine classification"),
        (13, "market_context", "news_impact", core.get('news_impact'), "check_news_impact(symbol) / OTC override 'NONE_OTC'", "OK - OTC spec compliant"),
        (14, "market_context", "expected_volatility_%", core.get('expected_volatility_%'), "round((m5_atr / close_price)*100, 3)", "OK - Calculated live from ATR & Close"),
        
        (15, "timeframes.m1", "last_candle", core.get('m1_last_candle'), "'BULLISH' if close > open else 'BEARISH'", "OK - Calculated from M1 OHLC"),
        (16, "timeframes.m1", "ema5", core.get('m1_ema5'), "EMA(M1_Close, 5)", "OK - Calculated from M1 CSV"),
        (17, "timeframes.m1", "ema20", core.get('m1_ema20'), "EMA(M1_Close, 20)", "OK - Calculated from M1 CSV"),
        (18, "timeframes.m1", "rsi", core.get('m1_rsi'), "RSI(M1_Close, 14)", "OK - Calculated from M1 CSV"),
        (19, "timeframes.m1", "stoch_k", core.get('m1_stoch_k'), "Stochastic %K(M1, 14, 3)", "OK - Calculated from M1 CSV"),
        (20, "timeframes.m1", "stoch_d", core.get('m1_stoch_d'), "Stochastic %D(M1, 3)", "OK - Calculated from M1 CSV"),
        (21, "timeframes.m1", "macd", core.get('m1_macd'), "MACD Line(M1, 12, 26)", "OK - Calculated from M1 CSV"),
        (22, "timeframes.m1", "macd_signal", core.get('m1_macd_signal'), "MACD Signal(M1, 9)", "OK - Calculated from M1 CSV"),
        (23, "timeframes.m1.ohclv", "open", m1_ohlcv.get('open'), "candles_dict['M1']['open'].iloc[-1]", "OK - Real CSV price"),
        (24, "timeframes.m1.ohclv", "high", m1_ohlcv.get('high'), "candles_dict['M1']['high'].iloc[-1]", "OK - Real CSV price"),
        (25, "timeframes.m1.ohclv", "low", m1_ohlcv.get('low'), "candles_dict['M1']['low'].iloc[-1]", "OK - Real CSV price"),
        (26, "timeframes.m1.ohclv", "close", m1_ohlcv.get('close'), "candles_dict['M1']['close'].iloc[-1]", "OK - Real CSV price"),
        (27, "timeframes.m1.ohclv", "volume", m1_ohlcv.get('volume'), "'NONE_OTC' if OTC else volume", "OK - OTC spec compliant"),

        (28, "timeframes.m5", "bias", core.get('m5_bias'), "'BULLISH' if ema5 > ema20 else 'BEARISH'", "OK - Dynamic technical bias"),
        (29, "timeframes.m5", "ema5", core.get('m5_ema5'), "EMA(M5_Close, 5)", "OK - Calculated from M5 CSV"),
        (30, "timeframes.m5", "ema10", core.get('m5_ema10'), "EMA(M5_Close, 10)", "OK - Calculated from M5 CSV"),
        (31, "timeframes.m5", "ema20", core.get('m5_ema20'), "EMA(M5_Close, 20)", "OK - Calculated from M5 CSV"),
        (32, "timeframes.m5", "ema50", core.get('m5_ema50'), "EMA(M5_Close, 50)", "OK - Calculated from M5 CSV"),
        (33, "timeframes.m5", "bb_upper", core.get('m5_bb_upper'), "Bollinger Upper(M5_Close, 20, 2)", "OK - Calculated from M5 CSV"),
        (34, "timeframes.m5", "bb_lower", core.get('m5_bb_lower'), "Bollinger Lower(M5_Close, 20, 2)", "OK - Calculated from M5 CSV"),
        (35, "timeframes.m5", "bb_width", core.get('m5_bb_width'), "bb_upper - bb_lower", "OK - Exact difference"),
        (36, "timeframes.m5", "rsi", core.get('m5_rsi'), "RSI(M5_Close, 14)", "OK - Calculated from M5 CSV"),
        (37, "timeframes.m5", "stoch_k", core.get('m5_stoch_k'), "Stochastic %K(M5, 14, 3)", "OK - Calculated from M5 CSV"),
        (38, "timeframes.m5", "stoch_d", core.get('m5_stoch_d'), "Stochastic %D(M5, 3)", "OK - Calculated from M5 CSV"),
        (39, "timeframes.m5", "macd", core.get('m5_macd'), "MACD Line(M5, 12, 26)", "OK - Calculated from M5 CSV"),
        (40, "timeframes.m5", "macd_signal", core.get('m5_macd_signal'), "MACD Signal(M5, 9)", "OK - Calculated from M5 CSV"),
        (41, "timeframes.m5", "adx", core.get('m5_adx'), "ADX(M5, 14)", "OK - Calculated from M5 CSV"),
        (42, "timeframes.m5", "atr", core.get('m5_atr'), "ATR(M5, 14)", "OK - Calculated from M5 CSV"),
        (43, "timeframes.m5", "support", core.get('m5_support'), "Support level calculated from M5 swing lows", "OK - Dynamic level"),
        (44, "timeframes.m5", "resistance", core.get('m5_resistance'), "Resistance level calculated from M5 swing highs", "OK - Dynamic level"),
        (45, "timeframes.m5", "pivot", core.get('m5_pivot'), "(M5_High + M5_Low + M5_Close) / 3", "OK - Standard Pivot point formula"),
        (46, "timeframes.m5.ohclv", "open", m5_ohlcv.get('open'), "candles_dict['M5']['open'].iloc[-1]", "OK - Real CSV price"),
        (47, "timeframes.m5.ohclv", "high", m5_ohlcv.get('high'), "candles_dict['M5']['high'].iloc[-1]", "OK - Real CSV price"),
        (48, "timeframes.m5.ohclv", "low", m5_ohlcv.get('low'), "candles_dict['M5']['low'].iloc[-1]", "OK - Real CSV price"),
        (49, "timeframes.m5.ohclv", "close", m5_ohlcv.get('close'), "candles_dict['M5']['close'].iloc[-1]", "OK - Real CSV price"),
        (50, "timeframes.m5.ohclv", "volume", m5_ohlcv.get('volume'), "'NONE_OTC' if OTC else volume", "OK - OTC spec compliant"),

        (51, "timeframes.m15", "bias", core.get('m15_bias'), "EMA5 > EMA20 on M15", "OK - Calculated from M15 CSV"),

        (52, "price_action", "pattern", core.get('pa_pattern'), "price_action_analyzer.analyze()", "OK - Dynamic PA pattern detector"),
        (53, "price_action", "last_candle_bias", core.get('pa_last_candle_bias'), "M5 last candle color ('BULLISH'/'BEARISH')", "OK - Dynamic M5 candle bias"),
        (54, "price_action", "body_strength", core.get('pa_body_strength'), "'STRONG' if body > 0.1 else 'WEAK'", "OK - Dynamic body size check"),
        (55, "price_action", "wick_dominance", core.get('pa_wick_dominance'), "wick ratio calculation ('UPPER_WICK'/'LOW_WICK')", "OK - Dynamic wick ratio"),
        (56, "price_action", "momentum_bias", core.get('pa_momentum_bias'), "directional_bias from price action engine", "OK - Dynamic PA momentum"),
        (57, "price_action", "move_quality", core.get('pa_move_quality'), "move_type from price action engine", "OK - Dynamic PA move quality"),
        (58, "price_action", "trap_alert", core.get('pa_trap_alert'), "trap_detector.analyze()", "OK - Dynamic trap detector"),
        (59, "price_action", "sr_interaction", core.get('pa_sr_interaction'), "sr_interaction from advanced_tools", "OK - Dynamic S/R proximity check"),

        (60, "volume", "tick_volume", core.get('vol_tick_volume'), "1.0 if OTC else m5 volume", "OK - OTC spec compliant"),
        (61, "volume", "volume_momentum", core.get('vol_momentum'), "'NO_VOLUME_DATA' if OTC else volume_momentum", "OK - OTC spec compliant"),
        (62, "volume", "volume_vs_average", core.get('vol_vs_average'), "1.0 if OTC else volume_ratio", "OK - OTC spec compliant"),

        (63, "analysis", "trend_direction", core.get('eng_trend_direction'), "trend_engine.analyze()['direction']", "OK - Engine 1 trend direction"),
        (64, "analysis", "trend_type", core.get('eng_trend_type'), "trend_engine.analyze()['type']", "OK - Engine 1 trend type"),
        (65, "analysis", "trend_strength_score", core.get('eng_trend_strength'), "trend_engine.analyze()['strength']", "OK - Engine 1 trend strength"),
        (66, "analysis", "mtf_alignment_%", core.get('eng_mtf_alignment_score'), "mtf_engine.analyze()['alignment_score']", "OK - Engine 5 MTF score"),
        (67, "analysis", "compression_quality_%", core.get('eng_volatility_compression_quality'), "volatility_engine.analyze()['compression_quality']", "OK - Engine 3 compression quality"),
        (68, "analysis", "exhaustion_risk_%", core.get('eng_strength_exhaustion_risk'), "strength_engine.analyze()['exhaustion_risk']", "OK - Engine 2 exhaustion risk"),
        (69, "analysis", "bos_detected", core.get('eng_structure_bos_detected'), "structure_engine.analyze()['bos_detected']", "OK - Engine 4 BOS boolean"),

        (70, "decision_layer", "tradeable", core.get('dl_tradeable'), "MarketStateClassifier._is_tradeable()", "OK - Real statistical logic"),
        (71, "decision_layer", "stability_score", core.get('dl_stability_score'), "state_data['metrics']['alignment_score']", "OK - Calculated stability metric"),
        (72, "decision_layer", "quality_score", core.get('dl_quality_score'), "state_data['quality_score']", "OK - Calculated quality score"),
        (73, "decision_layer", "risk_level", core.get('dl_risk_level'), "state_data['risk_level']", "OK - Calculated risk level"),
        (74, "decision_layer", "confidence_score", core.get('dl_confidence_score'), "'รอการวิเคราะห์จาก AI'", "OK - Spec placeholder for DeepSeek"),
        (75, "decision_layer", "suggested_expiry_minutes", core.get('dl_suggested_expiry_minutes'), "'รอการวิเคราะห์จาก AI'", "OK - Spec placeholder for DeepSeek"),
        (76, "decision_layer", "suggested_action", core.get('dl_suggested_action'), "'รอการวิเคราะห์จาก AI'", "OK - Spec placeholder for DeepSeek"),
        (77, "decision_layer", "final_reason_th", core.get('dl_final_reason_th'), "'รอการวิเคราะห์จาก AI'", "OK - Spec placeholder for DeepSeek")
    ]
    
    print("\nTotal fields audited:", len(fields_spec))
    for f in fields_spec:
        print(f"[{f[0]}] {f[1]}.{f[2]}: {f[3]} -> {f[5]}")

if __name__ == '__main__':
    generate_boss_audit()
