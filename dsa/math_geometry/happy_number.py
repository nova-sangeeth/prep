"""Happy Number  |  tier: neetcode150  |  Math & Geometry

A number is happy if repeatedly replacing it with the sum of squares of its digits
eventually reaches 1. Return True if n is happy.

Approach: this is cycle detection. Use Floyd's slow/fast pointers over the
digit-square-sum sequence; reaching 1 means happy, meeting elsewhere means a loop.
Time: O(log n) per step   Space: O(1)
"""
from __future__ import annotations


def _next(n: int) -> int:
    total = 0
    while n:
        n, digit = divmod(n, 10)
        total += digit * digit
    return total


def is_happy(n: int) -> bool:
    """Return True if n is a happy number."""
    slow, fast = n, _next(n)
    while fast != 1 and slow != fast:
        slow = _next(slow)
        fast = _next(_next(fast))
    return fast == 1


if __name__ == "__main__":
    assert is_happy(19) is True  # 1+81=82 ... -> 1
    assert is_happy(2) is False
    assert is_happy(1) is True
    print("ok")
