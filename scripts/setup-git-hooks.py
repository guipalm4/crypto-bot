#!/usr/bin/env python3
"""
Configuração de Git Hooks para automatizar o fluxo de desenvolvimento
"""

import os
import subprocess
from pathlib import Path

def setup_git_hooks():
    """Configura Git hooks para automatizar o fluxo"""
    repo_path = Path.cwd()
    hooks_dir = repo_path / '.git' / 'hooks'
    
    # Pre-commit hook
    pre_commit_content = '''#!/bin/bash
# Pre-commit hook para validação de código

echo "🔍 Executando pre-commit checks..."

# Verifica se está em um branch de feature
current_branch=$(git branch --show-current)
if [[ $current_branch == feature/task-* ]]; then
    echo "✅ Branch de feature detectado: $current_branch"
else
    echo "⚠️  Aviso: Não está em um branch de feature"
fi

# Executa linting se disponível
if command -v black &> /dev/null; then
    echo "🎨 Executando Black formatter..."
    black --check .
fi

if command -v flake8 &> /dev/null; then
    echo "🔍 Executando Flake8 linter..."
    flake8 .
fi

if command -v mypy &> /dev/null; then
    echo "🔍 Executando MyPy type checker..."
    mypy .
fi

echo "✅ Pre-commit checks concluídos"
'''
    
    # Commit-msg hook
    commit_msg_content = '''#!/bin/bash
# Commit-msg hook para validar mensagens de commit convencionais

commit_regex='^(feat|fix|docs|style|refactor|test|chore|config)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "❌ Mensagem de commit inválida!"
    echo "📝 Formato esperado: type(scope): description"
    echo "📚 Tipos válidos: feat, fix, docs, style, refactor, test, chore, config"
    echo "📖 Exemplo: feat(task-6): implement project structure setup"
    exit 1
fi

echo "✅ Mensagem de commit válida"
'''
    
    # Post-commit hook
    post_commit_content = '''#!/bin/bash
# Post-commit hook para ações pós-commit

echo "🎉 Commit realizado com sucesso!"

# Verifica se está em um branch de feature
current_branch=$(git branch --show-current)
if [[ $current_branch == feature/task-* ]]; then
    echo "💡 Dica: Execute 'python scripts/dev-workflow.py pr' para criar um PR"
fi
'''
    
    # Cria os hooks
    hooks = {
        'pre-commit': pre_commit_content,
        'commit-msg': commit_msg_content,
        'post-commit': post_commit_content
    }
    
    for hook_name, content in hooks.items():
        hook_path = hooks_dir / hook_name
        with open(hook_path, 'w') as f:
            f.write(content)
        
        # Torna executável
        os.chmod(hook_path, 0o755)
        print(f"✅ Hook {hook_name} configurado")
    
    print("🎉 Git hooks configurados com sucesso!")

def setup_git_aliases():
    """Configura aliases úteis do Git"""
    aliases = {
        'task-start': '!python scripts/taskmaster-integration.py start',
        'task-complete': '!python scripts/taskmaster-integration.py complete',
        'task-next': '!python scripts/taskmaster-integration.py next',
        'task-list': '!python scripts/taskmaster-integration.py list',
        'task-status': '!python scripts/taskmaster-integration.py status',
        'dev-start': '!python scripts/dev-workflow.py start',
        'dev-commit': '!python scripts/dev-workflow.py commit',
        'dev-pr': '!python scripts/dev-workflow.py pr'
    }
    
    for alias, command in aliases.items():
        subprocess.run(['git', 'config', '--global', f'alias.{alias}', command])
        print(f"✅ Alias {alias} configurado")
    
    print("🎉 Git aliases configurados com sucesso!")

def main():
    print("🔧 Configurando Git Hooks e Aliases...")
    
    setup_git_hooks()
    setup_git_aliases()
    
    print("""
🎉 Configuração concluída!

📋 Aliases disponíveis:
  git task-start <task_id>    # Inicia desenvolvimento de uma tarefa
  git task-complete <task_id> # Completa uma tarefa (commit + PR)
  git task-next               # Inicia próxima tarefa disponível
  git task-list               # Lista tarefas disponíveis
  git task-status             # Mostra status das tarefas
  git dev-start <task_id>     # Inicia desenvolvimento (modo manual)
  git dev-commit <task_id>    # Faz commit e cria PR
  git dev-pr <task_id>        # Apenas cria PR

🚀 Exemplo de uso:
  git task-next               # Inicia próxima tarefa
  # ... desenvolve a funcionalidade ...
  git task-complete 6         # Completa a tarefa 6
""")

if __name__ == "__main__":
    main()
