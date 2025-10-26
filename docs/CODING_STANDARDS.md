# Coding Standards - Crypto Trading Bot

Este documento define os padrões de código para o projeto Crypto Trading Bot, incluindo configurações de linters, regras ignoradas e justificativas.

## Índice

- [Resumo](#resumo)
- [Ferramentas de Qualidade](#ferramentas-de-qualidade)
- [Configuração Ruff](#configuração-ruff)
- [Configuração MyPy](#configuração-mypy)
- [Regras Ignoradas e Justificativas](#regras-ignoradas-e-justificativas)
- [Padrões de Código](#padrões-de-código)
- [Testes](#testes)

## Resumo

O projeto utiliza um stack moderno de quality tools:

- **Ruff**: Linter rápido (substituiu Flake8 + isort)
- **Black**: Formatador de código (padrão de linha 88)
- **MyPy**: Type checker estático
- **Pytest**: Framework de testes
- **Pre-commit**: Hooks de validação automática

**Objetivo**: Manter código limpo, tipado e testado sem comprometer a velocidade de desenvolvimento.

## Ferramentas de Qualidade

### Pre-commit Hooks

O projeto utiliza hooks automatizados que executam antes de cada commit:

```bash
# Instalar hooks
pre-commit install

# Rodar manualmente
pre-commit run --all-files
```

**Hooks configurados:**
- `ruff`: Linting e organização de imports
- `black`: Formatação de código
- `mypy`: Verificação de tipos
- `pytest`: Testes unitários (pre-push only)

### Pre-push Hook

Apenas testes unitários são executados no pre-push para manter feedback rápido:

```yaml
# .pre-commit-config.yaml
- id: pytest
  entry: pytest -q tests/unit/
  stages: [pre-push]
```

**Motivo**: Testes de integração requerem PostgreSQL e são executados apenas no CI.

## Configuração Ruff

### Regras Ativas

```toml
[tool.ruff.lint]
select = ["F", "E", "W", "I", "B"]
```

- **F**: Pyflakes (erros lógicos)
- **E**: pycodestyle errors (erros PEP 8)
- **W**: pycodestyle warnings (warnings PEP 8)
- **I**: isort (organização de imports)
- **B**: flake8-bugbear (bugs comuns)

### Regras Ignoradas

```toml
ignore = [
    "E501",  # Line too long - controlado por Black (88 chars)
    "E402",  # Module level import not at top of file (necessário em alguns casos)
    "W291", "W292", "W391", "W293",  # Whitespace cosmético
    "E265",  # Block comment spacing
]
```

**Justificativas:**

- **E501 (Line too long)**: Redundante com Black que mantém 88 caracteres
- **E402**: Às vezes necessário para configuração antes de imports (ex: `sys.path` modifications)
- **W291-W293**: Whitespace é tratado automaticamente por Black
- **E265**: Espaçamento em comentários não afeta funcionalidade

**Quando revisar:**
- Se time crescer (evitar inconsistências)
- Antes de release major
- Quando ferramentas evoluírem

## Configuração MyPy

### Configurações Ativas

```toml
[tool.mypy]
python_version = "3.12"
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
```

### Configurações Desabilitadas

```toml
disallow_untyped_decorators = false  # Click decorators are type-safe in Python 3.12+
ignore_missing_imports = true  # Global ignore for missing stubs
```

**Justificativas:**

- **disallow_untyped_decorators**: Click funciona bem sem type ignores no Python 3.12+
- **ignore_missing_imports**: Global ignore, mas temos overrides específicos para bibliotecas sem stubs

### Overrides Específicos

```toml
[[tool.mypy.overrides]]
# Bibliotecas sem stubs disponíveis
module = [
    "ccxt.*",
    "pandas.*",
    "numpy.*",
]
ignore_missing_imports = true
```

### Stubs Instaladas

```txt
# requirements-dev.txt
types-PyYAML>=6.0.0  # Para PyYAML
```

**Nota**: SQLAlchemy 2.0+ inclui stubs built-in, não requer instalação adicional.

### Quando Usar Type Ignores

**✅ Justificado:**
- Acessar atributos dinâmicos em SQLAlchemy models (`entity.id`)
- Operações que MyPy não consegue inferir mas são seguras em runtime

**❌ Evitar:**
- Mascarar erros de tipo reais
- Compensar má arquitetura
- Type ignores desnecessários

**Exemplo de uso correto:**

```python
# ✅ CORRETO: Type ignore justificado com comentário
entity_id = entity.id  # type: ignore[attr-defined]
# Motivo: T é bound a Base que deve ter 'id', mas MyPy não infere isso

# ❌ ERRADO: Type ignore sem comentário ou contexto
entity_id = entity.id  # type: ignore
```

## Regras Ignoradas e Justificativas

### Ruff - Regras Cosméticas

| Regra | Descrição | Justificativa |
|-------|-----------|---------------|
| E501 | Line too long | Black controla automaticamente (88 chars) |
| E402 | Module level import not at top | Necessário em alguns casos de configuração |
| W291-W293 | Trailing/blank whitespace | Black trata automaticamente |
| E265 | Block comment spacing | Cosmético, não afeta funcionalidade |

**Ação**: Revisar quando time crescer ou antes de releases major.

### MyPy - Configurações Globais

| Configuração | Valor | Justificativa |
|--------------|-------|---------------|
| `disallow_untyped_decorators` | `false` | Click funciona bem sem ignores no Python 3.12+ |
| `ignore_missing_imports` | `true` (global) | Overrides específicos para cada lib sem stubs |
| `warn_unused_ignores` | `true` | Detecta ignores obsoletos automaticamente |

## Padrões de Código

### Type Hints

**✅ Obrigatório:**
- Todas as funções públicas devem ter type hints
- Parâmetros de funções devem ser tipados
- Retorno de funções deve ser tipado
- Use `None` explícito: `str | None` ao invés de `Optional[str]` (Python 3.12+)

**Exemplo:**
```python
def process_order(order: OrderDTO) -> OrderDTO:
    """Process an order and return the result."""
    pass
```

### Docstrings

**✅ Formato:**
```python
def fetch_balance(currency: str | None = None) -> Dict[str, BalanceDTO]:
    """
    Fetch account balance for specified currency or all currencies.
    
    Args:
        currency: Optional currency code (e.g., 'BTC', 'ETH'). 
                 If None, returns all currencies.
    
    Returns:
        Dictionary mapping currency codes to BalanceDTO objects.
        
    Raises:
        ExchangeError: If the exchange API request fails.
        NetworkError: If there's a network connectivity issue.
    """
    pass
```

**Incluir sempre:**
- Descrição da função
- Args com tipos e descrições
- Returns com tipos
- Raises quando aplicável

### Imports

**Ordem (por Ruff isort):**
1. Standard library
2. Third-party packages
3. First-party (`crypto_bot`)

**Exemplo:**
```python
import asyncio
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from crypto_bot.domain.exceptions import ExchangeError
from crypto_bot.infrastructure.database.base import Base
```

### Async/Await

**Padrão:**
```python
async def fetch_data() -> Dict[str, Any]:
    """Fetch data asynchronously."""
    async with session() as conn:
        result = await conn.execute(query)
        return await result.fetchall()
```

**Fixtures Async:**
```python
import pytest_asyncio

@pytest_asyncio.fixture
async def db_session():
    """Provide async database session."""
    async for session in get_db_session():
        yield session
        await session.rollback()
```

### Error Handling

**Use exceptions específicas:**
```python
from crypto_bot.domain.exceptions import ExchangeError, NetworkError

try:
    response = await exchange.fetch_ticker(symbol)
except aiohttp.ClientError as e:
    raise NetworkError(f"Network error: {e}") from e
except Exception as e:
    raise ExchangeError(f"Exchange error: {e}") from e
```

## Testes

### Estrutura

```
tests/
├── unit/           # Testes unitários (sem dependências)
├── integration/    # Testes de integração (com DB)
└── e2e/            # Testes end-to-end
```

### Markers

```python
@pytest.mark.unit         # Teste unitário
@pytest.mark.integration  # Requer PostgreSQL
@pytest.mark.e2e          # Teste completo
@pytest.mark.slow         # Teste lento
```

### Executar Testes

```bash
# Unit tests (rápido, sem DB)
pytest tests/unit/ -v

# Integration tests (requer postgres-test)
pytest tests/integration/ -v

# Todos
pytest -v
```

### Coverage

**Meta:**
- Novo código: 100%
- Código existente: >90%

```bash
pytest --cov=src/crypto_bot --cov-report=term-missing
```

## Workflow de Desenvolvimento

### Antes de Commitar

```bash
# 1. Formatar
black .

# 2. Lint
ruff check .

# 3. Type check
mypy src/crypto_bot/

# 4. Testes
pytest tests/unit/
```

### Pre-commit

Hooks executam automaticamente:
- ✅ Ruff (linting)
- ✅ Black (formatação)
- ✅ MyPy (type checking)

### Pre-push

- ✅ Pytest (apenas unit tests)

### CI/CD

- ✅ Todos os testes (unit + integration)
- ✅ Coverage report
- ✅ Security checks (bandit)

## Decisões Arquiteturais

### Por que Python 3.12+?

- Type hints nativos melhores (uso de `|` ao invés de `Union`)
- Melhor performance
- Features modernas de asyncio
- Click decorators type-safe

### Por que Ruff + Black?

- **Ruff**: 10-100x mais rápido que Flake8
- **Black**: Padrão da indústria, zero configuração
- Compatibilidade garantida entre ambos

### Por que manter Click?

- Funciona bem com Python 3.12+ type hints
- Não requer ignores
- Stack estável e maduro
- Typer seria breaking change sem benefício claro

### Por que pytest-asyncio?

- Melhor suporte a fixtures async
- Sem warnings de deprecation
- Padrão recomendado para testes async

## Contato

Para dúvidas sobre padrões de código, abra uma issue ou consulte:

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Black Documentation](https://black.readthedocs.io/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Asyncio Documentation](https://github.com/pytest-dev/pytest-asyncio)

---

**Atualizado:** 2025-01-27  
**Versão:** 1.0  
**Autor:** Equipe de Desenvolvimento