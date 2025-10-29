# Operational Hardening Guide (2025)

Este guia descreve hardening operacional e scans de segurança para o `crypto-bot`.

## Ferramentas de Segurança

### 1. Bandit (Security Linter)

Bandit já está configurado em `pyproject.toml` e disponível no Makefile:

```bash
# Executar scan de segurança
make security-check

# Ou via bandit diretamente
bandit -r src/crypto_bot
```

**Configuração atual**:
- Exclui diretórios de teste
- Skip de regras: `B101` (assert_used), `B601` (shell_injection_subprocess)

**Integração CI**: Ver seção "CI/CD Integration" abaixo.

### 2. Safety / pip-audit (Dependency Scanning)

Para escanear dependências vulneráveis:

```bash
# Via safety
safety check --json

# Via pip-audit (alternativa)
pip-audit

# Com output em arquivo
pip-audit -f requirements.txt -o audit-report.json
```

**Recomendação**: Usar `pip-audit` por ser mantido pela PyPA e estar mais atualizado.

### 3. Gitleaks (Secret Detection)

Para detectar segredos comitados acidentalmente:

```bash
# Instalar (macOS)
brew install gitleaks

# Scan repositório
gitleaks detect --verbose

# Scan commito específico
gitleaks detect --commit HEAD

# Criar relatório
gitleaks detect --report-path gitleaks-report.json
```

**Recomendação**: Executar em pre-commit hooks e no CI antes de merge.

## Rate Limiting

### Implementação Atual

O utilitário de rate limiting existe em `src/crypto_bot/utils/rate_limiter.py`:

- **AsyncTokenBucket**: Token bucket para rate limiting de requests
- **ConcurrencyGuard**: Semáforo para limitar requests concorrentes

### Uso Recomendado

```python
from crypto_bot.utils.rate_limiter import AsyncTokenBucket, ConcurrencyGuard

# Rate limiter por exchange
binance_limiter = AsyncTokenBucket(rate_per_sec=10.0)  # 10 req/s
await binance_limiter.acquire()

# Guard de concorrência
guard = ConcurrencyGuard(max_in_flight=5)  # Máximo 5 requests simultâneas
async with guard.limit():
    # Fazer request
    pass
```

### Configuração por Exchange

Adicionar no `config_json` de cada exchange:

```yaml
# config/environments/base.yaml
exchanges:
  binance:
    rate_limit:
      requests_per_second: 10
      max_concurrent: 5
  coinbase:
    rate_limit:
      requests_per_second: 5
      max_concurrent: 3
```

## ORM Injection Safety (SQLAlchemy 2.0)

### Boas Práticas

✅ **SEMPRE usar ORM**:
```python
# ✅ Correto
orders = await session.execute(select(Order).where(Order.symbol == symbol))

# ❌ NUNCA fazer
orders = await session.execute(f"SELECT * FROM orders WHERE symbol = '{symbol}'")
```

✅ **Parameterized queries quando necessário**:
```python
# ✅ Correto
stmt = text("SELECT * FROM orders WHERE symbol = :symbol")
result = await session.execute(stmt, {"symbol": symbol})

# ❌ NUNCA fazer
result = await session.execute(f"SELECT * FROM orders WHERE symbol = '{symbol}'")
```

### Testes de Injeção

Executar testes para validar proteção:

```bash
# Tests existentes já cobrem ORM usage
pytest tests/integration/test_repositories.py -v
```

## Backup e Disaster Recovery

### Backup de Banco de Dados

**PostgreSQL**:

```bash
# Backup completo
pg_dump -U crypto_bot_user -d crypto_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup apenas esquema
pg_dump -U crypto_bot_user -d crypto_bot --schema-only > schema_backup.sql

# Backup apenas dados
pg_dump -U crypto_bot_user -d crypto_bot --data-only > data_backup.sql
```

**Automatização**:

```bash
# Criar script: scripts/backup-database.sh
#!/bin/bash
BACKUP_DIR="./data/backups"
mkdir -p $BACKUP_DIR
pg_dump -U crypto_bot_user -d crypto_bot > "$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"
# Manter últimos 7 backups
ls -t "$BACKUP_DIR"/*.sql | tail -n +8 | xargs rm -f
```

### Recovery Procedure

1. **Restaurar esquema**:
   ```bash
   psql -U crypto_bot_user -d crypto_bot < schema_backup.sql
   ```

2. **Restaurar dados**:
   ```bash
   psql -U crypto_bot_user -d crypto_bot < data_backup.sql
   ```

3. **Verificar integridade**:
   ```bash
   pytest tests/integration/test_database_connection.py -v
   ```

## CI/CD Integration

### GitHub Actions (Recomendado)

Criar `.github/workflows/security.yml`:

```yaml
name: Security Scans

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install bandit safety
      
      - name: Bandit Security Scan
        run: bandit -r src/crypto_bot -f json -o bandit-report.json
      
      - name: Safety Scan
        run: safety check --json --output safety-report.json || true
        continue-on-error: true
      
      - name: Upload reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: security-reports
          path: |
            bandit-report.json
            safety-report.json
      
      - name: Install gitleaks
        uses: gitleaks/gitleaks-action@v2
      
      - name: Gitleaks Scan
        run: gitleaks detect --verbose
```

### Pre-commit Hooks (Local)

Adicionar ao `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.8
    hooks:
      - id: bandit
        args: ["-r", "src/crypto_bot", "-f", "json", "-o", "bandit-report.json"]
        
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.22.0
    hooks:
      - id: gitleaks
```

## Checklist de Hardening

### Antes de Cada Deploy

- [ ] Executar `bandit` (via `make security-check`)
- [ ] Executar `pip-audit` ou `safety check`
- [ ] Executar `gitleaks` no repositório
- [ ] Verificar que rate limiting está configurado para todas as exchanges
- [ ] Verificar que nenhum segredo foi commitado (git log recente)
- [ ] Backup do banco antes de alterações de schema

### Mensal

- [ ] Revisar vulnerabilidades de dependências (pip-audit)
- [ ] Rotacionar chaves de criptografia (ver KEY_ROTATION_PLAYBOOK.md)
- [ ] Auditoria de logs por segredos expostos
- [ ] Verificar backups automáticos
- [ ] Teste de restore (DR drill)

### Trimestral

- [ ] Penetration testing de credential storage
- [ ] Code review focado em segurança
- [ ] Atualização de documentação de segurança
- [ ] Revisão de checklist operacional

## Referências

- Bandit docs: https://bandit.readthedocs.io/
- pip-audit docs: https://pip-audit.readthedocs.io/
- Gitleaks docs: https://gitleaks.io/
- SQLAlchemy 2.0 security: https://docs.sqlalchemy.org/en/20/security.html

---

**Última atualização**: 2025-10-28  
**Próxima revisão**: Após primeiro uso em produção

