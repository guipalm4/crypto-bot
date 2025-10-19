# ⚡ Workflow Quick Start

## 🎯 Setup (Uma vez só)

```bash
# 1. Instalar hooks que bloqueiam push direto na main
./scripts/install-hooks.sh

# 2. Configurar branch protection no GitHub
# Acesse: https://github.com/guipalm4/crypto-bot/settings/branches
# - Add rule para "main"
# - ✅ Require pull request before merging
# - ✅ Include administrators
```

## 🚀 Workflow Diário

### Método Automático (Recomendado)

```bash
# 1. Iniciar nova task
./scripts/workflow.sh start
# ✅ Created branch: feature/task-2-database-schema

# 2. Desenvolver
# ... código aqui ...

# 3. Commit
git add .
git commit -m "feat(task-2): implement database schema"

# 4. Finalizar (push + PR automático)
./scripts/workflow.sh finish
# ✅ PR created!
```

### Método Manual

```bash
# 1. Ver próxima task
task-master next

# 2. Criar branch
git checkout -b feature/task-X-description

# 3. Desenvolver
# ... código ...

# 4. Commit
git add .
git commit -m "feat(task-X): description"

# 5. Push
git push origin feature/task-X-description

# 6. Criar PR
gh pr create --fill
```

## 🛡️ Proteções Ativas

### Local (Git Hook)
- ❌ Bloqueia `git push origin main`
- ✅ Permite push em feature branches

### GitHub (Branch Protection)
- ❌ Bloqueia commits diretos na main
- ✅ Força pull requests
- ✅ Requer CI/CD passing
- ✅ Funciona até para admins

## 🧪 Testar Proteções

```bash
# Deve falhar
git checkout main
echo "test" >> test.txt
git add test.txt
git commit -m "test"
git push origin main
# 🚫 ERROR: Direct push to 'main' is not allowed!

# Deve funcionar
git checkout -b feature/test
git push origin feature/test
# ✅ Success!
```

## 🆘 Se Esquecer e Commitar na Main

```bash
# Salvar commits em nova branch
git branch feature/task-X-fix

# Voltar main para remoto
git reset --hard origin/main

# Mudar para feature branch
git checkout feature/task-X-fix

# Push e PR
git push origin feature/task-X-fix
gh pr create
```

## 💡 Dicas

- Use `./scripts/workflow.sh start` para começar
- Use `./scripts/workflow.sh finish` para finalizar
- Sempre trabalhe em feature branches
- Nunca force push (`git push -f`)

---

**Proteções configuradas! 🛡️**

