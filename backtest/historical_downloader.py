"""
Historical CSV Downloader for Backtesting

Uses IQ Option API to fetch and store historical candle data locally.
Ensures that all required data is available before backtesting.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import logging

# Add parent directory to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from core.data.iq_option_adapter import IQOptionAdapter

logger = logging.getLogger(__name__)

# Default data directory
DATA_DIR = PROJECT_ROOT / "backtest" / "data test"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Timeframes to download (M1, M5, M15, M60)
TIMEFRAMES = ['M1', 'M5', 'M15', 'M60']
# Number of candles to fetch per request (max 1000 typically)
CANDLE_COUNT = 5000  # Increased to ensure enough candles for backtest (was 1000 causing truncation)


def get_iq_adapter() -> IQOptionAdapter:
    """Create and return IQ Option adapter using credentials from settings."""
    from core.config_loader import get_account_type, get_iq_credentials
    email, password = get_iq_credentials()
    account_type = get_account_type()
    if not email or not password:
        raise RuntimeError("IQ Option credentials not found in settings.json")
    return IQOptionAdapter(email=email, password=password, account_type=account_type)


def download_candles(symbol: str, timeframe: str, days_back: int = 30) -> pd.DataFrame:
    """
    Download historical candles for a symbol and timeframe.
    Uses iterative fetching to get enough data.
    """
    adapter = get_iq_adapter()
    if not adapter.is_connected():
        raise RuntimeError("Cannot download data: IQ Option not connected")
    
    all_candles = []
    # Use naive UTC datetime for consistent comparisons
    end_time = datetime.now(timezone.utc).replace(tzinfo=None)
    
    max_attempts = 40  # safety
    for attempt in range(max_attempts):
        # Pass end_time as naive or aware? IQOptionAdapter expects timezone-aware? We'll keep as naive but adapter might expect aware.
        # Convert to aware for adapter call
        end_time_aware = end_time.replace(tzinfo=timezone.utc) if end_time.tzinfo is None else end_time
        df = adapter.get_candles(symbol, timeframe, count=CANDLE_COUNT, end_time=end_time_aware)
        if df.empty:
            break
        # Ensure index is naive UTC
        df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
        all_candles.append(df)
        earliest = df.index.min()
        print(f"   -> [DOWNLOAD] {symbol} ({timeframe}) - ดึงข้อมูลย้อนหลังถึง: {earliest.strftime('%Y-%m-%d %H:%M')} (รอบที่ {attempt+1})")
        if earliest < end_time - timedelta(days=days_back):
            break
        end_time = earliest
        import time
        time.sleep(0.5)
    
    if not all_candles:
        return pd.DataFrame()
    
    combined = pd.concat(all_candles).sort_index()
    combined = combined[~combined.index.duplicated(keep='first')]
    return combined


def save_to_csv(symbol: str, timeframe: str, df: pd.DataFrame) -> Path:
    """Save dataframe to CSV file."""
    safe_sym = symbol.replace("-OTC", "_OTC")
    file_name = f"history_{safe_sym}_{timeframe}.csv"
    file_path = DATA_DIR / file_name
    # Reset index to have timestamp as column
    df_to_save = df.reset_index()
    df_to_save.to_csv(file_path, index=False)
    logger.info(f"Saved {len(df)} candles to {file_path}")
    return file_path


def load_existing(symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
    """Load existing CSV if available."""
    safe_sym = symbol.replace("-OTC", "_OTC")
    file_name = f"history_{safe_sym}_{timeframe}.csv"
    file_path = DATA_DIR / file_name
    if not file_path.exists():
        return None
    try:
        df = pd.read_csv(file_path)
        if "timestamp" not in df.columns:
            return None
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        # Ensure UTC
        if df["timestamp"].dt.tz is None:
            df["timestamp"] = df["timestamp"].dt.tz_localize(timezone.utc)
        df = df.set_index("timestamp").sort_index()
        return df
    except Exception as e:
        logger.warning(f"Failed to load existing CSV {file_path}: {e}")
        return None


def ensure_data(symbols: List[str], days_back: int = 30, force_download: bool = False, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> bool:
    """
    Ensure that all symbols have historical data for required timeframes.
    Downloads missing data or extends existing data if needed.
    
    Returns True if all data is available, False otherwise.
    """
    # Define the required date boundaries (including a 5-day buffer for indicators warmup before start_dt)
    req_start = start_date - timedelta(days=5) if start_date else (datetime.now(timezone.utc) - timedelta(days=days_back))
    req_end = end_date if end_date else datetime.now(timezone.utc)
    
    # Calculate how many days back we need to fetch from current time to cover req_start
    days_back = (datetime.now(timezone.utc) - req_start).days + 2
        
    success = True
    for symbol in symbols:
        for tf in TIMEFRAMES:
            existing = None if force_download else load_existing(symbol, tf)
            need_download = False
            if existing is None:
                print(f"[DATA] ไม่พบไฟล์ข้อมูลของ {symbol} ({tf}) เริ่มดาวน์โหลด...")
                need_download = True
            else:
                # Check if existing data covers the required range
                has_start = existing.index.min() <= req_start
                has_end = existing.index.max() >= req_end - timedelta(hours=2) # 2 hours leeway for recent data
                
                if not (has_start and has_end):
                    print(f"[DATA] ข้อมูลที่มีอยู่ ({existing.index.min().strftime('%Y-%m-%d')} ถึง {existing.index.max().strftime('%Y-%m-%d')}) ครอบคลุมไม่ถึงช่วงที่ต้องการทดสอบ (ต้องการ: {req_start.strftime('%Y-%m-%d')} ถึง {req_end.strftime('%Y-%m-%d')}) เริ่มดาวน์โหลด...")
                    need_download = True
            
            if need_download:
                try:
                    df = download_candles(symbol, tf, days_back)
                    if df.empty:
                        print(f"[ERR] ดาวน์โหลดข้อมูลล้มเหลว {symbol} ({tf})")
                        success = False
                    else:
                        save_to_csv(symbol, tf, df)
                        print(f"[DATA] อัปเดตข้อมูลสำเร็จ: {symbol} ({tf}) -> บันทึกลง CSV เรียบร้อย")
                except Exception as e:
                    print(f"[ERR] เกิดข้อผิดพลาดขณะโหลด {symbol} ({tf}): {e}")
                    success = False
            else:
                print(f"[DATA OK] {symbol} ({tf}) มีข้อมูลครอบคลุมแล้ว (ตรวจพบช่วง: {existing.index.min().strftime('%Y-%m-%d')} ถึง {existing.index.max().strftime('%Y-%m-%d')})")
    return success


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from core.config_loader import get_symbols
    symbols = get_symbols()
    ensure_data(symbols, days_back=30)
