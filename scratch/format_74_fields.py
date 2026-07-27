import os
import yaml

folder = 'all_filelogs/logs_orchestrator/EURUSD-OTC'
files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.txt')]

# Find the latest file that has valid YAML format (space after ID:)
valid_file = None
for f in sorted(files, reverse=True):
    try:
        content = open(f, 'r', encoding='utf-8').read()
        parsed = yaml.safe_load(content)
        valid_file = f
        break
    except Exception:
        continue

print(f"Using file: {valid_file}")
content = open(valid_file, 'r', encoding='utf-8').read()
parsed = yaml.safe_load(content)

# Extract core analysis fields (excluding ID and meta header lines)
fields_list = []

def collect_fields(d, prefix=''):
    for k, v in d.items():
        if k in ['ID', 'meta']:
            continue
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            # Skip OHLCV subdict if present or handle recursively
            collect_fields(v, full_key)
        else:
            type_name = type(v).__name__
            fields_list.append((full_key, v, type_name))

collect_fields(parsed)

print(f"Total fields collected: {len(fields_list)}")
for idx, (name, val, dtype) in enumerate(fields_list, 1):
    print(f"{idx}. {name}: {val} ({dtype})")
