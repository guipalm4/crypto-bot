# PRD - Robô de Trading de Criptomoedas (Crypto Trading Bot)

## 📋 Visão Geral do Projeto

### Objetivo
Desenvolver um robô de trading automatizado em Python capaz de executar operações de compra e venda de criptoativos em múltiplas corretoras, com arquitetura modular baseada em plugins, gestão de risco robusta e parametrização completa.

### Stack Tecnológico
- **Linguagem**: Python 3.12+ (versão mais recente e estável)
- **Database**: PostgreSQL 16+
- **ORM**: SQLAlchemy 2.x (última versão)
- **Validação**: Pydantic 2.x
- **Exchange Integration**: CCXT 4.x
- **Testing**: pytest, pytest-asyncio
- **Code Quality**: black, flake8, mypy, isort
- **Architecture**: Domain-Driven Design (DDD)

### Princípios de Desenvolvimento
- Código modular e desacoplado
- PEP 8 compliance
- Type hints em todo o código
- Testes unitários e de integração
- Documentação inline (docstrings)
- Configuration over hardcoding
- Plugin-based architecture
- Security by design

---

## 🎯 MVP - Escopo de 1 Mês

### Funcionalidades Prioritárias

#### 1. Core Trading Engine
**Contexto**: Motor principal de execução de trades
**Requisitos**:
- Executar ordens de compra (market e limit orders)
- Executar ordens de venda (market e limit orders)
- Cancelar ordens abertas
- Consultar status de ordens
- Verificar saldo disponível
- **Parâmetros configuráveis**:
  - Tipo de ordem (market/limit)
  - Quantidade a negociar
  - Preço limite (para limit orders)
  - Timeout de ordem
  - Retry policy (tentativas, intervalo)

#### 2. Sistema de Registro e Persistência
**Contexto**: Rastreabilidade completa de todas as operações
**Requisitos**:
- Registrar todas as ordens executadas
- Armazenar histórico de preços
- Salvar snapshots de carteira
- Registrar eventos do sistema
- **Dados a persistir**:
  - ID da ordem na exchange
  - Timestamp de criação e execução
  - Par de trading (ex: BTC/USDT)
  - Tipo (compra/venda)
  - Quantidade
  - Preço de execução
  - Taxas (fees)
  - Status (pending/filled/cancelled/failed)
  - Exchange utilizada
  - Estratégia aplicada
  - Razão da operação

#### 3. Gestão de Risco Básica
**Contexto**: Proteção do capital e controle de exposição
**Requisitos**:
- Stop Loss automático
- Take Profit automático
- Limite de exposição por ativo
- Limite de exposição por exchange
- **Parâmetros configuráveis**:
  - Percentual de stop loss (ex: 2%, 5%, 10%)
  - Percentual de take profit (ex: 3%, 5%, 10%, 20%)
  - Percentual máximo de capital por trade (ex: 5%, 10%)
  - Percentual máximo de capital por ativo (ex: 20%, 30%)
  - Percentual máximo de capital por exchange (ex: 50%)
  - Stop loss trailing (ativo/inativo, distância)
  - Máximo de trades simultâneos
  - Drawdown máximo permitido

#### 4. Plugin System - Exchanges
**Contexto**: Suporte multi-exchange via arquitetura de plugins
**Requisitos**:
- Interface abstrata para exchanges
- Implementar plugins para 2 exchanges no MVP:
  - Binance (maior liquidez)
  - Coinbase (alternativa popular)
- **Funcionalidades por plugin**:
  - Autenticação via API keys
  - Fetch de orderbook
  - Fetch de ticker price
  - Fetch de histórico OHLCV
  - Executar ordens
  - Consultar ordens
  - Consultar saldo
- **Parâmetros configuráveis por exchange**:
  - API Key
  - API Secret
  - Passphrase (se necessário)
  - Testnet/Sandbox mode
  - Rate limits
  - Timeout
  - Proxy (opcional)

#### 5. Plugin System - Indicadores Técnicos
**Contexto**: Análise técnica modular via plugins
**Requisitos**:
- Interface abstrata para indicadores
- Implementar 3 indicadores no MVP:
  - **RSI (Relative Strength Index)**:
    - Período (padrão: 14)
    - Zona de sobrevenda (padrão: 30)
    - Zona de sobrecompra (padrão: 70)
  - **MACD (Moving Average Convergence Divergence)**:
    - Fast period (padrão: 12)
    - Slow period (padrão: 26)
    - Signal period (padrão: 9)
  - **EMA (Exponential Moving Average)**:
    - Período (padrão: 20, 50, 200)
