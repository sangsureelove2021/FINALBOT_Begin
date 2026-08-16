"""
Configuration Manager for Data Feed.
รวม hardcoded values ทั้งหมดไว้ในที่เดียว
"""

from typing import Dict, Any

class DataFeedConfig:
    """Configuration constants for data feed module"""
    
    # Timeframe settings
    TIMEFRAMES = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4']
    
    # Candle fetch limits (จำนวนแท่งที่ดึงต่อครั้ง)
    CANDLE_LIMITS = {
        'M1': 110,
        'M5': 260,
        'M15': 260,
        'M30': 260,
        'H1': 260,
        'H4': 260,
    }
    
    # Refresh intervals (วินาที)
    REFRESH_INTERVALS = {
        'M1': 60,
        'M5': 60,
        'M15': 60,
        'M30': 60,
        'H1': 60,
        'H4': 60,
    }
    
    # Validation settings
    GAP_TOLERANCE_SECONDS = 30
    MAX_OVERLAP_ROWS = 10
    
    # Cache settings
    CACHE_MAX_BLOCKS = 100
    CACHE_EXPIRY_SECONDS = 300
    
    # CSV settings
    CSV_FLUSH_INTERVAL = 5  # จำนวนแท่งก่อนจะ flush ลงไฟล์
    CSV_BACKUP_ENABLED = True
    
    # Connection settings
    CONNECTION_TIMEOUT = 30
    RECONNECT_DELAY = 5
    MAX_RECONNECT_ATTEMPTS = 3
    
    @classmethod
    def get_candle_limit(cls, timeframe: str) -> int:
        return cls.CANDLE_LIMITS.get(timeframe, 260)
    
    @classmethod
    def get_refresh_interval(cls, timeframe: str) -> int:
        return cls.REFRESH_INTERVALS.get(timeframe, 60)
