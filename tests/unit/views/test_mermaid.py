from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import MagicMock, mock_open, patch

from pytest import fixture, raises

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.mermaid import (
    MermaidStylingConfig,
    _check_mmdc_on_path,
    _cleanup_on_exit,
    _create_mmdc_script,
    _execute_build_script,
    create_topology_mermaid_mmd,
    export_topology_mermaid_mmd,
    export_topology_mermaid_svg,
)


class TestMermaid:
    @fixture
    def graph_fixture(self):
        a = Graphable("A")
        b = Graphable("B")
        g = Graph()
        g.add_edge(a, b)
        return g, a, b

    def test_create_topology_mermaid_mmd_default(self, graph_fixture):
        g, a, b = graph_fixture
        mmd = create_topology_mermaid_mmd(g)

        assert "flowchart TD" in mmd
        assert "A --> B" in mmd

    def test_create_topology_mermaid_mmd_custom_config(self, graph_fixture):
        g, a, b = graph_fixture

        config = MermaidStylingConfig(
            node_text_fnc=lambda n: f"Node:{n.reference}",
            link_text_fnc=lambda n, sn: "--link-->",
            node_style_fnc=lambda n: "fill:#f9f,stroke:#333"
            if n.reference == "A"
            else None,
            link_style_default="stroke-width:2px,fill:none,stroke:red",
        )

        mmd = create_topology_mermaid_mmd(g, config)

        assert "A --link--> B" in mmd
        assert "A[Node:A]" in mmd
        assert "B[Node:B]" in mmd
        assert "style A fill:#f9f,stroke:#333" in mmd
        assert "linkStyle default stroke-width:2px,fill:none,stroke:red" in mmd

    def test_create_topology_mermaid_mmd_link_style(self, graph_fixture):
        g, a, b = graph_fixture
        config = MermaidStylingConfig(link_style_fnc=lambda n, sn: "stroke:blue")
        mmd = create_topology_mermaid_mmd(g, config)
        assert "linkStyle 0 stroke:blue" in mmd

    def test_export_topology_mermaid_mmd(self, graph_fixture):
        g, _, _ = graph_fixture
        output_path = Path("output.mmd")

        with patch("builtins.open", mock_open()) as mock_file:
            export_topology_mermaid_mmd(g, output_path)

            mock_file.assert_called_with(output_path, "w+")
            mock_file().write.assert_called()

    @patch("graphable.views.mermaid.which")
    def test_check_mmdc_on_path_success(self, mock_which):
        mock_which.return_value = "/usr/bin/mmdc"
        _check_mmdc_on_path()  # Should not raise

    @patch("graphable.views.mermaid.which")
    def test_check_mmdc_on_path_failure(self, mock_which):
        mock_which.return_value = None
        with raises(FileNotFoundError):
            _check_mmdc_on_path()

    def test_create_mmdc_script(self):
        content = "test script content"
        script_path = _create_mmdc_script(content)
        try:
            assert script_path.exists()
            assert script_path.read_text() == content
        finally:
            script_path.unlink()

    @patch("graphable.views.mermaid.run")
    def test_execute_build_script_success(self, mock_run):
        mock_run.return_value = MagicMock()
        assert _execute_build_script(Path("dummy.sh")) is True

    @patch("graphable.views.mermaid.run")
    def test_execute_build_script_failure(self, mock_run):
        mock_run.side_effect = CalledProcessError(1, "cmd", stderr="error message")
        assert _execute_build_script(Path("dummy.sh")) is False

    @patch("graphable.views.mermaid.run")
    def test_execute_build_script_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        assert _execute_build_script(Path("dummy.sh")) is False

    @patch("graphable.views.mermaid.Path.unlink")
    def test_cleanup_on_exit_exists(self, mock_unlink):
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = True
        _cleanup_on_exit(mock_path)
        mock_path.unlink.assert_called_once()

    @patch("graphable.views.mermaid.Path.unlink")
    def test_cleanup_on_exit_not_exists(self, mock_unlink):
        mock_path = MagicMock(spec=Path)
        mock_path.exists.return_value = False
        _cleanup_on_exit(mock_path)
        mock_path.unlink.assert_not_called()

    @patch("graphable.views.mermaid.Path.unlink")
    @patch("graphable.views.mermaid._execute_build_script")
    @patch("graphable.views.mermaid._create_mmdc_script")
    @patch("graphable.views.mermaid.NamedTemporaryFile")
    @patch("graphable.views.mermaid._check_mmdc_on_path")
    def test_export_topology_mermaid_svg(
        self,
        mock_check,
        mock_temp,
        mock_create_script,
        mock_exec,
        mock_unlink,
        graph_fixture,
    ):
        g, _, _ = graph_fixture
        output_path = Path("output.svg")

        # Setup mocks
        mock_temp_file = MagicMock()
        mock_temp_file.name = "temp.mmd"
        mock_temp.return_value.__enter__.return_value = mock_temp_file

        mock_script_path = MagicMock(spec=Path)
        mock_create_script.return_value = mock_script_path

        mock_exec.return_value = True

        export_topology_mermaid_svg(g, output_path)

        mock_check.assert_called_once()
        mock_exec.assert_called_with(mock_script_path)
        assert mock_script_path.unlink.call_count == 1

    @patch("graphable.views.mermaid._execute_build_script")
    @patch("graphable.views.mermaid._create_mmdc_script")
    @patch("graphable.views.mermaid.NamedTemporaryFile")
    @patch("graphable.views.mermaid._check_mmdc_on_path")
    def test_export_topology_mermaid_svg_failure(
        self,
        mock_check,
        mock_temp,
        mock_create_script,
        mock_exec,
        graph_fixture,
    ):
        g, _, _ = graph_fixture
        output_path = Path("output.svg")

        # Setup mocks
        mock_temp_file = MagicMock()
        mock_temp_file.name = "temp.mmd"
        mock_temp.return_value.__enter__.return_value = mock_temp_file

        mock_script_path = MagicMock(spec=Path)
        mock_create_script.return_value = mock_script_path

        mock_exec.return_value = False

        export_topology_mermaid_svg(g, output_path)

        mock_exec.assert_called_with(mock_script_path)
        # Should NOT unlink on failure in the current implementation?
        # Wait, let's check the code:
        # if _execute_build_script(build_script):
        #     build_script.unlink()
        #     source.unlink()
        #     logger.info(f"Successfully exported SVG to {output}")
        # else:
        #     logger.error(f"Failed to export SVG to {output}")
        # So it DOES NOT unlink if it fails. That might be a bug or intentional for debugging.
        # But for coverage, it covers line 207.
        assert mock_script_path.unlink.call_count == 0

    def test_create_topology_mermaid_mmd_clustering(self):
        a = Graphable("A")
        a.add_tag("group1")
        b = Graphable("B")
        b.add_tag("group1")
        c = Graphable("C")
        c.add_tag("group2")

        g = Graph()
        g.add_edge(a, b)
        g.add_edge(b, c)

        from graphable.views.mermaid import MermaidStylingConfig

        config = MermaidStylingConfig(cluster_by_tag=True)

        mmd = create_topology_mermaid_mmd(g, config)

        assert "subgraph group1" in mmd
        assert "subgraph group2" in mmd
        assert "A[A]" in mmd
        assert "B[B]" in mmd
        assert "C[C]" in mmd
        # Ensure connections still exist
        assert "A --> B" in mmd
        assert "B --> C" in mmd
