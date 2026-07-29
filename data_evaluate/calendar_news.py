"""
ff_calendar_fetch.py
====================
ดึงปฏิทินข่าว Forex Factory ทั้งวัน → export JSON
Output: data_base/calendar_news/calendar_YYYY-MM-DD.json

วิธีรัน:
    python ff_calendar_fetch.py              → ดึงข่าววันนี้
    python ff_calendar_fetch.py 2026-06-27   → ดึงข่าววันที่ระบุ
"""

import requests
import json
import sys
import os
import re
import traceback
from datetime import datetime, date
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo
from pathlib import Path
from bs4 import BeautifulSoup

# บังคับให้ Console พิมพ์ UTF-8
if getattr(sys.stdout, 'encoding', None) and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# ─────────────────────────────────────────
#  THAI DAY/MONTH MAPPING
# ─────────────────────────────────────────
THAI_DAYS = {
    0: "วันจันทร์", 1: "วันอังคาร", 2: "วันพุธ",
    3: "วันพฤหัสบดี", 4: "วันศุกร์", 5: "วันเสาร์", 6: "วันอาทิตย์"
}
THAI_MONTHS = {
    1: "มกราคม", 2: "กุมภาพันธ์", 3: "มีนาคม", 4: "เมษายน",
    5: "พฤษภาคม", 6: "มิถุนายน", 7: "กรกฎาคม", 8: "สิงหาคม",
    9: "กันยายน", 10: "ตุลาคม", 11: "พฤศจิกายน", 12: "ธันวาคม"
}

IMPACT_ICON = {
    "High":    "🔴 High   ",
    "Medium":  "🟡 Medium ",
    "Low":     "⚪ Low    ",
    "Holiday": "🔵 Holiday",
}

def log(msg: str = ""):
    """Print with timestamp prefix"""
    now = datetime.now().strftime("%Y-%m-%d T%H:%M:%S")
    print(f"[{now}] - {msg}")

def print_header(target_date: date):
    """พิมพ์ header สไตล์ FINALBOT"""
    now_str    = datetime.now().strftime("%Y-%m-%d T%H:%M:%S")
    thai_day   = THAI_DAYS[target_date.weekday()]
    thai_month = THAI_MONTHS[target_date.month]
    thai_year  = target_date.year + 543
    date_th    = f"{thai_day} ที่ {target_date.day} {thai_month} {thai_year}"
    width      = 80

    print()
    print("=" * width)
    print(f"[{now_str}] - [.FINALBOT_NEWS.]")
    print(f"[{now_str}] - [ระบบรายงานข่าวเศรษฐกิจและการเงิน : {date_th} : By Athena(Ai)]")
    print("=" * width)
    print(f"{'':>22}{'เวลา(ET)':<12}{'ข่าว':<38}{'สกุลเงิน':<10}{'ความรุนแรง':<12}{'Forecast':<12}{'Previous'}")
    print("-" * width)

def print_events(events: list[dict]):
    """พิมพ์ข่าวแต่ละรายการ"""
    now_str = datetime.now().strftime("%Y-%m-%d T%H:%M:%S")
    for e in events:
        # แปลง ISO datetime → แสดงแค่เวลา HH:MM
        try:
            dt = datetime.fromisoformat(e["date"])
            # แปลงกลับเป็นเวลา ET เพื่อแสดงใน Console ตามที่ระบุใน Header
            dt_et = dt.astimezone(ZoneInfo("America/New_York"))
            time_display = dt_et.strftime("%H:%M")
        except Exception as ex:
            time_display = "--:--"
            log(f"[ERROR] Date parse error: {ex}")

        impact_str = IMPACT_ICON.get(e["impact"], "⚪ Low    ")
        title_short = e["title"][:36]  # ตัดถ้าชื่อยาวเกิน
        forecast   = e.get("forecast", "") or "-"
        previous   = e.get("previous", "") or "-"

        line = (
            f"{time_display:<12}"
            f"{title_short:<38}"
            f"{e['country']:<10}"
            f"{impact_str:<14}"
            f"{forecast:<12}"
            f"{previous}"
        )
        print(f"[{now_str}] -  {line}")

