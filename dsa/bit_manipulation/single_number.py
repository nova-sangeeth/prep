"""Single Number  |  tier: core50, blind75, neetcode150  |  Bit Manipulation

Every element appears twice except one. Find the single element in O(n) time and
O(1) space.

Approach: XOR all elements. x ^ x == 0 and x ^ 0 == x, so paired values cancel and
the lone value remains.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations

from functools import reduce
from operator import xor


def single_number(nums: list[int]) -> int:
    """Return the element that appears exactly once."""
    return reduce(xor, nums)


if __name__ == "__main__":
    assert single_number([2, 2, 1]) == 1
    assert single_number([4, 1, 2, 1, 2]) == 4
    assert single_number([7]) == 7
    print("ok")
