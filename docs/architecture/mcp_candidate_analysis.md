# MCP Candidates Assessment

## Objetivo

Identificar MCPs adicionais que possam agregar valor ao bot de trading,
avaliando compatibilidade com a arquitetura atual, benefícios esperados e
esforço de integração.

## 1. Categorias consideradas

| Categoria | Necessidade principal |
| --- | --- |
| **Mercado & Blockchain** | Acesso a dados de mercado em tempo real, DeFi, histórico financeiro |
| **Observabilidade** | Métricas, alertas e visualização (Prometheus/Grafana) |
| **Persistência & Cache** | Armazenamento rápido, filas, memória compartilhada (Redis) |
| **Memória/Contexto** | Histórico consolidado de decisões e progresso (Memory Bank) |
| **Integração externa** | APIs adicionais (fetch, web crawling, mensagens) |

## 2. Candidatos avaliados

| MCP | Categoria | Valor agregado | Esforço estimado | Observações |
| --- | --- | --- | --- | --- |
| **Polygon.io MCP** (`/polygon-io/mcp_polygon`) | Mercado | Acesso a dados de bolsa (equities, crypto) com interface MCP | Médio | Necessita chave API; útil para backtesting e monitoramento. |
| **Financial Datasets MCP** (docker repo) | Mercado | API de mercado pronta para agentes com suporte a histórico | Médio | Ideal para PoC de agentes analíticos; validar limites de uso. |
| **Dappier MCP** (`dappier_mcp`) | Mercado | Modelos de dados específicos (notícias, finanças, crypto) | Médio | Complementa dados de mercado com contexto de notícias. |
| **DeFi Rates MCP** (`/qingfeng/defi-rates-mcp`) | DeFi | Taxas em protocolos DeFi para estratégias yield/risk | Médio | Útil para futuros agentes de arbitragem/risk. |
| **Moralis MCP** (`/moralisweb3/moralis-mcp-server`) | Blockchain | Dados on-chain multi-chain | Alto | Relevante se expandirmos para estratégias on-chain. |
| **Redis MCP** (`/redis/mcp-redis`) | Persistência/cache | Operações em Redis (listas, pub/sub, streams, vetores) | Baixo | Excelente para orquestração, filas e state store entre agentes. |
| **Redis Agent Memory** (`/redis/agent-memory-server`) | Memória | Memória semântica persistente | Médio | Pode complementar Context7 ou atuar como fallback local. |
| **Prometheus MCP** (`/pab1it0/prometheus-mcp-server`) | Observabilidade | Permite consultas e alertas em métricas Prometheus | Médio | Facilita monitoramento agentic e automação de mitigação. |
| **Grafana MCP** (`/grafana/mcp-grafana`) | Observabilidade | Gerenciamento de dashboards e incidentes | Médio | Integrar com Prometheus/Loki para visão end-to-end. |
| **Memory Bank MCP** (`/movibe/memory-bank-mcp`) | Memória | Armazena decisões, logs e progresso | Médio | Pode atuar como memória institucional para agentes. |
| **Fetch MCP** (`/zcaceres/fetch-mcp`) | Integração externa | Web scraping controlado, com JSDOM/Turndown | Baixo | Útil para coleta de notícias/regulatórios. |
| **Crawlbase MCP** (`/crawlbase/crawlbase-mcp`) | Integração externa | Web crawler com proxy rotation, JS rendering | Médio | Considerar para dados mais complexos; avaliar custo. |
| **Kubernetes MCP** (`/flux159/mcp-server-kubernetes`) | Infraestrutura | Operações em clusters (deploys, scaling) | Alto | Relevante para fase de SRE/DevOps agentic. |

## 3. Priorização recomendada

| Prioridade | MCPs | Justificativa |
| --- | --- | --- |
| **Alta** | Redis MCP, Prometheus MCP, Grafana MCP, Polygon MCP | Endereçam requisitos imediatos: coordenação entre agentes, observabilidade, dados de mercado abrangentes. |
| **Média** | Financial Datasets, Dappier, DeFi Rates, Memory Bank, Fetch | Ampliação gradual de capacidades analíticas e de memória contextual. |
| **Baixa** | Moralis MCP, Crawlbase, Kubernetes MCP | Requerem maturidade maior (estratégias on-chain, crawling avançado, automação de infraestrutura). |

## 4. Critérios usados para avaliação

- **Compatibilidade** com arquitetura atual (Python async, plugin system, event sourcing).
- **Valor agregado** para agentes planejados (Strategy, Risk, Ops/Monitoring).
- **Complexidade de integração** (dependências, autenticação, infraestrutura). 
- **Maturidade/comunidade** do MCP (trust score, documentação, suporte).
- **Requisitos operacionais** (custos de API, segurança, governança de dados).

## 5. Gaps identificados

- **Mensageria dedicada**: avaliar MCPs ou implementação custom para RabbitMQ/Kafka caso redis-streams não seja suficiente.
- **Secrets Management**: não foi identificado MCP pronto para Vault ou AWS Secrets Manager; considerar desenvolvimento interno ou wrappers.
- **Alerting automático**: integrar Prometheus MCP com canais (ex. Discord MCP) para notificações agentic.
- **Backtesting histórico**: potencialmente combinar Polygon MCP com armazenamentos vectoriais (Chroma MCP) para construir datasets reutilizáveis.

## 6. Próximos passos sugeridos

1. **PoC** com Redis MCP para orquestração de mensagens entre Strategy e Execution Agents.
2. Integração inicial com Prometheus + Grafana MCP em ambiente de staging para monitoramento agentic.
3. Avaliar limites/custos de Polygon e Financial Datasets MCP antes de produção.
4. Planejar implementação de secrets via solução própria ou MCP custom.
5. Atualizar AGENTS.md com instruções de configuração para MCPs priorizados.


