# Dívidas Técnicas da Migração Linter

**Data:** 2025-01-27  
**PR:** Migração de Flake8/isort para Ruff + Black  
**Autor:** Sistema de Qualidade de Código

---

## Resumo Executivo

Este documento cataloga as dívidas técnicas introduzidas durante a migração completa do stack de linting (Flake8/isort → Ruff + Black), bem como as configurações deliberadamente escolhidas para facilitar a migração sem comprometer a segurança/robustez do código.

**Status Geral:** ✅ **CRÍTICO** - Requer atenção em próximo ciclo de desenvolvimento

**Prioridade:** Alta - afeta manutenibilidade de longo prazo e escalabilidade do time

---

## 🔴 Dívidas Técnicas Críticas

### 1. Type Safety em `BaseRepository.update()`

**Arquivo:** `src/crypto_bot/infrastructure/database/repositories/base_repository.py:138-144`

**Situação Atual:**
```python
entity_id = cast(UUID, cast(Any, entity).id)
existing = await self.get_by_id(entity_id)
```

**Problema:**
- Uso de `cast(Any, entity)` para contornar falta de type safety genérica
- Violação de princípios SOLID (substituição genérica)
- MyPy não valida que `T` realmente tem atributo `id`

**Impacto:**
- **Alto risco em runtime:** Tentativa de acessar `.id` em tipos incompatíveis resultará em `AttributeError`
- **Reduzida type safety:** Erros de tipo só aparecem em runtime
- **Efeito cascata:** Reduz confiabilidade de todos os repositórios (Order, Position, Asset, etc.)

**Solução Recomendada:**
```python
# Opção 1: Protocol explícito
class HasId(Protocol):
    id: UUID

T = TypeVar("T", bound=HasId)

# Opção 2: Constraint genérica
from typing import Generic, TypeVar, Protocol

class HasId(Protocol):
    id: UUID

T = TypeVar("T", bound=Base | HasId)
```

**Custo Estimado:** 4-6 horas
- Criar protocol `HasId`
- Atualizar todos os modelos SQLAlchemy para implementá-lo explicitamente
- Validar com MyPy strict mode
- Atualizar documentação de repositórios

**Risco de NÃO fazer:** Bugs de type em produção relacionados a IDs inexistentes ou tipos errados.

---

### 2. MyPy `disallow_untyped_decorators = false`

**Arquivo:** `pyproject.toml:129`

**Situação Atual:**
```toml
[tool.mypy]
disallow_untyped_decorators = false
```

**Problema:**
- Decoradores não-tipados (principalmente `@click.group()`, `@click.command()`, etc.)
- Perda de type safety em callbacks CLI
- Funções CLI não validadas pelo MyPy

**Impacto:**
- **Médio:** Bugs em CLI não detectados até runtime
- **Manutenibilidade:** Difícil adicionar novos comandos sem erros silenciosos
- **Developer Experience:** Autocomplete pior em contextos CLI

**Solução Recomendada:**
```python
# Usar stubs ou criar wrappers tipados
from click.decorators import group, command  # type: ignore[attr-defined]

@group()  # type: ignore[misc]
def main() -> None:
    pass
```

**Alternativa:**
- Usar `typer` (type-safe CLI framework)
- Criar stubs para `click`

**Custo Estimado:** 2-3 horas
- Investigar alternativas tipadas para Click
- Avaliar Typer como substituição
- Migration path se necessário

---

### 3. MyPy `ignore_missing_imports = true`

**Arquivo:** `pyproject.toml:136`

**Situação Atual:**
```toml
[tool.mypy]
ignore_missing_imports = true
```

**Problema:**
- Imports sem types não são validados (ex: `asyncpg`, algumas libs de `sqlalchemy.ext.asyncio`)
- Potencial para bugs de interface não detectados
- Reduz efetividade do MyPy em 30-40%

**Impacto:**
- **Alto:** Bugs de API em bibliotecas externas não detectados
- **Migrations:** Breaking changes em bibliotecas (ex: SQLAlchemy 2.x) podem passar despercebidos
- **Type Safety:** Componentes críticos (asyncpg, SQLAlchemy) não totalmente validados

**Solução Recomendada:**
```bash
# Instalar stubs específicos
pip install types-asyncpg types-sqlalchemy
```

**Arquivo:** `requirements-dev.txt` - adicionar:
```txt
types-asyncpg>=0.x.x  # Se disponível
types-sqlalchemy>=0.x.x
types-redis>=0.x.x  # Se usamos Redis
types-yaml  # Já incluído
```

**Configuração:**
```toml
[tool.mypy]
ignore_missing_imports = false
# Ou usar inline type ignores específicos:
# import asyncpg  # type: ignore[misc,unused-ignore]
```

