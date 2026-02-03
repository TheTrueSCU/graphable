import os
import sys
from datetime import datetime

# Add the src directory to the path so sphinx can find the code
sys.path.insert(0, os.path.abspath("../src"))

project = "graphable"
copyright = f"{datetime.now().year}, Richard West"
author = "Richard West"
release = "0.1.0"

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
