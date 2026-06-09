import pandas as pd
report_path = r'C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\docs\GBPUSD_may_7_backtest_report.md'
executed = []
wins = 0
total_pnl = 0.0

with open(report_path, 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('| 2026') and '| Yes |' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 10:
                executed.append({'Time': parts[1], 'Strategy': parts[2], 'Action': parts[3], 'Score': parts[4], 'Outcome': parts[8], 'PnL': parts[9]})
                if parts[8] == 'WIN': wins += 1
                try: total_pnl += float(parts[9])
                except: pass

print('### Backtest Report (After LOW_ENTRY_SCORE unlock)')
print(f'**Summary**')
print(f'- Total Executed: {len(executed)} trades')
print(f'- WIN: {wins} trades')
print(f'- LOSS: {len(executed) - wins} trades')
print(f'- Net PnL: {total_pnl:+.2f} THB\n')
print('| Time | Strategy | Action | Entry Score | Outcome | PnL |')
print('| :--- | :--- | :--- | :--- | :--- | :--- |')
for t in executed:
    print(f"| {t['Time']} | {t['Strategy']} | {t['Action']} | {t['Score']} | {t['Outcome']} | {t['PnL']} |")