- Sistema de cache de indicadores calculados
- **Parâmetros configuráveis por indicador**: todos os períodos e thresholds

#### 6. Plugin System - Estratégias
**Contexto**: Lógica de decisão modular via plugins
**Requisitos**:
- Interface abstrata para estratégias
- Implementar 2 estratégias simples no MVP:
  - **RSI Mean Reversion**:
    - Compra quando RSI < 30
    - Vende quando RSI > 70
    - Parâmetros: período RSI, thresholds
  - **MACD Crossover**:
    - Compra quando MACD cruza acima da linha de sinal
    - Vende quando MACD cruza abaixo da linha de sinal
    - Parâmetros: períodos MACD
- **Parâmetros configuráveis**:
  - Indicadores utilizados e seus parâmetros
  - Regras de entrada (condições para compra)
  - Regras de saída (condições para venda)
  - Timeframe de análise
  - Ativo(s) a operar

#### 7. Sistema de Configuração
**Contexto**: Centralização de parâmetros em arquivos de configuração
**Requisitos**:
- Arquivo de configuração em YAML/JSON
- Suporte a múltiplos perfis (dev, staging, production)
- Variáveis de ambiente para dados sensíveis
- Validação de configuração com Pydantic
- **Configurações principais**:
  - Exchanges ativas e credenciais
  - Estratégias ativas e parâmetros
  - Regras de gestão de risco
  - Ativos a operar
  - Timeframes
  - Logging level
  - Database connection

#### 8. Logging e Monitoramento Básico
**Contexto**: Observabilidade para debugging e auditoria
**Requisitos**:
- Structured logging (JSON format)
- Níveis: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Logs separados por módulo
- Rotação de logs
- **Eventos a logar**:
  - Inicialização do sistema
  - Conexão com exchanges
  - Execução de estratégias
  - Sinais de compra/venda
  - Execução de ordens
  - Erros e exceções
  - Mudanças de estado

#### 9. CLI Básica
**Contexto**: Interface de linha de comando para operação
**Requisitos**:
- Iniciar/parar o bot
- Listar estratégias ativas
- Listar posições abertas
- Verificar saldo
- Forçar execução de estratégia
- Visualizar logs em tempo real
- Dry-run mode (simulação sem execução real)

---

## 🚀 Pós-MVP - Roadmap de Evolução

### Fase 2: Aprimoramentos Core (Mês 2-3)

#### 10. Gestão de Risco Avançada
- Position sizing dinâmico (Kelly Criterion, Fixed Fractional)
- Correlação entre ativos
- Portfolio rebalancing automático
- Circuit breaker (parada automática em eventos anormais)
- Análise de volatilidade (ATR - Average True Range)
- Maximum adverse excursion tracking
- Risk-reward ratio enforcement
- **Parâmetros**:
  - Método de position sizing
  - Frequência de rebalanceamento
  - Thresholds de circuit breaker
  - Janela de volatilidade

#### 11. Backtesting Engine
- Simulação de estratégias com dados históricos
- Métricas de performance:
  - Sharpe Ratio
  - Sortino Ratio
  - Maximum Drawdown
  - Win Rate
  - Profit Factor
  - Expectancy
- Visualização de resultados (gráficos)
- Otimização de parâmetros (grid search, random search)
- Walk-forward analysis
- **Parâmetros**:
  - Período de backtest
  - Comissões e slippage
  - Capital inicial
  - Parâmetros da estratégia

#### 12. Paper Trading
- Modo de simulação com dados reais
- Carteira virtual
- Execução sem risco real
- Validação de estratégias antes de produção
- Estatísticas de performance

#### 13. Mais Exchanges
- Kraken
- OKX
- Bybit
- KuCoin
- Bitfinex

#### 14. Indicadores Avançados
- Bollinger Bands
- ATR (Average True Range)
- Ichimoku Cloud
- Volume Profile
- On-Balance Volume (OBV)
- Fibonacci Retracement
- Parabolic SAR
- Stochastic Oscillator

#### 15. Estratégias Avançadas
- Grid Trading
- DCA (Dollar Cost Averaging)
- Arbitragem (intra-exchange e inter-exchange)
- Market Making
- Pairs Trading
- Mean Reversion avançada
- Trend Following avançado
- Breakout strategies

