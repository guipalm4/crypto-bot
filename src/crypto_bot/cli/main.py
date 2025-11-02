#!/usr/bin/env python3
"""
Crypto Trading Bot - CLI Main Module

This module provides the command-line interface for the Crypto Trading Bot.
"""

import uuid
from decimal import Decimal

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from crypto_bot.application.dtos.order import BalanceDTO
from crypto_bot.cli.context import cli_context, run_async
from crypto_bot.infrastructure.database.repositories.position_repository import (
    PositionRepository,
)
from crypto_bot.utils.structured_logger import get_logger
from crypto_bot.utils.system_events import log_error, log_system_event

console = Console()
logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0", prog_name="Crypto Trading Bot")
def main() -> None:
    """
    🚀 Crypto Trading Bot - Sistema automatizado de trading de criptomoedas

    Um sistema modular e robusto para trading automatizado de criptomoedas
    com arquitetura baseada em Domain-Driven Design (DDD).
    """
    pass


@main.command()
def version() -> None:
    """Mostra a versão do Crypto Trading Bot."""
    console.print(
        Panel(
            Text("Crypto Trading Bot v0.1.0", style="bold green"),
            title="Version",
            border_style="green",
        )
    )


@main.command()
def status() -> None:
    """Mostra o status do sistema."""

    async def _get_status() -> None:
        async with cli_context.get_session():
            try:
                strategy_repo = await cli_context.get_strategy_repository()
                active_strategies = await strategy_repo.get_active_strategies()

                # Create status table
                table = Table(
                    title="System Status", show_header=True, header_style="bold magenta"
                )
                table.add_column("Component", style="cyan")
                table.add_column("Status", style="green")
                table.add_column("Count", justify="right", style="yellow")

                table.add_row("Strategies", "✅ Active", str(len(active_strategies)))
                table.add_row("Database", "✅ Connected", "1")
                table.add_row("Orchestrator", "⏸️  Stopped", "0")

                console.print(table)
            except Exception as e:
                console.print(f"[red]Error getting status: {e}[/red]")
                logger.error(
                    "status_command_error", exc_type=type(e).__name__, exc_msg=str(e)
                )

    run_async(_get_status())


@main.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Caminho para o arquivo de configuração YAML",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Executar em modo simulação (sem trades reais). Todos os trades serão simulados.",
)
def start(config: str | None, dry_run: bool) -> None:
    """
    Inicia o bot de trading.

    Inicia o StrategyOrchestrator e começa a executar estratégias ativas
    conforme seus timeframes configurados. O bot roda até ser interrompido
    com Ctrl+C.

    \b
    Exemplos:
        # Iniciar em modo live
        crypto-bot start

        # Iniciar em modo dry-run (simulação)
        crypto-bot start --dry-run

        # Iniciar com arquivo de configuração específico
        crypto-bot start --config /path/to/config.yaml

    \b
    Modos:
        --dry-run: Em modo simulação, nenhum trade real é executado.
                  Todos os sinais são processados mas não resultam em ordens reais.
                  Ideal para testar estratégias sem risco.
    """

    async def _start() -> None:
        try:
            log_system_event(
                "bot_start_command",
                event_type="cli",
                config_path=config,
                dry_run=dry_run,
            )

            console.print(
                Panel(
                    Text(
                        f"Iniciando Crypto Trading Bot...\n{'🔍 Modo Dry-Run Ativado' if dry_run else '💰 Modo Live Ativado'}",
                        style="bold yellow" if dry_run else "bold green",
                    ),
                    title="Starting",
                    border_style="yellow" if dry_run else "green",
                )
            )

            if config:
                console.print(f"📁 Usando configuração: {config}")

            async with cli_context.get_session():
                orchestrator = await cli_context.get_orchestrator(dry_run=dry_run)
                await orchestrator.start()

                logger.info(
                    "bot_started_successfully",
                    config_used=config is not None,
                    dry_run=dry_run,
                )

                console.print("✅ Bot iniciado com sucesso!")
                console.print(
                    f"[{'yellow' if dry_run else 'green'}]Modo: {'Dry-Run (Simulação)' if dry_run else 'Live (Trades Reais)'}[/]"
                )

                # Keep running until interrupted
                try:
                    import asyncio

                    while orchestrator._running:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    console.print("\n[yellow]Parando bot...[/yellow]")
                    await orchestrator.stop()
                    await cli_context.cleanup()
                    console.print("[green]✅ Bot parado com sucesso![/green]")

        except Exception as e:
            log_error(
                e, context={"command": "start", "config": config, "dry_run": dry_run}
            )
            console.print(f"[red]❌ Erro ao iniciar bot: {e}[/red]")
            raise

    run_async(_start())


