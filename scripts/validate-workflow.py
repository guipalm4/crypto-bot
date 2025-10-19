#!/usr/bin/env python3
"""
Script de validação do fluxo de desenvolvimento
Verifica se tudo está configurado corretamente
"""

import os
import subprocess
import json
from pathlib import Path

def check_command(cmd: str, name: str) -> bool:
    """Verifica se um comando está disponível"""
    result = subprocess.run(['which', cmd], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {name} disponível")
        return True
    else:
        print(f"❌ {name} não encontrado")
        return False

def check_file_exists(file_path: Path, name: str) -> bool:
    """Verifica se um arquivo existe"""
    if file_path.exists():
        print(f"✅ {name} encontrado")
        return True
    else:
        print(f"❌ {name} não encontrado")
        return False

def check_git_config():
    """Verifica configuração do Git"""
    print("\n🔍 Verificando configuração do Git...")
    
    configs = ['user.name', 'user.email', 'init.defaultBranch']
    all_good = True
    
    for config in configs:
        result = subprocess.run(['git', 'config', config], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print(f"✅ Git {config}: {result.stdout.strip()}")
        else:
            print(f"❌ Git {config} não configurado")
            all_good = False
    
    return all_good

def check_git_hooks():
    """Verifica Git hooks"""
    print("\n🔍 Verificando Git hooks...")
    
    hooks_dir = Path('.git/hooks')
    hooks = ['pre-commit', 'commit-msg', 'post-commit']
    all_good = True
    
    for hook in hooks:
        hook_path = hooks_dir / hook
        if hook_path.exists() and hook_path.stat().st_mode & 0o111:
            print(f"✅ Hook {hook} configurado e executável")
        else:
            print(f"❌ Hook {hook} não configurado ou não executável")
            all_good = False
    
    return all_good

def check_github_auth():
    """Verifica autenticação do GitHub"""
    print("\n🔍 Verificando autenticação do GitHub...")
    
    result = subprocess.run(['gh', 'auth', 'status'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ GitHub CLI autenticado")
        return True
    else:
        print("❌ GitHub CLI não autenticado")
        print("Execute: gh auth login")
        return False

def check_taskmaster():
    """Verifica Task Master AI"""
    print("\n🔍 Verificando Task Master AI...")
    
    result = subprocess.run(['task-master', '--version'], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Task Master AI disponível: {result.stdout.strip()}")
        return True
    else:
        print("❌ Task Master AI não encontrado")
        return False

def check_project_structure():
    """Verifica estrutura do projeto"""
    print("\n🔍 Verificando estrutura do projeto...")
    
    required_files = [
        Path('scripts/dev-workflow.py'),
        Path('scripts/taskmaster-integration.py'),
        Path('scripts/setup-git-hooks.py'),
        Path('.github/workflow-config.json'),
        Path('.taskmaster/workflow-integration.json'),
        Path('.github/pull_request_template.md')
    ]
    
    all_good = True
    for file_path in required_files:
        if not check_file_exists(file_path, file_path.name):
            all_good = False
    
    return all_good

def check_git_aliases():
    """Verifica aliases do Git"""
    print("\n🔍 Verificando aliases do Git...")
    
    aliases = [
        'task-start', 'task-complete', 'task-next', 
        'task-list', 'task-status', 'dev-start', 
        'dev-commit', 'dev-pr'
    ]
    
    all_good = True
    for alias in aliases:
        result = subprocess.run(['git', 'config', f'alias.{alias}'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Alias {alias} configurado")
        else:
            print(f"❌ Alias {alias} não configurado")
            all_good = False
    
    return all_good

def run_workflow_test():
    """Executa teste do fluxo de trabalho"""
    print("\n🧪 Testando fluxo de trabalho...")
    
    # Testa listagem de tarefas
    result = subprocess.run(['git', 'task-list'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Comando 'git task-list' funcionando")
    else:
        print("❌ Comando 'git task-list' falhou")
        return False
    
    # Testa status
    result = subprocess.run(['git', 'task-status'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Comando 'git task-status' funcionando")
    else:
        print("❌ Comando 'git task-status' falhou")
        return False
    
    return True

def main():
    print("🔍 Validando Fluxo de Desenvolvimento Automatizado")
    print("=" * 60)
    
    checks = [
        ("Requisitos básicos", lambda: all([
            check_command('git', 'Git'),
            check_command('gh', 'GitHub CLI'),
            check_command('python3', 'Python 3')
        ])),
        ("Configuração do Git", check_git_config),
        ("Git hooks", check_git_hooks),
        ("Autenticação GitHub", check_github_auth),
        ("Task Master AI", check_taskmaster),
        ("Estrutura do projeto", check_project_structure),
        ("Aliases do Git", check_git_aliases),
        ("Teste do fluxo", run_workflow_test)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Erro na verificação: {e}")
            results.append((check_name, False))
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DA VALIDAÇÃO")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} {check_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} verificações passaram")
    
    if passed == total:
        print("\n🎉 Fluxo de desenvolvimento configurado corretamente!")
        print("\n🚀 Próximos passos:")
        print("1. Execute: git task-status")
        print("2. Execute: git task-next")
        print("3. Desenvolva a funcionalidade")
        print("4. Execute: git task-complete <task_id>")
    else:
        print(f"\n⚠️ {total - passed} verificações falharam")
        print("Execute: python scripts/setup-dev-workflow.py")
        print("Depois execute novamente: python scripts/validate-workflow.py")

if __name__ == "__main__":
    main()
