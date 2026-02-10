set dotenv-load

GIT_BRANCH:=`git branch --show-current`
GIT_COMMIT:=`git rev-parse HEAD`

@_:
    just --list

_browser *args:
    @uv run -m webbrowser -t {{ args }}

_cleandir name:
    @rm -rf {{ name }}

_cleanfiles type:
    @find . -type f -name "*.{{ type }}" -delete

[group('env')]
@clean:
    just _cleandir build
    just _cleandir __pycache__
    just _cleandir .coverage
    just _cleandir .pytest_cache
    just _cleandir .ruff_cache
    just _cleandir htmlcov
    just _cleandir htmlrep
    just _cleandir _minted
    just _cleandir svg-inkscape
    just _cleandir docs/_build
    just _cleandir docs/_extra

[group('docs')]
docs-examples:
    mkdir -p docs/_static/examples
    uv run examples/basic_usage.py --d2-svg --graphviz-svg --interactive-html --mermaid-svg --output-dir docs/_static/examples --puml-svg > docs/_static/examples/basic_usage_output.txt

[group('docs')]
docs: docs-examples
    #!/usr/bin/env bash
    mkdir -p docs/_extra
    if [ -d "htmlcov" ]; then
        echo "Including coverage report..."
        rm -rf docs/_extra/coverage
        cp -r htmlcov docs/_extra/coverage
    fi
    if [ -d "htmlrep" ]; then
        echo "Including test report..."
        rm -rf docs/_extra/tests
        cp -r htmlrep docs/_extra/tests
    fi
    uv run sphinx-build -b html docs docs/_build/html

[group('docs')]
docs-view mode="local":
    #!/usr/bin/env bash
    if [ "{{mode}}" == "served" ]; then
        echo "Please ensure 'just docs-serve' is running in another terminal."
        just _browser http://localhost:8000
    else
        just docs
        just _browser docs/_build/html/index.html
    fi

[group('docs')]
docs-serve: docs
    echo "Serving documentation at http://localhost:8000 (Ctrl+C to stop)"
    uv run uvicorn docs.server:app --port 8000 --host 127.0.0.1 --log-level info


[group('env')]
fresh: nuke install

[group('env')]
install:
    uv sync

[group('env')]
nuke: clean
    just _cleandir .venv

[group('env')]
update:
    uv sync --upgrade

[group('qa')]
check: lint typing coverage

[group('qa')]
@coverage *args:
    just test --cov=. --cov-fail-under=95 --cov-report html --cov-report term-missing:skip-covered {{ args }}

[group('qa')]
[group('view')]
covrep:
    just _browser htmlcov/index.html

[group('qa')]
[group('view')]
testrep:
    just _browser htmlrep/report.html

[group('qa')]
lint:
    uv run isort .
    uv run ruff format
    uv run ruff check --fix

[group('qa')]
@test *args:
    uv run -m pytest --git-branch {{ GIT_BRANCH }} --git-commit {{ GIT_COMMIT }} --html-output htmlrep -n auto --should-open-report never {{ args }}

[group('qa')]
typing:
    uv run ty check

[group('run')]
@run *args:
    uv run cli/main.py {{ args }}

demo:
    uv run examples/basic_usage.py --mermaid-svg --graphviz-svg --d2-svg --puml-svg --output-dir examples_output

