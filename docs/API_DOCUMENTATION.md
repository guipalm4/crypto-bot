# 📚 Documentação de API

Este documento descreve como gerar e manter a documentação da API do Crypto Trading Bot.

## 🔧 Ferramentas Recomendadas

### Opção 1: Sphinx (Recomendado para Python)

Sphinx é a ferramenta padrão da comunidade Python para documentação.

**Instalação:**

```bash
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints
```

**Configuração:**

```bash
# Criar estrutura inicial
sphinx-quickstart docs/api-sphinx

# Gerar documentação a partir de docstrings
sphinx-apidoc -o docs/api-sphinx src/crypto_bot
```

**Exemplo de `conf.py`:**

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",  # Google/NumPy style docstrings
    "sphinx_autodoc_typehints",
]

html_theme = "sphinx_rtd_theme"
```

**Gerar documentação:**

```bash
cd docs/api-sphinx
make html
```

### Opção 2: MkDocs com mkdocstrings

MkDocs oferece uma experiência mais moderna e fácil de usar.

**Instalação:**

```bash
pip install mkdocs mkdocstrings[python] mkdocs-material
```

**Configuração `mkdocs.yml`:**

```yaml
site_name: Crypto Trading Bot API
theme:
  name: material

plugins:
  - mkdocstrings:
      handlers:
        python:
          paths: [src]

nav:
  - Home: index.md
  - API Reference:
    - Services: api/services.md
    - Plugins: api/plugins.md
    - DTOs: api/dtos.md
```

**Gerar documentação:**

```bash
mkdocs build
mkdocs serve  # Para visualização local
```

### Opção 3: pydoc (Built-in Python)

Para documentação rápida sem dependências externas:

```bash
# Gerar HTML de um módulo
pydoc -w crypto_bot.application.services.trading_service

# Servir documentação interativa
pydoc -p 8000
```

## 📝 Formatando Docstrings

O projeto usa **Google-style docstrings**:

```python
def fetch_balance(
    self,
    exchange: str,
    currency: str | None = None,
) -> Dict[str, BalanceDTO]:
    """
    Fetch account balance for specified exchange and currency.
    
    Args:
        exchange: Exchange name (e.g., 'binance', 'coinbase')
        currency: Optional currency code. If None, returns all currencies.
    
    Returns:
        Dictionary mapping currency codes to BalanceDTO objects.
        
    Raises:
        ExchangeError: If the exchange API request fails.
        NetworkError: If there's a network connectivity issue.
        
    Example:
        >>> service = TradingService()
        >>> balance = await service.fetch_balance('binance')
        >>> print(balance['USDT'].free)
        Decimal('1000.00')
    """
    pass
```

## 🔄 Integração no CI/CD

### GitHub Actions Example

```yaml
# .github/workflows/docs.yml
name: Generate API Documentation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install sphinx sphinx-rtd-theme
          pip install -r requirements.txt
      
      - name: Generate documentation
        run: |
          sphinx-apidoc -o docs/api-sphinx src/crypto_bot
          cd docs/api-sphinx
          make html
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: docs/api-sphinx/_build/html
```

## 📂 Estrutura Recomendada

```
docs/
├── api/
│   ├── index.md              # Overview da API
│   ├── services/             # Documentação de serviços
│   │   ├── trading_service.md
│   │   ├── risk_service.md
│   │   └── strategy_orchestrator.md
│   ├── plugins/              # Documentação de plugins
│   │   ├── exchanges.md
│   │   ├── indicators.md
│   │   └── strategies.md
│   ├── dtos/                 # Documentação de DTOs
│   │   └── order_dtos.md
│   └── sphinx/               # Build do Sphinx (gerado)
│       ├── conf.py
│       ├── index.rst
│       └── _build/
└── ...
```

## 🔗 Links para Documentação Gerada

Após gerar a documentação, adicione links no README:

```markdown
## 📚 Documentação

- [API Reference](https://guipalm4.github.io/crypto-bot/api/) - Documentação completa da API
- [Configuration Guide](docs/CONFIGURATION_GUIDE.md) - Guia de configuração
- [Plugin Development](docs/PLUGIN_DEVELOPMENT_GUIDE.md) - Desenvolvimento de plugins
```

## ✅ Checklist de Documentação

Antes de considerar a documentação completa:

- [ ] Todos os módulos públicos documentados
- [ ] Todos os métodos públicos têm docstrings
- [ ] Exemplos de uso em docstrings principais
- [ ] Type hints completos
- [ ] Documentação gerada e acessível
- [ ] Links no README atualizados
- [ ] CI/CD configurado para gerar docs automaticamente
- [ ] Documentação publicada (GitHub Pages ou similar)

## 📝 Notas

**Status Atual:**
- ✅ Docstrings completos nos módulos principais
- ⚠️ Geração automática de API docs ainda não configurada
- ✅ Documentação manual completa (guides, configuration, etc.)

**Próximos Passos:**
1. Configurar Sphinx ou MkDocs
2. Integrar geração no CI/CD
3. Publicar documentação automaticamente
4. Adicionar links no README

---

**Nota**: A documentação manual (guides, configuration, etc.) já está completa. A geração automática de API docs pode ser implementada quando necessário.
