# =============================================================================
# CRYPTO TRADING BOT - Makefile
# =============================================================================
.PHONY: help install dev-install up down restart logs ps shell db-shell
.PHONY: test test-unit test-integration test-e2e test-cov test-watch
.PHONY: lint format type-check security-check quality-check
.PHONY: migrate migrate-up migrate-down migrate-head migrate-revision
.PHONY: clean clean-py clean-docker clean-data clean-all
.PHONY: venv activate run check-all

# =============================================================================
# Variáveis
# =============================================================================
PYTHON := python3
PIP := pip
VENV := .venv
PYTEST := pytest
RUFF := ruff
BLACK := black
MYPY := mypy
BANDIT := bandit
ALEMBIC := alembic

# Nome do container do PostgreSQL
POSTGRES_CONTAINER := crypto-bot-postgres

# Diretórios
SRC_DIR := src
TESTS_DIR := tests

# =============================================================================
# Ajuda
# =============================================================================
help:  ## Mostra esta mensagem de ajuda
	@echo "========================================================================"
	@echo "CRYPTO TRADING BOT - Makefile"
	@echo "========================================================================"
	@echo ""
	@echo "Principais comandos:"
	@echo ""
	@echo "  Ambiente:"
	@echo "    make install          - Instala dependências do projeto"
	@echo "    make dev-install      - Instala dependências de desenvolvimento"
	@echo "    make venv             - Cria ambiente virtual"
	@echo ""
	@echo "  Docker:"
	@echo "    make up               - Sobe os serviços (PostgreSQL + Redis)"
	@echo "    make down             - Para os serviços"
	@echo "    make restart          - Reinicia os serviços"
	@echo "    make logs             - Mostra logs dos containers"
	@echo "    make ps               - Lista containers em execução"
	@echo "    make shell            - Abre shell no container"
	@echo "    make up-test          - Sobe apenas postgres de testes"
	@echo "    make down-test        - Para apenas postgres de testes"
	@echo ""
	@echo "  Testes:"
	@echo "    make test             - Executa todos os testes"
	@echo "    make test-unit        - Executa apenas testes unitários"
	@echo "    make test-integration - Executa apenas testes de integração"
	@echo "    make test-cov         - Testes com cobertura de código"
	@echo ""
	@echo "  Qualidade de Código:"
	@echo "    make format           - Formata código com Ruff"
	@echo "    make lint             - Verifica código com Ruff"
	@echo "    make type-check       - Verifica tipos com MyPy"
	@echo "    make security-check   - Verifica segurança com Bandit"
	@echo "    make quality-check    - Executa todos os checks de qualidade"
	@echo ""
	@echo "  Banco de Dados:"
	@echo "    make migrate-up       - Aplica migrações do Alembic"
	@echo "    make migrate-head     - Aplica todas as migrações pendentes"
	@echo "    make migrate-revision - Cria nova migração"
	@echo ""
	@echo "  Limpeza:"
	@echo "    make clean            - Remove arquivos temporários"
	@echo "    make clean-docker    - Remove containers e volumes"
	@echo "    make clean-all       - Limpa tudo"
	@echo ""
	@echo "========================================================================"

# =============================================================================
# Ambiente Virtual
# =============================================================================
venv:  ## Cria ambiente virtual Python
	@echo "📦 Criando ambiente virtual..."
	$(PYTHON) -m venv $(VENV)
	@echo "✅ Ambiente virtual criado em $(VENV)"

install:  ## Instala dependências do projeto
	@echo "📦 Instalando dependências do projeto..."
	$(PIP) install -r requirements.txt
	@echo "✅ Dependências instaladas"

dev-install:  ## Instala dependências de desenvolvimento
	@echo "📦 Instalando dependências de desenvolvimento..."
	$(PIP) install -r requirements-dev.txt
	@echo "✅ Dependências de desenvolvimento instaladas"

activate:  ## Ativa o ambiente virtual (informação apenas)
	@echo "Para ativar o ambiente virtual, execute:"
	@echo "  source .venv/bin/activate  # Linux/Mac"
	@echo "  .venv\\Scripts\\activate   # Windows"

# =============================================================================
# Docker Compose
# =============================================================================
up:  ## Sobe os serviços (PostgreSQL + Redis)
	@echo "🐳 Subindo serviços..."
	docker-compose up -d
	@echo "✅ Serviços iniciados"
	@echo "PostgreSQL: localhost:5432"
	@echo "Redis: localhost:6379"

