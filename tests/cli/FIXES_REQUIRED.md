# 🔧 Correções Necessárias para CLI

**Data:** 2025-11-01  
**Status:** 🟡 Algumas correções necessárias para ambiente completo

## 🚨 Ações Obrigatórias (Críticas)

### 1. ✅ Aplicar Database Migrations

**Problema:** Tabelas do banco de dados não existem, causando erros em comandos que acessam DB.

**Comandos Afetados:**
- `strategies` - ❌ Falha se tabela `strategy` não existe
- `positions` - ❌ Falha se tabela `position` não existe  
- `force` - ❌ Falha se tabela `strategy` não existe

**Solução:**
```bash
# Verificar se database existe
psql -l | grep crypto_bot

# Se não existe, criar:
createdb crypto_bot

# Aplicar todas as migrations
alembic upgrade head

# Verificar migrations aplicadas
alembic current
```

**Verificação:**
```bash
# Testar se comandos funcionam agora
python -m crypto_bot.cli.main strategies
python -m crypto_bot.cli.main positions
```

---

## 💡 Melhorias Recomendadas (Opcional)

### 2. Melhorar Mensagens de Erro para `balances`

**Arquivo:** `src/crypto_bot/cli/main.py`  
**Função:** `balances()` → `_get_balances()`

**Mudança Sugerida:**
```python
except Exception as e:
    if "not configured" in str(e).lower():
        console.print(f"[red]❌ Exchange '{exchange}' não está configurado[/red]")
        console.print("\n[yellow]💡 Para configurar:[/yellow]")
        console.print("   1. Arquivo de configuração:")
        console.print(f"      config/environments/development.yaml")
        console.print("   2. Variáveis de ambiente:")
        console.print(f"      export {exchange.upper()}_API_KEY=your_key")
        console.print(f"      export {exchange.upper()}_API_SECRET=your_secret")
        console.print("\n[dim]Para testnet, configure sandbox: true[/dim]")
    else:
        console.print(f"[red]❌ Erro ao obter saldos: {e}[/red]")
    logger.error("balances_command_error", exc_type=type(e).__name__, exc_msg=str(e), exchange=exchange)
```

### 3. Adicionar Sugestão em `force` quando estratégia não encontrada

**Arquivo:** `src/crypto_bot/cli/main.py`  
**Função:** `force()` → `_force_execution()`

**Mudança Sugerida:**
```python
if not strategy:
    console.print(f"[red]❌ Estratégia não encontrada: {strategy_id}[/red]")
    console.print("[yellow]💡 Use 'crypto-bot strategies' para listar estratégias disponíveis[/yellow]")
    return
```

### 4. Adicionar Verificação de Database em `status`

**Arquivo:** `src/crypto_bot/cli/main.py`  
**Função:** `status()` → `_get_status()`

**Mudança Sugerida:**
```python
async def _get_status() -> None:
    async with cli_context.get_session():
        try:
            # Verificar conexão com database
            strategy_repo = await cli_context.get_strategy_repository()
            active_strategies = await strategy_repo.get_active_strategies()
            
            # ... resto do código ...
            
        except Exception as e:
            if "does not exist" in str(e):
                console.print("[red]❌ Tabelas do banco não existem![/red]")
                console.print("[yellow]💡 Execute: alembic upgrade head[/yellow]")
            else:
                console.print(f"[red]Erro: {e}[/red]")
            logger.error("status_command_error", exc_type=type(e).__name__, exc_msg=str(e))
```

---

## 📋 Checklist de Verificação

Execute os seguintes comandos para verificar se tudo está funcionando:

```bash
# 1. Database setup
alembic upgrade head

# 2. Testar comandos básicos
python -m crypto_bot.cli.main --help
python -m crypto_bot.cli.main --version

# 3. Testar comandos que precisam de DB
python -m crypto_bot.cli.main strategies
python -m crypto_bot.cli.main positions

# 4. Testar comando que precisa de exchange configurado
python -m crypto_bot.cli.main balances --exchange binance
# Esperado: Erro mas com mensagem melhorada (após aplicar melhorias)

# 5. Testar comando de logs
python -m crypto_bot.cli.main logs --lines 5
```

---

## ✅ Status Atual

- ✅ **18/18 comandos básicos testados** - Todos passam nos testes de sintaxe
- ⚠️ **3 comandos precisam de database** - Requerem migrations aplicadas
- ⚠️ **1 comando precisa de exchange configurado** - Funciona mas mensagem pode melhorar
- ✅ **Tratamento de erros implementado** - Nenhum crash, apenas mensagens de erro

---

## 🎯 Prioridade de Correções

1. **🔴 ALTA:** Aplicar migrations do Alembic (`alembic upgrade head`)
2. **🟡 MÉDIA:** Melhorar mensagens de erro (opcional, mas melhora UX)
3. **🟢 BAIXA:** Adicionar comando `diagnose` para verificar setup (futuro)

---

**Última Atualização:** 2025-11-01

