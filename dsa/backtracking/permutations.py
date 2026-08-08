"""Permutations  |  tier: core50, neetcode150  |  Backtracking

Return all permutations of a list of distinct integers.

Approach: backtracking with a used set (or in-place swaps). Build a permutation
one position at a time, marking elements used to avoid reuse.
Time: O(n * n!)   Space: O(n) recursion
"""
from __future__ import annotations


def permute(nums: list[int]) -> list[list[int]]:
    """Return all permutations of nums."""
    result: list[list[int]] = []
    current: list[int] = []
    used = [False] * len(nums)

    def backtrack() -> None:
        if len(current) == len(nums):
            result.append(current[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True
            current.append(nums[i])
            backtrack()
            current.pop()
            used[i] = False

    backtrack()
    return result


if __name__ == "__main__":
    out = permute([1, 2, 3])
    assert len(out) == 6
    assert sorted(out) == sorted([[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]])
    print("ok")
