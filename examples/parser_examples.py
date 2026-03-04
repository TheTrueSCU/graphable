from graphable.graph import Graph
from graphable.views.texttree import create_topology_tree_txt


def demo_json_parsing():
    print("\n--- JSON Parsing ---")
    json_data = """
    {
      "nodes": [{"id": "A"}, {"id": "B"}],
      "edges": [{"source": "A", "target": "B", "label": "depends"}]
    }
    """
    g = Graph.from_json(json_data)
    print(f"Loaded {len(g)} nodes from JSON string.")
    print(g.render(create_topology_tree_txt))


def demo_yaml_parsing():
    print("\n--- YAML Parsing ---")
    yaml_data = """
nodes:
  - id: Server
  - id: Client
edges:
  - source: Server
    target: Client
    """
    g = Graph.from_yaml(yaml_data)
    print(f"Loaded {len(g)} nodes from YAML string.")
    print(g.render(create_topology_tree_txt))


def demo_toml_parsing():
    print("\n--- TOML Parsing ---")
    toml_data = """
[[nodes]]
id = "App"
[[nodes]]
id = "DB"

[[edges]]
source = "DB"
target = "App"
"""
    g = Graph.from_toml(toml_data)
    print(f"Loaded {len(g)} nodes from TOML string.")
    print(g.render(create_topology_tree_txt))


def demo_csv_parsing():
    print("\n--- CSV Parsing ---")
    csv_data = "source,target\nNode1,Node2\nNode2,Node3"
    g = Graph.from_csv(csv_data)
    print(f"Loaded {len(g)} nodes from CSV string.")
    print(g.render(create_topology_tree_txt))


def main():
    print("Graphable Parser Examples\n")
    demo_json_parsing()
    demo_yaml_parsing()
    demo_toml_parsing()
    demo_csv_parsing()


if __name__ == "__main__":
    main()
