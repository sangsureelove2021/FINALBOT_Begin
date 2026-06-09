import re
report_path = r'C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\docs\GBPUSD_may_7_backtest_report.md'
out_path = r'C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\scratch\table.md'
states = {}
evals = []

with open(report_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_states = False
in_evals = False

for line in lines:
    if line.startswith('## 1. Market'):
        in_states = True
        in_evals = False
        continue
    if line.startswith('## 2. Detailed'):
        in_states = False
        in_evals = True
        continue
        
    if in_states and line.startswith('| 2026'):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 4:
            time_ict = parts[1]
            new_state = parts[3]
            states[time_ict] = new_state
            
    if in_evals and line.startswith('| 2026'):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 12:
            time_ict = parts[1]
            strategy = parts[2]
            entry = float(parts[4])
            block = float(parts[5])
            fail = parts[10]
            if entry > 0:
                evals.append((time_ict, strategy, entry, block, fail))

all_times = sorted(list(set(list(states.keys()) + [e[0] for e in evals])))

with open(out_path, 'w', encoding='utf-8') as f:
    f.write('| เวลา (ICT) | เหตุการณ์ / สภาวะตลาด | กลยุทธ์ (Strategy) | Entry Score | Block Score | สาเหตุที่ไม่ได้ยิง (Fail Reason) |\n')
    f.write('| :--- | :--- | :--- | :--- | :--- | :--- |\n')
    
    for t in all_times:
        if t in states:
            f.write(f'| **{t}** | 🟢 **เปลี่ยนเป็น: {states[t]}** | - | - | - | - |\n')
        for e in evals:
            if e[0] == t:
                f.write(f'| {t} | ประเมินคะแนน | `{e[1]}` | {e[2]} | {e[3]} | ❌ {e[4]} |\n')
