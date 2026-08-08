"""Q3. Difference between `is` and `==`.

==  : compares values   (calls __eq__).
is  : compares identity  (same object, same id()).

Rule: use `is` only for None/True/False singletons; use `==` for value checks.
"""
from __future__ import annotations


def value_vs_identity() -> None:
    """Equal values but different objects -> == True, is False."""
    a: list[int] = [1, 2, 3]
    b: list[int] = [1, 2, 3]
    print("a == b:", a == b)  # True
    print("a is b:", a is b)  # False
    c = a
    print("a is c:", a is c)  # True (same object)


def int_caching_trap() -> None:
    """CPython caches small ints (-5..256); never rely on this for logic."""
    x = 256
    y = 256
    print("256 is 256:", x is y)  # True (cached)
    x = 257
    y = 257
    print("257 is 257:", x is y)  # usually False


def correct_none_check(value: object) -> bool:
    """Idiomatic None test uses identity."""
    return value is None


if __name__ == "__main__":
    value_vs_identity()
    int_caching_trap()
    print(correct_none_check(None))
