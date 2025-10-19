# Configuration System

This directory contains the configuration files for the Crypto Trading Bot. The configuration system uses YAML files for non-sensitive settings and environment variables for sensitive data like API keys and passwords.

## Directory Structure

```
config/
├── environments/
│   ├── base.yaml          # Base configuration (all environments)
│   ├── development.yaml   # Development overrides
│   ├── staging.yaml       # Staging overrides
│   └── production.yaml    # Production overrides
├── .env.example           # Example environment variables
└── README.md              # This file
```

## How It Works

1. **Base Configuration**: `base.yaml` contains default values for all settings
2. **Environment Overrides**: Environment-specific files override base values
3. **Environment Variables**: Sensitive data overlays YAML configuration
4. **Validation**: Pydantic schemas validate all settings

## Configuration Loading

The system loads configuration in this order:
1. Load `base.yaml`
2. Merge with `{environment}.yaml` (e.g., `development.yaml`)
3. Overlay environment variables from `.env`
4. Validate with Pydantic schemas

## Usage

### Basic Usage

```python
from crypto_bot.config import load_config

# Load config for current environment (from ENVIRONMENT env var)
config = load_config()

# Or specify environment explicitly
config = load_config(env="production")

# Access configuration
print(config.database.host)
print(config.trading.max_concurrent_trades)
print(config.exchanges.binance.api_key)
```

### Setting Up Environment

1. Copy `.env.example` to `.env` in project root:
   ```bash
   cp config/.env.example .env
   ```

2. Fill in your sensitive values in `.env`:
   ```bash
   # Required
   ENCRYPTION_KEY=your_32_char_encryption_key
   
   # Database
   DATABASE_USER=crypto_bot_user
   DATABASE_PASSWORD=secure_password
   
   # Exchange API keys
   BINANCE_API_KEY=your_api_key
   BINANCE_API_SECRET=your_api_secret
   ```

3. Set your environment:
   ```bash
   export ENVIRONMENT=development  # or staging, production
   ```

## Environment Profiles

### Development
- Debug logging enabled
- SQL echo enabled
- Dry run mode enforced
- Sandbox APIs
- Auto-reload enabled
- Console logging

### Staging
- Info logging
- Dry run mode enforced
- Sandbox APIs
- File + console logging
- Testing production-like setup

### Production
- Warning-level logging
- Real trading enabled (dry_run=false)
- Production APIs
- File logging only
- Optimized settings

## Configuration Sections

### App
- `name`: Application name
- `version`: Application version
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Database
- `host`: Database host
- `port`: Database port (1-65535)
- `name`: Database name
- `user`: Database user (from env)
- `password`: Database password (from env)
- `pool_size`: Connection pool size (1-100)
- `max_overflow`: Max overflow connections (0-100)
- `echo`: Echo SQL queries (development only)

### Redis
- `host`: Redis host
- `port`: Redis port (1-65535)
- `db`: Redis database number (0-15)
- `password`: Redis password (from env, optional)

### Trading
- `dry_run`: Enable dry run mode (no real trades)
- `max_concurrent_trades`: Maximum concurrent trades (1-100)
- `default_order_type`: "market" or "limit"
- `risk`: Risk management settings
  - `max_position_size_pct`: Max position size (0.1-100%)
  - `max_portfolio_risk_pct`: Max portfolio risk (1-100%)
  - `default_stop_loss_pct`: Default stop loss (0.1-50%)
  - `default_take_profit_pct`: Default take profit (0.1-100%)
  - `max_drawdown_pct`: Max drawdown (1-100%)

### Exchanges
- `binance`: Binance configuration
  - `enabled`: Enable exchange
  - `sandbox`: Use testnet/sandbox
  - `api_key`: API key (from env)
  - `api_secret`: API secret (from env)
- `coinbase`: Coinbase configuration
  - `enabled`: Enable exchange
  - `sandbox`: Use sandbox
  - `api_key`: API key (from env)
  - `api_secret`: API secret (from env)
  - `passphrase`: Passphrase (from env)

### API
- `host`: API host (default: 0.0.0.0)
- `port`: API port (1-65535)
- `workers`: Number of workers (1-32)
- `reload`: Auto-reload on code changes (development only)

### Security
- `encryption_key`: AES encryption key (REQUIRED, from env)
- `jwt_secret`: JWT signing secret (from env)

## Validation

All configuration is validated using Pydantic schemas with:
- Type checking
- Range validation (e.g., ports 1-65535)
- Required fields
- Default values
- Custom validators

Invalid configuration will raise `ValueError` with detailed error messages.

## Environment Variables

Required:
- `ENCRYPTION_KEY`: Used for encrypting sensitive data in database

Database:
- `DATABASE_USER`: Database username
- `DATABASE_PASSWORD`: Database password

Exchange APIs:
- `BINANCE_API_KEY`
- `BINANCE_API_SECRET`
- `COINBASE_API_KEY`
- `COINBASE_API_SECRET`
- `COINBASE_PASSPHRASE`

Optional:
- `REDIS_PASSWORD`
- `JWT_SECRET`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `DISCORD_WEBHOOK_URL`
- `EMAIL_SMTP_PASSWORD`

## Best Practices

1. **Never hardcode sensitive data** - Always use environment variables
2. **Use appropriate environment** - development for local, production for live
3. **Validate early** - Configuration loads and validates at startup
4. **Keep base.yaml DRY** - Put common settings in base, overrides in env files
5. **Document changes** - Update this README when adding new config options
6. **Test configurations** - Run tests after modifying YAML files

## Example: Adding New Configuration

1. Update schema in `src/crypto_bot/config/schemas.py`:
   ```python
   class NewFeatureConfig(BaseModel):
       enabled: bool = False
       option: str = "default"
   ```

2. Add to main Config schema:
   ```python
   class Config(BaseModel):
       # ... existing fields ...
       new_feature: NewFeatureConfig = Field(default_factory=NewFeatureConfig)
   ```

3. Add to `base.yaml`:
   ```yaml
   new_feature:
     enabled: false
     option: "default"
   ```

4. Override in environment files as needed:
   ```yaml
   # production.yaml
   new_feature:
     enabled: true
     option: "production_value"
   ```

5. Add tests in `tests/unit/config/test_schemas.py`

## Troubleshooting

### "ENCRYPTION_KEY environment variable is required"
Set `ENCRYPTION_KEY` in your `.env` file or as environment variable.

### "Configuration validation failed"
Check the error message for specific validation errors (e.g., invalid port, missing field).

### "Invalid environment"
Environment must be one of: development, staging, production.

### "Configuration file not found"
Ensure `config/environments/base.yaml` exists and is readable.

