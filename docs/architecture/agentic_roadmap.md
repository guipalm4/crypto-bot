# Agentic Adoption Roadmap

## Visão geral

Roadmap incremental para adoção da arquitetura agentic, alinhado às
recomendações do relatório de viabilidade e à matriz de riscos.

## Fase 0 – Preparação (Semanas 0-2)

- Provisionar infraestrutura base: Redis MCP (cache/checkpoints),
  Prometheus/Grafana MCP (observabilidade), secrets vault.
- Atualizar `AGENTS.md` com instruções agentic iniciais e configurar nova
  rule `agentic_workflow.mdc`.
- Definir KPIs iniciais e dashboards (latência por trade, falhas por
  agente, backlog de eventos).
- Entregáveis: ambiente de staging configurado, checklists de segurança,
  scripts helpers mínimos (lint, validação de agentes).

## Fase 1 – PoC controlado (Semanas 3-6)

- Implementar pipeline LangGraph com Strategy Agent ↔ Execution Agent
  usando Redis MCP para estado.
- Instrumentar Prometheus/Grafana MCP para monitoramento de latência e
  erros.
- Conduzir testes E2E em modo dry-run com volume reduzido.
- Avaliar AutoGen para sessões de revisão (Risk + Execution + humano).
- Gate: latência média < 20% acima do baseline e zero perda de eventos.

## Fase 2 – Expansão funcional (Semanas 7-10)

- Introduzir Risk Agent e Event & Compliance Agent na malha LangGraph.
- Integrar Polygon MCP (dados de mercado) e, se aprovado, Financial
  Datasets/Dappier.
- Documentar scripts helpers priorizados (deploy, troubleshooting,
  backfills) e atualizar `agent_helper_scripts.md`.
- Atualizar AGENTS.md e rules conforme fluxo completo.
- Gate: testes E2E completos (stop loss, emergency exit) aprovados;
  cobertura ≥ 80%; métricas de risco estáveis.

## Fase 3 – Hardening & Produção (Semanas 11-14)

- Automação de rollback, blue/green e auto-escalonamento de agentes.
- Implementar alertas automáticos (Prometheus + canal MCP ex. Discord).
- Revisão de compliance/auditoria; validar governança de segredos.
- Preparar documentação final para onboarding (docs, AGENTS, rules).
- Gate final: KPIs atendidos por 4 semanas, aprovação de stakeholders.

## Linhas de trabalho transversais

- **Scripts helpers**: expandir catálogo conforme subtask 22.9 e incluir no
  fluxo CI (execução antes de merges críticos).
- **Knowledge Base**: registrar decisões importantes no `.cursor/kb/`
  seguindo [knowledge_base.mdc](mdc:.cursor/rules/knowledge_base.mdc).
- **Treinamento**: sessões quinzenais com equipe para revisar fluxos e
  ajustar AGENTS.md.

## Indicadores e metas

| Métrica | Meta | Observações |
| --- | --- | --- |
| Latência média de trade | ≤ baseline + 20% | Monitorar via Prometheus |
| Falhas por agente | < 3 por semana | Alertas automáticos |
| Event gap | 0 | Verificar EventService |
| Cobertura de testes | ≥ 80% | Foco em fluxos críticos |
| Tempo de resolução de incidentes | < 1h | Scripts helpers + runbooks |

## Dependências externas

- Aprovação de orçamento para APIs (Polygon, Dappier).
- Disponibilidade de infraestrutura (Redis, Prometheus, Grafana, vault).
- Sincronização com compliance para requisitos de auditoria.

## Próximas ações

1. Validar roadmap com stakeholders técnicos/compliance.
2. Iniciar implementação da Fase 0 imediatamente após aprovação.
3. Atualizar Task Master com subtasks/épicos por fase e vincular scripts
   helpers quando prontos.


