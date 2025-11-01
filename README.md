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

   # Instale as dependências e o pacote em modo de desenvolvimento
   pip install -r requirements.txt
   pip install -e .  # Instala o pacote e disponibiliza o comando 'crypto-bot'
   
   # Para desenvolvimento, instale também as dependências de desenvolvimento (opcional)
   # pip install -r requirements-dev.txt
   ```
   
   **Nota:** Se preferir não instalar o pacote, você pode usar `python -m crypto_bot.cli.main` em vez de `crypto-bot`.

3. **Configure o banco de dados**
   ```bash
   # Inicie o PostgreSQL com Docker
   docker-compose up -d postgres

   # Execute as migrações
   alembic upgrade head
   ```

4. **Configure as variáveis de ambiente**
   ```bash
   # Copie o arquivo de exemplo
   cp .env.example .env

   # Edite o arquivo .env com suas credenciais
   # Mínimo necessário:
   # - ENCRYPTION_KEY (gere com: openssl rand -hex 32)
   # - DATABASE_USER e DATABASE_PASSWORD (ou use valores padrão do docker-compose)
   nano .env
   ```
   
   **Variáveis mínimas:** `ENCRYPTION_KEY` é obrigatória. Veja `docs/ONBOARDING_GUIDE.md` para lista completa.

5. **Execute o bot**
   ```bash
   # Modo dry-run (simulação)
   crypto-bot start --dry-run

   # Modo produção
   crypto-bot start

   # Ver status do bot
   crypto-bot status

   # Ver todas as opções
   crypto-bot --help
   ```

## 📚 Uso da CLI

O bot fornece uma interface de linha de comando completa para gerenciar e monitorar operações:

```bash
# Iniciar bot em modo simulação
crypto-bot start --dry-run

# Iniciar bot em modo produção
crypto-bot start

# Parar bot
crypto-bot stop

# Reiniciar bot
crypto-bot restart --dry-run

# Ver status do bot
crypto-bot status

# Listar estratégias configuradas
crypto-bot strategies

# Listar posições abertas
crypto-bot positions

# Ver saldos
crypto-bot balances --exchange binance

# Forçar execução de uma estratégia específica
crypto-bot force <strategy_id>

# Ver logs do bot
crypto-bot logs --follow
crypto-bot logs --lines 50

# Versão
crypto-bot version
```

Para mais informações sobre cada comando, use `crypto-bot <comando> --help`.

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

### 🏗️ Sprint 1: Foundation & Core Infrastructure ✅
- [x] Project Structure & Environment Setup
- [x] Database Schema Design & Migration Setup
- [x] Configuration System Implementation
- [x] Code Quality & Compliance Automation

### 🚀 Sprint 2: Core Trading Engine & Risk Management ✅
- [x] Core Trading Engine - Order Execution Logic
- [x] Persistence Layer & Event Logging
- [x] Basic Risk Management Module
- [x] Security Hardening & Credential Management

### 🔌 Sprint 3: Exchange Integration & Plugin System ✅
- [x] Plugin System - Exchange Interface & Loader
- [x] Exchange Plugins: Binance & Coinbase
- [x] Plugin System - Technical Indicators Interface & Loader
- [x] Indicator Plugins: RSI, MACD, EMA

### 🎯 Sprint 4: Trading Strategies & Orchestration ✅
- [x] Plugin System - Strategy Interface & Loader
- [x] Strategy Plugins: RSI Mean Reversion & MACD Crossover
- [x] Strategy Orchestration & Execution Engine
- [x] Snapshot & Price History Recording

### 🎨 Sprint 5: User Interface & Final Polish ✅
- [x] Structured Logging & Monitoring
- [x] Basic CLI Implementation
- [x] Unit, Integration, and E2E Test Suite
- [x] Documentation & Developer Onboarding

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
- **ruff**: Linter (substitui Flake8/isort)
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

O projeto possui uma suite completa de testes com 400+ testes cobrindo unitários, integração e E2E.

### Executando Testes

```bash
# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=src/crypto_bot --cov-report=term-missing

# Executar testes específicos
pytest tests/unit/              # Testes unitários
pytest tests/integration/       # Testes de integração
pytest tests/e2e/               # Testes end-to-end

