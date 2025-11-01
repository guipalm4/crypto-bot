# 📝 Workflow de Atualização de Documentação

Este documento define o processo para manter a documentação atualizada junto com o desenvolvimento de features.

## 🎯 Princípios

1. **Documentação é Código**: Documentação deve ser versionada e revisada como código
2. **Documentação Simultânea**: Documentação deve ser atualizada junto com o código
3. **Revisão Inclui Docs**: Code review inclui revisão de documentação
4. **Automação Quando Possível**: Usar ferramentas para manter sincronização

## 📋 Checklist para Novas Features

Ao desenvolver uma nova feature, sempre atualize:

### 1. Docstrings no Código

```python
def new_feature(self, param: str) -> Result:
    """
    Descrição da nova funcionalidade.
    
    Args:
        param: Descrição do parâmetro
    
    Returns:
        Descrição do retorno
    
    Raises:
        ErrorType: Quando ocorre
    
    Example:
        >>> result = new_feature("value")
        >>> print(result)
    """
    pass
```

### 2. Documentação de Configuração

Se a feature adiciona novas opções de configuração:

- [ ] Atualizar `docs/CONFIGURATION_GUIDE.md`
- [ ] Adicionar ao schema em `src/crypto_bot/config/schemas.py`
- [ ] Adicionar ao `config/environments/base.yaml`
- [ ] Atualizar `.env.example` se necessário

### 3. Guias de Uso

Se a feature afeta uso da CLI ou API:

- [ ] Atualizar seção relevante no `README.md`
- [ ] Adicionar exemplos de uso
- [ ] Atualizar comandos da CLI se necessário

### 4. Documentação de Plugins

Se adiciona novo plugin ou altera sistema de plugins:

- [ ] Atualizar `docs/PLUGIN_DEVELOPMENT_GUIDE.md`
- [ ] Adicionar exemplos de código
- [ ] Documentar mudanças na interface base

### 5. Documentação de Segurança

Se afeta segurança:

- [ ] Atualizar `docs/SECURITY_PRACTICES.md`
- [ ] Adicionar ao checklist de segurança
- [ ] Documentar novas vulnerabilidades (se aplicável)

## 🔄 Processo de Desenvolvimento

### Durante Desenvolvimento

1. **Escreva docstrings** junto com o código
2. **Atualize documentação** enquanto desenvolve
3. **Mantenha sincronizado** código e docs

### No Commit

Inclua atualizações de documentação no mesmo commit do código:

```bash
git add src/crypto_bot/new_feature.py
git add docs/NEW_FEATURE_GUIDE.md
git commit -m "feat(feature): add new feature with documentation"
```

### No Pull Request

O template de PR já inclui checklist de documentação:

```markdown
## 📚 Documentação
- [ ] ✅ Atualizei a documentação relevante
- [ ] ✅ Adicionei comentários no código
- [ ] ✅ Atualizei README se necessário
```

## 📂 Onde Documentar

### Estrutura de Documentação

```
docs/
├── CONFIGURATION_GUIDE.md          # Configurações e opções
├── PLUGIN_DEVELOPMENT_GUIDE.md     # Desenvolvimento de plugins
├── SECURITY_PRACTICES.md            # Práticas de segurança
├── API_DOCUMENTATION.md             # Geração de API docs
├── DOCUMENTATION_WORKFLOW.md        # Este arquivo
├── TESTING_SETUP.md                 # Setup de testes
├── CODING_STANDARDS.md              # Padrões de código
├── WORKFLOW_QUICK_START.md          # Workflow de desenvolvimento
├── security/                        # Documentos de segurança
│   ├── SECURITY_BASELINE.md
│   ├── HARDENING_GUIDE.md
│   └── KEY_ROTATION_PLAYBOOK.md
└── architecture/                    # Documentos de arquitetura
    └── strategy_plugins.md
```

### Tipo de Documento por Feature

| Tipo de Feature | Documentos a Atualizar |
|----------------|----------------------|
| Nova configuração | `CONFIGURATION_GUIDE.md`, schema, YAML |
| Novo plugin | `PLUGIN_DEVELOPMENT_GUIDE.md`, exemplos |
| Mudança de segurança | `SECURITY_PRACTICES.md`, `security/` |
| Nova CLI command | `README.md` (seção CLI) |
| Nova API endpoint | `API_DOCUMENTATION.md`, docstrings |
| Mudança de arquitetura | `architecture/`, `README.md` |

