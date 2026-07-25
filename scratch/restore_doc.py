import json
import re
import os

transcript_path = r"C:\Users\BUSOLOVE\.gemini\antigravity\brain\7ce830e2-7637-474f-918f-111454a3eae9\.system_generated\logs\transcript_full.jsonl"
target_path = r"E:\BOT_FINALBOT13 STG\BOT_FINALBOT_NEW\docs\About_Me\กระบวนการทำงานของบอท ส่วนที่ 1 INPUT\กระบวนการทำงานของบอท - ส่วนที่ 1 INPUT - รวมเอกสาร.md"

def restore():
    if not os.path.exists(transcript_path):
        print(f"Transcript path not found: {transcript_path}")
        return
        
    lines_content = []
    
    # Read transcript_full.jsonl line by line
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("type") == "VIEW_FILE" and "Showing lines 1 to 629" in data.get("content", ""):
                    content = data["content"]
                    # Extract the lines
                    for file_line in content.split("\n"):
                        match = re.match(r"^(\d+):\s?(.*)$", file_line)
                        if match:
                            lines_content.append(match.group(2))
            except Exception as e:
                pass
                
    if not lines_content:
        print("Failed to find file contents in transcript.")
        return

    # Join the lines
    full_text = "\n".join(lines_content)
    
    # Insert the rules section after "บันทึกข้อมูลแบบ **Async (ไม่บล็อกหลัก)** อย่างรวดเร็ว"
    target_phrase = "บันทึกข้อมูลแบบ **Async (ไม่บล็อกหลัก)** อย่างรวดเร็ว"
    rules_text = (
        "\n\n## 🚨 กฎการทำงานของบอท\n"
        "- หากระบบทำงานผิดพลาด ให้แสดง Error ที่คอนโซล หยุดทำงาน และบันทึกรายงานความผิดพลาดไว้ที่ `\\all_filelogs\\logs_datafeed` ห้ามมีระบบ Fallback ระบบต้องมีเพียงหนึ่งเดียวที่ทำงานได้ถูกต้อง\n"
        "- ห้ามสร้างระบบให้มี Mock การทำงาน หรือการทดสอบต้องมาจากระบบจริง ทุกอย่างต้องรันจริง\n"
        "- หากเปลี่ยนแปลง แก้ไข ข้อมูล ข้อความ โค้ด หรือสิ่งต่าง ๆ ในบอท เอกสารนี้ต้องได้รับการแก้ไข อัปเดตตามจริง"
    )
    
    if target_phrase in full_text:
        if "กฎการทำงานของบอท" not in full_text:
            idx = full_text.find(target_phrase) + len(target_phrase)
            full_text = full_text[:idx] + rules_text + full_text[idx:]
            print("Successfully inserted rules section.")
    else:
        print("Could not find the target phrase to insert rules.")
        
    # Make sure folder exists
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    # Write to destination
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(full_text)
    print(f"Successfully restored file to {target_path}")

if __name__ == "__main__":
    restore()
