"""Valid Sudoku  |  tier: neetcode150  |  Arrays & Hashing

Determine if a 9x9 board is valid: no repeated digit within any row, column, or
3x3 box. Empty cells are '.' and are ignored.

Approach: one pass; track seen digits per row, per column, and per box. Box key
is (row // 3, col // 3). Any collision -> invalid.
Time: O(81) = O(1)   Space: O(1)
"""
from __future__ import annotations

from collections import defaultdict


def is_valid_sudoku(board: list[list[str]]) -> bool:
    """Return True if the current board configuration is valid."""
    rows: defaultdict[int, set[str]] = defaultdict(set)
    cols: defaultdict[int, set[str]] = defaultdict(set)
    boxes: defaultdict[tuple[int, int], set[str]] = defaultdict(set)

    for r in range(9):
        for c in range(9):
            val = board[r][c]
            if val == ".":
                continue
            box = (r // 3, c // 3)
            if val in rows[r] or val in cols[c] or val in boxes[box]:
                return False
            rows[r].add(val)
            cols[c].add(val)
            boxes[box].add(val)
    return True


if __name__ == "__main__":
    board = [
        ["5", "3", ".", ".", "7", ".", ".", ".", "."],
        ["6", ".", ".", "1", "9", "5", ".", ".", "."],
        [".", "9", "8", ".", ".", ".", ".", "6", "."],
        ["8", ".", ".", ".", "6", ".", ".", ".", "3"],
        ["4", ".", ".", "8", ".", "3", ".", ".", "1"],
        ["7", ".", ".", ".", "2", ".", ".", ".", "6"],
        [".", "6", ".", ".", ".", ".", "2", "8", "."],
        [".", ".", ".", "4", "1", "9", ".", ".", "5"],
        [".", ".", ".", ".", "8", ".", ".", "7", "9"],
    ]
    assert is_valid_sudoku(board) is True
    board[0][0] = "8"  # collides with the 8 in column 0
    assert is_valid_sudoku(board) is False
    print("ok")