def print_summary(events: list[dict], filepath: Path):
    """พิมพ์สรุปท้าย"""
    now_str = datetime.now().strftime("%Y-%m-%d T%H:%M:%S")
    high    = sum(1 for e in events if e["impact"] == "High")
    medium  = sum(1 for e in events if e["impact"] == "Medium")
    low     = sum(1 for e in events if e["impact"] in ("Low", "Holiday"))
    width   = 80

    print("-" * width)
    print(f"[{now_str}] - [สรุป] ข่าวทั้งหมด {len(events)} รายการ  |  🔴 High: {high}  🟡 Medium: {medium}  ⚪ Low: {low}")
    print(f"[{now_str}] - [บันทึกไฟล์] → {filepath}")
    print("=" * width)
    print()

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
OUTPUT_DIR = Path(__file__).resolve().parent / "data_base" / "calendar_news"

FF_URL = "https://www.forexfactory.com/calendar"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.forexfactory.com/",
    "Connection": "keep-alive",
}

# Impact mapping จาก class ของ FF
IMPACT_MAP = {
    "icon--ff-impact-red":    "High",
    "icon--ff-impact-ora":    "Medium",
    "icon--ff-impact-yel":    "Low",
    "icon--ff-impact-gra":    "Holiday",
}


# ─────────────────────────────────────────
#  FETCH
# ─────────────────────────────────────────
def fetch_calendar(target_date: date) -> list[dict]:
    """ดึงข่าวจาก Forex Factory สำหรับวันที่ระบุ"""

    # FF รับ query แบบ ?day=jun26.2026
    day_param = target_date.strftime("%b%d.%Y").lower()  # e.g. jun26.2026
    url = f"{FF_URL}?day={day_param}"

    log(f"[FETCH] กำลังดึงข้อมูล → {url}")

    try:
        session = requests.Session()
        # นำการยิง Request ไปหน้าแรกออกเพื่อลด Latency แต่เพิ่ม Timeout ป้องกัน Network แกว่ง
        response = session.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        log(f"[ERROR] Request failed: {e}")
        traceback.print_exc()
        raise RuntimeError(f"Network error fetching calendar: {e}")

    soup = BeautifulSoup(response.text, "html.parser")
    
    # ตรวจสอบว่าโดน Cloudflare บล็อกหรือไม่
    page_title = soup.title.text.lower() if soup.title else ""
    if "just a moment" in page_title or "cloudflare" in page_title:
        log("[ERROR] ถูกบล็อกโดยระบบป้องกันของเว็บ (Cloudflare / CAPTCHA)")
        raise RuntimeError("Blocked by Cloudflare")
        
    return parse_calendar(soup, target_date)


# ─────────────────────────────────────────
#  PARSE
# ─────────────────────────────────────────
def parse_calendar(soup: BeautifulSoup, target_date: date) -> list[dict]:
    """Parse HTML table → list of event dicts"""

    table = soup.find("table", class_=re.compile(r"calendar__table"))
    if not table:
        log("[WARN] ไม่พบตารางข่าว — FF อาจเปลี่ยน HTML structure")
        return []

    rows = table.find_all("tr", class_=re.compile(r"calendar__row"))
    events = []
    current_time_str = ""
    
    # Pre-compile regex เพื่อลดภาระ CPU (ประสิทธิภาพ 100%)
    re_time = re.compile(r"calendar__time")
    re_currency = re.compile(r"calendar__currency")
    re_impact = re.compile(r"calendar__impact")
    re_event = re.compile(r"calendar__event")
    re_forecast = re.compile(r"calendar__forecast")
    re_previous = re.compile(r"calendar__previous")

    for row in rows:
        # ─── เวลา ───────────────────────────────────────
        time_cell = row.find("td", class_=re_time)
        if time_cell:
            t = time_cell.get_text(strip=True)
            if t and t.lower() not in ("", "all day", "tentative"):
                current_time_str = t

        # ─── currency / country ──────────────────────────
        currency_cell = row.find("td", class_=re_currency)
        if not currency_cell:
            continue
        country = currency_cell.get_text(strip=True).upper()
        if not country:
            continue

        # ─── impact ─────────────────────────────────────
        impact = "Low"
        impact_cell = row.find("td", class_=re_impact)
        if impact_cell:
            span = impact_cell.find("span")
            if span:
                classes = span.get("class", [])
                for cls in classes:
                    if cls in IMPACT_MAP:
                        impact = IMPACT_MAP[cls]
                        break

        # ─── title ──────────────────────────────────────
        event_cell = row.find("td", class_=re_event)
        if not event_cell:
            continue
        title = event_cell.get_text(strip=True)
        if not title:
            continue

        # ─── forecast / previous ────────────────────────
        forecast_cell = row.find("td", class_=re_forecast)
        forecast = forecast_cell.get_text(strip=True) if forecast_cell else ""

        previous_cell = row.find("td", class_=re_previous)
        previous = previous_cell.get_text(strip=True) if previous_cell else ""

        # ─── build datetime string ──────────────────────
        date_str = _build_datetime(target_date, current_time_str)

        events.append({
            "title":    title,
            "country":  country,
            "date":     date_str,
            "impact":   impact,
            "forecast": forecast,
            "previous": previous,
        })

    log(f"[PARSE] พบข่าว {len(events)} รายการ")
    return events


