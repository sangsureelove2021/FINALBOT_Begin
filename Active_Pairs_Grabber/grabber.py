"""
Active Pairs Grabber Bot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A standalone utility that fetches active trading pairs from IQ Option 
and exports them to a text file.

Reads credentials from: ../config/settings.json
Writes active pairs to: active_symbols.txt
"""

import sys
import json
from pathlib import Path

# Safe stream wrapper to prevent UnicodeEncodeError in IDLE and Windows consoles
class SafeStreamWrapper:
    def __init__(self, original_stream):
        self.original_stream = original_stream
        self.encoding = getattr(original_stream, 'encoding', None) or 'utf-8'

    def write(self, data):
        try:
            self.original_stream.write(data)
        except Exception:
            try:
                safe_data = data.encode('ascii', errors='backslashreplace').decode('ascii')
                self.original_stream.write(safe_data)
            except Exception:
                pass

    def flush(self):
        if hasattr(self.original_stream, 'flush'):
            self.original_stream.flush()

    def __getattr__(self, attr):
        return getattr(self.original_stream, attr)

sys.stdout = SafeStreamWrapper(sys.stdout)
sys.stderr = SafeStreamWrapper(sys.stderr)

def classify_asset(symbol):
    clean_sym = symbol.replace("-OTC-op", "").replace("-OTC", "").upper()
    
    # Standard currency codes in IQ Option
    CURRENCIES = {
        'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD', 'THB', 'SGD', 
        'HKD', 'INR', 'MYR', 'IDR', 'PHP', 'VND', 'CNY', 'RUB', 'BRL', 'MXN', 
        'ZAR', 'TRY', 'PLN', 'SEK', 'NOK', 'DKK', 'ARS', 'CLP', 'COP', 'PEN', 
        'AED', 'BDT', 'BOB', 'DOP', 'SAR', 'NGN'
    }
    
    # 1. Commodities (สินค้าโภคภัณฑ์)
    commodities = ['COCOA', 'COFFEE', 'COTTON', 'SUGAR', 'URANIUM', 'XAUUSD', 'XAGUSD', 'XPDUSD', 'XPTUSD', 'UKOUSD', 'USOUSD', 'XNGUSD', 'XAU', 'XAG']
    if clean_sym in commodities or any(c in clean_sym for c in commodities):
        return "COMMODITIES"
        
    # 2. Indices (ดัชนี)
    indices_keywords = ['SP500', 'US30', 'GER30', 'HK33', 'JP225', 'AUS200', 'EU50', 'FR40', 'UK100', 'US2000', 'USNDAQ100', 'SP35']
    if any(k in clean_sym for k in indices_keywords):
        return "INDICES"
        
    # 3. Forex (สกุลเงิน)
    if len(clean_sym) == 6 and clean_sym.isalpha():
        c1, c2 = clean_sym[:3], clean_sym[3:]
        if c1 in CURRENCIES and c2 in CURRENCIES:
            return "FOREX"
            
    # 4. Crypto (คริปโต)
    crypto_keywords = [
        'BTC', 'ETH', 'LTC', 'XRP', 'SOL', 'DASH', 'EOS', 'DOT', 'ARB', 'ATOM', 
        'BONK', 'FLOKI', 'PEPE', 'SHIB', 'RENDER', 'ONDO', 'PYTH', 'TIA', 'SUI', 
        'TAO', 'WLD', 'WIF', 'FET', 'GRT', 'ICP', 'IMX', 'INJ', 'IOTA', 'LINK', 
        'MANA', 'SAND', 'STX', 'TON', 'TRON', 'SATS', 'RONIN', 'SEI', 'JUP', 
        'RAYDIUM', 'PENGU', 'DYDX', 'FARTCOIN', 'LABUBU', 'MELANIA', 'TRUMP'
    ]
    if any(k in clean_sym for k in crypto_keywords) or clean_sym.endswith('USD'):
        return "CRYPTO"
        
    # 5. Stocks (หุ้น)
    return "STOCKS"

