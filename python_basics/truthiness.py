"""Q36. Truthiness: what is falsy in Python?

Falsy: None, False, 0, 0.0, 0j, "", [], {}, (), set(), range(0).
Everything else is truthy. `if x:` checks truthiness via __bool__/__len__.
"""
from __future__ import annotations

from typing import Any


def is_truthy(value: Any) -> bool:
    """Mirror what `if value:` evaluates to."""
    return bool(value)


def safe_default(value: str | None) -> str:
    """`or` returns the first truthy operand -> handy for defaults."""
    return value or "default"


def empty_check(items: list[int]) -> str:
    """Pythonic emptiness check: `if not items`, not `len(items) == 0`."""
    return "empty" if not items else f"{len(items)} items"


if __name__ == "__main__":
    falsy = [None, False, 0, "", [], {}, set()]
    print([is_truthy(v) for v in falsy])  # all False
    print(safe_default(""))  # default
    print(safe_default("hi"))  # hi
    print(empty_check([]))  # empty
