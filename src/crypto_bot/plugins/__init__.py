"""
Plugin system module.

This module provides the plugin registry and loader functionality for
dynamic loading of exchange and indicator plugins.
"""

from .registry import PluginRegistry, ExchangePluginRegistry

__all__ = ["PluginRegistry", "ExchangePluginRegistry"]
