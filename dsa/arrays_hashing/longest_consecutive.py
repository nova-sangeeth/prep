"""Longest Consecutive Sequence  |  tier: blind75, neetcode150  |  Arrays & Hashing

Return the length of the longest run of consecutive integers, in O(n). Order in
the input does not matter.

Approach: put all values in a set. Only start counting from a sequence START
(a value with no n-1 present). From each start, walk n+1, n+2, ... This makes
each value visited at most twice overall.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def longest_consecutive(nums: list[int]) -> int:
    """Return length of the longest consecutive integer sequence."""
    num_set = set(nums)
    best = 0
    for num in num_set:
        if num - 1 in num_set:
            continue  # not a sequence start
        length = 1
        while num + length in num_set:
            length += 1
        best = max(best, length)
    return best


if __name__ == "__main__":
    assert longest_consecutive([100, 4, 200, 1, 3, 2]) == 4  # 1,2,3,4
    assert longest_consecutive([0, 3, 7, 2, 5, 8, 4, 6, 0, 1]) == 9
    assert longest_consecutive([]) == 0
    print("ok")
