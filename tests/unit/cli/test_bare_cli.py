from pathlib import Path
from unittest.mock import MagicMock, patch
from graphable.cli.bare_cli import run_bare

@patch("graphable.cli.bare_cli.render_command")
@patch("sys.argv", ["graphable", "render", "input.json", "output.png", "--engine", "mermaid"])
def test_bare_cli_render(mock_render):
    """Verify render command in Bare CLI."""
    # We need to mock sys.exit because run_bare might call it via ArgumentParser or logic
    with patch("sys.exit"):
        run_bare()
        
    mock_render.assert_called_once()
    args, kwargs = mock_render.call_args
    assert args[0] == Path("input.json")
    assert args[1] == Path("output.png")
    assert kwargs["engine"] == "mermaid"
