# Task Master AI - Configuração Local

Este projeto usa o Task Master AI para gerenciamento de tarefas. Os arquivos de controle são mantidos localmente para evitar conflitos de merge.

## 📁 Arquivos Excluídos do Controle de Versão

Os seguintes arquivos são mantidos apenas localmente:

- `.taskmaster/tasks/tasks.json` - Estado atual das tarefas
- `.taskmaster/state.json` - Estado do sistema
- `.taskmaster/cache/` - Cache local
- `.taskmaster/logs/` - Logs locais
- `.taskmaster/reports/` - Relatórios locais

## 🚀 Configuração Inicial

1. **Instalar Task Master AI:**
   ```bash
   npm install -g task-master-ai
   ```

2. **Inicializar o projeto:**
   ```bash
   task-master init
   ```

3. **Criar tasks a partir do PRD:**
   ```bash
   task-master parse-prd REQUISITOS.md
   ```

## 📋 Comandos Úteis

- `task-master list` - Listar todas as tarefas
- `task-master next` - Mostrar próxima tarefa
- `task-master show <id>` - Mostrar detalhes de uma tarefa
- `task-master expand <id>` - Expandir tarefa em subtarefas
- `task-master set-status <id> <status>` - Alterar status da tarefa

## 🔄 Workflow

1. Use `task-master next` para identificar a próxima tarefa
2. Implemente a tarefa
3. Use `task-master set-status <id> done` para marcar como concluída
4. Continue com a próxima tarefa

## 📝 Notas

- Cada desenvolvedor mantém seu próprio estado de tarefas
- Não há sincronização automática entre desenvolvedores
- Use branches do Git para coordenar trabalho em equipe
- O arquivo `tasks.json` é recriado automaticamente quando necessário
