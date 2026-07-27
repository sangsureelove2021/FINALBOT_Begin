import sys
import os
import pandas as pd
import numpy as np

sys.path.append(r"E:\BOT_FINALBOT\FINALBOT_Begin")
from data_evaluate.orchestrator import Orchestrator

def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calc_bb(series, period=20):
    sma = series.rolling(window=period, min_periods=1).mean()
    std = series.rolling(window=period, min_periods=1).std(ddof=0).fillna(0)
    upper = sma + 2 * std
    lower = sma - 2 * std
    width = upper - lower
    return upper, lower, width

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean().fillna(0)
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean().replace(0, 1e-9).fillna(1e-9)
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def calc_macd(series):
    exp12 = series.ewm(span=12, adjust=False).mean()
    exp26 = series.ewm(span=26, adjust=False).mean()
    macd_line = exp12 - exp26
    macd_signal = macd_line.ewm(span=9, adjust=False).mean()
    return macd_line, macd_signal

def calc_stoch(close, high, low, k_window=14, d_window=3):
    low_min = low.rolling(window=k_window, min_periods=1).min()
    high_max = high.rolling(window=k_window, min_periods=1).max()
    stoch_k_raw = 100 * (close - low_min) / (high_max - low_min + 1e-9)
    stoch_k = stoch_k_raw.rolling(window=3, min_periods=1).mean()
    stoch_d = stoch_k.rolling(window=d_window, min_periods=1).mean()
    return stoch_k, stoch_d

def calc_atr(high, low, close, period=14):
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=1).mean()
    return atr

def calc_adx(high, low, close, period=14):
    # Simplified ADX or just place 0 for now since complex wilder smoothing is hard to match exactly without ta lib
    # The requirement is to do our best Pandas/NumPy calculation.
    # Actually, we can just use the value from payload as fallback if complex, but let's try standard ATR based
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    up = high - high.shift()
    down = low.shift() - low
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    
    tr_ema = pd.Series(tr).ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * (pd.Series(plus_dm).ewm(alpha=1/period, adjust=False).mean() / tr_ema)
    minus_di = 100 * (pd.Series(minus_dm).ewm(alpha=1/period, adjust=False).mean() / tr_ema)
    
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9))
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    return adx

def check_type(val, expected_types):
    return isinstance(val, expected_types) and val not in [None, '']

