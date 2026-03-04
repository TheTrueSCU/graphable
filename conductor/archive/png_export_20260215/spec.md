# Specification: PNG Export and Unified Rendering CLI

## Overview
This track introduces support for exporting graphs as PNG images across all supported visualization engines (Mermaid, Graphviz, D2, and PlantUML). It also involves a CLI overhaul to introduce a dedicated `render` command, separating image generation from data format conversion.

## Functional Requirements
- **New CLI Command:** Implement `graphable render <input> <output>` for image exports.
- **Supported Formats:** Support `.png` and `.svg` output extensions.
- **Engine Selection:** Add an `--engine` (or `-e`) flag to specify the visualization engine (`mermaid`, `graphviz`, `d2`, `plantuml`).
- **Auto-Detection:** If no engine is specified, auto-detect based on system availability with priority: Mermaid -> Graphviz -> D2 -> PlantUML.
- **PNG Support:** 
    - **Mermaid:** Use `mmdc` with the `-o` flag pointing to a `.png` file.
    - **Graphviz:** Use `dot -Tpng`.
    - **D2:** Use `d2` CLI which supports PNG natively.
    - **PlantUML:** Use `plantuml -tpng`.
- **Decoupling:** Remove image-specific logic from the `convert` command to keep it focused on graph data formats (JSON, YAML, etc.).

## Non-Functional Requirements
- **Minimal Dependencies:** Rely on existing external CLI tools for image generation; do not add new Python image processing libraries.
- **Error Handling:** Provide clear error messages if a requested engine or its required CLI tool is missing.

## Acceptance Criteria
- `graphable render input.json output.png` produces a valid PNG image.
- `graphable render input.json output.png --engine graphviz` forces the use of Graphviz.
- The `convert` command no longer handles `.png` or `.svg` extensions.
- All visualization engines are covered by unit and integration tests for PNG output.

## Out of Scope
- Adding internal Python libraries for SVG-to-PNG conversion.
- Support for other image formats like JPEG or GIF.
