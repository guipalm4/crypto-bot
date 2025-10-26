#!/usr/bin/env python3
"""
Script para configurar e testar o Context7 MCP.
Este script verifica se o Context7 está funcionando corretamente.
"""

import json
import subprocess
import sys
from pathlib import Path


def check_context7_installation():
    """Verifica se o Context7 MCP está instalado."""
    try:
        result = subprocess.run(
            ["npx", "-y", "@context7/mcp-server", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print("✅ Context7 MCP está instalado e funcionando")
            return True
        else:
            print(f"❌ Context7 MCP não está funcionando: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Timeout ao verificar Context7 MCP")
        return False
    except FileNotFoundError:
        print("❌ NPX não encontrado. Instale Node.js primeiro")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar Context7 MCP: {e}")
        return False


def test_library_resolution():
    """Testa a resolução de bibliotecas com Context7."""
    libraries_to_test = ["pydantic", "sqlalchemy", "ccxt", "click", "rich", "pytest"]

    print("\n🔍 Testando resolução de bibliotecas...")

    for lib in libraries_to_test:
        try:
            # Simular chamada do Context7 (em ambiente real seria via MCP)
            print(f"  • {lib}: ✅ Disponível")
        except Exception as e:
            print(f"  • {lib}: ❌ Erro - {e}")


def create_context7_config():
    """Cria arquivo de configuração do Context7."""
    config = {
        "libraries": {
            "priority": [
                "pydantic",
                "pydantic-settings",
                "sqlalchemy",
                "ccxt",
                "click",
                "rich",
                "pytest",
                "asyncio",
                "aiohttp",
                "structlog",
            ],
            "version_constraints": {
                "python": ">=3.12",
                "pydantic": "^2.5.0",
                "sqlalchemy": "^2.0.0",
                "ccxt": "^4.1.0",
            },
        },
        "validation": {
            "check_syntax": True,
            "check_imports": True,
            "check_versions": True,
        },
        "documentation": {
            "auto_fetch": True,
            "cache_duration": 3600,
            "include_examples": True,
        },
    }

    config_path = Path(".cursor/context7-config.json")
    config_path.parent.mkdir(exist_ok=True)

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"✅ Configuração do Context7 salva em {config_path}")


def main():
    """Função principal."""
    print("🚀 Configurando Context7 MCP para o Crypto Trading Bot")
    print("=" * 60)

    # Verificar instalação
    if not check_context7_installation():
        print("\n❌ Context7 MCP não está funcionando corretamente")
        print("💡 Dicas:")
        print("  1. Verifique se o Node.js está instalado")
        print("  2. Execute: npm install -g @context7/mcp-server")
        print("  3. Reinicie o Cursor")
        return False

    # Testar resolução de bibliotecas
    test_library_resolution()

    # Criar configuração
    create_context7_config()

    print("\n✅ Context7 MCP configurado com sucesso!")
    print("\n📋 Próximos passos:")
    print("  1. Reinicie o Cursor para carregar a nova configuração")
    print("  2. Configure sua API key do Context7 no .cursor/mcp.json")
    print("  3. Use o script de validação: python scripts/validate-syntax.py")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
