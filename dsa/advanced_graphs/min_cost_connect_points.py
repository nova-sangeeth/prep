"""Min Cost to Connect All Points  |  tier: neetcode150  |  Advanced Graphs

Connect all points with minimum total Manhattan-distance edge cost (a minimum
spanning tree).

Approach: Prim's algorithm with a min-heap. Start from any point; repeatedly add
the cheapest edge to an unvisited point, then push that point's edges.
Time: O(n^2 log n)   Space: O(n^2)
"""
from __future__ import annotations

import heapq


def min_cost_connect_points(points: list[list[int]]) -> int:
    """Return the minimum cost to connect all points (MST)."""
    n = len(points)
    visited: set[int] = set()
    heap: list[tuple[int, int]] = [(0, 0)]  # (cost, point index)
    total = 0
    while len(visited) < n:
        cost, i = heapq.heappop(heap)
        if i in visited:
            continue
        visited.add(i)
        total += cost
        xi, yi = points[i]
        for j in range(n):
            if j not in visited:
                xj, yj = points[j]
                dist = abs(xi - xj) + abs(yi - yj)
                heapq.heappush(heap, (dist, j))
    return total


if __name__ == "__main__":
    assert min_cost_connect_points([[0, 0], [2, 2], [3, 10], [5, 2], [7, 0]]) == 20
    assert min_cost_connect_points([[0, 0]]) == 0
    print("ok")
