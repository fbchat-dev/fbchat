# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

import fbchat

# -- Project information -----------------------------------------------------

project = fbchat.__name__
copyright = fbchat.__copyright__
author = fbchat.__author__

# The short X.Y version
version = fbchat.__version__
# The full version, including alpha/beta/rc tags
release = fbchat.__version__


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
needs_sphinx = "2.0"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinxcontrib.spelling",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The master toctree document.
master_doc = "index"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

rst_prolog = ".. currentmodule:: " + project

# The reST default role (used for this markup: `text`) to use for all
# documents.
#
default_role = "any"

# Make the reference parsing more strict
#
nitpicky = True

# Prefer strict Python highlighting
#
highlight_language = "python3"

# If true, '()' will be appended to :func: etc. cross-reference text.
#
add_function_parentheses = False


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "alabaster"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    "show_powered_by": False,
    "github_user": "carpedm20",
    "github_repo": project,
    "github_banner": True,
    "show_related": False,
}

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
html_sidebars = {"**": ["sidebar.html", "searchbox.html"]}

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
#
html_show_sphinx = False

# If true, links to the reST sources are added to the pages.
#
html_show_sourcelink = False

# A shorter title for the navigation bar. Default is the same as html_title.
#
html_short_title = fbchat.__description__


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = project + "doc"


# -- Options for LaTeX output ------------------------------------------------

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [(master_doc, project + ".tex", fbchat.__title__, author, "manual")]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, project, fbchat.__title__, [x.strip() for x in author.split(";")], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        project,
        fbchat.__title__,
        author,
        project,
        fbchat.__description__,
        "Miscellaneous",
    )
]


# -- Options for Epub output -------------------------------------------------

# A list of files that should not be packed into the epub file.
epub_exclude_files = ["search.html"]


# -- Extension configuration -------------------------------------------------

# -- Options for autodoc extension ---------------------------------------

autoclass_content = "both"
autodoc_member_order = "bysource"
autodoc_default_options = {"members": True}

# -- Options for intersphinx extension ---------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {"https://docs.python.org/": None}

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

todo_link_only = True

# -- Options for napoleon extension ----------------------------------------------

# Use Google style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# napoleon_use_admonition_for_examples = False
# napoleon_use_admonition_for_notes = False
# napoleon_use_admonition_for_references = False

# -- Options for spelling extension ----------------------------------------------

spelling_word_list_filename = [
    "spelling/names.txt",
    "spelling/technical.txt",
    "spelling/fixes.txt",
]
spelling_ignore_wiki_words = False
# spelling_ignore_acronyms = False
spelling_ignore_python_builtins = False
spelling_ignore_importable_modules = False
