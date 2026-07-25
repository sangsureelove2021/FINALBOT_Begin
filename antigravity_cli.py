
import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

# 1. โหลดค่าคอนฟิกจากไฟล์ .env
load_dotenv()

ENV_FILE = ".env"
api_key = os.getenv("GEMINI_API_KEY")

# 2. ถ้าไม่มี GEMINI_API_KEY ใน .env ให้ถามเจ้านายและบันทึกให้
if not api_key:
    print("=== ตรวจไม่พบ GEMINI_API_KEY ===")
    print("1. ไปที่หน้าเว็บ Google AI Studio (aistudio.google.com) เพื่อขอคีย์ฟรี")
    print("2. กดปุ่ม 'Get API key'")
    print("3. คัดลอกคีย์มาวางที่นี่\n")
    
    user_key = input("วาง GEMINI_API_KEY ของคุณที่นี่: ").strip()
    if not user_key:
        print("ข้อผิดพลาด: คีย์ว่างเปล่า")
        sys.exit(1)
        
    # เขียนลงไฟล์ .env
    try:
        existing_lines = []
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()
        
        new_lines = [line for line in existing_lines if not line.startswith("GEMINI_API_KEY=")]
        new_lines.append(f"GEMINI_API_KEY={user_key}\n")
        
        with open(ENV_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
        print(f"\n[สำเร็จ] บันทึก API Key ลงในไฟล์ {ENV_FILE} เรียบร้อยแล้ว!")
        api_key = user_key
    except Exception as e:
        print(f"ไม่สามารถเขียนไฟล์ .env ได้: {e}")
        sys.exit(1)

# 3. ตั้งค่าการเชื่อมต่อกับ Gemini
try:
    genai.configure(api_key=api_key)
    # ใช้โมเดล gemini-1.5-flash ที่ทำงานได้เร็วและฟรี
    model = genai.GenerativeModel('gemini-1.5-flash')
    chat = model.start_chat(history=[])
except Exception as e:
    print(f"เกิดข้อผิดพลาดในการตั้งค่า Gemini: {e}")
    sys.exit(1)

print("\n==============================================")
print("   ยินดีต้อนรับสู่ Antigravity CLI (Gemini Engine)")
print("   พิมพ์คำถามของคุณ และกด Enter เพื่อคุย (ฟรี 100%)")
print("   (พิมพ์ 'exit' หรือ 'quit' เพื่อออกจากโปรแกรม)")
print("==============================================\n")

def show_help():
    print("คีย์ลัดพิเศษสำหรับบอทเทรด:")
    print("  /code <ชื่อไฟล์>     - ส่งโค้ดในโปรเจกต์ให้ AI ช่วยตรวจ (เช่น /code runner.py)")
    print("  /market <ชื่อคู่เงิน> - ส่งค่าอินดิเคเตอร์ล่าสุดให้ AI วิเคราะห์ (เช่น /market EURUSD-OTC)")
    print("  /logs [ชื่อไฟล์]     - ดึงไฟล์ Log ล่าสุด (หรือไฟล์ที่ระบุ) มาวิเคราะห์")
    print("  exit หรือ quit     - ออกจากโปรแกรม\n")

show_help()

while True:
    try:
        user_message = input("คุณ: ").strip()
        if not user_message:
            continue
            
        if user_message.lower() in ["exit", "quit"]:
            print("ลาก่อนครับเจ้านาย!")
            break

        prompt = user_message

        # ตรวจสอบคำสั่งพิเศษ
        if user_message.startswith("/"):
            parts = user_message.split(" ", 1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd == "/code":
                if not arg:
                    print("กรุณาระบุชื่อไฟล์ เช่น: /code runner.py\n")
                    continue
                if not os.path.exists(arg):
                    print(f"ไม่พบไฟล์ {arg} ในโฟลเดอร์นี้\n")
                    continue
                
                print(f"กำลังอ่านไฟล์ {arg}...")
                with open(arg, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                prompt = f"นี่คือโค้ดไฟล์ {arg} ของบอท ช่วยตรวจหาข้อผิดพลาด แนะนำแนวทางปรับปรุง หรืออธิบายการทำงานให้หน่อย:\n\n```python\n{content}\n```"

            elif cmd == "/market":
                symbol = arg if arg else "EURUSD-OTC"
                json_path = f"all_filelogs/market_state/market_state_{symbol}.json"
                if not os.path.exists(json_path):
                    json_path = "all_filelogs/market_state/market_state.json"
                
                if not os.path.exists(json_path):
                    print(f"ไม่พบไฟล์ข้อมูลตลาดของ {symbol} ในโฟลเดอร์ all_filelogs/\n")
                    continue
                
                print(f"กำลังอ่านสถานะตลาดล่าสุดจาก {json_path}...")
                with open(json_path, "r", encoding="utf-8") as f:
                    market_data = f.read()

                prompt = f"นี่คือข้อมูลสถานะตลาดล่าสุดของคู่เงิน {symbol} ที่บอทบันทึกไว้ ช่วยวิเคราะห์แนวโน้มตลาดและบอกจุดเด่นทางเทคนิคตามอินดิเคเตอร์เหล่านี้ให้หน่อย:\n\n```json\n{market_data}\n```"

            elif cmd == "/logs":
                log_file_path = arg
                if not log_file_path:
                    # ถ้าไม่ระบุไฟล์ ให้หาไฟล์ล่าสุดในโฟลเดอร์ all_filelogs/system_logs ตามเดิม
                    log_dir = "all_filelogs/system_logs"
                    if not os.path.exists(log_dir):
                        print("ไม่พบโฟลเดอร์ all_filelogs/system_logs/\n")
                        continue
                    
                    log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir) if f.endswith((".log", ".txt"))]
                    if not log_files:
                        print("ไม่พบไฟล์ .log หรือ .txt ในโฟลเดอร์ all_filelogs/system_logs/\n")
                        continue
                    
                    log_file_path = max(log_files, key=os.path.getmtime)

                if not os.path.exists(log_file_path):
                    print(f"ไม่พบไฟล์ Log ที่ระบุ: {log_file_path}\n")
                    continue

                print(f"กำลังอ่าน Log: {log_file_path} (อ่าน 150 บรรทัดสุดท้าย)...")
                with open(log_file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                last_lines = "".join(lines[-150:])
                prompt = f"นี่คือ Log ล่าสุดของบอทเทรด (150 บรรทัดสุดท้าย) ช่วยตรวจสอบว่ามี Error อะไรเกิดขึ้นไหม หรือบอททำงานปกติอย่างไรบ้าง:\n\n```text\n{last_lines}\n```"
                
            else:
                print(f"ไม่รู้จักคำสั่ง {cmd}")
                show_help()
                continue
        
        print("Antigravity กำลังคิด...", end="\r")
        
        response = chat.send_message(prompt)
        
        print(" " * 30, end="\r")
        print(f"Antigravity: {response.text}\n")
        
    except KeyboardInterrupt:
        print("\nลาก่อนครับเจ้านาย!")
        break
    except Exception as e:
        print(f"\nเกิดข้อผิดพลาด: {e}\n")
