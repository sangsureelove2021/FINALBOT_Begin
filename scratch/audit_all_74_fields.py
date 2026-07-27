import sys
import os
import re
import yaml
import pandas as pd
import numpy as np

sys.path.append(r"E:\BOT_FINALBOT\FINALBOT_Begin")
from data_evaluate.orchestrator import Orchestrator

def detailed_74_field_audit():
    orch = Orchestrator()
    symbol = 'EURUSD-OTC'
    
    formatted_payload = orch.process_cycle(symbol)
    
    txt_dir = os.path.join(orch.orchestrator_log_dir, symbol)
    txt_files = [os.path.join(txt_dir, f) for f in os.listdir(txt_dir) if f.endswith('.txt')]
    latest_txt = sorted(txt_files)[-1]
    
    with open(latest_txt, 'r', encoding='utf-8') as f:
        gen_lines = f.read().splitlines()
        
    ref_path = r"E:\BOT_FINALBOT\FINALBOT_Begin\docs\About_Me\Payload - ที่ต้องการ.txt"
    with open(ref_path, 'r', encoding='utf-8') as f:
        ref_lines = f.read().splitlines()
        
    print(f"Generated TXT lines count: {len(gen_lines)}")
    print(f"Reference TXT lines count: {len(ref_lines)}")

    # Parse fields from ref_lines
    # 74 fields mapping list
    fields_list = [
        # Line in ref, Section, Field Name, Expected Type, Source In Code, Notes
        # meta (9 fields in meta section, but let's count 74 payload fields according to standard specification)
    ]

    # Let's map lines from ref_lines to field numbers
    field_counter = 0
    ref_field_map = []
    
    for idx, line in enumerate(ref_lines, 1):
        line_str = line.strip()
        indent = len(line) - len(line.lstrip(' '))
        if not line_str:
            continue
        if line_str.startswith('ID:'):
            ref_field_map.append((idx, 0, 'ID', 'Header ID', line_str))
            continue
        if line_str.endswith(':') and not ':' in line_str[:-1]:
            ref_field_map.append((idx, 0, 'Section Header', line_str[:-1], line_str))
            continue
            
        # Key value pair
        parts = line_str.split(':', 1)
        key = parts[0].strip()
        val = parts[1].strip() if len(parts) > 1 else ''
        
        # Is it a parent section header like ohclv:?
        if val == '' and line_str.endswith(':'):
            ref_field_map.append((idx, 0, 'SubSection Header', key, line_str))
            continue
            
        field_counter += 1
        ref_field_map.append((idx, field_counter, 'Field', key, val))

    print(f"Total key-value fields extracted from reference file: {field_counter}")
    for item in ref_field_map:
        if item[2] == 'Field':
            print(f"Field #{item[1]} (Line {item[0]}): {item[3]} -> Ref Value: {item[4]}")

if __name__ == '__main__':
    detailed_74_field_audit()
