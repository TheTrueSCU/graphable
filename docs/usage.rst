Usage Examples
==============

The following example demonstrates the core features of ``graphable``, including building a graph, performing topological sorts, and generating various visualizations.

Basic Usage
-----------

This script (available in the repository as ``examples/basic_usage.py``) shows how to:
- Define nodes and relationships.
- Use tags for organization and styling.
- Utilize orchestration attributes (duration, status).
- Perform advanced analysis (CPM, diffing, slicing).
- Generate text-based and graphical representations.

.. code-block:: bash

   uv run examples/basic_usage.py --mermaid-svg --graphviz-svg --output-dir docs/_static/examples > docs/_static/examples/basic_usage_output.txt

.. literalinclude:: ../examples/basic_usage.py
   :language: python
   :linenos:
   :caption: examples/basic_usage.py

Output
------

Running the script produces the following text output:

.. literalinclude:: _static/examples/basic_usage_output.txt
   :language: text
   :caption: Execution Output

Orchestration & Edge Attributes
-------------------------------

``graphable`` supports rich metadata on both nodes and edges, making it ideal for task orchestration and workflow management.

**Node Attributes**

Nodes have built-in support for ``duration`` and ``status``:

.. code-block:: python

   task = Graphable("Compile")
   task.duration = 15.5  # seconds
   task.status = "running"

**Edge Attributes**

Edges can store arbitrary key-value pairs, such as weights or labels:

.. code-block:: python

   # Add edge with attributes
   graph.add_edge(node_a, node_b, weight=10, label="primary")

   # Retrieve attributes
   attrs = node_a.edge_attributes(node_b)
   print(attrs["weight"])

   # Modify attributes
   node_a.set_edge_attribute(node_b, "weight", 20)

Dependency Algorithms
---------------------

Beyond simple topological sorts, ``graphable`` provides native implementations of common graph algorithms.

**Critical Path Method (CPM)**

Identify the "critical" chain of tasks that determines the minimum project duration:

.. code-block:: python

   # Returns ES, EF, LS, LF, and slack for all nodes
   analysis = graph.cpm_analysis()

   # Returns a list of nodes on the critical path
   cp = graph.critical_path()

**Longest Path**

Find the deepest chain of dependencies based on node durations:

.. code-block:: python

   lp = graph.longest_path()

**Transitive Closure**

Analyze the full reachability of your graph. The transitive closure contains an edge (u, v) if a path exists from u to v in the original graph:

.. code-block:: python

   closure = graph.transitive_closure()

**All Paths**

Find every possible route between two nodes:

.. code-block:: python

   paths = graph.all_paths(source, target)

Advanced Slicing
----------------

Extract focused subgraphs to analyze specific parts of your dependency tree.

.. code-block:: python

   # All nodes that 'target' depends on (recursively)
   upstream = graph.upstream_of(target)

   # All nodes that depend on 'source' (recursively)
   downstream = graph.downstream_of(source)

   # All nodes and edges on any path between 'start' and 'end'
   between = graph.subgraph_between(start, end)

Custom Traversals (BFS & DFS)
-----------------------------

For custom logic, you can perform breadth-first or depth-first searches using generators. This allows you to use standard Python loops to process nodes in a specific order.

.. code-block:: python

   from graphable.enums import Direction

   # Breadth-First Search (level-by-level)
   for node in graph.bfs(start_node):
       print(f"Current depth level node: {node.reference}")

   # Depth-First Search (deep chains)
   for node in graph.dfs(start_node, direction=Direction.UP):
       print(f"Ancestry chain node: {node.reference}")

The ``bfs()`` and ``dfs()`` methods both accept a ``direction`` parameter (``Direction.UP`` or ``Direction.DOWN``) and a ``limit_to_graph`` boolean (defaulting to ``True``).

Graph Diffing
-------------

Compare two versions of a graph to identify what changed.

**Structural Diff**

Get a detailed dictionary of added, removed, and modified nodes/edges:

.. code-block:: python

   diff_data = g_old.diff(g_new)
   print(diff_data["added_nodes"])

**Visual Diff**

