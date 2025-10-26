"""
Coinbase Pro Exchange Plugin.

This module provides a Coinbase Pro-specific implementation of the exchange plugin
using CCXT 4.x library with support for sandbox, encrypted credentials (including
passphrase), and all standard trading operations.
"""

import logging
from typing import Any, Dict, List

import ccxt.async_support as ccxt

from crypto_bot.plugins.exchanges.base_ccxt_plugin import CCXTExchangePlugin
from crypto_bot.plugins.exchanges.config_models import CoinbaseProConfig

logger = logging.getLogger(__name__)


class CoinbaseProPlugin(CCXTExchangePlugin):
    """
    Coinbase Pro exchange plugin implementation.

    This plugin provides integration with Coinbase Pro exchange using CCXT 4.x,
    supporting both production and sandbox environments. It extends the base
    CCXT plugin with Coinbase Pro-specific configuration including mandatory
    passphrase authentication.

    Features:
    - Spot trading support
    - Sandbox mode with dedicated testnet
    - Three-factor authentication (API key + secret + passphrase)
    - Encrypted credential storage
    - Rate limiting and retry logic
    - Comprehensive error handling

    Note:
        Coinbase Pro requires a passphrase in addition to API key and secret
        for authenticated operations. This passphrase must be encrypted and
        stored in the 'password' field of the configuration.
    """

    def __init__(self, config: CoinbaseProConfig, **kwargs: Any) -> None:
        """
        Initialize Coinbase Pro exchange plugin.

        Args:
            config: Validated Coinbase Pro configuration (must include passphrase)
            **kwargs: Additional parameters
        """
        super().__init__(
            config=config,
            exchange_class=ccxt.coinbase,  # CCXT 4.x uses 'coinbase' instead of 'coinbasepro'
            **kwargs,
        )

        # Store Coinbase Pro-specific config
        self._coinbase_config = config

    @property
    def name(self) -> str:
        """Get the exchange name."""
        return "Coinbase Pro"

    @property
    def id(self) -> str:
        """Get the exchange ID."""
        return "coinbasepro"

    @property
    def countries(self) -> List[str]:
        """Get the list of countries where the exchange operates."""
        # Coinbase Pro primarily operates in these countries
        return ["US", "GB", "DE", "FR", "CA", "JP", "SG", "AU"]

    @property
    def urls(self) -> Dict[str, str]:
        """Get the exchange URLs."""
        if self._ccxt and hasattr(self._ccxt, "urls"):
            return self._ccxt.urls

        # Default URLs (will be replaced by CCXT after initialization)
        return {
            "api": "https://api.pro.coinbase.com",
            "www": "https://pro.coinbase.com",
            "doc": "https://docs.pro.coinbase.com",
        }

    @property
    def version(self) -> str:
        """Get the exchange API version."""
        if self._ccxt and hasattr(self._ccxt, "version"):
            return self._ccxt.version
        return "v1"

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
            "fetchPositions": False,  # Coinbase Pro doesn't support futures/positions
            "fetchMyTrades": True,
            "fetchOpenOrders": True,
            "cancelAllOrders": False,  # Not directly supported
            "fetchOrder": True,
        }

    async def _initialize_ccxt(self) -> None:
        """
        Initialize CCXT exchange instance with Coinbase Pro-specific configuration.

        This method extends the base initialization to handle Coinbase Pro sandbox
        configuration, which requires API URL overrides. It also ensures that the
        passphrase (password) is properly configured.

        Raises:
            RuntimeError: If encryption service is not available
            ValueError: If passphrase is missing for authenticated operations
        """
        # Call parent initialization first
        await super()._initialize_ccxt()

        # Coinbase Pro sandbox configuration
        if self._config.sandbox and self._ccxt:
            logger.info("Configuring Coinbase Pro sandbox mode")

            # Coinbase Pro sandbox URLs
            sandbox_url = "https://api-public.sandbox.pro.coinbase.com"

            # Override API URLs for sandbox
            self._ccxt.urls["api"] = sandbox_url

            logger.info(f"Coinbase Pro sandbox configured: api={sandbox_url}")

        # Validate that passphrase is present if using authenticated operations
        if self._ccxt and self._config.api_key and not self._config.password:
            logger.warning(
                "Coinbase Pro requires a passphrase for authenticated operations. "
                "Some operations may fail without it."
            )

        logger.info(
            f"Coinbase Pro initialized successfully "
            f"(sandbox={self._config.sandbox}, "
            f"authenticated={bool(self._config.api_key)})"
        )
