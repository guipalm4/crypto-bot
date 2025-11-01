# 🚀 Guia de Onboarding para Desenvolvedores

Este guia fornece um caminho completo para novos desenvolvedores começarem a contribuir no Crypto Trading Bot.

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter:

- ✅ Python 3.12+ instalado
- ✅ Git instalado e configurado
- ✅ Conta GitHub (para contribuições)
- ✅ Editor de código (VS Code, PyCharm, etc.)
- ✅ Conhecimento básico de Python async/await
- ✅ Conhecimento básico de Git

## 🎯 Objetivo do Onboarding

Ao final deste guia, você deve ser capaz de:

1. ✅ Configurar ambiente de desenvolvimento
2. ✅ Executar o projeto localmente
3. ✅ Executar testes e verificar qualidade
4. ✅ Entender a arquitetura do projeto
5. ✅ Contribuir com código seguindo padrões
6. ✅ Criar Pull Requests corretamente

## 📚 Documentação Essencial

Antes de começar a codificar, leia:

1. **[README.md](../README.md)** - Visão geral e quick start
2. **[WORKFLOW_QUICK_START.md](WORKFLOW_QUICK_START.md)** - Workflow de desenvolvimento
3. **[CODING_STANDARDS.md](CODING_STANDARDS.md)** - Padrões de código
4. **[CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)** - Configuração completa

## 🔧 Setup Inicial

### 1. Clone e Configure

```bash
# Clone o repositório
git clone https://github.com/guipalm4/crypto-bot.git
cd crypto-bot

# Crie e ative ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Se existir

# Instale pre-commit hooks
pre-commit install
```

### 2. Configure Banco de Dados

```bash
# Inicie PostgreSQL com Docker
docker-compose up -d postgres

# Execute migrações
alembic upgrade head

# (Opcional) Inicie banco de testes
docker-compose up -d postgres-test
```

### 3. Configure Variáveis de Ambiente

```bash
# Copie arquivo de exemplo
cp .env.example .env

# Edite .env com suas configurações
# Para desenvolvimento, você pode usar valores padrão ou testnet
nano .env
```

**Mínimo necessário para desenvolvimento:**

```bash
ENCRYPTION_KEY=your_32_byte_key_here_minimum_required
DATABASE_PASSWORD=crypto_bot_password
BINANCE_TESTNET_API_KEY=your_testnet_key  # Opcional
BINANCE_TESTNET_API_SECRET=your_testnet_secret  # Opcional
ENVIRONMENT=development
```

### 4. Verifique Instalação

```bash
# Execute testes
pytest tests/unit/ -v

# Verifique qualidade do código
ruff check src/crypto_bot
black --check src/crypto_bot
mypy src/crypto_bot

# Teste CLI
crypto-bot --help
crypto-bot version
```

## 📖 Entendendo a Arquitetura

### Estrutura de Diretórios

```
src/crypto_bot/
├── domain/              # Regras de negócio (DDD)
│   ├── entities/        # Entidades de domínio
│   ├── value_objects/   # Value objects
│   └── events/          # Domain events
├── application/         # Use cases e orquestração
│   ├── services/        # Serviços de aplicação
│   └── dtos/            # Data Transfer Objects
├── infrastructure/      # Implementações técnicas
│   ├── database/        # SQLAlchemy models
│   ├── exchanges/      # Exchange adapters
│   └── security/        # Criptografia
├── plugins/             # Sistema de plugins
│   ├── exchanges/       # Exchange plugins
│   ├── indicators/     # Indicadores técnicos
│   └── strategies/      # Estratégias de trading
└── cli/                 # Interface de linha de comando
```

### Fluxo de Dados

```
Strategy Plugin → Strategy Orchestrator → Trading Service → Exchange Plugin → API Externa
                                    ↓
                            Risk Service
                                    ↓
                            Database (Persistence)
```

### Componentes Principais

1. **StrategyOrchestrator**: Orquestra execução de estratégias
2. **TradingService**: Gerencia criação e cancelamento de ordens
3. **RiskService**: Aplica regras de gestão de risco
4. **Plugin Registry**: Descobre e carrega plugins
5. **Database Repositories**: Persistência de dados

## 🧪 Primeira Contribuição

### Escolha uma Issue Simples

Recomendações para primeira contribuição:

- 🔰 Issues marcadas com `good first issue`
- 🐛 Correções de bugs simples
- 📝 Melhorias de documentação
- 🧪 Adição de testes

