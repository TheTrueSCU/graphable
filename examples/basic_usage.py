import argparse
import sys
from pathlib import Path

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.graphviz import (
    GraphvizStylingConfig,
    create_topology_graphviz_dot,
    export_topology_graphviz_svg,
)
from graphable.views.mermaid import (
    create_topology_mermaid_mmd,
    export_topology_mermaid_svg,
)
from graphable.views.texttree import create_topology_tree_txt


def main():
    parser = argparse.ArgumentParser(description="Demonstrate graphable features.")
    parser.add_argument(
        "--mermaid-svg",
        action="store_true",
        help="Generate Mermaid SVG (requires mmdc)",
    )
    parser.add_argument(
        "--graphviz-svg",
        action="store_true",
        help="Generate Graphviz SVG (requires dot)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="examples_output",
        help="Directory for SVG output",
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

    # 5. Optional SVG Generation
    if args.mermaid_svg or args.graphviz_svg:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(exist_ok=True)
        print(f"\n--- Generating SVGs in {out_dir}/ ---")

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


if __name__ == "__main__":
    main()
