import pandas as pd
import os

report_path = r"C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\docs\GBPUSD_may_7_backtest_report.md"
output_path = r"C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT\docs\GBPUSD_May7_Timeline.md"

states = {}
evaluations = {}

with open(report_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

in_states = False
in_evals = False

for line in lines:
    if line.startswith("## 1. Market"):
        in_states = True
        in_evals = False
        continue
    if line.startswith("## 2. Detailed"):
        in_states = False
        in_evals = True
        continue
        
    if in_states and line.startswith("| 2026"):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 4:
            time_ict = parts[1]
            new_state = parts[3]
            states[time_ict] = new_state
            
    if in_evals and line.startswith("| 2026"):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 12:
            time_ict = parts[1]
            strategy = parts[2]
            entry = float(parts[4])
            block = float(parts[5])
            fail = parts[10]
            
            # Filter out the boring 0.0 entry ones that just say MARKET_STATE_BLOCKED
            # unless we want to show everything. The user said "ทุก ที่ ตลาดเปลี่ยน ..ตลาด เรียกกลยุทธ์ กลยุทธ์ ใด มีคะแนนเท่าไหร่"
            # We will show everything, but keep it concise per timestamp.
            if time_ict not in evaluations:
                evaluations[time_ict] = []
            evaluations[time_ict].append((strategy, entry, block, fail))

# Get all unique timestamps
all_times = sorted(list(set(list(states.keys()) + list(evaluations.keys()))))

current_state = "UNKNOWN"

with open(output_path, 'w', encoding='utf-8') as out:
    out.write("# ไทม์ไลน์การทำงานของบอทแบบละเอียด (GBPUSD - 7 พ.ค. 2026)\n\n")
    out.write("รายงานนี้แสดงเหตุการณ์ตามลำดับเวลา ว่าเมื่อใดที่ตลาดเปลี่ยนสภาวะ และในแต่ละช่วงเวลานั้น บอทเรียกใช้กลยุทธ์ใดบ้าง ได้คะแนนเท่าไหร่ และทำไมถึงไม่ได้ยิงออเดอร์\n\n")
    
    for t in all_times:
        if t in states:
            current_state = states[t]
            out.write(f"\n## 🕒 {t} \n")
            out.write(f"**🟢 สภาวะตลาดเปลี่ยนเป็น: {current_state}**\n\n")
            out.write(f"กลยุทธ์ที่เข้ามาประเมินในช่วงเวลานี้:\n")
            
        # Check if there are evaluations at this timestamp
        if t in evaluations:
            # If no state change happened exactly at this minute, but we have evals, we can optionally print the time
            if t not in states:
                # We only print the header if there are non-zero score evaluations, to save space, 
                # OR we print it anyway because user wants EVERYTHING.
                # Since the file might be huge, let's print all but indent them.
                out.write(f"\n### ⏱️ {t} (สภาวะ: {current_state})\n")
            
            for eval_data in evaluations[t]:
                strategy, entry, block, fail = eval_data
                
                # Format nicely
                if entry > 0:
                    icon = "🔥"
                    entry_text = f"**Entry: {entry}**"
                else:
                    icon = "➖"
                    entry_text = f"Entry: {entry}"
                    
                if fail != "N/A" and fail != "":
                    reason = f"-> ❌ โดนบล็อกเพราะ: {fail}"
                else:
                    reason = "-> ✅ ยิงออเดอร์!"
                    
                out.write(f"- {icon} `{strategy}` | {entry_text} | Block: {block} {reason}\n")

print(f"Timeline written to {output_path}")
