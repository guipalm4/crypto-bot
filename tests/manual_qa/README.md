# 🧪 Testes Manuais e QA - Crypto Trading Bot MVP

Este diretório contém os testes automatizados criados a partir dos testes manuais realizados por QA Senior, seguindo boas práticas e separados dos testes unit, integration e e2e existentes.

## 📁 Estrutura de Diretórios

```
tests/manual_qa/
├── README.md                    # Este arquivo
├── cli/                         # Testes de CLI
├── exchange/                    # Testes de integração com exchanges
├── strategy/                    # Testes de estratégias de trading
├── risk/                        # Testes de gestão de risco
├── config/                      # Testes de configuração e persistência
├── security/                    # Testes de segurança e criptografia
├── exploratory/                 # Testes exploratórios e edge cases
└── fixtures/                    # Fixtures compartilhadas
```

## 🎯 Objetivo

Estes testes foram criados após validação manual completa das funcionalidades do MVP, seguindo uma abordagem crítica e realista de QA. Cada teste automatizado representa um cenário validado manualmente que simula ações reais de usuário.

## ✅ Processo de Criação

1. **Teste Manual**: Execução de cenários como um usuário real
2. **Validação**: Confirmar comportamento esperado vs real
3. **Automação**: Criar teste automatizado para cenário validado
4. **Bug Tracking**: Registrar bugs encontrados (veja `BUG_REPORT_TEMPLATE.md`)

## 📝 Convenções

### Nomenclatura de Testes
- Use nomes descritivos que expliquem o que está sendo testado
- Padrão: `test_<feature>_<scenario>_<expected_behavior>`
- Exemplo: `test_cli_start_command_with_dry_run_mode_simulates_trades`

### Organização
- Um arquivo de teste por feature/funcionalidade principal
- Agrupar testes relacionados por classe quando apropriado
- Usar fixtures do diretório `fixtures/` para dados compartilhados

### Boas Práticas
- Testes isolados e independentes
- Mock de dependências externas (exchanges, APIs)
- Dados de teste consistentes e reutilizáveis
- Comentários explicativos quando necessário
- Tratamento adequado de casos de erro

## 🐛 Reporte de Bugs

Ao encontrar um bug durante os testes manuais:

1. Documentar em `docs/qa/BUG_REPORTS.md`
2. Seguir o template em `docs/qa/BUG_REPORT_TEMPLATE.md`
3. Criar issue no GitHub
4. Criar tarefa no Task Master para correção

## 🔄 Integração com CI/CD

Estes testes são executados no pipeline de CI/CD junto com os outros testes:

```bash
# Executar apenas testes manuais de QA
pytest tests/manual_qa/

# Executar com cobertura
pytest tests/manual_qa/ --cov=src/crypto_bot

# Executar com verbose
pytest tests/manual_qa/ -v
```

## 📊 Status dos Testes

- ⏳ **Pendente**: Cenário ainda não foi testado manualmente
- ✅ **Validado**: Teste manual concluído com sucesso
- 🤖 **Automatizado**: Teste automatizado criado e passando
- 🐛 **Bug Encontrado**: Problema identificado, issue criado

---

**Nota**: Estes testes complementam mas não substituem os testes unitários, de integração e E2E. Eles focam em cenários de uso real e validação comportamental do ponto de vista do usuário final.