### Fase 3: Features Inteligentes (Mês 4-6)

#### 16. Machine Learning Pipeline
- Previsão de preços (LSTM, GRU, Transformer)
- Classificação de tendências (Random Forest, XGBoost)
- Clustering de regimes de mercado
- Reinforcement Learning para otimização de estratégias
- Feature engineering automático
- Model versioning e A/B testing
- **Parâmetros**:
  - Modelo selecionado
  - Hiperparâmetros
  - Features utilizadas
  - Frequência de retreinamento
  - Threshold de confiança

#### 17. Sentiment Analysis
- Web scraping de notícias cripto
- Análise de sentimento Twitter/X
- Análise de sentimento Reddit
- Fear & Greed Index integration
- Social signals como input para estratégias
- **Fontes**:
  - CoinTelegraph, CoinDesk
  - Twitter crypto influencers
  - Reddit r/cryptocurrency
  - Alternative.me Fear & Greed Index

#### 18. On-Chain Analysis
- Métricas blockchain como indicadores
- Exchange flows (deposits/withdrawals)
- Whale wallet tracking
- Hash rate analysis (Bitcoin)
- Network fees
- Active addresses
- **Parâmetros**:
  - Chains monitoradas
  - Wallets rastreadas
  - Thresholds de alerta

#### 19. Adaptive Strategies
- Auto-ajuste de parâmetros baseado em performance
- Detecção de mudança de regime de mercado
- Switch automático entre estratégias
- Meta-learning para combinação de estratégias

### Fase 4: Produção e Escalabilidade (Mês 7-9)

#### 20. Dashboard Web
- Interface gráfica (FastAPI + React/Vue)
- Visualização de posições em tempo real
- Gráficos de performance
- Configuração via UI
- Alertas visuais
- Mobile responsive

#### 21. Sistema de Alertas
- Notificações via:
  - Telegram bot
  - Email
  - Discord webhook
  - SMS (Twilio)
- **Tipos de alerta**:
  - Ordem executada
  - Stop loss/Take profit acionado
  - Erro crítico
  - Drawdown excessivo
  - Nova oportunidade detectada

#### 22. Multi-Account Support
- Gerenciar múltiplas contas/exchanges
- Agregação de portfolio
- Performance consolidada
- Alocação de capital entre contas

#### 23. High-Frequency Trading (HFT) Capabilities
- Otimização de latência
- WebSocket streams
- Async execution otimizada
- Co-location considerations

#### 24. Distributed Architecture
- Message queue (RabbitMQ/Redis)
- Worker pools para processamento paralelo
- Load balancing
- Containerização (Docker)
- Orquestração (Kubernetes)

### Fase 5: Avançado e Compliance (Mês 10-12)

#### 25. Tax Reporting
- Cálculo de ganhos/perdas
- Relatórios para declaração
- FIFO/LIFO tracking
- Suporte a diferentes jurisdições

#### 26. API Pública
- Endpoints REST para integração externa
- Webhooks para eventos
- Rate limiting
- API key management

#### 27. Security Hardening
- Encryption at rest
- Secrets management (HashiCorp Vault)
- 2FA para operações críticas
- Audit trail completo
- Penetration testing

#### 28. Advanced Analytics
- Custom metrics dashboard
- A/B testing framework
- Cohort analysis
- Attribution modeling

#### 29. Compliance e Auditoria
- KYC/AML integration
- Trade reporting para reguladores
- Immutable audit log
- Compliance rules engine

---

## 🏗️ Arquitetura Técnica

### Estrutura de Diretórios (DDD-Inspired)

