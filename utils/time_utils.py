"""
Time Utilities

"""

from datetime import datetime, timedelta, timezone
from typing import Optional


TIMEFRAME_MINUTES = {
    'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30,
    'M60': 60, 'H1': 60, 'H4': 240, 'D1': 1440
}


def get_timeframe_minutes(timeframe: str) -> int:
    """Convert timeframe string to minutes"""
    return TIMEFRAME_MINUTES.get(timeframe, 1)


def utc_now() -> datetime:
    """Get current UTC time"""
    return datetime.now(timezone.utc)


def round_to_timeframe(dt: datetime, timeframe: str) -> datetime:
    """Round datetime down to nearest timeframe boundary"""
    minutes = get_timeframe_minutes(timeframe)
    delta = timedelta(minutes=minutes)
    rounded = dt - timedelta(
        minutes=dt.minute % minutes,
        seconds=dt.second,
        microseconds=dt.microsecond
    )
    return rounded


def candle_close_time(open_time: datetime, timeframe: str) -> datetime:
    """Get the close time of a candle"""
    return open_time + timedelta(minutes=get_timeframe_minutes(timeframe))
