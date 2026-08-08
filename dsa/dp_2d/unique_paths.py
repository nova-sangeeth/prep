"""Unique Paths  |  tier: blind75, neetcode150  |  2-D DP

A robot at the top-left of an m x n grid moves only right or down. Count distinct
paths to the bottom-right.

Approach: paths to a cell = paths from above + paths from the left. Keep a single
row, updating in place; row[c] += row[c-1].
Time: O(m * n)   Space: O(n)
"""
from __future__ import annotations


def unique_paths(m: int, n: int) -> int:
    """Return the number of unique top-left to bottom-right paths."""
    row = [1] * n
    for _ in range(1, m):
        for c in range(1, n):
            row[c] += row[c - 1]
    return row[-1]


if __name__ == "__main__":
    assert unique_paths(3, 7) == 28
    assert unique_paths(3, 2) == 3
    assert unique_paths(1, 1) == 1
    print("ok")
