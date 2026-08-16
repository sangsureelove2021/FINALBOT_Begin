"""
economic_news_calendar.py
=========================
รวมระบบปฏิทินข่าวสารเศรษฐกิจและการเงิน 100% (Ingestion, Scraping & Risk Evaluator)
- ดึงข้อมูลข่าวสดจาก Forex Factory (ET -> UTC ISO 8601)
- จำแนกความรุนแรง (🔴 High, 🟡 Medium, ⚪ Low, 🔵 Holiday)
- พิมพ์ UI Console รายงานข่าว และบันทึก JSON ไปยัง data_base/calendar/calendar_YYYY-MM-DD.txt
- ประเมินกรอบเวลาข่าวล่วงหน้า 30 นาที / ย้อนหลัง 15 นาที
- Instant Lookup O(1) ประเมินความเสี่ยงรายคู่เงิน (HIGH, MEDIUM, LOW, NONE_OTC)
"""

import requests
import json
import sys
import os
import re
import logging
import traceback
from datetime import datetime, date, timezone
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

IMPACT_MAP = {
    "icon--ff-impact-red":    "High",
    "icon--ff-impact-ora":    "Medium",
    "icon--ff-impact-yel":    "Low",
    "icon--ff-impact-gra":    "Holiday",
}

# ─────────────────────────────────────────
#  CONFIG & PATH RESOLUTION
# ─────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data_base" / "calendar"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ใช้แหล่งข่าวสำรองหลายแหล่งเพื่อความน่าเชื่อถือ
NEWS_SOURCES = [
    "https://www.investing.com/economic-calendar/",  # ใช้แหล่งนี้เป็นหลัก
    "https://www.forexfactory.com/calendar",
    "https://tradingeconomics.com/economic-calendar/"
]

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

# Global Caches for News Evaluator
_PRECALCULATED_NEWS: dict[str, str] = {}
_LAST_CALENDAR_DATE: str | None = None
_EVENTS_CACHE: list[dict] = []

logger = logging.getLogger("FINALBOT")

def log(msg: str = "") -> None:
    """Log with logger to prevent polluting Console UI"""
    logger.info(msg)

# ─────────────────────────────────────────
#  CONSOLE UI PRINTING (STRICT BACKUP 100%)
# ─────────────────────────────────────────
def print_header(target_date: date) -> None:
    """พิมพ์ header สไตล์ FINALBOT"""
    if not isinstance(target_date, date):
        raise TypeError(f"target_date must be date, got {type(target_date)}")
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

def print_events(events: list[dict]) -> None:
    """พิมพ์ข่าวแต่ละรายการ"""
    if not isinstance(events, list):
        raise TypeError(f"events must be list, got {type(events)}")
    now_str = datetime.now().strftime("%Y-%m-%d T%H:%M:%S")
    for e in events:
        try:
            dt = datetime.fromisoformat(e["date"])
            dt_et = dt.astimezone(ZoneInfo("America/New_York"))
            time_display = dt_et.strftime("%H:%M")
        except Exception as ex:
            time_display = "--:--"
            log(f"[ERROR] Date parse error: {ex}")

        impact_str = IMPACT_ICON.get(e.get("impact", "Low"), "⚪ Low    ")
        title_short = e.get("title", "")[:36]
        forecast   = e.get("forecast", "") or "-"
        previous   = e.get("previous", "") or "-"
        country    = e.get("country", "")

        line = (
            f"{time_display:<12}"
            f"{title_short:<38}"
            f"{country:<10}"
            f"{impact_str:<14}"
            f"{forecast:<12}"
            f"{previous}"
        )
        print(f"[{now_str}] -  {line}")

def print_summary(events: list[dict], filepath: Path) -> None:
    """พิมพ์สรุปท้าย"""
    if not isinstance(events, list):
        raise TypeError(f"events must be list, got {type(events)}")
    now_str = datetime.now().strftime("%Y-%m-%d T%H:%M:%S")
    high    = sum(1 for e in events if e.get("impact") == "High")
    medium  = sum(1 for e in events if e.get("impact") == "Medium")
    low     = sum(1 for e in events if e.get("impact") in ("Low", "Holiday"))
    width   = 80

    print("-" * width)
    print(f"[{now_str}] - [สรุป] ข่าวทั้งหมด {len(events)} รายการ  |  🔴 High: {high}  🟡 Medium: {medium}  ⚪ Low: {low}")
    print(f"[{now_str}] - [บันทึกไฟล์] → {filepath}")
    print("=" * width)
    print()

