# Context7 MCP Setup - Crypto Trading Bot

## 🎯 Objetivo

Configurar o Context7 MCP para evitar erros de sintaxe e manter o código atualizado com as melhores práticas das bibliotecas utilizadas no projeto.

## 📋 Configuração Atual

### 1. **MCP Server Configurado**
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"],
      "env": {
        "CONTEXT7_API_KEY": "YOUR_CONTEXT7_API_KEY_HERE"
      }
    }
  }
}
```

### 2. **Bibliotecas Prioritárias**
- **Pydantic v2** - Validação de dados e configurações
- **SQLAlchemy v2** - ORM e gerenciamento de banco
- **CCXT v4** - Integração com exchanges de cripto
- **Click v8** - Interface de linha de comando
- **Rich v13** - Formatação de saída
- **Pytest v7** - Framework de testes
- **AsyncIO** - Programação assíncrona

## 🚀 Como Usar

### 1. **Configuração Inicial**
```bash
# Instalar dependências
npm install -g @context7/mcp-server

# Configurar Context7
python scripts/setup-context7.py

# Validar sintaxe
python scripts/validate-syntax.py
```

### 2. **Durante o Desenvolvimento**

#### Antes de Escrever Código
1. Use o Context7 para verificar a sintaxe correta:
   - `mcp_context7_resolve-library-id` para encontrar a biblioteca
   - `mcp_context7_get-library-docs` para obter documentação

#### Exemplo de Uso
```python
# ❌ Sintaxe obsoleta (Pydantic v1)
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    class Config:
        env_file = ".env"
    
    database_url: str = Field(env="DATABASE_URL")

# ✅ Sintaxe correta (Pydantic v2)
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    database_url: str = Field(alias="DATABASE_URL")
```

### 3. **Validação Automática**
O pre-commit hook valida automaticamente:
- Sintaxe das bibliotecas
- Imports corretos
- Versões compatíveis

## 📚 Recursos Disponíveis

### 1. **Arquivos de Referência**
- `.cursor/syntax-reference.md` - Guia rápido de sintaxe
- `.cursor/context7-libraries.json` - Bibliotecas prioritárias
- `.cursor/context7-config.json` - Configuração do Context7

### 2. **Scripts de Validação**
- `scripts/validate-syntax.py` - Valida sintaxe das bibliotecas
- `scripts/setup-context7.py` - Configura e testa o Context7

### 3. **Pre-commit Hooks**
- Validação de sintaxe automática
- Formatação com Black
- Linting com Flake8
- Verificação de tipos com MyPy

## 🔧 Troubleshooting

### Problema: Context7 não está funcionando
```bash
# Verificar instalação
npx @context7/mcp-server --help

# Reinstalar se necessário
npm uninstall -g @context7/mcp-server
npm install -g @context7/mcp-server
```

### Problema: Erros de sintaxe
```bash
# Validar sintaxe
python scripts/validate-syntax.py

# Verificar imports
python -c "import pydantic_settings; print('OK')"
```

### Problema: Pre-commit falhando
```bash
# Instalar pre-commit
pip install pre-commit

# Instalar hooks
pre-commit install

# Executar manualmente
pre-commit run --all-files
```

## 📖 Documentação das Bibliotecas

### Pydantic v2
- [Documentação Oficial](https://docs.pydantic.dev/2.0/)
- [Migration Guide](https://docs.pydantic.dev/2.0/migration/)
- [Settings Management](https://docs.pydantic.dev/2.0/concepts/pydantic_settings/)

### SQLAlchemy v2
- [Documentação Oficial](https://docs.sqlalchemy.org/en/20/)
- [Migration Guide](https://docs.sqlalchemy.org/en/20/changelog/migration_20.html)
- [Async Support](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

### CCXT v4
- [Documentação Oficial](https://docs.ccxt.com/en/latest/)
- [Exchange Support](https://docs.ccxt.com/en/latest/exchange_support_by_country.html)
- [API Reference](https://docs.ccxt.com/en/latest/manual.html)

## 🎉 Benefícios

1. **Menos Erros**: Sintaxe sempre atualizada
2. **Produtividade**: Documentação rápida e precisa
3. **Qualidade**: Validação automática
4. **Manutenibilidade**: Código compatível com versões mais recentes
5. **Aprendizado**: Entendimento das melhores práticas

## 🔄 Atualizações

Para manter o Context7 atualizado:

```bash
# Atualizar Context7
npm update -g @context7/mcp-server

# Atualizar bibliotecas do projeto
pip install --upgrade -r requirements.txt
pip install --upgrade -r requirements-dev.txt

# Validar após atualizações
python scripts/validate-syntax.py
```