```
cripto-bot/
├── src/
│   ├── domain/                    # Regras de negócio puras
│   │   ├── entities/              # Entidades de domínio
│   │   │   ├── order.py
│   │   │   ├── position.py
│   │   │   ├── trade.py
│   │   │   ├── asset.py
│   │   │   └── portfolio.py
│   │   ├── value_objects/         # Value objects imutáveis
│   │   │   ├── price.py
│   │   │   ├── quantity.py
│   │   │   ├── percentage.py
│   │   │   └── timeframe.py
│   │   └── events/                # Domain events
│   │       ├── order_executed.py
│   │       ├── stop_loss_triggered.py
│   │       └── signal_generated.py
│   │
│   ├── application/               # Use cases e orquestração
│   │   ├── services/
│   │   │   ├── trading_service.py
│   │   │   ├── risk_service.py
│   │   │   ├── strategy_service.py
│   │   │   └── backtest_service.py
│   │   └── dto/                   # Data Transfer Objects
│   │       ├── order_dto.py
│   │       └── trade_dto.py
│   │
│   ├── infrastructure/            # Implementações técnicas
│   │   ├── database/
│   │   │   ├── models/           # SQLAlchemy models
│   │   │   ├── repositories/     # Repository pattern
│   │   │   └── migrations/       # Alembic migrations
│   │   ├── exchanges/            # Exchange adapters
│   │   │   ├── base.py
│   │   │   ├── binance.py
│   │   │   └── coinbase.py
│   │   └── external/             # APIs externas
│   │
│   ├── plugins/                   # Sistema de plugins
│   │   ├── indicators/
│   │   │   ├── base.py
│   │   │   ├── rsi.py
│   │   │   ├── macd.py
│   │   │   └── ema.py
│   │   ├── strategies/
│   │   │   ├── base.py
│   │   │   ├── rsi_mean_reversion.py
│   │   │   └── macd_crossover.py
│   │   └── registry.py           # Plugin loader/registry
│   │
│   ├── config/                    # Configurações
│   │   ├── settings.py
│   │   ├── config.yaml
│   │   └── schemas.py            # Pydantic schemas
│   │
│   └── utils/                     # Utilitários
│       ├── logging.py
│       ├── decorators.py
│       └── validators.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                          # Documentação
├── scripts/                       # Scripts utilitários
├── alembic/                       # Database migrations
├── .env.example
├── pyproject.toml
├── requirements.txt
├── README.md
└── docker-compose.yml
```

### Modelo de Dados (PostgreSQL)

#### Tabelas Principais

**exchanges**
- id (UUID, PK)
- name (VARCHAR) - "binance", "coinbase"
- api_key_encrypted (TEXT)
- api_secret_encrypted (TEXT)
- is_active (BOOLEAN)
- is_testnet (BOOLEAN)
- config_json (JSONB) - parâmetros específicos
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

**assets**
- id (UUID, PK)
- symbol (VARCHAR) - "BTC", "ETH"
- name (VARCHAR)
- is_active (BOOLEAN)
- metadata_json (JSONB)
- created_at (TIMESTAMP)

**trading_pairs**
- id (UUID, PK)
- base_asset_id (UUID, FK -> assets)
- quote_asset_id (UUID, FK -> assets)
- exchange_id (UUID, FK -> exchanges)
- symbol (VARCHAR) - "BTC/USDT"
- min_order_size (DECIMAL)
- max_order_size (DECIMAL)
- tick_size (DECIMAL)
- is_active (BOOLEAN)

**orders**
- id (UUID, PK)
- exchange_order_id (VARCHAR) - ID na exchange
- trading_pair_id (UUID, FK)
- exchange_id (UUID, FK)
- strategy_id (UUID, FK)
- type (ENUM) - "market", "limit"
- side (ENUM) - "buy", "sell"
- status (ENUM) - "pending", "filled", "cancelled", "failed"
- quantity (DECIMAL)
- price (DECIMAL)
- executed_price (DECIMAL)
- executed_quantity (DECIMAL)
- fee (DECIMAL)
- fee_currency (VARCHAR)
- reason (TEXT) - motivo da ordem
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
- executed_at (TIMESTAMP)

**trades** (ordens executadas)
- id (UUID, PK)
- order_id (UUID, FK -> orders)
- exchange_trade_id (VARCHAR)
- price (DECIMAL)
- quantity (DECIMAL)
- fee (DECIMAL)
- timestamp (TIMESTAMP)

**positions**
- id (UUID, PK)
- trading_pair_id (UUID, FK)
- exchange_id (UUID, FK)
- strategy_id (UUID, FK)
- entry_order_id (UUID, FK -> orders)
- exit_order_id (UUID, FK -> orders)
- side (ENUM) - "long", "short"
- quantity (DECIMAL)
- entry_price (DECIMAL)
- exit_price (DECIMAL)
- stop_loss (DECIMAL)
- take_profit (DECIMAL)
- pnl (DECIMAL)
- pnl_percentage (DECIMAL)
- status (ENUM) - "open", "closed"
- opened_at (TIMESTAMP)
- closed_at (TIMESTAMP)

**strategies**
- id (UUID, PK)
- name (VARCHAR)
- plugin_name (VARCHAR) - referência ao plugin
- description (TEXT)
- parameters_json (JSONB) - parâmetros configuráveis
- is_active (BOOLEAN)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

