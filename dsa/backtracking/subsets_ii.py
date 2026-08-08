"""Subsets II  |  tier: neetcode150  |  Backtracking

Return all unique subsets when the input may contain duplicates.

Approach: sort first so duplicates are adjacent. During backtracking, skip a
candidate that equals the previous one at the SAME recursion level -- this avoids
generating duplicate subsets.
Time: O(n * 2^n)   Space: O(n)
"""
from __future__ import annotations


def subsets_with_dup(nums: list[int]) -> list[list[int]]:
    """Return all unique subsets (input may have duplicates)."""
    nums.sort()
    result: list[list[int]] = []
    current: list[int] = []

    def backtrack(start: int) -> None:
        result.append(current[:])
        for i in range(start, len(nums)):
            if i > start and nums[i] == nums[i - 1]:
                continue  # skip duplicate at this level
            current.append(nums[i])
            backtrack(i + 1)
            current.pop()

    backtrack(0)
    return result


if __name__ == "__main__":
    out = subsets_with_dup([1, 2, 2])
    assert sorted(out) == sorted([[], [1], [1, 2], [1, 2, 2], [2], [2, 2]])
    print("ok")
