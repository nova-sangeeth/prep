"""Surrounded Regions  |  tier: neetcode150  |  Graphs

Capture all regions of 'O' fully surrounded by 'X' by flipping them to 'X'. An
'O' connected to a border is NOT captured.

Approach: DFS from every border 'O', marking the whole connected region as safe
(temporary '#'). Then flip all remaining 'O' (captured) to 'X' and restore '#'
back to 'O'.
Time: O(rows * cols)   Space: O(rows * cols)
"""
from __future__ import annotations


def solve(board: list[list[str]]) -> None:
    """Flip surrounded 'O' regions to 'X' in place."""
    if not board:
        return
    rows, cols = len(board), len(board[0])

    def mark_safe(r: int, c: int) -> None:
        if not (0 <= r < rows and 0 <= c < cols) or board[r][c] != "O":
            return
        board[r][c] = "#"
        mark_safe(r + 1, c)
        mark_safe(r - 1, c)
        mark_safe(r, c + 1)
        mark_safe(r, c - 1)

    for r in range(rows):
        mark_safe(r, 0)
        mark_safe(r, cols - 1)
    for c in range(cols):
        mark_safe(0, c)
        mark_safe(rows - 1, c)

    for r in range(rows):
        for c in range(cols):
            if board[r][c] == "O":
                board[r][c] = "X"  # captured
            elif board[r][c] == "#":
                board[r][c] = "O"  # restore safe


if __name__ == "__main__":
    board = [
        ["X", "X", "X", "X"],
        ["X", "O", "O", "X"],
        ["X", "X", "O", "X"],
        ["X", "O", "X", "X"],
    ]
    solve(board)
    assert board == [
        ["X", "X", "X", "X"],
        ["X", "X", "X", "X"],
        ["X", "X", "X", "X"],
        ["X", "O", "X", "X"],
    ]
    print("ok")
