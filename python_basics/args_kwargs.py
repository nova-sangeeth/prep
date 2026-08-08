"""Q4. What are *args and **kwargs?

*args    -> extra positional args collected into a tuple.
**kwargs -> extra keyword args collected into a dict.
The leading * / ** matter; the names are convention only.
"""
from __future__ import annotations

from typing import Any


def collect(*args: Any, **kwargs: Any) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """Return the captured positional tuple and keyword dict."""
    return args, kwargs


def unpacking_demo() -> None:
    """The reverse: * spreads a sequence, ** spreads a mapping into a call."""
    nums = [1, 2, 3]
    print(*nums)  # 1 2 3
    opts = {"sep": "-", "end": "!\n"}
    print("a", "b", **opts)  # a-b!


if __name__ == "__main__":
    print(collect(1, 2, 3, name="Sam", age=30))
    unpacking_demo()