## ✅ Template de Checklist para PRs

Copie e cole no seu PR:

```markdown
### Documentação
- [ ] Docstrings adicionados/atualizados no código
- [ ] README.md atualizado (se aplicável)
- [ ] Guias específicos atualizados:
  - [ ] CONFIGURATION_GUIDE.md (se adiciona configurações)
  - [ ] PLUGIN_DEVELOPMENT_GUIDE.md (se altera plugins)
  - [ ] SECURITY_PRACTICES.md (se afeta segurança)
  - [ ] Outros guias relevantes
- [ ] Exemplos de código/testes atualizados
- [ ] Links no README verificados
```

## 🔍 Revisão de Documentação

### Durante Code Review

Revisores devem verificar:

1. **Docstrings completos?**
   - Todas as funções públicas têm docstrings?
   - Args, Returns, Raises documentados?
   - Exemplos fornecidos quando útil?

2. **Documentação atualizada?**
   - Guias relevantes foram atualizados?
   - Exemplos ainda funcionam?
   - Links quebrados corrigidos?

3. **Consistência?**
   - Terminologia consistente?
   - Formato de docstrings consistente?
   - Estilo de escrita consistente?

## 🤖 Automação

### Pre-commit Hook (Opcional)

Adicionar verificação de docstrings:

```bash
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/pydocstyle
    rev: 6.3.0
    hooks:
      - id: pydocstyle
        args: [--convention=google, src/crypto_bot]
```

### CI/CD Checks

```yaml
# .github/workflows/docs-check.yml
name: Documentation Check

on: [pull_request]

jobs:
  check-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check docstrings
        run: |
          pip install pydocstyle
          pydocstyle --convention=google src/crypto_bot
      - name: Check broken links
        run: |
          pip install linkchecker
          find docs -name "*.md" -exec linkchecker {} \;
```

## 📝 Exemplos

### Exemplo 1: Nova Feature de Configuração

**Código:**
```python
# src/crypto_bot/config/schemas.py
class NewFeatureConfig(BaseModel):
    enabled: bool = False
    option: str = "default"
```

**Documentação:**
1. Atualizar `CONFIGURATION_GUIDE.md` com nova seção
2. Adicionar exemplo em `base.yaml`
3. Adicionar variável de ambiente no `.env.example`

### Exemplo 2: Novo Plugin

**Código:**
```python
# src/crypto_bot/plugins/strategies/new_strategy.py
class NewStrategy(Strategy):
    name = "new_strategy"
    # ...
```

**Documentação:**
1. Atualizar `PLUGIN_DEVELOPMENT_GUIDE.md` com exemplo
2. Adicionar docstring completa no código
3. Atualizar lista de estratégias no README

### Exemplo 3: Nova CLI Command

**Código:**
```python
# src/crypto_bot/cli/main.py
@main.command()
def new_command():
    """Nova funcionalidade da CLI."""
    pass
```

**Documentação:**
1. Atualizar seção CLI no `README.md`
2. Adicionar exemplo de uso
3. Adicionar docstring com `@click` help

## 🚨 Quando a Documentação está Atrasada

Se você encontrar documentação desatualizada:

1. **Crie uma issue** marcando como `documentation`
2. **Ou atualize diretamente** se souber as mudanças
3. **Mencione no PR** se corrigir documentação desatualizada

## 📚 Referências

- [Google Python Style Guide - Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- [Sphinx Documentation](https://www.sphinx-doc.org/)
- [MkDocs Documentation](https://www.mkdocs.org/)

## ✅ Checklist de Manutenção Periódica

Execute periodicamente (mensal ou trimestral):

- [ ] Revisar todos os guias para informações desatualizadas
- [ ] Verificar links quebrados
- [ ] Atualizar exemplos de código
- [ ] Revisar docstrings de módulos principais
- [ ] Verificar consistência de terminologia
- [ ] Atualizar screenshots/capturas (se aplicável)
- [ ] Verificar se novas features estão documentadas

---

**💡 Lembre-se**: Boa documentação economiza tempo a longo prazo e facilita onboarding de novos desenvolvedores!
