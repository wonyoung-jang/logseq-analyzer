# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from pathlib import Path
import sys

sys.path.insert(0, str(Path("../..").resolve()))  # Adjust if needed
HERE = Path(__file__).parent.parent
PROJECT_ROOT = HERE.parent
MODULES = str(PROJECT_ROOT / "logseq_analyzer")

# -- Project information -----------------------------------------------------
project = "Logseq Analyzer"
author = "Wonyoung Jang"
copyright = "2025, Wonyoung Jang"
release = "0.0.1"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.apidoc",  # Generate API documentation from docstrings
    "sphinx.ext.viewcode",  # Add links to highlighted source code
    "sphinx.ext.napoleon",  # Support for NumPy and Google style docstrings
]

# Apidoc settings
apidoc_modules = [
    {
        "path": MODULES,
        "destination": "./api",
        "exclude_patterns": [f"{MODULES}/**/tests/*"],
        "max_depth": 4,
        "follow_links": False,
        "separate_modules": True,
        "include_private": False,
        "no_headings": False,
        "module_first": False,
        "implicit_namespaces": False,
        "automodule_options": {"members", "show-inheritance", "undoc-members"},
    },
]

# Autodoc settings
autodoc_mock_imports = [
    "PySide6",
    "PySide6.QtCore",
    "PySide6.QtWidgets",
    "PySide6.QtGui",
]


# Napoleon settings (for Google/NumPy style docstrings)
napoleon_google_docstring = True  # Enable Google style docstrings
napoleon_numpy_docstring = True  # Enable NumPy style docstrings
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# Document Python Code
root_doc = "index"
templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"  # Use Read the Docs theme
html_static_path = ["_static"]  # Path to static files


# -- Options for Python Domain -----------------------------------------------
add_module_names = False
