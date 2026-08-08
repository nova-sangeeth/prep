"""Combination Sum  |  tier: core50, blind75, neetcode150  |  Backtracking

Given distinct candidates and a target, return all unique combinations summing to
target. Each candidate may be reused unlimited times.

Approach: backtracking. At each step either reuse the current candidate (stay on
the same index) or advance. Prune when the remaining target goes negative.
Time: exponential in target/candidates   Space: O(target) depth
"""
from __future__ import annotations


def combination_sum(candidates: list[int], target: int) -> list[list[int]]:
    """Return all combinations summing to target (reuse allowed)."""
    result: list[list[int]] = []
    current: list[int] = []

    def backtrack(start: int, remaining: int) -> None:
        if remaining == 0:
            result.append(current[:])
            return
        if remaining < 0:
            return
        for i in range(start, len(candidates)):
            current.append(candidates[i])
            backtrack(i, remaining - candidates[i])  # i, not i+1 -> reuse
            current.pop()

    backtrack(0, target)
    return result


if __name__ == "__main__":
    assert sorted(combination_sum([2, 3, 6, 7], 7)) == sorted([[2, 2, 3], [7]])
    assert sorted(combination_sum([2, 3, 5], 8)) == sorted([[2, 2, 2, 2], [2, 3, 3], [3, 5]])
    assert combination_sum([2], 1) == []
    print("ok")
