# Implementation Plan - Documentation Update and Coverage Improvement

This plan outlines the steps to improve code coverage to >95% and perform a comprehensive documentation update for the `graphable` project.

## Phase 1: Coverage Improvement (CLI & Parsers)
Focus on the modules with the lowest coverage to reach the 95% threshold.

- [x] Task: Improve coverage for `src/graphable/cli/rich_cli.py` (Current: 28%) (89d9e36)
    - [x] Write tests for terminal UI formatting and Rich-specific output logic in `tests/unit/cli/test_rich_cli.py`
    - [x] Implement missing logic/fixes to ensure tests pass
- [x] Task: Improve coverage for `src/graphable/cli/commands/serve.py` (Current: 40%) (89d9e36)
    - [x] Write tests for the live-reload server and Starlette/Uvicorn integration in `tests/unit/cli/test_commands.py`
    - [x] Implement missing logic/fixes to ensure tests pass
- [x] Task: Improve coverage for `src/graphable/cli/bare_cli.py` (Current: 56%) (89d9e36)
    - [x] Write tests for basic CLI entry points and argument parsing in `tests/unit/cli/test_bare_cli.py`
    - [x] Implement missing logic/fixes to ensure tests pass
- [x] Task: Improve coverage for Parsers (`graphml.py`, `toml.py`, `utils.py`, `yaml.py`) (89d9e36)
    - [x] Write tests for edge cases and error handling in parser modules
    - [x] Implement missing logic/fixes to ensure tests pass
- [x] Task: Conductor - User Manual Verification 'Phase 1: Coverage Improvement (CLI & Parsers)' (Protocol in workflow.md)

## Phase 2: Coverage Improvement (Core & Views)
Refine coverage for the core library and visualization utilities.

- [x] Task: Improve coverage for `src/graphable/graph.py` and `src/graphable/graphable.py` (89d9e36)
    - [x] Write tests for missing branches in graph algorithms and the main `Graphable` interface
    - [x] Implement missing logic/fixes to ensure tests pass
- [x] Task: Improve coverage for `src/graphable/views/utils.py` and other views (89d9e36)
    - [x] Write tests for visualization utility functions and any view-specific gaps (e.g., TOML, YAML views)
    - [x] Implement missing logic/fixes to ensure tests pass
- [x] Task: Conductor - User Manual Verification 'Phase 2: Coverage Improvement (Core & Views)' (Protocol in workflow.md)

## Phase 3: Documentation Audit and Update
Update docstrings and Sphinx-based documentation.

- [x] Task: Audit and update API docstrings (89d9e36)
    - [x] Review all public classes and methods in `src/graphable/`
    - [x] Ensure Google-style docstrings are complete and accurate
- [x] Task: Update Sphinx documentation and User Guides (2d957c8)
    - [x] Update `docs/api.rst`, `docs/usage.rst`, and `docs/index.rst`
    - [x] Update `README.md` and `USAGE.md` with latest feature details (Cytoscape, Serve)
- [x] Task: Review internal Conductor documentation (2d957c8)
    - [x] Ensure `conductor/` files are up-to-date and clear for future development
- [x] Task: Conductor - User Manual Verification 'Phase 3: Documentation Audit and Update' (Protocol in workflow.md)

## Phase 4: Examples Expansion and Final Verification
Add advanced examples and perform a final quality check.

- [x] Task: Update and expand `examples/` directory (2d957c8)
    - [x] Audit `examples/basic_usage.py`
    - [x] Create `examples/advanced_usage.py` showing complex DAGs and multiple exports
    - [x] Create `examples/parser_examples.py` showing different input formats
- [x] Task: Final Quality Gate Verification (2d957c8)
    - [x] Run `just check` to verify linting, type safety, and 95% coverage
    - [x] Build Sphinx docs (`cd docs && make html`) and verify output
- [x] Task: Conductor - User Manual Verification 'Phase 4: Examples Expansion and Final Verification' (Protocol in workflow.md)

## Phase: Review Fixes
- [x] Task: Refactor all imports to 'from x import y' and consolidate coverage tests (89d9e36)
