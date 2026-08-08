"""Minimum Interval to Include Each Query  |  tier: neetcode150  |  Intervals

For each query, return the size of the smallest interval [start, end] with
start <= query <= end, or -1 if none contains the query.

Approach: sort intervals by start and queries ascending. Sweep queries; push every
interval that has started into a min-heap keyed by size. Pop intervals that have
already ended; the heap top is then the smallest interval covering the query.
Time: O((n + q) log(n + q))   Space: O(n)
"""
from __future__ import annotations

import heapq


def min_interval(intervals: list[list[int]], queries: list[int]) -> list[int]:
    """Return the smallest covering interval size for each query."""
    intervals.sort()
    heap: list[tuple[int, int]] = []  # (size, end)
    answer: dict[int, int] = {}
    i = 0
    for query in sorted(queries):
        while i < len(intervals) and intervals[i][0] <= query:
            start, end = intervals[i]
            heapq.heappush(heap, (end - start + 1, end))
            i += 1
        while heap and heap[0][1] < query:  # interval already ended
            heapq.heappop(heap)
        answer[query] = heap[0][0] if heap else -1
    return [answer[query] for query in queries]


if __name__ == "__main__":
    assert min_interval([[1, 4], [2, 4], [3, 6], [4, 4]], [2, 3, 4, 5]) == [3, 3, 1, 4]
    assert min_interval([[2, 3], [2, 5], [1, 8], [20, 25]], [2, 19, 5, 22]) == [2, -1, 4, 6]
    print("ok")
