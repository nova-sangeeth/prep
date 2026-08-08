"""N-Queens  |  tier: neetcode150  |  Backtracking

Place n queens on an n x n board so none attack each other; return the number of
distinct solutions.

Approach: place one queen per row, backtracking. Track occupied columns and both
diagonal directions (r + c and r - c) in sets for O(1) conflict checks.
Time: O(n!)   Space: O(n)
"""
from __future__ import annotations


def total_n_queens(n: int) -> int:
    """Return the number of distinct N-Queens placements."""
    cols: set[int] = set()
    diag: set[int] = set()  # r + c
    anti: set[int] = set()  # r - c
    count = 0

    def backtrack(row: int) -> None:
        nonlocal count
        if row == n:
            count += 1
            return
        for col in range(n):
            if col in cols or (row + col) in diag or (row - col) in anti:
                continue
            cols.add(col)
            diag.add(row + col)
            anti.add(row - col)
            backtrack(row + 1)
            cols.remove(col)
            diag.remove(row + col)
            anti.remove(row - col)

    backtrack(0)
    return count


if __name__ == "__main__":
    assert total_n_queens(4) == 2
    assert total_n_queens(1) == 1
    assert total_n_queens(8) == 92
    print("ok")
