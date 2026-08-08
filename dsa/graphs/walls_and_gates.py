"""Walls and Gates  |  tier: neetcode150  |  Graphs

Fill each empty room (2^31 - 1) with the distance to its nearest gate (0). Walls
are -1. Unreachable rooms keep their large value. Modify the grid in place.

Approach: multi-source BFS from all gates simultaneously. The first time BFS
reaches a room is its shortest distance to any gate.
Time: O(rows * cols)   Space: O(rows * cols)
"""
from __future__ import annotations

from collections import deque

INF = 2**31 - 1


def walls_and_gates(rooms: list[list[int]]) -> None:
    """Fill rooms with distance to nearest gate, in place."""
    if not rooms:
        return
    rows, cols = len(rooms), len(rooms[0])
    queue: deque[tuple[int, int]] = deque((r, c) for r in range(rows) for c in range(cols) if rooms[r][c] == 0)
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and rooms[nr][nc] == INF:
                rooms[nr][nc] = rooms[r][c] + 1
                queue.append((nr, nc))


if __name__ == "__main__":
    rooms = [
        [INF, -1, 0, INF],
        [INF, INF, INF, -1],
        [INF, -1, INF, -1],
        [0, -1, INF, INF],
    ]
    walls_and_gates(rooms)
    assert rooms == [
        [3, -1, 0, 1],
        [2, 2, 1, -1],
        [1, -1, 2, -1],
        [0, -1, 3, 4],
    ]
    print("ok")
