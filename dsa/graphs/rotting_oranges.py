"""Rotting Oranges  |  tier: neetcode150  |  Graphs

Each minute, rotten oranges (2) rot their fresh (1) 4-directional neighbors.
Return minutes until none are fresh, or -1 if impossible.

Approach: multi-source BFS. Start with all rotten cells in the queue, spread
level by level counting minutes. If fresh oranges remain afterward, return -1.
Time: O(rows * cols)   Space: O(rows * cols)
"""
from __future__ import annotations

from collections import deque


def oranges_rotting(grid: list[list[int]]) -> int:
    """Return minutes until all oranges rot, or -1."""
    rows, cols = len(grid), len(grid[0])
    queue: deque[tuple[int, int]] = deque()
    fresh = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                queue.append((r, c))
            elif grid[r][c] == 1:
                fresh += 1

    minutes = 0
    while queue and fresh:
        minutes += 1
        for _ in range(len(queue)):
            r, c = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                    grid[nr][nc] = 2
                    fresh -= 1
                    queue.append((nr, nc))
    return -1 if fresh else minutes


if __name__ == "__main__":
    assert oranges_rotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]]) == 4
    assert oranges_rotting([[2, 1, 1], [0, 1, 1], [1, 0, 1]]) == -1
    assert oranges_rotting([[0, 2]]) == 0
    print("ok")
