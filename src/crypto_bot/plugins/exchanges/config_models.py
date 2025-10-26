"""
Exchange plugin configuration models using Pydantic.

This module defines Pydantic models for validating exchange plugin configurations,
ensuring type safety and proper parameter validation before CCXT initialization.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ExchangeConfig(BaseModel):
    """
    Base configuration for exchange plugins.

    Attributes:
        api_key: Encrypted API key for authentication
        secret: Encrypted secret key for authentication
        password: Optional encrypted password/passphrase (required by some exchanges)
        sandbox: Whether to use testnet/sandbox mode (default: False)
        timeout: Request timeout in milliseconds (default: 30000)
        rate_limit: Milliseconds between requests (default: 1000)
        enable_rate_limit: Enable CCXT built-in rate limiting (default: True)
        proxy: Optional HTTP/HTTPS proxy URL
        verbose: Enable verbose logging for debugging (default: False)
        options: Additional exchange-specific options
    """

    api_key: Optional[str] = Field(
        None, description="Encrypted API key for authentication"
    )
    secret: Optional[str] = Field(
        None, description="Encrypted secret key for authentication"
    )
    password: Optional[str] = Field(
        None, description="Optional encrypted password/passphrase"
    )
    sandbox: bool = Field(False, description="Use testnet/sandbox mode")
    timeout: int = Field(30000, gt=0, description="Request timeout in milliseconds")
    rate_limit: int = Field(1000, gt=0, description="Milliseconds between requests")
    enable_rate_limit: bool = Field(
        True, description="Enable CCXT built-in rate limiting"
    )
    proxy: Optional[str] = Field(None, description="Optional HTTP/HTTPS proxy URL")
    verbose: bool = Field(False, description="Enable verbose logging for debugging")
    options: dict[str, Any] = Field(
        default_factory=dict, description="Additional exchange-specific options"
    )

    @field_validator("proxy")
    @classmethod
    def validate_proxy(cls, v: Optional[str]) -> Optional[str]:
        """Validate proxy URL format."""
        if v is not None and v:
            if not (v.startswith("http://") or v.startswith("https://")):
                raise ValueError("Proxy must start with http:// or https://")
        return v

    model_config = {"extra": "forbid"}  # Reject unknown fields


class BinanceConfig(ExchangeConfig):
    """
    Binance-specific configuration.

    Extends ExchangeConfig with Binance-specific options.
    """

    model_config = {"extra": "forbid"}


class CoinbaseProConfig(ExchangeConfig):
    """
    Coinbase Pro-specific configuration.

    Extends ExchangeConfig with Coinbase Pro-specific options.
    Coinbase Pro requires a passphrase in addition to API key and secret.
    """

    @model_validator(mode="after")
    def validate_coinbase_password(self) -> "CoinbaseProConfig":
        """Validate that password is provided for authenticated operations."""
        # If api_key is provided, password (passphrase) is required
        if self.api_key and not self.password:
            raise ValueError(
                "Coinbase Pro requires a passphrase (password field) "
                "when using API key authentication"
            )
        return self

    model_config = {"extra": "forbid"}
