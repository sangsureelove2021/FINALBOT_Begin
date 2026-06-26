"""
ff_calendar_fetch.py
====================
ดึงปฏิทินข่าว Forex Factory ทั้งวัน → export JSON
Output: E:\\BOT_FINALBOT13 STG\\BOT_FINALBOT\\logs\\calendar_logs\\calendar_YYYY-MM-DD.json

วิธีรัน:
    python ff_calendar_fetch.py              → ดึงข่าววันนี้
    python ff_calendar_fetch.py 2026-06-27   → ดึงข่าววันที่ระบุ
"""

import requests
import json
import sys
import os
import re
from datetime import datetime, date
from pathlib import Path
from bs4 import BeautifulSoup

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
    print(f"[{now_str}] - [ระบบรายงานข่าวเศรษฐกิจและการเงิน : {date_th} : By Joy Anthropic(Ai)]")
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
            time_display = dt.strftime("%H:%M")
        except Exception:
            time_display = "--:--"

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
OUTPUT_DIR = Path(r"E:\BOT_FINALBOT13 STG\BOT_FINALBOT\logs\calendar_logs")

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
        session.get("https://www.forexfactory.com/", headers=HEADERS, timeout=15)
        response = session.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        log(f"[ERROR] Request failed: {e}")
        return []

    soup = BeautifulSoup(response.text, "lxml")
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
    current_time_str = ""   # FF ไม่แสดง time ซ้ำในทุก row

    for row in rows:
        # ─── เวลา ───────────────────────────────────────
        time_cell = row.find("td", class_=re.compile(r"calendar__time"))
        if time_cell:
            t = time_cell.get_text(strip=True)
            if t and t.lower() not in ("", "all day", "tentative"):
                current_time_str = t  # เก็บเวลาล่าสุด

        # ─── currency / country ──────────────────────────
        currency_cell = row.find("td", class_=re.compile(r"calendar__currency"))
        if not currency_cell:
            continue
        country = currency_cell.get_text(strip=True).upper()
        if not country:
            continue

        # ─── impact ─────────────────────────────────────
        impact = "Low"
        impact_cell = row.find("td", class_=re.compile(r"calendar__impact"))
        if impact_cell:
            span = impact_cell.find("span")
            if span:
                classes = span.get("class", [])
                for cls in classes:
                    if cls in IMPACT_MAP:
                        impact = IMPACT_MAP[cls]
                        break

        # ─── title ──────────────────────────────────────
        event_cell = row.find("td", class_=re.compile(r"calendar__event"))
        if not event_cell:
            continue
        title = event_cell.get_text(strip=True)
        if not title:
            continue

        # ─── forecast / previous ────────────────────────
        forecast_cell = row.find("td", class_=re.compile(r"calendar__forecast"))
        forecast = forecast_cell.get_text(strip=True) if forecast_cell else ""

        previous_cell = row.find("td", class_=re.compile(r"calendar__previous"))
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
    แปลง date + time string → ISO 8601 string
    FF ใช้ Eastern Time (ET) = UTC-4 (EDT) / UTC-5 (EST)
    """
    # ตรวจ DST แบบง่าย: EDT (Mar-Nov) = -04:00, EST (Nov-Mar) = -05:00
    month = target_date.month
    offset = "-04:00" if 3 <= month <= 11 else "-05:00"

    # parse time เช่น "8:30am", "10:00am", "All Day"
    time_str_clean = time_str.strip().lower()

    if not time_str_clean or time_str_clean in ("all day", "tentative", ""):
        return f"{target_date.isoformat()}T00:00:00{offset}"

    try:
        # รองรับ "8:30am", "12:00pm" ฯลฯ
        t = datetime.strptime(time_str_clean, "%I:%M%p")
        time_part = t.strftime("%H:%M:%S")
    except ValueError:
        try:
            t = datetime.strptime(time_str_clean, "%I%p")
            time_part = t.strftime("%H:%M:%S")
        except ValueError:
            time_part = "00:00:00"

    return f"{target_date.isoformat()}T{time_part}{offset}"


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
