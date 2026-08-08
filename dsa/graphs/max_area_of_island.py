"""Max Area of Island  |  tier: neetcode150  |  Graphs

Return the area of the largest island (1s connected 4-directionally); 0 if none.

Approach: flood-fill DFS from each unvisited land cell, summing the cells
reached, and track the maximum.
Time: O(rows * cols)   Space: O(rows * cols)
"""
from __future__ import annotations


def max_area_of_island(grid: list[list[int]]) -> int:
    """Return the maximum island area."""
    rows, cols = len(grid), len(grid[0])

    def area(r: int, c: int) -> int:
        if not (0 <= r < rows and 0 <= c < cols) or grid[r][c] == 0:
            return 0
        grid[r][c] = 0  # mark visited
        return 1 + area(r + 1, c) + area(r - 1, c) + area(r, c + 1) + area(r, c - 1)

    best = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                best = max(best, area(r, c))
    return best


if __name__ == "__main__":
    grid = [
        [0, 0, 1, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 1, 1],
    ]
    assert max_area_of_island(grid) == 3
    assert max_area_of_island([[0, 0], [0, 0]]) == 0
    print("ok")
