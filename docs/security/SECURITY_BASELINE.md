## Security Baseline (2025)

Este documento define o escopo de segurança, inventário de segredos, ameaças principais e os controles mínimos obrigatórios para o projeto `crypto-bot`. Ele serve como referência operacional e checklist para desenvolvimento, revisão e deploys.

### 1) Escopo

- Aplicação Python 3.12+ com arquitetura modular e plugins de exchanges.
- Persistência em PostgreSQL (SQLAlchemy 2.0 / Alembic). Redis opcional.
- Integrações com exchanges (p.ex. Binance, Coinbase) via CCXT.
- CLI operacional e serviços assíncronos (`aiohttp`/tarefas internas).

### 2) Inventário de Segredos (origem: `.env`/vault)

- Banco de dados: `DATABASE_PASSWORD` (ou embutido em `DATABASE_URL`).
- Redis: `REDIS_PASSWORD` (quando aplicável).
- Criptografia: `ENCRYPTION_KEY` e opcional `ENCRYPTION_KEY_PREVIOUS` (rotação).
- JWT: `JWT_SECRET` (se JWT for utilizado).
- Exchanges:
  - Binance: `BINANCE_API_KEY`, `BINANCE_API_SECRET`.
  - Coinbase: `COINBASE_API_KEY`, `COINBASE_API_SECRET`, `COINBASE_PASSPHRASE`.
- Notificações (quando habilitadas): `TELEGRAM_BOT_TOKEN`, `DISCORD_WEBHOOK_URL`, `EMAIL_SMTP_PASSWORD`.

Regras:
- Nunca versionar `.env`. Usar `.env.example`/`env.config.example` como guia.
- Em produção, preferir vault (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault). `.env` apenas para desenvolvimento local.

### 3) Principais Ameaças

- Vazamento de segredos (logs, exceptions, commits, artefatos de build).
- Injeção em banco (quando fugir do ORM) e validação fraca de entrada.
- Exposição de dados sensíveis em logs (sem redaction).
- Dependências com vulnerabilidades conhecidas.
- Abuso de chamadas a exchanges (rate limiting insuficiente) e travamentos operacionais.

### 4) Controles Existentes (baseline atual do repositório)

- Criptografia de dados sensíveis em repouso
  - `src/crypto_bot/infrastructure/security/encryption.py`: serviço baseado em `cryptography` e derivação via PBKDF2.
  - Suporte a rotação suave de chaves com `ENCRYPTION_KEY_PREVIOUS` e prefixo de KID.
- Redação de logs (segre-dados/PII)
  - `src/crypto_bot/utils/logger.py`: formatter com padrões para mascarar `api_key`, `secret`, `passphrase` (testes em `tests/unit/utils/test_logger_redaction.py`).
- Configuração & validação
  - Pydantic v2 (`src/crypto_bot/config/settings.py` + YAML em `config/environments/`).
- Ferramentas de qualidade
  - Ruff/Black/MyPy/Pytest configurados em `pyproject.toml`. `bandit` disponível como extra de dev.
- Rate limiting
  - Utilitário existente em `src/crypto_bot/utils/rate_limiter.py` (aplicar por integração/UC).

### 5) Decisões e Diretrizes (2025)

1. Gestão de Segredos
   - Dev: `.env` carregado via `python-dotenv` (não versionar). Prod: vault.
   - Permissões mínimas (RBAC) e rotação periódica (90 dias) de segredos críticos.

2. Criptografia em Repouso
   - Usar serviço de criptografia existente (Fernet com chave derivada por PBKDF2) para campos sensíveis.
   - Manter versionamento de chaves (KID). Rotacionar com `ENCRYPTION_KEY_PREVIOUS` e recriptografar gradualmente.
   - Definir `ENCRYPTION_SALT` exclusivo em produção (nunca usar o default).

3. Validação de Entrada (Pydantic v2)
   - Modelos estritos para configurações e inputs; validadores customizados p/ padrões de chaves e URLs.

4. SQLAlchemy 2.0
   - Preferir ORM/Query Builder. Se SQL bruto for inevitável, sempre parametrizar.

5. Logs
   - Manter redaction ativa em todos os loggers. Evitar logs de segredos/PII em nível DEBUG/INFO.
   - Formato estruturado quando possível (ver config do `structlog` em `pyproject.toml`).

6. Scans de Segurança
   - Estático: `bandit` obrigatório no CI.
   - Dependências: `safety` ou `pip-audit` no CI.
   - Segredos: `gitleaks` em PRs e periodicamente no repositório.

7. Rate Limiting
   - Aplicar limitadores por exchange/endpoint conforme políticas públicas das exchanges.
   - Monitorar eventos de throttling.

8. Configuração de Produção
   - `DEBUG=false`, logs no nível mínimo necessário, objetos de config imutáveis após carga.
   - Restringir permissões de arquivos de config em hosts.

### 6) Checklists Operacionais

Segredos
- [ ] `.env` fora do versionamento e com permissões restritas no host.
- [ ] Vault integrado no pipeline de deploy (prod/staging).
- [ ] Rotação periódica de `ENCRYPTION_KEY`/`JWT_SECRET` e chaves de exchanges.

Criptografia
- [ ] Todos os campos sensíveis criptografados antes de persistir.
- [ ] `ENCRYPTION_SALT` definido e não padrão em produção.
- [ ] Plano de rotação com KIDs validado (decrypt com chave antiga, encrypt com chave nova).

Logs
- [ ] Redaction testado (tests verdes) e aplicado globalmente.
- [ ] Sem segredos em DEBUG/INFO. Auditoria periódica de logs.

Validação & DB
- [ ] Modelos Pydantic v2 estritos e testados.
- [ ] Sem SQL bruto; quando houver, sempre com parâmetros.

Scans & CI
- [ ] `bandit` obrigatório no CI.
- [ ] `safety` ou `pip-audit` no CI com falha em vulnerabilidades críticas.
- [ ] `gitleaks` para PRs e varredura programada do repositório.

Rate Limiting
- [ ] Limites por exchange implementados e monitorados.

Produção
- [ ] `DEBUG=false`, logging mínimo, configs imutáveis após carga.
- [ ] Permissões de arquivos de config revisadas (least privilege).

### 7) Próximos Passos (ligação com tarefas)

- 17.2 Secrets mgmt: implementar política de rotação (usar KID atual + `ENCRYPTION_KEY_PREVIOUS`) e documentar playbook.
- 17.3 Validação & logging hygiene: reforçar validadores Pydantic e ampliar padrões de redaction.
- 17.4 Operacional & scans: habilitar `bandit`, `safety/pip-audit` e `gitleaks` no CI/pre-commit.

Referências
- `src/crypto_bot/infrastructure/security/encryption.py`
- `src/crypto_bot/utils/logger.py`
- `env.example`, `env.config.example`
- `pyproject.toml` (Black, Ruff, MyPy, Pytest, Bandit, Structlog)