def _build_datetime(target_date: date, time_str: str) -> str:
    """
    แปลง date + time string → ISO 8601 string (UTC)
    """
    time_str_clean = time_str.strip().lower()

    if not time_str_clean or time_str_clean in ("all day", "tentative", "") or time_str_clean.startswith("day"):
        dt_ny = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=ZoneInfo("America/New_York"))
        return dt_ny.astimezone(ZoneInfo("UTC")).isoformat()

    # ลอง format แรก: "jun 13th" (ForexFactor ส่งมาบางครั้ง)
    if "th" in time_str_clean or "st" in time_str_clean or "nd" in time_str_clean or "rd" in time_str_clean:
        try:
            # แปลง "jun 13th" → "06 13" แล้ว parse เป็น time
            parts = time_str_clean.split()
            if len(parts) >= 2:
                month_map = {
                    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
                }
                month_str = parts[0]
                day_str = parts[1]
                if month_str in month_map and day_str.isdigit():
                    month = month_map[month_str]
                    day = int(day_str)
                    # ตัด ordinal suffix เช่น "13th" → "13"
                    if "th" in day_str:
                        day = int(day_str.replace("th", ""))
                    elif "st" in day_str:
                        day = int(day_str.replace("st", ""))
                    elif "nd" in day_str:
                        day = int(day_str.replace("nd", ""))
                    elif "rd" in day_str:
                        day = int(day_str.replace("rd", ""))
                    # กลับมาใช้ logic เดิม แต่กำหนดเวลาเป็น 12:00 (เฉลี่ย)
                    t = datetime(target_date.year, month, day, 12, 0, 0)
                    return t.astimezone(ZoneInfo("America/New_York")).astimezone(ZoneInfo("UTC")).isoformat()
        except Exception as e:
            log(f"[WARN] Could not parse ordinal time '{time_str_clean}': {e}")

    try:
        t = datetime.strptime(time_str_clean, "%I:%M%p")
    except ValueError:
        try:
            t = datetime.strptime(time_str_clean, "%I%p")
        except ValueError:
            log(f"[WARN] Could not parse time string '{time_str_clean}', using 12:00am")
            t = datetime.strptime("12:00am", "%I:%M%p")

    # รวมวันที่และเวลา แล้วระบุว่ามันคือเวลาของนิวยอร์ก (จัดการ DST อัตโนมัติด้วย zoneinfo)
    dt_ny = datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        t.hour,
        t.minute,
        t.second,
        tzinfo=ZoneInfo("America/New_York")
    )

    # แปลงกลับเป็น UTC เพื่อการใช้งานที่เป็นมาตรฐาน
    return dt_ny.astimezone(ZoneInfo("UTC")).isoformat()


# ─────────────────────────────────────────
#  EXPORT
# ─────────────────────────────────────────
def export_json(events: list[dict], target_date: date) -> Path:
    """บันทึก JSON ลงไฟล์"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"calendar_{target_date.isoformat()}.json"
    filepath = OUTPUT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

    return filepath


# ─────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────
def main():
    # รับ argument วันที่ (optional)
    if len(sys.argv) > 1:
        try:
            target_date = date.fromisoformat(sys.argv[1])
        except ValueError:
            log(f"[ERROR] รูปแบบวันที่ไม่ถูกต้อง: {sys.argv[1]}  (ใช้ YYYY-MM-DD)")
            sys.exit(1)
    else:
        target_date = date.today()

    # Header
    print_header(target_date)

    log(f"[START] เริ่มดึงปฏิทินข่าว วันที่: {target_date}")

    events = fetch_calendar(target_date)

    if not events:
        log("[WARN] ไม่พบข่าว — บันทึก list ว่าง")

    # แสดงข่าวทุกรายการ
    print_events(events)

    # บันทึกไฟล์
    filepath = export_json(events, target_date)

    # สรุป
    print_summary(events, filepath)


if __name__ == "__main__":
    main()
