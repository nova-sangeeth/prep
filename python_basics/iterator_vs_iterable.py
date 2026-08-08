"""Q21. Iterable vs iterator.

Iterable : has __iter__; can be looped over (list, str, dict, ...).
Iterator : has __iter__ AND __next__; yields values once, raises StopIteration.
Every iterator is iterable; not every iterable is an iterator.
"""
from __future__ import annotations

from typing import Iterator


def manual_iteration() -> None:
    """A for loop is iter() + next() until StopIteration."""
    nums = [1, 2, 3]
    it = iter(nums)  # iterable -> iterator
    print(next(it), next(it), next(it))
    try:
        next(it)
    except StopIteration:
        print("exhausted")


class Counter:
    """A custom iterator counting from 1 to `limit`."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.n = 0

    def __iter__(self) -> "Counter":
        return self

    def __next__(self) -> int:
        if self.n >= self.limit:
            raise StopIteration
        self.n += 1
        return self.n


if __name__ == "__main__":
    manual_iteration()
    print(list(Counter(4)))  # [1, 2, 3, 4]