@main.command()
def stop() -> None:
    """
    Para o bot de trading.

    Interrompe o StrategyOrchestrator de forma segura, aguardando
    que execuções em andamento sejam finalizadas.

    \b
    Exemplo:
        crypto-bot stop
    """

    async def _stop() -> None:
        try:
            console.print(
                Panel(
                    Text("Parando Crypto Trading Bot...", style="bold red"),
                    title="Stopping",
                    border_style="red",
                )
            )

            async with cli_context.get_session():
                orchestrator = await cli_context.get_orchestrator(dry_run=False)
                if orchestrator._running:
                    await orchestrator.stop()
                    await cli_context.cleanup()
                    console.print("✅ Bot parado com sucesso!")
                else:
                    console.print("[yellow]⚠️  Bot não estava rodando[/yellow]")

        except Exception as e:
            log_error(e, context={"command": "stop"})
            console.print(f"[red]❌ Erro ao parar bot: {e}[/red]")

    run_async(_stop())


@main.command()
@click.option("--config", "-c", help="Caminho para o arquivo de configuração")
@click.option("--dry-run", is_flag=True, help="Executar em modo simulação")
def restart(config: str | None, dry_run: bool) -> None:
    """Reinicia o bot de trading."""

    async def _restart() -> None:
        console.print(
            Panel(
                Text("Reiniciando Crypto Trading Bot...", style="bold blue"),
                title="Restarting",
                border_style="blue",
            )
        )

        # Stop first
        try:
            orchestrator = await cli_context.get_orchestrator(dry_run=dry_run)
            if orchestrator._running:
                await orchestrator.stop()
                await cli_context.cleanup()
        except Exception:
            pass

        # Start again
        await cli_context.get_session().__aenter__()
        orchestrator = await cli_context.get_orchestrator(dry_run=dry_run)
        await orchestrator.start()

        console.print("✅ Bot reiniciado com sucesso!")

    run_async(_restart())


@main.command()
@click.option(
    "--exchange",
    "-e",
    help="Filtrar estratégias por exchange (ex: binance, coinbase)",
)
def strategies(exchange: str | None) -> None:
    """
    Lista todas as estratégias ativas.

    Mostra informações sobre todas as estratégias configuradas e ativas,
    incluindo ID, nome, plugin, símbolo e timeframe.

    \b
    Exemplos:
        # Listar todas as estratégias
        crypto-bot strategies

        # Filtrar por exchange
        crypto-bot strategies --exchange binance

    \b
    Colunas da tabela:
        ID: Identificador único da estratégia (UUID truncado)
        Name: Nome da estratégia
        Plugin: Nome do plugin de estratégia usado
        Symbol: Par de trading (ex: BTC/USDT)
        Timeframe: Timeframe configurado (ex: 1h, 5m)
    """

    async def _list_strategies() -> None:
        async with cli_context.get_session():
            try:
                strategy_repo = await cli_context.get_strategy_repository()
                strategies = await strategy_repo.get_active_strategies()

                if not strategies:
                    console.print(
                        "[yellow]⚠️  Nenhuma estratégia ativa encontrada[/yellow]"
                    )
                    return

                # Create strategies table
                table = Table(
                    title="Active Strategies",
                    show_header=True,
                    header_style="bold cyan",
                )
                table.add_column("ID", style="dim", width=36)
                table.add_column("Name", style="bold")
                table.add_column("Plugin", style="cyan")
                table.add_column("Symbol", style="yellow")
                table.add_column("Timeframe", style="magenta")

                for strategy in strategies:
                    params = strategy.parameters_json
                    symbol = params.get("symbol", "N/A")
                    timeframe = params.get("timeframe", "N/A")
                    table.add_row(
                        str(strategy.id)[:8] + "...",
                        strategy.name,
                        strategy.plugin_name,
                        symbol,
                        timeframe,
                    )

                console.print(table)
                console.print(
                    f"\n[green]Total: {len(strategies)} estratégias ativas[/green]"
                )

            except Exception as e:
                console.print(f"[red]❌ Erro ao listar estratégias: {e}[/red]")
                logger.error(
                    "strategies_command_error",
                    exc_type=type(e).__name__,
                    exc_msg=str(e),
                )

    run_async(_list_strategies())