Create a special "diff graph" where changes are tagged and colored (added=green, removed=red, modified=orange):

.. code-block:: python

   dg = g_old.diff_graph(g_new)
   print(dg.render(create_topology_mermaid_mmd))

Cycle Resolution
----------------

If your graph contains cycles (which prevents it from being a DAG), ``graphable`` can suggest which edges to remove to restore its integrity.

.. code-block:: python

   # Returns a list of (source, target) tuples to remove
   suggested_breaks = graph.suggest_cycle_breaks()

Cycle Detection
---------------

When building a graph, especially when relationships are defined dynamically or based on user input, it's important to avoid circular dependencies. ``graphable`` provides a mechanism to check for cycles whenever you add a relationship.

You can enable cycle detection by passing ``check_cycles=True`` to any of the dependency management methods on a ``Graphable`` node:

.. code-block:: python

   from graphable.graphable import Graphable
   from graphable.errors import GraphCycleError

   a = Graphable("A")
   b = Graphable("B")
   c = Graphable("C")

   a.add_dependency(b)
   b.add_dependency(c)

   try:
       # This would create a cycle: C -> B -> A -> C
       c.add_dependency(a, check_cycles=True)
   except GraphCycleError as e:
       print(f"Cycle detected! Path: {[n.reference for n in e.cycle]}")

This check is performed using a Breadth-First Search (BFS) to find if a path already exists in the direction that would complete a loop.

The following methods support the ``check_cycles`` parameter:

*   ``add_dependency(dependency, check_cycles=False, **attributes)``
*   ``add_dependencies(dependencies, check_cycles=False, **attributes)``
*   ``add_dependent(dependent, check_cycles=False, **attributes)``
*   ``add_dependents(dependents, check_cycles=False, **attributes)``
*   ``requires(dependency, check_cycles=False)``
*   ``provides_to(dependent, check_cycles=False)``

In addition, the ``Graph.add_edge`` and ``Graph.add_node`` methods always perform cycle detection to ensure the integrity of the graph.

Transitive Reduction
--------------------

For complex graphs, redundant edges can clutter the visualization. Transitive reduction removes these edges while preserving the reachability of the graph.

.. code-block:: python

   # Returns a new Graph instance with redundant edges removed
   reduced_g = graph.transitive_reduction()

   # Or render directly using the convenience method
   from graphable.views.mermaid import create_topology_mermaid_mmd
   print(graph.render(create_topology_mermaid_mmd, transitive_reduction=True))

Clustering by Tags
------------------

You can group nodes into clusters in visualizations like Mermaid, Graphviz, D2, and PlantUML based on their tags.

.. code-block:: python

   from graphable.views.mermaid import MermaidStylingConfig, create_topology_mermaid_mmd

   # Enable clustering in the configuration
   config = MermaidStylingConfig(cluster_by_tag=True)

   # Render the graph with clusters
   print(graph.render(create_topology_mermaid_mmd, config=config))

Nodes are grouped by their first tag (by default, tags are sorted alphabetically). You can provide a custom ``tag_sort_fnc`` in the configuration to control which tag is used for grouping.

Parsing Graphs
--------------

``graphable`` can reconstruct graphs from all major export formats. This is useful for terminal-based tools or for persisting graph structures between sessions.

.. code-block:: python

   from graphable.graph import Graph

   # Load from JSON file
   g_json = Graph.from_json("topology.json")

   # Load from YAML string
   yaml_content = "nodes: [{id: A}, {id: B}], edges: [{source: A, target: B}]"
   g_yaml = Graph.from_yaml(yaml_content)

   # Load from CSV edge list
   g_csv = Graph.from_csv("edges.csv")

The following static methods are available on the ``Graph`` class:

*   ``from_json(source, reference_type=str)``
*   ``from_yaml(source, reference_type=str)``
*   ``from_toml(source, reference_type=str)``
*   ``from_csv(source, reference_type=str)``
*   ``from_graphml(source, reference_type=str)``

Equality Comparison
-------------------

Graphs can be compared for equality using the standard ``==`` operator or the ``is_equal_to()`` method. Two graphs are considered equal if they have:
1. The same number of nodes.
2. Nodes with matching references, tags, durations, and statuses.
3. The same directed edges with matching attributes.

