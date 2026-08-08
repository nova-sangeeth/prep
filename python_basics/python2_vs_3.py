"""Q20. Main differences between Python 2 and Python 3.

Python 2 is end-of-life (Jan 1 2020). Use Python 3.
- print is a function, not a statement.
- / is true division (5/2 == 2.5); // is floor division.
- str is Unicode by default.
- range/map/filter return lazy iterators.
- except E as e (not except E, e).
"""
from __future__ import annotations


def division_demo() -> tuple[float, int]:
    """Python 3 true vs floor division."""
    return 5 / 2, 5 // 2  # (2.5, 2)


def unicode_demo() -> bool:
    """In Python 3, str is Unicode -- non-ASCII text is fine."""
    text = "café — 日本語"
    return len(text) > 0


if __name__ == "__main__":
    print(division_demo())  # (2.5, 2)
    print(unicode_demo())
    print(list(range(3)))  # lazy in 3, list() to materialize
