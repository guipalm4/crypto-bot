# 📋 Guia Completo de Configuração

Este documento fornece uma referência completa para todas as opções de configuração disponíveis no Crypto Trading Bot.

## 📁 Estrutura de Configuração

O sistema de configuração usa uma abordagem em camadas:

1. **Base Configuration** (`config/environments/base.yaml`) - Valores padrão para todos os ambientes
2. **Environment Overrides** (`config/environments/{environment}.yaml`) - Sobrescritas específicas por ambiente
3. **Environment Variables** (`.env`) - Dados sensíveis e sobrescritas em tempo de execução
4. **Pydantic Validation** - Validação e tipagem forte de todas as configurações

## 🔧 Como Funciona

### Ordem de Carregamento

1. Carrega `base.yaml` como base
2. Mescla com arquivo específico do ambiente (ex: `development.yaml`)
3. Aplica variáveis de ambiente do `.env`
4. Valida usando schemas Pydantic

### Variáveis de Ambiente

O sistema suporta variáveis de ambiente que sobrescrevem valores dos arquivos YAML:

```bash
# Exemplo de .env
# CRITICAL: Gere ENCRYPTION_KEY com: openssl rand -hex 32
ENCRYPTION_KEY=your_32_character_minimum_encryption_key_here
DATABASE_USER=crypto_bot_user
DATABASE_PASSWORD=secure_password
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_SANDBOX=false  # true para testnet, false para produção
ENVIRONMENT=development
```

## 📊 Seções de Configuração

### 🎯 Application Configuration (`app`)

Configurações gerais da aplicação.

```yaml
app:
  name: "Crypto Trading Bot"      # Nome da aplicação
  version: "0.1.0"                 # Versão
  log_level: "INFO"                # Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
```

**Variáveis de Ambiente:**
- `ENVIRONMENT`: Ambiente atual (development, staging, production)
- `DEBUG`: Modo debug (true/false)
- `LOG_LEVEL`: Nível de log

**Valores Válidos:**
- `log_level`: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

### 🗄️ Database Configuration (`database`)

Configurações do banco de dados PostgreSQL.

```yaml
database:
  host: "localhost"                # Host do banco
  port: 5432                       # Porta (1-65535)
  name: "crypto_bot"               # Nome do banco
  user: null                       # Usuário (de env: DATABASE_USER)
  password: null                   # Senha (de env: DATABASE_PASSWORD)
  pool_size: 5                     # Tamanho do pool (1-100)
  max_overflow: 10                 # Conexões overflow máximas (0-100)
  pool_timeout: 30                 # Timeout do pool em segundos (>= 1)
  pool_recycle: 1800               # Reciclagem do pool em segundos (>= 60)
  echo: false                      # Log de queries SQL (dev only)
```

**Variáveis de Ambiente:**
- `DATABASE_USER`: Usuário do banco
- `DATABASE_PASSWORD`: Senha do banco
- `DATABASE_URL`: URL completa do banco (override de host/port/name/user/password)

**Validações:**
- `port`: Deve estar entre 1 e 65535
- `pool_size`: Deve estar entre 1 e 100
- `max_overflow`: Deve estar entre 0 e 100

### 💾 Redis Configuration (`redis`)

Configurações do Redis para cache e filas.

```yaml
redis:
  host: "localhost"                # Host do Redis
  port: 6379                       # Porta (1-65535)
  db: 0                           # Número do banco (0-15)
  password: null                  # Senha (de env: REDIS_PASSWORD)
  socket_timeout: 5               # Timeout do socket em segundos (>= 1)
  socket_connect_timeout: 5       # Timeout de conexão em segundos (>= 1)
  max_connections: 50             # Máximo de conexões (1-1000)
```

**Variáveis de Ambiente:**
- `REDIS_PASSWORD`: Senha do Redis (opcional)
- `REDIS_URL`: URL completa do Redis (override)

### 💹 Trading Configuration (`trading`)

Configurações gerais de trading.

