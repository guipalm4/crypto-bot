# 🤖 Fluxo de Desenvolvimento Automatizado

## 📋 Visão Geral

Este projeto utiliza um fluxo de trabalho automatizado que integra:
- **Task Master AI** para gerenciamento de tarefas
- **Git** para controle de versão
- **GitHub** para colaboração e revisão de código
- **Conventional Commits** para padronização

## 🚀 Comandos Principais

### Iniciar Desenvolvimento
```bash
# Inicia próxima tarefa disponível
git task-next

# Inicia tarefa específica
git task-start 6
```

### Completar Tarefa
```bash
# Completa tarefa (commit + PR)
git task-complete 6
```

### Comandos Manuais
```bash
# Apenas commit e PR
git dev-commit 6

# Apenas criar PR
git dev-pr 6

# Listar tarefas
git task-list

# Status das tarefas
git task-status
```

## 🔄 Fluxo Completo

1. **Iniciar**: `git task-next`
   - Cria branch baseado na tarefa
   - Marca tarefa como "in-progress"
   - Configura ambiente de desenvolvimento

2. **Desenvolver**: Implementar funcionalidade
   - Seguir padrões de código
   - Escrever testes
   - Atualizar documentação

3. **Completar**: `git task-complete 6`
   - Faz commit convencional
   - Cria Pull Request
   - Marca tarefa como "review"

4. **Revisar**: Code review no GitHub
   - Aprovar mudanças
   - Fazer merge
   - Marcar tarefa como "done"

## 📝 Convenções

### Nomenclatura de Branches
```
feature/task-{id}-{title}
Exemplo: feature/task-6-project-structure-setup
```

### Commits Convencionais
```
type(scope): description

Tipos: feat, fix, docs, style, refactor, test, chore, config
Exemplo: feat(task-6): implement project structure setup
```

### Pull Requests
- Título: `[Task #6] 🏗️ Project Structure & Environment Setup`
- Template automático com critérios de aceitação
- Labels automáticos: `task`, `in-progress`, `ready-for-review`

## 🛠️ Configuração

### Instalação
```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar fluxo de trabalho
python scripts/setup-dev-workflow.py

# Configurar Git hooks
python scripts/setup-git-hooks.py
```

### Verificação
```bash
# Verificar configuração
git task-status
git dev-status
```

## 📚 Recursos

- [Task Master AI](https://github.com/guipalm4/crypto-bot)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub CLI](https://cli.github.com/)
- [Git Hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
