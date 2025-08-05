# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
from pathlib import Path

sys.path.insert(0, str("/home/genta/git/chnobli-test"))

# import mock
 
# MOCK_MODULES = ['json', "os", "argparse", "pytest"]
# for mod_name in MOCK_MODULES:
# sys.modules[mod_name] = mock.Mock()

project = 'chnobli-test'
copyright = '2025, Gentiana Rashiti'
author = 'Gentiana Rashiti'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest',
              'sphinx.ext.intersphinx', 'sphinx.ext.todo',
              'sphinx.ext.ifconfig', 'sphinx.ext.viewcode',
              'sphinx.ext.inheritance_diagram',
              'sphinx.ext.autosummary']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

autoclass_content = 'both'
# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'
# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
