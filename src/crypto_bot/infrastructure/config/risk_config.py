"""
Risk Management Configuration Models.

This module defines Pydantic models for all risk management parameters,
ensuring type safety, validation, and easy loading from YAML/JSON configuration files.
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class StopLossConfig(BaseModel):
    """
    Stop loss configuration.

    Defines parameters for automatic position closure when losses exceed a threshold.
    """

    enabled: bool = Field(True, description="Enable stop loss protection")
    percentage: Decimal = Field(
        ...,
        gt=0,
        lt=100,
        description="Stop loss threshold as percentage of entry price (e.g., 2.0 = 2%)",
    )
    cooldown_seconds: int = Field(
        60,
        ge=0,
        description="Minimum time between stop loss actions for the same asset",
    )
    trailing: bool = Field(
        False, description="Enable trailing stop loss (follows price upward)"
    )

    model_config = {"frozen": False}


class TakeProfitConfig(BaseModel):
    """
    Take profit configuration.

    Defines parameters for automatic position closure when profits reach a target.
    """

    enabled: bool = Field(True, description="Enable take profit protection")
    percentage: Decimal = Field(
        ...,
        gt=0,
        lt=1000,
        description="Take profit threshold as percentage of entry price (e.g., 5.0 = 5%)",
    )
    cooldown_seconds: int = Field(
        60,
        ge=0,
        description="Minimum time between take profit actions for the same asset",
    )
    partial_close: bool = Field(
        False, description="Close only part of position at take profit levels"
    )
    partial_close_percentage: Optional[Decimal] = Field(
        None,
        gt=0,
        le=100,
        description="Percentage of position to close if partial_close enabled",
    )

    @model_validator(mode="after")
    def validate_partial_close(self) -> "TakeProfitConfig":
        """Validate that partial_close_percentage is provided if partial_close is enabled."""
        if self.partial_close and not self.partial_close_percentage:
            raise ValueError(
                "partial_close_percentage must be provided when partial_close is enabled"
            )
        return self

    model_config = {"frozen": False}


class ExposureLimitConfig(BaseModel):
    """
    Exposure limits configuration.

    Defines maximum exposure per asset, per exchange, and total portfolio exposure.
    """

    max_per_asset: Decimal = Field(
        ...,
        gt=0,
        description="Maximum exposure per asset in base currency (e.g., USDT)",
    )
    max_per_exchange: Decimal = Field(
        ...,
        gt=0,
        description="Maximum total exposure per exchange in base currency",
    )
    max_total: Decimal = Field(
        ..., gt=0, description="Maximum total exposure across all assets and exchanges"
    )
    base_currency: str = Field(
        "USDT", description="Base currency for exposure calculations"
    )

    @model_validator(mode="after")
    def validate_exposure_hierarchy(self) -> "ExposureLimitConfig":
        """Validate that exposure limits follow logical hierarchy."""
        if self.max_per_asset > self.max_per_exchange:
            raise ValueError("max_per_asset cannot exceed max_per_exchange")
        if self.max_per_exchange > self.max_total:
            raise ValueError("max_per_exchange cannot exceed max_total")
        return self

    model_config = {"frozen": False}


class TrailingStopConfig(BaseModel):
    """
    Trailing stop configuration.

    Defines parameters for trailing stop loss that follows price movement.
    """

    enabled: bool = Field(True, description="Enable trailing stop")
    trailing_percentage: Decimal = Field(
        ...,
        gt=0,
        lt=100,
        description="Trailing stop distance as percentage (e.g., 3.0 = 3%)",
    )
    activation_percentage: Decimal = Field(
        ...,
        gt=0,
        lt=1000,
        description="Profit percentage required to activate trailing stop",
    )
    update_interval_seconds: int = Field(
        5, ge=1, description="Interval to update trailing stop level"
    )

    @model_validator(mode="after")
    def validate_activation(self) -> "TrailingStopConfig":
        """Validate that activation percentage is greater than trailing percentage."""
        if self.trailing_percentage >= self.activation_percentage:
            raise ValueError(
                "activation_percentage must be greater than trailing_percentage"
            )
        return self

    model_config = {"frozen": False}


class MaxConcurrentTradesConfig(BaseModel):
    """
    Maximum concurrent trades configuration.

    Defines limits on the number of simultaneous open positions.
    """

    max_trades: int = Field(
        ..., gt=0, description="Maximum number of concurrent trades"
    )
    max_per_asset: int = Field(
        1,
        gt=0,
        description="Maximum concurrent trades per asset (default: 1 to avoid multiple positions)",
    )
    max_per_exchange: int = Field(
        ..., gt=0, description="Maximum concurrent trades per exchange"
    )

    @model_validator(mode="after")
    def validate_trade_limits(self) -> "MaxConcurrentTradesConfig":
        """Validate that trade limits follow logical hierarchy."""
        if self.max_per_exchange > self.max_trades:
            raise ValueError("max_per_exchange cannot exceed max_trades")
        return self

    model_config = {"frozen": False}


class DrawdownControlConfig(BaseModel):
    """
    Drawdown control configuration.

    Defines maximum acceptable drawdown and actions to take when exceeded.
    """

    max_drawdown_percentage: Decimal = Field(
        ...,
        gt=0,
        lt=100,
        description="Maximum acceptable drawdown as percentage of peak equity",
    )
    enable_emergency_exit: bool = Field(
        True, description="Enable emergency exit of all positions when max exceeded"
    )
    emergency_exit_percentage: Decimal = Field(
        ...,
        gt=0,
        lt=100,
        description="Drawdown percentage that triggers emergency exit",
    )
    pause_trading_on_breach: bool = Field(
        True, description="Pause new trades when drawdown limit breached"
    )
    calculation_period_days: int = Field(
        30, gt=0, description="Period in days to calculate drawdown"
    )

    @model_validator(mode="after")
    def validate_emergency_exit(self) -> "DrawdownControlConfig":
        """Validate that emergency exit threshold is higher than max drawdown."""
        if self.enable_emergency_exit:
            if self.emergency_exit_percentage <= self.max_drawdown_percentage:
                raise ValueError(
                    "emergency_exit_percentage must be greater than max_drawdown_percentage"
                )
        return self

    model_config = {"frozen": False}


class RiskConfig(BaseModel):
    """
    Top-level risk management configuration.

    Aggregates all risk management parameters and provides validation.
    """

    stop_loss: StopLossConfig
    take_profit: TakeProfitConfig
    exposure_limit: ExposureLimitConfig
    trailing_stop: TrailingStopConfig
    max_concurrent_trades: MaxConcurrentTradesConfig
    drawdown_control: DrawdownControlConfig

    risk_check_interval: float = Field(
        1.0, gt=0, description="Interval in seconds for periodic risk checks"
    )
    emergency_only_mode: bool = Field(
        False,
        description="If true, only emergency risk checks run (for degraded system)",
    )

    @model_validator(mode="after")
    def validate_risk_consistency(self) -> "RiskConfig":
        """
        Validate consistency across risk parameters.

        Ensures that stop loss and take profit are logically consistent.
        """
        if self.stop_loss.enabled and self.take_profit.enabled:
            if self.stop_loss.percentage >= self.take_profit.percentage:
                raise ValueError(
                    "stop_loss percentage should typically be lower than take_profit percentage "
                    "for balanced risk/reward ratio"
                )
        return self

    model_config = {"frozen": False}
