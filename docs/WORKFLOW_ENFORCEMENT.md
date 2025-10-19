# 🛡️ Workflow Enforcement - Como Prevenir Commits Diretos na Main

Este guia mostra como configurar proteções para **forçar o uso correto do workflow** e evitar commits diretos na branch `main`.

## 🎯 Objetivo

Garantir que:
- ✅ Todos os commits passem por uma branch de feature
- ✅ Todas as mudanças sejam revisadas via Pull Request
- ✅ CI/CD seja executado antes do merge
- ✅ Ninguém (nem eu!) possa commitar direto na main

---

## 🔧 Solução 1: Branch Protection no GitHub (Recomendado)

### Configuração Manual

1. Acesse: https://github.com/guipalm4/crypto-bot/settings/branches
2. Clique em **"Add branch protection rule"**
3. Configure:

```yaml
Branch name pattern: main

✅ Require pull request before merging
   ✅ Require approvals: 1 (pode ser você mesmo)
   ✅ Dismiss stale pull request approvals when new commits are pushed

✅ Require status checks to pass before merging
   ✅ Require branches to be up to date before merging
   Status checks:
   - validate-config
   - validate-templates
   - validate-taskmaster
   - validate-cursor
   - validate-config-files

✅ Require conversation resolution before merging

✅ Include administrators (IMPORTANTE!)
   # Isso te impede de burlar as regras

✅ Allow force pushes: Specify who can force push
   # Deixe vazio para ninguém
```

4. Clique em **"Create"**

### Por que isso funciona?

- 🚫 **Bloqueia push direto** para main
- ✅ **Força PR** para qualquer mudança
- 🧪 **CI/CD obrigatório** antes do merge
- 👥 **Review obrigatório** (pode ser auto-review)

---

## 🔧 Solução 2: Git Hook Local (Pre-push)

Crie um hook que **bloqueia push** para main localmente.

### Instalação

```bash
# Criar o hook
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
# Pre-push hook to prevent direct pushes to main/master

protected_branches=("main" "master")
current_branch=$(git symbolic-ref HEAD | sed -e 's,.*/\(.*\),\1,')

for branch in "${protected_branches[@]}"; do
    if [ "$current_branch" = "$branch" ]; then
        echo "🚫 ERROR: Direct push to '$branch' is not allowed!"
        echo ""
        echo "📋 Correct workflow:"
        echo "  1. Create a feature branch: git checkout -b feature/task-X-description"
        echo "  2. Make your changes and commit"
        echo "  3. Push the feature branch: git push origin feature/task-X-description"
        echo "  4. Create a Pull Request on GitHub"
        echo ""
        echo "💡 Quick fix if you already committed:"
        echo "  git branch feature/task-X-description  # Create branch at current commit"
        echo "  git reset --hard origin/main           # Reset main to remote"
        echo "  git checkout feature/task-X-description # Switch to feature branch"
        echo "  git push origin feature/task-X-description # Push feature branch"
        echo ""
        exit 1
    fi
done

exit 0
EOF

# Tornar executável
chmod +x .git/hooks/pre-push

echo "✅ Pre-push hook installed!"
```

### Testar

```bash
# Tentar push na main (deve falhar)
git checkout main
echo "test" >> test.txt
git add test.txt
git commit -m "test"
git push origin main
# 🚫 ERROR: Direct push to 'main' is not allowed!

# Workflow correto
git reset HEAD~1  # Desfazer último commit
git checkout -b feature/test
git add test.txt
git commit -m "test"
git push origin feature/test  # ✅ Funciona!
```

---

## 🔧 Solução 3: Git Alias para Workflow Automático

Adicione aliases que **automatizam o workflow correto**.

### Configuração

```bash
# Adicionar ao ~/.gitconfig ou executar:

# Criar branch automaticamente baseada na task
git config --global alias.task-branch '!f() { \
    task_id=$(task-master next | grep "ID:" | awk "{print \$2}"); \
    task_name=$(task-master next | grep "Title:" | awk "{print \$2}" | tr "[:upper:]" "[:lower:]" | tr " " "-"); \
    branch_name="feature/task-${task_id}-${task_name}"; \
    git checkout -b "$branch_name"; \
    echo "✅ Created branch: $branch_name"; \
}; f'

# Commit e push automático com validação
git config --global alias.task-push '!f() { \
    current_branch=$(git symbolic-ref --short HEAD); \
    if [[ "$current_branch" == "main" ]] || [[ "$current_branch" == "master" ]]; then \
        echo "🚫 ERROR: Cannot push from main/master branch!"; \
        echo "Use: git task-branch"; \
        exit 1; \
    fi; \
    git push origin "$current_branch"; \
}; f'

# Criar PR automaticamente
git config --global alias.task-pr '!f() { \
    gh pr create --fill; \
}; f'
```

### Uso

```bash
# 1. Ver próxima task
task-master next

# 2. Criar branch automaticamente
git task-branch
# ✅ Created branch: feature/task-2-database-schema

# 3. Desenvolver...
# ... código ...

# 4. Commit
git add .
git commit -m "feat(task-2): implement database schema"

# 5. Push (com validação)
git task-push

# 6. Criar PR
git task-pr
```

---

## 🔧 Solução 4: Script de Workflow Automático

Crie um script que **integra tudo**.

### Script

