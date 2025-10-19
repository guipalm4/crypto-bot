"""
Configuration schemas using Pydantic for validation.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class AppConfig(BaseModel):
    """Application configuration."""

    name: str = "Crypto Trading Bot"
    version: str = "0.1.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


class DatabaseConfig(BaseModel):
    """Database configuration."""

    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)
    name: str = "crypto_bot"
    user: Optional[str] = None  # From env
    password: Optional[str] = None  # From env
    pool_size: int = Field(default=5, ge=1, le=100)
    max_overflow: int = Field(default=10, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=1)
    pool_recycle: int = Field(default=1800, ge=60)
    echo: bool = False


class RedisConfig(BaseModel):
    """Redis configuration."""

    host: str = "localhost"
    port: int = Field(default=6379, ge=1, le=65535)
    db: int = Field(default=0, ge=0, le=15)
    password: Optional[str] = None  # From env
    socket_timeout: int = Field(default=5, ge=1)
    socket_connect_timeout: int = Field(default=5, ge=1)
    max_connections: int = Field(default=50, ge=1, le=1000)


class RiskConfig(BaseModel):
    """Risk management configuration."""

    max_position_size_pct: float = Field(default=10.0, ge=0.1, le=100.0)
    max_portfolio_risk_pct: float = Field(default=30.0, ge=1.0, le=100.0)
    default_stop_loss_pct: float = Field(default=2.0, ge=0.1, le=50.0)
    default_take_profit_pct: float = Field(default=5.0, ge=0.1, le=100.0)
    max_drawdown_pct: float = Field(default=15.0, ge=1.0, le=100.0)


class ExecutionConfig(BaseModel):
    """Order execution configuration."""

    order_timeout_seconds: int = Field(default=30, ge=1, le=300)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: int = Field(default=2, ge=1, le=60)


class TradingConfig(BaseModel):
    """Trading configuration."""

    dry_run: bool = True
    max_concurrent_trades: int = Field(default=5, ge=1, le=100)
    default_order_type: Literal["market", "limit"] = "limit"
    risk: RiskConfig = Field(default_factory=RiskConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)


class RateLimitsConfig(BaseModel):
    """Exchange rate limits configuration."""

    requests_per_second: int = Field(default=10, ge=1, le=100)
    orders_per_day: int = Field(default=200000, ge=1)


class ExchangeConfig(BaseModel):
    """Individual exchange configuration."""

    enabled: bool = False
    sandbox: bool = True
    api_key: Optional[str] = None  # From env
    api_secret: Optional[str] = None  # From env
    passphrase: Optional[str] = None  # From env (Coinbase)
    rate_limits: RateLimitsConfig = Field(default_factory=RateLimitsConfig)


class ExchangesConfig(BaseModel):
    """All exchanges configuration."""

    binance: ExchangeConfig = Field(default_factory=ExchangeConfig)
    coinbase: ExchangeConfig = Field(default_factory=ExchangeConfig)


class StrategiesConfig(BaseModel):
    """Strategies configuration."""

    enabled: List[str] = Field(default_factory=list)
    default_params: dict = Field(default_factory=dict)


class CorsConfig(BaseModel):
    """CORS configuration."""

    enabled: bool = True
    origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])


class ApiConfig(BaseModel):
    """API configuration."""

    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=4, ge=1, le=32)
    reload: bool = False
    cors: CorsConfig = Field(default_factory=CorsConfig)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    file_path: str = "./data/logs/crypto-bot.log"
    max_size: str = "10MB"
    backup_count: int = Field(default=5, ge=0, le=100)
    format: Literal["json", "pretty"] = "json"
    handlers: List[Literal["console", "file"]] = Field(
        default_factory=lambda: ["console", "file"]
    )


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""

    enabled: bool = True
    metrics_enabled: bool = True
    health_check_interval: int = Field(default=60, ge=10, le=3600)


class NotificationChannelConfig(BaseModel):
    """Individual notification channel configuration."""

    enabled: bool = False
    token: Optional[str] = None  # From env
    chat_id: Optional[str] = None  # From env
    webhook_url: Optional[str] = None  # From env


class NotificationsConfig(BaseModel):
    """Notifications configuration."""

    telegram: NotificationChannelConfig = Field(
        default_factory=NotificationChannelConfig
    )
    discord: NotificationChannelConfig = Field(
        default_factory=NotificationChannelConfig
    )
    email: NotificationChannelConfig = Field(
        default_factory=NotificationChannelConfig
    )


class SecurityConfig(BaseModel):
    """Security configuration."""

    encryption_key: str  # From env - REQUIRED
    jwt_secret: Optional[str] = None  # From env


class Config(BaseModel):
    """Complete application configuration."""

    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    strategies: StrategiesConfig = Field(default_factory=StrategiesConfig)
    exchanges: ExchangesConfig = Field(default_factory=ExchangesConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    notifications: NotificationsConfig = Field(
        default_factory=NotificationsConfig
    )
    security: SecurityConfig

