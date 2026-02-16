# Specification - v0.6.0 Feature Enhancements

This track focuses on exposing advanced graph analysis features to the CLI and improving the interactivity of the standalone HTML export.

## 1. CLI Graph Slicing
Add capability to the CLI to filter graphs by reachability.

### Requirements
- Add `--upstream-of <node_ref>` and `--downstream-of <node_ref>` flags to `render`, `convert`, and `info` commands.
- These flags should be mutually exclusive with each other and with the existing `--tag` flag if possible (or applied sequentially).
- Use existing `upstream_of` and `downstream_of` methods from the `Graph` class.

## 2. CLI `paths` Command
Add a new subcommand to find paths between nodes.

### Requirements
- Subcommand: `paths <file> <source> <target>`
- Output: List all simple paths from `source` to `target`.
- Support `--bare` for automated parsing.

## 3. Enhanced Interactive HTML
Improve the `html` view with basic UI controls.

### Requirements
- **Search Bar**: Add a text input to the HTML template that highlights nodes matching the query using Cytoscape.js.
- **Metadata Sidebar**: Implement a side panel that displays detailed node information (tags, duration, status) when a node is clicked.
- **Pure Frontend**: Implementation should be entirely within the generated HTML/JS (no backend required for interaction).
