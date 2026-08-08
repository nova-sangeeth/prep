"""Last Stone Weight  |  tier: neetcode150  |  Heap

Repeatedly smash the two heaviest stones; if unequal, the difference returns to
the pile. Return the weight of the last remaining stone (0 if none).

Approach: max-heap (negate values for Python's min-heap). Pop the two largest,
push back their difference if non-zero.
Time: O(n log n)   Space: O(n)
"""
from __future__ import annotations

import heapq


def last_stone_weight(stones: list[int]) -> int:
    """Return the weight of the last stone after all smashes."""
    heap = [-stone for stone in stones]
    heapq.heapify(heap)
    while len(heap) > 1:
        first = -heapq.heappop(heap)
        second = -heapq.heappop(heap)
        if first != second:
            heapq.heappush(heap, -(first - second))
    return -heap[0] if heap else 0


if __name__ == "__main__":
    assert last_stone_weight([2, 7, 4, 1, 8, 1]) == 1
    assert last_stone_weight([1]) == 1
    assert last_stone_weight([2, 2]) == 0
    print("ok")
