# Implementation Plan - Documentation Update and Coverage Improvement

This plan outlines the steps to improve code coverage to >95% and perform a comprehensive documentation update for the `graphable` project.

## Phase 1: Coverage Improvement (CLI & Parsers)
Focus on the modules with the lowest coverage to reach the 95% threshold.

- [~] Task: Improve coverage for `src/graphable/cli/rich_cli.py` (Current: 28%)
    - [ ] Write tests for terminal UI formatting and Rich-specific output logic in `tests/unit/cli/test_rich_cli.py`
    - [ ] Implement missing logic/fixes to ensure tests pass
- [ ] Task: Improve coverage for `src/graphable/cli/commands/serve.py` (Current: 40%)
    - [ ] Write tests for the live-reload server and Starlette/Uvicorn integration in `tests/unit/cli/test_commands.py`
    - [ ] Implement missing logic/fixes to ensure tests pass
- [ ] Task: Improve coverage for `src/graphable/cli/bare_cli.py` (Current: 56%)
    - [ ] Write tests for basic CLI entry points and argument parsing in `tests/unit/cli/test_bare_cli.py`
    - [ ] Implement missing logic/fixes to ensure tests pass
- [ ] Task: Improve coverage for Parsers (`graphml.py`, `toml.py`, `utils.py`, `yaml.py`)
    - [ ] Write tests for edge cases and error handling in parser modules
    - [ ] Implement missing logic/fixes to ensure tests pass
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Coverage Improvement (CLI & Parsers)' (Protocol in workflow.md)

## Phase 2: Coverage Improvement (Core & Views)
Refine coverage for the core library and visualization utilities.

- [ ] Task: Improve coverage for `src/graphable/graph.py` and `src/graphable/graphable.py`
    - [ ] Write tests for missing branches in graph algorithms and the main `Graphable` interface
    - [ ] Implement missing logic/fixes to ensure tests pass
- [ ] Task: Improve coverage for `src/graphable/views/utils.py` and other views
    - [ ] Write tests for visualization utility functions and any view-specific gaps (e.g., TOML, YAML views)
    - [ ] Implement missing logic/fixes to ensure tests pass
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Coverage Improvement (Core & Views)' (Protocol in workflow.md)

## Phase 3: Documentation Audit and Update
Update docstrings and Sphinx-based documentation.

- [ ] Task: Audit and update API docstrings
    - [ ] Review all public classes and methods in `src/graphable/`
    - [ ] Ensure Google-style docstrings are complete and accurate
- [ ] Task: Update Sphinx documentation and User Guides
    - [ ] Update `docs/api.rst`, `docs/usage.rst`, and `docs/index.rst`
    - [ ] Update `README.md` and `USAGE.md` with latest feature details (Cytoscape, Serve)
- [ ] Task: Review internal Conductor documentation
    - [ ] Ensure `conductor/` files are up-to-date and clear for future development
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Documentation Audit and Update' (Protocol in workflow.md)

## Phase 4: Examples Expansion and Final Verification
Add advanced examples and perform a final quality check.

- [ ] Task: Update and expand `examples/` directory
    - [ ] Audit `examples/basic_usage.py`
    - [ ] Create `examples/advanced_usage.py` showing complex DAGs and multiple exports
    - [ ] Create `examples/parser_examples.py` showing different input formats
- [ ] Task: Final Quality Gate Verification
    - [ ] Run `just check` to verify linting, type safety, and 95% coverage
    - [ ] Build Sphinx docs (`cd docs && make html`) and verify output
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Examples Expansion and Final Verification' (Protocol in workflow.md)
