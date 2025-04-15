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
MODULES = str(PROJECT_ROOT / 'logseq_analyzer')

# -- Project information -----------------------------------------------------
project = 'Logseq Analyzer'
author = 'Wonyoung Jang'
copyright = '2025, Wonyoung Jang'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.apidoc',        # Generate API documentation from docstrings
    'sphinx.ext.autodoc',       # Core extension for API doc generation from docstrings
    'sphinx.ext.autosummary',   # Generate summary tables for modules/classes
    'sphinx.ext.viewcode',      # Add links to highlighted source code
    'sphinx.ext.napoleon',      # Support for NumPy and Google style docstrings
]

# Apidoc settings
apidoc_modules = [
    {
        'path': MODULES,
        'destination': '.',
        'exclude_patterns': [f'{MODULES}/**/tests/*'],
        'max_depth': 4,
        'follow_links': True,
        'separate_modules': True,
        'include_private': True,
        'no_headings': False,
        'module_first': True,
        'implicit_namespaces': False,
        'automodule_options': {
            'members', 'show-inheritance', 'undoc-members'
        },
    },
]

# Autodoc settings
autodoc_default_options = {
    'members': True,                # Document all members
    'undoc-members': True,          # Document members without docstrings
    'show-inheritance': True,       # Show base classes
    'member-order': 'bysource',     # Order members by source order
}
autodoc_mock_imports = [
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtWidgets',
    'PySide6.QtGui',
]


# Napoleon settings (for Google/NumPy style docstrings)
napoleon_google_docstring = True        # Enable Google style docstrings
napoleon_numpy_docstring = True         # Enable NumPy style docstrings
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False

# Document Python Code
master_doc = 'modules' # The main page
exclude_patterns = [
    '_build', 
    'Thumbs.db',
    '.DS_Store',
]
templates_path = ['_templates']

# -- Options for HTML output -------------------------------------------------
html_theme = 'furo'  # Use Read the Docs theme
html_static_path = ['_static']  # Path to static files


# -- Options for Python Domain -----------------------------------------------
add_module_names = False


