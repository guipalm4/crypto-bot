#!/usr/bin/env python3
"""
Script de fluxo de trabalho automatizado para desenvolvimento
Integra Task Master AI com Git/GitHub para automatizar:
- Criação de branches
- Commits convencionais
- Abertura de PRs
- Rastreamento de issues/milestones
"""

import os
import sys
import subprocess
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Configuração
REPO_OWNER = 'guipalm4'
REPO_NAME = 'crypto-bot'
BASE_BRANCH = 'main'

class DevWorkflow:
    def __init__(self):
        self.repo_path = Path.cwd()
        self.taskmaster_config = self.repo_path / '.taskmaster' / 'config.json'
        
    def run_command(self, command: str, cwd: Optional[Path] = None) -> tuple[str, int]:
        """Executa comando e retorna output e exit code"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd or self.repo_path
            )
            return result.stdout.strip(), result.returncode
        except Exception as e:
            print(f"❌ Erro ao executar comando: {e}")
            return "", 1
    
    def get_current_branch(self) -> str:
        """Obtém o branch atual"""
        output, _ = self.run_command("git branch --show-current")
        return output
    
    def get_task_info(self, task_id: str) -> Optional[Dict]:
        """Obtém informações da tarefa do Task Master"""
        try:
            # Tenta usar o MCP do Task Master primeiro
            output, code = self.run_command(f"task-master show {task_id}")
            if code == 0:
                # Parse básico da saída do task-master
                lines = output.split('\n')
                task_info = {
                    'id': task_id,
                    'title': '',
                    'description': '',
                    'priority': 'medium',
                    'labels': []
                }
                
                for line in lines:
                    if line.startswith('Title:'):
                        task_info['title'] = line.replace('Title:', '').strip()
                    elif line.startswith('Description:'):
                        task_info['description'] = line.replace('Description:', '').strip()
                    elif line.startswith('Priority:'):
                        task_info['priority'] = line.replace('Priority:', '').strip().lower()
                
                return task_info
        except Exception as e:
            print(f"⚠️ Erro ao obter info da tarefa: {e}")
        
        return None
    
    def create_branch_name(self, task_id: str, task_title: str) -> str:
        """Cria nome do branch seguindo boas práticas"""
        # Remove emojis e caracteres especiais
        clean_title = re.sub(r'[^\w\s-]', '', task_title)
        # Converte para lowercase e substitui espaços por hífens
        clean_title = re.sub(r'[-\s]+', '-', clean_title.lower())
        # Remove hífens no início/fim
        clean_title = clean_title.strip('-')
        # Limita tamanho
        clean_title = clean_title[:50]
        
        return f"feature/task-{task_id}-{clean_title}"
    
    def create_branch(self, task_id: str, task_title: str) -> bool:
        """Cria branch para a tarefa"""
        branch_name = self.create_branch_name(task_id, task_title)
        
        print(f"🌿 Criando branch: {branch_name}")
        
        # Verifica se já existe
        output, _ = self.run_command(f"git branch --list {branch_name}")
        if output:
            print(f"⚠️ Branch {branch_name} já existe")
            return False
        
        # Cria e muda para o branch
        commands = [
            f"git checkout -b {branch_name}",
            f"git push -u origin {branch_name}"
        ]
        
        for cmd in commands:
            output, code = self.run_command(cmd)
            if code != 0:
                print(f"❌ Erro ao executar: {cmd}")
                print(f"Output: {output}")
                return False
        
        print(f"✅ Branch {branch_name} criado com sucesso")
        return True
    
    def create_conventional_commit(self, task_id: str, task_title: str, files_changed: List[str]) -> str:
        """Cria mensagem de commit convencional"""
        # Determina o tipo baseado nos arquivos modificados
        commit_type = "feat"  # padrão
        
        if any("test" in f.lower() for f in files_changed):
            commit_type = "test"
        elif any("doc" in f.lower() or f.endswith('.md') for f in files_changed):
            commit_type = "docs"
        elif any("config" in f.lower() or f.endswith('.yml') or f.endswith('.yaml') for f in files_changed):
            commit_type = "config"
        elif any("fix" in f.lower() or "bug" in f.lower() for f in files_changed):
            commit_type = "fix"
        
        # Cria a mensagem
        scope = f"task-{task_id}"
        description = task_title.replace('[', '').replace(']', '').strip()
        
        # Remove emojis da descrição
        description = re.sub(r'[^\w\s-]', '', description)
        description = description.strip()
        
        commit_msg = f"{commit_type}({scope}): {description}"
        
        # Adiciona referência à issue se possível
        if task_id.isdigit():
            commit_msg += f"\n\nCloses #{task_id}"
        
        return commit_msg
    
    def commit_changes(self, task_id: str, task_title: str) -> bool:
        """Faz commit das mudanças"""
        # Verifica se há mudanças
        output, _ = self.run_command("git status --porcelain")
        if not output:
            print("ℹ️ Nenhuma mudança para commitar")
            return True
        
        # Lista arquivos modificados
        files_changed = [line.split()[-1] for line in output.split('\n') if line.strip()]
        
        # Adiciona todos os arquivos
        self.run_command("git add .")
        
        # Cria mensagem de commit
        commit_msg = self.create_conventional_commit(task_id, task_title, files_changed)
        
        print(f"📝 Fazendo commit: {commit_msg}")
        
        # Faz o commit
        output, code = self.run_command(f'git commit -m "{commit_msg}"')
        if code != 0:
            print(f"❌ Erro no commit: {output}")
            return False
        
        print("✅ Commit realizado com sucesso")
        return True
    
    def create_pull_request(self, task_id: str, task_title: str, task_description: str) -> bool:
        """Cria Pull Request no GitHub"""
        branch_name = self.create_branch_name(task_id, task_title)
        
        # Cria título do PR
        pr_title = f"[Task #{task_id}] {task_title}"
        
        # Cria body do PR usando template
        pr_body = f"""## 📋 Task Master Reference
