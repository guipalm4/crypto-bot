# Padrões de Código - Crypto Trading Bot

**Última atualização:** 2025-01-27  
**Stack de Qualidade:** Ruff (lint + imports) + Black (format) + MyPy (type check)

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Ferramentas Utilizadas](#ferramentas-utilizadas)
3. [Regras de Formatação](#regras-de-formatação)
4. [Regras de Linting](#regras-de-linting)
5. [Type Safety](#type-safety)
6. [Import Sorting](#import-sorting)
7. [Testes](#testes)
8. [Pre-commit Hooks](#pre-commit-hooks)
9. [Troubleshooting](#troubleshooting)
10. [Quick Reference](#quick-reference)

---

## Visão Geral

Este projeto utiliza um stack moderno de ferramentas de qualidade de código:

- **Ruff**: Linting rápido (F, E, W, I rules) + import sorting (isort)
- **Black**: Code formatter (line-length 88, opinionated)
- **MyPy**: Type checker com configuração restritiva

**Filosofia:** Linter equilibrado focado em problemas reais de código, não cosméticos.

---

## Ferramentas Utilizadas

### 1. Ruff (Lint + Imports)

**Configuração:** `pyproject.toml [tool.ruff]`

```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = [
    "F",    # Pyflakes - Python errors
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "I",    # isort - import sorting
    "B",    # Bugbear - common bugs and design problems
    "UP",   # pyupgrade - modernize code
]
ignore = [
    "E501",  # Line too long (handled by Black)
    "E402",  # Module level import not at top
    "W291",  # Trailing whitespace
    "W292",  # No newline at EOF
    "W391",  # Blank line at EOF
    "W293",  # Blank line contains whitespace
    "E265",  # Block comment should start with '#'
]

[tool.ruff.lint.isort]
known-first-party = ["crypto_bot"]
split-on-trailing-comma = true
```

**Comandos:**
```bash
# Verificar
ruff check .

# Autofix
ruff check --fix .

# Config específico
ruff check --config=pyproject.toml .
```

**Regras Selecionadas:**
- `F`: Erros de Python (variáveis não definidas, imports não usados, etc.)
- `E`: Erros de estilo do PEP 8 (limitados - Black cuida da maioria)
- `W`: Warnings de estilo (limitados por cosmetic reasons)
- `B`: Bugbear (bugs comuns como mutáveis em defaults, etc.)
- `UP`: pyupgrade (modernizar código - `list` vs `List`, etc.)

**Por que ignoramos algumas regras?**
- **E501**: Black já cuida de line-length (88 chars)
- **E402**: Necessário em alguns casos (sys.path, etc.)
- **W291-W293**: Cosmético, Black remove automaticamente
- **E265**: Cosmético, não afeta funcionalidade

---

### 2. Black (Formatter)

**Configuração:** `pyproject.toml [tool.black]` (implicit via Black defaults)

Black é **opiniado** e não configuravel além de `line-length`.

**Comandos:**
```bash
# Formatar
black .

# Verificar sem formatar
black --check .

# Linha específica
black --line-length=88 src/crypto_bot/
```

**Padrões Black:**
- **Line length:** 88 caracteres
- **Quotes:** Prefere aspas duplas (mas aceita qual)
- **Trailing commas:** Sempre que possível
- **String quotes:** Duplas quando possível
- **Blank lines:** 2 linhas entre top-level, 1 entre classes

**O que Black NÃO faz:**
- Reorganizar imports (Ruff isort faz isso)
- Type hints (MyPy cuida disso)
- Linting (Ruff cuida disso)

---

### 3. MyPy (Type Checker)

**Configuração:** `pyproject.toml [tool.mypy]`

```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = false
warn_unused_configs = true

# Disabled for migration ease (TODO: tighten)
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = false  # TODO: Enable for click decorators
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = false  # TODO: Enable after cleanup
warn_no_return = true
warn_unreachable = true
strict_equality = true
ignore_missing_imports = true  # TODO: Add stubs

# Package structure
files = ["src/crypto_bot"]
namespace_packages = true
explicit_package_bases = true
mypy_path = ["src"]

[tool.mypy.plugins]
plugins = ["pydantic.mypy"]
```

**Comandos:**
```bash
# Verificar
mypy src/crypto_bot/

# Com config específico
mypy --config-file=pyproject.toml

# Strict mode (sem relaxações)
mypy --strict src/crypto_bot/
```

**O que MyPy faz:**
- Valida type hints
- Detecta erros de tipo em compile-time
- Integra com SQLAlchemy via `declared_attr`
- Integra com Pydantic via plugin

**Limitações atuais:**
- CLI decorators (`@click.group()`) não validados (conhecido issue)
- Alguns imports externos ignorados (falta de stubs)
- Genéricos complexos requerem type ignores (work in progress)

Ver [técnico_debt_linter_migration.md](técnico_debt_linter_migration.md) para detalhes.

---

## Regras de Formatação

### Line Length

**Padrão:** 88 caracteres (Black default)

```python
# ✅ OK
def create_order(
    symbol: str,
    side: OrderSide,
    amount: Decimal,
    exchange: str,
) -> OrderDTO:

# ❌ Muito longo (>88 chars)
def create_order_with_complex_logic(symbol: str, side: OrderSide, ...) -> OrderDTO:
```

**Por que 88?**
- Black default (vs 79 do PEP 8)
- Melhor uso de espaço em telas modernas
- Consistente com bibliotecas Python modernas

---

### Import Organization

**Regra de Ruff isort:**
```
stdlib imports
↓ (blank line)
third-party imports (asyncpg, sqlalchemy, etc.)
↓ (blank line)
first-party imports (crypto_bot.*)
```

**Exemplo:**
```python
# stdlib
from datetime import datetime
from typing import Optional
from uuid import UUID

# third-party
import asyncpg
from sqlalchemy import Column
from sqlalchemy.ext.asyncio import AsyncSession

# first-party
from crypto_bot.domain.exceptions import EntityNotFoundError
from crypto_bot.domain.repositories import IOrderRepository
```

**Comandos:**
```bash
# Autofix imports
ruff check --fix --select I .

# Verificar apenas imports
ruff check --select I .
```

---

### Type Hints

**Padrão:** Sempre tipar funções públicas e retornos.

```python
# ✅ OK
def create_order(symbol: str, amount: Decimal) -> OrderDTO:
    """Create a new order."""
    return OrderDTO(...)

# ❌ Sem type hints
def create_order(symbol, amount):  # MyPy: error
    return OrderDTO(...)
```

**Exceções:**
- Testes podem omitir type hints (mas recomendado adicionar)
- Closures simples podem omitir se óbvio

**Comandos:**
```bash
# Verificar types
mypy src/crypto_bot/

# Encontrar sem type hints
mypy --disallow-untyped-defs src/crypto_bot/
```

---

### Async/Await

**Padrão:** Sempre usar `async def` e `await` para I/O.

```python
# ✅ OK
async def fetch_balance(exchange: str) -> BalanceDTO:
    result = await self._client.fetch_balance(exchange)
    return result

# ❌ Bloqueante
def fetch_balance(exchange: str):  # ❌ sync I/O
    result = self._client.fetch_balance(exchange)  # blocks
    return result
```

**Comandos:**
```bash
# Verificar async patterns
ruff check --select B src/crypto_bot/
```

---

## Regras de Linting

### Pyflakes (F rules)

**F401: Imported but unused**
```python
# ❌ Bad
import os  # não usado
from typing import Optional  # não usado

# ✅ Good
from typing import Optional

def func(value: Optional[str]) -> None:
    pass
```

**F841: Local variable assigned but never used**
```python
# ❌ Bad
for item in items:
    result = process(item)  # não usado

# ✅ Good
for item in items:
    _ = process(item)  # Prefix com underscore
```

**F811: Redefinition of unused**
```python
# ❌ Bad
from foo import bar
# ... later
from bar import bar  # redefinition

# ✅ Good - Use alias
from bar import bar as bar2
```

---

### Pycodestyle (E/W rules)

**E501: Line too long** ❌ **IGNORADO** (Black cuida)

**E402: Module level import not at top** ❌ **IGNORADO** (Necessário em alguns casos)

```python
# ✅ Quando OK ignorar E402
import sys
sys.path.insert(0, "/custom/path")  # type: ignore[E402]
from custom_module import something
```

**W291-W293: Whitespace issues** ❌ **IGNORADO** (Black remove automaticamente)

---

### Bugbear (B rules)

**B006: Do not use mutable data structures for argument defaults**
```python
# ❌ Bad
def process(items: list = []):  # ❌ shared state
    items.append("new")
    return items

# ✅ Good
def process(items: list | None = None):
    if items is None:
        items = []
    items.append("new")
    return items
```

**B009: Do not call `getattr` with a constant attribute value**
```python
# ❌ Bad
value = getattr(obj, "id")  # ❌ use obj.id

# ✅ Good
value = obj.id
```

**Exceção:** Quando necessário para type safety com genéricos:
```python
# ✅ OK - necessário para MyPy com genéricos
entity_id = cast(UUID, cast(Any, entity).id)  # noqa: B009
```

**B904: Specify an exception class when catching all exceptions**
```python
# ❌ Bad
try:
    risky_operation()
except:  # ❌ too broad
    pass

# ✅ Good
try:
    risky_operation()
except SpecificError:
    pass
```

---

### pyupgrade (UP rules)

**UP035: Use `X | None` for type annotations**
```python
# ❌ Old
from typing import Optional
def func() -> Optional[str]:
    pass

# ✅ Modern
def func() -> str | None:
    pass
```

**UP006: Use `list` instead of `List`**
```python
# ❌ Old
from typing import List
def func() -> List[str]:
    pass

# ✅ Modern
def func() -> list[str]:
    pass
```

**Comandos:**
```bash
# Autofix pyupgrade issues
ruff check --fix --select UP .
```

---

## Type Safety

### Funcionalidades Enforçadas

1. **Type hints obrigatórios em funções públicas**
   ```python
   # ✅ Required
   def public_function(param: str) -> None:
       pass
   ```

2. **No implicit Optional**
   ```python
   # ❌ Not allowed
   def func(value: str = None):  # type error
       pass
   
   # ✅ Required
   def func(value: str | None = None):
       pass
   ```

3. **Strict equality checking**
   ```python
   # ✅ MyPy catches this
   if value == None:  # type error
       pass
   
   # ✅ Correct
   if value is None:
       pass
   ```

4. **Return type checking**
   ```python
   # ✅ MyPy validates
   def func() -> str:
       return "value"  # OK
   
   # ❌ MyPy error
   def func() -> str:
       return 123  # type error
   ```

### Limitações Atuais

Ver [técnico_debt_linter_migration.md](técnico_debt_linter_migration.md#dividas-técnicas-críticas) para:
- `disallow_untyped_decorators = false` (CLI decorators)
- `ignore_missing_imports = true` (externas sem stubs)
- `warn_unused_ignores = false` (não audita ignores)

---

## Import Sorting

### Ordem

1. **Stdlib** (datetime, typing, uuid, etc.)
2. **Third-party** (asyncpg, sqlalchemy, click, etc.)
3. **First-party** (`crypto_bot.*`)

### Configuração Ruff isort

```toml
[tool.ruff.lint.isort]
known-first-party = ["crypto_bot"]
split-on-trailing-comma = true
```

### Comandos

```bash
# Sort imports
ruff check --fix --select I .

# Preview changes (dry-run)
ruff check --select I .
```

---

## Testes

### Structure

```
tests/
├── unit/          # Quick tests, no DB required
├── integration/   # Requires Postgres (run in CI)
└── fixtures/      # Shared test data
```

### Unit Tests (Quick, Local)

```bash
# Run unit tests
pytest -q tests/unit/

# Run specific test
pytest tests/unit/plugins/test_plugin_registry.py
```

### Integration Tests (Requires DB)

```bash
# Requires Postgres running
docker-compose up -d postgres

# Run integration tests
pytest -q tests/integration/

# Or mark-based
pytest -m integration
```

### Marking Tests

```python
import pytest

@pytest.mark.unit
def test_quick_function():
    """Unit test - no external deps."""
    pass

@pytest.mark.integration
async def test_database_operation(db_session):
    """Integration test - requires DB."""
    result = await session.execute(text("SELECT 1"))
    assert result
```

---

## Pre-commit Hooks

### Configuração

Arquivo: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff  # Lint
      - id: ruff-format  # Format (opcional)
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
  - repo: local
    hooks:
      - id: pytest  # Unit tests only
```

### Comandos

```bash
# Install hooks
pre-commit install
pre-commit install --hook-type pre-push

# Run hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
```

### O que Cada Hook Faz

1. **ruff**: Verifica linting e import sorting
2. **black**: Formata código (line-length 88)
3. **mypy**: Valida type hints em `src/crypto_bot/`
4. **pytest** (pre-push): Roda unit tests antes de push

---

## Troubleshooting

### Ruff Encontra E501 (Line Too Long)

**Problema:**
```bash
src/main.py:42:80: E501 line too long (92 > 79 characters)
```

**Solução:**
```bash
# Rodar Black primeiro
black .

# Verificar novamente
ruff check .
```

**Se persistir:**
- Verifique se `.flake8` ainda existe (deve ser removido)
- Verifique se `pyproject.toml` tem `ignore = ["E501"]`

---

### MyPy Reclama de Decoradores Não-Tipados

**Problema:**
```python
@click.group()  # type: ignore[misc]
def main() -> None:
    pass
```

**Por que:** Click decorators não são tipados nativamente.

**Solução temporária:**
```toml
[tool.mypy]
disallow_untyped_decorators = false  # TODO: Enable with stub
```

**Solução definitiva:** Usar Typer ou criar stub para Click (ver dívida técnica P1).

---

### MyPy Reclama de `T` não tem `id`

**Problema:**
```python
class BaseRepository(Generic[T]):
    async def update(self, entity: T) -> T:
        existing = await self.get_by_id(entity.id)  # error: T has no id
```

**Solução atual:**
```python
from typing import Any, cast

entity_id = cast(UUID, cast(Any, entity).id)  # noqa: B009
existing = await self.get_by_id(entity_id)
```

**Solução definitiva:** Protocol `HasId` (ver dívida técnica P0).

---

### Import Order Errado

**Problema:**
```bash
ruff check --select I .
# Many import sorting issues
```

**Solução:**
```bash
# Autofix
ruff check --fix --select I .

# Commit
git add .
git commit
```

---

## Quick Reference

### Verificar Código (Local)

```bash
# All checks at once
ruff check . && black --check . && mypy src/crypto_bot/ && pytest -q tests/unit/

# Or use pre-commit
pre-commit run --all-files
```

### Autofix

```bash
# Ruff lint + imports
ruff check --fix .

# Black format
black .

# MyPy has no autofix - requires manual fixes
```

### Arquivos de Configuração

- `pyproject.toml`: Ruff, Black, MyPy config
- `.pre-commit-config.yaml`: Git hooks
- `requirements-dev.txt`: Dependencies (ruff, black, mypy, etc.)
- `.github/workflows/ci.yml`: CI pipeline

### Git Hooks

```bash
# Install
./scripts/install-hooks.sh

# Manually trigger
git commit  # Runs pre-commit

# Skip hooks (avoid unless emergency)
git commit --no-verify
```

---

## Referências

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Black Documentation](https://black.readthedocs.io/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Python Type Hints (PEP 484)](https://peps.python.org/pep-0484/)
- [Protocols (PEP 544)](https://peps.python.org/pep-0544/)
- [PEP 8](https://peps.python.org/pep-0008/)

---

## Perguntas Frequentes

**Q: Por que 88 chars em vez de 79?**  
A: Black default e padrão moderno Python (ex: Django, Requests).

**Q: Posso usar `# type: ignore`?**  
A: Sim, mas documente o motivo. Exemplo: `# type: ignore[misc]  # Click decorator not typed`

**Q: Ruff ou Black formata imports?**  
A: Ruff (isort rules). Black não toca em imports.

**Q: Preciso rodar todos os checks antes de commit?**  
A: Não, `pre-commit` hooks fazem isso automaticamente.

**Q: O que fazer se pre-commit falha?**  
A: Fix o código, `git add` novamente, e tente commit de novo.

---

**Última atualização:** 2025-01-27  
**Mantenedor:** Equipe de Desenvolvimento

