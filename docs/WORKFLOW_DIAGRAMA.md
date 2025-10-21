# 🔄 Diagrama do Workflow de Desenvolvimento

## Fluxo Principal

```
┌─────────────────────────────────────────────────────────────────┐
│                    🚀 INÍCIO DO DESENVOLVIMENTO                │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              🎯 FASE 1: TASK MASTER (PRIORIDADE #1)            │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   next_task     │───▶│   get_task      │───▶│ expand_task  │ │
│  │ (próxima tarefa)│    │ (detalhes)      │    │ (se complexa)│ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│            🔍 FASE 2: PESQUISA (OBRIGATÓRIA)                   │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   Context7      │    │ Task Master     │    │ update_      │ │
│  │ (melhores       │    │ research        │    │ subtask      │ │
│  │  práticas)      │    │ (contexto)      │    │ (logar)      │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│            ⚙️ FASE 3: PREPARAÇÃO DO AMBIENTE                   │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ git branch      │    │ git checkout    │    │ set_status   │ │
│  │ --show-current  │    │ -b feature/...  │    │ in-progress  │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              💻 FASE 4: IMPLEMENTAÇÃO                          │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   Implementar   │    │ update_subtask  │    │ Quality      │ │
│  │   seguindo      │    │ (progresso)     │    │ Checks       │ │
│  │   padrões       │    │                 │    │ (black, etc) │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│            📝 FASE 5: COMMIT E VERSIONAMENTO                   │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ git add .       │    │ git commit      │    │ git push     │ │
│  │                 │    │ -m "feat:..."   │    │ origin ...   │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              🔄 FASE 6: PULL REQUEST                           │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ gh pr create    │    │ Preencher       │    │ Checklist    │ │
│  │ --title "..."   │    │ Template        │    │ Segurança    │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              ✅ FASE 7: FINALIZAÇÃO                            │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │ set_status      │    │ Verificar       │    │ update       │ │
│  │ done            │    │ dependências    │    │ dependentes  │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    🎉 TAREFA CONCLUÍDA                         │
└─────────────────────────────────────────────────────────────────┘
```

## Hierarquia de Prioridades

```
🥇 TASK MASTER (PRIORIDADE ABSOLUTA)
├── 🥈 Context7 (Pesquisa e melhores práticas)
├── 🥉 Git (Controle de versão - se usado)
├── 🏅 GitHub Templates (Templates - se usando Git)
└── 🏅 Code Quality (Linting, formatação, testes)
```

## Regras de Enforcamento

### ❌ NUNCA FAZER:
- Bypass do Task Master workflow
- Implementar sem tarefa ativa no Task Master
- Pular pesquisa com Context7
- Commitar diretamente no main/master
- Pular quality checks
- Pular atualizações de progresso no Task Master

### ✅ SEMPRE FAZER:
- Começar com Task Master (`next_task`)
- Pesquisar com Context7 + Task Master research
- Atualizar progresso regularmente (`update_subtask`)
- Executar quality checks antes de commitar
- Usar templates do GitHub (se usando Git)
- Marcar tarefas como concluídas (`set_task_status`)

## Quality Gates

### Antes de Implementar:
- [ ] Task Master task ativa e compreendida
- [ ] Context7 research completada
- [ ] Task Master research completada
- [ ] Branch de feature criada (se usando Git)

### Durante Implementação:
- [ ] Progresso logado regularmente no Task Master
- [ ] Padrões pesquisados sendo seguidos
- [ ] Quality checks executados

### Antes de Commitar:
- [ ] Todos os quality checks passando
- [ ] Código formatado com Black
- [ ] Linting sem erros
- [ ] Type hints corretos
- [ ] Testes passando

### Antes de Finalizar:
- [ ] Task Master task marcada como done
- [ ] Tarefas dependentes atualizadas (se necessário)
- [ ] Documentação atualizada
- [ ] PR criado e template preenchido (se usando Git)
