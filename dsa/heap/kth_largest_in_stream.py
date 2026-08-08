"""Kth Largest Element in a Stream  |  tier: neetcode150  |  Heap

Design a class that, given k, returns the k-th largest value seen so far after
each add().

Approach: a min-heap of size k holds the k largest values; its root is the
k-th largest. On add, push and pop the smallest if size exceeds k.
Time: O(log k) per add   Space: O(k)
"""
from __future__ import annotations

import heapq


class KthLargest:
    """Maintains the k-th largest element of a stream."""

    def __init__(self, k: int, nums: list[int]) -> None:
        self.k = k
        self.heap = nums[:]
        heapq.heapify(self.heap)
        while len(self.heap) > k:
            heapq.heappop(self.heap)

    def add(self, val: int) -> int:
        """Add a value and return the current k-th largest."""
        heapq.heappush(self.heap, val)
        if len(self.heap) > self.k:
            heapq.heappop(self.heap)
        return self.heap[0]


if __name__ == "__main__":
    kth = KthLargest(3, [4, 5, 8, 2])
    assert kth.add(3) == 4
    assert kth.add(5) == 5
    assert kth.add(10) == 5
    assert kth.add(9) == 8
    assert kth.add(4) == 8
    print("ok")
