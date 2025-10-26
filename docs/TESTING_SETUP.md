# Testing Setup Guide

Este documento descreve a configuração e execução dos testes no Crypto Trading Bot.

## Estrutura de Testes

O projeto utiliza três níveis de testes:

- **Unit Tests**: Testes isolados sem dependências externas (`tests/unit/`)
- **Integration Tests**: Testes com banco de dados real (`tests/integration/`)
- **E2E Tests**: Testes end-to-end completos (`tests/e2e/`)

## Configuração de Ambiente

### Variáveis de Ambiente Necessárias

```bash
# Required for integration tests
ENCRYPTION_KEY="your_32_byte_encryption_key"
DATABASE_URL="postgresql+asyncpg://test_user:test_password@localhost:5433/crypto_bot_test"
```

### Banco de Dados para Testes

O projeto utiliza um container Docker PostgreSQL separado para testes:

**Configuração do Container:**
- Banco: `crypto_bot_test`
- Usuário: `test_user`
- Senha: `test_password`
- Porta: `5433` (para não conflitar com o banco principal na 5432)
- Storage: In-memory (tmpfs) para máxima velocidade

**Iniciar o Banco de Testes:**

```bash
# Iniciar apenas o postgres de teste
docker-compose up -d postgres-test

# Aguardar o banco estar pronto (healthcheck automático)
# Verificar logs se necessário
docker-compose logs -f postgres-test
```

**Parar o Banco de Testes:**

```bash
docker-compose stop postgres-test
docker-compose rm -f postgres-test
```

## Executando Testes

### Testes Unitários (Recomendado para Desenvolvimento Diário)

```bash
# Executar todos os testes unitários
pytest tests/unit/ -v

# Executar com coverage
pytest tests/unit/ --cov=src/crypto_bot --cov-report=term-missing

# Executar testes específicos
pytest tests/unit/application/test_trading_service.py -v
```

**Características:**
- ⚡ Rápidos (sem dependências de banco)
- 🔒 Não requerem PostgreSQL rodando
- ✅ Executados automaticamente no pre-push hook

### Testes de Integração

```bash
# Requer: Docker Compose com postgres-test rodando
pytest tests/integration/ -v

# Executar teste específico
pytest tests/integration/test_repositories.py -v

# Executar apenas testes de um marcador
pytest -m integration -v
```

**Características:**
- 🐘 Requer PostgreSQL rodando (via Docker)
- ⏱️ Mais lentos que unit tests
- 🎯 Testam interações reais com o banco
- ⚙️ Utilizam fixtures async do pytest-asyncio

### Todos os Testes

```bash
# Executar TODOS os testes (unit + integration + e2e)
pytest -v

# Com coverage completo
pytest --cov=src/crypto_bot --cov-report=term-missing
```

## Fixtures Async do Pytest-Asyncio

O projeto utiliza `@pytest_asyncio.fixture` para fixtures assíncronas:

```python
import pytest_asyncio

@pytest_asyncio.fixture
async def db_session():
    """Provide async database session."""
    async for session in get_db_session():
        yield session
        await session.rollback()
```

**Nota:** Esto é uma melhoria em relação às versões antigas do pytest-asyncio que geravam warnings de deprecation.

## Workflow Recomendado

### Durante Desenvolvimento

1. **Rápido Iterativo (Unit Tests):**
   ```bash
   pytest tests/unit/ -v
   ```

2. **Antes de Commit:**
   ```bash
   # Pre-push hook executa unit tests automaticamente
   git push
   ```

3. **Antes de PR:**
   ```bash
   # Garantir que todos os testes passam
   docker-compose up -d postgres-test
   pytest -v
   ```

### No CI/CD Pipeline

O pipeline deve:
1. Executar unit tests sempre
2. Executar integration tests com postgres-test container
3. Gerar relatório de coverage
4. Validar que coverage >= threshold configurado

## Troubleshooting

### Testes de Integração Falhando

**Problema:** "Connection refused" ou "database does not exist"

**Solução:**
```bash
# Verificar se o container está rodando
docker-compose ps postgres-test

# Ver logs
docker-compose logs postgres-test

# Recriar o container
docker-compose up -d postgres-test
```

### Fixtures com Warnings de Deprecation

**Problema:** Warnings sobre `@pytest.fixture` ao invés de `@pytest_asyncio.fixture`

**Solução:** Use sempre `@pytest_asyncio.fixture` para fixtures async:
```python
import pytest_asyncio

@pytest_asyncio.fixture  # Correto
async def my_fixture():
    pass
```

### Problemas com ENCRYPTION_KEY

**Problema:** `RuntimeError: Encryption key not configured`

**Solução:**
```bash
# Definir no ambiente de teste
export ENCRYPTION_KEY="test_encryption_key_32_bytes_long!!"

# Ou criar arquivo .env.test
echo "ENCRYPTION_KEY=test_encryption_key_32_bytes_long!!" > .env.test
```

## Markers Personalizados

O projeto define markers no `pyproject.toml`:

```python
@pytest.mark.unit  # Teste unitário
@pytest.mark.integration  # Teste de integração
@pytest.mark.e2e  # Teste end-to-end
@pytest.mark.slow  # Teste lento
```

**Executar por marker:**
```bash
pytest -m unit  # Apenas unit tests
pytest -m "integration"  # Apenas integration tests
pytest -m "not slow"  # Todos exceto slow
```

## Boas Práticas

1. **Fixtures Async:**
   - Sempre use `@pytest_asyncio.fixture` para fixtures async
   - Use `async def` para fixtures que precisam de `await`

2. **Limpeza de Dados:**
   - Cada teste deve limpar seus dados via fixtures
   - Utilize `await session.rollback()` em tearDown

3. **Isolamento:**
   - Cada teste deve ser independente
   - Não compartilhe estado entre testes

4. **Cobertura:**
   - Mantenha cobertura >90% para código crítico
   - 100% para novos features (mandatório)

5. **Performance:**
   - Unit tests devem ser rápidos (<1s cada)
   - Integration tests podem ser mais lentos mas <10s cada

## Referências

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Asyncio Documentation](https://github.com/pytest-dev/pytest-asyncio)
- [SQLAlchemy Async Guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
