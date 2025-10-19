#!/usr/bin/env python3
"""
Crypto Trading Bot - CLI Main Module

This module provides the command-line interface for the Crypto Trading Bot.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

@click.group()
@click.version_option(version="0.1.0", prog_name="Crypto Trading Bot")
def main():
    """
    🚀 Crypto Trading Bot - Sistema automatizado de trading de criptomoedas
    
    Um sistema modular e robusto para trading automatizado de criptomoedas
    com arquitetura baseada em Domain-Driven Design (DDD).
    """
    pass

@main.command()
def version():
    """Mostra a versão do Crypto Trading Bot."""
    console.print(Panel(
        Text("Crypto Trading Bot v0.1.0", style="bold green"),
        title="Version",
        border_style="green"
    ))

@main.command()
def status():
    """Mostra o status do sistema."""
    console.print(Panel(
        Text("Sistema inicializado com sucesso! 🎉", style="bold green"),
        title="Status",
        border_style="green"
    ))

@main.command()
@click.option("--config", "-c", help="Caminho para o arquivo de configuração")
def start(config):
    """Inicia o bot de trading."""
    console.print(Panel(
        Text("Iniciando Crypto Trading Bot...", style="bold yellow"),
        title="Starting",
        border_style="yellow"
    ))
    
    if config:
        console.print(f"📁 Usando configuração: {config}")
    
    # TODO: Implementar lógica de inicialização do bot
    console.print("✅ Bot iniciado com sucesso!")

@main.command()
def stop():
    """Para o bot de trading."""
    console.print(Panel(
        Text("Parando Crypto Trading Bot...", style="bold red"),
        title="Stopping",
        border_style="red"
    ))
    
    # TODO: Implementar lógica de parada do bot
    console.print("✅ Bot parado com sucesso!")

@main.command()
def restart():
    """Reinicia o bot de trading."""
    console.print(Panel(
        Text("Reiniciando Crypto Trading Bot...", style="bold blue"),
        title="Restarting",
        border_style="blue"
    ))
    
    # TODO: Implementar lógica de reinicialização do bot
    console.print("✅ Bot reiniciado com sucesso!")

if __name__ == "__main__":
    main()
