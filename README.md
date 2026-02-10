# graphable

[![CI](https://github.com/TheTrueSCU/graphable/actions/workflows/ci.yml/badge.svg)](https://github.com/TheTrueSCU/graphable/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`graphable` is a lightweight, type-safe Python library for building, managing, and visualizing dependency graphs. It provides a simple API for defining nodes and their relationships, performing topological sorts, and exporting graphs to various formats like Mermaid, Graphviz, and ASCII text trees.

## Features

- **Type-Safe:** Built with modern Python generics and type hints.
- **Topological Sorting:** Easily get nodes in dependency order.
- **Cycle Detection:** Built-in protection against circular dependencies.
- **Filtering & Tagging:** Create subgraphs based on custom predicates or tags.
- **Visualizations:**
    - **Mermaid:** Generate flowchart definitions or export directly to SVG.
    - **Graphviz:** Generate DOT definitions or export to SVG with custom styling.
    - **D2:** Generate D2 definitions or export to SVG with modern styling and layouts.
    - **PlantUML:** Generate component or deployment diagram definitions.
    - **TikZ:** Generate high-quality LaTeX definitions for academic documents.
    - **GraphML:** Industrial-standard XML export for professional analysis tools (Gephi, yEd).
    - **Interactive HTML:** Generate a single, portable HTML file with zooming and panning.
    - **JSON & Cytoscape:** Export graph structure as machine-readable data.
    - **CSV:** Export simple edge lists for data processing.
    - **NetworkX:** Seamless integration with the NetworkX library for advanced analysis.
    - **Text Tree & ASCII Flowchart:** Generate beautiful ASCII representations.
- **Modern Tooling:** Managed with `uv` and `just`.

## Installation

```bash
uv add graphable
# or
pip install graphable
```

## Quick Start

```python
from graphable.graph import Graph
from graphable.graphable import Graphable
from graphable.views.texttree import create_topology_tree_txt

# 1. Define your nodes
a = Graphable("Database")
b = Graphable("API Service")
c = Graphable("Web Frontend")

# 2. Build the graph
g = Graph()
g.add_edge(a, b)  # API Service depends on Database
g.add_edge(b, c)  # Web Frontend depends on API Service

# 3. Get topological order
for node in g.topological_order():
    print(node.reference)
# Output: Database, API Service, Web Frontend

# 4. Visualize as a text tree
print(create_topology_tree_txt(g))
# Output:
# Web Frontend
# └─ API Service
#    └─ Database
```

## Visualizing with ASCII Flowchart

```python
from graphable.views.asciiflow import create_topology_ascii_flow

print(create_topology_ascii_flow(g))
# Output:
# +----------+
# | Database |
# +----------+
#   v
#   +--> API Service
#
# +-------------+
# | API Service |
# +-------------+
#   v
#   +--> Web Frontend
```

## Visualizing with Mermaid

```python
from graphable.views.mermaid import create_topology_mermaid_mmd

mmd = create_topology_mermaid_mmd(g)
print(mmd)
# Output:
# flowchart TD
# Database --> API Service
# API Service --> Web Frontend
```

## Visualizing with Graphviz

```python
from graphable.views.graphviz import create_topology_graphviz_dot

dot = create_topology_graphviz_dot(g)
print(dot)
# Output:
# digraph G {
#     "Database" [label="Database"];
#     "Database" -> "API Service";
#     "API Service" [label="API Service"];
#     "API Service" -> "Web Frontend";
#     "Web Frontend" [label="Web Frontend"];
# }
```

## Advanced Analysis with NetworkX

If you have `networkx` installed, you can convert your graph for advanced analysis:

```python
import networkx as nx

# Convert to NetworkX DiGraph
dg = g.to_networkx()

# Use NetworkX algorithms
print(nx.dag_longest_path(dg))
# Output: ['Database', 'API Service', 'Web Frontend']
```

## Visualizing with D2

```python
from graphable.views.d2 import create_topology_d2

d2 = create_topology_d2(g)
print(d2)
# Output:
# Database: Database
# Database -> API Service
# API Service: API Service
# API Service -> Web Frontend
# Web Frontend: Web Frontend
```

## Documentation

Full documentation is available in the `docs/` directory. You can build it locally:

```bash
just docs-view
```

## Development

This project uses `uv` for dependency management and `just` as a command runner.

```bash
just install    # Install dependencies
just check      # Run linting, type checking, and tests
just coverage   # Run tests with coverage report
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