```bash
#!/bin/bash
# scripts/workflow.sh - Workflow automation

set -e

command=$1
shift

case "$command" in
    start)
        # Iniciar nova task
        task_info=$(task-master next)
        task_id=$(echo "$task_info" | grep "ID:" | awk '{print $2}')
        task_title=$(echo "$task_info" | grep "Title:" | awk -F: '{print $2}' | xargs | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
        
        branch_name="feature/task-${task_id}-${task_title}"
        
        # Verificar se está na main
        current_branch=$(git symbolic-ref --short HEAD)
        if [[ "$current_branch" != "main" ]]; then
            echo "⚠️  Warning: Not on main branch. Switch to main first?"
            read -p "Switch to main? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                git checkout main
                git pull origin main
            fi
        fi
        
        git checkout -b "$branch_name"
        echo "✅ Started work on Task #${task_id}"
        echo "📋 Branch: $branch_name"
        ;;
        
    finish)
        # Finalizar task
        current_branch=$(git symbolic-ref --short HEAD)
        
        if [[ "$current_branch" == "main" ]] || [[ "$current_branch" == "master" ]]; then
            echo "🚫 ERROR: Cannot finish from main/master branch!"
            exit 1
        fi
        
        # Extract task ID from branch name
        task_id=$(echo "$current_branch" | grep -oP 'task-\K\d+')
        
        if [[ -z "$task_id" ]]; then
            echo "⚠️  Warning: Could not extract task ID from branch name"
            read -p "Enter task ID manually: " task_id
        fi
        
        # Push branch
        git push origin "$current_branch"
        
        # Create PR
        gh pr create --title "[Task #${task_id}] $(echo $current_branch | sed 's/feature\/task-[0-9]*-//' | tr '-' ' ')" \
                     --body "Closes Task #${task_id}" \
                     --base main
        
        echo "✅ PR created for Task #${task_id}"
        ;;
        
    *)
        echo "Usage: $0 {start|finish}"
        echo ""
        echo "Commands:"
        echo "  start  - Start new task (creates branch from Task Master)"
        echo "  finish - Finish task (push + create PR)"
        exit 1
        ;;
esac
```

### Instalação

```bash
# Criar script
mkdir -p scripts
cat > scripts/workflow.sh << 'SCRIPT'
[... conteúdo do script acima ...]
SCRIPT

# Tornar executável
chmod +x scripts/workflow.sh

# Criar alias
echo 'alias task-start="./scripts/workflow.sh start"' >> ~/.zshrc
echo 'alias task-finish="./scripts/workflow.sh finish"' >> ~/.zshrc
source ~/.zshrc
```

### Uso

```bash
# Iniciar nova task
task-start
# ✅ Started work on Task #2
# 📋 Branch: feature/task-2-database-schema

# Desenvolver...
# ... código ...

# Finalizar task
git add .
git commit -m "feat(task-2): implement database schema"
task-finish
# ✅ PR created for Task #2
```

---

## 📋 Checklist de Implementação

Execute nesta ordem:

- [ ] **1. Branch Protection no GitHub** (mais importante!)
  ```bash
  # Configure manualmente no GitHub
  https://github.com/guipalm4/crypto-bot/settings/branches
  ```

- [ ] **2. Install Pre-push Hook**
  ```bash
  cat > .git/hooks/pre-push << 'EOF'
  [... código do hook ...]
  EOF
  chmod +x .git/hooks/pre-push
  ```

- [ ] **3. Git Aliases**
  ```bash
  git config --global alias.task-branch '!f() { ... }; f'
  git config --global alias.task-push '!f() { ... }; f'
  git config --global alias.task-pr '!f() { ... }; f'
  ```

- [ ] **4. Workflow Script**
  ```bash
  chmod +x scripts/workflow.sh
  alias task-start="./scripts/workflow.sh start"
  alias task-finish="./scripts/workflow.sh finish"
  ```

- [ ] **5. Teste o Sistema**
  ```bash
  # Tentar push direto na main (deve falhar)
  git checkout main
  echo "test" >> test.txt
  git add test.txt
  git commit -m "test"
  git push origin main  # 🚫 Deve falhar!
  ```

---

## 🎯 Workflow Recomendado

```bash
# 1. Ver próxima task
task-master next

# 2. Iniciar work
task-start  # ou: git task-branch

# 3. Desenvolver
# ... código ...

# 4. Commit
git add .
git commit -m "feat(task-X): description"

# 5. Finalizar
task-finish  # ou: git task-push && git task-pr

# 6. Merge no GitHub após aprovação
```

---

## 🆘 Troubleshooting

### Já commitei na main, e agora?

```bash
# Mover commits para feature branch
git branch feature/task-X-description  # Criar branch no commit atual
git reset --hard origin/main           # Resetar main
git checkout feature/task-X-description # Mudar para feature
git push origin feature/task-X-description # Push
gh pr create                           # Criar PR
```

### Hook não está funcionando

```bash
# Verificar se hook está instalado
ls -la .git/hooks/pre-push

# Verificar se é executável
chmod +x .git/hooks/pre-push

# Testar manualmente
.git/hooks/pre-push
```

### Branch protection não funciona para admin

```bash
# Verifique se marcou "Include administrators"
# Essa opção é crítica!
```

---

## 💡 Dicas

1. **Sempre use branch protection** - É a camada mais forte
2. **Configure hooks locais** - Feedback imediato
3. **Use aliases/scripts** - Facilita seguir o workflow
4. **Teste regularmente** - Verifique se proteções funcionam
5. **Documente para o time** - Todos devem seguir o mesmo workflow

---

**Configurado com ❤️ para evitar commits diretos na main!**
