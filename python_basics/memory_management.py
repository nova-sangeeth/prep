"""Q18. How does Python manage memory?

- Reference counting (primary): object freed when refcount hits 0.
- Garbage collector (gc): reclaims reference cycles ref counting can't.
- Private heap + pymalloc pools/arenas for small objects.
You rarely manage memory by hand.
"""
from __future__ import annotations

import gc
import sys


def refcount_demo() -> None:
    """Reference count rises with new references, falls with del."""
    obj: list[int] = [1, 2, 3]
    print("refs:", sys.getrefcount(obj))  # inflated by the call arg
    alias = obj
    print("refs after alias:", sys.getrefcount(obj))
    del alias
    print("refs after del:", sys.getrefcount(obj))


def cycle_demo() -> None:
    """A self-reference cycle is reclaimed by the gc, not refcounting alone."""
    a: dict[str, object] = {}
    a["self"] = a  # cycle: refcount never 0
    del a
    collected = gc.collect()  # force a collection
    print("cycles collected:", collected)


if __name__ == "__main__":
    refcount_demo()
    cycle_demo()