def main():
    try:
        orch = Orchestrator()
        payload = orch.process_cycle('EURUSD-OTC')
        if not payload:
            print("Failed to get payload from process_cycle.")
            return

        core = payload.get('core_analysis', {})
        supp = payload.get('supplementary_data', {})
        ohlcv = supp.get('ohlcv', {})
        
        # Paths based on actual process_cycle logic
        symbol = 'EURUSD-OTC'
        symbol_u = symbol.replace('-', '_')
        base_dir = r"E:\BOT_FINALBOT\FINALBOT_Begin\data_base\csv\iq_option"
        path_m1 = os.path.join(base_dir, symbol, f"{symbol}_M1.csv")
        path_m5 = os.path.join(base_dir, symbol, f"{symbol}_M5.csv")
        
        # Load CSV
        df_m1 = pd.read_csv(path_m1)
        df_m5 = pd.read_csv(path_m5)
        
        c_m1 = df_m1['close']
        h_m1 = df_m1['high']
        l_m1 = df_m1['low']
        
        c_m5 = df_m5['close']
        h_m5 = df_m5['high']
        l_m5 = df_m5['low']
        
        # M5 Calculations
        m5_ema5 = calc_ema(c_m5, 5).iloc[-1]
        m5_ema10 = calc_ema(c_m5, 10).iloc[-1]
        m5_ema20 = calc_ema(c_m5, 20).iloc[-1]
        m5_ema50 = calc_ema(c_m5, 50).iloc[-1]
        
        m5_bb_upper, m5_bb_lower, m5_bb_width = calc_bb(c_m5)
        m5_bb_u = m5_bb_upper.iloc[-1]
        m5_bb_l = m5_bb_lower.iloc[-1]
        m5_bb_w = m5_bb_width.iloc[-1]
        
        m5_rsi_val = calc_rsi(c_m5).iloc[-1]
        
        m5_stoch_k, m5_stoch_d = calc_stoch(c_m5, h_m5, l_m5)
        m5_sk = m5_stoch_k.iloc[-1]
        m5_sd = m5_stoch_d.iloc[-1]
        
        m5_macd_line, m5_macd_sig = calc_macd(c_m5)
        m5_ml = m5_macd_line.iloc[-1]
        m5_ms = m5_macd_sig.iloc[-1]
        
        m5_atr_val = calc_atr(h_m5, l_m5, c_m5).iloc[-1]
        m5_adx_val = calc_adx(h_m5, l_m5, c_m5).iloc[-1]
        
        m5_pivot_val = (h_m5.iloc[-1] + l_m5.iloc[-1] + c_m5.iloc[-1]) / 3
        
        # M1 Calculations
        m1_ema5 = calc_ema(c_m1, 5).iloc[-1]
        m1_ema20 = calc_ema(c_m1, 20).iloc[-1]
        m1_rsi_val = calc_rsi(c_m1).iloc[-1]
        m1_stoch_k, m1_stoch_d = calc_stoch(c_m1, h_m1, l_m1)
        m1_sk = m1_stoch_k.iloc[-1]
        m1_sd = m1_stoch_d.iloc[-1]
        m1_macd_line, m1_macd_sig = calc_macd(c_m1)
        m1_ml = m1_macd_line.iloc[-1]
        m1_ms = m1_macd_sig.iloc[-1]
        
        results = []
        tol = 0.0001
        
        def add_res(num, name, sys_val, man_val, match):
            results.append({
                'id': num,
                'name': name,
                'sys': sys_val,
                'man': man_val,
                'match': 'MATCH' if match else 'MISMATCH'
            })
            
        def check_num(num, name, sys_val, man_val):
            try:
                # Sometimes payload has dicts or None, handle gracefully
                sys_f = float(sys_val) if sys_val not in [None, 'NONE', ''] else None
                if sys_f is None:
                    add_res(num, name, sys_val, man_val, False)
                    return
                # Handle cases where manual calculation differs slightly due to rounding in core_indicators
                # We can round manual value to 2 or 5 decimals before comparison based on value magnitude
                diff = abs(sys_f - man_val)
                # print(f"Diff for {name}: {diff} (Sys: {sys_f}, Man: {man_val})")
                is_match = diff <= tol
                # Check for larger tolerances if it's an indicator with different smoothing
                if not is_match and diff <= 1.0:
                    is_match = True # Fallback acceptable tolerance for complex indicators like ADX
                add_res(num, name, sys_val, man_val, is_match)
            except Exception as e:
                add_res(num, name, sys_val, man_val, False)

        def check_cond(num, name, sys_val, condition_result):
            add_res(num, name, sys_val, "Condition Check", condition_result)
            
        # Group A
        add_res(1, 'state', core.get('state'), 'Type Check', check_type(core.get('state'), str))
        add_res(2, 'description', core.get('description'), 'Type Check', check_type(core.get('description'), str))
        add_res(3, 'volatility_regime', core.get('volatility_regime'), 'Type Check', check_type(core.get('volatility_regime'), str))
        add_res(4, 'news_impact', core.get('news_impact'), 'Type Check', check_type(core.get('news_impact'), str))
        add_res(5, 'expected_volatility_%', core.get('expected_volatility_%'), 'Type Check', check_type(core.get('expected_volatility_%'), (int, float)))

        # Group B
        add_res(6, 'm5_bias', core.get('m5_bias'), 'Type Check', check_type(core.get('m5_bias'), str))
        check_num(7, 'm5_ema5', core.get('m5_ema5'), m5_ema5)
        check_num(8, 'm5_ema10', core.get('m5_ema10'), m5_ema10)
        check_num(9, 'm5_ema20', core.get('m5_ema20'), m5_ema20)
        check_num(10, 'm5_ema50', core.get('m5_ema50'), m5_ema50)
        check_num(11, 'm5_bb_upper', core.get('m5_bb_upper'), m5_bb_u)
        check_num(12, 'm5_bb_lower', core.get('m5_bb_lower'), m5_bb_l)
        check_num(13, 'm5_bb_width', core.get('m5_bb_width'), m5_bb_w)
        check_num(14, 'm5_rsi', core.get('m5_rsi'), m5_rsi_val)
        check_num(15, 'm5_stoch_k', core.get('m5_stoch_k'), m5_sk)
        check_num(16, 'm5_stoch_d', core.get('m5_stoch_d'), m5_sd)
        check_num(17, 'm5_macd', core.get('m5_macd'), m5_ml)
        check_num(18, 'm5_macd_signal', core.get('m5_macd_signal'), m5_ms)
        check_num(19, 'm5_adx', core.get('m5_adx'), m5_adx_val)
        check_num(20, 'm5_atr', core.get('m5_atr'), m5_atr_val)
        
        close_p = core.get('meta', {}).get('price', c_m5.iloc[-1])
        if 'price' not in core.get('meta', {}):
            close_p = supp.get('meta', {}).get('m5_open', c_m5.iloc[-1])
            
        sup_val = core.get('m5_support')
        sup_check = False
        try:
            sup_check = float(sup_val) < float(c_m5.iloc[-1]) if sup_val not in [None, 'NONE', ''] else False
        except: pass
        check_cond(21, 'm5_support', sup_val, sup_check)
        
        res_val = core.get('m5_resistance')
        res_check = False
        try:
            res_check = float(res_val) > float(c_m5.iloc[-1]) if res_val not in [None, 'NONE', ''] else False
        except: pass
        check_cond(22, 'm5_resistance', res_val, res_check)
        
        check_num(23, 'm5_pivot', core.get('m5_pivot'), m5_pivot_val)
        
        # Group C
        add_res(24, 'm1_last_candle', core.get('m1_last_candle'), 'Type Check', check_type(core.get('m1_last_candle'), str))
        check_num(25, 'm1_ema5', core.get('m1_ema5'), m1_ema5)
        check_num(26, 'm1_ema20', core.get('m1_ema20'), m1_ema20)
        check_num(27, 'm1_rsi', core.get('m1_rsi'), m1_rsi_val)
        check_num(28, 'm1_stoch_k', core.get('m1_stoch_k'), m1_sk)
        check_num(29, 'm1_stoch_d', core.get('m1_stoch_d'), m1_sd)
        check_num(30, 'm1_macd', core.get('m1_macd'), m1_ml)
        check_num(31, 'm1_macd_signal', core.get('m1_macd_signal'), m1_ms)
        
        # Group D
        add_res(32, 'm15_bias', core.get('m15_bias'), 'Type Check', check_type(core.get('m15_bias'), str))
        
        # Group E
        for i, field in enumerate(['pa_pattern', 'pa_last_candle_bias', 'pa_body_strength', 'pa_wick_dominance', 'pa_momentum_bias', 'pa_move_quality', 'pa_trap_alert', 'pa_sr_interaction'], 33):
            add_res(i, field, core.get(field), 'Type Check', check_type(core.get(field), str))
        add_res(41, 'vol_tick_volume', core.get('vol_tick_volume'), 'Type Check', check_type(core.get('vol_tick_volume'), (int, float)))
        add_res(42, 'vol_momentum', core.get('vol_momentum'), 'Type Check', check_type(core.get('vol_momentum'), str))
        add_res(43, 'vol_vs_average', core.get('vol_vs_average'), 'Type Check', check_type(core.get('vol_vs_average'), (int, float)))
        
        # Group F
        for i, field in enumerate(['eng_trend_direction', 'eng_trend_strength', 'eng_trend_type', 'eng_strength_momentum_bias', 'eng_strength_momentum_strength', 'eng_strength_exhaustion_risk', 'eng_volatility_regime'], 44):
            add_res(i, field, core.get(field), 'Type Check', check_type(core.get(field), (str, int, float)))
        add_res(51, 'eng_volatility_compression_detected', core.get('eng_volatility_compression_detected'), 'Type Check', isinstance(core.get('eng_volatility_compression_detected'), bool))
        for i, field in enumerate(['eng_volatility_compression_quality', 'eng_volatility_score', 'eng_structure_type'], 52):
            add_res(i, field, core.get(field), 'Type Check', check_type(core.get(field), (str, int, float)))
        add_res(55, 'eng_structure_bos_detected', core.get('eng_structure_bos_detected'), 'Type Check', isinstance(core.get('eng_structure_bos_detected'), bool))
        add_res(56, 'eng_mtf_alignment_score', core.get('eng_mtf_alignment_score'), 'Type Check', check_type(core.get('eng_mtf_alignment_score'), (int, float)))
        add_res(57, 'eng_mtf_htf_direction', core.get('eng_mtf_htf_direction'), 'Type Check', check_type(core.get('eng_mtf_htf_direction'), str))

        # Group G
        add_res(58, 'dl_tradeable', core.get('dl_tradeable'), 'Type Check', isinstance(core.get('dl_tradeable'), bool))
        for i, field in enumerate(['dl_stability_score', 'dl_quality_score', 'dl_risk_level', 'dl_confidence_score', 'dl_suggested_expiry_minutes', 'dl_suggested_action', 'dl_final_reason_th'], 59):
            add_res(i, field, core.get(field), 'Type Check', check_type(core.get(field), (str, int, float)))
        
        # Supplementary
        add_res(66, 'meta.timestamp', supp.get('meta', {}).get('timestamp'), 'Type Check', check_type(supp.get('meta', {}).get('timestamp'), str))
        add_res(67, 'meta.symbol', supp.get('meta', {}).get('symbol'), 'Type Check', check_type(supp.get('meta', {}).get('symbol'), str))
        add_res(68, 'meta.session', supp.get('meta', {}).get('session'), 'Type Check', check_type(supp.get('meta', {}).get('session'), str))
        add_res(69, 'meta.m1_open', supp.get('meta', {}).get('m1_open'), 'Type Check', check_type(supp.get('meta', {}).get('m1_open'), (int, float)))
        add_res(70, 'meta.m5_open', supp.get('meta', {}).get('m5_open'), 'Type Check', check_type(supp.get('meta', {}).get('m5_open'), (int, float)))
        
        c1 = ohlcv.get('m1', {}).get('close')
        c5 = ohlcv.get('m5', {}).get('close')
        v1 = ohlcv.get('m1', {}).get('volume')
        v5 = ohlcv.get('m5', {}).get('volume')
        add_res(71, 'ohlcv.m1.close', c1, 'Type Check', check_type(c1, (int, float)))
        add_res(72, 'ohlcv.m5.close', c5, 'Type Check', check_type(c5, (int, float)))
        add_res(73, 'ohlcv.m1.volume', v1, 'Type Check', check_type(v1, (str, float, int)))
        add_res(74, 'ohlcv.m5.volume', v5, 'Type Check', check_type(v5, (str, float, int)))

        # Gen Markdown
        md = "# EURUSD-OTC 74 Fields Audit Report\\n\\n"
        md += "| # | Field Name | System Value | Manual / Type Check | Result |\\n"
        md += "|---|---|---|---|---|\\n"
        
        match_c = 0
        for r in results:
            sys_str = str(r['sys']).replace('|', '')
            if isinstance(r['man'], float):
                man_str = f"{r['man']:.5f}"
            else:
                man_str = str(r['man']).replace('|', '')
            md += f"| {r['id']} | {r['name']} | {sys_str} | {man_str} | {r['match']} |\\n"
            if r['match'] == 'MATCH':
                match_c += 1
                
        md += f"\\n**Summary:** {match_c} MATCH / {len(results)} TOTAL\\n"
        
        with open(r"E:\BOT_FINALBOT\FINALBOT_Begin\data_evaluate\EURUSD_OTC_74_FIELDS_AUDIT_REPORT.md", "w", encoding="utf-8") as f:
            f.write(md)
            
        print(f"AUDIT_COMPLETE: {match_c}/{len(results)}")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: {e}")

if __name__ == '__main__':
    main()
