"""Q6. Generators and the `yield` keyword.

A generator produces values lazily, one at a time, keeping state between
calls. Memory efficient for large/infinite streams. `yield` pauses and
resumes the function.
"""
from __future__ import annotations

from typing import Iterator


def count_up(n: int) -> Iterator[int]:
    """Yield 0..n-1 lazily instead of building a list."""
    i = 0
    while i < n:
        yield i
        i += 1


def fibonacci() -> Iterator[int]:
    """Infinite generator: take only what you consume."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


if __name__ == "__main__":
    print(list(count_up(5)))

    fib = fibonacci()
    print([next(fib) for _ in range(8)])  # first 8 Fibonacci numbers

    lazy_squares = (x * x for x in range(1_000_000))  # generator expression
    print(sum(lazy_squares))  # no memory blow-up