### Processo Completo

```bash
# 1. Crie uma branch
git checkout -b feature/minha-primeira-contribuicao

# 2. Desenvolva a feature
# ... código aqui ...

# 3. Execute testes
pytest

# 4. Verifique qualidade
ruff check .
black --check .
mypy src/crypto_bot

# 5. Commit
git add .
git commit -m "feat(scope): minha primeira contribuição"

# 6. Push e crie PR
git push origin feature/minha-primeira-contribuicao
gh pr create --fill
```

## 🎓 Recursos de Aprendizado

### Documentação do Projeto

- [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) - Tudo sobre configuração
- [PLUGIN_DEVELOPMENT_GUIDE.md](PLUGIN_DEVELOPMENT_GUIDE.md) - Desenvolver plugins
- [SECURITY_PRACTICES.md](SECURITY_PRACTICES.md) - Práticas de segurança
- [TESTING_SETUP.md](TESTING_SETUP.md) - Setup e execução de testes

### Tecnologias Usadas

- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [Pydantic 2.0](https://docs.pydantic.dev/)
- [CCXT 4.x](https://docs.ccxt.com/)
- [pandas](https://pandas.pydata.org/)
- [asyncio](https://docs.python.org/3/library/asyncio.html)

### Arquitetura e Padrões

- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Plugin Pattern](https://refactoring.guru/design-patterns/strategy)

## ✅ Checklist de Onboarding

### Semana 1: Setup e Exploração

- [ ] Ambiente configurado e funcionando
- [ ] Todos os testes passando
- [ ] README.md lido completamente
- [ ] Estrutura de código explorada
- [ ] Primeiro comando CLI executado

### Semana 2: Entendimento

- [ ] Arquitetura entendida
- [ ] Fluxo de uma estratégia até execução de ordem compreendido
- [ ] Sistema de plugins entendido
- [ ] Configuração testada

### Semana 3: Primeira Contribuição

- [ ] Issue escolhida
- [ ] Branch criada
- [ ] Código desenvolvido
- [ ] Testes escritos
- [ ] PR criado e aprovado

## 🆘 Problemas Comuns

### "ModuleNotFoundError"

**Causa**: Ambiente virtual não ativado ou instalação incompleta.

**Solução:**
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### "Database connection failed"

**Causa**: PostgreSQL não iniciado ou credenciais incorretas.

**Solução:**
```bash
docker-compose up -d postgres
# Verifique DATABASE_URL no .env
```

### "ENCRYPTION_KEY required"

**Causa**: Variável de ambiente não configurada.

**Solução:**
```bash
echo "ENCRYPTION_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env
```

### "Tests failing"

**Causa**: Banco de testes não iniciado ou configuração incorreta.

**Solução:**
```bash
docker-compose up -d postgres-test
# Verifique ENCRYPTION_KEY configurado
```

## 📞 Suporte

Se encontrar problemas durante onboarding:

1. **Verifique a documentação** primeiro
2. **Procure em Issues** por problemas similares
3. **Crie uma Issue** descrevendo o problema
4. **Pergunte no Discord/Slack** (se disponível)

## 🎉 Próximos Passos

Após completar onboarding:

1. ✅ Explore código de plugins existentes
2. ✅ Leia testes para entender comportamento esperado
3. ✅ Contribua com melhorias de documentação
4. ✅ Participe de code reviews
5. ✅ Sugira melhorias e novas features

## 📚 Referências Rápidas

### Comandos Essenciais

```bash
# Testes
pytest                          # Todos os testes
pytest tests/unit/              # Apenas unitários
pytest -v -k test_name         # Teste específico

# Qualidade
ruff check .                    # Linting
black .                         # Formatação
mypy src/crypto_bot            # Type checking

# CLI
crypto-bot --help               # Ajuda geral
crypto-bot start --dry-run      # Iniciar em simulação
crypto-bot status               # Status do bot

# Database
alembic upgrade head            # Aplicar migrações
alembic revision --autogenerate # Criar migração
```

### Workflow Git

```bash
# Criar branch de feature
git checkout -b feature/minha-feature

# Commit com mensagem padronizada
git commit -m "feat(scope): descrição"

# Push e criar PR
git push origin feature/minha-feature
gh pr create --fill
```

---

**💡 Dica**: Não tenha medo de perguntar! A comunidade está aqui para ajudar. Boa sorte com sua primeira contribuição! 🚀
