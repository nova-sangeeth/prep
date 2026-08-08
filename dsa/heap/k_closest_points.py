"""K Closest Points to Origin  |  tier: neetcode150  |  Heap

Return the k points closest to the origin (Euclidean distance).

Approach: max-heap of size k keyed by squared distance (no sqrt needed -- it is
monotonic). Keep only the k smallest distances by evicting the largest.
Time: O(n log k)   Space: O(k)
"""
from __future__ import annotations

import heapq


def k_closest(points: list[list[int]], k: int) -> list[list[int]]:
    """Return the k points nearest the origin (any order)."""
    heap: list[tuple[int, list[int]]] = []
    for x, y in points:
        dist = -(x * x + y * y)  # negate -> max-heap behavior
        if len(heap) < k:
            heapq.heappush(heap, (dist, [x, y]))
        elif dist > heap[0][0]:
            heapq.heapreplace(heap, (dist, [x, y]))
    return [point for _, point in heap]


if __name__ == "__main__":
    out = k_closest([[1, 3], [-2, 2]], 1)
    assert out == [[-2, 2]]
    out2 = sorted(k_closest([[3, 3], [5, -1], [-2, 4]], 2))
    assert out2 == [[-2, 4], [3, 3]]
    print("ok")
