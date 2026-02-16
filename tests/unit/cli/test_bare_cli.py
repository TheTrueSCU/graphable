import json
from pathlib import Path
from unittest.mock import patch

from graphable.cli.bare_cli import run_bare


def test_bare_cli_info():
    """Verify info command in Bare CLI."""
    with (
        patch("graphable.cli.bare_cli.info_command") as mock_info,
        patch("sys.argv", ["graphable", "info", "test.json"]),
        patch("sys.exit"),
    ):
        mock_info.return_value = {
            "nodes": 2,
            "edges": 1,
            "sources": ["A"],
            "sinks": ["B"],
            "project_duration": 10.0,
            "critical_path_length": 2,
        }
        run_bare()
        mock_info.assert_called_once_with(Path("test.json"), tag=None)


def test_bare_cli_check_valid():
    """Verify check command (valid) in Bare CLI."""
    with (
        patch("graphable.cli.bare_cli.check_command") as mock_check,
        patch("sys.argv", ["graphable", "check", "test.json"]),
        patch("sys.exit"),
    ):
        mock_check.return_value = {"valid": True, "error": None}
        run_bare()
        mock_check.assert_called_once()


def test_bare_cli_check_invalid():
    """Verify check command (invalid) in Bare CLI."""
    with (
        patch("graphable.cli.bare_cli.check_command") as mock_check,
        patch("sys.argv", ["graphable", "check", "test.json"]),
        patch("graphable.cli.bare_cli.exit") as mock_exit,
    ):
        mock_check.return_value = {"valid": False, "error": "Test error"}
        run_bare()
        mock_exit.assert_called_once_with(1)


def test_bare_cli_reduce():
    """Verify reduce command in Bare CLI."""
    with (
        patch("graphable.cli.bare_cli.reduce_command") as mock_reduce,
        patch("sys.argv", ["graphable", "reduce", "i.json", "o.json"]),
        patch("sys.exit"),
    ):
        run_bare()
        mock_reduce.assert_called_once_with(
            Path("i.json"), Path("o.json"), embed_checksum=False, tag=None
        )


def test_bare_cli_convert():
    """Verify convert command in Bare CLI."""
    with (
        patch("graphable.cli.bare_cli.convert_command") as mock_convert,
        patch("sys.argv", ["graphable", "convert", "i.json", "o.yaml"]),
        patch("sys.exit"),
    ):
        run_bare()
        mock_convert.assert_called_once_with(
            Path("i.json"), Path("o.yaml"), embed_checksum=False, tag=None
        )


def test_bare_cli_render():
    """Verify render command in Bare CLI."""
    with (
        patch("graphable.cli.bare_cli.render_command") as mock_render,
        patch(
            "sys.argv",
            ["graphable", "render", "i.json", "o.png", "--engine", "mermaid"],
        ),
        patch("sys.exit"),
    ):
        run_bare()
        mock_render.assert_called_once_with(
            Path("i.json"), Path("o.png"), engine="mermaid", tag=None
        )


def test_bare_cli_checksum():
    """Verify checksum command in Bare CLI."""
    with (
        patch("graphable.cli.bare_cli.checksum_command") as mock_checksum,
        patch("sys.argv", ["graphable", "checksum", "test.json"]),
        patch("sys.exit"),
    ):
        mock_checksum.return_value = "hash"
        run_bare()
        mock_checksum.assert_called_once()


def test_bare_cli_verify_success():
    """Verify verify command (success) in Bare CLI."""
    with (
        patch("graphable.cli.bare_cli.verify_command") as mock_verify,
        patch("sys.argv", ["graphable", "verify", "test.json"]),
        patch("sys.exit"),
    ):
        mock_verify.return_value = {"valid": True, "actual": "abc", "expected": "abc"}
        run_bare()
        mock_verify.assert_called_once()


def test_bare_cli_verify_mismatch():
    """Verify verify command (mismatch) in Bare CLI."""
    with (
        patch("graphable.cli.bare_cli.verify_command") as mock_verify,
        patch("sys.argv", ["graphable", "verify", "test.json"]),
        patch("graphable.cli.bare_cli.exit") as mock_exit,
    ):
        mock_verify.return_value = {"valid": False, "actual": "abc", "expected": "def"}
        run_bare()
        mock_exit.assert_called_once_with(1)


def test_bare_cli_verify_no_checksum():
    """Verify verify command (no checksum) in Bare CLI."""
    with (
        patch("graphable.cli.bare_cli.verify_command") as mock_verify,
        patch("sys.argv", ["graphable", "verify", "test.json"]),
        patch("sys.exit"),
    ):
        mock_verify.return_value = {"valid": None, "actual": "abc", "expected": None}
        run_bare()
        mock_verify.assert_called_once()


def test_bare_cli_write_checksum():
    """Verify write-checksum command in Bare CLI."""
    with (
        patch("graphable.cli.bare_cli.write_checksum_command") as mock_write,
        patch("sys.argv", ["graphable", "write-checksum", "test.json", "test.blake2b"]),
        patch("sys.exit"),
    ):
        run_bare()
        mock_write.assert_called_once()


def test_bare_cli_diff_default():
    """Verify diff command (JSON output) in Bare CLI."""
    with (
        patch("graphable.cli.bare_cli.diff_command") as mock_diff,
        patch("sys.argv", ["graphable", "diff", "v1.json", "v2.json"]),
        patch("sys.exit"),
        patch("builtins.print") as mock_print,
    ):
        mock_diff.return_value = {
            "added_nodes": ["C"],
            "removed_nodes": [],
            "modified_nodes": [],
            "added_edges": [("A", "B")],
            "removed_edges": [],
            "modified_edges": [],
        }
        run_bare()
        # Verify JSON was printed
        printed_call = mock_print.call_args_list[-1][0][0]
        data = json.loads(printed_call)
        assert "added_nodes" in data
        assert "added_edges" in data


def test_bare_cli_diff_visual():
    """Verify diff command (visual) in Bare CLI."""
    with (
        patch("graphable.cli.bare_cli.diff_visual_command") as mock_diff_visual,
        patch("sys.argv", ["graphable", "diff", "v1.json", "v2.json", "-o", "d.svg"]),
        patch("sys.exit"),
    ):
        run_bare()
        mock_diff_visual.assert_called_once()


def test_bare_cli_serve():
    """Verify serve command in Bare CLI."""
    with (
        patch("graphable.cli.commands.serve.serve_command") as mock_serve,
        patch("sys.argv", ["graphable", "serve", "test.json"]),
        patch("sys.exit"),
    ):
        run_bare()
        mock_serve.assert_called_once()


def test_bare_cli_no_command():
    """Verify help is shown when no command is provided in Bare CLI."""
    with (
        patch("argparse.ArgumentParser.print_help") as mock_help,
        patch("sys.argv", ["graphable"]),
        patch("sys.exit"),
    ):
        run_bare()
        assert mock_help.called
