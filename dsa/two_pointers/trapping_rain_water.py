"""Trapping Rain Water  |  tier: core50, neetcode150  |  Two Pointers

Given an elevation map, compute how much rain water it traps.

Approach: two pointers tracking left_max and right_max. Water over a bar is
min(left_max, right_max) - height[i]. Always advance the side with the smaller
max -- that side's max is the true bound there, so the trapped amount is fixed.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def trap(height: list[int]) -> int:
    """Return total trapped rain water."""
    if not height:
        return 0
    left, right = 0, len(height) - 1
    left_max, right_max = height[left], height[right]
    water = 0
    while left < right:
        if left_max < right_max:
            left += 1
            left_max = max(left_max, height[left])
            water += left_max - height[left]
        else:
            right -= 1
            right_max = max(right_max, height[right])
            water += right_max - height[right]
    return water


if __name__ == "__main__":
    assert trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6
    assert trap([4, 2, 0, 3, 2, 5]) == 9
    assert trap([]) == 0
    print("ok")
