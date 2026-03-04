from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from graphable.cli.rich_cli import app
from graphable.enums import Engine

runner = CliRunner()


@patch("graphable.cli.rich_cli.info_command")
def test_rich_cli_info(mock_info):
    """Verify info command in Rich CLI."""
    mock_info.return_value = {
        "nodes": 2,
        "edges": 1,
        "sources": ["A"],
        "sinks": ["B"],
        "project_duration": 10.0,
        "critical_path_length": 2,
    }
    result = runner.invoke(app, ["info", "test.json"])
    assert result.exit_code == 0
    assert "Nodes" in result.stdout
    assert "Edges" in result.stdout
    assert "Sources" in result.stdout
    assert "Sinks" in result.stdout
    assert "Project Duration" in result.stdout
    assert "Critical Path Length" in result.stdout
    mock_info.assert_called_once_with(
        Path("test.json"), tag=None, upstream_of=None, downstream_of=None
    )


@patch("graphable.cli.rich_cli.info_command")
def test_rich_cli_info_error(mock_info):
    """Verify info command handles error in Rich CLI."""
    mock_info.side_effect = Exception("Test error")
    result = runner.invoke(app, ["info", "test.json"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout
    assert "Test error" in result.stdout


@patch("graphable.cli.rich_cli.check_command")
def test_rich_cli_check_valid(mock_check):
    """Verify check command (valid) in Rich CLI."""
    mock_check.return_value = {"valid": True, "error": None}
    result = runner.invoke(app, ["check", "test.json"])
    assert result.exit_code == 0
    assert "Graph is valid!" in result.stdout


@patch("graphable.cli.rich_cli.check_command")
def test_rich_cli_check_invalid(mock_check):
    """Verify check command (invalid) in Rich CLI."""
    mock_check.return_value = {"valid": False, "error": "Test error"}
    result = runner.invoke(app, ["check", "test.json"])
    assert result.exit_code == 1
    assert "Graph is invalid:" in result.stdout
    assert "Test error" in result.stdout


@patch("graphable.cli.rich_cli.reduce_command")
def test_rich_cli_reduce(mock_reduce):
    """Verify reduce command in Rich CLI."""
    result = runner.invoke(app, ["reduce", "input.json", "output.json"])
    assert result.exit_code == 0
    assert "Successfully reduced graph" in result.stdout
    mock_reduce.assert_called_once_with(
        Path("input.json"),
        Path("output.json"),
        embed_checksum=False,
        tag=None,
        upstream_of=None,
        downstream_of=None,
    )


@patch("graphable.cli.rich_cli.convert_command")
def test_rich_cli_convert(mock_convert):
    """Verify convert command in Rich CLI."""
    result = runner.invoke(app, ["convert", "input.json", "output.yaml"])
    assert result.exit_code == 0
    assert "Successfully converted" in result.stdout
    mock_convert.assert_called_once_with(
        Path("input.json"),
        Path("output.yaml"),
        embed_checksum=False,
        tag=None,
        upstream_of=None,
        downstream_of=None,
    )


@patch("graphable.cli.rich_cli.render_command")
def test_rich_cli_render(mock_render):
    """Verify render command in Rich CLI."""
    result = runner.invoke(app, ["render", "i.json", "o.png", "--engine", "mermaid"])
    assert result.exit_code == 0
    assert "Successfully rendered" in result.stdout
    mock_render.assert_called_once()
    # Check that engine is passed correctly
    args, kwargs = mock_render.call_args
    assert kwargs["engine"] == Engine.MERMAID


@patch("graphable.cli.rich_cli.render_command")
def test_rich_cli_render_error(mock_render):
    """Verify render command error handling in Rich CLI."""
    mock_render.side_effect = Exception("Render error")
    result = runner.invoke(app, ["render", "i.json", "o.png"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout
    assert "Render error" in result.stdout


@patch("graphable.cli.rich_cli.checksum_command")
def test_rich_cli_checksum(mock_checksum):
    """Verify checksum command in Rich CLI."""
    mock_checksum.return_value = "abcdef123456"
    result = runner.invoke(app, ["checksum", "test.json"])
    assert result.exit_code == 0
    assert "abcdef123456" in result.stdout


@patch("graphable.cli.rich_cli.checksum_command")
def test_rich_cli_checksum_error(mock_checksum):
    """Verify checksum command error handling in Rich CLI."""
    mock_checksum.side_effect = Exception("Checksum error")
    result = runner.invoke(app, ["checksum", "test.json"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout
    assert "Checksum error" in result.stdout


@patch("graphable.cli.rich_cli.verify_command")
def test_rich_cli_verify_success(mock_verify):
    """Verify verify command (success) in Rich CLI."""
    mock_verify.return_value = {"valid": True, "actual": "abc", "expected": "abc"}
    result = runner.invoke(app, ["verify", "test.json"])
    assert result.exit_code == 0
    assert "Checksum verified successfully." in result.stdout
    mock_verify.assert_called_once_with(
        Path("test.json"), None, tag=None, upstream_of=None, downstream_of=None
    )


@patch("graphable.cli.rich_cli.verify_command")
def test_rich_cli_verify_mismatch(mock_verify):
    """Verify verify command (mismatch) in Rich CLI."""
    mock_verify.return_value = {"valid": False, "actual": "abc", "expected": "def"}
    result = runner.invoke(app, ["verify", "test.json"])
    assert result.exit_code == 1
    assert "Checksum mismatch!" in result.stdout


@patch("graphable.cli.rich_cli.verify_command")
def test_rich_cli_verify_no_checksum(mock_verify):
    """Verify verify command (no checksum) in Rich CLI."""
    mock_verify.return_value = {"valid": None, "actual": "abc", "expected": None}
    result = runner.invoke(app, ["verify", "test.json"])
    assert result.exit_code == 0
    assert "No checksum found to verify." in result.stdout


@patch("graphable.cli.rich_cli.verify_command")
def test_rich_cli_verify_error(mock_verify):
    """Verify verify command error handling in Rich CLI."""
    mock_verify.side_effect = Exception("Verify error")
    result = runner.invoke(app, ["verify", "test.json"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout
    assert "Verify error" in result.stdout


@patch("graphable.cli.rich_cli.write_checksum_command")
def test_rich_cli_write_checksum(mock_write):
    """Verify write-checksum command in Rich CLI."""
    result = runner.invoke(app, ["write-checksum", "test.json", "test.blake2b"])
    assert result.exit_code == 0
    assert "Checksum written to" in result.stdout
    mock_write.assert_called_once_with(
        Path("test.json"),
        Path("test.blake2b"),
        tag=None,
        upstream_of=None,
        downstream_of=None,
    )


@patch("graphable.cli.rich_cli.write_checksum_command")
def test_rich_cli_write_checksum_error(mock_write):
    """Verify write-checksum command error handling in Rich CLI."""
    mock_write.side_effect = Exception("Write error")
    result = runner.invoke(app, ["write-checksum", "test.json", "test.blake2b"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout
    assert "Write error" in result.stdout


@patch("graphable.cli.rich_cli.diff_command")
def test_rich_cli_diff(mock_diff):
    """Verify diff command in Rich CLI."""
    mock_diff.return_value = {
        "added_nodes": ["C"],
        "removed_nodes": ["A"],
        "modified_nodes": ["B"],
        "added_edges": [("B", "C")],
        "removed_edges": [("A", "B")],
        "modified_edges": [("X", "Y")],
    }
    result = runner.invoke(app, ["diff", "v1.json", "v2.json"])
    assert result.exit_code == 0
    assert "Graph Diff" in result.stdout
    assert "Added Nodes" in result.stdout
    assert "Removed Nodes" in result.stdout
    assert "Modified Nodes" in result.stdout
    assert "Added Edges" in result.stdout
    assert "Removed Edges" in result.stdout
    assert "Modified Edges" in result.stdout


@patch("graphable.cli.rich_cli.diff_visual_command")
def test_rich_cli_diff_visual(mock_diff_visual):
    """Verify diff command with output (visual) in Rich CLI."""
    result = runner.invoke(app, ["diff", "v1.json", "v2.json", "--output", "diff.svg"])
    assert result.exit_code == 0
    assert "Visual diff saved to" in result.stdout
    mock_diff_visual.assert_called_once_with(
        Path("v1.json"), Path("v2.json"), Path("diff.svg"), tag=None
    )


@patch("graphable.cli.rich_cli.diff_command")
def test_rich_cli_diff_identical(mock_diff):
    """Verify diff command (identical) in Rich CLI."""
    mock_diff.return_value = {
        "added_nodes": set(),
        "removed_nodes": set(),
        "modified_nodes": set(),
        "added_edges": set(),
        "removed_edges": set(),
        "modified_edges": set(),
    }
    result = runner.invoke(app, ["diff", "v1.json", "v2.json"])
    assert result.exit_code == 0
    assert "Graphs are identical." in result.stdout


@patch("graphable.cli.rich_cli.diff_command")
def test_rich_cli_diff_error(mock_diff):
    """Verify diff command error handling in Rich CLI."""
    mock_diff.side_effect = Exception("Diff error")
    result = runner.invoke(app, ["diff", "v1.json", "v2.json"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout
    assert "Diff error" in result.stdout


@patch("graphable.cli.rich_cli.serve_command")
def test_rich_cli_serve(mock_serve):
    """Verify serve command in Rich CLI."""
    result = runner.invoke(app, ["serve", "test.json", "--port", "8080"])
    assert result.exit_code == 0
    assert "Serving" in result.stdout
    mock_serve.assert_called_once_with(Path("test.json"), port=8080)


@patch("graphable.cli.rich_cli.serve_command")
def test_rich_cli_serve_error(mock_serve):
    """Verify serve command error handling in Rich CLI."""
    mock_serve.side_effect = Exception("Serve error")
    result = runner.invoke(app, ["serve", "test.json"])
    assert result.exit_code == 1
    assert "Error:" in result.stdout
    assert "Serve error" in result.stdout
