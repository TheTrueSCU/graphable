# Gemini Instructions
- Always execute `just test` instead of `pytest` for running tests. Any arguments you specify will be passed through to the wrapped `pytest` command. For example, you may wish to pass `-n 0 -p no:sugar` to disable the xdist and sugar plugins.
- Always execute `just coverage` instead of `pytest` for coverage.
- When adding, removing, or modifying code, adhere to the code ordering guidelines in @./.gemini/code-ordering.md.
- Always execute `just lint` after finishing code changes and address any issues flagged.
- Do not use `pip` or `venv` directly; use `uv` for all environment management.
- Do not stage or commit any changes