```yaml
trading:
  dry_run: true                    # Modo simulação (não executa trades reais)
  max_concurrent_trades: 5         # Máximo de trades simultâneos (1-100)
  default_order_type: "limit"      # Tipo padrão de ordem ("market" ou "limit")
  risk:                            # Configurações de risco (veja seção abaixo)
    # ... configurações de risco
  execution:                       # Configurações de execução
    order_timeout_seconds: 30      # Timeout de ordem em segundos (1-300)
    retry_attempts: 3              # Tentativas de retry (0-10)
    retry_delay_seconds: 2         # Delay entre retries em segundos (1-60)
```

**Variáveis de Ambiente:**
- `DRY_RUN`: Modo dry-run (true/false)
- `MAX_CONCURRENT_TRADES`: Máximo de trades simultâneos

**Valores Válidos:**
- `default_order_type`: `"market"` ou `"limit"`

### ⚠️ Risk Management Configuration (`trading.risk`)

Configurações detalhadas de gestão de risco.

#### Stop Loss

```yaml
stop_loss:
  enabled: true                     # Habilitar stop loss
  percentage: 2.0                 # Porcentagem de stop loss (ex: 2.0 = 2%)
  cooldown_seconds: 60             # Cooldown entre ações de stop loss
  trailing: false                  # Stop loss trailing (seguir preço para cima)
```

**Valores:**
- `percentage`: Deve estar entre 0 e 100 (excluído)
- `cooldown_seconds`: >= 0

#### Take Profit

```yaml
take_profit:
  enabled: true                     # Habilitar take profit
  percentage: 5.0                  # Porcentagem de take profit (ex: 5.0 = 5%)
  cooldown_seconds: 60             # Cooldown entre ações de take profit
  partial_close: false             # Fechar apenas parte da posição
  partial_close_percentage: null   # Porcentagem a fechar se partial_close = true
```

**Valores:**
- `percentage`: Deve estar entre 0 e 1000 (excluído)
- `partial_close_percentage`: Se `partial_close` = true, deve estar entre 0 e 100
- Se `partial_close` = true, `partial_close_percentage` é obrigatório

#### Exposure Limits

```yaml
exposure_limit:
  max_per_asset: 10000.0           # Máximo por ativo em moeda base
  max_per_exchange: 30000.0        # Máximo por exchange em moeda base
  max_total: 50000.0               # Máximo total em moeda base
  base_currency: "USDT"            # Moeda base para cálculos
```

**Validações:**
- `max_per_asset` <= `max_per_exchange` <= `max_total`
- Todos devem ser > 0

#### Trailing Stop

```yaml
trailing_stop:
  enabled: true                     # Habilitar trailing stop
  trailing_percentage: 3.0         # Porcentagem de trailing (ex: 3.0 = 3%)
  activation_percentage: 5.0       # Porcentagem de lucro para ativar trailing
  update_interval_seconds: 5       # Intervalo para atualizar trailing stop
```

**Validações:**
- `activation_percentage` > `trailing_percentage`
- `update_interval_seconds` >= 1

#### Max Concurrent Trades

```yaml
max_concurrent_trades:
  max_trades: 5                     # Máximo de trades simultâneos
  max_per_asset: 1                 # Máximo de trades por ativo (geralmente 1)
  max_per_exchange: 3              # Máximo de trades por exchange
```

**Validações:**
- `max_per_exchange` <= `max_trades`
- Todos devem ser > 0

#### Drawdown Control

```yaml
drawdown_control:
  max_drawdown_percentage: 15.0    # Máximo drawdown aceitável (%)
  enable_emergency_exit: true      # Habilitar saída de emergência
  emergency_exit_percentage: 20.0  # Drawdown que dispara saída de emergência
  pause_trading_on_breach: true    # Pausar trading quando limite excedido
  calculation_period_days: 30      # Período para cálculo de drawdown
```

**Validações:**
- Se `enable_emergency_exit` = true, `emergency_exit_percentage` > `max_drawdown_percentage`
- `calculation_period_days` > 0

#### Risk Check Settings

