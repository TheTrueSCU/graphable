import argparse
import sys
from pathlib import Path

from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.asciiflow import create_topology_ascii_flow
from graphable.views.csv import create_topology_csv
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
from graphable.views.html import (
    HtmlStylingConfig,
    create_topology_html,
    export_topology_html,
)
from graphable.views.json import create_topology_json
from graphable.views.mermaid import (
    MermaidStylingConfig,
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
from graphable.views.toml import create_topology_toml
from graphable.views.yaml import create_topology_yaml


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

    # Add a redundant edge for transitive reduction demo
    # Postgres -> React (redundant because Postgres -> FastAPI -> React)
    g.add_edge(db, ui)

    db.add_tag("persistence")
    cache.add_tag("ephemeral")
    api.add_tag("backend")
    worker.add_tag("backend")
    ui.add_tag("frontend")

    # 2. Container Protocols
    print("--- 2. Container Protocols ---")
    print(f"Graph size: {len(g)} nodes")
    print(f"Is 'Postgres' in graph? {'Postgres' in g}")
    print(f"Access node by reference: {g['FastAPI'].reference}")

    # 3. Reachability & Ordering
    print("\n--- 3. Reachability & Ordering ---")
    print(f"Ancestors of React: {[n.reference for n in g.ancestors(ui)]}")
    print(f"Descendants of Postgres: {[n.reference for n in g.descendants(db)]}")

    if db < ui:
        print(f"Verified: {db.reference} is an ancestor of {ui.reference}")
    if ui > db:
        print(f"Verified: {ui.reference} is a descendant of {db.reference}")

    # 4. Transitive Reduction
    print("\n--- 4. Transitive Reduction ---")
    print(f"Edges before reduction: {sum(len(n.dependents) for n in g)}")
    reduced_g = g.transitive_reduction()
    print(f"Edges after reduction: {sum(len(n.dependents) for n in reduced_g)}")

    # 5. Basic Text Output
    print("\n--- 5. Topological Order ---")
    for node in g:  # Using __iter__
        tags_str = f" (Tags: {', '.join(node.tags)})" if node.tags else ""
        print(f"- {node.reference}{tags_str}")

    print("\n--- 6. Text Tree (Sinks to Sources) ---")
    print(g.render(create_topology_tree_txt))  # Using .render()

    print("\n--- 7. ASCII Flowchart ---")
    print(create_topology_ascii_flow(g))

    # 8. Visualizations with Clustering
    print("\n--- 8. Mermaid Definition (Clustered) ---")
    mmd_config = MermaidStylingConfig(cluster_by_tag=True)
    print(g.render(create_topology_mermaid_mmd, config=mmd_config))

    print("\n--- 9. Graphviz DOT (Clustered) ---")
    gv_config = GraphvizStylingConfig(
        cluster_by_tag=True,
        graph_attr={"rankdir": "LR", "nodesep": "0.5"},
        node_attr_default={"shape": "rounded", "style": "filled", "fontname": "Arial"},
    )
    print(g.render(create_topology_graphviz_dot, config=gv_config))

    print("\n--- 10. D2 Definition (Clustered) ---")
    d2_config = D2StylingConfig(
        layout="dagre",
        cluster_by_tag=True,
        node_style_fnc=lambda n: {
            "fill": "lightblue"
            if "backend" in n.tags
            else "lightgreen"
            if "frontend" in n.tags
            else "lightgrey"
        },
    )
    print(create_topology_d2(g, d2_config))

    # 11. Serialization formats
    print("\n--- 11. YAML Definition ---")
    print(create_topology_yaml(g))

    print("\n--- 12. TOML Definition ---")
    print(create_topology_toml(g))

    print("\n--- 13. JSON Definition ---")
    print(create_topology_json(g))

    print("\n--- 14. CSV Edge List ---")
    print(create_topology_csv(g))

    # 15. Other Views
    print("\n--- 15. PlantUML Definition (Clustered) ---")
    puml_config = PlantUmlStylingConfig(
        node_type="component",
        direction="left to right direction",
        cluster_by_tag=True,
    )
    print(create_topology_plantuml(g, puml_config))

    print("\n--- 16. TikZ Definition ---")
    print(create_topology_tikz(g))

    print("\n--- 17. GraphML Definition ---")
    print(create_topology_graphml(g))

    # 18. Advanced Analysis & Interactive
    print("\n--- 18. NetworkX Integration ---")
    try:
        dg = g.to_networkx()
        print(
            f"NetworkX DiGraph created with {dg.number_of_nodes()} nodes and {dg.number_of_edges()} edges."
        )
    except ImportError as e:
        print(f"NetworkX not available: {e}")

    print("\n--- 19. Interactive HTML (Snippet) ---")
    html_config = HtmlStylingConfig(title="Demo Graph")
    html = create_topology_html(g, html_config)
    print(html[:200] + "...")

    # 20. Mutation Demo
    print("\n--- 20. Mutation Demo ---")
    g.remove_edge(db, ui)
    print(
        f"Removed redundant edge manually. Edges: {sum(len(n.dependents) for n in g)}"
    )
    g.remove_node(cache)
    print(f"Removed Redis. Graph size: {len(g)}")

    # 21. Parsing Demo
    print("\n--- 21. Parsing Demo ---")
    json_data = create_topology_json(g)
    parsed_g = Graph.from_json(json_data)
    print(f"Reconstructed graph from JSON. Nodes: {len(parsed_g)}")
    print(f"Nodes in topological order: {[n.reference for n in parsed_g]}")

    # 22. Equality Demo
    print("\n--- 22. Equality Demo ---")
    print(f"Is parsed_g equal to g? {parsed_g == g}")

    # 23. Optional SVG & HTML Generation
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
