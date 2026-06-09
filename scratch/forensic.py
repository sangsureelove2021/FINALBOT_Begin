import json
import pandas as pd
import re
from collections import Counter

report_path = r"C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\docs\GBPUSD_may_7_backtest_report.md"

logs = []
with open(report_path, 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('| 2026-05-07') or line.startswith('| 2026-05-08'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 12:
                time_ict = parts[1]
                strategy = parts[2]
                action = parts[3]
                entry_score = float(parts[4])
                block_score = float(parts[5])
                confidence = float(parts[6])
                execution = parts[7]
                outcome = parts[8]
                pnl = parts[9]
                fail_reason = parts[10]
                details_str = parts[11]
                
                try:
                    details = json.loads(details_str)
                except:
                    details = {}
                    
                logs.append({
                    'time': time_ict,
                    'strategy': strategy,
                    'action': action,
                    'entry_score': entry_score,
                    'block_score': block_score,
                    'confidence': confidence,
                    'fail_reason': fail_reason,
                    'details': details
                })

df = pd.DataFrame(logs)

print("=== DEEP FORENSIC REPORT ===")
print(f"Total Evaluations: {len(df)}")

print("\n--- Fail Reasons Frequency ---")
print(df['fail_reason'].value_counts())

print("\n--- Strategy Frequencies ---")
print(df['strategy'].value_counts())

print("\n--- Top 5 Highest Entry Scores ---")
top_entries = df.sort_values(by='entry_score', ascending=False).head(5)
for _, row in top_entries.iterrows():
    print(f"Time: {row['time']}, Strategy: {row['strategy']}, Score: {row['entry_score']}, Block: {row['block_score']}, Fail: {row['fail_reason']}, Details: {row['details']}")

print("\n--- PA SNR Analysis ---")
pa_snr = df[df['strategy'] == 'pa_snr']
print(f"Total pa_snr evaluations: {len(pa_snr)}")
print(f"Max pa_snr entry score: {pa_snr['entry_score'].max()}")

print("\n--- Triple Confluence Analysis ---")
tc = df[df['strategy'] == 'triple_confluence']
print(f"Total triple_confluence evaluations: {len(tc)}")
print(tc['fail_reason'].value_counts())
