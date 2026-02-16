# Specification: Cytoscape.js Export

## Overview
Implement a new exporter and view for Cytoscape.js JSON format. This will allow `graphable` to produce data that can be consumed by the Cytoscape.js library for high-performance, interactive web visualizations.

## Requirements
- Create a `CytoscapeStylingConfig` dataclass in `src/graphable/views/cytoscape.py`.
- Implement `create_topology_cytoscape(graph, config)` which returns a JSON string in Cytoscape.js "elements" format.
- Implement `export_topology_cytoscape(graph, output, config)` which writes the JSON to a file.
- Register the new view for the `.cy.json` extension.
- Ensure all node and edge attributes are correctly mapped to the Cytoscape `data` object.

## Technical Details
- Format: A list of objects, each containing a `data` key.
- Nodes should have `id`, `label`, and any tags.
- Edges should have `id`, `source`, and `target`.
- Support custom data mapping via configuration.
