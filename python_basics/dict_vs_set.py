"""Q17. Dictionary vs set.

Both are hash tables with O(1) average lookup.
dict -> key:value pairs, lookup by key.
set  -> unique values only, membership + set algebra.
Note: {} is an empty dict; use set() for an empty set.
"""
from __future__ import annotations


def dict_demo() -> None:
    """Key access and membership (checks keys)."""
    scores: dict[str, int] = {"a": 1, "b": 2}
    print(scores["a"], "a" in scores)


def set_demo() -> None:
    """Duplicates dropped; set algebra."""
    s: set[int] = {1, 2, 2, 3}  # {1, 2, 3}
    print(s)
    print({1, 2, 3} & {2, 3, 4})  # {2, 3} intersection
    print({1, 2, 3} | {3, 4})  # {1, 2, 3, 4} union
    print({1, 2, 3} - {2})  # {1, 3} difference


def dedupe(items: list[int]) -> list[int]:
    """Common use of a set: remove duplicates."""
    return list(set(items))


if __name__ == "__main__":
    dict_demo()
    set_demo()
    print(dedupe([1, 1, 2, 3, 3]))