.. code-block:: python

   g1 = Graph.from_json("graph.json")
   g2 = Graph.from_yaml("graph.yaml")

   if g1 == g2:
       print("The graphs are identical.")

Subgraph Semantics & Syncing
----------------------------

A ``Graph`` instance acts as a "view" of a specific set of nodes. Even if a node in the graph is connected to "external" nodes that are not members of the graph, operations like topological sorts and checksums will only respect and include nodes that are explicitly part of the ``Graph`` instance.

**Filtering Behavior**

*   **Topological Order**: Methods like ``topological_order()`` and ``parallelized_topological_order()`` will filter out any nodes not present in the graph's membership.
*   **Checksums**: The ``checksum()`` method only accounts for nodes in the graph and edges between those specific nodes.

**Syncing with Discover**

If you want to expand a ``Graph`` to include all reachable ancestors and descendants of its current nodes, you can use the ``discover()`` method. This effectively "syncs" the graph with the full connected structure of its members.

.. code-block:: python

   # G only contains node 'A' initially
   g = Graph({a})

   # A depends on B, B depends on C
   # After discover(), G will contain A, B, and C
   g.discover()

Node Ordering
-------------

``Graphable`` nodes support rich comparison operators based on their reachability in the graph:
- ``a < b``: ``a`` is a proper ancestor of ``b``.
- ``a <= b``: ``a`` is an ancestor of or identical to ``b``.
- ``a > b``: ``a`` is a proper descendant of ``b``.
- ``a >= b``: ``a`` is a descendant of or identical to ``b``.

This provides a clean way to check for dependency relationships directly between node objects.

.. code-block:: python

   if node_a < node_b:
       print("node_a must come before node_b")

Caching & Performance
---------------------

The ``Graph`` class implements an efficient observer-based caching system for expensive operations:
*   ``topological_order()``
*   ``parallelized_topological_order()``
*   ``checksum()``

Calculations are performed once and cached. If any node in the graph is modified (tags changed, duration/status updated, dependencies added/removed), the graph is automatically notified and invalidates its cache. This ensures high performance for repeated access while maintaining absolute correctness.

Unified I/O
-----------

``graphable`` provides high-level ``read()`` and ``write()`` methods that automatically detect the file format based on the extension. This is the simplest way to work with graph files.

.. code-block:: python

   # Reading
   g = Graph.read("topology.json")

   # Writing (supports all formats including graphical)
   g.write("topology.svg")
   g.write("topology.yaml")

   # Supports transitive reduction during write
   g.write("simple.mmd", transitive_reduction=True)

Integrity & Checksums
---------------------

To ensure your graph structure and metadata (tags, duration, status, edge attributes) haven't changed, you can use the deterministic BLAKE2b checksum feature.

.. code-block:: python

   # Calculate hex digest
   digest = g.checksum()

   # Validate later
   if g.validate_checksum(digest):
       print("Integrity verified!")

The checksum is stable across different Python sessions and is independent of node creation order.

Parallel Processing
-------------------

For task orchestration, you often need to know which nodes can be processed simultaneously. The ``parallelized_topological_order()`` method groups nodes into independent "layers."

.. code-block:: python

   for i, layer in enumerate(g.parallelized_topological_order()):
       print(f"Layer {i} (can run in parallel): {[n.reference for n in layer]}")

Like the standard topological sort, this also supports ``_filtered`` and ``_tagged`` variants.

Command Line Interface
----------------------

``graphable`` includes a command-line tool for managing graph files without writing Python code. It is available as the ``graphable`` command after installation.

**Installation**

To get the full experience with formatted tables and panels, install the ``cli`` extra:

.. code-block:: bash

   pipx install "graphable[cli]"

**Subcommands**

*   **``info <file>``**: Displays summary statistics about the graph.
*   **``check <file>``**: Performs validation (cycles and consistency).
*   **``convert <input> <output>``**: Converts between formats.
*   **``reduce <input> <output>``**: Computes transitive reduction.
*   **``diff <file1> <file2> [-o output]``**: Compares two graphs.
*   **``serve <file> [-p port]``**: Starts a live-reloading interactive visualization.
*   **``checksum <file>``**: Prints the graph checksum.
*   **``verify <file> [--expected hash]``**: Verifies integrity.

