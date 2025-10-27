# 📋 Pull Request

## 📝 Descrição
<!-- Descreva as mudanças feitas neste PR -->

## 🔗 Issues Relacionadas
<!-- Lista de issues que este PR resolve -->
Closes #
Fixes #
Relates to #

## 🎯 Tipo de Mudança
- [ ] 🐛 Bug fix (mudança que corrige um problema)
- [ ] ✨ Nova feature (mudança que adiciona funcionalidade)
- [ ] 💥 Breaking change (correção ou feature que causaria mudança em funcionalidade existente)
- [ ] 📚 Documentação (mudanças apenas na documentação)
- [ ] 🎨 Refatoração (mudança de código que não corrige bug nem adiciona feature)
- [ ] ⚡ Performance (mudança que melhora performance)
- [ ] 🧪 Testes (adição ou correção de testes)
- [ ] 🔧 Configuração (mudanças em arquivos de configuração)

## 🧪 Como Testar
<!-- Instruções para testar as mudanças -->
1. 
2. 
3. 

## 📋 Checklist
- [ ] ✅ Meu código segue as diretrizes de estilo do projeto
- [ ] ✅ Realizei uma auto-revisão do meu código
- [ ] ✅ Comentei partes do código difíceis de entender
- [ ] ✅ Minhas mudanças não geram warnings
- [ ] ✅ Adicionei testes que provam que minha correção é eficaz ou que minha feature funciona
- [ ] ] ✅ Testes novos e existentes passam localmente
- [ ] ✅ Qualquer mudança dependente foi mergeada e publicada

### Regras de Event Sourcing (Obrigatório se tocar em eventos/repositórios)
- [ ] 🔒 `EventRepository` mantém separação domínio/ORM (conversão interface↔modelo)
- [ ] 🔒 `create()` aceita/retorna `DomainEvent` (domínio); conversão para `DomainEventModel` interna
- [ ] 🔒 Nenhum `Session.add()` recebe classe de domínio (`domain.repositories.event_repository.DomainEvent`)

## 📸 Screenshots/Logs
<!-- Se aplicável, adicione screenshots ou logs relevantes -->

## 🔒 Segurança
<!-- Se aplicável, mencione considerações de segurança -->
- [ ] ✅ Não expõe credenciais ou dados sensíveis
- [ ] ✅ Valida todas as entradas do usuário
- [ ] ✅ Usa práticas seguras de criptografia
- [ ] ✅ Não introduz vulnerabilidades conhecidas

## 📊 Performance
<!-- Se aplicável, mencione impactos na performance -->
- [ ] ✅ Não degrada performance significativamente
- [ ] ✅ Otimizações de performance implementadas
- [ ] ✅ Testes de performance executados

## 📚 Documentação
<!-- Se aplicável, mencione mudanças na documentação -->
- [ ] ✅ Atualizei a documentação relevante
- [ ] ✅ Adicionei comentários no código
- [ ] ✅ Atualizei README se necessário

## 🔄 Breaking Changes
<!-- Se aplicável, liste breaking changes -->
- [ ] ✅ Não há breaking changes
- [ ] ⚠️ Breaking changes documentados abaixo

## 📝 Notas Adicionais
<!-- Qualquer informação adicional relevante -->
