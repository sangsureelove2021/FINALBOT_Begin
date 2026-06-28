import os
import json
import requests
import traceback
import logging
from datetime import datetime, timezone

_PRECALCULATED_NEWS = {}
_LAST_CALENDAR_DATE = None
_EVENTS_CACHE = []

def update_all_news_impact(symbols: list):
    """
    คำนวณและอัปเดตผลกระทบข่าวล่วงหน้าสำหรับทุกคู่เงิน
    ถูกเรียกโดย runner.py ทุกๆ 1 นาที
    """
    global _PRECALCULATED_NEWS, _LAST_CALENDAR_DATE, _EVENTS_CACHE
    try:
        now_utc = datetime.now(timezone.utc)
        today_str = now_utc.strftime("%Y-%m-%d")
        
        # โหลดไฟล์ JSON เฉพาะเมื่อยังไม่มีข้อมูลของวันนี้
        if _LAST_CALENDAR_DATE != today_str:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            log_dir = os.path.join(base_dir, "logs", "calendar_logs")
            calendar_file = os.path.join(log_dir, f"calendar_{today_str}.json")
            
            if not os.path.exists(calendar_file):
                logging.info(f"Calendar file for {today_str} not found (Day Rollover). Auto-fetching...")
                script_path = os.path.join(base_dir, "calendar_news.py")
                if os.path.exists(script_path):
                    import subprocess
                    import sys
                    try:
                        subprocess.run([sys.executable, script_path], check=False, timeout=60)
                        logging.info("Auto-fetch completed.")
                    except subprocess.TimeoutExpired as e:
                        logging.error("Auto-fetch news timed out after 60 seconds")
                        raise Exception("Auto-fetch news timed out after 60 seconds") from e
                    except Exception as e:
                        logger.exception(str(e))
                        raise Exception(str(e))
            
            if os.path.exists(calendar_file):
                try:
                    with open(calendar_file, "r", encoding="utf-8") as f:
                        _EVENTS_CACHE = json.load(f)
                    _LAST_CALENDAR_DATE = today_str
                except json.JSONDecodeError as e:
                    logging.error(f"Calendar JSON is corrupt: {e}. Removing file.")
                    os.remove(calendar_file)
                    raise Exception(f"Calendar JSON is corrupt: {e}") from e
            else:
                logging.warning(f"Calendar file {calendar_file} not found even after auto-fetch. Using empty events.")
                _EVENTS_CACHE = []
                _LAST_CALENDAR_DATE = today_str
        
        # คำนวณทีละคู่เงิน
        for symbol in symbols:
            # 1. จัดการ OTC
            if "OTC" in symbol.upper():
                _PRECALCULATED_NEWS[symbol] = "NONE (OTC)"
                continue
            
            # ถ้าไม่มีไฟล์ข่าว ให้ตั้งเป็น UNKNOWN
            if not _EVENTS_CACHE:
                raise Exception(f"No news events available for symbol {symbol}")
                
            clean_symbol = symbol.upper().replace("-OTC", "").replace("_OTC", "")
            upcoming_news = []
            past_news = []
            
            for event in _EVENTS_CACHE:
                date_str = event["date"]
                if not date_str:
                    continue
                    
                event_time = datetime.fromisoformat(date_str)
                    
                if event_time.tzinfo is None:
                    event_time = event_time.replace(tzinfo=timezone.utc)
                    
                time_diff = (event_time - now_utc).total_seconds() / 60
                impact = event["impact"]
                currency = event["country"]
                
                relevant = clean_symbol[:3] in currency or clean_symbol[3:] in currency
                if relevant:
                    if 0 <= time_diff <= 30:
                        upcoming_news.append({"impact": impact})
                    elif -15 <= time_diff < 0:
                        past_news.append({"impact": impact})
                        
            all_news = upcoming_news + past_news
            
            has_high = any(n['impact'].strip().upper() == "HIGH" for n in all_news)
            has_medium = any(n['impact'].strip().upper() == "MEDIUM" for n in all_news)
            
            if has_high:
                _PRECALCULATED_NEWS[symbol] = "HIGH"
            elif has_medium:
                _PRECALCULATED_NEWS[symbol] = "MEDIUM"
            else:
                _PRECALCULATED_NEWS[symbol] = "LOW"
                
    except Exception as e:
        logger.exception(str(e))
        raise Exception(str(e))

def check_news_impact(symbol="EURUSD"):
    """
    ดึงข้อมูลผลกระทบข่าวที่คำนวณไว้แล้ว (Instant Lookup)
    สำหรับ OTC จะไม่มีข่าวจริง จึงกำหนดเป็น 'NONE_OTC' เพื่อแยกจากคู่เงินปกติ
    """
    if not isinstance(symbol, str):
        return 'NONE_OTC'
    if "OTC" in symbol.upper():
        return 'NONE_OTC'
    if symbol not in _PRECALCULATED_NEWS:
        return 'UNKNOWN'
    return _PRECALCULATED_NEWS[symbol]

if __name__ == "__main__":
    result = check_news_impact("EURUSD")
    print(f"Result: {result}")

