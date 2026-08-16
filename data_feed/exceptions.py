"""
data_feed/exceptions.py

Custom exception hierarchy for data_feed module.
Provides specific exception types for precise error handling.
"""


class DataFeedError(Exception):
    """Base exception for data_feed module."""
    pass


class ValidationError(DataFeedError):
    """Data validation failure."""
    pass


class DataFeedConnectionError(DataFeedError):
    """Broker connection failure."""
    pass


class DataGapError(DataFeedError):
    """Missing data gap detected."""
    pass


class TimeframeSyncError(DataFeedError):
    """Timeframe synchronization failure."""
    pass


class FallbackTriggered(DataFeedError):
    """REST fallback was used instead of WebSocket. Logs to fallback.log."""
    pass
