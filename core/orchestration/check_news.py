import os
import json
import requests
import traceback
import logging
from datetime import datetime, timezone

def check_news_impact(symbol="EURUSD"):
    """
    เช็คข่าวและรายงาน
    คืนค่า: "LOW", "MEDIUM", "HIGH"
    """
    try:
        now_utc = datetime.now(timezone.utc)
        today_str = now_utc.strftime("%Y-%m-%d")
        
        # 1. สร้างโฟลเดอร์ logs/calendar_logs อัตโนมัติ (ถ้ายังไม่มี)
        # หาตำแหน่ง root ของโปรเจกต์ (ขึ้นไปจาก core/orchestration)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        log_dir = os.path.join(base_dir, "logs", "calendar_logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # 2. กำหนดชื่อไฟล์ข่าวคือ logs/calendar_logs/calendar_{YYYY-MM-DD}.json
        calendar_file = os.path.join(log_dir, f"calendar_{today_str}.json")
        
        file_exists = os.path.exists(calendar_file)
        
        # ผู้ใช้งานตั้งใจให้ดึงจากไฟล์ในเครื่องแทนการยิง API เพื่อแก้ปัญหา 429 Too Many Requests
        if not file_exists:
            logging.warning(f"Calendar file {calendar_file} not found. Skipping web fetch.")
            return "LOW"
            
        # 4. (ต่อ) เปิดไฟล์ปฏิทินขึ้นมาโหลดข้อมูล Events เพื่อคำนวณหา Impact ต่อ
        with open(calendar_file, "r", encoding="utf-8") as f:
            events = json.load(f)
            
        upcoming_news = []
        past_news = []
        
        # Bug #2 fix: ลบ -OTC ออกก่อนเทียบสกุลเงิน
        clean_symbol = symbol.replace("-OTC", "")
        
        for event in events:
            date_str = event.get("date", "")
            if not date_str:
                continue
                
            try:
                # 5. ค่า event.get("date") จาก ForexFactory เป็น ISO string ที่ฝัง Timezone ไว้ 
                event_time = datetime.fromisoformat(date_str)
            except ValueError:
                continue
                
            # กรณีที่ข้อมูล timezone ไม่มี ให้ตั้งเป็น UTC ป้องกัน error ตอนเทียบกับ now_utc
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone.utc)
                
            time_diff = (event_time - now_utc).total_seconds() / 60  # นาที
            
            event_name = event.get("title", "Unknown")
            impact = event.get("impact", "Low")
            currency = event.get("country", "")
            forecast = event.get("forecast", "N/A")
            previous = event.get("previous", "N/A")
            
            # เช็คว่าเกี่ยวข้องกับคู่เงินเราไหม
            relevant = clean_symbol[:3] in currency or clean_symbol[3:] in currency
            
            if relevant:
                # ข่าวที่จะเกิดใน 30 นาทีข้างหน้า
                if 0 <= time_diff <= 30:
                    upcoming_news.append({
                        "name": event_name,
                        "time": event_time.strftime("%H:%M"),
                        "impact": impact,
                        "in_minutes": int(time_diff)
                    })
                
                # ข่าวที่เกิดไปแล้วไม่เกิน 15 นาที
                elif -15 <= time_diff < 0:
                    actual = event.get("actual", "N/A")
                    past_news.append({
                        "name": event_name,
                        "time": event_time.strftime("%H:%M"),
                        "impact": impact,
                        "minutes_ago": int(abs(time_diff)),
                        "forecast": forecast,
                        "previous": previous,
                        "actual": actual
                    })
                    
        # ตรวจสอบว่ามี High impact ไหม
        all_news = upcoming_news + past_news
        has_high = any(n['impact'] == "High" for n in all_news)
        has_medium = any(n['impact'] == "Medium" for n in all_news)
        
        if has_high:
            return "HIGH"
        elif has_medium:
            return "MEDIUM"
        else:
            return "LOW"
            
    except Exception as e:
        logging.exception("Error checking news impact")
        traceback.print_exc()
        return "LOW"

if __name__ == "__main__":
    result = check_news_impact("EURUSD")
    print(f"Result: {result}")