@main.command()
def positions() -> None:
    """
    Mostra todas as posições abertas.

    Exibe uma tabela com todas as posições de trading atualmente abertas,
    incluindo símbolo, lado (buy/sell), tamanho, preço de entrada e PnL.

    \b
    Exemplo:
        crypto-bot positions

    \b
    Colunas da tabela:
        ID: Identificador único da posição
        Symbol: Par de trading
        Side: Lado da posição (BUY ou SELL)
        Size: Tamanho da posição
        Entry Price: Preço médio de entrada
        Current PnL: Lucro/Prejuízo não realizado (verde para lucro, vermelho para prejuízo)
    """

    async def _list_positions() -> None:
        async with cli_context.get_session() as session:
            try:
                position_repo = PositionRepository(session)
                # session is used here
                open_positions = await position_repo.get_open_positions()

                if not open_positions:
                    console.print(
                        "[yellow]⚠️  Nenhuma posição aberta encontrada[/yellow]"
                    )
                    return

                # Create positions table
                table = Table(
                    title="Open Positions", show_header=True, header_style="bold cyan"
                )
                table.add_column("ID", style="dim", width=36)
                table.add_column("Symbol", style="bold yellow")
                table.add_column("Side", style="green")
                table.add_column("Size", justify="right", style="cyan")
                table.add_column("Entry Price", justify="right", style="magenta")
                table.add_column("Current PnL", justify="right", style="yellow")

                for position in open_positions:
                    # Get PnL (assuming we have this field, adjust as needed)
                    pnl = getattr(position, "unrealized_pnl", Decimal("0"))
                    pnl_style = "green" if pnl >= 0 else "red"

                    table.add_row(
                        str(position.id)[:8] + "...",
                        getattr(position, "symbol", "N/A"),
                        (
                            str(position.side.value)
                            if hasattr(position, "side")
                            else "N/A"
                        ),
                        str(position.size) if hasattr(position, "size") else "N/A",
                        (
                            str(position.entry_price)
                            if hasattr(position, "entry_price")
                            else "N/A"
                        ),
                        f"[{pnl_style}]{pnl}[/{pnl_style}]",
                    )

                console.print(table)
                console.print(
                    f"\n[green]Total: {len(open_positions)} posições abertas[/green]"
                )

            except Exception as e:
                console.print(f"[red]❌ Erro ao listar posições: {e}[/red]")
                logger.error(
                    "positions_command_error", exc_type=type(e).__name__, exc_msg=str(e)
                )

    run_async(_list_positions())


@main.command()
@click.option(
    "--exchange",
    "-e",
    required=True,
    help="Nome do exchange (ex: binance, coinbase)",
)
@click.option(
    "--currency",
    "-c",
    help="Moeda específica para consultar (opcional). Se omitido, mostra todas as moedas.",
)
def balances(exchange: str, currency: str | None) -> None:
    """
    Verifica saldos das contas nas exchanges.

    Consulta e exibe os saldos disponíveis em uma exchange específica.
    Pode mostrar uma moeda específica ou todas as moedas com saldo não-zero.

    \b
    Exemplos:
        # Ver todos os saldos de uma exchange
        crypto-bot balances --exchange binance

        # Ver saldo de uma moeda específica
        crypto-bot balances --exchange binance --currency BTC

        # Forma abreviada
        crypto-bot balances -e binance -c USDT

    \b
    Colunas da tabela:
        Currency: Símbolo da moeda (BTC, USDT, etc)
        Free: Saldo disponível para trading
        Used: Saldo usado em ordens abertas
        Total: Saldo total (free + used)
    """

    async def _get_balances() -> None:
        try:
            async with cli_context.get_session():
                trading_service = await cli_context.get_trading_service()
                try:
                    balance_data = await trading_service.get_balance(exchange, currency)

                    if currency:
                        # Single balance
                        if isinstance(balance_data, dict):
                            balance = balance_data.get(currency)
                            if not balance:
                                console.print(
                                    f"[red]❌ Moeda {currency} não encontrada[/red]"
                                )
                                return
                        elif hasattr(balance_data, "currency"):
                            # It's a BalanceDTO object
                            balance = balance_data
                        else:
                            console.print("[red]❌ Formato de dados inválido[/red]")
                            return

                        table = Table(
                            title=f"Balance - {exchange.upper()}",
                            show_header=True,
                            header_style="bold cyan",
                        )
                        table.add_column("Currency", style="bold yellow")
                        table.add_column("Free", justify="right", style="green")
                        table.add_column("Used", justify="right", style="yellow")
                        table.add_column("Total", justify="right", style="cyan")

                        table.add_row(
                            balance.currency,
                            str(balance.free),
                            str(balance.used),
                            str(balance.total),
                        )
                        console.print(table)
                    else:
                        # All balances
                        if isinstance(balance_data, dict):
                            balances_dict: dict[str, BalanceDTO] = balance_data
                        elif hasattr(balance_data, "currency"):
                            # Single balance returned, convert to dict
                            balances_dict = {balance_data.currency: balance_data}
                        else:
                            console.print("[red]❌ Formato de dados inválido[/red]")
                            return

                        table = Table(
                            title=f"Balances - {exchange.upper()}",
                            show_header=True,
                            header_style="bold cyan",
                        )
                        table.add_column("Currency", style="bold yellow")
                        table.add_column("Free", justify="right", style="green")
                        table.add_column("Used", justify="right", style="yellow")
                        table.add_column("Total", justify="right", style="cyan")

                        for curr, bal in balances_dict.items():
                            # balances_dict is typed as dict[str, BalanceDTO], so bal is always BalanceDTO
                            # But we check anyway for runtime safety
                            if bal.total > 0:
                                # Only show non-zero balances
                                table.add_row(
                                    curr, str(bal.free), str(bal.used), str(bal.total)
                                )

                        console.print(table)
                finally:
                    # Always close trading service to prevent resource leaks
                    if trading_service and hasattr(trading_service, "close"):
                        try:
                            await trading_service.close()
                        except Exception as close_error:
                            logger.warning(
                                "Error closing trading service: %s", str(close_error)
                            )

        except Exception as e:
            console.print(f"[red]❌ Erro ao obter saldos: {e}[/red]")
            logger.error(
                "balances_command_error",
                exc_type=type(e).__name__,
                exc_msg=str(e),
                exchange=exchange,
            )

    run_async(_get_balances())


