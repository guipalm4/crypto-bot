"""
Binance Exchange Plugin.

This module provides a Binance-specific implementation of the exchange plugin
using CCXT 4.x library with support for testnet, encrypted credentials, and
all standard trading operations.
"""

import logging
from typing import Any, Dict, List

import ccxt.async_support as ccxt

from crypto_bot.plugins.exchanges.base_ccxt_plugin import CCXTExchangePlugin
from crypto_bot.plugins.exchanges.config_models import BinanceConfig

logger = logging.getLogger(__name__)


class BinancePlugin(CCXTExchangePlugin):
    """
    Binance exchange plugin implementation.

    This plugin provides integration with Binance exchange using CCXT 4.x,
    supporting both production and testnet environments. It extends the base
    CCXT plugin with Binance-specific configuration and initialization.

    Features:
    - Spot trading support
    - Futures trading support (via options)
    - Testnet/sandbox mode
    - Encrypted credential storage
    - Rate limiting and retry logic
    - Comprehensive error handling
    """

    def __init__(self, config: BinanceConfig, **kwargs: Any) -> None:
        """
        Initialize Binance exchange plugin.

        Args:
            config: Validated Binance configuration
            **kwargs: Additional parameters
        """
        super().__init__(
            config=config,
            exchange_class=ccxt.binance,
            **kwargs,
        )

        # Store Binance-specific config
        self._binance_config = config

    @property
    def name(self) -> str:
        """Get the exchange name."""
        return "Binance"

    @property
    def id(self) -> str:
        """Get the exchange ID."""
        return "binance"

    @property
    def countries(self) -> List[str]:
        """Get the list of countries where the exchange operates."""
        # Binance operates globally with some restrictions
        return ["JP", "MT", "US", "GB", "SG", "KR"]

    @property
    def urls(self) -> Dict[str, str]:
        """Get the exchange URLs."""
        if self._ccxt and hasattr(self._ccxt, "urls"):
            return self._ccxt.urls

        # Default URLs (will be replaced by CCXT after initialization)
        return {
            "api": "https://api.binance.com",
            "www": "https://www.binance.com",
            "doc": "https://binance-docs.github.io/apidocs/spot/en/",
        }

    @property
    def version(self) -> str:
        """Get the exchange API version."""
        if self._ccxt and hasattr(self._ccxt, "version"):
            return self._ccxt.version
        return "v3"

    @property
    def certified(self) -> bool:
        """Check if the exchange is certified by CCXT."""
        return True

    @property
    def has(self) -> Dict[str, bool]:
        """Get the capabilities of the exchange."""
        if self._ccxt and hasattr(self._ccxt, "has"):
            return self._ccxt.has

        # Default capabilities (will be replaced by CCXT after initialization)
        return {
            "createOrder": True,
            "cancelOrder": True,
            "fetchBalance": True,
            "fetchTicker": True,
            "fetchTickers": True,
            "fetchOrderBook": True,
            "fetchOHLCV": True,
            "fetchTrades": True,
            "fetchMarkets": True,
            "fetchPositions": True,
            "fetchMyTrades": True,
            "fetchOpenOrders": True,
            "cancelAllOrders": True,
            "fetchOrder": True,
        }

    async def _initialize_ccxt(self) -> None:
        """
        Initialize CCXT exchange instance with Binance-specific configuration.

        This method extends the base initialization to handle Binance testnet
        configuration, which requires URL overrides instead of set_sandbox_mode().

        Raises:
            RuntimeError: If encryption service is not available
            ValueError: If required credentials are missing
        """
        # Call parent initialization first
        await super()._initialize_ccxt()

        # Binance testnet configuration
        if self._config.sandbox and self._ccxt:
            logger.info("Configuring Binance testnet mode")

            # Binance testnet uses different URLs
            # Spot testnet
            testnet_urls = {
                "api": {
                    "public": "https://testnet.binance.vision/api",
                    "private": "https://testnet.binance.vision/api",
                },
            }

            # Override URLs for testnet
            self._ccxt.urls["api"] = testnet_urls["api"]

            logger.info(
                f"Binance testnet configured: " f"api={testnet_urls['api']['public']}"
            )

        # Configure default trading type if specified in options
        if self._ccxt and "defaultType" in self._config.options:
            default_type = self._config.options["defaultType"]
            logger.info(f"Setting Binance default trading type: {default_type}")
            # This will be used by CCXT for futures/spot selection