# Executar por marker
pytest -m unit                  # Apenas unitários
pytest -m integration           # Apenas integração
pytest -m e2e                   # Apenas E2E

# Executar com verbose
pytest -v

# Executar testes específicos por padrão
pytest tests/unit/test_trading_service.py
```

### Configuração de Testes

Para mais detalhes sobre configuração e execução de testes, consulte:
- [TESTING_SETUP.md](docs/TESTING_SETUP.md)

### Cobertura Atual

- **Cobertura geral**: 79%
- **405+ testes unitários**
- **Testes de integração** com testnets reais
- **14 testes E2E** para fluxos completos

## 📝 Contribuição

Agradecemos contribuições! Por favor, siga estas diretrizes:

### Pré-requisitos

- Python 3.12+
- PostgreSQL 16+ (ou Docker)
- Conhecimento básico de Git e GitHub

### Processo de Contribuição

1. **Fork o projeto**
   ```bash
   # Clone seu fork
   git clone https://github.com/seu-usuario/crypto-bot.git
   cd crypto-bot
   ```

2. **Configure o ambiente de desenvolvimento**
   ```bash
   # Crie e ative ambiente virtual
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   
   # Instale dependências de desenvolvimento
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   
   # Instale o pacote em modo de desenvolvimento
   pip install -e .  # Disponibiliza o comando 'crypto-bot'
   
   # Instale pre-commit hooks
   pre-commit install
   ```

3. **Crie uma branch para sua feature**
   ```bash
   git checkout -b feature/sua-feature-descritiva
   ```

4. **Desenvolva e teste sua mudança**
   ```bash
   # Execute os testes
   pytest
   
   # Verifique qualidade do código
   ruff check .
   black --check .
   mypy src/crypto_bot
   ```

5. **Commit suas mudanças**
   ```bash
   git add .
   git commit -m "feat(scope): descrição clara da mudança"
   ```
   
   **Formato de commit**: Use [Conventional Commits](https://www.conventionalcommits.org/)
   - `feat`: Nova feature
   - `fix`: Correção de bug
   - `docs`: Documentação
   - `test`: Testes
   - `refactor`: Refatoração
   - `chore`: Manutenção

6. **Push e abra um Pull Request**
   ```bash
   git push origin feature/sua-feature-descritiva
   ```
   
   Depois abra um PR no GitHub seguindo o template fornecido.

### Padrões de Código

- Siga os padrões definidos em [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md)
- Todos os testes devem passar
- Código deve ser formatado com Black
- Type hints são obrigatórios
- Docstrings seguindo Google style são esperados

### Workflow de Desenvolvimento

Para mais detalhes sobre o workflow, consulte:
- [WORKFLOW_QUICK_START.md](docs/WORKFLOW_QUICK_START.md)
- [WORKFLOW_ENFORCEMENT.md](docs/WORKFLOW_ENFORCEMENT.md)

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

## 📚 Documentação Adicional

A documentação completa está disponível na pasta `docs/`:

- **[WORKFLOW_QUICK_START.md](docs/WORKFLOW_QUICK_START.md)**: Guia rápido de workflow de desenvolvimento
- **[CODING_STANDARDS.md](docs/CODING_STANDARDS.md)**: Padrões de código e qualidade
- **[TESTING_SETUP.md](docs/TESTING_SETUP.md)**: Guia completo de testes
- **[SECURITY_BASELINE.md](docs/security/SECURITY_BASELINE.md)**: Baseline de segurança
- **[HARDENING_GUIDE.md](docs/security/HARDENING_GUIDE.md)**: Guia de hardening
- **[strategy_plugins.md](docs/architecture/strategy_plugins.md)**: Arquitetura de plugins de estratégias

## 📞 Suporte

- 📧 Email: gomes.lmc@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/guipalm4/crypto-bot/issues)
- 📚 Documentação: Veja a pasta `docs/` no repositório

## 🙏 Agradecimentos

- [CCXT](https://github.com/ccxt/ccxt) - Biblioteca de integração multi-exchange
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM para Python
- [Pydantic](https://pydantic.dev/) - Validação de dados
- [pandas-ta](https://github.com/twopirllc/pandas-ta) - Indicadores técnicos

---

**Desenvolvido com ❤️ por [Guilherme Palma](https://github.com/guipalm4)**