"""Insert Interval  |  tier: blind75, neetcode150  |  Intervals

Insert a new interval into a sorted, non-overlapping list and merge as needed.

Approach: three phases -- append all intervals ending before the new one, merge
all that overlap it (expanding the new interval), then append the rest.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def insert(intervals: list[list[int]], new_interval: list[int]) -> list[list[int]]:
    """Insert new_interval and return the merged interval list."""
    result: list[list[int]] = []
    i, n = 0, len(intervals)

    while i < n and intervals[i][1] < new_interval[0]:
        result.append(intervals[i])  # ends before new starts
        i += 1
    while i < n and intervals[i][0] <= new_interval[1]:
        new_interval[0] = min(new_interval[0], intervals[i][0])
        new_interval[1] = max(new_interval[1], intervals[i][1])
        i += 1
    result.append(new_interval)
    while i < n:
        result.append(intervals[i])
        i += 1
    return result


if __name__ == "__main__":
    assert insert([[1, 3], [6, 9]], [2, 5]) == [[1, 5], [6, 9]]
    assert insert([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]) == [[1, 2], [3, 10], [12, 16]]
    assert insert([], [5, 7]) == [[5, 7]]
    print("ok")
