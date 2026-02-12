from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from graphable.cli.commands.core import (
    check_command,
    checksum_command,
    convert_command,
    info_command,
    reduce_command,
    verify_command,
    write_checksum_command,
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
    embed: bool = typer.Option(False, "--embed", help="Embed checksum in output"),
):
    """Perform transitive reduction on a graph and save the result."""
    with console.status("[bold green]Reducing graph..."):
        reduce_command(input, output, embed_checksum=embed)
    console.print(f"[green]Successfully reduced graph and saved to {output}[/green]")


@app.command()
def convert(
    input: Path = typer.Argument(..., help="Input graph file"),
    output: Path = typer.Argument(..., help="Output graph file"),
    embed: bool = typer.Option(False, "--embed", help="Embed checksum in output"),
):
    """Convert a graph between supported formats."""
    with console.status(f"[bold green]Converting {input.name} to {output.name}..."):
        convert_command(input, output, embed_checksum=embed)
    console.print(f"[green]Successfully converted {input} to {output}[/green]")


@app.command()
def checksum(file: Path = typer.Argument(..., help="Graph file")):
    """Calculate and print the graph checksum."""
    try:
        console.print(checksum_command(file))
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def verify(
    file: Path = typer.Argument(..., help="Graph file"),
    expected: str = typer.Option(None, "--expected", help="Expected checksum (hex)"),
):
    """Verify graph checksum (embedded or provided)."""
    try:
        data = verify_command(file, expected)
        if data["valid"] is True:
            console.print("[green]Checksum verified successfully.[/green]")
        elif data["valid"] is False:
            console.print(
                f"[red]Checksum mismatch![/red] Expected {data['expected']}, got {data['actual']}"
            )
            raise typer.Exit(1)
        else:
            console.print(
                f"[yellow]No checksum found to verify.[/yellow] Current hash: {data['actual']}"
            )
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def write_checksum(
    file: Path = typer.Argument(..., help="Graph file"),
    output: Path = typer.Argument(..., help="Output checksum file"),
):
    """Write graph checksum to a standalone file."""
    try:
        write_checksum_command(file, output)
        console.print(f"[green]Checksum written to {output}[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
