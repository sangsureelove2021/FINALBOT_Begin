import json
import os

transcript_path = r"C:\Users\BUSOLOVE\.gemini\antigravity\brain\7ce830e2-7637-474f-918f-111454a3eae9\.system_generated\logs\transcript_full.jsonl"

with open(transcript_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        try:
            data = json.loads(line)
            content = data.get("content", "")
            if "Showing lines 1 to 629" in content or "กระบวนการทำงานของบอท" in content:
                print(f"Line {i}: keys: {list(data.keys())}, type: {data.get('type')}, source: {data.get('source')}")
                print(content[:200])
                print("-" * 50)
        except Exception as e:
            print(f"Error parsing line {i}: {e}")
