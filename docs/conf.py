import os
import sys
import tomllib
from datetime import datetime
from pathlib import Path

# Add the src directory to the path so sphinx can find the code
sys.path.insert(0, os.path.abspath("../src"))

# Get version information from pyproject.toml
with open(Path(__file__).parent.parent / "pyproject.toml", "rb") as f:
    pyproject = tomllib.load(f)

project = pyproject["project"]["name"]
copyright = f"{datetime.now().year}, Richard West"
author = "Richard West"
release = pyproject["project"]["version"]
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_theme_options = {
    "source_repository": "https://github.com/TheTrueSCU/graphable/",
    "source_branch": "main",
    "source_directory": "docs/",
}
html_static_path = ["_static"]

html_extra_path = ["_extra"]

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_class_signature = "separated"

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True

# Custom roles
rst_prolog = """
.. role:: raw-html(raw)
   :format: html
"""
