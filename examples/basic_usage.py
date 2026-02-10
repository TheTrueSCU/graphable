import argparse
import sys
from pathlib import Path

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.asciiflow import create_topology_ascii_flow
from graphable.views.csv import create_topology_csv
from graphable.views.cytoscape import create_topology_cytoscape
from graphable.views.d2 import (
    D2StylingConfig,
    create_topology_d2,
    export_topology_d2_svg,
)
from graphable.views.graphml import create_topology_graphml
from graphable.views.graphviz import (
    GraphvizStylingConfig,
    create_topology_graphviz_dot,
    export_topology_graphviz_svg,
)
from graphable.views.html import HtmlStylingConfig, create_topology_html, export_topology_html
from graphable.views.json import create_topology_json
from graphable.views.markdown import wrap_in_markdown
from graphable.views.mermaid import (
    create_topology_mermaid_mmd,
    export_topology_mermaid_svg,
)
from graphable.views.plantuml import (
    PlantUmlStylingConfig,
    create_topology_plantuml,
    export_topology_plantuml_svg,
)
from graphable.views.texttree import create_topology_tree_txt
from graphable.views.tikz import create_topology_tikz


def main():
    parser = argparse.ArgumentParser(description="Demonstrate graphable features.")
    parser.add_argument(
        "--d2-svg",
        action="store_true",
        help="Generate D2 SVG (requires d2)",
    )
    parser.add_argument(
        "--graphviz-svg",
        action="store_true",
        help="Generate Graphviz SVG (requires dot)",
    )
    parser.add_argument(
        "--interactive-html",
        action="store_true",
        help="Generate interactive HTML",
    )
    parser.add_argument(
        "--mermaid-svg",
        action="store_true",
        help="Generate Mermaid SVG (requires mmdc)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="examples_output",
        help="Directory for SVG output",
    )
    parser.add_argument(
        "--puml-svg",
        action="store_true",
        help="Generate PlantUML SVG (requires plantuml)",
    )
    args = parser.parse_args()

    # 1. Define nodes and relationships
    db = Graphable("Postgres")
    cache = Graphable("Redis")
    api = Graphable("FastAPI")
    worker = Graphable("Celery")
    ui = Graphable("React")

    g = Graph()
    g.add_edge(db, api)
    g.add_edge(cache, api)
    g.add_edge(api, ui)
    g.add_edge(db, worker)
    g.add_edge(api, worker)

    db.add_tag("persistence")
    cache.add_tag("ephemeral")
    api.add_tag("backend")
    worker.add_tag("backend")
    ui.add_tag("frontend")

    # 2. Basic Text Output
    print("--- Topological Order ---")
    for node in g.topological_order():
        tags_str = f" (Tags: {', '.join(node.tags)})" if node.tags else ""
        print(f"- {node.reference}{tags_str}")

    print("\n--- Text Tree (Sinks to Sources) ---")
    print(create_topology_tree_txt(g))

    print("\n--- ASCII Flowchart ---")
    print(create_topology_ascii_flow(g))

    # 3. Mermaid View
    print("\n--- Mermaid Definition ---")
    print(create_topology_mermaid_mmd(g))

    # 4. Graphviz View with custom styling
    print("\n--- Graphviz DOT ---")
    gv_config = GraphvizStylingConfig(
        graph_attr={"rankdir": "LR", "nodesep": "0.5"},
        node_attr_default={"shape": "rounded", "style": "filled", "fontname": "Arial"},
        node_attr_fnc=lambda n: {
            "fillcolor": "lightblue"
            if "backend" in n.tags
            else "lightgreen"
            if "frontend" in n.tags
            else "lightgrey"
        },
    )
    print(create_topology_graphviz_dot(g, gv_config))

    # 5. D2 View with custom styling
    print("\n--- D2 Definition ---")
    d2_config = D2StylingConfig(
        layout="dagre",
        node_style_fnc=lambda n: {
            "fill": "lightblue"
            if "backend" in n.tags
            else "lightgreen"
            if "frontend" in n.tags
            else "lightgrey"
        },
    )
    print(create_topology_d2(g, d2_config))

    # 6. PlantUML View
    print("\n--- PlantUML Definition ---")
    puml_config = PlantUmlStylingConfig(
        node_type="component", direction="left to right direction"
    )
    print(create_topology_plantuml(g, puml_config))

    # 7. JSON View
    print("\n--- JSON Definition ---")
    print(create_topology_json(g))

    # 8. Cytoscape JSON View
    print("\n--- Cytoscape JSON Definition ---")
    print(create_topology_cytoscape(g))

    # 9. TikZ View
    print("\n--- TikZ Definition ---")
    print(create_topology_tikz(g))

    # 10. CSV View
    print("\n--- CSV Edge List ---")
    print(create_topology_csv(g))

    # 11. GraphML View
    print("\n--- GraphML Definition ---")
    print(create_topology_graphml(g))

    # 12. Interactive HTML View
    print("\n--- Interactive HTML (Snippet) ---")
    html_config = HtmlStylingConfig(title="Demo Graph")
    html = create_topology_html(g, html_config)
    print(html[:200] + "...")

    # 13. Markdown Wrapper (Mermaid)
    print("\n--- Markdown Wrapped Mermaid ---")
    mermaid = create_topology_mermaid_mmd(g)
    print(wrap_in_markdown(mermaid, "mermaid"))

    # 12. NetworkX Integration
    print("\n--- NetworkX Integration ---")
    try:
        dg = g.to_networkx()
        print(
            f"NetworkX DiGraph created with {dg.number_of_nodes()} nodes and {dg.number_of_edges()} edges."
        )
        print(f"Nodes with metadata: {list(dg.nodes(data=True))}")
    except ImportError as e:
        print(f"NetworkX not available: {e}")

    # 13. Optional SVG & HTML Generation
    if (
        args.mermaid_svg
        or args.graphviz_svg
        or args.d2_svg
        or args.puml_svg
        or args.interactive_html
    ):
        out_dir = Path(args.output_dir)
        out_dir.mkdir(exist_ok=True)
        print(f"\n--- Generating Assets in {out_dir}/ ---")

        # Mermaid SVG
        if args.mermaid_svg:
            mermaid_out = out_dir / "topology_mermaid.svg"
            try:
                export_topology_mermaid_svg(g, mermaid_out)
                print(f"Successfully generated: {mermaid_out}")
            except Exception as e:
                print(f"Failed to generate Mermaid SVG: {e}", file=sys.stderr)

        # Graphviz SVG
        if args.graphviz_svg:
            graphviz_out = out_dir / "topology_graphviz.svg"
            try:
                export_topology_graphviz_svg(g, graphviz_out, gv_config)
                print(f"Successfully generated: {graphviz_out}")
            except Exception as e:
                print(f"Failed to generate Graphviz SVG: {e}", file=sys.stderr)

        # D2 SVG
        if args.d2_svg:
            d2_out = out_dir / "topology_d2.svg"
            try:
                export_topology_d2_svg(g, d2_out, d2_config)
                print(f"Successfully generated: {d2_out}")
            except Exception as e:
                print(f"Failed to generate D2 SVG: {e}", file=sys.stderr)

        # PlantUML SVG
        if args.puml_svg:
            puml_out = out_dir / "topology_plantuml.svg"
            try:
                export_topology_plantuml_svg(g, puml_out, puml_config)
                print(f"Successfully generated: {puml_out}")
            except Exception as e:
                print(f"Failed to generate PlantUML SVG: {e}", file=sys.stderr)

        # Interactive HTML
        if args.interactive_html:
            html_out = out_dir / "topology_interactive.html"
            try:
                export_topology_html(g, html_out, html_config)
                print(f"Successfully generated: {html_out}")
            except Exception as e:
                print(f"Failed to generate Interactive HTML: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