**strategy_executions**
- id (UUID, PK)
- strategy_id (UUID, FK)
- trading_pair_id (UUID, FK)
- signal_type (ENUM) - "buy", "sell", "hold"
- signal_strength (DECIMAL) - 0.0 a 1.0
- indicators_json (JSONB) - valores dos indicadores
- executed_at (TIMESTAMP)

**risk_events**
- id (UUID, PK)
- event_type (ENUM) - "stop_loss", "take_profit", "drawdown", "exposure_limit"
- position_id (UUID, FK)
- description (TEXT)
- severity (ENUM) - "info", "warning", "critical"
- metadata_json (JSONB)
- created_at (TIMESTAMP)

**balance_snapshots**
- id (UUID, PK)
- exchange_id (UUID, FK)
- asset_id (UUID, FK)
- free_balance (DECIMAL)
- locked_balance (DECIMAL)
- total_balance (DECIMAL)
- value_in_usd (DECIMAL)
- snapshot_at (TIMESTAMP)

**market_data** (cache de dados históricos)
- id (UUID, PK)
- trading_pair_id (UUID, FK)
- exchange_id (UUID, FK)
- timeframe (VARCHAR) - "1m", "5m", "1h", "1d"
- timestamp (TIMESTAMP)
- open (DECIMAL)
- high (DECIMAL)
- low (DECIMAL)
- close (DECIMAL)
- volume (DECIMAL)

**indicator_cache**
- id (UUID, PK)
- indicator_name (VARCHAR)
- trading_pair_id (UUID, FK)
- timeframe (VARCHAR)
- parameters_hash (VARCHAR) - hash dos parâmetros
- value (DECIMAL)
- metadata_json (JSONB)
- calculated_at (TIMESTAMP)

**system_logs**
- id (UUID, PK)
- level (VARCHAR)
- module (VARCHAR)
- message (TEXT)
- context_json (JSONB)
- created_at (TIMESTAMP)

### Interfaces de Plugin

#### Exchange Plugin Interface
```python
class ExchangePlugin(ABC):
    @abstractmethod
    async def connect(self) -> bool: ...
    
    @abstractmethod
    async def get_balance(self, asset: str) -> Decimal: ...
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker: ...
    
    @abstractmethod
    async def get_orderbook(self, symbol: str, depth: int) -> OrderBook: ...
    
    @abstractmethod
    async def create_order(self, order: Order) -> str: ...
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool: ...
    
    @abstractmethod
    async def get_order_status(self, order_id: str) -> OrderStatus: ...
    
    @abstractmethod
    async def get_historical_data(
        self, symbol: str, timeframe: str, since: datetime, limit: int
    ) -> List[OHLCV]: ...
```

#### Indicator Plugin Interface
```python
class IndicatorPlugin(ABC):
    @abstractmethod
    def calculate(self, data: pd.DataFrame, **params) -> pd.Series: ...
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict: ...
    
    @abstractmethod
    def validate_parameters(self, params: Dict) -> bool: ...
```

#### Strategy Plugin Interface
```python
class StrategyPlugin(ABC):
    @abstractmethod
    async def analyze(
        self, market_data: MarketData, indicators: Dict[str, pd.Series]
    ) -> Signal: ...
    
    @abstractmethod
    def get_required_indicators(self) -> List[str]: ...
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict: ...
    
    @abstractmethod
    def validate_parameters(self, params: Dict) -> bool: ...
```

---

## 🔒 Segurança

### Práticas Obrigatórias

1. **Credenciais**
   - Nunca hardcode API keys
   - Usar variáveis de ambiente
   - Criptografar credenciais no banco (AES-256)
   - Rotação periódica de keys

2. **API Keys Permissions**
   - Usar API keys somente-leitura para backtest
   - Nunca habilitar saque (withdrawal) nas API keys
   - IP whitelist quando possível

3. **Code Security**
   - Input validation em todos os endpoints
   - SQL injection prevention (usar ORM)
   - Rate limiting
   - Dependency scanning (safety, bandit)

4. **Operational Security**
   - Logs não devem conter dados sensíveis
   - Backup regular do banco de dados
   - Disaster recovery plan
   - 2FA para acesso admin

---

## 🧪 Estratégia de Testes

### Cobertura Mínima: 80%

