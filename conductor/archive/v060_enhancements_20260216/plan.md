# Implementation Plan - v0.6.0 Feature Enhancements

Expose graph analysis capabilities to the CLI and enhance interactive HTML visualizations.

## Phase 1: Core CLI Enhancements
Focus on adding slicing and path-finding to the CLI.

- [x] Task: Implement `--upstream-of` and `--downstream-of` logic in `src/graphable/cli/commands/core.py` (e029971)
- [x] Task: Update `rich_cli.py` and `bare_cli.py` to support the new slicing flags. (e029971)
- [x] Task: Implement the `paths` subcommand in `core.py` and register it in the CLIs. (e029971)
- [x] Task: Add unit tests for new CLI flags and commands in `tests/unit/cli/`. (e029971)

## Phase 2: Interactive HTML UI
Enhance the HTML visualization template.

- [x] Task: Refactor `src/graphable/views/html.py` to include a search bar in the template. (e029971)
- [x] Task: Implement metadata sidebar logic in JavaScript within the HTML template. (e029971)
- [x] Task: Update `test_html.py` to verify the new template structure. (e029971)

## Phase 3: Documentation and Final Polish
Synchronize documentation with the new features.

- [x] Task: Update `USAGE.md` and `README.md` with the new CLI commands and flags. (e029971)
- [x] Task: Update Sphinx documentation (`docs/usage.rst`) to include details about slicing and the enhanced UI. (e029971)
- [x] Task: Final Quality Gate Verification with `just check`. (e029971)
