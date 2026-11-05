"""CLI interface for Dynamic Script Runner."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from .config import ConfigManager
from .registry import ScriptRegistry
from .executor import ExecutionEngine
from .history import HistoryManager

app = typer.Typer(
    name="runner",
    help="Dynamic Developer Script Runner – discover, execute and manage external scripts.",
    add_completion=False,
)
console = Console()


def get_engine() -> ExecutionEngine:
    config = ConfigManager()
    registry = ScriptRegistry(config)
    history = HistoryManager(config)
    return ExecutionEngine(config, registry, history)


@app.command("list")
def list_scripts(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category"),
):
    """List all discovered scripts."""
    engine = get_engine()
    scripts = engine.registry.list(category=category)

    if not scripts:
        console.print("[yellow]No scripts discovered. Check script_directories in settings.json[/yellow]")
        return

    table = Table(title="Discovered Scripts", box=box.ROUNDED)
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Category", style="magenta")
    table.add_column("Path", style="dim")
    table.add_column("Description")

    for s in scripts:
        table.add_row(s.name, s.category, s.relative_path, s.description[:60])

    console.print(table)
    console.print(f"\n[dim]Total unique scripts: {len(scripts)}[/dim]")


@app.command("search")
def search_scripts(query: str = typer.Argument(..., help="Search term")):
    """Search scripts by name, category or description."""
    engine = get_engine()
    results = engine.registry.search(query)

    if not results:
        console.print(f"[yellow]No scripts matching '{query}'[/yellow]")
        return

    table = Table(title=f"Search results for '{query}'", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Category")
    table.add_column("Path", style="dim")

    for s in results:
        table.add_row(s.name, s.category, s.relative_path)

    console.print(table)


@app.command("run")
def run_script(
    name: str = typer.Argument(..., help="Script name or alias"),
    args: Optional[List[str]] = typer.Argument(None, help="Arguments to pass to the script"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    timeout: Optional[int] = typer.Option(None, "--timeout", "-t", help="Timeout in seconds"),
):
    """Execute a discovered script."""
    engine = get_engine()
    try:
        result = engine.run(
            name,
            args=args or [],
            confirm=False if yes else None,
            timeout=timeout,
        )
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1)

    # Pretty output
    status_style = "green" if result.success else "red"
    console.print(Panel(
        f"[{status_style}]{result.summary()}[/{status_style}]",
        title="Execution Result",
        border_style=status_style,
    ))

    if result.stdout:
        console.print("\n[bold]STDOUT[/bold]")
        console.print(result.stdout.rstrip())
    if result.stderr:
        console.print("\n[bold red]STDERR[/bold red]")
        console.print(result.stderr.rstrip())
    if result.error_message:
        console.print(f"\n[bold red]Error:[/bold red] {result.error_message}")

    raise typer.Exit(code=0 if result.success else result.exit_code or 1)


@app.command("info")
def script_info(name: str = typer.Argument(..., help="Script name")):
    """Show detailed information about a script."""
    engine = get_engine()
    script = engine.registry.get(name)
    if not script:
        console.print(f"[red]Script '{name}' not found[/red]")
        raise typer.Exit(1)

    console.print(Panel(
        f"[cyan]Name[/cyan]       : {script.name}\n"
        f"[cyan]Category[/cyan]   : {script.category}\n"
        f"[cyan]Path[/cyan]       : {script.path}\n"
        f"[cyan]Relative[/cyan]   : {script.relative_path}\n"
        f"[cyan]Extension[/cyan]  : {script.extension}\n"
        f"[cyan]Description[/cyan]: {script.description or '(none)'}",
        title="Script Info",
        border_style="blue",
    ))


@app.command("history")
def show_history(limit: int = typer.Option(15, "--limit", "-n")):
    """Show recent execution history."""
    engine = get_engine()
    entries = engine.history.list(limit=limit)

    if not entries:
        console.print("[yellow]No execution history yet.[/yellow]")
        return

    table = Table(title="Execution History", box=box.ROUNDED)
    table.add_column("When", style="dim")
    table.add_column("Script", style="cyan")
    table.add_column("Exit")
    table.add_column("Duration")
    table.add_column("Status")

    for e in entries:
        status = "[green]OK[/green]" if e.get("success") else "[red]FAIL[/red]"
        table.add_row(
            e.get("started_at", "")[:19],
            e.get("script_name", ""),
            str(e.get("exit_code", "")),
            f"{e.get('duration_seconds', 0):.2f}s",
            status,
        )

    console.print(table)


@app.command("refresh")
def refresh_registry():
    """Re-scan configured directories and refresh the script registry."""
    engine = get_engine()
    count = engine.registry.refresh()
    console.print(f"[green]Registry refreshed.[/green] {count} script entries registered.")


@app.command("config")
def show_config():
    """Display current configuration."""
    config = ConfigManager()
    console.print_json(data=config.config.model_dump())


# Dynamic command support – allow `runner network-check` style
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    name: Optional[str] = typer.Argument(None, help="Script name to run directly"),
    args: Optional[List[str]] = typer.Argument(None),
):
    """
    Dynamic Script Runner.

    You can either use subcommands (list, run, search, ...)
    or call a script directly:  runner network-check --verbose
    """
    if ctx.invoked_subcommand is not None:
        return

    if name is None:
        console.print(ctx.get_help())
        raise typer.Exit()

    # Treat the first argument as a script name
    engine = get_engine()
    if name not in engine.registry and engine.registry.get(name) is None:
        console.print(f"[red]Unknown command or script: {name}[/red]")
        console.print("Use 'runner list' to see available scripts.")
        raise typer.Exit(1)

    # Re-use the run logic
    try:
        result = engine.run(name, args=args or [], confirm=None)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1)

    status_style = "green" if result.success else "red"
    console.print(Panel(result.summary(), border_style=status_style))
    if result.stdout:
        console.print(result.stdout.rstrip())
    if result.stderr:
        console.print(f"[red]{result.stderr.rstrip()}[/red]")
    raise typer.Exit(code=0 if result.success else 1)


if __name__ == "__main__":
    app()
