"""Largest Rectangle in Histogram  |  tier: neetcode150  |  Stack

Given bar heights of width 1, return the area of the largest axis-aligned
rectangle that fits inside the histogram.

Approach: monotonic increasing stack of (start_index, height). When a shorter
bar appears, pop taller bars and compute their area extending from their start
to the current index. Popped bars can extend the new bar's start leftward.
Time: O(n)   Space: O(n)
"""
from __future__ import annotations


def largest_rectangle_area(heights: list[int]) -> int:
    """Return the largest rectangle area in the histogram."""
    stack: list[tuple[int, int]] = []  # (start index, height)
    best = 0
    for i, current_height in enumerate(heights):
        start = i
        while stack and stack[-1][1] > current_height:
            idx, height = stack.pop()
            best = max(best, height * (i - idx))
            start = idx  # this bar can extend back to idx
        stack.append((start, current_height))
    n = len(heights)
    for idx, height in stack:  # bars running to the end
        best = max(best, height * (n - idx))
    return best


if __name__ == "__main__":
    assert largest_rectangle_area([2, 1, 5, 6, 2, 3]) == 10
    assert largest_rectangle_area([2, 4]) == 4
    assert largest_rectangle_area([1]) == 1
    print("ok")
