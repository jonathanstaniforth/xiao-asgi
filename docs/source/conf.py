# Configuration file for the Sphinx documentation builder.

# -- Path setup --------------------------------------------------------------

import os
import sys

#sys.path.insert(0, os.path.abspath('../../xiao_asgi'))


# -- Project information -----------------------------------------------------

project = 'xiao asgi'
copyright = '2021, Jonathan Staniforth'
author = 'Jonathan Staniforth'
release = '0.1.0'


# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinxcontrib.napoleon'
]

templates_path = []

exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

html_theme = 'alabaster'

html_static_path = []


# -- Napoleon settings -------------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None