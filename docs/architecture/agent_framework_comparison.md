# Agent Framework Comparison

## Objetivo

Comparar frameworks de agentes populares (LangChain/LangGraph, Microsoft
AutoGen, Microsoft Agent Framework) quanto à adequação para o bot de
trading agentic.

## 1. Resumo executivo

| Framework | Linguagem principal | Ponto forte | Riscos/limitações | Adequação |
| --- | --- | --- | --- | --- |
| **LangGraph (LangChain)** | Python/JS | Orquestração de grafos, memória persistente, ferramentas amplas | Exige setup de armazenamento (Redis/Postgres) e observabilidade customizada | Alta (integra-se bem com MCPs e stack Python) |
| **Microsoft AutoGen** | Python | Multi-agentes conversacionais com padrões prontos (debate, team) | Orientado a conversação; precisa adaptar para workloads long-running | Média (bom para protótipos de colaboração/decisão) |
| **Microsoft Agent Framework** | .NET/Python (em expansão) | Integração corporativa, bindings M365, foco em segurança | Forte acoplamento a ecossistema MS, maturidade Python ainda crescendo | Média/baixa (relevante se adotar stack híbrida .NET) |

## 2. Avaliação detalhada

### 2.1 LangGraph / LangChain

- **Características**: grafos de execução, checkpoints, retry policies,
  streaming, human-in-the-loop, suporte a memórias duráveis (Redis,
  Postgres, Mongo), integração com MCPs via projetos comunitários.
- **Vantagens**:
  - Ecosistema maduro com conectores (OpenAI, Anthropic, tools diversas);
  - Facilita modelar Strategy/Risk/Execution Agents como nós de grafo;
  - Compatível com Redis MCP (checkpoint store) e Prometheus/Grafana via
    instrumentação custom.
- **Desafios**:
  - Requer infraestrutura adicional para estados (Redis/Postgres);
  - Precisará de camada de observabilidade/alerting custom.
- **Aplicação sugerida**: orquestrar workflows de trading (ex. pipeline de
  ingestão → estratégia → execução → risco) com persistência e retomada.

### 2.2 Microsoft AutoGen

- **Características**: framework multi-agente conversacional com padrões
  como debate, round-robin, planejador/executor; suporte a ferramentas e
  integração com OpenAI/Azure.
- **Vantagens**:
  - Padrões prontos para colaboração de especialistas (Strategy vs Risk);
  - Suporte built-in a mensagens estruturadas e supervisores;
  - Comunidade ativa com exemplos de avaliação e monitoramento.
- **Desafios**:
  - Enfoque inicial em conversas; precisa adaptar para tarefas orientadas a
    eventos/streaming;
  - Menor ênfase em persistência e estados long-running.
- **Aplicação sugerida**: protótipos de discussão/validação entre agentes
  (ex. debate de estratégias ou revisão de propostas do Execution Agent).

### 2.3 Microsoft Agent Framework

- **Características**: plataforma multi-linguagem (foco .NET) com SDKs para
  agentes M365, Teams, Copilot; ênfase em segurança, compliance e canais
  corporativos.
- **Vantagens**:
  - Integração com ecossistema MS (Teams, Graph, Identity);
  - Ferramentas de orquestração, logging e deployment corporativo.
- **Desafios**:
  - Ferramentas Python ainda em evolução; stack principal .NET;
  - Menos orientado a workloads financeiros de baixa latência;
  - Introduz heterogeneidade tecnológica (mistura .NET + Python).
- **Aplicação sugerida**: se for necessário expor agentes diretamente para
  plataformas Microsoft (Teams dashboards, Copilot), como camada externa.

## 3. Critérios comparados

| Critério | LangGraph | AutoGen | MS Agent Framework |
| --- | --- | --- | --- |
| **Estado & durabilidade** | Checkpoints nativos com stores plugáveis | Limitado (scripts próprios) | Focado em stateful services corporativos |
| **Ferramentas prontas** | Amplo catálogo LangChain/LCEL | Padrões de colaboração (debate, planner) | Integrado com M365/APIs corporativas |
| **Integração MCP** | Comunidade ativa e exemplos (LangGraph MCP) | Necessário adaptar (tools custom) | Depende de bindings oficiais |
| **Escalabilidade** | Suporta distribuição (Redis, Kafka) | Focado em execuções controladas | Projetado para enterprise (Kubernetes, Azure) |
| **Curva de aprendizado** | Moderada (LangChain + grafos) | Moderada (padrões conversacionais) | Alta (stack corporativa) |
| **Alinhamento com stack atual (Python)** | Alto | Alto | Médio/Baixo |

## 4. Recomendação

1. **Adotar LangGraph** como plataforma principal para orquestração de
   agentes internos (Strategy, Execution, Risk, Ops), aproveitando
   integrações com Redis MCP e armazenamento durável.
2. **Utilizar AutoGen** para cenários de colaboração/human-in-the-loop
   (ex.: debates de estratégia, revisão de decisões antes de envio).
3. **Monitorar Microsoft Agent Framework** para integrações corporativas ou
   exposição de agentes em canais M365; considerar apenas quando houver
   requisito explícito.

## 5. Próximos passos sugeridos

1. Desenvolver prova de conceito LangGraph com pipeline completo (dados →
   estratégia → execução → risco) usando Redis MCP como checkpoint store.
2. Criar protótipo AutoGen para sessões de revisão de sinais envolvendo
   Risk Agent + Execution Agent + operador humano.
3. Documentar requisitos se for necessário interface Teams/SharePoint e,
   nesse caso, avaliar piloto com Microsoft Agent Framework.


