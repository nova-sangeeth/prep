"""Non-overlapping Intervals  |  tier: blind75, neetcode150  |  Intervals

Return the minimum number of intervals to remove so the rest do not overlap.

Approach: greedy. Sort by END time; always keep the interval that ends earliest
(leaves the most room). Count any interval whose start lies before the last kept
end as a removal.
Time: O(n log n)   Space: O(1)
"""
from __future__ import annotations


def erase_overlap_intervals(intervals: list[list[int]]) -> int:
    """Return the minimum number of intervals to remove."""
    intervals.sort(key=lambda iv: iv[1])
    removals = 0
    prev_end = float("-inf")
    for start, end in intervals:
        if start >= prev_end:  # no overlap -> keep
            prev_end = end
        else:
            removals += 1  # overlaps -> drop this one
    return removals


if __name__ == "__main__":
    assert erase_overlap_intervals([[1, 2], [2, 3], [3, 4], [1, 3]]) == 1
    assert erase_overlap_intervals([[1, 2], [1, 2], [1, 2]]) == 2
    assert erase_overlap_intervals([[1, 2], [2, 3]]) == 0
    print("ok")
