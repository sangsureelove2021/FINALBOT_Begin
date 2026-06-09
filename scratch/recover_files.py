import json
import glob
import os

logs = [
    r"C:\Users\Administrator\.gemini\antigravity\brain\7f57090e-5c34-4a85-9a39-b4b18f640209\.system_generated\logs\transcript.jsonl",
    r"C:\Users\Administrator\.gemini\antigravity\brain\9d7880de-bc74-4a91-9bb9-070ae00a2d60\.system_generated\logs\transcript.jsonl"
]

for log in logs:
    if not os.path.exists(log):
        continue
    with open(log, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                if 'tool_calls' in data:
                    for tc in data['tool_calls']:
                        if tc['function']['name'] == 'default_api:write_to_file':
                            args = tc['function']['arguments']
                            if isinstance(args, str):
                                args = json.loads(args)
                            target = args.get('TargetFile')
                            content = args.get('CodeContent')
                            if target and content and 'reversal_strategy' in target:
                                # Fix df_m5 bug automatically during recovery
                                content = content.replace('df_m5', 'df')
                                print(f"Recovering {target}")
                                with open(target, 'w', encoding='utf-8') as out:
                                    out.write(content)
            except Exception as e:
                pass
