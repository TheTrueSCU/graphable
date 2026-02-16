from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from graphable.cli.commands.core import render_command

@patch("graphable.cli.commands.core.load_graph")
def test_render_command_explicit_engine(mock_load_graph):
    """Verify render_command calls the correct engine when explicitly provided."""
    mock_g = MagicMock()
    mock_load_graph.return_value = mock_g
    
    input_path = Path("input.json")
    output_path = Path("output.png")
    
    # Mermaid
    with patch("graphable.views.mermaid.export_topology_mermaid_svg") as mock_mermaid:
        render_command(input_path, output_path, engine="mermaid")
        mock_mermaid.assert_called_once_with(mock_g, output_path)
        
    # Graphviz
    with patch("graphable.views.graphviz.export_topology_graphviz_svg") as mock_graphviz:
        render_command(input_path, output_path, engine="graphviz")
        mock_graphviz.assert_called_once_with(mock_g, output_path)
        
    # D2
    with patch("graphable.views.d2.export_topology_d2_svg") as mock_d2:
        render_command(input_path, output_path, engine="d2")
        mock_d2.assert_called_once_with(mock_g, output_path)
        
    # PlantUML
    with patch("graphable.views.plantuml.export_topology_plantuml_svg") as mock_puml:
        render_command(input_path, output_path, engine="plantuml")
        mock_puml.assert_called_once_with(mock_g, output_path)

@patch("graphable.cli.commands.core.load_graph")
@patch("graphable.views.utils.detect_engine")
def test_render_command_auto_detection(mock_detect_engine, mock_load_graph):
    """Verify render_command auto-detects engine when not provided."""
    mock_g = MagicMock()
    mock_load_graph.return_value = mock_g
    mock_detect_engine.return_value = "graphviz"
    
    input_path = Path("input.json")
    output_path = Path("output.png")
    
    with patch("graphable.views.graphviz.export_topology_graphviz_svg") as mock_graphviz:
        render_command(input_path, output_path)
        mock_detect_engine.assert_called_once()
        mock_graphviz.assert_called_once_with(mock_g, output_path)

@patch("graphable.cli.commands.core.load_graph")
def test_render_command_invalid_engine(mock_load_graph):
    """Verify render_command raises ValueError for unknown engine."""
    mock_load_graph.return_value = MagicMock()
    with pytest.raises(ValueError, match="Unknown engine: unknown"):
        render_command(Path("i.json"), Path("o.png"), engine="unknown")
