"""Container With Most Water  |  tier: core50, blind75, neetcode150  |  Two Pointers

Given heights, pick two lines forming a container holding the most water:
area = min(h[l], h[r]) * (r - l). Maximize it.

Approach: widest container first (both ends), then move the SHORTER wall inward.
Moving the taller wall can never help -- width shrinks and height is still
capped by the shorter wall.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def max_area(height: list[int]) -> int:
    """Return the maximum water a container can hold."""
    left, right = 0, len(height) - 1
    best = 0
    while left < right:
        width = right - left
        best = max(best, width * min(height[left], height[right]))
        if height[left] < height[right]:
            left += 1
        else:
            right -= 1
    return best


if __name__ == "__main__":
    assert max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49
    assert max_area([1, 1]) == 1
    print("ok")
