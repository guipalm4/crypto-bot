"""
Crypto Trading Bot - Configuration Settings

This module contains the configuration settings for the Crypto Trading Bot.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Crypto Trading Bot"
    app_version: str = "0.1.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Database
    database_url: str = Field(
        default="postgresql://crypto_bot_user:crypto_bot_password@localhost:5432/crypto_bot",
        env="DATABASE_URL"
    )
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="crypto_bot", env="POSTGRES_DB")
    postgres_user: str = Field(default="crypto_bot_user", env="POSTGRES_USER")
    postgres_password: str = Field(default="crypto_bot_password", env="POSTGRES_PASSWORD")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    # Exchange APIs
    binance_api_key: Optional[str] = Field(default=None, env="BINANCE_API_KEY")
    binance_api_secret: Optional[str] = Field(default=None, env="BINANCE_API_SECRET")
    binance_sandbox: bool = Field(default=False, env="BINANCE_SANDBOX")
    
    coinbase_api_key: Optional[str] = Field(default=None, env="COINBASE_API_KEY")
    coinbase_api_secret: Optional[str] = Field(default=None, env="COINBASE_API_SECRET")
    coinbase_passphrase: Optional[str] = Field(default=None, env="COINBASE_PASSPHRASE")
    coinbase_sandbox: bool = Field(default=False, env="COINBASE_SANDBOX")
    
    # Security
    encryption_key: Optional[str] = Field(default=None, env="ENCRYPTION_KEY")
    jwt_secret: Optional[str] = Field(default=None, env="JWT_SECRET")
    
    # Trading Configuration
    max_position_size_pct: float = Field(default=10.0, env="MAX_POSITION_SIZE_PCT")
    max_portfolio_risk_pct: float = Field(default=30.0, env="MAX_PORTFOLIO_RISK_PCT")
    default_stop_loss_pct: float = Field(default=2.0, env="DEFAULT_STOP_LOSS_PCT")
    default_take_profit_pct: float = Field(default=5.0, env="DEFAULT_TAKE_PROFIT_PCT")
    max_drawdown_pct: float = Field(default=15.0, env="MAX_DRAWDOWN_PCT")
    
    # Trading Settings
    dry_run: bool = Field(default=True, env="DRY_RUN")
    max_concurrent_trades: int = Field(default=5, env="MAX_CONCURRENT_TRADES")
    default_order_type: str = Field(default="limit", env="DEFAULT_ORDER_TYPE")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    api_reload: bool = Field(default=False, env="API_RELOAD")
    
    # Logging
    log_file_path: str = Field(default="./data/logs/crypto-bot.log", env="LOG_FILE_PATH")
    log_max_size: str = Field(default="10MB", env="LOG_MAX_SIZE")
    log_backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    # Feature Flags
    enable_telegram_notifications: bool = Field(default=False, env="ENABLE_TELEGRAM_NOTIFICATIONS")
    enable_discord_notifications: bool = Field(default=False, env="ENABLE_DISCORD_NOTIFICATIONS")
    enable_email_notifications: bool = Field(default=False, env="ENABLE_EMAIL_NOTIFICATIONS")
    enable_monitoring: bool = Field(default=True, env="ENABLE_MONITORING")
    enable_logging: bool = Field(default=True, env="ENABLE_LOGGING")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