```yaml
risk_check_interval: 1.0           # Intervalo de verificação de risco (segundos)
emergency_only_mode: false         # Modo apenas emergências (sistema degradado)
```

**Validações:**
- `risk_check_interval` > 0

### 🏦 Exchange Configuration (`exchanges`)

Configurações para cada exchange.

#### Binance

```yaml
exchanges:
  binance:
    enabled: false                  # Habilitar exchange
    sandbox: false                  # IMPORTANTE: true apenas para testnet, false para produção
    api_key: null                   # API key (de env: BINANCE_API_KEY)
    api_secret: null                # API secret (de env: BINANCE_API_SECRET)
    rate_limits:
      requests_per_second: 10      # Requests por segundo (1-100)
      orders_per_day: 200000       # Ordens por dia (>= 1)
```

**Variáveis de Ambiente:**
- `BINANCE_API_KEY`: API key do Binance
- `BINANCE_API_SECRET`: API secret do Binance
- `BINANCE_SANDBOX`: Usar sandbox/testnet (true) ou produção (false)
  **CRÍTICO**: Use `false` para API keys de produção, `true` apenas para testnet/testnet.binance.vision

#### Coinbase Pro

```yaml
exchanges:
  coinbase:
    enabled: false                  # Habilitar exchange
    sandbox: false                  # IMPORTANTE: true apenas para testnet, false para produção
    api_key: null                   # API key (de env: COINBASE_API_KEY)
    api_secret: null                # API secret (de env: COINBASE_API_SECRET)
    passphrase: null                # Passphrase (de env: COINBASE_PASSPHRASE)
    rate_limits:
      requests_per_second: 3       # Requests por segundo (1-100)
      orders_per_day: 10000        # Ordens por dia (>= 1)
```

**Variáveis de Ambiente:**
- `COINBASE_API_KEY`: API key do Coinbase
- `COINBASE_API_SECRET`: API secret do Coinbase
- `COINBASE_PASSPHRASE`: Passphrase do Coinbase
- `COINBASE_SANDBOX`: Usar sandbox/testnet (true) ou produção (false)
  **CRÍTICO**: Use `false` para API keys de produção, `true` apenas para sandbox

### 📊 Strategies Configuration (`strategies`)

Configuração de estratégias de trading.

```yaml
strategies:
  enabled: []                      # Lista de estratégias habilitadas
  default_params: {}               # Parâmetros padrão para estratégias
```

**Exemplo:**

```yaml
strategies:
  enabled:
    - "rsi_mean_reversion"
    - "macd_crossover"
  default_params:
    rsi_mean_reversion:
      rsi_period: 14
      rsi_oversold: 30
      rsi_overbought: 70
    macd_crossover:
      fast_period: 12
      slow_period: 26
      signal_period: 9
```

### 🌐 API Configuration (`api`)

Configurações da API REST.

```yaml
api:
  host: "0.0.0.0"                  # Host da API
  port: 8000                       # Porta (1-65535)
  workers: 4                       # Número de workers (1-32)
  reload: false                    # Auto-reload (apenas development)
  cors:
    enabled: true                  # Habilitar CORS
    origins:                        # Origens permitidas
      - "http://localhost:3000"
```

**Variáveis de Ambiente:**
- `API_HOST`: Host da API
- `API_PORT`: Porta da API
- `API_WORKERS`: Número de workers

### 📝 Logging Configuration (`logging`)

Configurações de logging.

```yaml
logging:
  level: "INFO"                    # Nível de log
  file_path: "./data/logs/crypto-bot.log"  # Caminho do arquivo de log
  max_size: "10MB"                 # Tamanho máximo do arquivo
  backup_count: 5                  # Número de backups (0-100)
  format: "json"                   # Formato: "json" ou "pretty"
  handlers:                        # Handlers habilitados
    - console                      # Console
    - file                         # Arquivo
```

**Valores Válidos:**
- `level`: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `format`: `"json"` ou `"pretty"`
- `handlers`: `["console"]`, `["file"]`, ou `["console", "file"]`

