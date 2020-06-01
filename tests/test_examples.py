import pytest
import py_compile
import glob
from os import path


def test_examples_compiles():
    # Compiles the examples, to check for syntax errors
    for name in glob.glob(path.join(path.dirname(__file__), "../examples", "*.py")):
        py_compile.compile(name)
