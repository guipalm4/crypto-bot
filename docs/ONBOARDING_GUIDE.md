# 🚀 Guia de Onboarding para Desenvolvedores

Este guia foi criado para facilitar o onboarding de novos desenvolvedores ao projeto Crypto Trading Bot, permitindo que eles comecem a contribuir rapidamente.

## 📋 Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Setup Inicial](#setup-inicial)
3. [Estrutura do Projeto](#estrutura-do-projeto)
4. [Primeira Contribuição](#primeira-contribuição)
5. [Workflow de Desenvolvimento](#workflow-de-desenvolvimento)
6. [Testando Mudanças](#testando-mudanças)
7. [Criando Pull Request](#criando-pull-request)
8. [Recursos de Aprendizado](#recursos-de-aprendizado)

## ✅ Pré-requisitos

Antes de começar, certifique-se de ter:

- **Python 3.12+** instalado
- **Git** instalado e configurado
- **Docker** e **Docker Compose** (para banco de dados)
- **Editor de código** (VS Code, PyCharm, etc.)
- **Conta no GitHub** (para forks e PRs)
- Conhecimento básico de:
  - Python (async/await, type hints)
  - Git e GitHub
  - SQL básico (PostgreSQL)

## 🛠️ Setup Inicial

### 1. Fork e Clone

```bash
# Fork o repositório no GitHub, depois clone seu fork
git clone https://github.com/seu-usuario/crypto-bot.git
cd crypto-bot

# Adicione o repositório original como upstream
git remote add upstream https://github.com/guipalm4/crypto-bot.git
```

### 2. Ambiente Virtual

```bash
# Crie e ative ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instale dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dependências de desenvolvimento
```

### 3. Configuração do Banco de Dados

```bash
# Inicie PostgreSQL com Docker
docker-compose up -d postgres

# Aguarde o banco estar pronto
sleep 5

# Execute migrações
alembic upgrade head
```

### 4. Variáveis de Ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite com suas configurações (pelo menos ENCRYPTION_KEY)
nano .env  # ou use seu editor preferido
```

**Mínimo necessário para desenvolvimento:**
```bash
ENCRYPTION_KEY=your_32_byte_key_here_minimum_required
ENVIRONMENT=development
DATABASE_USER=crypto_bot_user
DATABASE_PASSWORD=crypto_bot_password
```

### 5. Pre-commit Hooks

```bash
# Instale pre-commit hooks
pre-commit install

# Teste os hooks
pre-commit run --all-files
```

### 6. Verificação

```bash
# Execute testes para verificar que tudo está funcionando
pytest tests/unit/ -v

# Verifique qualidade do código
ruff check .
black --check .
mypy src/crypto_bot
```

## 📁 Estrutura do Projeto

Entender a estrutura do projeto ajuda muito:

```
crypto-bot/
├── src/crypto_bot/
│   ├── domain/              # Regras de negócio (DDD)
│   │   ├── entities/        # Entidades de domínio
│   │   ├── value_objects/   # Value objects
│   │   └── events/          # Domain events
│   ├── application/         # Use cases
│   │   ├── services/        # Serviços de aplicação
│   │   ├── dtos/            # Data Transfer Objects
│   │   └── interfaces/      # Interfaces (contratos)
│   ├── infrastructure/      # Implementações técnicas
│   │   ├── database/        # SQLAlchemy models
│   │   ├── exchanges/       # Exchange adapters
│   │   └── security/        # Criptografia
│   ├── plugins/             # Sistema de plugins
│   │   ├── exchanges/       # Exchange plugins
│   │   ├── indicators/      # Indicator plugins
│   │   └── strategies/      # Strategy plugins
│   ├── config/              # Configurações
│   └── cli/                 # Interface de linha de comando
├── tests/                   # Testes
│   ├── unit/                # Testes unitários
│   ├── integration/         # Testes de integração
│   └── e2e/                 # Testes end-to-end
├── docs/                    # Documentação
├── config/                  # Arquivos de configuração YAML
└── alembic/                 # Database migrations
```

**Princípios da Arquitetura:**
- **Domain-Driven Design (DDD)**: Separação clara entre domínio, aplicação e infraestrutura
- **Dependency Injection**: Baixo acoplamento entre componentes
- **Plugin System**: Extensibilidade via plugins
- **Type Safety**: Type hints obrigatórios em todo código

## 🎯 Primeira Contribuição

### Escolhendo uma Task

1. **Verifique tasks disponíveis:**
   ```bash
   task-master list  # ou use MCP tool: get_tasks
   ```

2. **Escolha uma task apropriada para iniciantes:**
   - Tasks marcadas como "good first issue"
   - Tasks de documentação
   - Tasks de testes
   - Correções de bugs pequenas

3. **Pegue a próxima task:**
   ```bash
   task-master next  # Mostra próxima task recomendada
   ```

### Criando uma Branch

```bash
# Sempre crie uma branch para seu trabalho
git checkout main
git pull upstream main
git checkout -b feature/task-X-short-description

# Ou use o script de workflow
./scripts/workflow.sh start
```

### Desenvolvendo

1. **Leia a documentação relevante:**
   - [CODING_STANDARDS.md](CODING_STANDARDS.md) - Padrões de código
   - [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) - Configuração
   - [PLUGIN_DEVELOPMENT_GUIDE.md](PLUGIN_DEVELOPMENT_GUIDE.md) - Desenvolvimento de plugins

2. **Desenvolva seguindo os padrões:**
   - Type hints obrigatórios
   - Docstrings Google-style
   - Código formatado com Black
   - Sem erros de linting

3. **Escreva testes:**
   - Testes unitários para nova lógica
   - Testes de integração se necessário
   - Mantenha cobertura >80%

## 🔄 Workflow de Desenvolvimento

### Workflow Completo

```bash
# 1. Iniciar nova task
./scripts/workflow.sh start
# ou manualmente:
git checkout -b feature/task-X-description

# 2. Desenvolver
# ... fazer mudanças ...

# 3. Verificar qualidade
ruff check .
black .
mypy src/crypto_bot
pytest

# 4. Commit
git add .
git commit -m "feat(scope): descrição clara"

# 5. Push
git push origin feature/task-X-description

# 6. Criar PR
./scripts/workflow.sh finish
# ou manualmente:
gh pr create --fill
```

### Convenções de Commit

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
feat(cli): adiciona comando de logs
fix(database): corrige timeout de conexão
docs(readme): atualiza instruções de instalação
test(services): adiciona testes para TradingService
refactor(plugins): simplifica registro de plugins
chore(deps): atualiza dependências
```

**Tipos:**
- `feat`: Nova feature
- `fix`: Correção de bug
- `docs`: Documentação
- `test`: Testes
- `refactor`: Refatoração
- `chore`: Manutenção

## 🧪 Testando Mudanças

### Executando Testes

```bash
# Todos os testes
pytest

# Apenas unitários
pytest tests/unit/

# Apenas integração
pytest tests/integration/

# Teste específico
pytest tests/unit/test_trading_service.py

# Com cobertura
pytest --cov=src/crypto_bot --cov-report=term-missing

# Com verbose
pytest -v

# Apenas testes que falharam
pytest --lf
```

### Linting e Formatação

```bash
# Verificar linting
ruff check .

# Corrigir automaticamente
ruff check --fix .

# Verificar formatação
black --check .

# Formatar
black .

# Type checking
mypy src/crypto_bot

# Segurança
bandit -r src/crypto_bot
```

### Pre-commit Hooks

Os hooks são executados automaticamente antes de cada commit:

- Ruff (linting)
- Black (formatação)
- MyPy (type checking)
- Pytest (testes unitários no pre-push)
- Bandit (segurança)

## 📝 Criando Pull Request

### Checklist Antes do PR

- [ ] Código segue padrões do projeto
- [ ] Todos os testes passam
- [ ] Cobertura de testes mantida ou melhorada
- [ ] Sem erros de linting/type checking
- [ ] Código formatado com Black
- [ ] Docstrings adicionados/atualizados
- [ ] README ou documentação atualizada se necessário
- [ ] Commits seguem convenção (Conventional Commits)
- [ ] Branch atualizada com `main` antes do PR

### Criando o PR

1. **Atualize sua branch:**
   ```bash
   git checkout main
   git pull upstream main
   git checkout feature/task-X-description
   git rebase main  # ou git merge main
   ```

2. **Push sua branch:**
   ```bash
   git push origin feature/task-X-description
   ```

3. **Crie o PR:**
   - Use o template do GitHub
   - Preencha todas as seções
   - Referencie a task relacionada
   - Adicione screenshots se aplicável
   - Complete todos os checklists

### Template de PR

O template está em `.github/pull_request_template.md`. Inclua:

- Descrição clara das mudanças
- Tipo de mudança (feat, fix, docs, etc.)
- Como testar
- Checklist completo
- Relação com tasks/issues

## 📚 Recursos de Aprendizado

### Documentação do Projeto

- **[README.md](../README.md)** - Visão geral e quick start
- **[CODING_STANDARDS.md](CODING_STANDARDS.md)** - Padrões de código
- **[CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)** - Configuração completa
- **[PLUGIN_DEVELOPMENT_GUIDE.md](PLUGIN_DEVELOPMENT_GUIDE.md)** - Desenvolvimento de plugins
- **[SECURITY_PRACTICES.md](SECURITY_PRACTICES.md)** - Práticas de segurança
- **[TESTING_SETUP.md](TESTING_SETUP.md)** - Setup e execução de testes
- **[WORKFLOW_QUICK_START.md](WORKFLOW_QUICK_START.md)** - Workflow Git

### Recursos Externos

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/en/20/)
- [Pydantic 2.0 Docs](https://docs.pydantic.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
- [CCXT Documentation](https://docs.ccxt.com/)
- [Async/Await in Python](https://docs.python.org/3/library/asyncio.html)

### Exemplos no Código

Estude os plugins existentes como referência:

- **Exchange Plugin**: `src/crypto_bot/plugins/exchanges/binance_plugin.py`
- **Indicator Plugin**: `src/crypto_bot/plugins/indicators/pandas_ta_indicators.py`
- **Strategy Plugin**: `src/crypto_bot/plugins/strategies/rsi_mean_reversion.py`

## 🤝 Obtendo Ajuda

### Quando Está Travado

1. **Revise a documentação** relevante
2. **Procure por issues similares** no GitHub
3. **Verifique exemplos** no código existente
4. **Consulte os logs** de erro detalhados
5. **Abra uma issue** no GitHub com:
   - Descrição clara do problema
   - Passos para reproduzir
   - Logs de erro
   - Ambiente (OS, Python version)

### Comunicação

- **Issues**: Use GitHub Issues para bugs e features
- **Discussions**: Use GitHub Discussions para perguntas
- **Email**: gomes.lmc@gmail.com (para questões privadas)

## ✅ Teste de Onboarding

Este guia foi projetado para permitir que novos desenvolvedores:

1. ✅ Configurem o ambiente completamente
2. ✅ Executem o projeto localmente
3. ✅ Entendam a arquitetura
4. ✅ Façam sua primeira contribuição
5. ✅ Criem um PR seguindo os padrões

**Teste você mesmo:**
- Siga este guia do zero
- Anote qualquer problema encontrado
- Sugira melhorias via issue ou PR

## 🔄 Feedback e Melhorias

Este guia é um documento vivo. Contribua melhorias:

1. **Identifique problemas** durante seu onboarding
2. **Documente soluções** encontradas
3. **Sugira melhorias** via issue ou PR
4. **Atualize o guia** conforme necessário

---

**💡 Dica**: Não tenha medo de perguntar ou pedir ajuda. A comunidade é amigável e está aqui para ajudar!