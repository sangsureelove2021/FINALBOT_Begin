import json
import os
import re

src_path = r"C:\Users\BUSOLOVE\.gemini\antigravity\brain\ee6003a8-808d-4ba1-a615-4fecf92d7738\.system_generated\logs\transcript.jsonl"
dest_path = r"e:\BOT_FINALBOT13 STG\BOT_FINALBOT_NEW\สนทนา_v2.0.txt"

def clean_xml_tags(text):
    # Remove XML tags like <USER_REQUEST> or <ADDITIONAL_METADATA> ...
    text = re.sub(r'<USER_REQUEST>.*?</USER_REQUEST>', lambda m: m.group(0).replace('<USER_REQUEST>', '').replace('</USER_REQUEST>', ''), text, flags=re.DOTALL)
    # Remove metadata completely for clean look
    text = re.sub(r'<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>', '', text, flags=re.DOTALL)
    return text.strip()

if os.path.exists(src_path):
    with open(src_path, 'r', encoding='utf-8') as f_in, open(dest_path, 'w', encoding='utf-8') as f_out:
        f_out.write("=== ประวัติการสนทนาจาก Session 2.0 (ee6003a8-808d-4ba1-a615-4fecf92d7738) ===\n")
        for line in f_in:
            try:
                data = json.loads(line)
                source = data.get('source', '')
                dtype = data.get('type', '')
                content = data.get('content', '')
                
                if source == 'USER_EXPLICIT' and dtype == 'USER_INPUT':
                    cleaned_content = clean_xml_tags(content)
                    if cleaned_content:
                        f_out.write(f"\n[ บอส ]: {cleaned_content}\n")
                elif source == 'MODEL' and dtype == 'PLANNER_RESPONSE':
                    # Extract content and remove thinking process if any
                    if 'thinking' in data:
                        # Sometimes content is already clean
                        pass
                    f_out.write(f"\n[ เอเธน่า ]: {content.strip()}\n")
                    f_out.write("-" * 50 + "\n")
            except Exception as e:
                pass
    print("Successfully extracted chat to สนทนา_v2.0.txt")
else:
    print("Source path does not exist")
