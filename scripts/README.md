# 🛠️ Scripts de Configuração

## 📋 setup_milestones.py

Script para criar automaticamente as milestones no GitHub baseadas no planejamento do Task Master AI.

### 🚀 Como Executar

1. **Configure o token do GitHub**:
   ```bash
   export GITHUB_TOKEN=seu_token_github_aqui
   ```

2. **Execute o script**:
   ```bash   cd scripts
   python setup_milestones.py
   ```

### 🔑 Como Obter o Token do GitHub

1. Acesse: https://github.com/settings/tokens
2. Clique em "Generate new token" → "Generate new token (classic)"
3. Dê um nome ao token (ex: "crypto-bot-setup")
4. Selecione os escopos:
   - ✅ `repo` (acesso completo aos repositórios)
   - ✅ `public_repo` (acesso a repositórios públicos)
5. Clique em "Generate token"
6. Copie o token e configure a variável de ambiente

### 📊 O que o Script Faz

1. **Cria 5 milestones** baseadas no planejamento:
   - 🏗️ Sprint 1: Foundation & Core Infrastructure
   - 🚀 Sprint 2: Core Trading Engine & Risk Management
   - 🔌 Sprint 3: Exchange Integration & Plugin System
   - 🎯 Sprint 4: Trading Strategies & Orchestration
   - 🎨 Sprint 5: User Interface & Final Polish

2. **Associa as issues** às milestones correspondentes

3. **Define datas limite** para cada sprint

### 🎯 Milestones Criadas

| Milestone | Issues | Data Limite |
|-----------|--------|-------------|
| Sprint 1 | #6, #7, #8 | 2025-11-01 |
| Sprint 2 | #9, #10 | 2025-11-22 |
| Sprint 3 | #11, #12 | 2025-12-13 |
| Sprint 4 | #13 | 2026-01-03 |
| Sprint 5 | #14 | 2026-01-17 |

### 🔧 Dependências

```bash
pip install requests
```

### 📝 Notas

- O script usa a API v3 do GitHub
- Requer token com permissões de repositório
- As issues #1-5 são milestones antigas (podem ser fechadas)
- Verifique o resultado em: https://github.com/guipalm4/crypto-bot/milestones
