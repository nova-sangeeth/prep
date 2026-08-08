"""Q25. Module vs package.

Module  : a single .py file of code (functions, classes, variables).
Package : a directory of modules (namespace), traditionally with __init__.py.
Import forms:
    import mod              -> mod.name
    from pkg import mod     -> mod.name
    from pkg.sub import fn  -> fn
    import numpy as np      -> alias
sys.path / PYTHONPATH controls where imports are searched.
"""
from __future__ import annotations

import math  # stdlib module
import sys


def use_module() -> float:
    """Call into an imported module."""
    return math.sqrt(144)


def show_search_path() -> list[str]:
    """sys.path lists the directories Python searches for imports."""
    return sys.path[:3]


if __name__ == "__main__":
    print(use_module())  # 12.0
    print(show_search_path())
