from unittest.mock import patch

from typer.testing import CliRunner

from graphable.cli.rich_cli import app
from graphable.enums import Engine

runner = CliRunner()


@patch("graphable.cli.rich_cli.render_command")
def test_rich_cli_render(mock_render):
    """Verify render command in Rich CLI."""
    result = runner.invoke(app, ["render", "i.json", "o.png", "--engine", "mermaid"])
    assert result.exit_code == 0
    mock_render.assert_called_once()
    # Check that engine is passed correctly
    args, kwargs = mock_render.call_args
    assert kwargs["engine"] == Engine.MERMAID
