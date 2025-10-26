"""
Plugin system module.

This module provides the plugin registry and loader functionality for
dynamic loading of exchange and indicator plugins.
"""

from .registry import ExchangePluginRegistry, PluginRegistry

__all__ = ["PluginRegistry", "ExchangePluginRegistry"]
