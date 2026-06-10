"""
Engine Exceptions

Custom exceptions for engine errors.
"""


class EngineError(Exception):
    """Base exception for all engine errors"""
    pass


class InsufficientDataError(EngineError):
    """Raised when engine doesn't have enough data to analyze"""
    pass


class InvalidInputError(EngineError):
    """Raised when input data is invalid"""
    pass


class EngineNotFoundError(EngineError):
    """Raised when requested engine is not registered"""
    pass


class EngineExecutionError(EngineError):
    """Raised when engine execution fails"""
    pass
