# AGENTS.md + MCP Integration Assessment

## Objetivo

Analisar como o padrão AGENTS.md pode ser integrado aos MCPs e
ferramentas em uso (Task Master AI, Context7 e GitHub MCP) para suportar
uma arquitetura agentic no projeto.

## 1. Papel de cada componente

| Componente | Função atual | Papel no cenário agentic |
| --- | --- | --- |
| **AGENTS.md** | Ponto único de instruções para agentes de código | Define convenções, comandos e critérios de qualidade/segurança que todos os agentes devem seguir. Pode ter versões hierárquicas por diretório. |
| **Task Master AI** | Orquestração de tarefas, subtasks, dependências | Scheduler central que decompõe demandas, atribui a agentes especializados e sincroniza contexto e checkpoints. |
| **Context7** | Memória/contexto compartilhado (pesquisas, decisões) | Repositório persistente de contexto para garantir continuidade entre agentes e histórico de decisões. |
| **GitHub MCP** | Coordenação em tempo real com Git/CI | Canal de comunicação para bloqueio de arquivos, notificações e automação de PRs/CI alinhadas ao AGENTS.md. |

## 2. Padrão de orquestração recomendado

1. **AGENTS.md raiz** documenta visão geral, comandos, estilo, segurança e
   requisitos de revisão. Subdiretórios críticos (ex. `src/crypto_bot/`,
   `docs/`) podem ter AGENTS.md específicos.
2. **Task Master AI** recebe objetivos de alto nível e gera subtasks
   atomizadas com dependências claras (ex.: integrar agente de risco com
   Execution Agent).
3. **Context7** armazena estado compartilhado (decisões tomadas, diffs,
   links para commits, resultados de testes) acessível por todos os
   agentes.
4. **GitHub MCP** faz ponte com o repositório: cria branches por task,
   bloqueia arquivos, dispara lint/tests e atualiza PRs seguindo o template
   obrigatório.
5. **Ciclo**: Task Master → atribui subtask → agente consulta AGENTS.md e
   contexto no Context7 → executa alterações → comunica via GitHub MCP →
   Task Master registra estado/artefatos.

## 3. Sinergias e benefícios

- **Consistência documental**: AGENTS.md garante que todos os agentes
  (humanos ou não) usam comandos, padrões de commit, checklists e políticas
  de segurança uniformes.
- **Workflow automatizado**: Task Master simplifica branch-per-task e
  enforce checkpoints de QA antes de merge, reduzindo risco de regressões.
- **Memória compartilhada**: Context7 evita perda de contexto em handoffs e
  mantém histórico consultável para auditoria/compliance.
- **Coordenação em tempo real**: GitHub MCP possibilita lock de arquivos e
  reduz conflitos quando múltiplos agentes atuam paralelamente.
- **Escalabilidade**: Ao separar responsabilidades (ex. Strategy Agent,
  Risk Agent), cada agente pode ser escalado horizontalmente com instâncias
  adicionais coordenadas pelo Task Master.

## 4. Potenciais conflitos e pontos de atenção

| Tema | Risco | Mitigação sugerida |
| --- | --- | --- |
| Conflitos de edição | Agentes alterando o mesmo arquivo simultaneamente | Adotar locking via MCP, branch por subtask e rebases frequentes automatizados. |
| Drift de documentação | AGENTS.md ficar desatualizado frente a fluxos reais | Automatizar atualizações via Task Master + PR checklist exigindo revisão do AGENTS.md relevante. |
| Sobrecarga de contexto | Synchronizações constantes em Context7 podem degradar performance | Utilizar diffs incrementais, cache local e políticas de compactação de histórico. |
| Latência de coordenação | Mais hops assíncronos entre agentes podem aumentar tempo de resposta | Priorizar filas leves (ex. Redis pub/sub), monitorar SLAs e otimizar tarefas críticas (execução de ordens). |
| Governança de segredos | Diversos agentes acessando configurações sensíveis | Centralizar gestão de segredos (ex. vault) e expor apenas tokens temporários. |

## 5. Considerações de performance

- **Granularidade de subtasks**: subtasks muito pequenas elevam a carga de
  coordenação; definir tamanho mínimo que agregue valor.
- **Batch de mensagens**: agrupar atualizações para reduzir tráfego via MCP
  e escritas em Context7.
- **Monitoramento**: estabelecer métricas (tempo por subtask, tempo de lock,
  falhas de sincronização) e criar alertas para degradação.
- **CI otimizada**: pipelines vinculadas ao GitHub MCP devem empregar caches
  (poetry/pip, pytest) para manter feedback rápido.

## 6. Recomendações práticas

1. **Atualizar AGENTS.md**: incluir seções sobre uso de Task Master, MCP e
   políticas de segurança/logging específicas para agentes.
2. **Template de task**: padronizar no Task Master campos como pré-condições,
   comandos obrigatórios, critérios de aceite e checkpoints humanos.
3. **Estratégia de contextos**: definir convenções de chaves/namespaces no
   Context7 (ex. `strategy-agent/<task-id>`).
4. **Automação MCP**: configurar hooks para criação de branch, execução de
   lint/tests e atualização de PR template conforme checkboxes obrigatórios.
5. **Revisões periódicas**: agenda mensal para revisar AGENTS.md, fluxos do
   Task Master e integrações MCP, alinhando com lessons learned.

## 7. Próximos passos sugiridos

- Implementar prova de conceito onde um Strategy Agent gera um PR seguindo
  AGENTS.md, com Task Master registrando progresso e Context7 armazenando
  justificativas.
- Monitorar métricas de coordenação (tempo de subtask, conflitos resolved
  via MCP) para validar ganhos de eficiência.
- Evoluir documentação com diagramas que ilustrem o fluxo Task Master ↔
  Agentes ↔ MCP/Context7 como parte do relatório final da task 22.


