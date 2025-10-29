"""
Tests for YAML-based logging configuration.
"""

import tempfile
from pathlib import Path

import pytest

from crypto_bot.config.loader import ConfigLoader
from crypto_bot.config.schemas import LoggingConfig
from crypto_bot.utils.structured_logger import initialize_from_config


class TestYAMLLoggingConfig:
    """Test suite for YAML-based logging configuration."""

    def test_initialize_from_logging_config(self, tmp_path: Path) -> None:
        """Test that logging can be initialized from LoggingConfig."""
        log_file = tmp_path / "yaml_test.log"

        config = LoggingConfig(
            level="DEBUG",
            file_path=str(log_file),
            max_size="5MB",
            backup_count=3,
            format="json",
            handlers=["file"],
        )

        initialize_from_config(config)

        # Verify logger works
        from crypto_bot.utils.structured_logger import get_logger

        logger = get_logger("test.yaml")
        logger.info("yaml_config_test", test="value")

        assert logger is not None

    def test_logging_config_from_yaml_file(self, tmp_path: Path) -> None:
        """Test loading logging config from YAML and initializing."""
        # Create a minimal LoggingConfig directly to test YAML parsing
        # In real usage, this would come from Config.logging
        import yaml

        yaml_data = """
logging:
  level: "WARNING"
  file_path: "./logs/test.log"
  max_size: "20MB"
  backup_count: 10
  format: "pretty"
  handlers:
    - console
    - file
"""

        data = yaml.safe_load(yaml_data)
        config = LoggingConfig(**data["logging"])

        # Initialize logging from config
        initialize_from_config(config)

        # Verify it was configured
        from crypto_bot.utils.structured_logger import get_logger

        logger = get_logger("test.yaml.config")
        assert logger is not None
        assert config.level == "WARNING"
        assert config.format == "pretty"

    def test_handlers_console_only(self) -> None:
        """Test configuration with console handler only."""
        config = LoggingConfig(
            level="INFO",
            format="pretty",
            handlers=["console"],
        )

        initialize_from_config(config)
        assert config.handlers == ["console"]

    def test_handlers_file_only(self, tmp_path: Path) -> None:
        """Test configuration with file handler only."""
        log_file = tmp_path / "file_only.log"

        config = LoggingConfig(
            level="INFO",
            format="json",
            file_path=str(log_file),
            handlers=["file"],
        )

        initialize_from_config(config)
        assert config.handlers == ["file"]

    def test_handlers_both(self, tmp_path: Path) -> None:
        """Test configuration with both console and file handlers."""
        log_file = tmp_path / "both_handlers.log"

        config = LoggingConfig(
            level="INFO",
            format="json",
            file_path=str(log_file),
            handlers=["console", "file"],
        )

        initialize_from_config(config)
        assert "console" in config.handlers
        assert "file" in config.handlers

    def test_all_log_levels(self) -> None:
        """Test that all log levels can be configured."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = LoggingConfig(level=level, handlers=["console"])
            initialize_from_config(config)
            assert config.level == level

    def test_invalid_config_raises_error(self) -> None:
        """Test that invalid config object raises TypeError."""
        with pytest.raises(TypeError, match="must be a LoggingConfig instance"):
            initialize_from_config("not_a_config")  # type: ignore[arg-type]
