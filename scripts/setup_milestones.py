#!/usr/bin/env python3
"""
Script para criar milestones no GitHub automaticamente
Baseado no planejamento do Task Master AI
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List

# Configuração
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = 'guipalm4'
REPO_NAME = 'crypto-bot'

# Headers para a API do GitHub
HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'crypto-bot-setup'
}

# Definição das milestones
MILESTONES = [
    {
        'title': '🏗️ Sprint 1: Foundation & Core Infrastructure',
        'description': 'Estabelecer a base sólida do projeto com estrutura, configuração e infraestrutura essencial',
        'due_on': '2025-11-01T23:59:59Z',
        'issues': [6, 7, 8]  # Task #1, #2, #3
    },
    {
        'title': '🚀 Sprint 2: Core Trading Engine & Risk Management',
        'description': 'Implementar o motor principal de trading e sistema de gestão de risco',
        'due_on': '2025-11-22T23:59:59Z',
        'issues': [9, 10]  # Task #4, #6
    },
    {
        'title': '🔌 Sprint 3: Exchange Integration & Plugin System',
        'description': 'Implementar integração com exchanges e sistema de plugins modular',
        'due_on': '2025-12-13T23:59:59Z',
        'issues': [11, 12]  # Task #7, #8
    },
    {
        'title': '🎯 Sprint 4: Trading Strategies & Orchestration',
        'description': 'Implementar estratégias de trading e sistema de orquestração',
        'due_on': '2026-01-03T23:59:59Z',
        'issues': [13]  # Task #12
    },
    {
        'title': '🎨 Sprint 5: User Interface & Final Polish',
        'description': 'Implementar interface de usuário e finalizar o MVP',
        'due_on': '2026-01-17T23:59:59Z',
        'issues': [14]  # Task #16
    }
]

def create_milestone(milestone_data: Dict) -> Dict:
    """Cria uma milestone no GitHub"""
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/milestones'
    
    payload = {
        'title': milestone_data['title'],
        'description': milestone_data['description'],
        'due_on': milestone_data['due_on']
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code == 201:
        return response.json()
    else:
        print(f"❌ Erro ao criar milestone '{milestone_data['title']}': {response.status_code}")
        print(f"Resposta: {response.text}")
        return None

def assign_issues_to_milestone(milestone_number: int, issue_numbers: List[int]):
    """Associa issues a uma milestone"""
    for issue_number in issue_numbers:
        url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{issue_number}'
        
        payload = {
            'milestone': milestone_number
        }
        
        response = requests.patch(url, headers=HEADERS, json=payload)
        
        if response.status_code == 200:
            print(f"✅ Issue #{issue_number} associada à milestone #{milestone_number}")
        else:
            print(f"❌ Erro ao associar issue #{issue_number}: {response.status_code}")

def main():
    """Função principal"""
    if not GITHUB_TOKEN:
        print("❌ Erro: GITHUB_TOKEN não encontrado nas variáveis de ambiente")
        print("Configure com: export GITHUB_TOKEN=seu_token_aqui")
        return
    
    print("🚀 Criando milestones no GitHub...")
    print(f"📁 Repositório: {REPO_OWNER}/{REPO_NAME}")
    print()
    
    created_milestones = []
    
    for milestone_data in MILESTONES:
        print(f"📋 Criando milestone: {milestone_data['title']}")
        
        milestone = create_milestone(milestone_data)
        
        if milestone:
            created_milestones.append(milestone)
            print(f"✅ Milestone criada com sucesso! ID: {milestone['number']}")
            
            # Associar issues à milestone
            if milestone_data['issues']:
                print(f"🔗 Associando issues {milestone_data['issues']} à milestone...")
                assign_issues_to_milestone(milestone['number'], milestone_data['issues'])
            
            print()
        else:
            print(f"❌ Falha ao criar milestone: {milestone_data['title']}")
            print()
    
    # Resumo
    print("📊 Resumo da criação de milestones:")
    print(f"✅ Milestones criadas: {len(created_milestones)}")
    print()
    
    for milestone in created_milestones:
        print(f"🎯 {milestone['title']}")
        print(f"   📅 Data limite: {milestone['due_on']}")
        print(f"   🔗 URL: {milestone['html_url']}")
        print()
    
    print("🎉 Configuração de milestones concluída!")
    print("📝 Acesse: https://github.com/guipalm4/crypto-bot/milestones")

if __name__ == '__main__':
    main()
