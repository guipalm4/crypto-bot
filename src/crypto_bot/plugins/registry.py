"""
Plugin registry and loader system.

This module provides functionality for discovering, loading, and managing
exchange and indicator plugins dynamically.
"""

import importlib
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Union
from abc import ABC

from crypto_bot.infrastructure.exchanges.base import ExchangeBase

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass


class PluginNotFound(PluginError):
    """Raised when a plugin cannot be found."""
    pass


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""
    pass


class PluginValidationError(PluginError):
    """Raised when a plugin fails validation."""
    pass


class PluginRegistry(ABC):
    """
    Abstract base class for plugin registries.
    
    This class provides the common interface for plugin discovery,
    loading, and management functionality.
    """
    
    def __init__(self, plugin_directory: str, base_class: Type[ABC]):
        """
        Initialize the plugin registry.
        
        Args:
            plugin_directory: Directory path where plugins are located
            base_class: Base class that all plugins must inherit from
        """
        self.plugin_directory = Path(plugin_directory)
        self.base_class = base_class
        self._plugins: Dict[str, Type[ABC]] = {}
        self._instances: Dict[str, ABC] = {}
        self._loaded = False
    
    @property
    def plugins(self) -> Dict[str, Type[ABC]]:
        """
        Get all registered plugin classes.
        
        Returns:
            Dictionary mapping plugin names to plugin classes
        """
        if not self._loaded:
            self.load_plugins()
        return self._plugins.copy()
    
    @property
    def plugin_names(self) -> List[str]:
        """
        Get list of all registered plugin names.
        
        Returns:
            List of plugin names
        """
        return list(self.plugins.keys())
    
    def load_plugins(self) -> None:
        """
        Load all plugins from the plugin directory.
        
        This method scans the plugin directory for Python modules,
        imports them, and registers any classes that inherit from
        the base class.
        
        Raises:
            PluginLoadError: If plugin loading fails
        """
        if self._loaded:
            return
        
        if not self.plugin_directory.exists():
            logger.warning(f"Plugin directory {self.plugin_directory} does not exist")
            self._loaded = True
            return
        
        try:
            # Add plugin directory to Python path if not already there
            plugin_path = str(self.plugin_directory.parent)
            if plugin_path not in sys.path:
                sys.path.insert(0, plugin_path)
            
            # Discover and load plugins
            self._discover_plugins()
            self._loaded = True
            logger.info(f"Loaded {len(self._plugins)} plugins from {self.plugin_directory}")
            
        except Exception as e:
            logger.error(f"Failed to load plugins from {self.plugin_directory}: {e}")
            raise PluginLoadError(f"Failed to load plugins: {e}") from e
    
    def _discover_plugins(self) -> None:
        """
        Discover plugins in the plugin directory.
        
        This method recursively scans the plugin directory for Python
        modules and attempts to load them.
        """
        for py_file in self.plugin_directory.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue
            
            try:
                self._load_plugin_from_file(py_file)
            except Exception as e:
                logger.warning(f"Failed to load plugin from {py_file}: {e}")
                continue
    
    def _load_plugin_from_file(self, file_path: Path) -> None:
        """
        Load plugins from a specific Python file.
        
        Args:
            file_path: Path to the Python file to load
        """
        # Convert file path to module name
        relative_path = file_path.relative_to(self.plugin_directory.parent)
        module_name = str(relative_path.with_suffix("")).replace(os.sep, ".")
        
        try:
            # Import the module
            module = importlib.import_module(module_name)
            
            # Find classes that inherit from the base class
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (obj is not self.base_class and 
                    issubclass(obj, self.base_class) and 
                    obj.__module__ == module.__name__):
                    
                    # Validate the plugin
                    self._validate_plugin(obj)
                    
                    # Register the plugin
                    plugin_name = self._get_plugin_name(obj)
                    self._plugins[plugin_name] = obj
                    logger.debug(f"Registered plugin: {plugin_name} ({obj.__name__})")
        
        except Exception as e:
            logger.error(f"Failed to load module {module_name}: {e}")
            raise PluginLoadError(f"Failed to load module {module_name}: {e}") from e
    
    def _validate_plugin(self, plugin_class: Type[ABC]) -> None:
        """
        Validate that a plugin class is properly implemented.
        
        Args:
            plugin_class: Plugin class to validate
            
        Raises:
            PluginValidationError: If plugin validation fails
        """
        # Check if the class is abstract
        if inspect.isabstract(plugin_class):
            raise PluginValidationError(f"Plugin class {plugin_class.__name__} is abstract")
        
        # Check if all abstract methods are implemented
        abstract_methods = getattr(plugin_class, '__abstractmethods__', set())
        if abstract_methods:
            raise PluginValidationError(
                f"Plugin class {plugin_class.__name__} has unimplemented abstract methods: {abstract_methods}"
            )
        
        # Additional validation can be added here
        self._validate_plugin_specific(plugin_class)
    
    def _validate_plugin_specific(self, plugin_class: Type[ABC]) -> None:
        """
        Perform plugin-specific validation.
        
        This method can be overridden by subclasses to add
        specific validation logic for their plugin types.
        
        Args:
            plugin_class: Plugin class to validate
        """
        pass
    
    def _get_plugin_name(self, plugin_class: Type[ABC]) -> str:
        """
        Get the name for a plugin class.
        
        Args:
            plugin_class: Plugin class
            
        Returns:
            Plugin name
        """
        # For ExchangeBase, try to get 'id' first, then 'name'
        if hasattr(plugin_class, '__bases__') and any(issubclass(base, ExchangeBase) for base in plugin_class.__bases__):
            # Try 'id' attribute first
            if 'id' in plugin_class.__dict__:
                id_value = plugin_class.__dict__['id']
                if isinstance(id_value, str):
                    return id_value
            
            # Fall back to 'name' attribute
            if 'name' in plugin_class.__dict__:
                name_value = plugin_class.__dict__['name']
                if isinstance(name_value, str):
                    return name_value.lower()  # Convert to lowercase for consistency
        
        # Try to get name from class attribute (check if it's defined in the class itself)
        if 'name' in plugin_class.__dict__:
            name_value = plugin_class.__dict__['name']
            # Check if it's a string value, not a property object
            if isinstance(name_value, str):
                return name_value.lower()  # Convert to lowercase for consistency
        
        # Fall back to class name in lowercase
        return plugin_class.__name__.lower()
    
    def get_plugin(self, name: str) -> Type[ABC]:
        """
        Get a plugin class by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin class
            
        Raises:
            PluginNotFound: If plugin is not found
        """
        if not self._loaded:
            self.load_plugins()
        
        if name not in self._plugins:
            available = ", ".join(self.plugin_names)
            raise PluginNotFound(f"Plugin '{name}' not found. Available plugins: {available}")
        
        return self._plugins[name]
    
    def create_instance(self, name: str, *args, **kwargs) -> ABC:
        """
        Create an instance of a plugin.
        
        Args:
            name: Plugin name
            *args: Positional arguments for plugin constructor
            **kwargs: Keyword arguments for plugin constructor
            
        Returns:
            Plugin instance
            
        Raises:
            PluginNotFound: If plugin is not found
            PluginLoadError: If instance creation fails
        """
        plugin_class = self.get_plugin(name)
        
        try:
            instance = plugin_class(*args, **kwargs)
            
            # For ExchangePluginRegistry, store multiple instances
            if hasattr(self, '_instances'):
                # Store with unique key
                instance_key = f"{name}_{id(instance)}"
                self._instances[instance_key] = instance
                # Only store with original name if this is the first instance
                if name not in self._instances:
                    self._instances[name] = instance
                else:
                    # If there's already an instance with the original name, remove it
                    # to avoid confusion with multiple instances
                    if self._instances[name] is not instance:
                        del self._instances[name]
            else:
                # For base PluginRegistry, only store one instance per name
                self._instances[name] = instance
                
            return instance
        except Exception as e:
            logger.error(f"Failed to create instance of plugin '{name}': {e}")
            raise PluginLoadError(f"Failed to create instance of plugin '{name}': {e}") from e
    
    def get_instance(self, name: str) -> Optional[ABC]:
        """
        Get an existing plugin instance.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin instance if exists, None otherwise
        """
        return self._instances.get(name)
    
    def has_plugin(self, name: str) -> bool:
        """
        Check if a plugin is registered.
        
        Args:
            name: Plugin name
            
        Returns:
            True if plugin is registered, False otherwise
        """
        if not self._loaded:
            self.load_plugins()
        
        return name in self._plugins
    
    def reload_plugins(self) -> None:
        """
        Reload all plugins from the plugin directory.
        
        This method clears the current plugin registry and
        reloads all plugins from the directory.
        """
        self._plugins.clear()
        self._instances.clear()
        self._loaded = False
        self.load_plugins()
    
    def unload_plugin(self, name: str) -> None:
        """
        Unload a specific plugin.
        
        Args:
            name: Plugin name
            
        Raises:
            PluginNotFound: If plugin is not found
        """
        if name not in self._plugins:
            raise PluginNotFound(f"Plugin '{name}' not found")
        
        # Remove from registry
        del self._plugins[name]
        
        # Close and remove instance if exists
        if name in self._instances:
            instance = self._instances[name]
            if hasattr(instance, 'close'):
                try:
                    instance.close()
                except Exception as e:
                    logger.warning(f"Failed to close plugin instance '{name}': {e}")
            del self._instances[name]
        
        logger.info(f"Unloaded plugin: {name}")


