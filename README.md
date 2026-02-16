# graphable

[![CI](https://github.com/TheTrueSCU/graphable/actions/workflows/ci.yml/badge.svg)](https://github.com/TheTrueSCU/graphable/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`graphable` is a lightweight, type-safe Python library for building, managing, and visualizing dependency graphs. It provides a simple API for defining nodes and their relationships, performing topological sorts, and exporting graphs to various formats like Mermaid, Graphviz, and ASCII text trees.

## Features

- **Type-Safe:** Built with modern Python generics and type hints.
- **Topological Sorting:** Easily get nodes in dependency order.
- **Cycle Detection:** Built-in protection against circular dependencies.
- **Filtering & Tagging:** Create subgraphs based on custom predicates or tags.
- **Graph Syncing:** Automatically expand graphs to include all reachable nodes with `discover()`.
- **Transitive Reduction:** Automatically remove redundant edges while preserving reachability.
- **Reachability Analysis:** Easily find ancestors or descendants of any node.
- **Node Ordering:** Compare nodes using standard operators (`a < b` means `a` is an ancestor of `b`).
- **Container Protocols:** Use Pythonic idioms like `len(graph)`, `node in graph`, and `for node in graph`.
- **Integrity:** Generate and validate deterministic BLAKE2b checksums of graph structure and metadata.
- **Parallel Sorting:** Group nodes into execution layers for parallel processing with `parallelized_topological_order()`.
- **Orchestration Ready:** Track node `status` and `duration` for workflow execution.
- **Edge Attributes:** Support for weights, labels, and custom metadata on relationships.
- **Diffing:** Compare two graphs structurally and visually with `diff()` and `diff_graph()`.
- **Dependency Algorithms:** Native implementations for:
    - **Critical Path Method (CPM):** Identify bottlenecks based on node durations.
    - **BFS & DFS:** Perform breadth-first or depth-first traversals with generators.
    - **Longest Path:** Find the deepest chain of dependencies.
    - **All Paths:** Explore every possible connection between two nodes.
    - **Transitive Closure:** Analyze the full "blast radius" of dependencies.
    - **Cycle Resolution:** Get suggestions for breaking circular dependencies with `suggest_cycle_breaks()`.
- **Advanced Slicing:** Extract focused subgraphs using `upstream_of()`, `downstream_of()`, or `subgraph_between()`.
- **Unified I/O:** Easy `Graph.read()` and `graph.write()` methods with automatic format detection.
- **Parsing:** Reconstruct graphs from JSON, YAML, TOML, CSV, or GraphML files and strings.
- **Clustering:** Group nodes into subgraphs/clusters in visualizations based on tags.
- **Visualizations:**
    - **Mermaid:** Generate flowchart definitions or export directly to SVG. Supports clustering and color-coded diffs.
    - **Graphviz:** Generate DOT definitions or export to SVG with custom styling. Supports clustering.
    - **D2:** Generate D2 definitions or export to SVG with modern styling and layouts. Supports clustering.
    - **PlantUML:** Generate component or deployment diagram definitions. Supports clustering.
    - **TikZ:** Generate high-quality LaTeX definitions for academic documents.
    - **GraphML:** Industrial-standard XML export for professional analysis tools (Gephi, yEd).
    - **Interactive HTML:** Generate a single, portable HTML file with zooming, panning, and **Live Reload** when used with the CLI.
    - **JSON, YAML & TOML:** Export graph structure as machine-readable data.
    - **CSV:** Export simple edge lists for data processing.
    - **NetworkX:** Seamless integration with the NetworkX library for advanced analysis.
    - **Text Tree & ASCII Flowchart:** Generate beautiful ASCII representations.
- **Modern Tooling:** Managed with `uv` and `just`.

## Installation

### As a Library

Use your preferred package manager to add `graphable` to your project:

```bash
# Using uv (recommended)
uv add graphable

# Using pip
pip install graphable
```

### As a Command Line Tool

To use the `graphable` CLI globally, we recommend using `pipx`. You can choose between the bare-bones version or the full-featured "Rich" version:

```bash
# Full version with beautiful terminal output (recommended)
pipx install "graphable[cli]"

# Bare-bones version (standard library only)
pipx install graphable
```

---

## Command Line Interface

`graphable` provides a powerful CLI for analyzing and transforming graph files.

### Basic Usage

```bash
# Get summary information about a graph
graphable info topology.json

# Validate a graph for cycles and consistency
graphable check topology.yaml

# Convert between graph data formats
graphable convert input.json output.yaml

# Render a graph as an image (SVG or PNG)
graphable render input.json output.png --engine graphviz

# Simplify a graph using transitive reduction
graphable reduce complex.graphml simple.svg

# Compare two versions of a graph
graphable diff old.json new.json

# Generate a visual diff (added elements in green, removed in red)
graphable diff old.json new.json -o diff.svg

# Serve a live-reloading interactive visualization
graphable serve architecture.yaml
```

### Automation & CI/CD

If you have the `cli` extra installed but need plain-text output for logging or automation, use the `--bare` flag:

```bash
graphable --bare info topology.json
```

### Supported Formats

The CLI automatically detects formats based on file extensions:
- **Parsers:** `.json`, `.yaml`/`.yml`, `.toml`, `.csv`, `.graphml`
- **Exporters:** `.json`, `.yaml`, `.toml`, `.csv`, `.graphml`, `.dot`, `.mmd`, `.d2`, `.puml`, `.html`, `.tex`, `.txt`, `.ascii`, `.cy.json`
- **Image Engines:** Mermaid, Graphviz, D2, PlantUML (Supports `.svg` and `.png`)

---

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

## Advanced Analysis

### Edge Attributes & Orchestration

Track durations and weights for workflow optimization:

```python
# Add weighted edges
g.add_edge(task_a, task_b, weight=10, label="critical path")

# Set task metadata
task_a.duration = 5.0
task_a.status = "completed"
```

### Critical Path Method (CPM)

Identify the longest chain of dependencies:

```python
analysis = g.cpm_analysis()
print(f"Project duration: {max(n['EF'] for n in analysis.values())}")

critical_nodes = g.critical_path()
print(f"Critical Path: {[n.reference for n in critical_nodes]}")
```

### Graph Diffing

Compare two versions of a graph:

```python
diff_data = g_v1.diff(g_v2)
print(f"Added nodes: {diff_data['added_nodes']}")

# Generate a visual diff graph for rendering
dg = g_v1.diff_graph(g_v2)
print(dg.render(create_topology_mermaid_mmd))
```

### Advanced Slicing

Focus on specific parts of the graph:

```python
# All nodes required by 'Web UI'
sub = g.upstream_of(ui)

# All nodes impacted by a change in 'Database'
sub = g.downstream_of(db)

# Everything between 'Source' and 'Sink'
sub = g.subgraph_between(source, sink)
```

### Native Traversals (BFS & DFS)

Perform idiomatic iterations over your graph:

```python
from graphable.enums import Direction

# Visit every node reachable from 'Task A' breadth-first
for node in g.bfs(task_a):
    print(f"Visiting: {node.reference}")

# Explore dependencies (upstream) depth-first
for node in g.dfs(task_a, direction=Direction.UP):
    print(f"Required by: {node.reference}")
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

## Advanced Usage

### Pythonic Protocols

```python
print(f"Nodes: {len(g)}")
if "Database" in g:
    node = g["Database"]
    
for node in g:  # Iterates in topological order
    print(node.reference)
```

### Transitive Reduction

Clean up your graphs by removing redundant edges:

```python
reduced_g = g.transitive_reduction()
# Or render directly
print(g.render(create_topology_mermaid_mmd, transitive_reduction=True))
```

### Clustering by Tags

Group nodes in visualizations:

```python
from graphable.views.mermaid import MermaidStylingConfig

a.add_tag("backend")
b.add_tag("backend")
config = MermaidStylingConfig(cluster_by_tag=True)

print(g.render(create_topology_mermaid_mmd, config=config))
```

### Parsing Graphs

Reconstruct graphs from exported data:

```python
# From a file
g = Graph.from_json("graph.json")

# From a string (YAML)
yaml_data = """
nodes:
  - id: Database
  - id: API
edges:
  - source: Database
    target: API
"""
g = Graph.from_yaml(yaml_data)
```

### Equality Comparison

Compare graphs easily:

```python
g1 = Graph.from_json("topology.json")
g2 = Graph.from_yaml("topology.yaml")

if g1 == g2:
    print("Graphs are identical in structure and tags.")
```

### Node Ordering

Nodes support comparison based on reachability:

```python
if db < api:
    print("Database is an ancestor of API")
    
if ui > api:
    print("UI is a descendant of API")
```

### Checksums & Integrity

Verify your graph hasn't changed:

```python
digest = g.checksum()
# ... later ...
if g.validate_checksum(digest):
    print("Graph integrity verified.")
```

### Unified I/O

Read and write any format without thinking about parsers:

```python
# Automatically detects JSON
g = Graph.read("topology.json")

# Automatically detects YAML
g.write("topology.yaml")
```

## Documentation

Full documentation is available in the `docs/` directory. You can build it locally:

```bash
just docs-view
```

## Security

`graphable` takes security seriously. We implement strict sanitization for all external inputs and use secure defaults for parsing and export. For more details, see our [Security Policy](https://thetruescu.github.io/graphable/security.html).

If you discover a vulnerability, please report it via email to the maintainer.

## Development

This project uses `uv` for dependency management and `just` as a command runner.

```bash
just install    # Install dependencies
just check      # Run linting, type checking, and tests
just coverage   # Run tests with coverage report
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
