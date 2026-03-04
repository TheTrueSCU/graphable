Advanced Usage Example
======================

The following script demonstrates complex directed acyclic graphs (DAGs), multiple export formats, and the use of the ``render`` method for high-level visualization orchestration.

This script (available as ``examples/advanced_usage.py``) shows how to:
- Build a more complex graph structure.
- Export to multiple formats (Mermaid, Graphviz, D2, PlantUML).
- Use high-level orchestration for visualization.

Command
-------

.. code-block:: bash

   uv run examples/advanced_usage.py --output-dir docs/_static/examples > docs/_static/examples/advanced_usage_output.txt

Script
------

.. literalinclude:: ../examples/advanced_usage.py
   :language: python
   :linenos:
   :caption: examples/advanced_usage.py

Output
------

Running the script produces the following text output:

.. literalinclude:: _static/examples/advanced_usage_output.txt
   :language: text
   :caption: Execution Output
