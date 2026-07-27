import os
import yaml

folder = 'all_filelogs/logs_orchestrator/EURUSD-OTC'
latest = os.path.join(folder, sorted(os.listdir(folder))[-1])
print(f"Auditing File: {latest}")

content = open(latest, 'r', encoding='utf-8').read()
lines = content.split('\n')
parsed = yaml.safe_load(content)

print("\n--- FIELD BY FIELD AUDIT ---")
field_count = 0
nans = []
nulls = []

def walk(d, prefix=''):
    global field_count
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            walk(v, full_key)
        else:
            field_count += 1
            val_str = str(v).lower()
            if 'nan' in val_str:
                nans.append((full_key, v))
            if val_str == 'none' and full_key not in ['price_action.pattern', 'price_action.trap_alert', 'analysis.trend_direction']:
                nulls.append((full_key, v))
            print(f"[{field_count:02d}] {full_key:<45} | Type: {type(v).__name__:<8} | Value: {v}")

walk(parsed)

print("\n--- SUMMARY REPORT ---")
print(f"Total Fields Counted: {field_count}")
print(f"Total Lines Counted : {len(lines)}")
print(f"NaN Values Detected : {len(nans)}")
print(f"Null Values Detected: {len(nulls)}")
