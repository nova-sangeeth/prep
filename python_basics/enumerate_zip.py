"""Q33. enumerate() and zip().

enumerate(it, start) -> (index, value) pairs; avoids manual counters.
zip(a, b, ...)       -> pairs items across iterables; stops at the shortest.
Both are lazy iterators.
"""
from __future__ import annotations


def enumerate_demo() -> None:
    """Index + value without a manual counter."""
    for i, fruit in enumerate(["a", "b", "c"], start=1):
        print(i, fruit)


def zip_demo() -> dict[str, int]:
    """Combine two lists into a dict; zip stops at the shorter one."""
    keys = ["x", "y", "z"]
    vals = [1, 2, 3]
    return dict(zip(keys, vals))


def unzip(pairs: list[tuple[str, int]]) -> tuple[tuple[str, ...], tuple[int, ...]]:
    """zip(*pairs) transposes -> the inverse of zip."""
    names, nums = zip(*pairs)
    return names, nums


if __name__ == "__main__":
    enumerate_demo()
    print(zip_demo())  # {'x': 1, 'y': 2, 'z': 3}
    print(unzip([("a", 1), ("b", 2)]))  # (('a','b'), (1,2))
