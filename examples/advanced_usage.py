from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.mermaid import MermaidStylingConfig, create_topology_mermaid_mmd


def build_complex_project():
    """
    Simulate a complex software project with multiple subsystems.

    Structure:
    - Backend: Database -> API -> Worker
    - Frontend: API -> Web UI, Mobile App
    - Infrastructure: Monitoring, Logging (depend on all)
    """
    # 1. Core Services
    db = Graphable("Database Cluster")
    api = Graphable("API Gateway")
    worker = Graphable("Background Worker")

    # 2. Frontend Applications
    web = Graphable("React Web App")
    mobile = Graphable("Flutter Mobile App")

    # 3. Observability
    logging = Graphable("ELK Logging")
    monitoring = Graphable("Prometheus/Grafana")

    # Build Graph
    g = Graph()

    # Backend dependencies
    g.add_edge(db, api, label="provides data")
    g.add_edge(api, worker, label="enqueues tasks")

    # Frontend dependencies
    g.add_edge(api, web, label="REST API")
    g.add_edge(api, mobile, label="gRPC")

    # Observability (depends on everything)
    for node in [db, api, worker, web, mobile]:
        g.add_edge(node, logging, label="logs")
        g.add_edge(node, monitoring, label="metrics")

    # Metadata for analysis
    db.duration = 15.0
    api.duration = 5.0
    worker.duration = 10.0
    web.duration = 3.0
    mobile.duration = 4.0

    # Tags for visualization clustering
    for n in [db, api, worker]:
        n.add_tag("backend")
    for n in [web, mobile]:
        n.add_tag("frontend")
    for n in [logging, monitoring]:
        n.add_tag("ops")

    return g, db, api, worker, web, mobile


def main():
    print("--- Graphable Advanced Usage Demo ---")
    g, db, api, worker, web, mobile = build_complex_project()

    print(f"Total project nodes: {len(g)}")
    print(f"Sinks (Final Deliverables): {[n.reference for n in g.sinks]}")

    # 1. Critical Path Analysis
    print("\n--- 1. Critical Path Analysis ---")
    cp = g.critical_path()
    print(f"Critical Path: {' -> '.join([n.reference for n in cp])}")

    analysis = g.cpm_analysis()
    max_duration = max(v["EF"] for v in analysis.values())
    print(f"Estimated Project Duration: {max_duration} units")

    # 2. Impact Analysis (Downstream)
    print("\n--- 2. Impact Analysis ---")
    print("What is impacted if the 'API Gateway' changes?")
    impacted = list(g.descendants(api))
    for n in impacted:
        print(f"  - {n.reference}")

    # 3. Traceability (Upstream)
    print("\n--- 3. Traceability Analysis ---")
    print("What does the 'Mobile App' depend on?")
    deps = list(g.ancestors(mobile))
    for n in deps:
        print(f"  - {n.reference}")

    # 4. Filtered Subgraphs
    print("\n--- 4. Backend Focus Subgraph ---")
    backend_g = g.subgraph_tagged("backend")
    print(f"Nodes in backend subgraph: {[n.reference for n in backend_g]}")

    # 5. Visualizing the full picture
    print("\n--- 5. Mermaid Definition (Clustered) ---")
    config = MermaidStylingConfig(cluster_by_tag=True)
    print(g.render(create_topology_mermaid_mmd, config=config))

    # 6. Saving to different formats
    print("\n--- 6. Exporting to multiple formats ---")
    print("Export logic ready (write() calls commented out in demo).")


if __name__ == "__main__":
    main()
