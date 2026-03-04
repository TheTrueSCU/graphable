Parser Examples
===============

The following script shows how to load graphs from various machine-readable formats including JSON, YAML, and CSV.

This script (available as ``examples/parser_examples.py``) shows how to:
- Load graphs from JSON files and strings.
- Load graphs from YAML.
- Load graphs from CSV edge lists.

Command
-------

.. code-block:: bash

   uv run examples/parser_examples.py > docs/_static/examples/parser_examples_output.txt

Script
------

.. literalinclude:: ../examples/parser_examples.py
   :language: python
   :linenos:
   :caption: examples/parser_examples.py

Output
------

Running the script produces the following text output:

.. literalinclude:: _static/examples/parser_examples_output.txt
   :language: text
   :caption: Execution Output
