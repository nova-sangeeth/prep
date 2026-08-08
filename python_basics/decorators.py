"""Q5. What is a decorator?

A callable that wraps another function to add behavior without editing it.
`@deco` is sugar for `func = deco(func)`. Use functools.wraps to keep
the wrapped function's name/docstring.
"""
from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def timer(func: F) -> F:
    """Print how long the wrapped function takes, then return its result."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.perf_counter() - start:.6f}s")
        return result

    return wrapper  # type: ignore[return-value]


def repeat(n: int) -> Callable[[F], F]:
    """Decorator factory: run the wrapped function n times, return last result."""

    def deco(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result: Any = None
            for _ in range(n):
                result = func(*args, **kwargs)
            return result

        return wrapper  # type: ignore[return-value]

    return deco


@timer
@repeat(3)
def greet(name: str) -> str:
    """Return a greeting (called 3x, timed)."""
    return f"hi {name}"


if __name__ == "__main__":
    print(greet("Sam"))