**Custo Estimado:** 2-4 horas
- Investigar disponibilidade de stubs para dependências críticas
- Instalar e configurar stubs
- Resolver erros MyPy em imports que antes eram ignorados

---

### 4. MyPy `warn_unused_ignores = false`

**Arquivo:** `pyproject.toml:132`

**Situação Atual:**
```toml
[tool.mypy]
warn_unused_ignores = false
```

**Problema:**
- `# type: ignore` desnecessários não são reportados
- Acúmulo de ignores obsoletos ao longo do tempo
- Code smell escondido pelo linter

**Impacto:**
- **Baixo-Médio:** Debt acumulado invisível
- **Cleanup:** Difícil saber quando um ignore já não é mais necessário
- **Refactoring:** Múltiplos ignores podem mascarar melhorias arquiteturais

**Solução Recomendada:**

**Fase 1 - Auditar:**
```bash
# Temporariamente ativar para ver estado real
mypy --config-file=pyproject.toml src/crypto_bot/ > mypy-audit.txt
```

**Fase 2 - Limpar:**
- Remover ignores obsoletos
- Substituir por solução arquitetural quando possível
- Documentar justifies restantes

**Fase 3 - Reativar:**
```toml
[tool.mypy]
warn_unused_ignores = true  # Após cleanup completo
```

**Custo Estimado:** 1-2 horas
- Rodar audit
- Categorizar ignores (justificados vs obsoletos)
- Criar backlog de refactors necessários

---

## 🟡 Dívidas Técnicas Médias

### 5. Pre-push Hook: Apenas Testes Unitários

**Arquivo:** `.pre-commit-config.yaml:21-27`

**Situação Atual:**
```yaml
- id: pytest
  name: pytest (pre-push)
  entry: pytest -q
  stages: [pre-push]
```

**Problema:**
- Testes de integração não executam no pre-push
- Falhas de DB não detectadas localmente
- Risco de quebrar CI após push bem-sucedido

**Impacto:**
- **Médio:** Feedback loop mais longo (CI detecta falhas pós-push)
- **Developer Experience:** Desenvolvedor pode "passar local mas quebrar CI"
- **CI/CD:** Pipeline mais lento e potencialmente instável

**Solução Recomendada:**

**Opção 1 - CI Only para Integration:**
```yaml
# Pre-push: apenas unit
- id: pytest-unit
  entry: pytest -q tests/unit/
  stages: [pre-push]

# CI: roda todos incluindo integration
# em .github/workflows/ci.yml
- name: Run all tests
  run: pytest -q
```

**Opção 2 - Marcar Tests:**
```yaml
- id: pytest
  entry: pytest -q -m "not integration"
  stages: [pre-push]
```

**Custo Estimado:** 1 hora
- Atualizar `.pre-commit-config.yaml`
- Documentar em `docs/WORKFLOW_*`
- Verificar que CI ainda roda integration tests

---

### 6. Testes de Integração Desabilitados Localmente

**Situação Atual:**
- Testes de integração existem mas falham localmente por falta de Postgres
- CI provavelmente não está configurado para rodar integration tests com DB

**Problema:**
- Cobertura de testes reduzida
- Mudanças que quebram modelos SQLAlchemy podem passar
- Fixtures assíncronas com warnings de deprecação

**Impacto:**
- **Médio:** Regressões em integrações de DB não detectadas
- **CI/CD:** Dependência de testes manuais ou staging para validar integrações

**Solução Recomendada:**

**Local:**
```bash
# Docker Compose para Postgres local
docker-compose up -d postgres

# Configurar pytest.ini
[tool.pytest.ini_options]
markers =
    unit: Unit tests (quick, no DB)
    integration: Integration tests (require DB)
    asyncio: Async tests
```

**CI:**
```yaml
# .github/workflows/ci.yml
- name: Start PostgreSQL
  run: docker-compose up -d postgres

- name: Run integration tests
  run: pytest -m integration
```

**Custo Estimado:** 3-4 horas
- Configurar Docker Compose para local
- Migrar fixtures para `@pytest_asyncio.fixture` (remover warnings)
- Configurar CI para rodar integration tests com DB

---

## 🟢 Dívidas Técnicas Menores (Regras do Linter)

### 7. Regras Ruff Ignoradas (Cosméticas)

**Arquivo:** `pyproject.toml:[tool.ruff.lint]`

**Regras Ignoradas:**
```toml
ignore = [
    "E501",  # Line too long (handled by Black at 88 chars)
    "E402",  # Module level import not at top of file
    "W291",  # Trailing whitespace
    "W292",  # No newline at EOF
    "W391",  # Blank line at EOF
    "W293",  # Blank line contains whitespace
    "E265",  # Block comment should start with '#'
]
```