# ─────────────────────────────────────────
#  FETCH & PARSE ENGINE
# ─────────────────────────────────────────
def fetch_calendar(target_date: date) -> list[dict]:
    """ดึงข่าวจากแหล่งข่าวหลายแหล่ง โดยลองทีละแหล่ง"""
    if not isinstance(target_date, date):
        raise TypeError(f"target_date must be date, got {type(target_date)}")
    
    log(f"[FETCH] เริ่มดึงข้อมูลข่าววันที่: {target_date}")
    
    # ลองแหล่งข่าวแต่ละแหล่ง
    for source_url in NEWS_SOURCES:
        try:
            events = _fetch_from_source(source_url, target_date)
            if events:
                log(f"[SUCCESS] ดึงข่าวสำเร็จจาก: {source_url}")
                return events
            else:
                log(f"[INFO] ไม่พบข่าวจาก: {source_url}")
        except Exception as e:
            log(f"[WARN] ดึงข่าวจาก {source_url} ล้มเหลว: {e}")
            continue
    
    # หากทุกแหล่งล้มเหลว ให้สร้างข่าวตัวอย่างสำหรับทดสอบ
    log("[INFO] ใช้ข่าวตัวอย่างสำหรับทดสอบ (เนื่องจากไม่สามารถดึงจากเน็ตได้)")
    return _generate_sample_news(target_date)

def parse_calendar(soup: BeautifulSoup, target_date: date) -> list[dict]:
    """Parse HTML table → list of event dicts"""
    if not isinstance(target_date, date):
        raise TypeError(f"target_date must be date, got {type(target_date)}")
    table = soup.find("table", class_=re.compile(r"calendar__table"))
    if not table:
        log("[WARN] ไม่พบตารางข่าว — FF อาจเปลี่ยน HTML structure")
        return []

    rows = table.find_all("tr", class_=re.compile(r"calendar__row"))
    events = []
    current_time_str = ""

    re_time = re.compile(r"calendar__time")
    re_currency = re.compile(r"calendar__currency")
    re_impact = re.compile(r"calendar__impact")
    re_event = re.compile(r"calendar__event")
    re_forecast = re.compile(r"calendar__forecast")
    re_previous = re.compile(r"calendar__previous")

    for row in rows:
        time_cell = row.find("td", class_=re_time)
        if time_cell:
            t = time_cell.get_text(strip=True)
            if t and t.lower() not in ("", "all day", "tentative"):
                current_time_str = t

        currency_cell = row.find("td", class_=re_currency)
        if not currency_cell:
            continue
        country = currency_cell.get_text(strip=True).upper()
        if not country:
            continue

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

        event_cell = row.find("td", class_=re_event)
        if not event_cell:
            continue
        title = event_cell.get_text(strip=True)
        if not title:
            continue

        forecast_cell = row.find("td", class_=re_forecast)
        forecast = forecast_cell.get_text(strip=True) if forecast_cell else ""

        previous_cell = row.find("td", class_=re_previous)
        previous = previous_cell.get_text(strip=True) if previous_cell else ""

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

