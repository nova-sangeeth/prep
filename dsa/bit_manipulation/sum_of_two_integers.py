"""Sum of Two Integers  |  tier: blind75, neetcode150  |  Bit Manipulation

Add two integers without using + or -.

Approach: XOR gives the sum without carries; AND << 1 gives the carries. Repeat
until there is no carry. Python ints are unbounded, so mask to 32 bits each step
and reinterpret the sign at the end.
Time: O(1)  (<= 32 iterations)   Space: O(1)
"""
from __future__ import annotations

MASK = 0xFFFFFFFF
INT_MAX = 0x7FFFFFFF


def get_sum(first: int, second: int) -> int:
    """Return first + second using only bitwise operations."""
    while second & MASK:
        carry = (first & second) << 1
        first = first ^ second
        second = carry
    first &= MASK
    # interpret the masked result as a signed 32-bit integer
    return first if first <= INT_MAX else ~(first ^ MASK)


if __name__ == "__main__":
    assert get_sum(1, 2) == 3
    assert get_sum(2, 3) == 5
    assert get_sum(-2, 3) == 1
    assert get_sum(-1, -1) == -2
    print("ok")