**Justificativa:**
- E501: Redundante com Black (mantido a 88 caracteres)
- E402: Máscara razoável quando necessário (ex: sys.path manipulations)
- W291-W293: Cosmético, facilmente autofixe com Black/formatters
- E265: Cosmético, não afeta funcionalidade

**Impacto:**
- **Baixo:** Regras cosméticas intencionalmente relaxadas
- **Developer Experience:** Reduz ruído do linter focado em problemas reais

**Quando Revisar:**
- Quando time crescer (evitar inconsistência de estilo)
- Antes de release major
- Quando ferramentas de formatação evoluírem

**Actionable Item:**
- Documentar essas regras em `docs/CODING_STANDARDS.md`
- Considerar `ruff format` (experimental) para futuros ciclos

---

### 8. Import Sorting via Ruff (sem isort standalone)

**Situação Atual:**
- Ruff handling imports (isort rules)
- Ordem: stdlib → third-party → first-party (`crypto_bot`)
- Compatível com Black

**Configuração:**
```toml
[tool.ruff.lint.isort]
known-first-party = ["crypto_bot"]
split-on-trailing-comma = true
```

**Sem Problema Atual:**
- Configuração adequada
- Autofix funciona bem
- Alinhado com Black

**Monitoramento:**
- Se aparecer conflitos Black vs Ruff format, considerar unificar para `ruff format` quando estável

---

## 📊 Checklist de Ações Recomendadas

### Crítico (P0 - Próximo Sprint)

- [ ] **Refatorar `BaseRepository` com protocol `HasId`** (4-6h)
  - Criar `HasId` protocol
  - Atualizar todos os modelos SQLAlchemy
  - Remover `cast(Any, entity).id`
  - Testar com MyPy strict mode

- [ ] **Configurar stubs MyPy para dependências críticas** (2-4h)
  - `types-asyncpg`
  - `types-sqlalchemy`
  - `types-redis` (se aplicável)
  - Reativar `ignore_missing_imports = false`

### Alta Prioridade (P1 - Próximo Mês)

- [ ] **Melhorar type safety em CLI (`click` decorators)** (2-3h)
  - Avaliar Typer como alternativa
  - Ou criar stubs para Click
  - Remover `disallow_untyped_decorators = false`

- [ ] **Configurar integration tests localmente** (3-4h)
  - Docker Compose para Postgres
  - Migrar fixtures para `@pytest_asyncio.fixture`
  - Habilitar integration tests no pre-push (opcional)

### Média Prioridade (P2 - Backlog)

- [ ] **Auditar e limpar `type: ignore` obsoletos** (1-2h)
  - Rodar `warn_unused_ignores = true`
  - Categorizar ignores
  - Refatorar código que requer ignores

- [ ] **Documentar coding standards explícitos** (2h)
  - Criar `docs/CODING_STANDARDS.md`
  - Documentar regras ignoradas e justificativas
  - Onboarding guide para novos devs

### Baixa Prioridade (P3 - Future)

- [ ] **Avaliar `ruff format` como único formatter** (4h)
  - Quando Ruff format for estável
  - Unificar com Black ou substituir
  - Atualizar workflows e docs

---

## 📈 Métricas de Qualidade

**Estado Atual:**
- ✅ 0 erros Ruff (formatação e imports)
- ✅ 0 erros MyPy em `src/crypto_bot`
- ✅ 100% unit tests passando
- ⚠️ Integration tests não executam localmente
- ⚠️ Dívidas técnicas críticas em type safety

**Meta (3 meses):**
- Eliminar todos `cast(Any, ...)`
- 100% type coverage em repositórios
- Integration tests rodando em CI
- Documentação de standards atualizada

---

## 🔗 Referências

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Configuration](https://mypy.readthedocs.io/en/stable/config_file.html)
- [Black Documentation](https://black.readthedocs.io/)
- [Python Type Hints (PEP 484)](https://www.python.org/dev/peps/pep-0484/)
- [Protocols (PEP 544)](https://www.python.org/dev/peps/pep-0544/)

---

## Notas Finais

Esta migração foi **bem-sucedida** ao eliminar centenas de lints obsoletos, padronizar imports, e estabelecer uma base sólida de type checking. As dívidas técnicas catalogadas são **gestionáveis** e **priorizáveis** conforme roadmap do projeto.

**Recomendação:** Endereçar itens P0 no próximo sprint, P1 no próximo ciclo, manter P2/P3 no backlog para quando time tiver bandwidth adicional.

