#!/usr/bin/env python3
"""
Script de configuração do fluxo de desenvolvimento automatizado
Configura Git hooks, aliases e validações
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Verifica se todos os requisitos estão instalados"""
    requirements = {
        'git': 'Git',
        'gh': 'GitHub CLI',
        'task-master': 'Task Master AI'
    }
    
    missing = []
    
    for cmd, name in requirements.items():
        result = subprocess.run(['which', cmd], capture_output=True, text=True)
        if result.returncode != 0:
            missing.append(name)
        else:
            print(f"✅ {name} encontrado")
    
    if missing:
        print(f"❌ Requisitos faltando: {', '.join(missing)}")
        print("\n📋 Instruções de instalação:")
        print("  Git: https://git-scm.com/downloads")
        print("  GitHub CLI: https://cli.github.com/")
        print("  Task Master AI: npm install -g task-master-ai")
        return False
    
    return True

def setup_scripts():
    """Torna os scripts executáveis"""
    scripts_dir = Path.cwd() / 'scripts'
    scripts = [
        'dev-workflow.py',
        'taskmaster-integration.py',
        'setup-git-hooks.py'
    ]
    
    for script in scripts:
        script_path = scripts_dir / script
        if script_path.exists():
            os.chmod(script_path, 0o755)
            print(f"✅ {script} configurado como executável")
        else:
            print(f"⚠️  {script} não encontrado")

def setup_git_config():
    """Configura Git com configurações recomendadas"""
    configs = {
        'user.name': 'Guilherme Palma',
        'user.email': 'gomes.lmc@gmail.com',
        'init.defaultBranch': 'main',
        'pull.rebase': 'false',
        'push.autoSetupRemote': 'true'
    }
    
    for key, value in configs.items():
        subprocess.run(['git', 'config', key, value])
        print(f"✅ Git config {key} = {value}")

def create_workflow_docs():
    """Cria documentação do fluxo de trabalho"""
    docs_content = '''# 🤖 Fluxo de Desenvolvimento Automatizado

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
'''
    
    docs_path = Path.cwd() / 'docs' / 'DEVELOPMENT_WORKFLOW.md'
    docs_path.parent.mkdir(exist_ok=True)
    
    with open(docs_path, 'w') as f:
        f.write(docs_content)
    
    print(f"✅ Documentação criada: {docs_path}")

def main():
    print("🔧 Configurando Fluxo de Desenvolvimento Automatizado...")
    print("=" * 60)
    
    # Verifica requisitos
    print("\n📋 Verificando requisitos...")
    if not check_requirements():
        print("\n❌ Configuração interrompida. Instale os requisitos faltantes.")
        return
    
    # Configura scripts
    print("\n🔧 Configurando scripts...")
    setup_scripts()
    
    # Configura Git
    print("\n⚙️ Configurando Git...")
    setup_git_config()
    
    # Configura Git hooks
    print("\n🪝 Configurando Git hooks...")
    subprocess.run(['python', 'scripts/setup-git-hooks.py'])
    
    # Cria documentação
    print("\n📚 Criando documentação...")
    create_workflow_docs()
    
    print("\n" + "=" * 60)
    print("🎉 Configuração concluída com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Execute: git task-status")
    print("2. Execute: git task-next")
    print("3. Desenvolva a funcionalidade")
    print("4. Execute: git task-complete <task_id>")
    print("\n📚 Documentação: docs/DEVELOPMENT_WORKFLOW.md")

if __name__ == "__main__":
    main()
