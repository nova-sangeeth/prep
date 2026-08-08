"""Word Search  |  tier: core50, blind75, neetcode150  |  Backtracking

Return True if a word can be formed from sequentially adjacent cells in a grid
(no cell reused).

Approach: DFS from each cell matching the word char by char. Mark visited cells
in place (temporary sentinel), recurse to four neighbors, then restore.
Time: O(cells * 4^len)   Space: O(len) recursion
"""
from __future__ import annotations


def exist(board: list[list[str]], word: str) -> bool:
    """Return True if word exists as an adjacent path in the grid."""
    rows, cols = len(board), len(board[0])

    def dfs(r: int, c: int, i: int) -> bool:
        if i == len(word):
            return True
        if not (0 <= r < rows and 0 <= c < cols) or board[r][c] != word[i]:
            return False
        board[r][c] = "#"  # mark visited
        found = dfs(r + 1, c, i + 1) or dfs(r - 1, c, i + 1) or dfs(r, c + 1, i + 1) or dfs(r, c - 1, i + 1)
        board[r][c] = word[i]  # restore
        return found

    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False


if __name__ == "__main__":
    board = [["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]]
    assert exist(board, "ABCCED") is True
    assert exist(board, "SEE") is True
    assert exist(board, "ABCB") is False
    print("ok")
