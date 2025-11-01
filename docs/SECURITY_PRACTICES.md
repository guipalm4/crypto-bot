# 🔒 Práticas de Segurança e Considerações

Este documento cobre aspectos de segurança do Crypto Trading Bot, incluindo autenticação, autorização, proteção de dados e práticas de codificação segura.

## 📋 Índice

1. [Visão Geral de Segurança](#visão-geral-de-segurança)
2. [Gerenciamento de Credenciais](#gerenciamento-de-credenciais)
3. [Criptografia](#criptografia)
4. [Proteção de Dados](#proteção-de-dados)
5. [Segurança de Rede](#segurança-de-rede)
6. [Validação de Entrada](#validação-de-entrada)
7. [Logging Seguro](#logging-seguro)
8. [Práticas de Desenvolvimento Seguro](#práticas-de-desenvolvimento-seguro)
9. [Checklist de Segurança](#checklist-de-segurança)

## 🛡️ Visão Geral de Segurança

O Crypto Trading Bot implementa múltiplas camadas de segurança:

- **Criptografia AES-256** para credenciais no banco de dados
- **Variáveis de ambiente** para dados sensíveis
- **Validação rigorosa** de todas as entradas
- **Princípio do menor privilégio** para API keys de exchanges
- **Logging seguro** (dados sensíveis são mascarados)
- **HTTPS/SSL** para todas as comunicações externas

Para detalhes completos, consulte:
- [SECURITY_BASELINE.md](security/SECURITY_BASELINE.md) - Baseline de segurança
- [HARDENING_GUIDE.md](security/HARDENING_GUIDE.md) - Guia de hardening
- [KEY_ROTATION_PLAYBOOK.md](security/KEY_ROTATION_PLAYBOOK.md) - Rotação de chaves

## 🔑 Gerenciamento de Credenciais

### Variáveis de Ambiente

**NUNCA** hardcode credenciais no código. Use sempre variáveis de ambiente:

```python
# ✅ CORRETO
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

# ❌ ERRADO
api_key = "minha_chave_aqui"  # NUNCA faça isso!
api_secret = "minha_senha_aqui"
```

### Arquivo .env

Mantenha um arquivo `.env` no diretório raiz (nunca commitado):

```bash
# .env (não commitado no Git)
ENCRYPTION_KEY=your_32_byte_key_here_minimum_required
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
DATABASE_PASSWORD=secure_database_password
```

**⚠️ IMPORTANTE:**
- Adicione `.env` ao `.gitignore`
- Use `.env.example` como template (sem valores reais)
- Rotacione credenciais regularmente

### API Keys de Exchanges

**Princípio do Menor Privilégio:**

1. ✅ **Habilite apenas leitura** quando possível
2. ✅ **Desabilite saque (withdrawal)** SEMPRE
3. ✅ **Use IP whitelist** quando disponível
4. ✅ **Limite permissões** ao mínimo necessário
5. ✅ **Use testnet/sandbox** para desenvolvimento

**Exemplo de permissões seguras:**
- ✅ Leitura de mercado (market data)
- ✅ Leitura de saldo (balance)
- ✅ Criação de ordens (trading)
- ❌ Saque (withdrawal) - **NUNCA HABILITE**
- ❌ Transferências - **NUNCA HABILITE**

### Armazenamento de Credenciais no Banco

Credenciais de exchanges são **criptografadas** antes de serem armazenadas:

```python
from crypto_bot.infrastructure.security.encryption import get_encryption_service

# Criptografar antes de salvar
encryption_service = get_encryption_service()
encrypted_api_key = encryption_service.encrypt(api_key)

# Descriptografar ao usar
decrypted_api_key = encryption_service.decrypt(encrypted_api_key)
```

**Requisitos:**
- `ENCRYPTION_KEY` deve ter pelo menos 32 bytes
- Chave deve ser aleatória e segura
- Nunca compartilhe a chave de criptografia

## 🔐 Criptografia

### Chave de Criptografia

**Requisitos:**
- **Tamanho mínimo**: 32 bytes (256 bits para AES-256)
- **Aleatoriedade**: Use gerador seguro de números aleatórios
- **Proteção**: Nunca commite no código ou logs

**Geração segura:**

```python
import secrets

# Gerar chave de 32 bytes
encryption_key = secrets.token_urlsafe(32)
print(f"ENCRYPTION_KEY={encryption_key}")
```

**Armazenamento:**
- Armazene em variável de ambiente
- Use secret manager em produção (AWS Secrets Manager, HashiCorp Vault, etc.)
- Nunca logue ou imprima a chave

### AES-256 Encryption

O sistema usa AES-256-GCM para criptografar dados sensíveis:

- **Algoritmo**: AES-256 (Advanced Encryption Standard)
- **Modo**: GCM (Galois/Counter Mode) com autenticação
- **IV**: Gerado aleatoriamente para cada operação
- **Tag**: Autenticação integrada para detectar modificações

**Uso:**

```python
from crypto_bot.infrastructure.security.encryption import get_encryption_service

service = get_encryption_service()

# Criptografar
encrypted = service.encrypt("dado sensível")

# Descriptografar
decrypted = service.decrypt(encrypted)
```

## 📦 Proteção de Dados

### Dados Sensíveis

Os seguintes dados são tratados como sensíveis e **nunca logados em texto claro**:

- API keys e secrets
- Senhas de banco de dados
- Chaves de criptografia
- Tokens JWT
- Credenciais de notificações

### Máscara em Logs

O sistema automaticamente mascara dados sensíveis em logs:

```python
from crypto_bot.utils.logger import get_logger

logger = get_logger(__name__)

# Automaticamente mascara valores sensíveis
logger.info(f"API Key: {api_key}")  # Loga como: "API Key: ***REDACTED***"
logger.info(f"Password: {password}")  # Loga como: "Password: ***REDACTED***"
```

**Padrões mascarados automaticamente:**
- `*_key`, `*_secret`, `*_password`, `*_token`
- Valores que parecem chaves (strings longas base64)

### Sanitização de Dados

Sempre sanitize dados antes de exibir ou processar:

```python
def sanitize_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove dados sensíveis de um dict."""
    sensitive_keys = ["api_key", "api_secret", "password", "token"]
    sanitized = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = value
    return sanitized
```

## 🌐 Segurança de Rede

### HTTPS/SSL

**Sempre use HTTPS** para comunicações externas:

- ✅ Todas as APIs de exchanges suportam HTTPS
- ✅ Certificados SSL são validados automaticamente
- ✅ Conexões inseguras são bloqueadas

### Timeout e Retry

Configure timeouts apropriados para evitar conexões pendentes:

```python
# Timeouts configuráveis
request_timeout = 30  # segundos
connect_timeout = 10  # segundos

# Retry com backoff exponencial
max_retries = 3
initial_delay = 1.0
max_delay = 30.0
```

### Rate Limiting

Respeite rate limits das exchanges:

```python
# Configuração de rate limits
rate_limits = {
    "requests_per_second": 10,
    "orders_per_day": 200000,
}

# Semáforo para controlar concorrência
semaphore = asyncio.Semaphore(max_concurrent_requests)
```

## ✅ Validação de Entrada

### Validação Rigorosa

**Sempre valide** todas as entradas do usuário ou de APIs externas:

```python
from pydantic import BaseModel, Field, validator

class CreateOrderRequest(BaseModel):
    """Request validado para criar ordem."""
    
    symbol: str = Field(..., min_length=1, max_length=20)
    side: OrderSide
    type: OrderType
    quantity: Decimal = Field(..., gt=0)
    price: Decimal | None = Field(None, gt=0)
    
    @validator("symbol")
    def validate_symbol(cls, v):
        """Validar formato de símbolo."""
        if "/" not in v:
            raise ValueError("Symbol must be in format BASE/QUOTE")
        return v.upper()
    
    @validator("quantity")
    def validate_quantity(cls, v):
        """Validar quantidade."""
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v
```

### SQL Injection Prevention

Use sempre **parameterized queries** (SQLAlchemy faz isso automaticamente):

```python
# ✅ CORRETO (SQLAlchemy)
result = await session.execute(
    select(Order).where(Order.symbol == symbol)
)

# ❌ ERRADO (nunca faça isso)
result = await session.execute(
    f"SELECT * FROM orders WHERE symbol = '{symbol}'"  # Vulnerável!
)
```

### XSS Prevention

Para interfaces web (futuro), sempre escape dados do usuário:

```python
# Exemplo para futura interface web
from html import escape

def render_user_input(user_input: str) -> str:
    """Escapa input do usuário para prevenir XSS."""
    return escape(user_input)
```

## 📝 Logging Seguro

### Não Logue Dados Sensíveis

```python
# ✅ CORRETO
logger.info(f"Order created: symbol={symbol}, quantity={quantity}")

# ❌ ERRADO
logger.info(f"API Key: {api_key}, Secret: {secret}")  # NUNCA!
```

### Use Logging Estruturado

```python
from crypto_bot.utils.structured_logger import get_logger

logger = get_logger(__name__)

# Logging estruturado (dados sensíveis são mascarados automaticamente)
logger.info(
    "Order created",
    extra={
        "symbol": "BTC/USDT",
        "quantity": "0.001",
        "side": "buy",
        # api_key é automaticamente mascarado se presente
    },
)
```

### Níveis de Log Apropriados

```python
# DEBUG: Detalhes para desenvolvimento
logger.debug("Processing order with params", extra={"params": params})

# INFO: Eventos importantes do sistema
logger.info("Order created successfully", extra={"order_id": order_id})

# WARNING: Situações que requerem atenção
logger.warning("Rate limit approaching", extra={"remaining": remaining})

# ERROR: Erros que não impedem operação
logger.error("Failed to fetch ticker", exc_info=True)

# CRITICAL: Erros que impedem operação
logger.critical("Database connection lost", exc_info=True)
```

## 💻 Práticas de Desenvolvimento Seguro

### 1. Dependency Management

**Mantenha dependências atualizadas:**

```bash
# Verificar vulnerabilidades
pip-audit
safety check

# Atualizar dependências regularmente
pip list --outdated
pip install --upgrade <package>
```

**Use versões específicas:**

```txt
# requirements.txt
pydantic==2.5.0  # Versão específica, não ">=2.5.0"
ccxt==4.1.0
```

### 2. Secrets Scanning

**Use ferramentas para detectar credenciais no código:**

```bash
# gitleaks
gitleaks detect --source . --verbose

# truffleHog
trufflehog git file://. --json
```

**Integre no CI/CD:**

```yaml
# .github/workflows/security.yml
- name: Scan for secrets
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
```

### 3. Code Review

**Checklist de revisão de segurança:**

- [ ] Nenhuma credencial hardcoded
- [ ] Todas as entradas validadas
- [ ] Dados sensíveis mascarados em logs
- [ ] SQL injection prevenido
- [ ] Rate limiting implementado
- [ ] Timeouts configurados
- [ ] Tratamento de erros adequado
- [ ] Sem informações sensíveis em mensagens de erro

### 4. Dependency Injection

**Use injeção de dependências** para facilitar testes e segurança:

```python
# ✅ CORRETO
class TradingService:
    def __init__(self, encryption_service: EncryptionService):
        self._encryption = encryption_service
    
    async def create_order(self, request: CreateOrderRequest):
        # Usa encryption_service injetado
        pass

# ❌ ERRADO
class TradingService:
    def __init__(self):
        self._encryption = get_encryption_service()  # Acoplamento
```

## 🔐 Checklist de Segurança

### Setup Inicial

- [ ] `ENCRYPTION_KEY` gerado e configurado (32+ bytes)
- [ ] Arquivo `.env` criado (não commitado)
- [ ] `.env.example` atualizado (sem valores reais)
- [ ] API keys de exchanges configuradas
- [ ] Permissões de API keys limitadas (sem withdrawal)
- [ ] IP whitelist configurada (quando disponível)

### Configuração de Produção

- [ ] `dry_run: false` apenas em produção
- [ ] Logging em arquivo (não console)
- [ ] Nível de log apropriado (INFO/WARNING)
- [ ] Database credentials seguros
- [ ] Redis password configurado (se usado)
- [ ] HTTPS habilitado para todas as conexões
- [ ] Rate limiting configurado
- [ ] Timeouts configurados
- [ ] Monitoring e alertas configurados

### Desenvolvimento

- [ ] Nenhuma credencial no código
- [ ] Dados sensíveis mascarados em logs
- [ ] Todas as entradas validadas
- [ ] SQL injection prevenido
- [ ] Dependências atualizadas
- [ ] Vulnerabilidades escaneadas
- [ ] Testes de segurança executados
- [ ] Code review realizado

### Manutenção Contínua

- [ ] Rotação de credenciais (trimestral)
- [ ] Auditoria de acesso regular
- [ ] Logs revisados para anomalias
- [ ] Dependências atualizadas
- [ ] Vulnerabilidades monitoradas
- [ ] Backups de configurações
- [ ] Disaster recovery testado

## 🚨 Incident Response

### Se Credenciais Forem Comprometidas

1. **Imediatamente:**
   - Revogue API keys comprometidas nas exchanges
   - Gere nova `ENCRYPTION_KEY`
   - Re-criptografe todos os dados no banco
   - Rotacione senhas de banco de dados

2. **Analise:**
   - Revise logs para atividade suspeita
   - Verifique se ordens não autorizadas foram executadas
   - Documente o incidente

3. **Prevenção:**
   - Identifique como o comprometimento ocorreu
   - Implemente medidas preventivas
   - Atualize documentação de segurança

### Se Dados Forem Acessados Não Autorizadamente

1. **Contenção:**
   - Desabilite acesso comprometido
   - Isole sistemas afetados

2. **Análise:**
   - Determine escopo do acesso
   - Identifique dados acessados

3. **Notificação:**
   - Notifique partes afetadas se necessário
   - Documente incidente

## 📚 Referências

- [SECURITY_BASELINE.md](security/SECURITY_BASELINE.md)
- [HARDENING_GUIDE.md](security/HARDENING_GUIDE.md)
- [KEY_ROTATION_PLAYBOOK.md](security/KEY_ROTATION_PLAYBOOK.md)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/secrets.html)

## 🔄 Atualizações de Segurança

**Procedimento para atualizar este documento:**

1. Identifique nova vulnerabilidade ou melhor prática
2. Documente no documento apropriado
3. Atualize checklist de segurança
4. Notifique equipe de desenvolvimento
5. Implemente correções/medidas preventivas

---

**⚠️ Lembre-se**: Segurança não é um produto, é um processo contínuo. Revise e atualize regularmente!
