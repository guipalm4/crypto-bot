# 🚀 Workflow de Desenvolvimento - Detalhado

## 📋 Visão Geral

O workflow de desenvolvimento foi completamente reformulado para garantir que **Task Master seja sempre a prioridade #1**, com todas as outras ferramentas funcionando como suporte, nunca como substitutos.

## 🎯 Hierarquia de Prioridades

```
1. 🥇 TASK MASTER (PRIORIDADE ABSOLUTA)
   ├── 2. 🥈 Context7 (Pesquisa e melhores práticas)
   ├── 3. 🥉 Git (Controle de versão - se usado)
   ├── 4. 🏅 GitHub Templates (Templates - se usando Git)
   └── 5. 🏅 Code Quality (Linting, formatação, testes)
```

## 🔄 Workflow Completo de Desenvolvimento

### **FASE 1: INICIALIZAÇÃO** 🚀

#### 1.1 Verificar Status do Task Master
```bash
# SEMPRE começar aqui - PRIORIDADE #1
task-master next
# OU usar MCP tool: next_task
```

#### 1.2 Entender a Tarefa Ativa
```bash
# Obter detalhes completos da tarefa
task-master show <task-id>
# OU usar MCP tool: get_task
```

#### 1.3 Expandir Tarefas Complexas (se necessário)
```bash
# Quebrar tarefas complexas em subtarefas
task-master expand --id=<task-id> --research
# OU usar MCP tool: expand_task
```

### **FASE 2: PESQUISA E CONTEXTUALIZAÇÃO** 🔍

#### 2.1 Pesquisa com Context7 (OBRIGATÓRIA)
```bash
# Pesquisar melhores práticas atuais
Context7: "What are the latest best practices for [technology] in 2024?"
Context7: "Are there any deprecated patterns in [library] that I should avoid?"
```

#### 2.2 Pesquisa com Task Master (OBRIGATÓRIA)
```bash
# Pesquisa com contexto do projeto
task-master research "query with project context"
# OU usar MCP tool: research
```

#### 2.3 Documentar Pesquisa
```bash
# Logar descobertas na subtarefa
task-master update-subtask --id=<subtask-id> --prompt="Research findings..."
# OU usar MCP tool: update_subtask
```

### **FASE 3: PREPARAÇÃO DO AMBIENTE** ⚙️

#### 3.1 Verificar Branch Git (se usando Git)
```bash
git branch --show-current
# Deve NÃO ser 'main' ou 'master'
```

#### 3.2 Criar Branch de Feature (se necessário)
```bash
# Se estiver no main/master, criar branch
git checkout -b feature/task-<id>-<description>
```

#### 3.3 Marcar Tarefa como "In Progress"
```bash
# Marcar subtarefa como em progresso
task-master set-status --id=<subtask-id> --status=in-progress
# OU usar MCP tool: set_task_status
```

### **FASE 4: IMPLEMENTAÇÃO** 💻

#### 4.1 Implementar Seguindo Padrões Pesquisados
- Seguir práticas descobertas no Context7
- Aplicar padrões específicos do projeto
- Implementar com base na pesquisa do Task Master

#### 4.2 Atualizar Progresso Regularmente
```bash
# Logar progresso e descobertas
task-master update-subtask --id=<subtask-id> --prompt="Progress update..."
# OU usar MCP tool: update_subtask
```

#### 4.3 Executar Quality Checks
```bash
# Executar antes de cada commit
black --check .
flake8 .
mypy .
pytest
```

### **FASE 5: COMMIT E VERSIONAMENTO** 📝

#### 5.1 Fazer Commit (se usando Git)
```bash
# Commit com mensagem descritiva
git add .
git commit -m "feat(scope): description based on task <id>"
```

#### 5.2 Push da Branch (se usando Git)
```bash
# Enviar branch para repositório remoto
git push origin feature/task-<id>-<description>
```

### **FASE 6: PULL REQUEST** 🔄

#### 6.1 Criar Pull Request (se usando Git)
```bash
# Usar template do GitHub
gh pr create --title "[Task #<id>] Description" --body-file .github/pull_request_template.md
```

#### 6.2 Preencher Template Completamente
- ✅ Descrição detalhada das mudanças
- ✅ Referência à tarefa do Task Master
- ✅ Checklist de segurança
- ✅ Checklist de performance
- ✅ Instruções de teste

### **FASE 7: FINALIZAÇÃO** ✅

#### 7.1 Marcar Subtarefa como Concluída
```bash
# Marcar subtarefa como done
task-master set-status --id=<subtask-id> --status=done
# OU usar MCP tool: set_task_status
```

#### 7.2 Verificar Tarefa Principal
```bash
# Verificar se todas as subtarefas estão concluídas
task-master show <task-id>
# OU usar MCP tool: get_task
```

