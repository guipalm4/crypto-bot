# 🤖 Crypto Trading Bot

[![CI/CD Pipeline](https://github.com/guipalm4/crypto-bot/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/guipalm4/crypto-bot/actions)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> Sistema automatizado de trading de criptomoedas com arquitetura modular baseada em plugins, gestão de risco robusta e suporte multi-exchange.

## 📋 Visão Geral

O Crypto Trading Bot é um sistema completo de trading automatizado desenvolvido em Python que permite executar operações de compra e venda de criptoativos em múltiplas corretoras. O projeto utiliza uma arquitetura modular baseada em plugins, permitindo fácil extensão e manutenção.

### ✨ Características Principais

- 🏗️ **Arquitetura DDD**: Domain-Driven Design para código limpo e manutenível
- 🔌 **Sistema de Plugins**: Extensível para exchanges, indicadores e estratégias
- ⚠️ **Gestão de Risco**: Stop loss, take profit, limites de exposição e drawdown
- 🏦 **Multi-Exchange**: Suporte para Binance, Coinbase e mais
- 📊 **Indicadores Técnicos**: RSI, MACD, EMA e outros
- 🎯 **Estratégias**: RSI Mean Reversion, MACD Crossover e mais
- 🔒 **Segurança**: Criptografia AES-256 para credenciais
- 📝 **Logging**: Sistema de logs estruturado e monitoramento
- 🖥️ **CLI**: Interface de linha de comando intuitiva

## 🚀 Quick Start

### Pré-requisitos

- Python 3.12+
- PostgreSQL 16+
- Docker e Docker Compose
- Git

### Instalação

1. **Clone o repositório**
   ```bash
   git clone https://github.com/guipalm4/crypto-bot.git
   cd crypto-bot
   ```

2. **Configure o ambiente**
   ```bash
   # Crie um ambiente virtual
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # ou
   .venv\Scripts\activate     # Windows

   # Instale as dependências
   pip install -r requirements.txt
   ```

3. **Configure o banco de dados**
   ```bash
   # Inicie o PostgreSQL com Docker
   docker-compose up -d

   # Execute as migrações
   alembic upgrade head
   ```

4. **Configure as variáveis de ambiente**
   ```bash
   # Copie o arquivo de exemplo
   cp .env.example .env

   # Edite o arquivo .env com suas credenciais
   nano .env
   ```

5. **Execute o bot**
   ```bash
   # Modo dry-run (simulação)
   python -m src.cli start --dry-run

   # Modo produção
   python -m src.cli start
   ```

## 📁 Estrutura do Projeto

```
crypto-bot/
├── src/                          # Código fonte principal
│   ├── domain/                   # Regras de negócio (DDD)
│   │   ├── entities/             # Entidades de domínio
│   │   ├── value_objects/        # Value objects
│   │   └── events/               # Domain events
│   ├── application/              # Use cases e orquestração
│   │   ├── services/             # Serviços de aplicação
│   │   └── dto/                  # Data Transfer Objects
│   ├── infrastructure/           # Implementações técnicas
│   │   ├── database/             # SQLAlchemy models
│   │   ├── exchanges/            # Exchange adapters
│   │   └── external/             # APIs externas
│   ├── plugins/                  # Sistema de plugins
│   │   ├── indicators/           # Indicadores técnicos
│   │   ├── strategies/           # Estratégias de trading
│   │   └── registry.py           # Plugin loader
│   ├── config/                   # Configurações
│   └── utils/                    # Utilitários
├── tests/                        # Testes
├── docs/                         # Documentação
├── .github/                      # GitHub workflows e templates
└── alembic/                      # Database migrations
```

## 🎯 Roadmap de Desenvolvimento

### 🏗️ Sprint 1: Foundation & Core Infrastructure
- [x] Project Structure & Environment Setup
- [x] Database Schema Design & Migration Setup
- [x] Configuration System Implementation
- [x] Code Quality & Compliance Automation

### 🚀 Sprint 2: Core Trading Engine & Risk Management
- [ ] Core Trading Engine - Order Execution Logic
- [ ] Persistence Layer & Event Logging
- [ ] Basic Risk Management Module
- [ ] Security Hardening & Credential Management

### 🔌 Sprint 3: Exchange Integration & Plugin System
- [ ] Plugin System - Exchange Interface & Loader
- [ ] Exchange Plugins: Binance & Coinbase
- [ ] Plugin System - Technical Indicators Interface & Loader
- [ ] Indicator Plugins: RSI, MACD, EMA

### 🎯 Sprint 4: Trading Strategies & Orchestration
- [ ] Plugin System - Strategy Interface & Loader
- [ ] Strategy Plugins: RSI Mean Reversion & MACD Crossover
- [ ] Strategy Orchestration & Execution Engine
- [ ] Snapshot & Price History Recording

### 🎨 Sprint 5: User Interface & Final Polish
- [ ] Structured Logging & Monitoring
- [ ] Basic CLI Implementation
- [ ] Unit, Integration, and E2E Test Suite
- [ ] Documentation & Developer Onboarding

## 🛠️ Tecnologias Utilizadas

### Core
- **Python 3.12+**: Linguagem principal
- **SQLAlchemy 2.x**: ORM para banco de dados
- **Alembic**: Database migrations
- **Pydantic 2.x**: Validação de dados
- **CCXT 4.x**: Integração multi-exchange

### Data & Analysis
- **pandas**: Manipulação de dados
- **numpy**: Computação numérica
- **pandas-ta**: Indicadores técnicos

### Async & Concurrency
- **asyncio**: Framework assíncrono
- **aiohttp**: Cliente HTTP assíncrono
- **asyncpg**: Driver PostgreSQL assíncrono

### Testing
- **pytest**: Framework de testes
- **pytest-asyncio**: Testes assíncronos
- **pytest-cov**: Cobertura de testes

### Code Quality
- **black**: Formatação de código
- **flake8**: Linter
- **mypy**: Verificação de tipos
- **bandit**: Linter de segurança

## 📊 Configuração

### Exemplo de configuração (config.yaml)

```yaml
environment: production

database:
  host: ${DB_HOST}
  port: 5432
  name: crypto_bot
  user: ${DB_USER}
  password: ${DB_PASSWORD}

exchanges:
  binance:
    enabled: true
    testnet: false
    api_key: ${BINANCE_API_KEY}
    api_secret: ${BINANCE_API_SECRET}
    rate_limit: 1200

trading:
  dry_run: false
  max_concurrent_trades: 5
  default_order_type: limit

risk_management:
  max_position_size_pct: 10.0
  max_portfolio_risk_pct: 30.0
  default_stop_loss_pct: 2.0
  default_take_profit_pct: 5.0
  trailing_stop: true
  max_drawdown_pct: 15.0

strategies:
  - name: rsi_mean_reversion
    enabled: true
    pairs: [BTC/USDT, ETH/USDT]
    timeframe: 1h
    parameters:
      rsi_period: 14
      rsi_oversold: 30
      rsi_overbought: 70
```

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=src --cov-report=html

# Executar testes específicos
pytest tests/unit/
pytest tests/integration/
```

## 📝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 🔒 Segurança

- **Nunca** hardcode credenciais no código
- Use variáveis de ambiente para dados sensíveis
- API keys são criptografadas no banco de dados
- Nunca habilite saque (withdrawal) nas API keys
- Use IP whitelist quando possível

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## ⚠️ Disclaimer

**ATENÇÃO**: Este software é fornecido apenas para fins educacionais e de pesquisa. Trading de criptomoedas envolve riscos significativos e pode resultar em perdas financeiras. Use por sua própria conta e risco.

## 📞 Suporte

- 📧 Email: gomes.lmc@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/guipalm4/crypto-bot/issues)
- 📚 Documentação: [Wiki](https://github.com/guipalm4/crypto-bot/wiki)

## 🙏 Agradecimentos

- [CCXT](https://github.com/ccxt/ccxt) - Biblioteca de integração multi-exchange
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM para Python
- [Pydantic](https://pydantic.dev/) - Validação de dados
- [pandas-ta](https://github.com/twopirllc/pandas-ta) - Indicadores técnicos

---

**Desenvolvido com ❤️ por [Guilherme Palma](https://github.com/guipalm4)**