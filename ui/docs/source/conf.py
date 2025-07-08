# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'SCOOTER'
copyright = '2025, Dren Fazlija'
author = 'Dren Fazlija'
release = '0.1'

# Add the project directory to the path so autodoc can find the modules
import os
import sys
# Point directly to the directory containing the Python files
# (not using package/module structure)
sys.path.insert(0, os.path.abspath('..'))

# Extensions
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
]

# Theme
html_theme = 'sphinx_rtd_theme'
