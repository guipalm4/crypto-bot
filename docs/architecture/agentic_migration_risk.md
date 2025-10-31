# Migration Cost & Risk Assessment

## Objetivo

Avaliar custos, riscos e impactos da migração da arquitetura atual baseada
em serviços/plugins para um modelo agentic.

## 1. Componentes impactados

- **Orquestração**: extração de `TradingService`, `RiskService` e
  estratégias para agentes independentes.
- **Persistência/event sourcing**: garantir consistência de eventos e
  logs em ambiente distribuído.
- **Configurações**: sincronização de Pydantic settings e segredos entre
  múltiplos agentes.
- **Observabilidade**: instrumentação adicional (Prometheus/Grafana MCP).
- **Operações**: gestão de filas, mensageria, retrys e escalabilidade.

## 2. Estimativa de custos (ordem de grandeza)

| Área | Itens | Esforço inicial |
| --- | --- | --- |
| Engenharia | Implementar orquestrador (LangGraph), adapters MCP, scripts helpers | 6–8 semanas |
| Infraestrutura | Provisionar Redis/Prometheus/Grafana, pipelines CI/CD, secrets vault | 4–6 semanas |
| Observabilidade & QA | Ajustar EventService/logging, cobertura de testes E2E agentic | 3–4 semanas |
| Enablement | Treinamento equipe, atualização de docs (AGENTS.md, rules) | 2 semanas |

Valores estimados para equipe dedicada de 3–4 devs + 1 SRE.

## 3. Matriz de risco

| Risco | Prob. | Impacto | Mitigação |
| --- | --- | --- | --- |
| **Inconsistência de estado** (transações distribuídas) | Média | Alto | Uso de Redis streams/checkpoints + testes de consistência; EventService como autoridade. |
| **Latência aumentada** (hops entre agentes) | Média | Alto | Benchmark em PoC, otimização de filas, priorização de caminhos críticos (execução). |
| **Sobrecarga operacional** | Alta | Médio | Automação via scripts helpers, monitoramento centralizado, runbooks. |
| **Falta de governança de segredos** | Alta | Alto | Implementar vault/secret manager antes da produção. |
| **Custo de APIs externas** | Média | Médio | Negociar planos (Polygon, Dappier) e estabelecer limites/alertas. |
| **Dependência de framework imaturo** | Baixa | Médio | Escolher frameworks com comunidade ativa (LangGraph), manter fallback síncrono. |
| **Regressões funcionais** | Média | Alto | Testes E2E com cenários críticos (stop-loss, emergency exit). |

## 4. Estratégia de mitigação

1. **Fase 0** (Preparação): infraestrutura básica (Redis, Prometheus,
   secrets), scripts helpers mínimos, atualização de AGENTS.md/rules.
2. **Fase 1** (PoC controlado): agentes Strategy + Execution com volume
   reduzido, monitoramento intensivo.
3. **Fase 2** (Expansão): incluir Risk Agent e Event & Compliance, testes E2E
   completos, integração MCP prioritária.
4. **Fase 3** (Hardening): tuning de performance, automação de
   rollback/failover, auditoria de segurança.

## 5. Indicadores de sucesso

- Latência média por trade dentro de limites pré-estabelecidos.
- Zero perda de eventos críticos (auditoria).
- Cobertura de testes >= 80% em fluxos agentic.
- Alertas e dashboards configurados (Prometheus/Grafana MCP).
- Scripts helpers adotados pelo time (feedback positivo e redução de erros).

## 6. Decisões pendentes

- Selecionar tecnologia de mensageria (Redis streams vs Kafka/RabbitMQ).
- Definir política de versionamento de agentes e rollback.
- Planejar estratégia de rollback para retornar ao modo plugin em caso de
  falha crítica.


