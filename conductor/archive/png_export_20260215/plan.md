# Implementation Plan: PNG Export and Unified Rendering CLI

## Phase 1: Core Logic and Engine Unification
- [x] Task: Implement `render_command` core logic in `src/graphable/cli/commands/core.py` (ecd3717)
    - [x] Write Tests: Verify logic for engine selection and output format detection
    - [x] Implement Feature: Command that dispatches to the correct visualization module
- [x] Task: Implement engine auto-detection logic in `src/graphable/views/utils.py` (ecd3717)
    - [x] Write Tests: Verify priority-based detection (Mermaid -> Graphviz -> D2 -> PlantUML)
    - [x] Implement Feature: Utility to check system PATH for required executables
- [x] Task: Conductor - User Manual Verification 'Phase 1: Core Logic and Engine Unification' (Protocol in workflow.md)

## Phase 2: Visualization Engine Updates
- [x] Task: Update Mermaid view for PNG support (f6c3a9a)
    - [x] Write Tests: Verify `mmdc` is called with correct flags for `.png`
    - [x] Implement Feature: Enhance `export_topology_mermaid_svg` (or rename to a generic export function)
- [x] Task: Update Graphviz view for PNG support (f6c3a9a)
    - [x] Write Tests: Verify `dot` is called with `-Tpng` for `.png`
    - [x] Implement Feature: Add `export_topology_graphviz_png` and unify with SVG export
- [x] Task: Update D2 and PlantUML views for PNG support (f6c3a9a)
    - [x] Write Tests: Verify native PNG flags are used for both
    - [x] Implement Feature: Ensure both modules support the new rendering flow
- [x] Task: Conductor - User Manual Verification 'Phase 2: Visualization Engine Updates' (Protocol in workflow.md)

## Phase 3: CLI Overhaul
- [x] Task: Add `render` command to `rich_cli.py` and `bare_cli.py`
    - [x] Write Tests: Verify CLI arguments and flags (--engine, -e)
    - [x] Implement Feature: UI logic for the new command
- [x] Task: Remove image support from `convert` command
    - [x] Write Tests: Ensure `convert` raises error for `.png` or `.svg`
    - [x] Implement Feature: Clean up `convert_command` logic
- [x] Task: Conductor - User Manual Verification 'Phase 3: CLI Overhaul' (Protocol in workflow.md)

## Phase: Review Fixes
- [x] Task: Apply review suggestions a67e9ff