down:  ## Para os serviços
	@echo "🐳 Parando serviços..."
	docker-compose down
	@echo "✅ Serviços parados"

restart:  ## Reinicia os serviços
	@echo "🔄 Reiniciando serviços..."
	docker-compose restart
	@echo "✅ Serviços reiniciados"

logs:  ## Mostra logs dos containers
	docker-compose logs -f

ps:  ## Lista containers em execução
	docker-compose ps

shell:  ## Abre shell no container
	docker-compose exec postgres psql -U crypto_bot_user -d crypto_bot

db-shell: shell  ## Alias para shell

up-test:  ## Sobe apenas o postgres de testes
	@echo "🐳 Subindo postgres-test..."
	docker-compose up -d postgres-test
	@echo "⏳ Aguardando banco estar pronto..."
	@sleep 3
	@echo "✅ postgres-test pronto na porta 5433"

down-test:  ## Para apenas o postgres de testes
	@echo "🐳 Parando postgres-test..."
	docker-compose stop postgres-test
	docker-compose rm -f postgres-test
	@echo "✅ postgres-test parado"

# =============================================================================
# Testes
# =============================================================================
test:  ## Executa todos os testes
	@echo "🧪 Executando testes..."
	$(PYTEST) $(TESTS_DIR)
	@echo "✅ Testes concluídos"

test-unit:  ## Executa apenas testes unitários
	@echo "🧪 Executando testes unitários..."
	$(PYTEST) $(TESTS_DIR)/unit
	@echo "✅ Testes unitários concluídos"

test-integration:  ## Executa apenas testes de integração
	@echo "🧪 Executando testes de integração..."
	@echo "🔧 Verificando se postgres-test está rodando..."
	@docker-compose ps postgres-test | grep -q "Up" || docker-compose up -d postgres-test
	@echo "⏳ Aguardando banco estar pronto..."
	@sleep 3
	@echo "🔧 Configurando DATABASE_URL para testes..."
	@export DATABASE_URL="postgresql+asyncpg://test_user:test_password@localhost:5433/crypto_bot_test" && \
	export ENCRYPTION_KEY="test_encryption_key_32_bytes_long!!" && \
	$(PYTEST) $(TESTS_DIR)/integration
	@echo "✅ Testes de integração concluídos"

test-e2e:  ## Executa apenas testes end-to-end
	@echo "🧪 Executando testes E2E..."
	$(PYTEST) $(TESTS_DIR)/e2e
	@echo "✅ Testes E2E concluídos"

