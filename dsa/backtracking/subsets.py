"""Subsets  |  tier: core50, neetcode150  |  Backtracking

Return all subsets (the power set) of a list of distinct integers.

Approach: backtracking. At each index choose to include or skip the element,
recording the current partial subset at every leaf. 2^n subsets.
Time: O(n * 2^n)   Space: O(n) recursion
"""
from __future__ import annotations


def subsets(nums: list[int]) -> list[list[int]]:
    """Return the power set of nums."""
    result: list[list[int]] = []
    current: list[int] = []

    def backtrack(start: int) -> None:
        result.append(current[:])
        for i in range(start, len(nums)):
            current.append(nums[i])
            backtrack(i + 1)
            current.pop()

    backtrack(0)
    return result


if __name__ == "__main__":
    out = subsets([1, 2, 3])
    assert len(out) == 8
    assert sorted(out) == sorted([[], [1], [2], [3], [1, 2], [1, 3], [2, 3], [1, 2, 3]])
    print("ok")
