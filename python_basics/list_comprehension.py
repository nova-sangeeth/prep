"""Q7. List comprehensions.

Form: [expression for item in iterable if condition]
Faster and clearer than an equivalent for+append loop. Set/dict/generator
comprehensions share the syntax.
"""
from __future__ import annotations


def basics() -> None:
    """Squares, filtering, and an inline if/else (placed before the for)."""
    squares: list[int] = [x * x for x in range(5)]
    evens: list[int] = [x for x in range(10) if x % 2 == 0]
    labels: list[str] = ["even" if x % 2 == 0 else "odd" for x in range(3)]
    print(squares, evens, labels)


def nested() -> list[tuple[int, int]]:
    """Two-level comprehension building coordinate pairs."""
    return [(i, j) for i in range(2) for j in range(2)]


def other_forms() -> None:
    """Set, dict, and generator comprehensions."""
    print({x * x for x in range(5)})  # set
    print({x: x * x for x in range(5)})  # dict
    print(sum(x * x for x in range(5)))  # generator (lazy)


if __name__ == "__main__":
    basics()
    print(nested())
    other_forms()
