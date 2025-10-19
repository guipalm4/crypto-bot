"""
Crypto Trading Bot - Configuration Settings

This module contains the configuration settings for the Crypto Trading Bot.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "Crypto Trading Bot"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # Database
    database_url: str = Field(
        default="postgresql://crypto_bot_user:crypto_bot_password@localhost:5432/crypto_bot",
        alias="DATABASE_URL"
    )
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="crypto_bot", alias="POSTGRES_DB")
    postgres_user: str = Field(default="crypto_bot_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="crypto_bot_password", alias="POSTGRES_PASSWORD")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    
    # Exchange APIs
    binance_api_key: Optional[str] = Field(default=None, alias="BINANCE_API_KEY")
    binance_api_secret: Optional[str] = Field(default=None, alias="BINANCE_API_SECRET")
    binance_sandbox: bool = Field(default=False, alias="BINANCE_SANDBOX")
    
    coinbase_api_key: Optional[str] = Field(default=None, alias="COINBASE_API_KEY")
    coinbase_api_secret: Optional[str] = Field(default=None, alias="COINBASE_API_SECRET")
    coinbase_passphrase: Optional[str] = Field(default=None, alias="COINBASE_PASSPHRASE")
    coinbase_sandbox: bool = Field(default=False, alias="COINBASE_SANDBOX")
    
    # Security
    encryption_key: Optional[str] = Field(default=None, alias="ENCRYPTION_KEY")
    jwt_secret: Optional[str] = Field(default=None, alias="JWT_SECRET")
    
    # Trading Configuration
    max_position_size_pct: float = Field(default=10.0, alias="MAX_POSITION_SIZE_PCT")
    max_portfolio_risk_pct: float = Field(default=30.0, alias="MAX_PORTFOLIO_RISK_PCT")
    default_stop_loss_pct: float = Field(default=2.0, alias="DEFAULT_STOP_LOSS_PCT")
    default_take_profit_pct: float = Field(default=5.0, alias="DEFAULT_TAKE_PROFIT_PCT")
    max_drawdown_pct: float = Field(default=15.0, alias="MAX_DRAWDOWN_PCT")
    
    # Trading Settings
    dry_run: bool = Field(default=True, alias="DRY_RUN")
    max_concurrent_trades: int = Field(default=5, alias="MAX_CONCURRENT_TRADES")
    default_order_type: str = Field(default="limit", alias="DEFAULT_ORDER_TYPE")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_workers: int = Field(default=4, alias="API_WORKERS")
    api_reload: bool = Field(default=False, alias="API_RELOAD")
    
    # Logging
    log_file_path: str = Field(default="./data/logs/crypto-bot.log", alias="LOG_FILE_PATH")
    log_max_size: str = Field(default="10MB", alias="LOG_MAX_SIZE")
    log_backup_count: int = Field(default=5, alias="LOG_BACKUP_COUNT")
    
    # Feature Flags
    enable_telegram_notifications: bool = Field(default=False, alias="ENABLE_TELEGRAM_NOTIFICATIONS")
    enable_discord_notifications: bool = Field(default=False, alias="ENABLE_DISCORD_NOTIFICATIONS")
    enable_email_notifications: bool = Field(default=False, alias="ENABLE_EMAIL_NOTIFICATIONS")
    enable_monitoring: bool = Field(default=True, alias="ENABLE_MONITORING")
    enable_logging: bool = Field(default=True, alias="ENABLE_LOGGING")
    enable_metrics: bool = Field(default=True, alias="ENABLE_METRICS")


# Global settings instance
settings = Settings()
