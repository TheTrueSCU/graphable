Usage Examples
==============

The following example demonstrates the core features of ``graphable``, including building a graph, performing topological sorts, and generating various visualizations.

Basic Usage
-----------

This script (available in the repository as ``examples/basic_usage.py``) shows how to:
- Define nodes and relationships.
- Use tags for organization and styling.
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

Visualizations
--------------

The script also generates visual representations of the graph.

Mermaid SVG
^^^^^^^^^^^

The Mermaid visualization shows the flow and relationships:

.. image:: _static/examples/topology_mermaid.svg
   :alt: Mermaid Topology Diagram
   :align: center

Graphviz SVG
^^^^^^^^^^^^

The Graphviz visualization (with custom styling) provides a different perspective:

.. image:: _static/examples/topology_graphviz.svg
   :alt: Graphviz Topology Diagram
   :align: center

D2 SVG
^^^^^^

The modern D2 visualization with automatic layout:

.. image:: _static/examples/topology_d2.svg
   :alt: D2 Topology Diagram
   :align: center

PlantUML SVG
^^^^^^^^^^^^

The enterprise-standard PlantUML visualization:

.. image:: _static/examples/topology_plantuml.svg
   :alt: PlantUML Topology Diagram
   :align: center

Graphviz Styling
^^^^^^^^^^^^^^^^

The Graphviz view supports extensive customization through the ``GraphvizStylingConfig`` class. You can customize node labels, attributes, and global graph settings.

.. code-block:: python

   from graphable.views.graphviz import GraphvizStylingConfig, create_topology_graphviz_dot

   gv_config = GraphvizStylingConfig(
       graph_attr={"rankdir": "LR", "nodesep": "0.5"},
       node_attr_default={"shape": "rounded", "style": "filled", "fontname": "Arial"},
       node_attr_fnc=lambda n: {
           "fillcolor": "lightblue" if "backend" in n.tags else "lightgreen"
       },
   )
   dot = create_topology_graphviz_dot(graph, gv_config)

Key configuration options include:

*   ``graph_attr``: Global attributes for the graph (e.g., ``rankdir``, ``label``).
*   ``node_attr_default``: Default attributes applied to all nodes.
*   ``edge_attr_default``: Default attributes applied to all edges.
*   ``node_attr_fnc``: A function that takes a ``Graphable[Any]`` and returns a dictionary of attributes for that specific node.
*   ``edge_attr_fnc``: A function that takes two ``Graphable[Any]`` nodes (source and target) and returns attributes for the edge between them.
*   ``node_label_fnc``: Customize how labels are generated for each node.

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

*   ``add_dependency(dependency, check_cycles=False)``
*   ``add_dependencies(dependencies, check_cycles=False)``
*   ``add_dependent(dependent, check_cycles=False)``
*   ``add_dependents(dependents, check_cycles=False)``
*   ``requires(dependency, check_cycles=False)``
*   ``provides_to(dependent, check_cycles=False)``

In addition, the ``Graph.add_edge`` and ``Graph.add_node`` methods always perform cycle detection to ensure the integrity of the graph.

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

**JSON & Cytoscape**

Export to a standard JSON format or a specialized Cytoscape.js-compatible schema:

.. code-block:: python

   from graphable.views.json import create_topology_json, JsonStylingConfig
   from graphable.views.cytoscape import create_topology_cytoscape, CytoscapeStylingConfig

   # Generic JSON
   # Custom indent and metadata
   json_config = JsonStylingConfig(indent=4, node_data_fnc=lambda n: {"type": "service"})
   generic_data = create_topology_json(g, config=json_config)

   # Cytoscape.js Elements format
   # Ready to be loaded into an interactive web viewer
   cy_data = create_topology_cytoscape(g)

**Interactive HTML**

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
