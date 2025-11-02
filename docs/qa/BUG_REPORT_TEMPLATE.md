# 🐛 Template de Bug Report

Use este template para documentar bugs encontrados durante os testes manuais de QA.

## 📋 Informações Básicas

**ID do Bug**: `BUG-XXX` (será atribuído automaticamente)  
**Data**: `YYYY-MM-DD HH:MM:SS`  
**Tester**: `Nome do QA`  
**Severidade**: `[CRITICAL | HIGH | MEDIUM | LOW]`  
**Prioridade**: `[P0 | P1 | P2 | P3]`  
**Status**: `[OPEN | IN_PROGRESS | RESOLVED | CLOSED]`  
**Componente**: `[CLI | Exchange | Strategy | Risk | Config | Security | Other]`

---

## 📝 Descrição do Bug

**Título Resumido**:  
Breve descrição do problema em uma linha

**Descrição Detalhada**:  
Descrição completa do problema encontrado, incluindo contexto e impacto.

---

## 🔄 Passos para Reproduzir

1. Passo 1
2. Passo 2
3. Passo 3
4. ...

**Dados de Entrada** (se aplicável):  
- Campo 1: Valor
- Campo 2: Valor

**Ambiente de Teste**:  
- Sistema Operacional: 
- Python Version: 
- Versão do Bot: 
- Exchange(s) testado(s): 
- Configurações relevantes:

---

## ✅ Comportamento Esperado

Descrição clara do que deveria acontecer.

---

## ❌ Comportamento Atual

Descrição do que está acontecendo atualmente (comportamento incorreto).

---

## 📸 Evidências

### Screenshots/Logs
```
[Incluir screenshots, logs ou mensagens de erro aqui]
```

### Stack Trace (se aplicável)
```python
Traceback (most recent call last):
  ...
```

### Logs Relevantes
```
[Logs do sistema relacionados ao bug]
```

---

## 🔍 Análise Técnica

**Onde o bug ocorre**:  
- Arquivo(s): `src/crypto_bot/...`
- Função(s): `nome_da_funcao()`
- Linha(s) aproximadas:

**Causa Raiz Provável**:  
Análise técnica da possível causa do problema.

**Impacto**:  
- Quantos usuários são afetados?
- Qual funcionalidade está quebrada?
- Existe workaround?

---

## 🔗 Referências

**GitHub Issue**: `#XXX`  
**Task Master**: `Task #XX`  
**Teste Relacionado**: `tests/manual_qa/.../test_xxx.py`

---

## ✅ Critérios de Aceitação (Resolução)

- [ ] Bug reproduzido e confirmado
- [ ] Causa raiz identificada
- [ ] Correção implementada
- [ ] Testes automatizados adicionados/atualizados
- [ ] Bug re-testado e validado
- [ ] Documentação atualizada (se necessário)

---

## 📝 Notas Adicionais

Qualquer informação adicional relevante para entender ou resolver o bug.

---

## 🏷️ Tags

`bug`, `componente`, `severidade`, `prioridade`, `mvp`, `qa-manual`

