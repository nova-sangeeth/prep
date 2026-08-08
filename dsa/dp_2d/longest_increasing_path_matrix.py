"""Longest Increasing Path in a Matrix  |  tier: neetcode150  |  2-D DP

Return the length of the longest strictly increasing path (moving 4-directionally)
in a matrix.

Approach: DFS with memoization. The longest path from a cell only depends on the
cell, so cache it. Strictly increasing moves mean no cycles, so no visited set is
needed.
Time: O(m * n)   Space: O(m * n)
"""
from __future__ import annotations

from functools import lru_cache


def longest_increasing_path(matrix: list[list[int]]) -> int:
    """Return the length of the longest strictly increasing path."""
    if not matrix:
        return 0
    rows, cols = len(matrix), len(matrix[0])

    @lru_cache(maxsize=None)
    def dfs(r: int, c: int) -> int:
        best = 1
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and matrix[nr][nc] > matrix[r][c]:
                best = max(best, 1 + dfs(nr, nc))
        return best

    return max(dfs(r, c) for r in range(rows) for c in range(cols))


if __name__ == "__main__":
    assert longest_increasing_path([[9, 9, 4], [6, 6, 8], [2, 1, 1]]) == 4  # 1,2,6,9
    assert longest_increasing_path([[3, 4, 5], [3, 2, 6], [2, 2, 1]]) == 4
    assert longest_increasing_path([[1]]) == 1
    print("ok")
