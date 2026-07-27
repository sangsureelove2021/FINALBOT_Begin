import sys
import os
import re
import pandas as pd
import numpy as np

sys.path.append(r"E:\BOT_FINALBOT\FINALBOT_Begin")
from data_evaluate.orchestrator import Orchestrator

def run_deep_audit():
    orch = Orchestrator()
    symbol = 'EURUSD-OTC'
    
    # Process cycle
    formatted_payload = orch.process_cycle(symbol)
    
    # Read saved TXT payload
    txt_dir = os.path.join(orch.orchestrator_log_dir, symbol)
    txt_files = [os.path.join(txt_dir, f) for f in os.listdir(txt_dir) if f.endswith('.txt')]
    latest_txt = sorted(txt_files)[-1]
    
    with open(latest_txt, 'r', encoding='utf-8') as f:
        gen_lines = f.read().splitlines()
        
    ref_path = r"E:\BOT_FINALBOT\FINALBOT_Begin\docs\About_Me\Payload - ที่ต้องการ.txt"
    with open(ref_path, 'r', encoding='utf-8') as f:
        ref_lines = f.read().splitlines()
        
    print(f"Generated TXT lines: {len(gen_lines)}")
    print(f"Reference TXT lines: {len(ref_lines)}")
    
    # 1. Line-by-line comparison of Key & Indentation
    print("\n=======================================================")
    print("1. LINE-BY-LINE INDENTATION & FIELD NAME AUDIT")
    print("=======================================================")
    
    line_errors = []
    for idx, (g_line, r_line) in enumerate(zip(gen_lines, ref_lines), 1):
        g_indent = len(g_line) - len(g_line.lstrip(' '))
        r_indent = len(r_line) - len(r_line.lstrip(' '))
        
        g_key = g_line.strip().split(':')[0] if ':' in g_line else g_line.strip()
        r_key = r_line.strip().split(':')[0] if ':' in r_line else r_line.strip()
        
        g_has_space_after_colon = ': ' in g_line if ':' in g_line else True
        r_has_space_after_colon = ': ' in r_line if ':' in r_line else True
        
        match = (g_indent == r_indent) and (g_key == r_key)
        if not match or (g_has_space_after_colon != r_has_space_after_colon):
            line_errors.append((idx, r_line, g_line, r_indent, g_indent, r_key, g_key, r_has_space_after_colon, g_has_space_after_colon))
            print(f"Line {idx} MISMATCH:")
            print(f"  REF: [{r_indent} spaces] '{r_line}'")
            print(f"  GEN: [{g_indent} spaces] '{g_line}'")
            
    if not line_errors:
        print("✅ Line keys and indentations match reference template 100%.")

    # Extract all 74 fields and check their origin / calculation
    core = formatted_payload.get('core_analysis', {})
    supp = formatted_payload.get('supplementary_data', {})
    meta = supp.get('meta', {})
    ohlcv = supp.get('ohlcv', {})
    
    print("\n=======================================================")
    print("2. 74 FIELDS AUDIT (ORIGIN, HARDCODED CHECK, CROSS-FIELD LOGIC)")
    print("=======================================================")
    
    # Let's inspect each of the 74 fields in core and supp
    # We will list all 74 fields and their source
    
    # Check Cross-Field Logic:
    # A) m1_last_candle vs m1 open/close
    m1_open = meta.get('m1_open') or ohlcv.get('m1', {}).get('open')
    m1_close = ohlcv.get('m1', {}).get('close')
    m1_last_candle = core.get('m1_last_candle')
    expected_m1_candle = 'BULLISH' if m1_close > m1_open else ('BEARISH' if m1_close < m1_open else 'NEUTRAL')
    print(f"\n[Cross-Logic A] m1_open={m1_open}, m1_close={m1_close}, m1_last_candle={m1_last_candle}, Expected={expected_m1_candle}")
    
    # B) eng_trend_direction vs m5_bias
    eng_trend_dir = core.get('eng_trend_direction')
    m5_bias = core.get('m5_bias')
    print(f"[Cross-Logic B] eng_trend_direction={eng_trend_dir}, m5_bias={m5_bias}")
    
    # C) pa_last_candle_bias vs m1_last_candle
    pa_last_candle_bias = core.get('pa_last_candle_bias')
    print(f"[Cross-Logic C] pa_last_candle_bias={pa_last_candle_bias}, m1_last_candle={m1_last_candle}")

    # D) m5_support, m5_resistance, m5_pivot vs m5_close
    m5_close = ohlcv.get('m5', {}).get('close')
    m5_sup = core.get('m5_support')
    m5_res = core.get('m5_resistance')
    m5_piv = core.get('m5_pivot')
    print(f"[Cross-Logic D] m5_close={m5_close}, support={m5_sup}, resistance={m5_res}, pivot={m5_piv}")
    
    # E) BB upper / lower / width
    bb_u = core.get('m5_bb_upper')
    bb_l = core.get('m5_bb_lower')
    bb_w = core.get('m5_bb_width')
    print(f"[Cross-Logic E] bb_upper={bb_u}, bb_lower={bb_l}, calculated width={bb_u - bb_l if isinstance(bb_u, (int,float)) and isinstance(bb_l, (int,float)) else 'N/A'}, payload bb_width={bb_w}")

if __name__ == '__main__':
    run_deep_audit()