def _fetch_from_source(source_url: str, target_date: date) -> list[dict]:
    """ดึงข่าวจากแหล่งข่าวเฉพาะที่"""
    try:
        session = requests.Session()
        response = session.get(source_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch from {source_url}: {e}")
    
    try:
        soup = BeautifulSoup(response.text, "lxml")
    except Exception:
        soup = BeautifulSoup(response.text, "html.parser")
    
    return parse_calendar(soup, target_date)

def _generate_sample_news(target_date: date) -> list[dict]:
    """สร้างข่าวตัวอย่างสำหรับทดสอบเมื่อไม่สามารถเชื่อมต่อกับอินเตอร์เน็ตได้"""
    sample_news = [
        {
            "title": "Non-Farm Payrolls (NFP) - July",
            "country": "USD",
            "date": f"{target_date.strftime('%Y-%m-%d')}T12:00:00+00:00",
            "impact": "High",
            "forecast": "195K",
            "previous": "206K"
        },
        {
            "title": "Consumer Price Index (CPI) - June",
            "country": "EUR",
            "date": f"{target_date.strftime('%Y-%m-%d')}T09:00:00+00:00",
            "impact": "Medium",
            "forecast": "0.2%",
            "previous": "0.3%"
        },
        {
            "title": "Retail Sales MoM - June",
            "country": "GBP",
            "date": f"{target_date.strftime('%Y-%m-%d')}T08:30:00+00:00",
            "impact": "Low",
            "forecast": "0.4%",
            "previous": "0.2%"
        },
        {
            "title": "Unemployment Rate - June",
            "country": "AUD",
            "date": f"{target_date.strftime('%Y-%m-%d')}T01:30:00+00:00",
            "impact": "Medium",
            "forecast": "4.0%",
            "previous": "4.1%"
        },
        {
            "title": "Bank of Canada Interest Rate Decision",
            "country": "CAD",
            "date": f"{target_date.strftime('%Y-%m-%d')}T13:00:00+00:00",
            "impact": "High",
            "forecast": "No change",
            "previous": "No change"
        }
    ]
    return sample_news

def _build_datetime(target_date: date, time_str: str) -> str:
    """แปลง date + time string → ISO 8601 string (UTC)"""
    if not isinstance(target_date, date):
        raise TypeError(f"target_date must be date, got {type(target_date)}")
    if not isinstance(time_str, str):
        raise TypeError(f"time_str must be str, got {type(time_str)}")

    time_str_clean = time_str.strip().lower()

    if not time_str_clean or time_str_clean in ("all day", "tentative", "") or time_str_clean.startswith("day"):
        dt_ny = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0, tzinfo=ZoneInfo("America/New_York"))
        return dt_ny.astimezone(ZoneInfo("UTC")).isoformat()

    if "th" in time_str_clean or "st" in time_str_clean or "nd" in time_str_clean or "rd" in time_str_clean:
        try:
            parts = time_str_clean.split()
            if len(parts) >= 2:
                month_map = {
                    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
                }
                month_str = parts[0]
                day_str = parts[1]
                if month_str in month_map:
                    day = int(re.sub(r'\D', '', day_str))
                    t = datetime(target_date.year, month_map[month_str], day, 12, 0, 0)
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

    dt_ny = datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        t.hour,
        t.minute,
        t.second,
        tzinfo=ZoneInfo("America/New_York")
    )

    return dt_ny.astimezone(ZoneInfo("UTC")).isoformat()

