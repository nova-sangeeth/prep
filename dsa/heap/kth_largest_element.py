"""Kth Largest Element in an Array  |  tier: core50, neetcode150  |  Heap

Return the k-th largest element (k-th in sorted-descending order).

Approach: a min-heap of size k. After processing all elements, the heap holds
the k largest and its root is the answer. (Quickselect gives O(n) average; the
heap is simpler and O(n log k).)
Time: O(n log k)   Space: O(k)
"""
from __future__ import annotations

import heapq


def find_kth_largest(nums: list[int], k: int) -> int:
    """Return the k-th largest element."""
    heap: list[int] = []
    for num in nums:
        heapq.heappush(heap, num)
        if len(heap) > k:
            heapq.heappop(heap)
    return heap[0]


if __name__ == "__main__":
    assert find_kth_largest([3, 2, 1, 5, 6, 4], 2) == 5
    assert find_kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4
    assert find_kth_largest([1], 1) == 1
    print("ok")
