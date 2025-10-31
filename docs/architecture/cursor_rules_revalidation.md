# Cursor Rules Revalidation

## Objetivo

Registrar a revisão das regras existentes em `.cursor/rules/` e
identificar ajustes necessários para suportar a adoção do padrão
AGENTS.md e da arquitetura agentic.

## 1. Inventário das regras atuais

| Arquivo | Escopo |
| --- | --- |
| `cursor_rules.mdc` | Metarregra de formatação/manutenção de rules |
| `code_quality.mdc` | Padrões de qualidade (Black, Ruff, MyPy, pytest) |
| `context7_integration.mdc` | Uso obrigatório do Context7 para pesquisa |
| `development_workflow.mdc` | Workflow geral de desenvolvimento |
| `event_sourcing.mdc` | Diretrizes para EventRepository e domínios |
| `git_workflow.mdc` | Branching, commits e PRs |
| `github_templates.mdc` | Uso dos templates de PR/issue |
| `knowledge_base.mdc` | Consulta e criação de entradas KB |
| `self_improve.mdc` | Atualização de regras quando padrões mudam |
| `taskmaster_priority.mdc` | Enfatiza Task Master como prioridade #1 |
| `taskmaster/dev_workflow.mdc`, `taskmaster/taskmaster.mdc` | Referências detalhadas do Task Master |

## 2. Principais achados

- **Coesão geral**: regras existentes cobrem qualidade, Task Master e
  workflows de desenvolvimento, mas não explicitam como AGENTS.md, MCPs e
  agentes devem interagir.
- **Redundâncias**: algumas instruções sobre Task Master aparecem em mais
  de um arquivo; manter `taskmaster/dev_workflow.mdc` como fonte primária.
- **Lacunas**:
  - Ausência de diretrizes explícitas para uso/atualização do arquivo
    `AGENTS.md`.
  - Falta de referência cruzada entre regras e MCPs priorizados (ex.
    Redis/Prometheus) para agentes.
  - Necessidade de orientar como registrar ajustes de regras quando novos
    agentes/scrips helpers forem adotados.

## 3. Atualizações executadas

1. **Nova regra** `agentic_workflow.mdc` criada:
   - Consolida requisitos para AGENTS.md, Task Master, Context7 e MCPs.
   - Fornece checklist para agentes (pesquisa, branch-per-task,
     atualização de documentação) e linka regras relacionadas.
2. **Cross-reference**: documento ressalta que qualquer atualização em
   AGENTS.md ou regras específicas deve ser registrada em `knowledge_base`
   e, quando aplicável, gerar subtasks no Task Master.

## 4. Recomendações adicionais

- Manter revisão trimestral das rules com foco em agentes (Strategy,
  Risk, Execution) para garantir que novos padrões sejam incorporados.
- Ao introduzir novos MCPs prioritários (Redis, Prometheus, Grafana,
  Polygon), atualizar `agentic_workflow.mdc` e AGENTS.md com instruções de
  configuração e segurança.
- Documentar scripts helpers aprovados dentro de uma futura regra
  específica após conclusão da subtask 22.9.

## 5. Dependências

- Atualizações complementares serão refletidas no relatório final da task
  22 e no roadmap (subtasks 22.7 e 22.8).
- Recomenda-se revisar novamente `development_workflow.mdc` após a
  implementação das PoCs de MCP para assegurar alinhamento contínuo.


