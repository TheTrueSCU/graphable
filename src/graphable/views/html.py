from dataclasses import dataclass
from html import escape
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
            overflow: hidden;
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
            background: rgba(255, 255, 255, 0.9);
            padding: 5px 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            color: #333;
        }}
        .controls {{
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 999;
            background: rgba(255, 255, 255, 0.9);
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            display: flex;
            gap: 10px;
        }}
        .controls input {{
            padding: 5px;
            border: 1px solid #ccc;
            border-radius: 3px;
        }}
        .sidebar {{
            position: absolute;
            top: 0;
            right: -300px;
            width: 300px;
            height: 100vh;
            background: rgba(255, 255, 255, 0.95);
            z-index: 1000;
            box-shadow: -2px 0 5px rgba(0,0,0,0.1);
            transition: right 0.3s ease;
            padding: 20px;
            box-sizing: border-box;
            color: #333;
            overflow-y: auto;
        }}
        .sidebar.open {{
            right: 0;
        }}
        .sidebar h3 {{ margin-top: 0; }}
        .sidebar .close-btn {{
            position: absolute;
            top: 10px;
            right: 10px;
            cursor: pointer;
            font-size: 20px;
        }}
        .metadata-item {{ margin-bottom: 10px; }}
        .metadata-label {{ font-weight: bold; display: block; font-size: 0.8em; color: #666; }}
        .tag {{
            display: inline-block;
            background: #e0e0e0;
            padding: 2px 6px;
            border-radius: 3px;
            margin-right: 4px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h2>{title}</h2>
        <p>Scroll to zoom, drag to move nodes.</p>
    </div>
    <div class="controls">
        <input type="text" id="search" placeholder="Search nodes...">
    </div>
    <div id="sidebar" class="sidebar">
        <span class="close-btn" onclick="closeSidebar()">&times;</span>
        <div id="sidebar-content">
            <p>Select a node to view details.</p>
        </div>
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
                    selector: 'node:selected',
                    style: {{
                        'border-width': '4px',
                        'border-color': '#ff0',
                        'background-color': '#0056b3'
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

        // Sidebar logic
        function openSidebar(node) {{
            var data = node.data();
            var content = '<h3>' + data.label + '</h3>';
            
            content += '<div class="metadata-item"><span class="metadata-label">ID</span>' + data.id + '</div>';
            
            if (data.tags && data.tags.length > 0) {{
                content += '<div class="metadata-item"><span class="metadata-label">Tags</span>';
                data.tags.forEach(function(tag) {{
                    content += '<span class="tag">' + tag + '</span>';
                }});
                content += '</div>';
            }}
            
            if (data.duration !== undefined) {{
                content += '<div class="metadata-item"><span class="metadata-label">Duration</span>' + data.duration + 's</div>';
            }}
            
            if (data.status) {{
                content += '<div class="metadata-item"><span class="metadata-label">Status</span>' + data.status + '</div>';
            }}

            document.getElementById('sidebar-content').innerHTML = content;
            document.getElementById('sidebar').classList.add('open');
        }}

        function closeSidebar() {{
            document.getElementById('sidebar').classList.remove('open');
            cy.$(':selected').unselect();
        }}

        cy.on('tap', 'node', function(evt){{
            openSidebar(evt.target);
        }});

        cy.on('tap', function(evt){{
            if (evt.target === cy) {{
                closeSidebar();
            }}
        }});

        // Search logic
        document.getElementById('search').addEventListener('input', function(e) {{
            var query = e.target.value.toLowerCase();
            cy.nodes().forEach(function(node) {{
                if (query && node.data('label').toLowerCase().includes(query)) {{
                    node.addClass('highlighted');
                    node.style('background-color', '#ff0');
                }} else {{
                    node.removeClass('highlighted');
                    node.style('background-color', '{node_color}');
                }}
            }});
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

    # Escape JSON for safe inclusion in <script> block
    safe_elements = elements_json.replace("</script>", r"<\/script>")

    return _HTML_TEMPLATE.format(
        title=escape(config.title),
        elements=safe_elements,
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