class ExchangePluginRegistry(PluginRegistry):
    """
    Registry for exchange plugins.
    
    This class manages the discovery, loading, and instantiation of
    exchange plugins that implement the ExchangeBase interface.
    """
    
    def __init__(self, plugin_directory: Optional[str] = None):
        """
        Initialize the exchange plugin registry.
        
        Args:
            plugin_directory: Directory path where exchange plugins are located.
                             Defaults to the exchanges plugin directory.
        """
        if plugin_directory is None:
            # Default to the exchanges plugin directory
            current_dir = Path(__file__).parent
            plugin_directory = str(current_dir / "exchanges")
        
        super().__init__(plugin_directory, ExchangeBase)
    
    def _validate_plugin_specific(self, plugin_class: Type[ExchangeBase]) -> None:
        """
        Perform exchange-specific validation.
        
        Args:
            plugin_class: Exchange plugin class to validate
        """
        # Check if the plugin has required attributes
        required_attributes = ['name', 'id', 'countries', 'urls', 'version']
        for attr in required_attributes:
            if not hasattr(plugin_class, attr):
                raise PluginValidationError(
                    f"Exchange plugin {plugin_class.__name__} missing required attribute: {attr}"
                )
        
        # Check if the plugin has required methods
        required_methods = [
            'initialize', 'load_markets', 'fetch_markets', 'fetch_ticker',
            'create_order', 'cancel_order', 'fetch_balance'
        ]
        
        for method_name in required_methods:
            if not hasattr(plugin_class, method_name):
                raise PluginValidationError(
                    f"Exchange plugin {plugin_class.__name__} missing required method: {method_name}"
                )
            
            method = getattr(plugin_class, method_name)
            if not callable(method):
                raise PluginValidationError(
                    f"Exchange plugin {plugin_class.__name__} attribute '{method_name}' is not callable"
                )
    
    def get_exchange(self, name: str, *args, **kwargs) -> ExchangeBase:
        """
        Get an exchange instance by name.
        
        Args:
            name: Exchange name (e.g., 'binance', 'coinbase')
            *args: Positional arguments for exchange constructor
            **kwargs: Keyword arguments for exchange constructor
            
        Returns:
            Exchange instance
            
        Raises:
            PluginNotFound: If exchange is not found
            PluginLoadError: If instance creation fails
        """
        return self.create_instance(name, *args, **kwargs)
    
    def list_exchanges(self) -> List[str]:
        """
        List all available exchange names.
        
        Returns:
            List of exchange names
        """
        return self.plugin_names
    
    def get_exchange_info(self, name: str) -> Dict[str, Any]:
        """
        Get information about an exchange plugin.
        
        Args:
            name: Exchange name
            
        Returns:
            Dictionary containing exchange information
            
        Raises:
            PluginNotFound: If exchange is not found
        """
        plugin_class = self.get_plugin(name)
        
        info = {
            'name': getattr(plugin_class, 'name', 'Unknown'),
            'id': getattr(plugin_class, 'id', 'unknown'),
            'countries': getattr(plugin_class, 'countries', []),
            'urls': getattr(plugin_class, 'urls', {}),
            'version': getattr(plugin_class, 'version', 'Unknown'),
            'certified': getattr(plugin_class, 'certified', False),
            'has': getattr(plugin_class, 'has', {}),
            'class_name': plugin_class.__name__,
            'module': plugin_class.__module__,
        }
        
        return info


# Global registry instance
exchange_registry = ExchangePluginRegistry()
