from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from graphable.cli.commands.core import (
    check_command,
    convert_command,
    info_command,
    reduce_command,
)

app = typer.Typer(help="Graphable CLI (Rich)")
console = Console()


@app.command()
def info(file: Path = typer.Argument(..., help="Input graph file")):
    """Get summary information about a graph."""
    try:
        data = info_command(file)

        table = Table(title=f"Graph Summary: {file.name}")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Nodes", str(data["nodes"]))
        table.add_row("Edges", str(data["edges"]))
        table.add_row("Sources", ", ".join(data["sources"]))
        table.add_row("Sinks", ", ".join(data["sinks"]))

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def check(file: Path = typer.Argument(..., help="Input graph file")):
    """Validate graph integrity (cycles and consistency)."""
    data = check_command(file)
    if data["valid"]:
        console.print(
            Panel("[green]Graph is valid![/green]", title="Validation Result")
        )
    else:
        console.print(
            Panel(
                f"[red]Graph is invalid:[/red] {data['error']}",
                title="Validation Result",
            )
        )
        raise typer.Exit(1)


@app.command()
def reduce(
    input: Path = typer.Argument(..., help="Input graph file"),
    output: Path = typer.Argument(..., help="Output graph file"),
):
    """Perform transitive reduction on a graph and save the result."""
    with console.status("[bold green]Reducing graph..."):
        reduce_command(input, output)
    console.print(f"[green]Successfully reduced graph and saved to {output}[/green]")


@app.command()
def convert(
    input: Path = typer.Argument(..., help="Input graph file"),
    output: Path = typer.Argument(..., help="Output graph file"),
):
    """Convert a graph between supported formats."""
    with console.status(f"[bold green]Converting {input.name} to {output.name}..."):
        convert_command(input, output)
    console.print(f"[green]Successfully converted {input} to {output}[/green]")


if __name__ == "__main__":
    app()
