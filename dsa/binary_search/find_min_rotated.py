"""Find Minimum in Rotated Sorted Array  |  tier: core50, blind75, neetcode150  |  Binary Search

A sorted array of distinct values was rotated. Return the minimum element in
O(log n).

Approach: binary search. If nums[mid] > nums[right], the minimum lies to the
right of mid; otherwise it is at mid or to its left. Converge to the pivot.
Time: O(log n)   Space: O(1)
"""
from __future__ import annotations


def find_min(nums: list[int]) -> int:
    """Return the minimum of the rotated sorted array."""
    left, right = 0, len(nums) - 1
    while left < right:
        mid = left + (right - left) // 2
        if nums[mid] > nums[right]:
            left = mid + 1  # min is right of mid
        else:
            right = mid  # min is mid or left
    return nums[left]


if __name__ == "__main__":
    assert find_min([3, 4, 5, 1, 2]) == 1
    assert find_min([4, 5, 6, 7, 0, 1, 2]) == 0
    assert find_min([11, 13, 15, 17]) == 11  # not rotated
    print("ok")
