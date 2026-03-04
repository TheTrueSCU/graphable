# Product Guidelines

## Voice and Tone
- **Technical & Precise:** The documentation and CLI output should prioritize accuracy and clarity. Use standard graph theory terminology (nodes, edges, DAG, topological sort) consistently.
- **Direct & Helpful:** Communication should be straightforward, providing clear instructions and explanations for technical concepts.

## Visual Identity
- **Clarity & Readability:** All graph visualizations (Mermaid, Graphviz, D2, etc.) must prioritize the legibility of node labels and the directionality of edges. Avoid unnecessary aesthetic flourishes that obscure the graph's structure.
- **Structural Integrity:** Visualizations should accurately reflect the underlying graph model, especially concerning hierarchy and connectivity.

## User Experience & CLI Design
- **Actionable Feedback:** Error messages must be descriptive and, where possible, suggest a remedy (e.g., identifying the nodes involved in a detected cycle).
- **Transparency:** The CLI should provide clear status updates during long-running operations (like CPM analysis on very large graphs) and offer detailed debug logs when requested.
- **Convention over Configuration:** Provide sensible defaults for all CLI commands while allowing advanced users to override them via flags or configuration files.
