from unittest.mock import patch
import pytest
from graphable.views.utils import detect_engine

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