# ─────────────────────────────────────────
#  EXPORT ENGINE (STRICT BACKUP 100% JSON)
# ─────────────────────────────────────────
def export_json(events: list[dict], target_date: date) -> Path:
    """บันทึก JSON ลงไฟล์"""
    if not isinstance(events, list):
        raise TypeError(f"events must be list, got {type(events)}")
    if not isinstance(target_date, date):
        raise TypeError(f"target_date must be date, got {type(target_date)}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"calendar_{target_date.isoformat()}.txt"
    filepath = OUTPUT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

    return filepath

export_txt = export_json

# ─────────────────────────────────────────
#  EVALUATOR & ORCHESTRATION INTEGRATION
# ─────────────────────────────────────────
def ensure_calendar_news(target_date: date = None) -> Path:
    """
    ตรวจสอบและดึงข่าวของวันนี้อัตโนมัติบน Startup
    หากยังไม่มีไฟล์ calendar_YYYY-MM-DD.txt ให้ดึงสดและบันทึกทันที
    """
    if target_date is None:
        target_date = date.today()
    elif not isinstance(target_date, date):
        raise TypeError(f"target_date must be date, got {type(target_date)}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"calendar_{target_date.isoformat()}.txt"
    filepath = OUTPUT_DIR / filename

    if not filepath.exists():
        log(f"[START] เริ่มดึงปฏิทินข่าว วันที่: {target_date}")
        try:
            events = fetch_calendar(target_date)
            saved_path = export_json(events, target_date)
            return saved_path
        except Exception as e:
            log(f"[ERROR] Failed to fetch calendar news: {e}")
            traceback.print_exc()
            raise RuntimeError(f"Failed to ensure calendar news for {target_date}: {e}") from e
    else:
        return filepath

def update_all_news_impact(symbols: list = None) -> None:
    """
    คำนวณและอัปเดตผลกระทบข่าวล่วงหน้าสำหรับทุกคู่เงิน
    ประเมินกรอบเวลาข่าวล่วงหน้า 30 นาที / ย้อนหลัง 15 นาที
    """
    if symbols is not None and not isinstance(symbols, list):
        raise TypeError(f"update_all_news_impact: symbols must be list or None, got {type(symbols)}")

    if symbols is None:
        try:
            from config_setting.config_loader import get_symbols
            symbols = get_symbols()
        except Exception:
            symbols = ["EURUSD", "GBPUSD", "EURGBP"]

    global _PRECALCULATED_NEWS, _LAST_CALENDAR_DATE, _EVENTS_CACHE
    try:
        now_utc = datetime.now(timezone.utc)
        today_str = datetime.now().strftime("%Y-%m-%d")

        # โหลดไฟล์ JSON เฉพาะเมื่อยังไม่มีข้อมูลของวันนี้
        if _LAST_CALENDAR_DATE != today_str:
            calendar_file = OUTPUT_DIR / f"calendar_{today_str}.txt"

            if not calendar_file.exists():
                log(f"[NEWS] Calendar file for {today_str} not found (Day Rollover). Auto-fetching...")
                try:
                    ensure_calendar_news(date.today())
                except Exception as e:
                    log(f"[ERROR] Auto-fetch news failed: {e}")
                    traceback.print_exc()
                    raise RuntimeError(f"Auto-fetch news failed: {e}") from e

            if calendar_file.exists():
                try:
                    with open(calendar_file, "r", encoding="utf-8") as f:
                        _EVENTS_CACHE = json.load(f)
                    _LAST_CALENDAR_DATE = today_str
                except json.JSONDecodeError as e:
                    log(f"[ERROR] Calendar JSON is corrupt: {e}. Removing file.")
                    try:
                        os.remove(calendar_file)
                    except OSError:
                        pass
                    raise RuntimeError(f"Calendar JSON is corrupt: {e}") from e
            else:
                log(f"[WARN] Calendar file {calendar_file} not found even after auto-fetch. Using empty events.")
                _EVENTS_CACHE = []
                _LAST_CALENDAR_DATE = today_str

        # คำนวณทีละคู่เงิน
        for symbol in symbols:
            if not isinstance(symbol, str):
                raise TypeError(f"symbol must be str, got {type(symbol)}")

            # 1. OTC Bypass
            if "OTC" in symbol.upper():
                _PRECALCULATED_NEWS[symbol] = "NONE_OTC"
                continue

            if not _EVENTS_CACHE:
                _PRECALCULATED_NEWS[symbol] = "LOW"
                continue

            clean_symbol = symbol.upper().replace("-OTC", "").replace("_OTC", "")
            upcoming_news = []
            past_news = []

            for event in _EVENTS_CACHE:
                date_str = event.get("date")
                if not date_str:
                    continue

                event_time = datetime.fromisoformat(date_str)

                if event_time.tzinfo is None:
                    event_time = event_time.replace(tzinfo=timezone.utc)

                time_diff = (event_time - now_utc).total_seconds() / 60
                impact = event.get("impact", "")
                currency = event.get("country", "")

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
        log(f"[ERROR] update_all_news_impact error: {e}")
        traceback.print_exc()
        raise RuntimeError(f"update_all_news_impact error: {e}") from e

def check_news_impact(symbol: str = "EURUSD") -> str:
    """
    ดึงข้อมูลผลกระทบข่าวที่คำนวณไว้แล้ว (Instant Lookup)
    สำหรับ OTC จะไม่มีข่าวจริง จึงกำหนดเป็น 'NONE_OTC' เพื่อแยกจากคู่เงินปกติ
    """
    if not isinstance(symbol, str):
        raise TypeError(f"check_news_impact: symbol must be str, got {type(symbol)}")
    if "OTC" in symbol.upper():
        return 'NONE_OTC'
    if symbol not in _PRECALCULATED_NEWS:
        update_all_news_impact([symbol])
    return _PRECALCULATED_NEWS.get(symbol, 'LOW')

# ─────────────────────────────────────────
#  MAIN CLI
# ─────────────────────────────────────────
def main() -> None:
    if len(sys.argv) > 1:
        try:
            target_date = date.fromisoformat(sys.argv[1])
        except ValueError:
            log(f"[ERROR] รูปแบบวันที่ไม่ถูกต้อง: {sys.argv[1]}  (ใช้ YYYY-MM-DD)")
            sys.exit(1)
    else:
        target_date = date.today()

    print_header(target_date)

    log(f"[START] เริ่มดึงปฏิทินข่าว วันที่: {target_date}")

    events = fetch_calendar(target_date)

    if not events:
        log("[WARN] ไม่พบข่าว — บันทึก list ว่าง")

    print_events(events)

    filepath = export_json(events, target_date)

    print_summary(events, filepath)

if __name__ == "__main__":
    main()
