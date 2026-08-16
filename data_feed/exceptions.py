"""
Custom Exceptions for Data Feed Module.
รวม Exception ทั้งหมดไว้ในที่เดียว เพื่อความสม่ำเสมอและง่ายต่อการจัดการ
"""

class DataFeedError(Exception):
    """Base exception for all data feed errors."""
    pass

class DataValidationError(DataFeedError):
    """Raised when data validation fails (e.g., missing columns, bad format)."""
    pass

class DataGapError(DataFeedError):
    """Raised when a time gap is detected in the data stream."""
    def __init__(self, symbol: str, timeframe: str, gap_start: str, gap_end: str, message: str = None):
        self.symbol = symbol
        self.timeframe = timeframe
        self.gap_start = gap_start
        self.gap_end = gap_end
        msg = message or f"Gap detected in {symbol} ({timeframe}): {gap_start} -> {gap_end}"
        super().__init__(msg)

class DataOverlapError(DataFeedError):
    """Raised when duplicate or overlapping data is detected."""
    pass

class ConnectionLostError(DataFeedError):
    """Raised when broker connection is lost and cannot be recovered immediately."""
    pass

class ConfigurationError(DataFeedError):
    """Raised when configuration values are missing or invalid."""
    pass

class BrokerConnectionError(DataFeedError):
    """Raised when broker connection fails."""
    pass

class DataFetchError(DataFeedError):
    """Raised when fetching data from broker fails."""
    pass
