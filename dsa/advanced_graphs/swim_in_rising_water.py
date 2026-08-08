"""Swim in Rising Water  |  tier: neetcode150  |  Advanced Graphs

At time t, water depth is t everywhere. You can move 4-directionally between
cells whose height <= t. Return the least time to reach the bottom-right from the
top-left.

Approach: Dijkstra-like greedy with a min-heap keyed by the max height seen on
the path so far. Always expand the cell reachable with the lowest "max height";
the first time the target pops, that value is the answer.
Time: O(n^2 log n)   Space: O(n^2)
"""
from __future__ import annotations

import heapq


def swim_in_water(grid: list[list[int]]) -> int:
    """Return the minimum time to reach the bottom-right cell."""
    n = len(grid)
    visited: set[tuple[int, int]] = set()
    heap: list[tuple[int, int, int]] = [(grid[0][0], 0, 0)]  # (max_height, r, c)
    while heap:
        height, r, c = heapq.heappop(heap)
        if (r, c) in visited:
            continue
        visited.add((r, c))
        if r == n - 1 and c == n - 1:
            return height
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in visited:
                heapq.heappush(heap, (max(height, grid[nr][nc]), nr, nc))
    return -1


if __name__ == "__main__":
    assert swim_in_water([[0, 2], [1, 3]]) == 3
    assert (
        swim_in_water(
            [[0, 1, 2, 3, 4], [24, 23, 22, 21, 5], [12, 13, 14, 15, 16], [11, 17, 18, 19, 20], [10, 9, 8, 7, 6]]
        )
        == 16
    )
    print("ok")
