"""Meeting Rooms  |  tier: blind75, neetcode150  |  Intervals

Given meeting intervals, return True if one person could attend all of them (no
two overlap).

Approach: sort by start; if any meeting begins before the previous one ends,
there is a conflict.
Time: O(n log n)   Space: O(1)
"""
from __future__ import annotations


def can_attend_meetings(intervals: list[list[int]]) -> bool:
    """Return True if no meetings overlap."""
    intervals.sort(key=lambda iv: iv[0])
    for i in range(1, len(intervals)):
        if intervals[i][0] < intervals[i - 1][1]:
            return False
    return True


if __name__ == "__main__":
    assert can_attend_meetings([[0, 30], [5, 10], [15, 20]]) is False
    assert can_attend_meetings([[7, 10], [2, 4]]) is True
    assert can_attend_meetings([]) is True
    print("ok")
