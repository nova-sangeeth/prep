"""Q12. What is a lambda function?

An anonymous, single-expression function: `lambda args: expression`.
Most useful inline as a `key`/callback. For anything reusable, prefer def.
"""
from __future__ import annotations

from typing import Callable


def make_multiplier(factor: int) -> Callable[[int], int]:
    """Return a lambda closing over `factor`."""
    return lambda x: x * factor


def sorting_demo() -> None:
    """Lambda as a sort key -- the canonical use."""
    words = ["banana", "kiwi", "apple"]
    print(sorted(words, key=lambda w: len(w)))  # by length
    nums = [3, 1, 4, 1, 5]
    print(sorted(nums, key=lambda x: -x))  # descending


if __name__ == "__main__":
    triple = make_multiplier(3)
    print(triple(5))  # 15
    sorting_demo()