#### 7.3 Marcar Tarefa Principal como Concluída (se aplicável)
```bash
# Se todas as subtarefas estiverem done
task-master set-status --id=<task-id> --status=done
# OU usar MCP tool: set_task_status
```

#### 7.4 Atualizar Tarefas Dependentes (se necessário)
```bash
# Se a implementação mudou outras tarefas
task-master update --from=<task-id> --prompt="Implementation changes..."
# OU usar MCP tool: update
```

## 🚨 Regras Críticas de Enforcamento

### **NUNCA FAZER:**
- ❌ Bypass do Task Master workflow
- ❌ Implementar sem tarefa ativa no Task Master
- ❌ Pular pesquisa com Context7
- ❌ Commitar diretamente no main/master
- ❌ Pular quality checks
- ❌ Pular atualizações de progresso no Task Master

### **SEMPRE FAZER:**
- ✅ Começar com Task Master (`next_task`)
- ✅ Pesquisar com Context7 + Task Master research
- ✅ Atualizar progresso regularmente (`update_subtask`)
- ✅ Executar quality checks antes de commitar
- ✅ Usar templates do GitHub (se usando Git)
- ✅ Marcar tarefas como concluídas (`set_task_status`)

## 🔧 Ferramentas e Comandos

### **Task Master (PRIORIDADE #1)**
```bash
# Comandos essenciais
task-master next                    # Próxima tarefa
task-master show <id>              # Detalhes da tarefa
task-master expand --id=<id>       # Expandir tarefa
task-master update-subtask --id=<id> --prompt="..."  # Atualizar progresso
task-master set-status --id=<id> --status=done      # Marcar como concluída
task-master research "query"       # Pesquisa com contexto
```

### **Context7 (PRIORIDADE #2)**
```bash
# Pesquisas obrigatórias antes de implementar
- "What are the latest best practices for [technology] on [version] in 2025?"
- "Are there any deprecated patterns in [library] that I should avoid?"
- "What are the security best practices for [use case]?"
- "What are the performance considerations for [implementation]?"
```

### **Git (PRIORIDADE #3 - se usado)**
```bash
# Workflow Git obrigatório
git branch --show-current          # Verificar branch atual
git checkout -b feature/task-<id>  # Criar branch de feature
git add .                          # Adicionar mudanças
git commit -m "feat(scope): desc"  # Commit descritivo
git push origin feature/task-<id>  # Push da branch
gh pr create --title "..."         # Criar Pull Request
```

### **Code Quality (SEMPRE OBRIGATÓRIO)**
```bash
# Quality checks obrigatórios
black --check .                    # Formatação
flake8 .                          # Linting
mypy .                            # Type checking
pytest                            # Testes
```

## 📊 Quality Gates

### **Antes de Implementar:**
- [ ] Task Master task ativa e compreendida
- [ ] Context7 research completada
- [ ] Task Master research completada
- [ ] Branch de feature criada (se usando Git)

### **Durante Implementação:**
- [ ] Progresso logado regularmente no Task Master
- [ ] Padrões pesquisados sendo seguidos
- [ ] Quality checks executados

### **Antes de Commitar:**
- [ ] Todos os quality checks passando
- [ ] Código formatado com Black
- [ ] Linting sem erros
- [ ] Type hints corretos
- [ ] Testes passando

### **Antes de Finalizar:**
- [ ] Task Master task marcada como done
- [ ] Tarefas dependentes atualizadas (se necessário)
- [ ] Documentação atualizada
- [ ] PR criado e template preenchido (se usando Git)

## 🎯 Benefícios do Workflow

### **Para o Desenvolvimento:**
- ✅ **Continuidade garantida** através do Task Master
- ✅ **Qualidade de código** através de pesquisa e quality checks
- ✅ **Rastreabilidade completa** de progresso e decisões
- ✅ **Padrões atualizados** através do Context7
- ✅ **Documentação automática** através de templates

### **Para o Projeto:**
- ✅ **Nunca perder o fio da meada** - Task Master mantém contexto
- ✅ **Código sempre atualizado** - Context7 garante práticas atuais
- ✅ **Qualidade consistente** - Quality gates obrigatórios
- ✅ **Histórico completo** - Logs detalhados no Task Master
- ✅ **Colaboração eficiente** - Templates e padrões claros

## 🚀 Próximos Passos

1. **Seguir o workflow** em todas as próximas tarefas
2. **Usar Task Master** como ponto de partida sempre
3. **Pesquisar com Context7** antes de implementar
4. **Manter qualidade** através dos quality gates
5. **Documentar tudo** através dos templates

---

**⚠️ LEMBRE-SE:** Task Master é a prioridade absoluta. Todas as outras ferramentas existem para apoiar o Task Master, nunca para substituí-lo!
