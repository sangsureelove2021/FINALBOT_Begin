"""
Context Exceptions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Custom exceptions for MarketContext errors.
"""


class ContextError(Exception):
    """Base exception for context errors"""
    pass


class ContextBuildError(ContextError):
    """Raised when context cannot be built"""
    pass


class IncompleteContextError(ContextError):
    """Raised when context is missing required data"""
    pass


class ContextValidationError(ContextError):
    """Raised when context fails validation"""
    pass
