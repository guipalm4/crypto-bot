"""
Application layer exceptions.
"""


class TradingException(Exception):
    """Base exception for trading operations."""

    pass


class OrderNotFound(TradingException):
    """Raised when an order cannot be found."""

    pass


class ExchangeError(TradingException):
    """Raised when an exchange operation fails."""

    pass


class NetworkError(TradingException):
    """Raised when network communication fails."""

    pass


class InsufficientBalance(TradingException):
    """Raised when account balance is insufficient for operation."""

    pass


class InvalidOrder(TradingException):
    """Raised when order parameters are invalid."""

    pass


class RateLimitExceeded(TradingException):
    """Raised when exchange rate limit is exceeded."""

    pass
