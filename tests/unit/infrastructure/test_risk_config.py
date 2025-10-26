"""
Unit tests for risk configuration models.

Tests validation rules, default values, and configuration logic.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from crypto_bot.infrastructure.config.risk_config import (
    DrawdownControlConfig,
    ExposureLimitConfig,
    MaxConcurrentTradesConfig,
    RiskConfig,
    StopLossConfig,
    TakeProfitConfig,
    TrailingStopConfig,
)


class TestStopLossConfig:
    """Tests for StopLossConfig model."""

    def test_valid_config(self) -> None:
        """Test valid stop loss configuration."""
        config = StopLossConfig(percentage=Decimal("2.0"))
        assert config.enabled is True
        assert config.percentage == Decimal("2.0")
        assert config.cooldown_seconds == 60
        assert config.trailing is False

    def test_custom_values(self) -> None:
        """Test custom stop loss configuration."""
        config = StopLossConfig(
            enabled=False,
            percentage=Decimal("5.5"),
            cooldown_seconds=120,
            trailing=True,
        )
        assert config.enabled is False
        assert config.percentage == Decimal("5.5")
        assert config.cooldown_seconds == 120
        assert config.trailing is True

    def test_invalid_percentage_zero(self) -> None:
        """Test that percentage must be greater than zero."""
        with pytest.raises(ValidationError):
            StopLossConfig(percentage=Decimal("0.0"))

    def test_invalid_percentage_negative(self) -> None:
        """Test that percentage cannot be negative."""
        with pytest.raises(ValidationError):
            StopLossConfig(percentage=Decimal("-1.0"))

    def test_invalid_percentage_too_high(self) -> None:
        """Test that percentage must be less than 100."""
        with pytest.raises(ValidationError):
            StopLossConfig(percentage=Decimal("100.0"))


class TestTakeProfitConfig:
    """Tests for TakeProfitConfig model."""

    def test_valid_config(self) -> None:
        """Test valid take profit configuration."""
        config = TakeProfitConfig(percentage=Decimal("5.0"))
        assert config.enabled is True
        assert config.percentage == Decimal("5.0")
        assert config.cooldown_seconds == 60
        assert config.partial_close is False

    def test_partial_close_with_percentage(self) -> None:
        """Test partial close with valid percentage."""
        config = TakeProfitConfig(
            percentage=Decimal("5.0"),
            partial_close=True,
            partial_close_percentage=Decimal("50.0"),
        )
        assert config.partial_close is True
        assert config.partial_close_percentage == Decimal("50.0")

    def test_partial_close_without_percentage(self) -> None:
        """Test that partial_close requires partial_close_percentage."""
        with pytest.raises(
            ValueError, match="partial_close_percentage must be provided"
        ):
            TakeProfitConfig(percentage=Decimal("5.0"), partial_close=True)

    def test_invalid_percentage_zero(self) -> None:
        """Test that percentage must be greater than zero."""
        with pytest.raises(ValidationError):
            TakeProfitConfig(percentage=Decimal("0.0"))


class TestExposureLimitConfig:
    """Tests for ExposureLimitConfig model."""

    def test_valid_config(self) -> None:
        """Test valid exposure limit configuration."""
        config = ExposureLimitConfig(
            max_per_asset=Decimal("10000.0"),
            max_per_exchange=Decimal("30000.0"),
            max_total=Decimal("50000.0"),
        )
        assert config.max_per_asset == Decimal("10000.0")
        assert config.max_per_exchange == Decimal("30000.0")
        assert config.max_total == Decimal("50000.0")
        assert config.base_currency == "USDT"

    def test_invalid_hierarchy_asset_exceeds_exchange(self) -> None:
        """Test that max_per_asset cannot exceed max_per_exchange."""
        with pytest.raises(
            ValueError, match="max_per_asset cannot exceed max_per_exchange"
        ):
            ExposureLimitConfig(
                max_per_asset=Decimal("40000.0"),
                max_per_exchange=Decimal("30000.0"),
                max_total=Decimal("50000.0"),
            )

    def test_invalid_hierarchy_exchange_exceeds_total(self) -> None:
        """Test that max_per_exchange cannot exceed max_total."""
        with pytest.raises(
            ValueError, match="max_per_exchange cannot exceed max_total"
        ):
            ExposureLimitConfig(
                max_per_asset=Decimal("10000.0"),
                max_per_exchange=Decimal("60000.0"),
                max_total=Decimal("50000.0"),
            )

    def test_custom_base_currency(self) -> None:
        """Test custom base currency."""
        config = ExposureLimitConfig(
            max_per_asset=Decimal("100.0"),
            max_per_exchange=Decimal("300.0"),
            max_total=Decimal("500.0"),
            base_currency="BTC",
        )
        assert config.base_currency == "BTC"


class TestTrailingStopConfig:
    """Tests for TrailingStopConfig model."""

    def test_valid_config(self) -> None:
        """Test valid trailing stop configuration."""
        config = TrailingStopConfig(
            trailing_percentage=Decimal("3.0"), activation_percentage=Decimal("5.0")
        )
        assert config.enabled is True
        assert config.trailing_percentage == Decimal("3.0")
        assert config.activation_percentage == Decimal("5.0")
        assert config.update_interval_seconds == 5

    def test_invalid_activation_lower_than_trailing(self) -> None:
        """Test that activation must be greater than trailing percentage."""
        with pytest.raises(
            ValueError,
            match="activation_percentage must be greater than trailing_percentage",
        ):
            TrailingStopConfig(
                trailing_percentage=Decimal("5.0"), activation_percentage=Decimal("3.0")
            )

    def test_invalid_activation_equal_to_trailing(self) -> None:
        """Test that activation cannot equal trailing percentage."""
        with pytest.raises(ValidationError):
            TrailingStopConfig(
                trailing_percentage=Decimal("5.0"), activation_percentage=Decimal("5.0")
            )


class TestMaxConcurrentTradesConfig:
    """Tests for MaxConcurrentTradesConfig model."""

    def test_valid_config(self) -> None:
        """Test valid max concurrent trades configuration."""
        config = MaxConcurrentTradesConfig(max_trades=5, max_per_exchange=3)
        assert config.max_trades == 5
        assert config.max_per_asset == 1
        assert config.max_per_exchange == 3

    def test_invalid_exchange_exceeds_total(self) -> None:
        """Test that max_per_exchange cannot exceed max_trades."""
        with pytest.raises(
            ValueError, match="max_per_exchange cannot exceed max_trades"
        ):
            MaxConcurrentTradesConfig(max_trades=3, max_per_exchange=5)

    def test_custom_max_per_asset(self) -> None:
        """Test custom max_per_asset configuration."""
        config = MaxConcurrentTradesConfig(
            max_trades=10, max_per_asset=2, max_per_exchange=5
        )
        assert config.max_per_asset == 2


class TestDrawdownControlConfig:
    """Tests for DrawdownControlConfig model."""

    def test_valid_config(self) -> None:
        """Test valid drawdown control configuration."""
        config = DrawdownControlConfig(
            max_drawdown_percentage=Decimal("15.0"),
            emergency_exit_percentage=Decimal("20.0"),
        )
        assert config.max_drawdown_percentage == Decimal("15.0")
        assert config.enable_emergency_exit is True
        assert config.emergency_exit_percentage == Decimal("20.0")
        assert config.pause_trading_on_breach is True
        assert config.calculation_period_days == 30

    def test_invalid_emergency_exit_lower_than_max(self) -> None:
        """Test that emergency_exit must be greater than max_drawdown."""
        with pytest.raises(
            ValueError,
            match="emergency_exit_percentage must be greater than max_drawdown_percentage",
        ):
            DrawdownControlConfig(
                max_drawdown_percentage=Decimal("20.0"),
                emergency_exit_percentage=Decimal("15.0"),
            )

    def test_emergency_exit_disabled(self) -> None:
        """Test configuration with emergency exit disabled."""
        config = DrawdownControlConfig(
            max_drawdown_percentage=Decimal("15.0"),
            enable_emergency_exit=False,
            emergency_exit_percentage=Decimal("10.0"),  # Can be lower when disabled
        )
        assert config.enable_emergency_exit is False


class TestRiskConfig:
    """Tests for top-level RiskConfig model."""

    def test_valid_complete_config(self) -> None:
        """Test valid complete risk configuration."""
        config = RiskConfig(
            stop_loss=StopLossConfig(percentage=Decimal("2.0")),
            take_profit=TakeProfitConfig(percentage=Decimal("5.0")),
            exposure_limit=ExposureLimitConfig(
                max_per_asset=Decimal("10000.0"),
                max_per_exchange=Decimal("30000.0"),
                max_total=Decimal("50000.0"),
            ),
            trailing_stop=TrailingStopConfig(
                trailing_percentage=Decimal("3.0"), activation_percentage=Decimal("5.0")
            ),
            max_concurrent_trades=MaxConcurrentTradesConfig(
                max_trades=5, max_per_exchange=3
            ),
            drawdown_control=DrawdownControlConfig(
                max_drawdown_percentage=Decimal("15.0"),
                emergency_exit_percentage=Decimal("20.0"),
            ),
        )
        assert config.risk_check_interval == 1.0
        assert config.emergency_only_mode is False

    def test_custom_risk_check_interval(self) -> None:
        """Test custom risk check interval."""
        config = RiskConfig(
            stop_loss=StopLossConfig(percentage=Decimal("2.0")),
            take_profit=TakeProfitConfig(percentage=Decimal("5.0")),
            exposure_limit=ExposureLimitConfig(
                max_per_asset=Decimal("10000.0"),
                max_per_exchange=Decimal("30000.0"),
                max_total=Decimal("50000.0"),
            ),
            trailing_stop=TrailingStopConfig(
                trailing_percentage=Decimal("3.0"), activation_percentage=Decimal("5.0")
            ),
            max_concurrent_trades=MaxConcurrentTradesConfig(
                max_trades=5, max_per_exchange=3
            ),
            drawdown_control=DrawdownControlConfig(
                max_drawdown_percentage=Decimal("15.0"),
                emergency_exit_percentage=Decimal("20.0"),
            ),
            risk_check_interval=0.5,
            emergency_only_mode=True,
        )
        assert config.risk_check_interval == 0.5
        assert config.emergency_only_mode is True

    def test_invalid_stop_loss_greater_than_take_profit(self) -> None:
        """Test that stop loss should be lower than take profit."""
        with pytest.raises(
            ValueError,
            match="stop_loss percentage should typically be lower than take_profit percentage",
        ):
            RiskConfig(
                stop_loss=StopLossConfig(percentage=Decimal("10.0")),
                take_profit=TakeProfitConfig(percentage=Decimal("5.0")),
                exposure_limit=ExposureLimitConfig(
                    max_per_asset=Decimal("10000.0"),
                    max_per_exchange=Decimal("30000.0"),
                    max_total=Decimal("50000.0"),
                ),
                trailing_stop=TrailingStopConfig(
                    trailing_percentage=Decimal("3.0"),
                    activation_percentage=Decimal("5.0"),
                ),
                max_concurrent_trades=MaxConcurrentTradesConfig(
                    max_trades=5, max_per_exchange=3
                ),
                drawdown_control=DrawdownControlConfig(
                    max_drawdown_percentage=Decimal("15.0"),
                    emergency_exit_percentage=Decimal("20.0"),
                ),
            )
