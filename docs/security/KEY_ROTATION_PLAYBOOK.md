# Key Rotation Playbook (2025)

Este documento descreve o procedimento para rotacionar chaves de criptografia do `crypto-bot` sem interrupção do serviço e com possibilidade de rollback seguro.

## Visão Geral

O sistema de criptografia suporta rotação suave de chaves através de:
- **Key Identifier (KID)**: Prefixo nas strings criptografadas (`v0:`, `v1:`, etc.)
- **Chave anterior**: Suportada via `ENCRYPTION_KEY_PREVIOUS`
- **Backward compatibility**: Dados antigos são descriptografados com a chave anterior quando necessário

**Tempo estimado**: 15-30 minutos (depende do volume de dados)

## Pré-requisitos

- Acesso ao ambiente de produção com permissão para modificar variáveis de ambiente
- Acesso ao banco de dados (opcional: para recriptografia batch)
- Backup completo do banco antes de iniciar a rotação
- Janela de manutenção sem operações críticas de trading

## Passos para Rotação

### 1) Preparar Nova Chave

```bash
# Gerar nova chave forte
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Exemplo de output: `2L4gR9xN8pQ3tV7wY6zA5bC1dE0fH2jK9`

**Nota**: Anote esta chave em local seguro e não commite no código!

### 2) Rotacionar Chaves no Ambiente (sem downtime)

```bash
# Definir nova chave como principal e antiga como PREVIOUS
ENCRYPTION_KEY="2L4gR9xN8pQ3tV7wY6zA5bC1dE0fH2jK9"  # Nova chave
ENCRYPTION_KEY_PREVIOUS="antiga_chave_aqui"  # Chave que estava ativa
```

**Importante**: O sistema suporta descriptografar com qualquer uma das duas chaves.

### 3) Verificar Operação Normal

```bash
# Testar descriptografia com dados existentes
pytest tests/integration/test_encrypted_models.py -v
```

**Monitoramento**: Verifique logs por 5-10 minutos para garantir que não há erros de descriptografia.

### 4) Recriptografar Dados Legacy (Opcional)

Se você tem muitos dados criptografados com a chave anterior e quer convertê-los para a nova:

```python
# Script de exemplo para recriptografia batch
# Criar: scripts/re-encrypt-secrets.py
from crypto_bot.infrastructure.database.session import get_session
from crypto_bot.infrastructure.database.models.exchange import Exchange
from sqlalchemy import select
import asyncio


async def re_encrypt_exchanges():
    """Recriptografa credenciais de exchanges para usar nova chave."""
    async for session in get_session():
        exchanges = await session.execute(select(Exchange))
        for exchange in exchanges.scalars():
            # Forçar re-criptografia lendo e reescrevendo
            if exchange.api_key_encrypted:
                # A descriptografia já ocorre automaticamente
                temp_key = exchange.api_key_encrypted
                temp_secret = exchange.api_secret_encrypted
                exchange.api_key_encrypted = None  # Reset
                exchange.api_secret_encrypted = None
                exchange.api_key_encrypted = temp_key  # Re-criptografa com nova chave
                exchange.api_secret_encrypted = temp_secret
                await session.commit()
        break  # Uma sessão é suficiente


if __name__ == "__main__":
    asyncio.run(re_encrypt_exchanges())
```

**Nota**: Execute apenas após verificar que a rotação simples está funcionando corretamente.

### 5) Remover Chave Anterior Após Período de Observação

Após 30-60 dias de operação normal sem necessidade de decryptar com a chave anterior:

```bash
# Remover chave anterior da configuração
ENCRYPTION_KEY="2L4gR9xN8pQ3tV7wY6zA5bC1dE0fH2jK9"  # Nova chave (mantém como principal)
# ENCRYPTION_KEY_PREVIOUS=""  # Não definida (remover)
```

**Segurança**: Mantenha a chave anterior em um arquivo seguro (criptografado) por 90 dias após remoção, para casos de recuperação.

## Rollback (Emergência)

Se houver problemas com a nova chave:

```bash
# Reverter para chave original
ENCRYPTION_KEY="antiga_chave"  # Voltar ao valor original
ENCRYPTION_KEY_PREVIOUS=""  # Remover anterior
```

O sistema voltará a descriptografar dados antigos normalmente.

## Checklist de Segurança

- [ ] Backup completo do banco antes da rotação
- [ ] Nova chave forte gerada (32+ caracteres)
- [ ] Chave antiga preservada como `ENCRYPTION_KEY_PREVIOUS`
- [ ] Testes de descriptografia bem-sucedidos
- [ ] Monitoramento de logs ativo durante período de observação
- [ ] Chave antiga arquivada de forma segura (criptografada) por 90 dias
- [ ] Documentação atualizada com nova chave (em lugar seguro, não no código)

## Integração com Vault

Para ambientes que usam vault (HashiCorp, AWS Secrets Manager, etc.):

1. **Armazenar nova chave no vault** com path: `crypto-bot/encryption-keys/v2`
2. **Manter chave antiga** em path: `crypto-bot/encryption-keys/v1` (read-only)
3. **Atualizar aplicação** para ler `ENCRYPTION_KEY` do vault
4. **Após período de observação**, remover permissão de leitura para `v1`

## Referências Técnicas

- `EncryptionService`: Implementa rotação suave via KID e suporte a `ENCRYPTION_KEY_PREVIOUS`
- `EncryptedString`: Type decorator do SQLAlchemy que aplica cifragem transparente
- Campos criptografados em `Exchange`: `api_key_encrypted`, `api_secret_encrypted`
- Testes: `tests/integration/test_encrypted_models.py`

---

**Última atualização**: 2025-10-28  
**Autor**: Security Team  
**Próxima revisão**: Após primeiro uso em produção

