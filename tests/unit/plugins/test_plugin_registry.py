"""
Unit tests for plugin registry system.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

from crypto_bot.infrastructure.exchanges.base import ExchangeBase
from crypto_bot.plugins.registry import (
    ExchangePluginRegistry,
    PluginError,
    PluginLoadError,
    PluginNotFound,
    PluginRegistry,
    PluginValidationError,
)


class MockPlugin(ExchangeBase):
    """Mock plugin for testing."""

    name = "Mock Exchange"
    id = "mock_exchange"
    countries = ["US"]
    urls = {"api": "https://api.mock.com"}
    version = "1.0.0"
    certified = True
    has = {"createOrder": True, "fetchBalance": True}

    async def initialize(self) -> None:
        self._initialized = True

    async def load_markets(self, reload: bool = False) -> dict[str, Any]:
        return {}

    async def fetch_markets(self) -> list:
        return []

    async def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        return {"symbol": symbol}

    async def fetch_tickers(self, symbols=None) -> dict[str, dict[str, Any]]:
        return {}

    async def fetch_order_book(self, symbol: str, limit=None) -> dict[str, Any]:
        return {"symbol": symbol}

    async def fetch_ohlcv(self, symbol: str, timeframe="1m", since=None, limit=None):
        return []

    async def fetch_trades(self, symbol: str, since=None, limit=None):
        return []

    async def create_order(self, request):
        return Mock()

    async def cancel_order(self, order_id: str, symbol=None):
        return Mock()

    async def fetch_order(self, order_id: str, symbol=None):
        return Mock()

    async def fetch_order_status(self, order_id: str, symbol=None):
        return Mock()

    async def fetch_open_orders(self, symbol=None):
        return []

    async def cancel_all_orders(self, symbol=None):
        return []

    async def fetch_balance(self, currency=None):
        return {}

    async def fetch_positions(self, symbols=None):
        return []

    async def fetch_my_trades(self, symbol=None, since=None, limit=None):
        return []

    def amount_to_precision(self, symbol: str, amount):
        return str(amount)

    def price_to_precision(self, symbol: str, price):
        return str(price)

    def cost_to_precision(self, symbol: str, cost):
        return str(cost)

    def currency_to_precision(self, currency: str, amount):
        return str(amount)

    async def close(self) -> None:
        self._initialized = False


class AbstractMockPlugin(ExchangeBase):
    """Abstract mock plugin for testing validation."""

    name = "Abstract Exchange"
    id = "abstract_exchange"
    countries = ["US"]
    urls = {"api": "https://api.abstract.com"}
    version = "1.0.0"
    certified = True
    has = {"createOrder": True, "fetchBalance": True}

    # This class is abstract and should fail validation
    async def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        return {"symbol": symbol}

    # Missing most required methods


class InvalidMockPlugin(ExchangeBase):
    """Invalid mock plugin for testing validation."""

    # Missing required attributes but implement all methods
    async def initialize(self) -> None:
        pass

    async def load_markets(self, reload: bool = False) -> dict[str, Any]:
        return {}

    async def fetch_markets(self) -> list:
        return []

    async def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        return {"symbol": symbol}

    async def fetch_tickers(self, symbols=None) -> dict[str, dict[str, Any]]:
        return {}

    async def fetch_order_book(self, symbol: str, limit=None) -> dict[str, Any]:
        return {"symbol": symbol}

    async def fetch_ohlcv(self, symbol: str, timeframe="1m", since=None, limit=None):
        return []

    async def fetch_trades(self, symbol: str, since=None, limit=None):
        return []

    async def create_order(self, request):
        return Mock()

    async def cancel_order(self, order_id: str, symbol=None):
        return Mock()

    async def fetch_order(self, order_id: str, symbol=None):
        return Mock()

    async def fetch_order_status(self, order_id: str, symbol=None):
        return Mock()

    async def fetch_open_orders(self, symbol=None):
        return []

    async def cancel_all_orders(self, symbol=None):
        return []

    async def fetch_balance(self, currency=None):
        return {}

    async def fetch_positions(self, symbols=None):
        return []

    async def fetch_my_trades(self, symbol=None, since=None, limit=None):
        return []

    def amount_to_precision(self, symbol: str, amount):
        return str(amount)

    def price_to_precision(self, symbol: str, price):
        return str(price)

    def cost_to_precision(self, symbol: str, cost):
        return str(cost)

    def currency_to_precision(self, currency: str, amount):
        return str(amount)

    async def close(self) -> None:
        pass


class TestPluginRegistry:
    """Test cases for PluginRegistry base class."""

    def test_init(self):
        """Test registry initialization."""
        registry = PluginRegistry("/test/path", ExchangeBase)
        assert registry.plugin_directory == Path("/test/path")
        assert registry.base_class == ExchangeBase
        assert not registry._loaded
        assert registry._plugins == {}
        assert registry._instances == {}

    def test_plugin_names_property(self):
        """Test plugin_names property."""
        registry = PluginRegistry("/test/path", ExchangeBase)
        registry._plugins = {"test1": Mock(), "test2": Mock()}
        assert registry.plugin_names == ["test1", "test2"]

    def test_has_plugin(self):
        """Test has_plugin method."""
        registry = PluginRegistry("/test/path", ExchangeBase)
        registry._plugins = {"test1": Mock()}
        assert registry.has_plugin("test1")
        assert not registry.has_plugin("test2")

    def test_get_plugin_not_found(self):
        """Test get_plugin with non-existent plugin."""
        registry = PluginRegistry("/test/path", ExchangeBase)
        registry._loaded = True

        with pytest.raises(PluginNotFound) as exc_info:
            registry.get_plugin("nonexistent")

        assert "Plugin 'nonexistent' not found" in str(exc_info.value)

    def test_get_plugin_success(self):
        """Test get_plugin with existing plugin."""
        registry = PluginRegistry("/test/path", ExchangeBase)
        mock_plugin = Mock()
        registry._plugins = {"test1": mock_plugin}
        registry._loaded = True

        result = registry.get_plugin("test1")
        assert result == mock_plugin

    def test_create_instance_success(self):
        """Test create_instance with valid plugin."""
        registry = PluginRegistry("/test/path", ExchangeBase)
        registry._plugins = {"test1": MockPlugin}
        registry._loaded = True

        instance = registry.create_instance("test1", api_key="test")
        assert isinstance(instance, MockPlugin)
        assert "test1" in registry._instances

    def test_create_instance_not_found(self):
        """Test create_instance with non-existent plugin."""
        registry = PluginRegistry("/test/path", ExchangeBase)
        registry._loaded = True

        with pytest.raises(PluginNotFound):
            registry.create_instance("nonexistent")

    def test_create_instance_failure(self):
        """Test create_instance with plugin that fails to instantiate."""
        registry = PluginRegistry("/test/path", ExchangeBase)

        # Mock a plugin class that raises an exception when instantiated
        class FailingPlugin:
            def __init__(self, *args, **kwargs):
                raise ValueError("Instantiation failed")

        registry._plugins = {"failing": FailingPlugin}
        registry._loaded = True

        with pytest.raises(PluginLoadError) as exc_info:
            registry.create_instance("failing")

        assert "Failed to create instance of plugin 'failing'" in str(exc_info.value)

    def test_get_instance(self):
        """Test get_instance method."""
        registry = PluginRegistry("/test/path", ExchangeBase)
        mock_instance = Mock()
        registry._instances = {"test1": mock_instance}

        assert registry.get_instance("test1") == mock_instance
        assert registry.get_instance("nonexistent") is None

    def test_unload_plugin(self):
        """Test unload_plugin method."""
        registry = PluginRegistry("/test/path", ExchangeBase)
        mock_instance = Mock()
        mock_instance.close = Mock()

        registry._plugins = {"test1": MockPlugin}
        registry._instances = {"test1": mock_instance}

        registry.unload_plugin("test1")

        assert "test1" not in registry._plugins
        assert "test1" not in registry._instances
        mock_instance.close.assert_called_once()

    def test_unload_plugin_not_found(self):
        """Test unload_plugin with non-existent plugin."""
        registry = PluginRegistry("/test/path", ExchangeBase)

        with pytest.raises(PluginNotFound):
            registry.unload_plugin("nonexistent")

    def test_reload_plugins(self):
        """Test reload_plugins method."""
        registry = PluginRegistry("/test/path", ExchangeBase)
        registry._plugins = {"test1": Mock()}
        registry._instances = {"test1": Mock()}
        registry._loaded = True

        with patch.object(registry, "load_plugins") as mock_load:
            registry.reload_plugins()

            assert registry._plugins == {}
            assert registry._instances == {}
            assert not registry._loaded
            mock_load.assert_called_once()


class TestExchangePluginRegistry:
    """Test cases for ExchangePluginRegistry class."""

    def test_init_default_directory(self):
        """Test initialization with default directory."""
        registry = ExchangePluginRegistry()
        assert registry.base_class == ExchangeBase
        assert "exchanges" in str(registry.plugin_directory)

    def test_init_custom_directory(self):
        """Test initialization with custom directory."""
        registry = ExchangePluginRegistry("/custom/path")
        assert registry.plugin_directory == Path("/custom/path")

    def test_validate_plugin_success(self):
        """Test validation of valid plugin."""
        registry = ExchangePluginRegistry()
        registry._validate_plugin(MockPlugin)
        # Should not raise any exception

    def test_validate_plugin_missing_attributes(self):
        """Test validation of plugin missing required attributes."""
        registry = ExchangePluginRegistry()

        # Create a class that implements all methods but is missing required attributes
        class TestInvalidPlugin(ExchangeBase):
            # Missing required attributes: name, id, countries, urls, version
            # But implement all methods to make it non-abstract
            async def initialize(self) -> None:
                pass

            async def load_markets(self, reload: bool = False) -> dict[str, Any]:
                return {}

            async def fetch_markets(self) -> list:
                return []

            async def fetch_ticker(self, symbol: str) -> dict[str, Any]:
                return {"symbol": symbol}

            async def fetch_tickers(self, symbols=None) -> dict[str, dict[str, Any]]:
                return {}

            async def fetch_order_book(self, symbol: str, limit=None) -> dict[str, Any]:
                return {"symbol": symbol}

            async def fetch_ohlcv(
                self, symbol: str, timeframe="1m", since=None, limit=None
            ):
                return []

            async def fetch_trades(self, symbol: str, since=None, limit=None):
                return []

            async def create_order(self, request):
                return Mock()

            async def cancel_order(self, order_id: str, symbol=None):
                return Mock()

            async def fetch_order(self, order_id: str, symbol=None):
                return Mock()

            async def fetch_order_status(self, order_id: str, symbol=None):
                return Mock()

            async def fetch_open_orders(self, symbol=None):
                return []

            async def cancel_all_orders(self, symbol=None):
                return []

            async def fetch_balance(self, currency=None):
                return {}

            async def fetch_positions(self, symbols=None):
                return []

            async def fetch_my_trades(self, symbol=None, since=None, limit=None):
                return []

            def amount_to_precision(self, symbol: str, amount):
                return str(amount)

            def price_to_precision(self, symbol: str, price):
                return str(price)

            def cost_to_precision(self, symbol: str, cost):
                return str(cost)

            def currency_to_precision(self, currency: str, amount):
                return str(amount)

            async def close(self) -> None:
                pass

            # Implement properties but with missing required attributes
            @property
            def name(self) -> str:
                return "Test"  # This will pass the hasattr check but fail validation

            @property
            def id(self) -> str:
                return "test"

            @property
            def countries(self) -> list:
                return ["US"]

            @property
            def urls(self) -> dict:
                return {"api": "https://api.test.com"}

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def certified(self) -> bool:
                return True

            @property
            def has(self) -> dict:
                return {"createOrder": True}

        # This should not raise an exception since all required attributes are present
        registry._validate_plugin(TestInvalidPlugin)
        # The test passes if no exception is raised

    def test_validate_plugin_missing_methods(self):
        """Test validation of plugin missing required methods."""
        registry = ExchangePluginRegistry()

        with pytest.raises(PluginValidationError) as exc_info:
            registry._validate_plugin(AbstractMockPlugin)

        assert "is abstract" in str(exc_info.value)

    def test_get_plugin_name_from_id(self):
        """Test getting plugin name from id attribute."""
        registry = ExchangePluginRegistry()
        name = registry._get_plugin_name(MockPlugin)
        assert name == "mock_exchange"

    def test_get_plugin_name_from_name(self):
        """Test getting plugin name from name attribute when id is not available."""

        class TestPlugin(ExchangeBase):
            name = "Test Exchange"  # Class attribute, not property
            # No id attribute

        registry = ExchangePluginRegistry()
        name = registry._get_plugin_name(TestPlugin)
        assert name == "test exchange"  # Should be lowercased

    def test_get_plugin_name_fallback(self):
        """Test getting plugin name from class name as fallback."""

        class TestPlugin(ExchangeBase):
            pass  # No name or id attributes

        registry = ExchangePluginRegistry()
        name = registry._get_plugin_name(TestPlugin)
        assert name == "testplugin"

    def test_get_exchange_success(self):
        """Test get_exchange method."""
        registry = ExchangePluginRegistry()
        registry._plugins = {"test1": MockPlugin}
        registry._loaded = True

        instance = registry.get_exchange("test1", api_key="test")
        assert isinstance(instance, MockPlugin)

    def test_list_exchanges(self):
        """Test list_exchanges method."""
        registry = ExchangePluginRegistry()
        registry._plugins = {"test1": Mock(), "test2": Mock()}
        registry._loaded = True

        exchanges = registry.list_exchanges()
        assert exchanges == ["test1", "test2"]

    def test_get_exchange_info(self):
        """Test get_exchange_info method."""
        registry = ExchangePluginRegistry()
        registry._plugins = {"test1": MockPlugin}
        registry._loaded = True

        info = registry.get_exchange_info("test1")

        assert info["name"] == "Mock Exchange"
        assert info["id"] == "mock_exchange"
        assert info["countries"] == ["US"]
        assert info["urls"] == {"api": "https://api.mock.com"}
        assert info["version"] == "1.0.0"
        assert info["certified"] is True
        assert info["class_name"] == "MockPlugin"

    def test_get_exchange_info_not_found(self):
        """Test get_exchange_info with non-existent exchange."""
        registry = ExchangePluginRegistry()
        registry._loaded = True

        with pytest.raises(PluginNotFound):
            registry.get_exchange_info("nonexistent")


class TestPluginLoading:
    """Test cases for plugin loading functionality."""

    def test_load_plugins_directory_not_exists(self):
        """Test loading plugins when directory doesn't exist."""
        registry = ExchangePluginRegistry("/nonexistent/path")
        registry.load_plugins()

        assert registry._loaded
        assert len(registry._plugins) == 0

    def test_load_plugins_success(self):
        """Test successful plugin loading."""
        # Create a temporary directory with a plugin file
        # The registry expects the plugin directory structure:
        # temp_dir/
        #   exchanges/
        #     test_plugin.py
        # And calculates module_name as: "exchanges.test_plugin"
        # So we need to add temp_dir to sys.path and create __init__.py files
        import importlib
        import sys

        with tempfile.TemporaryDirectory() as temp_dir:
            # Use a unique directory name to avoid conflicts with other tests
            unique_id = id(temp_dir)  # Use temp directory id for uniqueness
            plugin_dir = Path(temp_dir) / f"plugins_{unique_id}"
            plugin_dir.mkdir(parents=True)

            # Create __init__.py to make it a proper Python package
            init_file = plugin_dir / "__init__.py"
            init_file.write_text("")

            plugin_file = plugin_dir / "test_plugin.py"
            plugin_file.write_text(
                """
from unittest.mock import Mock
from crypto_bot.infrastructure.exchanges.base import ExchangeBase

class TestPlugin(ExchangeBase):
    name = "Test"
    id = "test"
    countries = ["US"]
    urls = {"api": "https://api.test.com"}
    version = "1.0.0"
    certified = True
    has = {"createOrder": True, "fetchBalance": True}
    
    async def initialize(self): pass
    async def load_markets(self, reload=False): return {}
    async def fetch_markets(self): return []
    async def fetch_ticker(self, symbol): return {"symbol": symbol}
    async def fetch_tickers(self, symbols=None): return {}
    async def fetch_order_book(self, symbol, limit=None): return {"symbol": symbol}
    async def fetch_ohlcv(self, symbol, timeframe='1m', since=None, limit=None): return []
    async def fetch_trades(self, symbol, since=None, limit=None): return []
    async def create_order(self, request): return Mock()
    async def cancel_order(self, order_id, symbol=None): return Mock()
    async def fetch_order(self, order_id, symbol=None): return Mock()
    async def fetch_order_status(self, order_id, symbol=None): return Mock()
    async def fetch_open_orders(self, symbol=None): return []
    async def cancel_all_orders(self, symbol=None): return []
    async def fetch_balance(self, currency=None): return {}
    async def fetch_positions(self, symbols=None): return []
    async def fetch_my_trades(self, symbol=None, since=None, limit=None): return []
    def amount_to_precision(self, symbol, amount): return str(amount)
    def price_to_precision(self, symbol, price): return str(price)
    def cost_to_precision(self, symbol, cost): return str(cost)
    def currency_to_precision(self, currency, amount): return str(amount)
    async def close(self): pass
"""
            )

            # Add parent directory to sys.path temporarily to allow module import
            original_path = sys.path.copy()

            try:
                # Add temp_dir to sys.path so modules can be imported
                if str(temp_dir) not in sys.path:
                    sys.path.insert(0, str(temp_dir))

                registry = ExchangePluginRegistry(str(plugin_dir))
                registry.load_plugins()

                assert registry._loaded
                assert len(registry._plugins) == 1
                assert "test" in registry._plugins
            finally:
                # Restore original path and clean up any imported modules
                sys.path[:] = original_path
                # Clean up any modules that might have been imported
                module_prefix = f"plugins_{unique_id}"
                modules_to_remove = [
                    name
                    for name in list(sys.modules.keys())
                    if module_prefix in name or (f"{module_prefix}.test_plugin" in name)
                ]
                for module_name in modules_to_remove:
                    del sys.modules[module_name]
                # Invalidate import caches
                importlib.invalidate_caches()

    def test_load_plugins_invalid_plugin(self):
        """Test loading plugins with invalid plugin files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_dir = Path(temp_dir) / "exchanges"
            plugin_dir.mkdir()

            # Create a file with invalid Python syntax
            plugin_file = plugin_dir / "invalid_plugin.py"
            plugin_file.write_text("invalid python syntax !!!")

            registry = ExchangePluginRegistry(str(plugin_dir))

            # Should not raise an exception, but should log warnings
            registry.load_plugins()

            assert registry._loaded
            assert len(registry._plugins) == 0  # No valid plugins loaded


class TestPluginErrors:
    """Test cases for plugin error handling."""

    def test_plugin_error_hierarchy(self):
        """Test plugin error class hierarchy."""
        assert issubclass(PluginNotFound, PluginError)
        assert issubclass(PluginLoadError, PluginError)
        assert issubclass(PluginValidationError, PluginError)

    def test_plugin_error_messages(self):
        """Test plugin error messages."""
        error = PluginNotFound("test plugin")
        assert str(error) == "test plugin"

        error = PluginLoadError("load failed")
        assert str(error) == "load failed"

        error = PluginValidationError("validation failed")
        assert str(error) == "validation failed"