def group_assets(assets_with_payout):
    forex = []
    crypto = []
    stocks = []
    others = []  # indices + commodities
    
    for item in assets_with_payout:
        pair = item.split()[0]
        category = classify_asset(pair)
        
        if category == "FOREX":
            forex.append(item)
        elif category == "CRYPTO":
            crypto.append(item)
        elif category == "STOCKS":
            stocks.append(item)
        else:
            others.append(item)
            
    forex.sort()
    crypto.sort()
    stocks.sort()
    others.sort()
    
    return forex, crypto, stocks, others

def main():
    print("==================================================")
    print("      IQ OPTION ACTIVE SYMBOLS EXTRACTOR          ")
    print("==================================================")

    # 1. Resolve paths
    current_dir = Path(__file__).resolve().parent
    settings_path = current_dir.parent / "config" / "settings.json"
    output_path = current_dir / "active_symbols.txt"

    print(f"[PATH] Config Path: {settings_path}")
    print(f"[PATH] Output Path: {output_path}")

    if not settings_path.is_file():
        print(f"[ERR] Settings file not found at: {settings_path}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # 2. Load credentials from settings.json
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        
        account = settings.get("account", {})
        email = account.get("iq_email", "").strip()
        password = account.get("iq_password", "").strip()
        
        # Reject placeholders
        if not email or not password or email.startswith("ใส่") or password.startswith("ใส่"):
            raise ValueError("Credentials are empty or placeholders.")
    except Exception as e:
        print(f"[ERR] Failed to load credentials from settings.json: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # 3. Connect to IQ Option
    try:
        from iqoptionapi.stable_api import IQ_Option
    except ImportError:
        print("[ERR] iqoptionapi library is not installed.")
        print("Please run: pip install iqoptionapi")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print(f"[CONN] Connecting to IQ Option as {email}...")
    api = IQ_Option(email, password)
    ok, reason = api.connect()
    if not ok:
        print(f"[ERR] Login failed: {reason}")
        input("\nPress Enter to exit...")
        sys.exit(1)
    print("[CONN] Connected successfully!")

    # 4. Fetch active assets
    print("[DATA] Fetching active assets from broker...")
    try:
        all_assets = api.get_all_open_time()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERR] Failed to fetch assets: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    raw_turbo = []

    # Extract active binary (turbo) pairs
    if "turbo" in all_assets:
        for name, details in all_assets["turbo"].items():
            if details.get("open") is True:
                raw_turbo.append(name)

    raw_turbo = sorted(list(set(raw_turbo)))

    # Fetch Binary payout rates
    print("[DATA] Fetching Binary payout rates...")
    binary_profits = {}
    try:
        binary_profits = api.get_all_profit()
    except Exception as e:
        print(f"[WARN] Failed to fetch Binary profits: {e}")

    active_turbo_with_payout = []
    for pair in raw_turbo:
        profit_val = binary_profits.get(pair, {}).get("turbo", 0)
        payout_pct = int(round(profit_val * 100)) if profit_val else 0
        # Filter: Only display payouts >= 83%
        if payout_pct >= 83:
            active_turbo_with_payout.append(f"{pair} (Payout: {payout_pct}%)")

    # Robust Digital probing: Since IQ Option V2 digital underlying endpoint is deprecated,
    # we probe active Binary symbols to see if they are open as Digital, using a 1s timeout.
    print("[DATA] Probing active symbols for Digital payouts (this may take a few seconds)...")
    active_digital_with_payout = []
    for pair in raw_turbo:
        try:
            digital_payout = api.get_digital_payout(pair, seconds=1)
            # Filter: Only display payouts >= 83%
            if digital_payout and digital_payout >= 83:
                active_digital_with_payout.append(f"{pair} (Payout: {digital_payout}%)")
        except Exception:
            pass

    print(f"[DATA] Found {len(active_turbo_with_payout)} Binary and {len(active_digital_with_payout)} Digital open pairs.")

    # Group turbo and digital assets
    turbo_forex, turbo_crypto, turbo_stocks, turbo_others = group_assets(active_turbo_with_payout)
    digital_forex, digital_crypto, digital_stocks, digital_others = group_assets(active_digital_with_payout)

    # 5. Write to active_symbols.txt
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("=== BINARY (TURBO) OPTIONS ===\n")
            if turbo_forex:
                f.write("--- สกุลเงิน (Forex) ---\n")
                for pair in turbo_forex:
                    f.write(f"{pair}\n")
                f.write("\n")
                
            if turbo_crypto:
                f.write("--- คริปโตเคอเรนซี (Crypto) ---\n")
                for pair in turbo_crypto:
                    f.write(f"{pair}\n")
                f.write("\n")
                
            if turbo_stocks:
                f.write("--- หุ้น (Stocks) ---\n")
                for pair in turbo_stocks:
                    f.write(f"{pair}\n")
                f.write("\n")
                
            if turbo_others:
                f.write("--- ดัชนี & สินค้าโภคภัณฑ์ & อื่นๆ ---\n")
                for pair in turbo_others:
                    f.write(f"{pair}\n")
                f.write("\n")
                
            f.write("=== DIGITAL OPTIONS ===\n")
            if digital_forex:
                f.write("--- สกุลเงิน (Forex) ---\n")
                for pair in digital_forex:
                    f.write(f"{pair}\n")
                f.write("\n")
                
            if digital_crypto:
                f.write("--- คริปโตเคอเรนซี (Crypto) ---\n")
                for pair in digital_crypto:
                    f.write(f"{pair}\n")
                f.write("\n")
                
            if digital_stocks:
                f.write("--- หุ้น (Stocks) ---\n")
                for pair in digital_stocks:
                    f.write(f"{pair}\n")
                f.write("\n")
                
            if digital_others:
                f.write("--- ดัชนี & สินค้าโภคภัณฑ์ & อื่นๆ ---\n")
                for pair in digital_others:
                    f.write(f"{pair}\n")
                f.write("\n")
                
        print(f"[OK] Successfully saved categorized active pairs to: {output_path.name}")
        
        # Display the pairs to the user
        print("\n=== BINARY (TURBO) OPTIONS ===")
        if turbo_forex:
            print("  --- สกุลเงิน (Forex) ---")
            for pair in turbo_forex:
                print(f"    • {pair}")
        if turbo_crypto:
            print("  --- คริปโตเคอเรนซี (Crypto) ---")
            for pair in turbo_crypto:
                print(f"    • {pair}")
        if turbo_stocks:
            print("  --- หุ้น (Stocks) ---")
            for pair in turbo_stocks:
                print(f"    • {pair}")
        if turbo_others:
            print("  --- ดัชนี & สินค้าโภคภัณฑ์ & อื่นๆ ---")
            for pair in turbo_others:
                print(f"    • {pair}")
                
        print("\n=== DIGITAL OPTIONS ===")
        if digital_forex:
            print("  --- สกุลเงิน (Forex) ---")
            for pair in digital_forex:
                print(f"    • {pair}")
        if digital_crypto:
            print("  --- คริปโตเคอเรนซี (Crypto) ---")
            for pair in digital_crypto:
                print(f"    • {pair}")
        if digital_stocks:
            print("  --- หุ้น (Stocks) ---")
            for pair in digital_stocks:
                print(f"    • {pair}")
        if digital_others:
            print("  --- ดัชนี & สินค้าโภคภัณฑ์ & อื่นๆ ---")
            for pair in digital_others:
                print(f"    • {pair}")
        print("========================")
    except Exception as e:
        print(f"[ERR] Failed to write active_symbols.txt: {e}")

    print("\n[OK] Task completed successfully!")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
