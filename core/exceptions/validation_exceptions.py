"""
Validation Exceptions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Custom exceptions for validation errors.
"""


class ValidationError(Exception):
    """Base validation exception"""
    pass


class CandleValidationError(ValidationError):
    """Raised when candle data is invalid"""
    pass


class ScoreValidationError(ValidationError):
    """Raised when score is out of bounds"""
    pass


class ConfigValidationError(ValidationError):
    """Raised when configuration is invalid"""
    pass
