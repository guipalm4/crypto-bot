"""Technical indicator plugins for the crypto bot."""

from crypto_bot.plugins.indicators.base import (
    BaseIndicator,
    Indicator,
    IndicatorMetadata,
    InvalidIndicatorParameters,
)
from crypto_bot.plugins.indicators.cache import IndicatorCache, get_cache
from crypto_bot.plugins.indicators.loader import (
    IndicatorPluginRegistry,
    indicator_registry,
)
from crypto_bot.plugins.indicators.pandas_ta_indicators import (
    EMAIndicator,
    MACDIndicator,
    RSIIndicator,
    SMAIndicator,
)

__all__ = [
    "BaseIndicator",
    "Indicator",
    "IndicatorMetadata",
    "InvalidIndicatorParameters",
    "IndicatorPluginRegistry",
    "indicator_registry",
    "IndicatorCache",
    "get_cache",
    "RSIIndicator",
    "EMAIndicator",
    "SMAIndicator",
    "MACDIndicator",
]