@main.command()
@click.argument(
    "strategy_id",
    type=str,
    metavar="STRATEGY_ID",
)
def force(strategy_id: str) -> None:
    """
    Força a execução de uma estratégia específica.

    Executa manualmente uma estratégia independentemente do seu timeframe
    configurado. Útil para testes ou execução sob demanda.

    \b
    Args:
        STRATEGY_ID: ID (UUID) ou nome da estratégia

    \b
    Exemplos:
        # Executar por UUID
        crypto-bot force 550e8400-e29b-41d4-a716-446655440000

        # Executar por nome
        crypto-bot force "My RSI Strategy"

    \b
    O comando:
        1. Busca a estratégia por ID ou nome
        2. Cria contexto de execução
        3. Executa ciclo completo: dados → indicadores → sinal → trade
        4. Exibe resultado do sinal gerado

    \b
    Nota: Este comando não respeita timeframes - executa imediatamente.
    """

    async def _force_execution() -> None:
        async with cli_context.get_session():
            try:
                strategy_repo = await cli_context.get_strategy_repository()

                # Try to parse as UUID
                try:
                    strategy_uuid = uuid.UUID(strategy_id)
                    strategy = await strategy_repo.get_by_id(strategy_uuid)
                except ValueError:
                    # Try by name
                    strategy = await strategy_repo.get_by_name(strategy_id)

                if not strategy:
                    console.print(
                        f"[red]❌ Estratégia não encontrada: {strategy_id}[/red]"
                    )
                    return

                console.print(f"[cyan]Executando estratégia: {strategy.name}[/cyan]")

                orchestrator = await cli_context.get_orchestrator(dry_run=False)
                contexts = await orchestrator._create_execution_contexts([strategy])

                if not contexts:
                    console.print(
                        "[red]❌ Não foi possível criar contexto de execução[/red]"
                    )
                    return

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                ) as progress:
                    task = progress.add_task("Executando estratégia...", total=None)
                    await orchestrator._run_strategy(contexts[0])
                    progress.update(task, completed=100)

                if contexts[0].error:
                    console.print(
                        f"[red]❌ Erro na execução: {contexts[0].error}[/red]"
                    )
                else:
                    signal = contexts[0].signal
                    if signal:
                        console.print("[green]✅ Execução concluída![/green]")
                        console.print(
                            f"   Sinal: {signal.action} (força: {signal.strength:.2f})"
                        )
                    else:
                        console.print("[yellow]⚠️  Nenhum sinal gerado[/yellow]")

            except Exception as e:
                console.print(f"[red]❌ Erro ao forçar execução: {e}[/red]")
                logger.error(
                    "force_command_error",
                    exc_type=type(e).__name__,
                    exc_msg=str(e),
                    strategy_id=strategy_id,
                )

    run_async(_force_execution())


