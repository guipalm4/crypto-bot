"""
Unit tests for configuration schemas.
"""

import pytest
from pydantic import ValidationError

from crypto_bot.config.schemas import (
    ApiConfig,
    AppConfig,
    Config,
    DatabaseConfig,
    ExchangeConfig,
    LoggingConfig,
    RiskConfig,
    TradingConfig,
)


class TestAppConfig:
    """Test AppConfig schema."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        config = AppConfig()
        assert config.name == "Crypto Trading Bot"
        assert config.version == "0.1.0"
        assert config.log_level == "INFO"

    def test_custom_values(self) -> None:
        """Test custom values are accepted."""
        config = AppConfig(
            name="Custom Bot", version="1.0.0", log_level="DEBUG"
        )
        assert config.name == "Custom Bot"
        assert config.version == "1.0.0"
        assert config.log_level == "DEBUG"

    def test_invalid_log_level(self) -> None:
        """Test invalid log level raises error."""
        with pytest.raises(ValidationError):
            AppConfig(log_level="INVALID")


class TestDatabaseConfig:
    """Test DatabaseConfig schema."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        config = DatabaseConfig()
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.name == "crypto_bot"
        assert config.pool_size == 5

    def test_port_validation(self) -> None:
        """Test port validation."""
        # Valid port
        config = DatabaseConfig(port=3000)
        assert config.port == 3000

        # Invalid port (too low)
        with pytest.raises(ValidationError):
            DatabaseConfig(port=0)

        # Invalid port (too high)
        with pytest.raises(ValidationError):
            DatabaseConfig(port=70000)

    def test_pool_size_validation(self) -> None:
        """Test pool size validation."""
        # Valid pool size
        config = DatabaseConfig(pool_size=10)
        assert config.pool_size == 10

        # Invalid pool size (too low)
        with pytest.raises(ValidationError):
            DatabaseConfig(pool_size=0)

        # Invalid pool size (too high)
        with pytest.raises(ValidationError):
            DatabaseConfig(pool_size=200)


class TestRiskConfig:
    """Test RiskConfig schema."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        config = RiskConfig()
        assert config.max_position_size_pct == 10.0
        assert config.max_portfolio_risk_pct == 30.0
        assert config.default_stop_loss_pct == 2.0
        assert config.default_take_profit_pct == 5.0
        assert config.max_drawdown_pct == 15.0

    def test_percentage_validation(self) -> None:
        """Test percentage values are validated."""
        # Valid percentages
        config = RiskConfig(
            max_position_size_pct=5.0,
            max_portfolio_risk_pct=20.0,
            default_stop_loss_pct=1.5,
            default_take_profit_pct=3.0,
            max_drawdown_pct=10.0,
        )
        assert config.max_position_size_pct == 5.0

        # Invalid percentage (too low)
        with pytest.raises(ValidationError):
            RiskConfig(max_position_size_pct=0.0)

        # Invalid percentage (too high)
        with pytest.raises(ValidationError):
            RiskConfig(max_position_size_pct=150.0)


class TestTradingConfig:
    """Test TradingConfig schema."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        config = TradingConfig()
        assert config.dry_run is True
        assert config.max_concurrent_trades == 5
        assert config.default_order_type == "limit"
        assert isinstance(config.risk, RiskConfig)

    def test_order_type_validation(self) -> None:
        """Test order type validation."""
        # Valid order types
        TradingConfig(default_order_type="market")
        TradingConfig(default_order_type="limit")

        # Invalid order type
        with pytest.raises(ValidationError):
            TradingConfig(default_order_type="stop_loss")

    def test_max_concurrent_trades_validation(self) -> None:
        """Test max concurrent trades validation."""
        # Valid value
        config = TradingConfig(max_concurrent_trades=10)
        assert config.max_concurrent_trades == 10

        # Invalid value (too low)
        with pytest.raises(ValidationError):
            TradingConfig(max_concurrent_trades=0)

        # Invalid value (too high)
        with pytest.raises(ValidationError):
            TradingConfig(max_concurrent_trades=200)


