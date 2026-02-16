from unittest.mock import patch

import pytest

from graphable.enums import Engine
from graphable.views.utils import detect_engine, get_image_exporter


@patch("graphable.views.utils.which")
def test_detect_engine_priority(mock_which):
    """Verify priority: mermaid -> graphviz -> d2 -> plantuml."""
    # Mermaid available
    mock_which.side_effect = lambda x: "/path/to/" + x if x == "mmdc" else None
    assert detect_engine() == "mermaid"

    # Only Graphviz available
    mock_which.side_effect = lambda x: "/path/to/" + x if x == "dot" else None
    assert detect_engine() == "graphviz"

    # Only D2 available
    mock_which.side_effect = lambda x: "/path/to/" + x if x == "d2" else None
    assert detect_engine() == "d2"

    # Only PlantUML available
    mock_which.side_effect = lambda x: "/path/to/" + x if x == "plantuml" else None
    assert detect_engine() == "plantuml"


@patch("graphable.views.utils.which")
def test_detect_engine_none_available(mock_which):
    """Verify error if no engine is found."""
    mock_which.return_value = None
    with pytest.raises(RuntimeError, match="No rendering engine found on PATH"):
        detect_engine()


def test_get_image_exporter_explicit():
    """Verify get_image_exporter returns the correct function for an explicit engine."""
    with patch("graphable.views.mermaid.export_topology_mermaid_image") as mock_mermaid:
        exporter = get_image_exporter(Engine.MERMAID)
        assert exporter == mock_mermaid

    with patch("graphable.views.graphviz.export_topology_graphviz_image") as mock_gv:
        exporter = get_image_exporter("graphviz")
        assert exporter == mock_gv


@patch("graphable.views.utils.detect_engine")
def test_get_image_exporter_auto(mock_detect):
    """Verify get_image_exporter uses detect_engine when none provided."""
    mock_detect.return_value = "d2"
    with patch("graphable.views.d2.export_topology_d2_image") as mock_d2:
        exporter = get_image_exporter()
        assert exporter == mock_d2
        mock_detect.assert_called_once()


def test_get_image_exporter_invalid():
    """Verify get_image_exporter raises error for unknown engine."""
    with pytest.raises(ValueError, match="Unknown rendering engine: unknown"):
        get_image_exporter("unknown")
