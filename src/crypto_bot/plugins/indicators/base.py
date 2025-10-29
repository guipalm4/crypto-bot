"""Base interfaces and types for technical indicator plugins.

This module defines the canonical interface that every indicator plugin must
implement so it can be discovered and executed by the indicator loader.

Design goals:
- Clear, explicit, and strongly-typed contract
- Independence from concrete libraries (e.g., pandas-ta) at the interface level
- Consistent parameter validation and error signaling
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

import pandas as pd


@dataclass(frozen=True)
class IndicatorMetadata:
    """Describes an indicator's identity and basic characteristics.

    - name: short machine-friendly name (e.g., "rsi", "ema")
    - version: semantic or simple version to help with evolution/migrations
    - description: short human description
    """

    name: str
    version: str = "1.0"
    description: str = ""


class InvalidIndicatorParameters(ValueError):
    """Raised when provided parameters are invalid for an indicator."""


@runtime_checkable
class Indicator(Protocol):
    """Protocol for technical indicator plugins.

    Implementations should be side-effect free and must not mutate the input
    DataFrame. Results should be returned as a new Series or DataFrame.
    """

    @property
    def metadata(self) -> IndicatorMetadata:
        """Static metadata describing the indicator."""

    def validate_parameters(self, params: Mapping[str, Any]) -> None:
        """Validate user-provided parameters.

        Should raise InvalidIndicatorParameters with a helpful message when
        parameters are missing/invalid and provide defaulting rules otherwise.
        """

    def calculate(
        self, data: pd.DataFrame, params: Mapping[str, Any]
    ) -> pd.Series | pd.DataFrame:
        """Compute the indicator using the provided OHLCV data.

        Expected columns typically include: "open", "high", "low", "close",
        and optionally "volume". Implementations should document any specific
        requirements and provide sensible defaults.
        """


class BaseIndicator(ABC):
    """Abstract base class to simplify implementing indicators.

    Concrete indicators should:
    - set `metadata` with a stable name (lowercase, no spaces)
    - implement `validate_parameters`
    - implement `_calculate_impl`
    """

    metadata: IndicatorMetadata

    @abstractmethod
    def validate_parameters(
        self, params: Mapping[str, Any]
    ) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    @abstractmethod
    def _calculate_impl(
        self, data: pd.DataFrame, params: Mapping[str, Any]
    ) -> pd.Series | pd.DataFrame:  # pragma: no cover - interface
        raise NotImplementedError

    def calculate(
        self, data: pd.DataFrame, params: Mapping[str, Any]
    ) -> pd.Series | pd.DataFrame:
        """Template method providing common validation and immutability guard."""
        if not isinstance(data, pd.DataFrame):  # Fast sanity check
            raise TypeError("data must be a pandas.DataFrame")

        # Validate parameters first for consistent error messages
        self.validate_parameters(params)

        # Avoid mutating caller-provided DataFrame by working on a copy of the
        # narrowest set needed inside implementations when required.
        result = self._calculate_impl(data.copy(deep=False), params)
        if not isinstance(result, (pd.Series, pd.DataFrame)):
            raise TypeError("calculate() must return a pandas Series or DataFrame")
        return result