**Task ID**: {task_id}
**Branch**: `{branch_name}`

## 📝 Descrição
{task_description}

## 🎯 Objetivos
- Implementar funcionalidade conforme especificado na task
- Seguir padrões de código estabelecidos
- Manter cobertura de testes adequada

## 🧪 Critérios de Aceitação
- [ ] Código implementado conforme especificação
- [ ] Testes unitários passando
- [ ] Documentação atualizada se necessário
- [ ] Code review aprovado

## 🔗 Relacionado
- Closes #{task_id}

## 📚 Recursos
- [Task Master AI](https://github.com/guipalm4/crypto-bot/issues/{task_id})
- [Conventional Commits](https://www.conventionalcommits.org/)

## ⏱️ Estimativa
- [x] 🟡 Média (1-3 dias)

## 🏷️ Labels
`task`, `in-progress`, `ready-for-review`
"""
        
        print(f"🔀 Criando Pull Request: {pr_title}")
        
        # Cria o PR usando GitHub CLI
        cmd = f'''gh pr create --title "{pr_title}" --body "{pr_body}" --base {BASE_BRANCH} --head {branch_name} --label "task,in-progress,ready-for-review"'''
        
        output, code = self.run_command(cmd)
        if code != 0:
            print(f"❌ Erro ao criar PR: {output}")
            return False
        
        print(f"✅ Pull Request criado com sucesso!")
        print(f"🔗 URL: {output}")
        return True
    
    def start_development(self, task_id: str) -> bool:
        """Inicia o fluxo de desenvolvimento para uma tarefa"""
        print(f"🚀 Iniciando desenvolvimento da Task #{task_id}")
        
        # Obtém informações da tarefa
        task_info = self.get_task_info(task_id)
        if not task_info:
            print(f"❌ Não foi possível obter informações da Task #{task_id}")
            return False
        
        task_title = task_info.get('title', f'Task {task_id}')
        task_description = task_info.get('description', '')
        
        print(f"📋 Tarefa: {task_title}")
        print(f"📝 Descrição: {task_description}")
        
        # 1. Cria branch
        if not self.create_branch(task_id, task_title):
            return False
        
        # 2. Marca tarefa como in-progress no Task Master
        print(f"⏳ Marcando Task #{task_id} como in-progress...")
        self.run_command(f"task-master set-status --id={task_id} --status=in-progress")
        
        print(f"""
🎉 Fluxo de desenvolvimento iniciado!

📋 Próximos passos:
1. Desenvolva a funcionalidade
2. Execute: python scripts/dev-workflow.py commit {task_id}
3. Execute: python scripts/dev-workflow.py pr {task_id}

🔗 Branch atual: {self.get_current_branch()}
📁 Repositório: {REPO_OWNER}/{REPO_NAME}
""")
        
        return True
    
    def commit_and_pr(self, task_id: str) -> bool:
        """Faz commit e cria PR"""
        # Obtém informações da tarefa
        task_info = self.get_task_info(task_id)
        if not task_info:
            print(f"❌ Não foi possível obter informações da Task #{task_id}")
            return False
        
        task_title = task_info.get('title', f'Task {task_id}')
        task_description = task_info.get('description', '')
        
        # 1. Faz commit
        if not self.commit_changes(task_id, task_title):
            return False
        
        # 2. Push das mudanças
        print("📤 Fazendo push das mudanças...")
        output, code = self.run_command("git push")
        if code != 0:
            print(f"❌ Erro no push: {output}")
            return False
        
        # 3. Cria PR
        if not self.create_pull_request(task_id, task_title, task_description):
            return False
        
        # 4. Marca tarefa como review no Task Master
        print(f"👀 Marcando Task #{task_id} como review...")
        self.run_command(f"task-master set-status --id={task_id} --status=review")
        
        print("🎉 Commit e PR criados com sucesso!")
        return True

def main():
    if len(sys.argv) < 2:
        print("""
🤖 Dev Workflow - Fluxo de Desenvolvimento Automatizado

Uso:
  python scripts/dev-workflow.py start <task_id>    # Inicia desenvolvimento
  python scripts/dev-workflow.py commit <task_id>   # Faz commit e cria PR
  python scripts/dev-workflow.py pr <task_id>       # Apenas cria PR
  python scripts/dev-workflow.py status             # Mostra status atual

Exemplos:
  python scripts/dev-workflow.py start 6
  python scripts/dev-workflow.py commit 6
  python scripts/dev-workflow.py pr 6
""")
        return
    
    workflow = DevWorkflow()
    command = sys.argv[1]
    
    if command == "start" and len(sys.argv) > 2:
        task_id = sys.argv[2]
        workflow.start_development(task_id)
    elif command == "commit" and len(sys.argv) > 2:
        task_id = sys.argv[2]
        workflow.commit_and_pr(task_id)
    elif command == "pr" and len(sys.argv) > 2:
        task_id = sys.argv[2]
        task_info = workflow.get_task_info(task_id)
        if task_info:
            workflow.create_pull_request(
                task_id, 
                task_info.get('title', f'Task {task_id}'),
                task_info.get('description', '')
            )
    elif command == "status":
        print(f"📊 Status atual:")
        print(f"🌿 Branch: {workflow.get_current_branch()}")
        print(f"📁 Repositório: {REPO_OWNER}/{REPO_NAME}")
    else:
        print("❌ Comando inválido. Use 'python scripts/dev-workflow.py' para ver a ajuda.")

if __name__ == "__main__":
    main()