1. **Unit Tests**
   - Testar lógica de negócio isoladamente
   - Mock de dependências externas
   - Testar edge cases

2. **Integration Tests**
   - Testar integração com exchanges (testnet)
   - Testar persistência no banco
   - Testar plugin loading

3. **E2E Tests**
   - Simular fluxo completo de trading
   - Testar cenários de erro
   - Testar recovery de falhas

4. **Performance Tests**
   - Load testing de estratégias
   - Latency de execução de ordens
   - Memory leaks

---

## 📊 Métricas de Sucesso

### MVP (Mês 1)
- ✅ Executar trades em 2 exchanges
- ✅ 2 estratégias funcionais
- ✅ Stop loss/take profit operacional
- ✅ 100% de trades registrados
- ✅ Zero perda de dados
- ✅ Cobertura de testes > 70%

### Produção (Mês 6)
- ✅ Uptime > 99%
- ✅ Latência de execução < 500ms
- ✅ Sharpe Ratio > 1.5
- ✅ Win Rate > 55%
- ✅ Maximum Drawdown < 15%
- ✅ Zero security incidents

---

## 🛠️ Ferramentas e Bibliotecas Recomendadas

### Core
- **ccxt**: Integração multi-exchange (v4.2+)
- **sqlalchemy**: ORM (v2.0+)
- **alembic**: Database migrations
- **pydantic**: Data validation (v2.0+)
- **python-dotenv**: Environment variables

### Data & Analysis
- **pandas**: Data manipulation
- **numpy**: Numerical computing
- **ta-lib**: Technical analysis (opcional, usar pandas-ta como alternativa)
- **pandas-ta**: Technical indicators

### Async & Concurrency
- **asyncio**: Async framework nativo
- **aiohttp**: Async HTTP client
- **asyncpg**: Async PostgreSQL driver

### Testing
- **pytest**: Test framework
- **pytest-asyncio**: Async testing
- **pytest-cov**: Coverage
- **faker**: Mock data generation
- **freezegun**: Time mocking

### Code Quality
- **black**: Code formatter
- **flake8**: Linter
- **mypy**: Type checker
- **isort**: Import sorter
- **bandit**: Security linter

### Logging & Monitoring
- **structlog**: Structured logging
- **prometheus-client**: Metrics (futuro)
- **sentry-sdk**: Error tracking (futuro)

### CLI
- **click**: CLI framework
- **rich**: Terminal formatting

### ML (Futuro)
- **scikit-learn**: Traditional ML
- **tensorflow/pytorch**: Deep learning
- **xgboost**: Gradient boosting
- **optuna**: Hyperparameter tuning

---

## 📝 Formato de Configuração

### config.yaml (exemplo)
```yaml
environment: production  # dev, staging, production

database:
  host: ${DB_HOST}
  port: 5432
  name: cripto_bot
  user: ${DB_USER}
  password: ${DB_PASSWORD}

exchanges:
  binance:
    enabled: true
    testnet: false
    api_key: ${BINANCE_API_KEY}
    api_secret: ${BINANCE_API_SECRET}
    rate_limit: 1200
  coinbase:
    enabled: true
    testnet: false
    api_key: ${COINBASE_API_KEY}
    api_secret: ${COINBASE_API_SECRET}

trading:
  dry_run: false  # se true, não executa ordens reais
  max_concurrent_trades: 5
  default_order_type: limit

risk_management:
  max_position_size_pct: 10.0  # % do capital total
  max_portfolio_risk_pct: 30.0
  default_stop_loss_pct: 2.0
  default_take_profit_pct: 5.0
  trailing_stop: true
  trailing_stop_distance_pct: 1.0
  max_drawdown_pct: 15.0

strategies:
  - name: rsi_mean_reversion
    enabled: true
    pairs:
      - BTC/USDT
      - ETH/USDT
    timeframe: 1h
    parameters:
      rsi_period: 14
      rsi_oversold: 30
      rsi_overbought: 70
      
  - name: macd_crossover
    enabled: true
    pairs:
      - BTC/USDT
    timeframe: 4h
    parameters:
      fast_period: 12
      slow_period: 26
      signal_period: 9

logging:
  level: INFO
  format: json
  output: both  # console, file, both
  file_path: logs/bot.log
  max_file_size_mb: 50
  backup_count: 10
```

---

## 🚦 Roadmap Visual

