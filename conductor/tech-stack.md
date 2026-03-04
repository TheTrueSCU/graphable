# Technology Stack

## Core
- **Language:** Python 3.13+
- **Dependency Management:** [uv](https://github.com/astral-sh/uv)
- **Task Runner:** [just](https://github.com/casey/just)

## CLI & Web
- **CLI Framework:** [typer](https://typer.tiangolo.com/)
- **Terminal UI & Output:** [rich](https://github.com/Textualize/rich) for formatting and external CLI integration for image rendering (Mermaid, Graphviz, D2, PlantUML).
- **Web Server (Serve Command):** [starlette](https://www.starlette.io/) / [uvicorn](https://www.uvicorn.org/)

## Testing & Quality
- **Test Runner:** [pytest](https://docs.pytest.org/)
- **Linting & Formatting:** [ruff](https://github.com/astral-sh/ruff)
- **Type Checking:** [mypy](http://mypy-lang.org/) (implied by `py.typed` and ruff config)

## Documentation
- **Documentation Generator:** [sphinx](https://www.sphinx-doc.org/)
- **Theme:** [furo](https://github.com/pradyunshl/furo)
