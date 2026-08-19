"""
Active Trading Pairs Grabber Utility
====================================
Fetches real-time active trading pairs (Binary, Turbo) and payout percentages
from IQ Option and exports them categorized to `active_symbols.txt`.

Reads credentials from: config_setting/settings.json
Writes active pairs to: config_setting/active_symbols.txt
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Ensure UTF-8 output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def classify_asset(symbol: str) -> str:
    """Classifies symbol into clear market categories."""
    clean_sym = symbol.upper()
    
    # 1. Commodities
    commodities = [
        'COCOA', 'COFFEE', 'COTTON', 'SUGAR', 'URANIUM', 'XAUUSD', 'XAGUSD', 
        'XPDUSD', 'XPTUSD', 'UKOUSD', 'USOUSD', 'XNGUSD', 'XAU', 'XAG'
    ]
    if any(c in clean_sym for c in commodities):
        return "COMMODITIES"
        
    # 2. Indices & ETFs
    indices_keywords = [
        'SPY', 'QQQ', 'DIA', 'IWM', 'GDX', 'XLK', 'XLE', 'XLU', 'XLY', 'SQQQ', 
        'SMH', 'TLT', 'SDS', 'US30', 'GER30', 'UK100', 'JP225', 'AUS200', 'EU50', 
        'FR40', 'US2000', 'USNDAQ100', 'SP35', 'SP500'
    ]
    if any(k in clean_sym for k in indices_keywords):
        return "INDICES_ETFS"
        
    # 3. Crypto
    crypto_keywords = [
        'BTC', 'ETH', 'LTC', 'XRP', 'SOL', 'DASH', 'EOS', 'DOT', 'ARB', 'ATOM', 
        'BONK', 'FLOKI', 'PEPE', 'SHIB', 'RENDER', 'ONDO', 'PYTH', 'TIA', 'SUI', 
        'TAO', 'WLD', 'WIF', 'FET', 'GRT', 'ICP', 'IMX', 'INJ', 'IOTA', 'LINK', 
        'MANA', 'SAND', 'STX', 'TON', 'TRON', 'SATS', 'RONIN', 'SEI', 'JUP', 
        'RAYDIUM', 'PENGU', 'DYDX', 'FARTCOIN', 'LABUBU', 'MELANIA', 'TRUMP'
    ]
    if any(k in clean_sym for k in crypto_keywords):
        return "CRYPTO"
        
    # 4. Forex OTC vs Normal Forex
    if "-OTC" in clean_sym:
        return "FOREX_OTC"
        
    # Standard currencies
    currencies = {
        'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD', 'THB', 'SGD', 
        'HKD', 'INR', 'MYR', 'IDR', 'PHP', 'VND', 'CNY', 'RUB', 'BRL', 'MXN', 
        'ZAR', 'TRY', 'PLN', 'SEK', 'NOK', 'DKK', 'ARS', 'CLP', 'COP', 'PEN'
    }
    if len(clean_sym) == 6 and clean_sym[:3] in currencies and clean_sym[3:] in currencies:
        return "FOREX"
        
    # 5. Stocks
    return "STOCKS"


def main():
    print("=" * 64)
    print("       IQ OPTION ACTIVE ASSETS & PAYOUTS GRABBER        ")
    print("=" * 64)

    # 1. Resolve paths
    current_dir = Path(__file__).resolve().parent
    settings_path = current_dir / "settings.json"
    if not settings_path.is_file():
        settings_path = current_dir.parent / "config_setting" / "settings.json"

    output_path = current_dir / "active_symbols.txt"

    print(f"[PATH] Config Path: {settings_path}")
    print(f"[PATH] Output Path: {output_path}")

    if not settings_path.is_file():
        print(f"[ERR] Settings file not found at: {settings_path}")
        return

    # 2. Load credentials from settings.json
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        
        account = settings.get("account", {})
        email = account.get("iq_email", "").strip()
        password = account.get("iq_password", "").strip()
        
        if not email or not password:
            raise ValueError("iq_email or iq_password is missing in settings.json")
    except Exception as e:
        print(f"[ERR] Failed to load credentials from settings.json: {e}")
        return

    # 3. Connect to IQ Option
    try:
        from iqoptionapi.stable_api import IQ_Option
        import iqoptionapi.constants as OP_code
    except ImportError:
        print("[ERR] iqoptionapi library is not installed.")
        return

    print(f"[CONN] Connecting to IQ Option as {email}...")
    api = IQ_Option(email, password)
    ok, reason = api.connect()
    if not ok:
        print(f"[ERR] Login failed: {reason}")
        return
    print(f"[CONN] Connected successfully! (Balance Mode: {api.get_balance_mode()})")

    # 4. Fetch real-time payout rates
    print("[DATA] Fetching active instruments and payout percentages from broker...")
    try:
        all_profits = api.get_all_profit()
    except Exception as e:
        print(f"[ERR] Failed to fetch profit rates: {e}")
        return

    # Group into categories
    categorized = {
        "FOREX": [],
        "FOREX_OTC": [],
        "INDICES_ETFS": [],
        "CRYPTO": [],
        "STOCKS": [],
        "COMMODITIES": []
    }

    total_active_count = 0
    all_valid_symbols = []

    for sym in OP_code.ACTIVES.keys():
        p_info = all_profits.get(sym, {})
        turbo_p = p_info.get("turbo") or 0.0
        binary_p = p_info.get("binary") or 0.0
        
        # Check if asset has active payout
        if turbo_p > 0 or binary_p > 0:
            max_payout = max(turbo_p, binary_p) * 100.0
            cat = classify_asset(sym)
            
            entry = {
                "symbol": sym,
                "turbo_pct": round(turbo_p * 100.0, 1),
                "binary_pct": round(binary_p * 100.0, 1),
                "max_payout": round(max_payout, 1)
            }
            if cat in categorized:
                categorized[cat].append(entry)
            else:
                categorized["STOCKS"].append(entry)
                
            total_active_count += 1
            all_valid_symbols.append(sym)

    # Sort each category by highest payout first
    for cat in categorized:
        categorized[cat].sort(key=lambda x: x["max_payout"], reverse=True)

    # 5. Build report text and write to active_symbols.txt
    tz_thailand = timezone(timedelta(hours=7))
    now_str = datetime.now(tz_thailand).strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append("=" * 68)
    lines.append(f"  IQ OPTION ACTIVE ASSETS REPORT (ดึงข้อมูลเมื่อ: {now_str})")
    lines.append(f"  สินทรัพย์ที่เปิดรับออเดอร์ Binary / Turbo ทั้งหมด: {total_active_count} รายการ")
    lines.append("=" * 68)
    lines.append("")

    cat_titles = [
        ("FOREX", "💱 สกุลเงินปกติ (Forex Standard)"),
        ("FOREX_OTC", "🌐 สกุลเงิน OTC (Forex OTC)"),
        ("INDICES_ETFS", "📈 ดัชนีและกองทุน ETF (Indices & ETFs - เทรดได้ 24 ชม.)"),
        ("CRYPTO", "🪙 คริปโตเคอเรนซี (Crypto)"),
        ("COMMODITIES", "🛢️ สินค้าโภคภัณฑ์ (Commodities - ทองคำ/น้ำมัน)"),
        ("STOCKS", "🏢 หุ้นสหรัฐฯ (US Stocks)")
    ]

    for cat_key, cat_title in cat_titles:
        items = categorized.get(cat_key, [])
        lines.append(f"=== {cat_title} [{len(items)} คู่] ===")
        if not items:
            lines.append("  (ขณะนี้ปิดให้บริการ)")
        else:
            for item in items:
                sym = item["symbol"]
                t_str = f"Turbo: {item['turbo_pct']}%" if item['turbo_pct'] > 0 else "Turbo: ปิด"
                b_str = f"Binary: {item['binary_pct']}%" if item['binary_pct'] > 0 else "Binary: ปิด"
                lines.append(f"  • {sym:<16} | {t_str:<13} | {b_str:<14} | Payout สูงสุด: {item['max_payout']}%")
        lines.append("")

    # Add ready-to-copy JSON block for top open assets
    top_open = []
    for cat in ["INDICES_ETFS", "FOREX", "FOREX_OTC"]:
        for it in categorized[cat]:
            if it["max_payout"] >= 80:
                top_open.append(it["symbol"])

    lines.append("=" * 68)
    lines.append("📋 JSON Configuration Ready (สามารถ Copy ใส่ settings.json ได้ทันที):")
    lines.append("=" * 68)
    lines.append('"symbols": ' + json.dumps(top_open[:8], ensure_ascii=False, indent=2))
    lines.append("")

    output_text = "\n".join(lines)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)
        print(f"[OK] Successfully saved active assets report to: {output_path.name}")
    except Exception as e:
        print(f"[ERR] Failed to write active_symbols.txt: {e}")

    # Display on console
    print("\n" + output_text)
    print("\n[OK] Grabber task finished successfully!")


if __name__ == "__main__":
    main()