**Variáveis de Ambiente:**
- `LOG_LEVEL`: Nível de log
- `LOG_FILE_PATH`: Caminho do arquivo de log

### 📊 Monitoring Configuration (`monitoring`)

Configurações de monitoramento.

```yaml
monitoring:
  enabled: true                     # Habilitar monitoramento
  metrics_enabled: true            # Habilitar métricas
  health_check_interval: 60        # Intervalo de health check em segundos (10-3600)
```

### 🔔 Notifications Configuration (`notifications`)

Configurações de notificações.

#### Telegram

```yaml
notifications:
  telegram:
    enabled: false                  # Habilitar notificações Telegram
    token: null                     # Bot token (de env: TELEGRAM_BOT_TOKEN)
    chat_id: null                   # Chat ID (de env: TELEGRAM_CHAT_ID)
```

**Variáveis de Ambiente:**
- `TELEGRAM_BOT_TOKEN`: Token do bot Telegram
- `TELEGRAM_CHAT_ID`: Chat ID para enviar mensagens

#### Discord

```yaml
notifications:
  discord:
    enabled: false                  # Habilitar notificações Discord
    webhook_url: null               # Webhook URL (de env: DISCORD_WEBHOOK_URL)
```

**Variáveis de Ambiente:**
- `DISCORD_WEBHOOK_URL`: URL do webhook Discord

#### Email

```yaml
notifications:
  email:
    enabled: false                  # Habilitar notificações por email
    # Configurações adicionais via env vars
```

**Variáveis de Ambiente:**
- `EMAIL_SMTP_HOST`: Servidor SMTP
- `EMAIL_SMTP_PORT`: Porta SMTP
- `EMAIL_SMTP_USER`: Usuário SMTP
- `EMAIL_SMTP_PASSWORD`: Senha SMTP
- `EMAIL_FROM`: Email remetente
- `EMAIL_TO`: Email destinatário

### 🔒 Security Configuration (`security`)

Configurações de segurança.

```yaml
security:
  encryption_key: null              # Chave de criptografia (REQUIRED, de env: ENCRYPTION_KEY)
  jwt_secret: null                 # Secret JWT (de env: JWT_SECRET)
```

**Variáveis de Ambiente (OBRIGATÓRIAS):**
- `ENCRYPTION_KEY`: Chave AES-256 de 32 bytes (mínimo 32 caracteres) para criptografar dados sensíveis no banco. **REQUIRED**. Gere com: `openssl rand -hex 32`

**Variáveis de Ambiente (Opcionais):**
- `JWT_SECRET`: Secret para assinatura de tokens JWT

## 🌍 Perfis de Ambiente

### Development

```yaml
app:
  log_level: "DEBUG"

database:
  echo: true  # Log SQL queries

trading:
  dry_run: true
  max_concurrent_trades: 2

exchanges:
  binance:
    enabled: true
    sandbox: true
  coinbase:
    enabled: true
    sandbox: true

api:
  reload: true  # Auto-reload
  workers: 1

logging:
  level: "DEBUG"
  handlers:
    - console  # Apenas console
  format: "pretty"
```

**Características:**
- Debug logging habilitado
- SQL echo habilitado
- Dry-run sempre ativo
- Sandbox/testnet apenas
- Auto-reload da API
- Logging apenas no console

### Staging

**Características:**
- Info logging
- Dry-run ativo
- Sandbox/testnet
- Logging em arquivo + console
- Teste de setup similar à produção

### Production

**Características:**
- Warning-level logging mínimo
- Trading real habilitado (`dry_run: false`)
- APIs de produção
- Logging apenas em arquivo
- Configurações otimizadas
- Sem auto-reload

## 📝 Exemplos de Configuração

### Exemplo Mínimo

```yaml
# config/environments/base.yaml
app:
  name: "Crypto Trading Bot"
  version: "0.1.0"
  log_level: "INFO"

database:
  host: "localhost"
  port: 5432
  name: "crypto_bot"

trading:
  dry_run: true
  max_concurrent_trades: 5

exchanges:
  binance:
    enabled: false
    sandbox: true

security:
  encryption_key: "${ENCRYPTION_KEY}"
```

