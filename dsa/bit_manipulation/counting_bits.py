"""Counting Bits  |  tier: blind75, neetcode150  |  Bit Manipulation

Return an array where ans[i] is the number of set bits in i, for i in 0..n.

Approach: DP. ans[i] = ans[i >> 1] + (i & 1) -- the bits of i are the bits of i//2
plus its lowest bit. Builds the whole table in one pass.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def count_bits(n: int) -> list[int]:
    """Return set-bit counts for every integer from 0 to n."""
    ans = [0] * (n + 1)
    for i in range(1, n + 1):
        ans[i] = ans[i >> 1] + (i & 1)
    return ans


if __name__ == "__main__":
    assert count_bits(2) == [0, 1, 1]
    assert count_bits(5) == [0, 1, 1, 2, 1, 2]
    assert count_bits(0) == [0]
    print("ok")
