"""Combination Sum II  |  tier: neetcode150  |  Backtracking

Given candidates (with duplicates) and a target, return unique combinations
summing to target. Each candidate may be used at most once.

Approach: sort, then backtrack advancing the index each pick (no reuse). Skip a
duplicate candidate at the same level to avoid duplicate combinations. Prune when
remaining < 0.
Time: O(2^n)   Space: O(n)
"""
from __future__ import annotations


def combination_sum2(candidates: list[int], target: int) -> list[list[int]]:
    """Return unique combinations summing to target (each used once)."""
    candidates.sort()
    result: list[list[int]] = []
    current: list[int] = []

    def backtrack(start: int, remaining: int) -> None:
        if remaining == 0:
            result.append(current[:])
            return
        for i in range(start, len(candidates)):
            if i > start and candidates[i] == candidates[i - 1]:
                continue  # skip duplicate at this level
            if candidates[i] > remaining:
                break  # sorted: no further candidate fits
            current.append(candidates[i])
            backtrack(i + 1, remaining - candidates[i])
            current.pop()

    backtrack(0, target)
    return result


if __name__ == "__main__":
    assert sorted(combination_sum2([10, 1, 2, 7, 6, 1, 5], 8)) == sorted([[1, 1, 6], [1, 2, 5], [1, 7], [2, 6]])
    assert sorted(combination_sum2([2, 5, 2, 1, 2], 5)) == sorted([[1, 2, 2], [5]])
    print("ok")
