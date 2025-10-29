"""Plugin loader for technical indicators.

This module provides functionality to discover, load, and manage technical
indicator plugins dynamically, following the same pattern as the exchange
plugin registry.
"""

from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import Any, cast

from crypto_bot.plugins.indicators.base import BaseIndicator, Indicator
from crypto_bot.plugins.registry import (
    PluginRegistry,
    PluginValidationError,
)

logger = logging.getLogger(__name__)


class IndicatorPluginRegistry(PluginRegistry):
    """
    Registry for technical indicator plugins.

    This class manages the discovery, loading, and instantiation of
    indicator plugins that implement the Indicator protocol or BaseIndicator.
    """

    def __init__(self, plugin_directory: str | None = None):
        """
        Initialize the indicator plugin registry.

        Args:
            plugin_directory: Directory path where indicator plugins are located.
                            Defaults to the indicators plugin directory.
        """
        if plugin_directory is None:
            # Default to the indicators plugin directory
            current_dir = Path(__file__).parent
            plugin_directory = str(current_dir)

        # Use BaseIndicator as the concrete base class for discovery
        super().__init__(plugin_directory, BaseIndicator)

    def _validate_plugin_specific(self, plugin_class: type) -> None:
        """
        Perform indicator-specific validation.

        Args:
            plugin_class: Indicator plugin class to validate

        Raises:
            PluginValidationError: If validation fails
        """
        # Check if it implements the Indicator protocol
        if not isinstance(plugin_class, type):
            raise PluginValidationError(f"Indicator class {plugin_class} is not a type")

        # Must have metadata attribute
        if not hasattr(plugin_class, "metadata"):
            raise PluginValidationError(
                f"Indicator plugin {plugin_class.__name__} missing required attribute: metadata"
            )

        # Check if metadata is a class attribute (descriptor) or instance attribute
        try:
            metadata = plugin_class.metadata
            # Check if it has the required attributes at least
            if not hasattr(metadata, "name"):
                raise PluginValidationError(
                    f"Indicator plugin {plugin_class.__name__} metadata missing 'name' attribute"
                )
        except AttributeError:
            raise PluginValidationError(
                f"Indicator plugin {plugin_class.__name__} metadata is not accessible"
            ) from None

        # Must have required methods
        required_methods = ["validate_parameters", "calculate"]
        for method_name in required_methods:
            if not hasattr(plugin_class, method_name):
                raise PluginValidationError(
                    f"Indicator plugin {plugin_class.__name__} missing required method: {method_name}"
                )

            method = getattr(plugin_class, method_name)
            if not callable(method):
                raise PluginValidationError(
                    f"Indicator plugin {plugin_class.__name__} attribute '{method_name}' is not callable"
                )

        # Check if it's an abstract class
        if inspect.isabstract(plugin_class):
            raise PluginValidationError(
                f"Indicator plugin {plugin_class.__name__} is abstract"
            )

        # Check for unimplemented abstract methods
        abstract_methods: set[str] = getattr(plugin_class, "__abstractmethods__", set())
        if abstract_methods:
            raise PluginValidationError(
                f"Indicator plugin {plugin_class.__name__} has unimplemented abstract methods: {abstract_methods}"
            )

    def _get_plugin_name(self, plugin_class: type) -> str:
        """
        Get the name for an indicator plugin class.

        Args:
            plugin_class: Indicator plugin class

        Returns:
            Plugin name (from metadata.name or class name)
        """
        # Try to get name from metadata
        if hasattr(plugin_class, "metadata"):
            metadata = plugin_class.metadata
            if hasattr(metadata, "name") and isinstance(metadata.name, str):
                return metadata.name.lower()

        # Fall back to class name in lowercase
        return plugin_class.__name__.lower().replace("indicator", "").strip("_")

    def get_indicator(self, name: str) -> type[BaseIndicator]:
        """
        Get an indicator plugin class by name.

        Args:
            name: Indicator name (e.g., 'rsi', 'ema', 'sma')

        Returns:
            Indicator plugin class

        Raises:
            PluginNotFound: If indicator is not found
        """
        plugin = self.get_plugin(name)
        return cast(type[BaseIndicator], plugin)

    def create_indicator_instance(self, name: str, **kwargs: Any) -> Indicator:
        """
        Create an instance of an indicator plugin.

        Args:
            name: Indicator name
            **kwargs: Keyword arguments for indicator constructor

        Returns:
            Indicator instance

        Raises:
            PluginNotFound: If indicator is not found
            PluginLoadError: If instance creation fails
        """
        instance = self.create_instance(name, **kwargs)
        return cast(Indicator, instance)

    def list_indicators(self) -> list[str]:
        """
        List all available indicator names.

        Returns:
            List of indicator names
        """
        return self.plugin_names

    def get_indicator_info(self, name: str) -> dict[str, Any]:
        """
        Get information about an indicator plugin.

        Args:
            name: Indicator name

        Returns:
            Dictionary containing indicator information

        Raises:
            PluginNotFound: If indicator is not found
        """
        plugin_class = cast(type[BaseIndicator], self.get_plugin(name))
        metadata = plugin_class.metadata

        info = {
            "name": metadata.name if hasattr(metadata, "name") else "Unknown",
            "version": metadata.version if hasattr(metadata, "version") else "Unknown",
            "description": (
                metadata.description if hasattr(metadata, "description") else ""
            ),
            "class_name": plugin_class.__name__,
            "module": plugin_class.__module__,
        }

        return info


# Global registry instance
indicator_registry = IndicatorPluginRegistry()
