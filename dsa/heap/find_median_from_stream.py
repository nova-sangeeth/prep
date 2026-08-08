"""Find Median from Data Stream  |  tier: blind75, neetcode150  |  Heap

Support addNum(num) and findMedian() over a growing stream.

Approach: two heaps. A max-heap 'low' holds the smaller half, a min-heap 'high'
holds the larger half. Keep their sizes balanced (differ by <= 1). The median is
the top of the larger heap, or the average of both tops when sizes are equal.
Time: add O(log n), median O(1)   Space: O(n)
"""
from __future__ import annotations

import heapq


class MedianFinder:
    """Streaming median via two balanced heaps."""

    def __init__(self) -> None:
        self._low: list[int] = []  # max-heap (negated)
        self._high: list[int] = []  # min-heap

    def add_num(self, num: int) -> None:
        """Add a number, keeping the two halves balanced and ordered."""
        heapq.heappush(self._low, -num)
        heapq.heappush(self._high, -heapq.heappop(self._low))  # move max over
        if len(self._high) > len(self._low):  # rebalance
            heapq.heappush(self._low, -heapq.heappop(self._high))

    def find_median(self) -> float:
        """Return the current median."""
        if len(self._low) > len(self._high):
            return float(-self._low[0])
        return (-self._low[0] + self._high[0]) / 2


if __name__ == "__main__":
    mf = MedianFinder()
    mf.add_num(1)
    mf.add_num(2)
    assert mf.find_median() == 1.5
    mf.add_num(3)
    assert mf.find_median() == 2.0
    print("ok")
