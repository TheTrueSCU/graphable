# Implementation Plan: PNG Export and Unified Rendering CLI

## Phase 1: Core Logic and Engine Unification
- [ ] Task: Implement `render_command` core logic in `src/graphable/cli/commands/core.py`
    - [ ] Write Tests: Verify logic for engine selection and output format detection
    - [ ] Implement Feature: Command that dispatches to the correct visualization module
- [ ] Task: Implement engine auto-detection logic in `src/graphable/views/utils.py`
    - [ ] Write Tests: Verify priority-based detection (Mermaid -> Graphviz -> D2 -> PlantUML)
    - [ ] Implement Feature: Utility to check system PATH for required executables
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Core Logic and Engine Unification' (Protocol in workflow.md)

## Phase 2: Visualization Engine Updates
- [ ] Task: Update Mermaid view for PNG support
    - [ ] Write Tests: Verify `mmdc` is called with correct flags for `.png`
    - [ ] Implement Feature: Enhance `export_topology_mermaid_svg` (or rename to a generic export function)
- [ ] Task: Update Graphviz view for PNG support
    - [ ] Write Tests: Verify `dot` is called with `-Tpng` for `.png`
    - [ ] Implement Feature: Add `export_topology_graphviz_png` and unify with SVG export
- [ ] Task: Update D2 and PlantUML views for PNG support
    - [ ] Write Tests: Verify native PNG flags are used for both
    - [ ] Implement Feature: Ensure both modules support the new rendering flow
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Visualization Engine Updates' (Protocol in workflow.md)

## Phase 3: CLI Overhaul
- [ ] Task: Add `render` command to `rich_cli.py` and `bare_cli.py`
    - [ ] Write Tests: Verify CLI arguments and flags (--engine, -e)
    - [ ] Implement Feature: UI logic for the new command
- [ ] Task: Remove image support from `convert` command
    - [ ] Write Tests: Ensure `convert` raises error for `.png` or `.svg`
    - [ ] Implement Feature: Clean up `convert_command` logic
- [ ] Task: Conductor - User Manual Verification 'Phase 3: CLI Overhaul' (Protocol in workflow.md)
