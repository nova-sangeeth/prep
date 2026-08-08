"""Longest Increasing Subsequence  |  tier: core50, blind75, neetcode150  |  1-D DP

Return the length of the longest strictly increasing subsequence.

Approach: patience sorting. Maintain 'tails', where tails[i] is the smallest
possible tail of an increasing subsequence of length i+1. For each number,
binary-search its insertion point; the length of tails is the answer.
Time: O(n log n)   Space: O(n)
"""
from __future__ import annotations

from bisect import bisect_left


def length_of_lis(nums: list[int]) -> int:
    """Return the length of the longest strictly increasing subsequence."""
    tails: list[int] = []
    for num in nums:
        i = bisect_left(tails, num)  # first tail >= num
        if i == len(tails):
            tails.append(num)  # extends the longest subsequence
        else:
            tails[i] = num  # lowers a tail -> more room later
    return len(tails)


if __name__ == "__main__":
    assert length_of_lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4  # 2,3,7,101
    assert length_of_lis([0, 1, 0, 3, 2, 3]) == 4
    assert length_of_lis([7, 7, 7, 7]) == 1
    print("ok")