```
Mês 1 (MVP)
├─ Core Trading Engine ✓
├─ Database & Persistence ✓
├─ Risk Management Básico ✓
├─ Plugins: 2 Exchanges ✓
├─ Plugins: 3 Indicators ✓
├─ Plugins: 2 Strategies ✓
├─ Config System ✓
├─ Logging ✓
└─ CLI ✓

Mês 2-3 (Aprimoramentos)
├─ Risk Avançado
├─ Backtesting
├─ Paper Trading
├─ +3 Exchanges
├─ +5 Indicators
└─ +3 Strategies

Mês 4-6 (ML & IA)
├─ ML Pipeline
├─ Sentiment Analysis
├─ On-Chain Analysis
├─ Adaptive Strategies
└─ Dashboard Web

Mês 7-9 (Produção)
├─ Sistema de Alertas
├─ Multi-Account
├─ HFT Optimization
└─ Distributed Architecture

Mês 10-12 (Avançado)
├─ Tax Reporting
├─ API Pública
├─ Security Hardening
└─ Compliance
```

---

## ✅ Definition of Done (DoD)

Para cada feature ser considerada "completa":

1. ✅ Código implementado seguindo PEP 8
2. ✅ Type hints em todas as funções
3. ✅ Docstrings completas
4. ✅ Testes unitários com cobertura > 80%
5. ✅ Testes de integração passando
6. ✅ Parâmetros configuráveis (não hardcoded)
7. ✅ Logging apropriado
8. ✅ Error handling robusto
9. ✅ Validação de inputs
10. ✅ Code review aprovado
11. ✅ Sem warnings de linter
12. ✅ Documentação atualizada

---

## 🎓 Considerações de um Trader Experiente

### Princípios de Trading
1. **Preserve Capital**: A prioridade #1 é não perder dinheiro
2. **Risk Management > Strategy**: Gestão de risco é mais importante que a estratégia de entrada
3. **Consistency**: Resultados consistentes > trades espetaculares esporádicos
4. **Backtest, mas não confie cegamente**: Overfitting é real
5. **Paper trade antes de produção**: SEMPRE teste com dinheiro fake primeiro
6. **Start Small**: Comece com capital pequeno, escale gradualmente
7. **Market Conditions Matter**: O que funciona em bull market pode falhar em bear market
8. **Slippage & Fees**: Em produção, comissões e slippage comem muito do lucro
9. **Liquidity First**: Trade apenas pares com boa liquidez
10. **Psychology**: Remova emoção da equação (por isso robôs são úteis)

### Armadilhas Comuns
- ❌ Overtrading (excesso de operações)
- ❌ Revenge trading (tentar recuperar perdas)
- ❌ Não usar stop loss
- ❌ Position size grande demais
- ❌ Ignorar market context
- ❌ Curve fitting no backtest
- ❌ Não considerar custos operacionais

### Métricas que Importam
1. **Sharpe Ratio**: Retorno ajustado ao risco
2. **Maximum Drawdown**: Maior queda do pico
3. **Win Rate**: % de trades vencedores
4. **Profit Factor**: Lucro total / Perda total
5. **Average Win vs Average Loss**: Deve ser > 1
6. **Expectancy**: Lucro médio esperado por trade
7. **Recovery Factor**: Lucro líquido / Max drawdown

---

## 📞 Próximos Passos

1. **Review deste documento**: Validar requisitos e prioridades
2. **Setup do ambiente**: Python 3.12, PostgreSQL, dependências
3. **Inicializar Task Master AI**: Para gestão de tarefas
4. **Criar estrutura de projeto**: Seguir arquitetura DDD proposta
5. **Implementar MVP sprint by sprint**:
   - Sprint 1: Database + Config System
   - Sprint 2: Core Trading Engine
   - Sprint 3: Plugins (Exchanges + Indicators)
   - Sprint 4: Strategies + Risk Management
   - Sprint 5: Testing + Refinements

---

## 📚 Referências e Recursos

### Documentação de Bibliotecas
- [CCXT Documentation](https://docs.ccxt.com/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

### Trading & TA
- "Technical Analysis of the Financial Markets" - John Murphy
- "Algorithmic Trading" - Ernest Chan
- [Investopedia - Technical Indicators](https://www.investopedia.com/technical-indicators-4689770)

### Code Quality
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)

---

**Documento criado para otimização de desenvolvimento com IA (Cursor)**
**Versão**: 1.0
**Data**: Outubro 2025
**Objetivo**: MVP em 30 dias + Roadmap de evolução