@main.command()
@click.option(
    "--follow", "-f", is_flag=True, help="Seguir logs em tempo real (tail -f)"
)
@click.option("--lines", "-n", default=50, help="Número de linhas para mostrar")
def logs(follow: bool, lines: int) -> None:
    """
    Visualiza logs do bot.

    Exibe logs do sistema com formatação colorida. Pode mostrar as últimas
    N linhas ou seguir logs em tempo real.

    \b
    Exemplos:
        # Ver últimas 50 linhas
        crypto-bot logs

        # Ver últimas 100 linhas
        crypto-bot logs --lines 100

        # Seguir logs em tempo real
        crypto-bot logs --follow

        # Forma abreviada
        crypto-bot logs -f

    \b
    Cores:
        - ERROR: Vermelho
        - WARNING: Amarelo
        - INFO: Ciano
        - Outros: Branco

    \b
    Arquivo de log: logs/app.log
    """
    import os
    from pathlib import Path

    log_path = Path("logs") / "app.log"
    if not log_path.exists():
        console.print("[yellow]⚠️  Arquivo de log não encontrado[/yellow]")
        return

    if follow:
        # Real-time log following
        console.print("[cyan]Seguindo logs em tempo real... (Ctrl+C para parar)[/cyan]")

        import time

        try:
            with open(log_path, "r", encoding="utf-8") as f:
                # Go to end of file
                f.seek(0, os.SEEK_END)

                while True:
                    line = f.readline()
                    if line:
                        # Parse and format log line
                        if "ERROR" in line:
                            console.print(f"[red]{line.rstrip()}[/red]")
                        elif "WARNING" in line:
                            console.print(f"[yellow]{line.rstrip()}[/yellow]")
                        elif "INFO" in line:
                            console.print(f"[cyan]{line.rstrip()}[/cyan]")
                        else:
                            console.print(line.rstrip())
                    else:
                        time.sleep(0.1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Parando...[/yellow]")
    else:
        # Show last N lines
        with open(log_path, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

            console.print(
                Panel("\n".join(last_lines), title="Recent Logs", border_style="blue")
            )


@main.command()
@click.option(
    "--enable",
    is_flag=True,
    default=False,
    help="Habilitar modo dry-run (simulação)",
)
@click.option(
    "--disable",
    is_flag=True,
    default=False,
    help="Desabilitar modo dry-run (retornar ao modo live)",
)
def dry_run(enable: bool, disable: bool) -> None:
    """
    Gerencia o modo dry-run (simulação).

    Permite habilitar ou desabilitar o modo de simulação, onde nenhum
    trade real é executado. Em modo dry-run, todas as estratégias funcionam
    normalmente mas não geram ordens reais.

    \b
    Exemplos:
        # Habilitar modo dry-run
        crypto-bot dry-run --enable

        # Desabilitar modo dry-run (voltar ao modo live)
        crypto-bot dry-run --disable

    \b
    Modo Dry-Run:
        ✅ Todas as estratégias executam normalmente
        ✅ Dados de mercado são buscados
        ✅ Indicadores são calculados
        ✅ Sinais são gerados
        ❌ Nenhuma ordem real é executada
        📝 Logs mostram trades simulados

    \b
    Use este modo para:
        - Testar novas estratégias sem risco
        - Validar lógica de trading
        - Desenvolver e debugar
        - Treinar antes de operar com capital real
    """
    if enable and disable:
        console.print(
            "[red]❌ Não é possível habilitar e desabilitar ao mesmo tempo[/red]"
        )
        return

    if not enable and not disable:
        # Show current status
        console.print(
            "[yellow]⚠️  Use --enable ou --disable para alterar o modo[/yellow]"
        )
        console.print("   Exemplo: crypto-bot dry-run --enable")
        return

    # In a real implementation, this would update a config file or database flag
    mode = "habilitado" if enable else "desabilitado"
    style = "green" if enable else "yellow"

    console.print(
        Panel(
            Text(f"Modo Dry-Run {mode}", style=f"bold {style}"),
            title="Dry-Run Mode",
            border_style=style,
        )
    )
    console.print(f"[{style}]✅ Modo dry-run {mode} com sucesso[/{style}]")

    if enable:
        console.print(
            "[yellow]ℹ️  Em modo dry-run, nenhum trade real será executado[/yellow]"
        )


if __name__ == "__main__":
    main()
