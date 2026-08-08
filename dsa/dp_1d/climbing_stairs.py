"""Climbing Stairs  |  tier: core50, blind75, neetcode150  |  1-D DP

You can climb 1 or 2 steps at a time. Return the number of distinct ways to reach
step n.

Approach: ways(n) = ways(n-1) + ways(n-2) -- it is the Fibonacci recurrence. Roll
two variables instead of an array.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def climb_stairs(n: int) -> int:
    """Return the number of distinct ways to climb n stairs."""
    prev, curr = 1, 1  # ways to reach step 0 and 1
    for _ in range(n - 1):
        prev, curr = curr, prev + curr
    return curr


if __name__ == "__main__":
    assert climb_stairs(2) == 2  # 1+1, 2
    assert climb_stairs(3) == 3  # 1+1+1, 1+2, 2+1
    assert climb_stairs(5) == 8
    print("ok")
