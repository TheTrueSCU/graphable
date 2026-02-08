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
*   ``node_attr_fnc``: A function that takes a ``Graphable`` and returns a dictionary of attributes for that specific node.
*   ``edge_attr_fnc``: A function that takes two ``Graphable`` nodes (source and target) and returns attributes for the edge between them.
*   ``node_label_fnc``: Customize how labels are generated for each node.
