from graphable.cyclic_graph import CyclicGraph
from graphable.graphable import Graphable
from graphable.views.mermaid import create_topology_mermaid_mmd


def demo_cyclic_graph():
    """
    Demonstrate how to work with Cyclic Graphs in graphable.
    """
    print("--- Graphable Cyclic Usage Demo ---")

    # 1. Create nodes that form a cycle
    # A common real-world example: circular feedback in a system
    sensor = Graphable("Sensor")
    controller = Graphable("Controller")
    actuator = Graphable("Actuator")

    # 2. Build the Cyclic Graph
    g = CyclicGraph()

    g.add_edge(sensor, controller, label="reads")
    g.add_edge(controller, actuator, label="commands")
    g.add_edge(
        actuator, sensor, label="affects"
    )  # Cycle: Sensor -> Controller -> Actuator -> Sensor

    print(f"Graph nodes: {[n.reference for n in g]}")
    print(f"Graph is cyclic. Number of nodes: {len(g)}")

    # 3. Suggesting cycle breaks
    print("\n--- 1. Suggesting Cycle Breaks ---")
    breaks = g.suggest_cycle_breaks()
    for u, v in breaks:
        print(f"Suggested break: {u.reference} -> {v.reference}")

    # 4. Converting to Acyclic
    print("\n--- 2. Converting to Acyclic Graph ---")
    dag = g.to_acyclic()
    print(f"DAG nodes: {[n.reference for n in dag]}")

    # Now we can perform DAG operations like topological sort
    print(f"Topological Order: {[n.reference for n in dag.topological_order()]}")

    # 5. Visualization
    print("\n--- 3. Mermaid Representation ---")
    print(g.render(create_topology_mermaid_mmd))


if __name__ == "__main__":
    demo_cyclic_graph()