### Exemplo Completo de Risco

```yaml
trading:
  risk:
    stop_loss:
      enabled: true
      percentage: 2.0
      cooldown_seconds: 60
      trailing: false
    
    take_profit:
      enabled: true
      percentage: 5.0
      cooldown_seconds: 60
      partial_close: false
    
    exposure_limit:
      max_per_asset: 10000.0
      max_per_exchange: 30000.0
      max_total: 50000.0
      base_currency: "USDT"
    
    trailing_stop:
      enabled: true
      trailing_percentage: 3.0
      activation_percentage: 5.0
      update_interval_seconds: 5
    
    max_concurrent_trades:
      max_trades: 5
      max_per_asset: 1
      max_per_exchange: 3
    
    drawdown_control:
      max_drawdown_percentage: 15.0
      enable_emergency_exit: true
      emergency_exit_percentage: 20.0
      pause_trading_on_breach: true
      calculation_period_days: 30
    
    risk_check_interval: 1.0
    emergency_only_mode: false
```

## 🔍 Validação e Troubleshooting

### Validação Automática

Todas as configurações são validadas automaticamente usando Pydantic:

```python
from crypto_bot.config import load_config

try:
    config = load_config()
    print("✓ Configuração válida")
except ValidationError as e:
    print(f"✗ Erro de validação: {e}")
```

### Erros Comuns

#### "ENCRYPTION_KEY environment variable is required"

**Solução:** Defina `ENCRYPTION_KEY` no arquivo `.env`. **CRITICAL**: Deve ter no mínimo 32 caracteres. Gere uma chave segura com:

```bash
# Gerar chave segura
openssl rand -hex 32

# Adicionar ao .env
ENCRYPTION_KEY=<chave_gerada_acima>
```

#### "Configuration validation failed"

**Possíveis causas:**
- Valores fora dos limites (ex: port > 65535)
- Campos obrigatórios ausentes
- Validações lógicas falhadas (ex: max_per_asset > max_per_exchange)

**Solução:** Verifique a mensagem de erro específica e ajuste os valores.

#### "Invalid environment"

**Solução:** Use um dos ambientes válidos:
- `development`
- `staging`
- `production`

Defina via variável de ambiente:
```bash
export ENVIRONMENT=development
```

#### "Configuration file not found"

**Solução:** Verifique se os arquivos existem:
- `config/environments/base.yaml`
- `config/environments/{environment}.yaml`

## 🔧 Adicionando Novas Configurações

Para adicionar novas opções de configuração:

1. **Atualize o schema** em `src/crypto_bot/config/schemas.py`:

```python
class NewFeatureConfig(BaseModel):
    enabled: bool = False
    option: str = "default"
```

2. **Adicione ao Config principal:**

```python
class Config(BaseModel):
    # ... campos existentes ...
    new_feature: NewFeatureConfig = Field(default_factory=NewFeatureConfig)
```

3. **Adicione ao `base.yaml`:**

```yaml
new_feature:
  enabled: false
  option: "default"
```

4. **Adicione testes** em `tests/unit/config/test_schemas.py`

5. **Atualize esta documentação**

## 📚 Referências

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [YAML Specification](https://yaml.org/spec/)
- [Environment Variables Best Practices](../security/HARDENING_GUIDE.md)

## ✅ Checklist de Configuração

Antes de executar em produção, verifique:

- [ ] `ENCRYPTION_KEY` definido e seguro
- [ ] `dry_run: false` apenas em produção
- [ ] Credenciais de exchange configuradas corretamente
- [ ] Sandbox desabilitado em produção
- [ ] Limites de risco configurados apropriadamente
- [ ] Logging configurado para arquivo em produção
- [ ] Database credentials seguros
- [ ] Testado em staging antes de produção
- [ ] Backup de configurações realizado
- [ ] Documentação atualizada

---

**⚠️ IMPORTANTE**: Nunca commit credenciais ou chaves de API no controle de versão. Use sempre variáveis de ambiente para dados sensíveis.
