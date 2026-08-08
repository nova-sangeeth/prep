"""Number of Islands  |  tier: core50, blind75, neetcode150  |  Graphs

Count islands ('1' land connected 4-directionally) in a grid of '1'/'0'.

Approach: scan cells; on each unvisited land cell, flood-fill (DFS) the whole
island marking cells visited, and increment the count.
Time: O(rows * cols)   Space: O(rows * cols) recursion worst case
"""
from __future__ import annotations


def num_islands(grid: list[list[str]]) -> int:
    """Return the number of islands in the grid."""
    if not grid:
        return 0
    rows, cols = len(grid), len(grid[0])

    def sink(r: int, c: int) -> None:
        if not (0 <= r < rows and 0 <= c < cols) or grid[r][c] != "1":
            return
        grid[r][c] = "0"  # mark visited
        sink(r + 1, c)
        sink(r - 1, c)
        sink(r, c + 1)
        sink(r, c - 1)

    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1":
                sink(r, c)
                count += 1
    return count


if __name__ == "__main__":
    grid = [
        ["1", "1", "0", "0", "0"],
        ["1", "1", "0", "0", "0"],
        ["0", "0", "1", "0", "0"],
        ["0", "0", "0", "1", "1"],
    ]
    assert num_islands(grid) == 3
    assert num_islands([["0"]]) == 0
    print("ok")
