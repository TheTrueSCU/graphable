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
