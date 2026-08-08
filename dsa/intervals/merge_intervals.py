"""Merge Intervals  |  tier: core50, blind75, neetcode150  |  Intervals

Merge all overlapping intervals.

Approach: sort by start. Walk through; if the current interval overlaps the last
merged one (start <= last end), extend the last end; otherwise append a new
interval.
Time: O(n log n)   Space: O(n)
"""
from __future__ import annotations


def merge(intervals: list[list[int]]) -> list[list[int]]:
    """Merge overlapping intervals and return the result."""
    intervals.sort(key=lambda iv: iv[0])
    merged: list[list[int]] = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


if __name__ == "__main__":
    assert merge([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert merge([[1, 4], [4, 5]]) == [[1, 5]]
    assert merge([[1, 4], [0, 4]]) == [[0, 4]]
    print("ok")