test-cov:  ## Testes com cobertura de código
	@echo "🧪 Executando testes com cobertura..."
	$(PYTEST) $(TESTS_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term
	@echo "✅ Relatório de cobertura em htmlcov/index.html"

test-watch:  ## Executa testes em modo watch
	@echo "🧪 Modo watch ativado..."
	$(PYTEST) --watch $(TESTS_DIR)

test-fast:  ## Executa testes mais rapidamente (com paralelização)
	@echo "🧪 Executando testes rápidos..."
	$(PYTEST) -n auto $(TESTS_DIR)
	@echo "✅ Testes concluídos"

# =============================================================================
# Qualidade de Código
# =============================================================================
format:  ## Formata código com Black
	@echo "🎨 Formatando código com Black..."
	$(BLACK) $(SRC_DIR) $(TESTS_DIR)
	@echo "✅ Código formatado"

format-check:  ## Verifica formatação com Black sem alterar arquivos
	@echo "🎨 Verificando formatação com Black..."
	$(BLACK) --check $(SRC_DIR) $(TESTS_DIR)

lint:  ## Verifica código com Ruff
	@echo "🔍 Verificando código com Ruff..."
	$(RUFF) check $(SRC_DIR) $(TESTS_DIR)
	@echo "✅ Verificação concluída"

lint-fix:  ## Corrige problemas automáticos do Ruff
	@echo "🔧 Corrigindo problemas automáticos..."
	$(RUFF) check --fix $(SRC_DIR) $(TESTS_DIR)
	@echo "✅ Correções aplicadas"

type-check:  ## Verifica tipos com MyPy
	@echo "🔍 Verificando tipos com MyPy..."
	$(MYPY) $(SRC_DIR)
	@echo "✅ Verificação de tipos concluída"

security-check:  ## Verifica segurança com Bandit
	@echo "🔒 Verificando segurança com Bandit..."
	$(BANDIT) -r $(SRC_DIR) -f json -o bandit-report.json || true
	$(BANDIT) -r $(SRC_DIR)
	@echo "✅ Verificação de segurança concluída"

quality-check: format-check lint type-check  ## Executa todos os checks de qualidade
	@echo "✅ Todos os checks de qualidade passaram!"

# =============================================================================
# Banco de Dados - Alembic
# =============================================================================
migrate: migrate-up  ## Alias para migrate-up

migrate-up:  ## Aplica migrações do Alembic (próxima)
	@echo "📊 Aplicando migração..."
	$(ALEMBIC) upgrade +1
	@echo "✅ Migração aplicada"

migrate-down:  ## Reverte migração anterior
	@echo "📊 Revertendo migração..."
	$(ALEMBIC) downgrade -1
	@echo "✅ Migração revertida"

migrate-head:  ## Aplica todas as migrações pendentes
	@echo "📊 Aplicando todas as migrações..."
	$(ALEMBIC) upgrade head
	@echo "✅ Todas as migrações aplicadas"

migrate-revision:  ## Cria nova migração (use: make migrate-revision MESSAGE="mensagem")
	@echo "📊 Criando nova migração..."
	@if [ -z "$(MESSAGE)" ]; then \
		$(ALEMBIC) revision --autogenerate; \
	else \
		$(ALEMBIC) revision --autogenerate -m "$(MESSAGE)"; \
	fi
	@echo "✅ Migração criada"

migrate-history:  ## Mostra histórico de migrações
	@echo "📊 Histórico de migrações:"
	$(ALEMBIC) history

migrate-current:  ## Mostra migração atual
	@echo "📊 Migração atual:"
	$(ALEMBIC) current

# =============================================================================
# Execução
# =============================================================================
run:  ## Executa o bot
	@echo "🚀 Executando bot..."
	python -m src.crypto_bot.cli.main

run-dry:  ## Executa o bot em modo dry-run
	@echo "🚀 Executando bot em modo dry-run..."
	python -m src.crypto_bot.cli.main --dry-run

check-all: quality-check test-unit  ## Executa todos os checks e testes unitários
	@echo "✅ Todos os checks e testes passaram!"

# =============================================================================
# Limpeza
# =============================================================================
clean:  ## Remove arquivos temporários
	@echo "🧹 Limpando arquivos temporários..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -delete 2>/dev/null || true
	rm -f bandit-report.json 2>/dev/null || true
	@echo "✅ Limpeza concluída"

clean-py: clean  ## Remove arquivos Python temporários (alias)

clean-docker:  ## Remove containers e volumes do Docker
	@echo "🧹 Removendo containers e volumes..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ Limpeza Docker concluída"

clean-data:  ## Remove dados persistentes (CUIDADO!)
	@echo "⚠️  Removendo dados persistentes..."
	docker volume rm crypto-bot-postgres-data crypto-bot-redis-data 2>/dev/null || true
	@echo "✅ Dados removidos"

clean-all: clean clean-docker  ## Limpa tudo (arquivos + Docker)
	@echo "🧹 Limpeza completa concluída"

# =============================================================================
# Setup Completo
# =============================================================================
setup: venv install dev-install up migrate-head  ## Setup completo do projeto
	@echo ""
	@echo "✅ Setup completo!"
	@echo ""
	@echo "Próximos passos:"
	@echo "1. Copie .env.example para .env"
	@echo "2. Configure suas credenciais no .env"
	@echo "3. Execute: make run"
	@echo ""
	@echo "Para ativar o ambiente virtual:"
	@echo "  source .venv/bin/activate"
	@echo ""

# =============================================================================
# Desenvolvimento
# =============================================================================
dev-setup: setup  ## Setup para desenvolvimento (alias)

dev-start: up  ## Inicia ambiente de desenvolvimento
	@echo "✅ Ambiente de desenvolvimento pronto!"

watch:  ## Executa testes em modo watch
	make test-watch

# =============================================================================
# Relatórios
# =============================================================================
report-cov: test-cov  ## Gera relatório de cobertura
	@echo "📊 Relatório de cobertura em: htmlcov/index.html"

report-lint: lint  ## Gera relatório de linting
	@echo "📊 Relatório de linting concluído"

# =============================================================================
# Comandos Especiais
# =============================================================================
fix: format lint-fix  ## Formata e corrige problemas automáticos
	@echo "✅ Correções aplicadas"

pre-commit: format lint type-check test  ## Executa checks pré-commit
	@echo "✅ Checks pré-commit passaram!"

ci: clean quality-check test-unit  ## Executa pipeline CI local
	@echo "✅ Pipeline CI local concluído!"

.DEFAULT_GOAL := help

