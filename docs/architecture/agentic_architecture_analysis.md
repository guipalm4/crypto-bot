# Agentic Architecture Analysis

## Objective

Documentar o panorama atual da arquitetura do bot de trading e estabelecer
referências para avaliar a adoção de um padrão agentic orientado por
AGENTS.md, alinhado à task 22.1.

## 1. Arquitetura Atual (Visão Geral)

- **Domain**: entidades, value objects e contratos de repositórios.
- **Application**: serviços orquestradores (`TradingService`,
  `RiskService`, `EventService`), DTOs e interfaces.
- **Infrastructure**: persistência (SQLAlchemy), adapters CCXT,
  configurações específicas de ambiente.
- **Plugins**: estratégias, indicadores e exchanges registrados via entry
  points (`plugins/registry.py`).
- **Observabilidade**: logging estruturado e event sourcing garantem
  rastreabilidade (`utils/structured_logger.py`, `EventService`).

Fluxo resumido:
1. Estratégias (plugins) processam dados de mercado e geram sinais.
2. `TradingService` executa ordens via CCXT com retries e timeouts.
3. `RiskService` monitora posições, aplica regras e aciona
   `RiskActionHandler` quando necessário.
4. `EventService` registra eventos de domínio para auditoria.

## 2. Componentes e Responsabilidades

| Componente atual | Responsabilidade | Observações para agentes |
| --- | --- | --- |
| Estratégias (plugins) | Lógica de decisão de trading baseada em indicadores | Candidatas naturais a *Strategy Agents* independentes por estratégia ou portfólio. |
| Indicadores (plugins) | Cálculo de métricas técnicas (RSI, MACD, EMA) | Podem se tornar serviços compartilhados consumidos via mensageria por múltiplos agentes. |
| TradingService | Execução assíncrona de ordens, integração CCXT, retries/timeout | Forte candidato a um *Execution Agent* dedicado. |
| RiskService + RiskActionHandler | Monitoramento contínuo de posições e aplicação de regras de risco | Pode evoluir para um *Risk Agent* com ciclo próprio. |
| EventService | Emissão de eventos de domínio e auditoria | Papel transversal que pode ser centralizado em um *Event & Compliance Agent*. |
| Infraestrutura de Config | Pydantic settings, perfis de ambiente, credenciais | Exige mecanismo seguro de compartilhamento de configuração entre agentes. |
| Observabilidade | Logging estruturado, métricas | Necessário padronizar telemetria por agente. |

## 3. Agentes Propostos

- **Market Intelligence Agent**: agrega dados de mercado, executa
  indicadores e disponibiliza streams para outros agentes.
- **Strategy Agent(s)**: encapsulam a lógica de decisão por estratégia ou
  portfólio, consumindo dados do Market Intelligence Agent.
- **Execution Agent**: comunica-se com exchanges (CCXT), gerencia ordens e
  fornece feedback de execução.
- **Risk Agent**: monitora posições, avalia regras de risco e instrui o
  Execution Agent a ajustar posições.
- **Event & Compliance Agent**: garante trilha de auditoria, enriquece
  eventos e monitora conformidade com regras de segurança.
- **Ops & Monitoring Agent**: acompanha saúde do sistema, ativa alertas e
  coordena ações corretivas cross-agent.

## 4. Critérios de Avaliação

1. **Autonomia e orquestração**: capacidade de agentes operarem com
   coordenação mínima e protocolos claros (mensageria, eventos).
2. **Escalabilidade horizontal**: facilidade de escalar agentes
   específicos sem reestruturar o núcleo da aplicação.
3. **Latência e determinismo**: impacto de hops assíncronos adicionais em
   relação às chamadas internas atuais.
4. **Observabilidade e auditoria**: preservação da consistência do
   event sourcing e logging estruturado.
5. **Governança e segurança**: gerenciamento de credenciais e limites de
   risco em ambiente distribuído.
6. **Compatibilidade com plugins**: manutenção da flexibilidade atual para
   estratégias e indicadores dinâmicos.
7. **Complexidade operacional**: custo para operar filas, schedulers e
   múltiplos agentes em produção.

## 5. Gaps e Considerações

- Necessidade de um serviço compartilhado de configuração segura para
  evitar divergências entre agentes.
- Definir protocolo de comunicação (mensageria, pub/sub, event bus) para
  acoplamento baixo entre Strategy, Risk e Execution Agents.
- Enriquecer logs e eventos com metadata de agente para garantir
  rastreabilidade em um ambiente distribuído.
- Avaliar impacto em latência ao mover loops assíncronos (ex.
  `RiskService`) para processos independentes.
- Revisar como o padrão AGENTS.md será estruturado por domínio (ex. um
  AGENTS.md raiz + diretórios específicos por agente ou pacote).

## 6. Próximos Passos

- Produzir diagramas de fluxo atual e do modelo agentic proposto.
- Detalhar orquestração via MCPs (Task Master, Context7, GitHub) nas
  subtasks seguintes.
- Mapear requisitos não funcionais (latência, tolerância a falhas,
  compliance) para alimentar a matriz de comparação.
- Validar o mapeamento de agentes com stakeholders técnicos antes de
  avançar para estimativas de migração.


