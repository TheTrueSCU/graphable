from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from graphable.cli.commands.core import (
    check_command,
    checksum_command,
    convert_command,
    diff_command,
    diff_visual_command,
    info_command,
    reduce_command,
    verify_command,
    write_checksum_command,
)
from graphable.cli.commands.serve import serve_command

app = typer.Typer(help="Graphable CLI (Rich)")
console = Console()


@app.command()
def info(
    file: Path = typer.Argument(..., help="Input graph file"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
):
    """Get summary information about a graph."""
    try:
        data = info_command(file, tag=tag)

        title = f"Graph Summary: {file.name}" + (f" (Tag: {tag})" if tag else "")
        table = Table(title=title)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Nodes", str(data["nodes"]))
        table.add_row("Edges", str(data["edges"]))
        table.add_row("Sources", ", ".join(data["sources"]))
        table.add_row("Sinks", ", ".join(data["sinks"]))

        if data.get("project_duration") is not None:
            table.add_row("Project Duration", str(data["project_duration"]))
            table.add_row("Critical Path Length", str(data["critical_path_length"]))

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def check(
    file: Path = typer.Argument(..., help="Input graph file"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
):
    """Validate graph integrity (cycles and consistency)."""
    data = check_command(file, tag=tag)
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
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
):
    """Perform transitive reduction on a graph and save the result."""
    with console.status("[bold green]Reducing graph..."):
        reduce_command(input, output, embed_checksum=embed, tag=tag)
    console.print(f"[green]Successfully reduced graph and saved to {output}[/green]")


@app.command()
def convert(
    input: Path = typer.Argument(..., help="Input graph file"),
    output: Path = typer.Argument(..., help="Output graph file"),
    embed: bool = typer.Option(False, "--embed", help="Embed checksum in output"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
):
    """Convert a graph between supported formats."""
    with console.status(f"[bold green]Converting {input.name} to {output.name}..."):
        convert_command(input, output, embed_checksum=embed, tag=tag)
    console.print(f"[green]Successfully converted {input} to {output}[/green]")


@app.command()
def checksum(
    file: Path = typer.Argument(..., help="Graph file"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
):
    """Calculate and print the graph checksum."""
    try:
        console.print(checksum_command(file, tag=tag))
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def verify(
    file: Path = typer.Argument(..., help="Graph file"),
    expected: str = typer.Option(None, "--expected", help="Expected checksum (hex)"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
):
    """Verify graph checksum (embedded or provided)."""
    try:
        data = verify_command(file, expected, tag=tag)
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
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
):
    """Write graph checksum to a standalone file."""
    try:
        write_checksum_command(file, output, tag=tag)
        console.print(f"[green]Checksum written to {output}[/green]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def diff(
    file1: Path = typer.Argument(..., help="First graph file"),
    file2: Path = typer.Argument(..., help="Second graph file"),
    output: Path = typer.Option(
        None, "--output", "-o", help="Output file for visual diff"
    ),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
):
    """Compare two graphs and highlight differences."""
    try:
        if output:
            diff_visual_command(file1, file2, output, tag=tag)
            console.print(f"[green]Visual diff saved to {output}[/green]")
            return

        data = diff_command(file1, file2, tag=tag)
# ... (rest of diff command)

        if not any(data.values()):
            console.print("[green]Graphs are identical.[/green]")
            return

        table = Table(title=f"Graph Diff: {file1.name} vs {file2.name}")
        table.add_column("Category", style="cyan")
        table.add_column("Changes", style="magenta")

        if data["added_nodes"]:
            table.add_row("Added Nodes", ", ".join(map(str, data["added_nodes"])))
        if data["removed_nodes"]:
            table.add_row("Removed Nodes", ", ".join(map(str, data["removed_nodes"])))
        if data["modified_nodes"]:
            table.add_row("Modified Nodes", ", ".join(map(str, data["modified_nodes"])))

        if data["added_edges"]:
            table.add_row(
                "Added Edges",
                ", ".join(f"{u}->{v}" for u, v in data["added_edges"]),
            )
        if data["removed_edges"]:
            table.add_row(
                "Removed Edges",
                ", ".join(f"{u}->{v}" for u, v in data["removed_edges"]),
            )
        if data["modified_edges"]:
            table.add_row(
                "Modified Edges",
                ", ".join(f"{u}->{v}" for u, v in data["modified_edges"]),
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def serve(
    file: Path = typer.Argument(..., help="Graph file to serve"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to serve on"),
):
    """Start a local web server with live-reloading visualization."""
    try:
        console.print(f"[green]Serving {file} on http://127.0.0.1:{port}[/green]")
        console.print("[yellow]Press Ctrl+C to stop.[/yellow]")
        serve_command(file, port=port)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
