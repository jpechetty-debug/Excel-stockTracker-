"""
Custom Exception Hierarchy for IOS v4.0
"""

class IOSException(Exception):
    """Base exception for all custom IOS errors."""
    pass

class ProviderUnavailableError(IOSException):
    """Raised when a data provider cannot be reached or fails to respond."""
    pass

class RateLimitExceededError(IOSException):
    """Raised when the rate limit for a provider is exceeded."""
    pass

class ValidationError(IOSException):
    """Raised when data fails quality gates and validation bounds."""
    pass

class CacheMissError(IOSException):
    """Raised when a requested domain object is not found in the cache or is expired."""
    pass

class WorkbookProtectionError(IOSException):
    """Raised when an attempt is made to overwrite a Manual Zone or protected Excel cell."""
    pass
