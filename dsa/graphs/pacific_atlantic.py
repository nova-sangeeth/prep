"""Pacific Atlantic Water Flow  |  tier: blind75, neetcode150  |  Graphs

Water flows from a cell to neighbors of equal or lower height. The Pacific
touches the top/left edges, the Atlantic the bottom/right. Return cells that can
reach both oceans.

Approach: instead of searching from each cell, DFS INWARD from each ocean's
border, marking cells that can reach that ocean (climbing to >= height). The
answer is the intersection of the two reachable sets.
Time: O(rows * cols)   Space: O(rows * cols)
"""
from __future__ import annotations


def pacific_atlantic(heights: list[list[int]]) -> list[list[int]]:
    """Return cells from which water reaches both oceans."""
    if not heights:
        return []
    rows, cols = len(heights), len(heights[0])
    pacific: set[tuple[int, int]] = set()
    atlantic: set[tuple[int, int]] = set()

    def dfs(r: int, c: int, seen: set[tuple[int, int]], prev: int) -> None:
        if not (0 <= r < rows and 0 <= c < cols) or (r, c) in seen or heights[r][c] < prev:
            return
        seen.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            dfs(r + dr, c + dc, seen, heights[r][c])

    for c in range(cols):
        dfs(0, c, pacific, heights[0][c])
        dfs(rows - 1, c, atlantic, heights[rows - 1][c])
    for r in range(rows):
        dfs(r, 0, pacific, heights[r][0])
        dfs(r, cols - 1, atlantic, heights[r][cols - 1])

    return [[r, c] for r, c in pacific & atlantic]


if __name__ == "__main__":
    heights = [
        [1, 2, 2, 3, 5],
        [3, 2, 3, 4, 4],
        [2, 4, 5, 3, 1],
        [6, 7, 1, 4, 5],
        [5, 1, 1, 2, 4],
    ]
    result = {tuple(cell) for cell in pacific_atlantic(heights)}
    expected = {(0, 4), (1, 3), (1, 4), (2, 2), (3, 0), (3, 1), (4, 0)}
    assert result == expected
    print("ok")
