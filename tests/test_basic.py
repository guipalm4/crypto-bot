"""
Crypto Trading Bot - Basic Tests

This module contains basic tests for the Crypto Trading Bot.
"""

# Add src to path for imports
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from crypto_bot.config.settings import Settings


class TestSettings:
    """Test configuration settings."""

    def test_settings_creation(self):
        """Test that settings can be created."""
        settings = Settings()
        assert settings.app_name == "Crypto Trading Bot"
        assert settings.app_version == "0.1.0"
        assert settings.environment == "development"
        assert settings.debug is False
        assert settings.log_level == "INFO"

    def test_database_url_default(self):
        """Test default database URL."""
        settings = Settings()
        assert "postgresql://" in settings.database_url
        assert "crypto_bot" in settings.database_url

    def test_redis_url_default(self):
        """Test default Redis URL."""
        settings = Settings()
        assert settings.redis_url == "redis://localhost:6379/0"

    def test_trading_config_defaults(self):
        """Test default trading configuration."""
        settings = Settings()
        assert settings.max_position_size_pct == 10.0
        assert settings.max_portfolio_risk_pct == 30.0
        assert settings.default_stop_loss_pct == 2.0
        assert settings.default_take_profit_pct == 5.0
        assert settings.max_drawdown_pct == 15.0
        assert settings.dry_run is True
        assert settings.max_concurrent_trades == 5
        assert settings.default_order_type == "limit"


class TestProjectStructure:
    """Test project structure."""

    def test_src_directory_exists(self):
        """Test that src directory exists."""
        src_dir = Path(__file__).parent.parent / "src"
        assert src_dir.exists()
        assert src_dir.is_dir()

    def test_crypto_bot_package_exists(self):
        """Test that crypto_bot package exists."""
        crypto_bot_dir = Path(__file__).parent.parent / "src" / "crypto_bot"
        assert crypto_bot_dir.exists()
        assert crypto_bot_dir.is_dir()

    def test_domain_structure_exists(self):
        """Test that domain structure exists."""
        domain_dir = Path(__file__).parent.parent / "src" / "crypto_bot" / "domain"
        assert domain_dir.exists()
        assert domain_dir.is_dir()

        # Check subdirectories
        assert (domain_dir / "entities").exists()
        assert (domain_dir / "value_objects").exists()
        assert (domain_dir / "repositories").exists()
        assert (domain_dir / "services").exists()

    def test_application_structure_exists(self):
        """Test that application structure exists."""
        app_dir = Path(__file__).parent.parent / "src" / "crypto_bot" / "application"
        assert app_dir.exists()
        assert app_dir.is_dir()

        # Check subdirectories
        assert (app_dir / "use_cases").exists()
        assert (app_dir / "dtos").exists()
        assert (app_dir / "interfaces").exists()

    def test_infrastructure_structure_exists(self):
        """Test that infrastructure structure exists."""
        infra_dir = (
            Path(__file__).parent.parent / "src" / "crypto_bot" / "infrastructure"
        )
        assert infra_dir.exists()
        assert infra_dir.is_dir()

        # Check subdirectories
        assert (infra_dir / "database").exists()
        assert (infra_dir / "external_apis").exists()
        assert (infra_dir / "config").exists()

    def test_interfaces_structure_exists(self):
        """Test that interfaces structure exists."""
        interfaces_dir = (
            Path(__file__).parent.parent / "src" / "crypto_bot" / "interfaces"
        )
        assert interfaces_dir.exists()
        assert interfaces_dir.is_dir()

        # Check subdirectories
        assert (interfaces_dir / "api").exists()
        assert (interfaces_dir / "cli").exists()
        assert (interfaces_dir / "web").exists()


class TestConfigurationFiles:
    """Test configuration files."""

    def test_pyproject_toml_exists(self):
        """Test that pyproject.toml exists."""
        pyproject_file = Path(__file__).parent.parent / "pyproject.toml"
        assert pyproject_file.exists()
        assert pyproject_file.is_file()

    def test_requirements_txt_exists(self):
        """Test that requirements.txt exists."""
        requirements_file = Path(__file__).parent.parent / "requirements.txt"
        assert requirements_file.exists()
        assert requirements_file.is_file()

    def test_requirements_dev_txt_exists(self):
        """Test that requirements-dev.txt exists."""
        requirements_dev_file = Path(__file__).parent.parent / "requirements-dev.txt"
        assert requirements_dev_file.exists()
        assert requirements_dev_file.is_file()

    def test_docker_compose_yml_exists(self):
        """Test that docker-compose.yml exists."""
        docker_compose_file = Path(__file__).parent.parent / "docker-compose.yml"
        assert docker_compose_file.exists()
        assert docker_compose_file.is_file()

    def test_env_example_exists(self):
        """Test that env.example exists."""
        env_example_file = Path(__file__).parent.parent / "env.example"
        assert env_example_file.exists()
        assert env_example_file.is_file()


if __name__ == "__main__":
    pytest.main([__file__])
