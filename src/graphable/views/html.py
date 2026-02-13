from dataclasses import dataclass
from logging import getLogger
from pathlib import Path

from ..graph import Graph
from ..registry import register_view
from .cytoscape import CytoscapeStylingConfig, create_topology_cytoscape

logger = getLogger(__name__)


@dataclass
class HtmlStylingConfig:
    """
    Configuration for Standalone HTML graph visualization.

    Attributes:
        title: Page title.
        layout: Cytoscape layout algorithm (e.g., 'breadthfirst', 'dagre', 'cose').
        theme: Color theme ('light' or 'dark').
        node_color: CSS color for nodes.
        edge_color: CSS color for edges.
        cy_config: Underlying Cytoscape configuration.
    """

    title: str = "Graphable Visualization"
    layout: str = "breadthfirst"
    theme: str = "light"
    node_color: str = "#007bff"
    edge_color: str = "#ccc"
    cy_config: CytoscapeStylingConfig | None = None


_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>
    <style>
        body {{
            font-family: sans-serif;
            margin: 0;
            padding: 0;
            background-color: {bg_color};
            color: {text_color};
        }}
        #cy {{
            width: 100vw;
            height: 100vh;
            display: block;
        }}
        .header {{
            position: absolute;
            top: 10px;
            left: 10px;
            z-index: 999;
            background: rgba(255, 255, 255, 0.8);
            padding: 5px 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    <div class="header">
        <h2>{title}</h2>
        <p>Scroll to zoom, drag to move nodes.</p>
    </div>
    <div id="cy"></div>
    <script>
        // Live Reload Logic
        (function() {{
            var protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            var address = protocol + '//' + window.location.host + '/ws';
            var socket = new WebSocket(address);
            socket.onmessage = function(msg) {{
                if (msg.data == 'reload') window.location.reload();
            }};
        }})();

        var cy = cytoscape({{
            container: document.getElementById('cy'),
            elements: {elements},
            style: [
                {{
                    selector: 'node',
                    style: {{
                        'background-color': '{node_color}',
                        'label': 'data(label)',
                        'color': '{text_color}',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'width': '60px',
                        'height': '60px',
                        'font-size': '12px'
                    }}
                }},
                {{
                    selector: 'edge',
                    style: {{
                        'width': 2,
                        'line-color': '{edge_color}',
                        'target-arrow-color': '{edge_color}',
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier'
                    }}
                }}
            ],
            layout: {{
                name: '{layout}',
                directed: true,
                padding: 50
            }}
        }});
    </script>
</body>
</html>
"""


def create_topology_html(graph: Graph, config: HtmlStylingConfig | None = None) -> str:
    """
    Generate a standalone interactive HTML representation of the graph.

    Args:
        graph (Graph): The graph to convert.
        config (HtmlStylingConfig | None): Export configuration.

    Returns:
        str: The full HTML content.
    """
    logger.debug("Creating Interactive HTML representation.")
    config = config or HtmlStylingConfig()

    # Get elements using the Cytoscape view
    elements_json = create_topology_cytoscape(graph, config.cy_config)

    # Set theme colors
    bg_color = "#fff" if config.theme == "light" else "#222"
    text_color = "#333" if config.theme == "light" else "#eee"

    return _HTML_TEMPLATE.format(
        title=config.title,
        elements=elements_json,
        layout=config.layout,
        bg_color=bg_color,
        text_color=text_color,
        node_color=config.node_color,
        edge_color=config.edge_color,
    )


@register_view(".html", creator_fnc=create_topology_html)
def export_topology_html(
    graph: Graph, output: Path, config: HtmlStylingConfig | None = None
) -> None:
    """
    Export the graph to a standalone HTML file.

    Args:
        graph (Graph): The graph to export.
        output (Path): The output file path.
        config (HtmlStylingConfig | None): Export configuration.
    """
    logger.info(f"Exporting Interactive HTML to: {output}")
    with open(output, "w+") as f:
        f.write(create_topology_html(graph, config))
