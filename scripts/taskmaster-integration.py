#!/usr/bin/env python3
"""
Integração do Task Master AI com fluxo de desenvolvimento
Automatiza a criação de branches, commits e PRs baseado nas tarefas
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional

class TaskMasterIntegration:
    def __init__(self):
        self.repo_path = Path.cwd()
        self.taskmaster_config = self.repo_path / '.taskmaster' / 'config.json'
        self.tasks_file = self.repo_path / '.taskmaster' / 'tasks' / 'tasks.json'
        
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
    
    def get_next_task(self) -> Optional[Dict]:
        """Obtém a próxima tarefa do Task Master"""
        output, code = self.run_command("task-master next")
        if code != 0:
            print(f"❌ Erro ao obter próxima tarefa: {output}")
            return None
        
        # Parse da saída do task-master next
        lines = output.split('\n')
        task_info = {}
        
        for line in lines:
            if line.startswith('Task ID:'):
                task_info['id'] = line.replace('Task ID:', '').strip()
            elif line.startswith('Title:'):
                task_info['title'] = line.replace('Title:', '').strip()
            elif line.startswith('Description:'):
                task_info['description'] = line.replace('Description:', '').strip()
            elif line.startswith('Priority:'):
                task_info['priority'] = line.replace('Priority:', '').strip()
            elif line.startswith('Status:'):
                task_info['status'] = line.replace('Status:', '').strip()
        
        return task_info if task_info else None
    
    def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """Obtém tarefa específica por ID"""
        output, code = self.run_command(f"task-master show {task_id}")
        if code != 0:
            print(f"❌ Erro ao obter tarefa {task_id}: {output}")
            return None
        
        # Parse da saída do task-master show
        lines = output.split('\n')
        task_info = {'id': task_id}
        
        for line in lines:
            if line.startswith('Title:'):
                task_info['title'] = line.replace('Title:', '').strip()
            elif line.startswith('Description:'):
                task_info['description'] = line.replace('Description:', '').strip()
            elif line.startswith('Priority:'):
                task_info['priority'] = line.replace('Priority:', '').strip()
            elif line.startswith('Status:'):
                task_info['status'] = line.replace('Status:', '').strip()
        
        return task_info
    
    def start_task_development(self, task_id: str = None) -> bool:
        """Inicia desenvolvimento de uma tarefa"""
        if not task_id:
            # Obtém próxima tarefa
            task_info = self.get_next_task()
            if not task_info:
                print("❌ Nenhuma tarefa disponível")
                return False
            task_id = task_info['id']
        else:
            # Obtém tarefa específica
            task_info = self.get_task_by_id(task_id)
            if not task_info:
                return False
        
        print(f"🚀 Iniciando desenvolvimento da Task #{task_id}")
        print(f"📋 Tarefa: {task_info.get('title', 'N/A')}")
        print(f"📝 Descrição: {task_info.get('description', 'N/A')}")
        print(f"⚡ Prioridade: {task_info.get('priority', 'N/A')}")
        
        # Executa o script de desenvolvimento
        output, code = self.run_command(f"python scripts/dev-workflow.py start {task_id}")
        if code != 0:
            print(f"❌ Erro ao iniciar desenvolvimento: {output}")
            return False
        
        print("✅ Desenvolvimento iniciado com sucesso!")
        return True
    
    def complete_task(self, task_id: str) -> bool:
        """Completa uma tarefa (commit + PR)"""
        print(f"🏁 Completando Task #{task_id}")
        
        # Executa commit e PR
        output, code = self.run_command(f"python scripts/dev-workflow.py commit {task_id}")
        if code != 0:
            print(f"❌ Erro ao completar tarefa: {output}")
            return False
        
        print("✅ Tarefa completada com sucesso!")
        return True
    
    def list_available_tasks(self) -> None:
        """Lista tarefas disponíveis"""
        output, code = self.run_command("task-master list --status=pending")
        if code != 0:
            print(f"❌ Erro ao listar tarefas: {output}")
            return
        
        print("📋 Tarefas Disponíveis:")
        print(output)
    
    def show_task_status(self) -> None:
        """Mostra status das tarefas"""
        output, code = self.run_command("task-master list")
        if code != 0:
            print(f"❌ Erro ao obter status: {output}")
            return
        
        print("📊 Status das Tarefas:")
        print(output)

def main():
    if len(sys.argv) < 2:
        print("""
🤖 Task Master Integration - Fluxo de Desenvolvimento Automatizado

Uso:
  python scripts/taskmaster-integration.py start [task_id]  # Inicia desenvolvimento
  python scripts/taskmaster-integration.py complete <task_id>  # Completa tarefa
  python scripts/taskmaster-integration.py list            # Lista tarefas disponíveis
  python scripts/taskmaster-integration.py status          # Mostra status das tarefas
  python scripts/taskmaster-integration.py next            # Inicia próxima tarefa

Exemplos:
  python scripts/taskmaster-integration.py start 6
  python scripts/taskmaster-integration.py complete 6
  python scripts/taskmaster-integration.py next
""")
        return
    
    integration = TaskMasterIntegration()
    command = sys.argv[1]
    
    if command == "start":
        task_id = sys.argv[2] if len(sys.argv) > 2 else None
        integration.start_task_development(task_id)
    elif command == "complete" and len(sys.argv) > 2:
        task_id = sys.argv[2]
        integration.complete_task(task_id)
    elif command == "list":
        integration.list_available_tasks()
    elif command == "status":
        integration.show_task_status()
    elif command == "next":
        integration.start_task_development()
    else:
        print("❌ Comando inválido. Use 'python scripts/taskmaster-integration.py' para ver a ajuda.")

if __name__ == "__main__":
    main()