class TestExchangeConfig:
    """Test ExchangeConfig schema."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        config = ExchangeConfig()
        assert config.enabled is False
        assert config.sandbox is True
        assert config.api_key is None
        assert config.api_secret is None

    def test_with_credentials(self) -> None:
        """Test config with credentials."""
        config = ExchangeConfig(
            enabled=True,
            sandbox=False,
            api_key="test_key",
            api_secret="test_secret",
        )
        assert config.enabled is True
        assert config.sandbox is False
        assert config.api_key == "test_key"
        assert config.api_secret == "test_secret"


class TestApiConfig:
    """Test ApiConfig schema."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        config = ApiConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.workers == 4
        assert config.reload is False

    def test_port_validation(self) -> None:
        """Test port validation."""
        # Valid port
        config = ApiConfig(port=3000)
        assert config.port == 3000

        # Invalid port
        with pytest.raises(ValidationError):
            ApiConfig(port=70000)

    def test_workers_validation(self) -> None:
        """Test workers validation."""
        # Valid workers
        config = ApiConfig(workers=8)
        assert config.workers == 8

        # Invalid workers (too low)
        with pytest.raises(ValidationError):
            ApiConfig(workers=0)

        # Invalid workers (too high)
        with pytest.raises(ValidationError):
            ApiConfig(workers=50)


class TestLoggingConfig:
    """Test LoggingConfig schema."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        config = LoggingConfig()
        assert config.file_path == "./data/logs/crypto-bot.log"
        assert config.max_size == "10MB"
        assert config.backup_count == 5
        assert config.format == "json"
        assert "console" in config.handlers
        assert "file" in config.handlers

    def test_format_validation(self) -> None:
        """Test format validation."""
        # Valid formats
        LoggingConfig(format="json")
        LoggingConfig(format="pretty")

        # Invalid format
        with pytest.raises(ValidationError):
            LoggingConfig(format="xml")

    def test_handlers_validation(self) -> None:
        """Test handlers validation."""
        # Valid handlers
        config = LoggingConfig(handlers=["console"])
        assert config.handlers == ["console"]

        # Invalid handler
        with pytest.raises(ValidationError):
            LoggingConfig(handlers=["syslog"])


class TestConfig:
    """Test complete Config schema."""

    def test_minimal_valid_config(self) -> None:
        """Test minimal valid configuration."""
        config = Config(security={"encryption_key": "test_key_123"})
        assert config.app.name == "Crypto Trading Bot"
        assert config.database.host == "localhost"
        assert config.trading.dry_run is True
        assert config.security.encryption_key == "test_key_123"

    def test_missing_encryption_key(self) -> None:
        """Test that missing encryption key raises error."""
        with pytest.raises(ValidationError) as exc_info:
            Config()

        # Check that security field is required
        assert "security" in str(exc_info.value).lower()

    def test_full_config(self) -> None:
        """Test full configuration with all sections."""
        config_data = {
            "app": {"name": "Test Bot", "log_level": "DEBUG"},
            "database": {"host": "db.example.com", "port": 5432},
            "redis": {"host": "redis.example.com"},
            "trading": {
                "dry_run": False,
                "max_concurrent_trades": 10,
                "risk": {"max_position_size_pct": 5.0},
            },
            "exchanges": {
                "binance": {
                    "enabled": True,
                    "api_key": "test_key",
                    "api_secret": "test_secret",
                }
            },
            "api": {"port": 9000},
            "security": {"encryption_key": "test_key_123"},
        }

        config = Config(**config_data)
        assert config.app.name == "Test Bot"
        assert config.app.log_level == "DEBUG"
        assert config.database.host == "db.example.com"
        assert config.trading.dry_run is False
        assert config.trading.max_concurrent_trades == 10
        assert config.exchanges.binance.enabled is True
        assert config.api.port == 9000