**CI/CD and Automation**

If you are using ``graphable`` in a script or CI/CD pipeline and want to ensure plain-text output regardless of installed dependencies, use the ``--bare`` flag before the subcommand:

.. code-block:: bash

   graphable --bare info topology.json

**Supported Extensions**

- **Input**: ``.json``, ``.yaml``, ``.yml``, ``.toml``, ``.csv``, ``.graphml``
- **Output**: All input formats plus ``.dot``, ``.gv``, ``.mmd``, ``.d2``, ``.puml``, ``.html``, ``.tex``, ``.txt``, ``.ascii``, ``.svg``

Live Visualization
------------------

The ``serve`` command provides a "Live Preview" experience. It starts a local web server and automatically reloads the visualization in your browser whenever you save changes to the input graph file.

.. code-block:: bash

   graphable serve architecture.json --port 8080

This is perfect for architecting and debugging complex dependency systems in real-time.

ASCII Flowchart
---------------

For a quick, boxed representation of the graph that handles multiple parents better than a standard tree, use the ``asciiflow`` view:

.. code-block:: python

   from graphable.views.asciiflow import create_topology_ascii_flow

   print(create_topology_ascii_flow(g))

This is ideal for terminal-based tools or quick debugging where you need to see the full directed structure without leaving the command line.

Scientific Publishing (TikZ)
----------------------------

If you are writing a LaTeX paper or report, you can export your graph directly to TikZ code:

.. code-block:: python

   from graphable.views.tikz import create_topology_tikz, TikzStylingConfig

   # Generates a \begin{tikzpicture} block
   tikz_code = create_topology_tikz(g)

It supports the modern TikZ ``graphs`` library by default, ensuring high-quality vector output that matches your document's font and style perfectly.

Data Export & Interoperability
------------------------------

``graphable`` makes it easy to move your graph data into other tools for analysis or custom visualization.

**JSON, YAML & TOML**

Export to standard machine-readable formats:

.. code-block:: python

   from graphable.views.json import create_topology_json
   from graphable.views.yaml import create_topology_yaml
   from graphable.views.toml import create_topology_toml

   json_data = create_topology_json(g)
   yaml_data = create_topology_yaml(g)
   toml_data = create_topology_toml(g)

**Cytoscape**

Generate a standalone, interactive HTML file that you can share with anyone. It uses Cytoscape.js for rendering and supports zooming, panning, and dragging:

.. code-block:: python

   from graphable.views.html import export_topology_html

   export_topology_html(g, "interactive_graph.html")

You can view a live demonstration here: :raw-html:`<a href="_static/examples/topology_interactive.html" target="_blank">topology_interactive.html</a>`

**GraphML**

For professional graph analysis in tools like Gephi or yEd, export your graph to the GraphML XML standard:

.. code-block:: python

   from graphable.views.graphml import export_topology_graphml

   export_topology_graphml(g, "graph_data.graphml")

**CSV Edge List**

For processing in Excel, Pandas, or other data tools:

.. code-block:: python

   from graphable.views.csv import create_topology_csv

   # Generates "source,target" rows
   csv_data = create_topology_csv(g)

NetworkX Integration
--------------------

For users who need advanced graph analysis capabilities, ``graphable`` provides seamless integration with the `NetworkX <https://networkx.org/>`_ library.

If you have ``networkx`` installed, you can convert any ``graphable.Graph`` to a ``networkx.DiGraph`` using the ``to_networkx()`` method:

.. code-block:: python

   import networkx as nx
   from graphable.graph import Graph
   from graphable.graphable import Graphable

   g = Graph()
   # ... build your graph ...

   # Convert to NetworkX
   dg = g.to_networkx()

   # Use any NetworkX algorithm
   longest_path = nx.dag_longest_path(dg)
   print(f"Longest path: {longest_path}")

The conversion preserves node references and tags as node attributes, allowing you to access your original data within NetworkX algorithms.
